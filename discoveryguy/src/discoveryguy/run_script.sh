#!/bin/bash

# Set the path to the Python script.
SCRIPT_PATH="script.py"

# Print the script.
cat "$SCRIPT_PATH"

echo "Running the script... in sh"
# Run it using Python.
timeout 60 python3 "$SCRIPT_PATH" "$@"
PYTHON_EXIT_CODE=$?

# Some generated scripts still write to /work/crash.txt; recover it for standalone mode.
if [ -f /work/crash.txt ] && [ ! -f crash.txt ]; then
    cp /work/crash.txt crash.txt
fi

if [ -f crash.txt ] && [ $(stat -c%s crash.txt) -gt 2097152 ]; then
    truncate -s 2M crash.txt
fi

exit $PYTHON_EXIT_CODE
