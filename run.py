import subprocess
import signal
import sys
import platform
import time
from flask import Flask
# Assuming 'app' is a folder and 'create_app' is a function inside 'app/__init__.py'
from app import create_app 

PORT = 8080

# --- Platform-Dependent Utility Function (Revised for safety) ---
def kill_process_on_port(port):
    """
    Finds and kills the process running on the specified port using native OS commands.
    Returns True if no process was found or if it was successfully killed.
    Returns False if an unrecoverable error occurred (e.g., permission denied).
    """
    print(f"Checking for existing processes on port {port}...")
    
    system = platform.system()
    
    if system in ["Linux", "Darwin"]: # Darwin is macOS
        # Use lsof to get PIDs
        command = f"lsof -t -i:{port}"
        
        try:
            # Execute command to get PIDs
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
            pids = result.stdout.strip().split()
            
            if not pids:
                print(f"Port {port} is free. Proceeding.")
                return True
            
            # Found one or more PIDs
            print(f"Found existing process(es) with PID(s): {', '.join(pids)}. Killing...")

            success = True
            for pid in pids:
                try:
                    # Attempt a forceful kill (kill -9) for existing processes
                    subprocess.run(f"kill -9 {pid}", shell=True, check=True, capture_output=True)
                    print(f"Process PID {pid} forcefully killed.")
                except subprocess.CalledProcessError as e:
                    # Check for permission errors, which often require 'sudo'
                    if "Operation not permitted" in e.stderr.strip() and pid != '0':
                        print(f"CRITICAL: Permission denied to kill PID {pid}. Try running script with 'sudo'.")
                        success = False
                    else:
                        print(f"Warning: Failed to kill PID {pid}. {e.stderr.strip()}")
            
            # Give the OS a moment to release the port socket
            if success:
                 time.sleep(1)
            return success
                
        except Exception as e:
            print(f"An unexpected error occurred during port check: {e}")
            return False

    elif system == "Windows":
        # Windows port check logic would go here, but is omitted for Linux focus
        print("Warning: Windows port killing logic is not implemented.")
        return True
    
    else:
        print(f"Unsupported OS: {system}. Skipping port check/kill.")
        return True

# --- Main Application Logic ---
if __name__ == '__main__':
    
    # 1. Kill any *pre-existing* processes on the port.
    if not kill_process_on_port(PORT):
        print(f"Failed to free port {PORT}. Exiting to prevent issues.")
        sys.exit(1)
    
    # 2. Start the Flask application on the now-free port.
    try:
        app = create_app()

        print("-" * 50)
        print(f"Starting Flask application on http://0.0.0.0:{PORT}")
        print("Press CTRL+C to stop the server.")
        print("-" * 50)
        
        # NOTE: app.run() is a BLOCKING call. The script waits here.
        app.run(
            host='0.0.0.0', 
            port=PORT, 
            debug=True,
            threaded=True, 
            processes=1
        )
        
    except Exception as e:
        print(f"An error occurred during application startup: {e}")