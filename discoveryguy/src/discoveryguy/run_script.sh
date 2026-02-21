#!/bin/bash

# Set the path to the Python script.
SCRIPT_PATH="script.py"

# Print the script.
cat "$SCRIPT_PATH"

echo "Running the script... in sh"
# Run it using Python.
timeout 60 python3 "$SCRIPT_PATH" "$@"

if [ -f crash.txt ] && [ $(stat -c%s crash.txt) -gt 2097152 ]; then
    truncate -s 2M crash.txt
fi
