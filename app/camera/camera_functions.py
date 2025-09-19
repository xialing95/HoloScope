from picamera2 import Picamera2
import pprint
import os
import io
import json
import time

'''
JSON file handling for camera settings
'''
# Get the directory of the currently executing script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Join the directory with the filename
SETTINGS_FILE = os.path.join(script_dir, 'camera_settings.json')
PREVIEW_FILE = os.path.join(script_dir, 'preview.jpg')

# Function to load settings from a file
def load_settings():
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Return default settings if the file does not exist
        return {
            "resolution": [1920, 1080],
            "framerate": 30,
            "iso": 100,
            "expSpd": 20000,
            "expMod": "Manual",
            "ExposureTimeMode": 1,
            "ExposureTime": 20000,
            "ExposureValue": 0,
            "AnalogueGainMode": 1,
            "AnalogueGain": 1.0,
            "AwbEnable": "True",
            "awbGain": 1.0,
            "Brightness": 0.0,
            "Contrast": 1.0
        }

# Function to save settings to a file
def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

# Load the initial settings
camera_settings = load_settings()

'''
Camera Picamera2 function
'''
# Global variables for the camera object and its settings
camera = None
preview_config = None
capture_config = None

def initialize_config_camera():
    global camera, preview_config, capture_config
    print("Attempting to initialize and configure camera...")

    if camera:
        print("Deleting existing camera object...")
        delete_camera_object()

    camera = Picamera2()

    preview_config = camera.create_preview_configuration()
    capture_config = camera.create_still_configuration(raw={}, display=None)
    camera.configure(preview_config)

    camera.start()
    time.sleep(2)


    # capture_config = camera.create_still_configuration(
    #             # main={'size': tuple(camera_settings['resolution'])},  
    #             # raw={'size': tuple(camera_settings['resolution'])}, 
    #             main = {},
    #             raw = {},
    #             display=None
    #             )
    # controls={
    #     'ExposureTimeMode': camera_settings['ExposureTimeMode'],
    #     'ExposureTime': camera_settings['ExposureTime'],
    #     'ExposureValue': camera_settings['ExposureValue'],
    #     'AnalogueGainMode': camera_settings['AnalogueGainMode'],
    #     'AnalogueGain': camera_settings['AnalogueGain'],
    #     'Brightness': camera_settings['Brightness'],
    #     'Contrast': camera_settings['Contrast'],
    # }

    # camera.configure(capture_config)
    # camera.start()
    # time.sleep(2)
    # camera.set_controls(controls)
    # time.sleep(1)
    # Switch mode, take the picture, and get a request object
    request_object = camera.switch_mode_capture_request_and_stop(capture_config)

    # Save the main frame as a JPEG
    request_object.save("main", PREVIEW_FILE)

    # Save the raw frame as a DNG file (for RAW data)
    request_object.save_dng(PREVIEW_FILE.replace('.jpg', '.dng'))
    print("Camera object created and configured.")


def delete_camera_object():
    global camera
    if camera:
        try:
            # 1. Stop the camera to halt any streams
            if camera.started:
                camera.stop()
                print("Camera stopped.")

            # 2. Close the camera to release hardware resources
            camera.close()
            print("Camera closed.")
            
            # 3. Explicitly remove the reference to the object
            camera = None
            print("Camera object reference deleted.")
        except Exception as e:
            print(f"Error while trying to delete camera object: {e}")
    else:
        print("No camera object to delete.")

# Initialize the camera object
try:
    # --- Stop, re-configure, and start the camera ---
    # Stop the camera if it's currently running
    if camera and camera.started:
        print("Stopping existing camera instance...")
        camera.stop()
        initialize_config_camera()
    else:
        initialize_config_camera()
    
except Exception as e:
    print(f"Error accessing camera controls: {e}")
finally:
    # Always remember to stop and close the camera
    if 'camera' in locals() and camera.started:
        camera.stop()
    if 'camera' in locals():
        camera.close()