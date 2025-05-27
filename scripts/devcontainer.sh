#!/bin/bash

# Enable debugging
set -euxo pipefail

# --- GCSFuse setup ---
# Replace with your actual bucket name and mount path
GCS_BUCKET_NAME="quipubase-store" # <-- IMPORTANT: REPLACE THIS
GCS_MOUNT_POINT="/app/data" # <-- IMPORTANT: REPLACE THIS

# Create the mount point if it doesn't exist
mkdir -p ${GCS_MOUNT_POINT}

echo "Attempting to mount GCS bucket: ${GCS_BUCKET_NAME} to ${GCS_MOUNT_POINT}"
# Mount the GCS bucket. Adjust options as needed.
# --foreground is important for gcsfuse to stay alive and log to stdout/stderr
# This assumes gcsfuse is in the PATH and authentication is set up (e.g., via GOOGLE_APPLICATION_CREDENTIALS)
gcsfuse --debug_gcs --debug_fuse --foreground ${GCS_BUCKET_NAME} ${GCS_MOUNT_POINT} &
# Capture the PID of the gcsfuse process
GCSFUSE_PID=$!
echo "gcsfuse started with PID: ${GCSFUSE_PID}"

# Wait a bit for gcsfuse to stabilize
sleep 5

# Check if gcsfuse mounted successfully
if mountpoint -q ${GCS_MOUNT_POINT}; then
    echo "GCS bucket ${GCS_BUCKET_NAME} successfully mounted to ${GCS_MOUNT_POINT}"
    # Ensure correct permissions for the mounted directory if needed (e.g., for 'vscode' user)
    # sudo chown -R vscode:vscode ${GCS_MOUNT_POINT}
else
    echo "Failed to mount GCS bucket ${GCS_BUCKET_NAME}. Checking gcsfuse logs..."
    # If gcsfuse failed, the process might have exited, or it might be hanging.
    # You might want to tail its logs or check `dmesg` if fuse operations failed.
    # For now, just exit with an error.
    kill ${GCSFUSE_PID} # Kill the background process if it didn't mount
    exit 1
fi
# --- End GCSFuse setup ---


# Activate Poetry venv (optional, but good for interactive sessions)
# The PATH is already set in the Dockerfile for the vscode user to include /app/.venv/bin
# so explicitly activating might not be strictly necessary for the CMD if it's already in PATH.
# source /app/.venv/bin/activate # If you need a full venv activation

echo "Executing command: $@"
# Execute the command passed to the entrypoint (i.e., the CMD from Dockerfile)
exec "$@"