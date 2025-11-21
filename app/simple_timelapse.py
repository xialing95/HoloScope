import time
import os
import sys
from datetime import datetime

from picamera2 import Picamera2
from libcamera import controls

# --- Configuration ---
# This finds the user's home directory and appends 'capture_image'.
LOG_DIR = os.path.join(os.path.expanduser('~'), 'capture_image')

# --- Logging Intervals ---
IMAGE_INTERVAL_SECONDS = 60 # Take a photo every 60 seconds

# --- Camera Exposure Control ---
# Exposure Time in microseconds (e.g., 1000000 us = 1 second)
# Set to None to use automatic exposure control (AEC).
EXPOSURE_TIME_US = 500 
# Set to None to use automatic analog gain control.
ANALOG_GAIN = 1.0 

# --- Setup Directories ---
os.makedirs(LOG_DIR, exist_ok=True)
print(f"Log and Image directory set to: {LOG_DIR}")

# --- Camera Setup (Picamera2) ---
try:
    picam2 = Picamera2()
    
    # Configure the camera for raw still capture
    raw_config = picam2.create_still_configuration(raw={'size': picam2.sensor_resolution})
    picam2.configure(raw_config)
    
    # 1. Start the camera
    picam2.start()

    # 2. Set Exposure Controls
    camera_controls = {}
    
    if EXPOSURE_TIME_US is not None:
        # FIX: Use string key ("ExposureTime") instead of the control object (controls.ExposureTime)
        # to avoid the libcamera internal type error. Value is cast to int.
        camera_controls["ExposureTime"] = int(EXPOSURE_TIME_US)
        # Disable Automatic Exposure Control (AEC) when setting manual exposure
        camera_controls["AeEnable"] = False 
        print(f"Manual Exposure Time set to: {EXPOSURE_TIME_US} us")
        
    if ANALOG_GAIN is not None:
        # FIX: Use string key ("AnalogueGain") instead of the control object (controls.AnalogueGain)
        # Value is cast to float.
        camera_controls["AnalogueGain"] = float(ANALOG_GAIN)
        print(f"Manual Analog Gain set to: {ANALOG_GAIN}")

    if camera_controls:
        # Apply the controls.
        picam2.set_controls(camera_controls)

    print("Picamera2 started successfully.")

except Exception as e:
    print(f"Error initializing Picamera2: {e}")
    print("Ensure the camera module is connected and enabled.")
    sys.exit(1)


# --- Helper Functions ---
def capture_timelapse_photo(picam2_obj, image_dir):
    """
    Captures a photo using Picamera2, saving it as a DNG file 
    by explicitly targeting the 'raw' stream output.
    """
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_filepath = os.path.join(image_dir, f"timelapse_{timestamp_str}.dng")

    print(f"--> Capturing raw image: {os.path.basename(image_filepath)}")

    try:
        # Explicitly specify 'name="raw"' to save the raw stream data,
        # which is the source of the DNG file.
        picam2_obj.capture_file(image_filepath, name='raw') 
        print(f"Raw DNG image successfully saved to {image_filepath}")

    except Exception as e:
        print(f"ERROR: Photo capture failed: {e}")


# --- Main Logic ---
print(f"Timelapse photos taken every {IMAGE_INTERVAL_SECONDS} seconds.")
print("Press Ctrl+C to stop.")

# Initialize the last capture time to ensure a photo is taken immediately or after first interval
last_image_time = time.time() - IMAGE_INTERVAL_SECONDS 

try:
    while True:
        current_time = time.time()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Image Capture Check (Every 60 seconds)
        if current_time - last_image_time >= IMAGE_INTERVAL_SECONDS:
            capture_timelapse_photo(picam2, LOG_DIR)
            last_image_time = current_time # Reset timer


except KeyboardInterrupt:
    print("\nLogging stopped by user.")
except Exception as e:
    print(f"\nAn error occurred: {e}")
finally:
    # IMPORTANT: Close the camera connection gracefully
    print("Closing Picamera2 connection...")
    picam2.close()
    print(f"Images saved to {LOG_DIR}.")