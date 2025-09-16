from flask import render_template, request, jsonify
from . import network_bp
import subprocess
from pathlib import Path

# # Get the absolute path to the directory containing the current script
# BASE_DIR = Path(__file__).resolve().parent.parent
# print(BASE_DIR)

@network_bp.route('/')
def index():
    return render_template('network.html')

# This route handles the request from the JavaScript function
# Assumed GET request for simplicity
@network_bp.route('/enable_hotspot')
def enable_hotspot():
    try:
        # Execute the bash script. The script should be in the same directory, or you can specify the full path.
        # It's good practice to provide the full path to the script to avoid issues.
        # `shell=True` is required to run the command directly in the shell. Be cautious with user input if you were to pass any.
        # `subprocess.check_output` will raise a `CalledProcessError` if the script returns a non-zero exit code.
        # `sudo` may be needed if the script requires elevated permissions.
        subprocess.check_output(['/bin/bash', '/app/bin/switch_to_ap.sh'], stderr=subprocess.STDOUT)
        
        # If the script runs without error, return a success message
        status_message = "AP successfully!"
        
    except subprocess.CalledProcessError as e:
        # If the script fails, capture the error output and return a failure message
        status_message = f"AP Failed: {e.output.decode('utf-8')}"
        
    except FileNotFoundError:
        status_message = "Script file not found: switch_to_ap.sh"

    # Return a JSON response with the status message
    return jsonify(status=status_message)


@network_bp.route('/connect_to_wifi', methods=['POST'])
def connect_to_wifi():
    data = request.json
    ssid = data.get('ssid')
    password = data.get('password')

    try:
        subprocess.check_output(
            ['/bin/bash', '/app/bin/switch_to_wifi.sh', ssid, password], 
            stderr=subprocess.STDOUT
        )
        # If the script runs without error, return a success message
        print("Script executed successfully with arguments.")
        
    except subprocess.CalledProcessError as e:
        # If the script fails, capture the error output and return a failure message
        status_message = f"Wifi Failed: {e.output.decode('utf-8')}"
        
    except FileNotFoundError:
        status_message = "Script file not found: switch_to_wifi.sh"

    # Return a JSON response with the status message
    return jsonify(status=status_message)