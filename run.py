import subprocess
import signal
import sys
import platform
import time
from flask import Flask
# Assuming 'app' is a folder and 'create_app' is a function inside 'app/__init__.py'
from app import create_app 
import epaper_display.epaper_service as epd_service

PORT = 8080

# --- Platform-Dependent Utility Function ---
def kill_process_on_port(port):
    """
    Finds and kills the process running on the specified port using native OS commands.
    Returns True if the port is free OR successfully freed.
    Returns False if an unrecoverable error occurred (e.g., persistent permission denied).
    """
    print(f"Checking for existing processes on port {port}...")
    
    system = platform.system()
    
    if system in ["Linux", "Darwin"]: # Darwin is macOS
        # Command to get PIDs using lsof
        command = f"lsof -t -i:{port}"
        
        try:
            # Execute command to get PIDs (no sudo initially)
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
            pids = result.stdout.strip().split()
            
            if not pids:
                print(f"✅ Port {port} is free. Proceeding.")
                return True
            
            # Found one or more PIDs
            print(f"\n🚨 Port {port} is IN USE by PID(s): {', '.join(pids)}. Attempting to kill...")

            all_killed_successfully = True
            for pid in pids:
                try:
                    # Attempt a forceful kill (kill -9) 
                    subprocess.run(f"kill -9 {pid}", shell=True, check=True, capture_output=True)
                    print(f"   - Process PID {pid} forcefully killed.")
                except subprocess.CalledProcessError as e:
                    all_killed_successfully = False
                    
                    # This check is tricky, as 'kill' errors differ, but permission is the main issue
                    print(f"   - ❌ Failed to kill PID {pid} (Error: {e.stderr.strip().splitlines()[-1]}).")
                    
            
            if all_killed_successfully:
                # Give the OS a moment to release the port socket
                time.sleep(1)
                # Quick re-check to confirm
                recheck = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
                if not recheck.stdout.strip().split():
                    print(f"\n✅ Port {port} is now successfully freed.")
                    return True
                else:
                    # Port still held, likely by a process that refused to die
                    print("\n❌ CRITICAL: Process killed but port is still held. Permission issue suspected.")
                    print("   If this issue persists, you must run the entire script with 'sudo'.")
                    return False
            else:
                print("\n❌ CRITICAL: Failed to kill one or more processes.")
                print("   The processes are likely owned by 'root' or another user.")
                print(f"   RECOMMENDATION: Stop the app manually, or run this script using: 'sudo python3 {sys.argv[0]}'")
                return False

        except Exception as e:
            print(f"\nAn unexpected error occurred during port check: {e}")
            return False

    elif system == "Windows":
        # Simplified placeholder for Windows
        print("Warning: Windows port killing logic is not implemented. Please check manually.")
        return True
    
    else:
        print(f"Unsupported OS: {system}. Skipping port check/kill.")
        return True
    
# Define the name of your Systemd unit file
SYSTEMD_SERVICE_NAME = "holo-scope.service"

def stop_systemd_service():
    """
    Attempts to stop the Systemd service unit.
    Requires the current user (or script) to have sudo privileges 
    or be configured via visudo for passwordless execution of this command.
    """
    print(f"\nAttempting to stop Systemd service: {SYSTEMD_SERVICE_NAME}...")
    try:
        # Run the stop command using sudo
        # NOTE: This will require a password if the script is not already run with sudo.
        subprocess.run(
            ["sudo", "systemctl", "stop", SYSTEMD_SERVICE_NAME], 
            check=True, 
            capture_output=True, 
            text=True
        )
        print(f"✅ Successfully requested Systemd to stop {SYSTEMD_SERVICE_NAME}.")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to stop Systemd service {SYSTEMD_SERVICE_NAME}.")
        print("   This is often due to insufficient permissions or the service not existing.")
        print(f"   Error: {e.stderr.strip()}")
    except FileNotFoundError:
        print("❌ Error: 'sudo' or 'systemctl' command not found.")
    except Exception as e:
        print(f"❌ An unexpected error occurred while calling systemctl: {e}")

# --- Main Application Logic ---
if __name__ == '__main__':
    try:
        app = create_app()

        print("-" * 50)
        print(f"Starting Flask application on http://0.0.0.0:{PORT}")
        print("Press CTRL+C to stop the server.")
        print("-" * 50)
        
        # NOTE: app.run() is a BLOCKING call. The script waits here.
        # Ensure the port is set on the app instance if create_app doesn't handle it
        app.config['PORT'] = PORT
        
        app.run(
            host='0.0.0.0', 
            port=PORT, 
            debug=False,         # This implicitly disables the reloader
            use_reloader=False,   # Explicitly disable the reloader
            # It's generally better to let the development server manage these settings
            # Using 'threaded=True' is fine, but Flask/Werkzeug may ignore 'processes=1'
            threaded=True, 
            processes=1 # Removed, as it's not a standard app.run() argument in recent Flask versions
        )
        
        epd_service.main()
        
    except Exception as e:
        print(f"An error occurred during application startup: {e}")