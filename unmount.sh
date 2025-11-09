#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
MOUNT_POINT="$SCRIPT_DIR/my_fs"

echo "Unmounting $MOUNT_POINT..."

# fusermount is the standard way to unmount FUSE filesystems
fusermount -u "$MOUNT_POINT"

if [ $? -eq 0 ]; then
    echo "Successfully unmounted."
else
    echo "Unmount failed. Trying lazy unmount..."
    # Fallback to lazy unmount if it's busy
    fusermount -uz "$MOUNT_POINT"
    if [ $? -eq 0 ]; then
        echo "Lazy unmount successful."
    else
        echo "Error: Could not unmount. Is it in use?"
        echo "You may need to unmount manually: sudo umount $MOUNT_POINT"
    fi
fi
