#!/usr/bin/env python3
import difflib
import hashlib
import os
import sqlite3
import subprocess
import typing as tp
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import click

DB_PATH = ".git/changes.db"


class GitHasher:
    def __init__(self):
        self.git_dir = self.find_git_directory()
        self.db_path = self.git_dir / DB_PATH
        self._setup_database()

    def _setup_database(self):
        """Initialize SQLite database for tracking changes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS changes (
                commit_hash TEXT PRIMARY KEY,
                timestamp TEXT,
                branch TEXT,
                changes TEXT
            )
        """
        )
        conn.commit()
        conn.close()

    def find_git_directory(self) -> Path:
        """Find the root git directory"""
        current = Path.cwd()
        while not (current / ".git").exists():
            if current == current.parent:
                raise Exception("Not in a git repository")
            current = current.parent
        return current

    def get_current_branch(self) -> str:
        """Get the current git branch"""
        return (
            subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
            .decode()
            .strip()
        )

    def get_last_commit_hash(self) -> str:
        """Get the hash of the last commit"""
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()

    def get_file_changes(self) -> Dict[str, List[str]]:
        """Get changes for each modified file"""
        changes = {}

        # Get list of modified files
        result = subprocess.run(["git", "diff"], capture_output=True, text=True)
        diff_output = result.stdout

        # Parse diff output
        current_file = None
        for line in diff_output.splitlines():
            if line.startswith("diff --git"):
                # Extract file names
                parts = line.split(" b/")[-1]
                current_file = parts.split()[0]
                changes[current_file] = []
            elif current_file:
                changes[current_file].append(line)

        return changes

    def compute_commit_hash(self, changes: Dict[str, List[str]], message: str) -> str:
        """Compute commit hash based on file changes and message"""
        # Create a string representation of all changes
        changes_str = ""
        for file, file_changes in changes.items():
            changes_str += f"\nFile: {file}\n"
            changes_str += "\n".join(file_changes)

        # Include timestamp and message in hash
        timestamp = datetime.now().isoformat()
        data = f"{changes_str}{message}{timestamp}".encode()
        return hashlib.sha256(data).hexdigest()

    def store_changes(
        self, commit_hash: str, changes: Dict[str, List[str]], message: str
    ):
        """Store changes in SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        branch = self.get_current_branch()

        # Convert changes to string format
        changes_str = "\n".join(
            [
                f"File: {file}\n" + "\n".join(file_changes)
                for file, file_changes in changes.items()
            ]
        )

        cursor.execute(
            """
            INSERT INTO changes (commit_hash, timestamp, branch, changes)
            VALUES (?, ?, ?, ?)
        """,
            (commit_hash, timestamp, branch, changes_str),
        )

        conn.commit()
        conn.close()

    def show_recent_changes(self, limit: int = 5) -> List[Tuple[str, str, str, str]]:
        """Show recent changes from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT commit_hash, timestamp, branch, changes
            FROM changes 
            ORDER BY timestamp DESC 
            LIMIT ?
        """,
            (limit,),
        )
        results = cursor.fetchall()
        conn.close()
        return results


@click.group()
def main():
    """Git commit hasher and automation tool"""
    pass


@main.command()
@click.option("--message", "-m", required=True, help="Commit message")
@click.option("--hash-only", is_flag=True, help="Only generate hash without committing")
@click.option("--push", is_flag=True, help="Push changes to remote after commit")
def commit(message: str, hash_only: bool, push: bool):
    """Create a git commit with a unique hash based on file changes"""
    hasher = GitHasher()
    changes = hasher.get_file_changes()
    commit_hash = hasher.compute_commit_hash(changes, message)

    if hash_only:
        click.echo(f"Generated commit hash: {commit_hash}")
        return

    try:
        # Stage all changes
        subprocess.run(["git", "add", "."], check=True)

        # Create commit with hash in message
        commit_msg = f"{message}\n\nHash: {commit_hash}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)

        # Store changes in database
        hasher.store_changes(commit_hash, changes, message)

        click.echo(f"Created commit with hash: {commit_hash}")

        if push:
            try:
                subprocess.run(["git", "push"], check=True)
                click.echo("Changes pushed successfully")
            except subprocess.CalledProcessError as e:
                click.echo(f"Warning: Failed to push changes: {e}")
        else:
            click.echo(
                "Commit created successfully. Use --push to push changes to remote"
            )

    except subprocess.CalledProcessError as e:
        click.echo(f"Error: {e}")
        raise


@main.command()
@click.option("--branch", "-b", default=None, help="Branch name")
@click.option("--show-changes", is_flag=True, help="Show recent changes")
def status(branch: str, show_changes: bool):
    """Show git status and current branch"""
    hasher = GitHasher()

    if branch:
        try:
            subprocess.run(["git", "checkout", branch], check=True)
        except subprocess.CalledProcessError:
            click.echo(f"Error: Branch '{branch}' not found")
            return

    click.echo("\nGit Status:")
    subprocess.run(["git", "status"])
    click.echo(f"\nCurrent branch: {hasher.get_current_branch()}")
    click.echo(f"Last commit hash: {hasher.get_last_commit_hash()}")

    if show_changes:
        click.echo("\nRecent Changes:")
        recent = hasher.show_recent_changes()
        for commit_hash, timestamp, branch in recent:
            click.echo(f"\nCommit: {commit_hash[:7]}")
            click.echo(f"Time: {timestamp}")
            click.echo(f"Branch: {branch}")


if __name__ == "__main__":
    main()
