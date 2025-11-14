import time
import board
import adafruit_bme680
import csv
import os
import sys # New import
from datetime import datetime

from picamera2 import Picamera2 # New import
from libcamera import controls # New import

# --- Configuration ---
# This finds the user's home directory and appends 'capture_image'.
LOG_DIR = os.path.join(os.path.expanduser('~'), 'capture_image')
LOG_FILE = os.path.join(LOG_DIR, 'bme680_data.csv')

# --- Logging Intervals ---
LOG_INTERVAL_SECONDS = 10   # Log BME680 data every 10 seconds
IMAGE_INTERVAL_SECONDS = 60 # Take a photo every 60 seconds

# The sensor compensates for altitude using sea-level pressure.
SEA_LEVEL_HPA = 1013.25 

# --- Setup Directories ---
os.makedirs(LOG_DIR, exist_ok=True)
print(f"Log and Image directory set to: {LOG_DIR}")


# --- Sensor Setup (BME680) ---

try:
    i2c = board.I2C()
    bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c)
except ValueError as e:
    print(f"Error initializing BME680 sensor: {e}")
    print("Ensure the sensor is correctly wired and I2C is enabled.")
    sys.exit(1) # Use sys.exit for clean termination

bme680.sea_level_pressure = SEA_LEVEL_HPA
bme680.set_gas_heater(320, 150) # Set gas heater for VOC measurement


# --- Camera Setup (Picamera2) ---
try:
    picam2 = Picamera2()
    
    # Configure the camera to use the raw stream (for DNG capture)
    # The raw stream resolution depends on your specific camera sensor.
    # We also include a main stream for potential preview/fast JPEG generation, 
    # but the raw stream configuration is key for DNG.
    raw_config = picam2.create_still_configuration(raw={'size': picam2.sensor_resolution})
    picam2.configure(raw_config)
    
    picam2.start()
    print("Picamera2 started successfully.")

except Exception as e:
    print(f"Error initializing Picamera2: {e}")
    print("Ensure the camera module is connected and enabled.")
    sys.exit(1)


# --- Helper Functions ---

def initialize_log_file(filename):
    """Checks if the log file exists and writes the header if it doesn't."""
    if not os.path.exists(filename):
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            # Write the header row
            header = ['Timestamp', 'Temperature_C', 'Humidity_perc', 'Pressure_hPa', 'Altitude_m', 'Gas_resistance_ohms']
            writer.writerow(header)
            print(f"Created new log file: {filename} with header.")
    else:
        print(f"Appending to existing log file: {filename}.")


def capture_timelapse_photo(picam2_obj, image_dir):
    """
    Captures a photo using Picamera2, saving it as a DNG file 
    by targeting the raw stream output.
    """
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Using .dng extension for raw capture
    image_filepath = os.path.join(image_dir, f"timelapse_{timestamp_str}.dng")

    print(f"--> Capturing raw image: {os.path.basename(image_filepath)}")

    try:
        # Capture from the raw stream and save to a DNG file.
        # This implicitly uses the raw sensor data configuration.
        picam2_obj.capture_file(image_filepath) 
        
        print(f"Raw DNG image successfully saved to {image_filepath}")

    except Exception as e:
        print(f"ERROR: Photo capture failed: {e}")


# --- Main Logic ---

initialize_log_file(LOG_FILE)

print(f"\nBME680 logging started. Readings every {LOG_INTERVAL_SECONDS} seconds.")
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

        # 2. Read sensor data
        temperature = bme680.temperature
        humidity = bme680.relative_humidity
        pressure = bme680.pressure
        altitude = bme680.altitude
        gas = bme680.gas

        # Wait until the gas sensor has completed a reading
        if gas is None:
            print(f"[{timestamp}] Waiting for gas reading...")
            time.sleep(LOG_INTERVAL_SECONDS)
            continue

        # 3. Prepare data row and log to file (same as before)
        data_row = [
            timestamp,
            f"{temperature:.2f}",
            f"{humidity:.2f}",
            f"{pressure:.2f}",
            f"{altitude:.2f}",
            f"{gas}",
        ]

        with open(LOG_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(data_row)

        # 4. Print to console for monitoring
        print(f"[{timestamp}] Temp: {temperature:.2f} C | Hum: {humidity:.2f} % | Pres: {pressure:.2f} hPa | Gas: {gas} ohms")

        # 5. Wait for the next log interval
        time.sleep(LOG_INTERVAL_SECONDS)

except KeyboardInterrupt:
    print("\nLogging stopped by user.")
except Exception as e:
    print(f"\nAn error occurred: {e}")
finally:
    # IMPORTANT: Close the camera connection gracefully
    print("Closing Picamera2 connection...")
    picam2.close()
    print(f"Sensor data saved to {LOG_FILE}.")
    print(f"Images saved to {LOG_DIR}.")