import json
import typing as tp
from dataclasses import dataclass

import typing_extensions as tpe

from ._base import Artifact


@dataclass
class JsonLoader(Artifact):
    ref: tpe.Annotated[
        str,
        tpe.Doc(
            """
		This `ref` can represent one out of three things:

		- An HTTP URL.
		- A file path (temporary or not) within the local filesystem.
		- A text file content.
		"""
        ),
    ]

    def extract(self) -> tp.Generator[str, None, None]:
        """
        Extract data from JSON/JSONL files.

        Yields:
            Each line from the JSON file as a string
        """
        file_path = self.retrieve()

        try:
            # Check file size before reading it all into memory
            file_size = file_path.stat().st_size

            # For small files (< 10MB), we can load entirely into memory
            if file_size < 10 * 1024 * 1024:  # 10MB threshold
                with open(file_path, "r", encoding="utf-8") as f:
                    # First try to parse as a single JSON object
                    try:
                        content = f.read()
                        data = json.loads(content)
                        if isinstance(data, list):
                            # Handle JSON arrays by yielding each item
                            for item in data:
                                yield json.dumps(item)
                        else:
                            # Handle single JSON object
                            yield content
                    except json.JSONDecodeError:
                        # If it fails, try to parse as JSONL (one JSON object per line)
                        f.seek(0)  # Reset file pointer
                        for line_num, line in enumerate(f, 1):
                            line = line.strip()
                            if line:  # Skip empty lines
                                try:
                                    # Validate it's proper JSON by parsing and re-serializing
                                    parsed = json.loads(line)
                                    yield json.dumps(parsed)
                                except json.JSONDecodeError:
                                    # Provide context about the error
                                    yield json.dumps(
                                        {
                                            "error": f"Invalid JSON at line {line_num}",
                                            "line": line,
                                        }
                                    )
            else:
                # For large files, process line by line to avoid memory issues
                with open(file_path, "r", encoding="utf-8") as f:
                    # Check if it might be a JSON array by examining the first character
                    first_char = f.read(1)
                    f.seek(0)

                    if first_char == "[":
                        # It might be a JSON array, but we'll process it as JSONL anyway
                        # for memory efficiency, with a warning
                        yield json.dumps(
                            {
                                "warning": "Large JSON array detected. Processing line by line, which may not preserve array structure."
                            }
                        )

                    # Process line by line
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if line:  # Skip empty lines
                            try:
                                # Try to parse each line as a separate JSON object
                                parsed = json.loads(line)
                                yield json.dumps(parsed)
                            except json.JSONDecodeError:
                                # If it's not valid JSON, report the error but include the line
                                yield json.dumps(
                                    {
                                        "error": f"Invalid JSON at line {line_num}",
                                        "line": line,
                                    }
                                )
        except Exception as e:
            # Handle file opening/reading errors
            yield f"Error processing JSON file: {str(e)}"
