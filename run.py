from flask import Flask
# Assuming 'app' is a folder and 'create_app' is a function inside 'app/__init__.py'
from app import create_app 
import os
import subprocess
import re
import platform

PORT = 8080

# --- Platform-Dependent Utility Function ---
def kill_process_on_port(port):
    """
    Finds and kills the process running on the specified port using native OS commands.
    This method is platform-dependent (Windows vs. Linux/macOS).
    """
    print(f"Checking for processes on port {port}...")
    
    system = platform.system()
    pid = None

    if system == "Windows":
        # Windows command: netstat -ano lists all connections and PIDs
        command = f"netstat -ano | findstr LISTENING | findstr :{port}"
        
        try:
            # Use run with capture_output=True to get the output
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            output = result.stdout
            
            # The PID is the last number on the line
            if output:
                # Regex to find the PID which is the last token on the line
                # It accounts for multiple spaces and line endings
                match = re.search(r"LISTENING\s+(\d+)\s*$", output.strip(), re.MULTILINE)
                if match:
                    pid = match.group(1)
            
            if pid:
                print(f"Found process with PID {pid} listening on port {port}. Killing...")
                # Windows command: taskkill /F /PID <pid>
                subprocess.run(f"taskkill /F /PID {pid}", shell=True, check=True, capture_output=True)
                print(f"Process PID {pid} forcefully killed.")
                return True
            
        except subprocess.CalledProcessError as e:
            # This is okay if the commands fail to find anything or taskkill fails (e.g., permission)
            print(f"Subprocess error (Port Check): {e.stderr.strip()}")
        except Exception as e:
            print(f"An unexpected error occurred on Windows: {e}")

    elif system in ["Linux", "Darwin"]: # Darwin is macOS
        # Linux/macOS command: lsof -t -i:<port> returns only the PIDs
        command = f"lsof -t -i:{port}"
        
        try:
            # Use run with check=False in case lsof returns no PIDs (exit code 1)
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
            output = result.stdout.strip()
            
            # Output is a string of PIDs separated by newlines
            if output:
                pids = output.split()
                
                for pid in pids:
                    print(f"Found process with PID {pid} listening on port {port}. Killing...")
                    # POSIX command: kill -9 <pid> (force kill)
                    # NOTE: kill -9 is a hard kill, kill -TERM (default) is graceful
                    subprocess.run(f"kill -9 {pid}", shell=True, check=True, capture_output=True)
                    print(f"Process PID {pid} forcefully killed.")
                return True
                
        except subprocess.CalledProcessError as e:
            # This is okay if the commands fail to find anything or kill fails (e.g., permission)
            print(f"Subprocess error (Port Check): {e.stderr.strip()}")
        except Exception as e:
            print(f"An unexpected error occurred on Linux/macOS: {e}")

    else:
        print(f"Unsupported OS: {system}. Cannot check/kill port.")
        return False

    print(f"No process found listening on port {port}.")
    return True

if not kill_process_on_port():
    print(f"Failed to ensure port {PORT} is free. Exiting.")

# --- Main Application Logic ---
if __name__ == '__main__':
    # Start the Flask application
    try:
        app = create_app()

        print("-" * 50)
        print(f"Starting Flask application on http://0.0.0.0:{PORT}")
        print("Press CTRL+C to stop the server.")
        print("-" * 50)
        
        app.run(
            host='0.0.0.0', 
            port=PORT, 
            debug=False,
            threaded=True, 
            processes=1
        )
        
    except Exception as e:
        print(f"An error occurred during application startup: {e}")