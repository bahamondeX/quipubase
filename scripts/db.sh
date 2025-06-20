#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Function to log messages with a timestamp
log_message() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Trap errors and log them
handle_error() {
  log_message "ERROR: Prisma client generation failed!"
  # Exit with the error code of the last failed command
  exit 1
}
trap 'handle_error' ERR

log_message "Starting Prisma client generation..."

# Execute the Prisma generate command.
# Note: The 'prisma generate' command is typically a Node.js application
# and is usually run directly if 'prisma' CLI is in the PATH, or via 'npx prisma generate'
# if installed as a local npm dependency.
# The `$(which python)` prefix is unusual for this command and might not be necessary or correct.
# Ensure Node.js and the Prisma CLI are properly installed and accessible in the environment.
$(which python) -m prisma db push
$(which python) -m prisma db pull
$(which python) -m prisma generate
$(which python) -m prisma py fetch

# Check the exit status of the previous command (prisma generate)
if [ $? -eq 0 ]; then
  log_message "Prisma client generated successfully."
else
  # This block should ideally not be reached if 'set -e' and 'trap ERR' are working,
  # but it's good for explicit handling or if 'set -e' is disabled.
  log_message "ERROR: Prisma client generation failed with an unexpected error."
  exit 1
fi

log_message "Prisma generation operations completed."