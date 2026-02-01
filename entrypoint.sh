#!/bin/bash
set -e

# Target directory for lerobot in the workspace
LEROBOT_DIR="/workspace/lerobot"
OPT_LEROBOT="/opt/lerobot"

# Check if lerobot directory exists in the workspace
if [ ! -d "$LEROBOT_DIR" ]; then
    echo "lerobot not found in $LEROBOT_DIR. Copying from $OPT_LEROBOT..."
    cp -r "$OPT_LEROBOT" "$LEROBOT_DIR"
else
    echo "lerobot already exists in $LEROBOT_DIR."
fi

# Install lerobot in editable mode to ensure it's linked
# Using 'pip install -e' updates the egg-link, which is fast if dependencies are already met
echo "Installing lerobot in editable mode..."
pip install --no-cache-dir -e "$LEROBOT_DIR[all,pi]"

# Execute the passed command
exec "$@"
