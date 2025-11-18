#!/bin/bash

# --- 1. Source the Virtual Environment ---
# The 'source' command must be used to execute the 'activate' script
# in the current shell, making 'python' and 'pip' point to the venv's versions.

echo "Activating Python virtual environment..."
source venv/bin/activate
sudo systemctl stop holo-scope.service

# --- 2. Check for the simple_log.py process and stop it (optional but recommended) ---
# If the script is already running via nohup, this prevents conflicts.
# Note: You need a better way to manage PIDs for a robust script. This is basic.
# pgrep -f "python3 app/sensors/simple_log.py" | xargs kill

# --- 3. Start the main application using nohup ---
# We use 'python3' here, which now points to the venv's Python.
# 'nohup' keeps it running after you log out.
# '>' redirects stdout, '2>&1' redirects stderr to the same file.
# '&' runs the process in the background.

echo "Starting simple_log.py using nohup..."
nohup python3 simple_timelapse.py > log_output.log 2>&1 &

# --- 4. Deactivate the Virtual Environment (Optional) ---
# It's good practice to deactivate the venv in the current shell
# once the background process has been started.
deactivate

echo "Script initiated. Check log_output.log for status."
echo "You can now safely close your SSH session."