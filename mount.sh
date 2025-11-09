#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Define project paths
STORAGE_BACKEND="$SCRIPT_DIR/storage_backend"
MOUNT_POINT="$SCRIPT_DIR/my_fs"
METADATA_DB="$SCRIPT_DIR/metadata/file_index.db"

# Check if python-fuse is installed
python -c "import fuse" &> /dev/null
if [ $? -ne 0 ]; then
    echo "Error: 'fuse-python' (or 'fusepy') is not installed."
    echo "Please install it: pip install fusepy"
    exit 1
fi

# Check if main script exists
if [ ! -f "$SCRIPT_DIR/insightfs.py" ]; then
    echo "Error: insightfs.py not found!"
    exit 1
fi

# Create directories if they don't exist
mkdir -p "$STORAGE_BACKEND"
mkdir -p "$MOUNT_POINT"
mkdir -p "$(dirname "$METADATA_DB")"

echo "Mounting InsightFS..."
echo "  Storage: $STORAGE_BACKEND"
echo "  Mount:   $MOUNT_POINT"
echo "  DB:      $METADATA_DB"

# Run the filesystem
# The 'foreground=True' in the python script will keep this running
python "$SCRIPT_DIR/insightfs.py" "$STORAGE_BACKEND" "$MOUNT_POINT" "$METADATA_DB"

echo "InsightFS unmounted."
