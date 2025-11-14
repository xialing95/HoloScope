import time
import board
import adafruit_bme680
import csv
import os
import subprocess
from datetime import datetime

# --- Configuration ---
# This finds the user's home directory and appends 'capture_image'.
LOG_DIR = os.path.join(os.path.expanduser('~'), 'capture_image')
LOG_FILE = os.path.join(LOG_DIR, 'bme680_data.csv')

LOG_INTERVAL_SECONDS = 10  # Log data every 10 seconds
IMAGE_INTERVAL_SECONDS = 60 # Take a photo every 60 seconds


# The sensor compensates for altitude using sea-level pressure.
# Change this to match the location's pressure (hPa) at sea level for your location.
# Default is 1013.25 hPa.
SEA_LEVEL_HPA = 1013.25 

# Camera command (assuming libcamera-still on modern Raspberry Pi OS)
CAMERA_CMD = 'libcamera-still' 
# File extension for raw image capture (often DNG or CR3 format)
IMAGE_EXT = '.dng' 


# --- Sensor Setup ---

# Create sensor object, communicating over the board's default I2C bus
try:
    i2c = board.I2C()
    bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c)
except ValueError as e:
    print(f"Error initializing BME680 sensor: {e}")
    print("Ensure the sensor is correctly wired and I2C is enabled.")
    exit()

bme680.sea_level_pressure = SEA_LEVEL_HPA

# Set the gas heater configuration (recommended for VOC measurement)
# (Temperature in deg C, duration in ms)
bme680.set_gas_heater(320, 150)

def capture_timelapse_photo(image_dir):
    """
    Executes the command-line camera utility to capture a raw DNG image.
    
    NOTE: Ensure the command utility (e.g., libcamera-still) is installed and in PATH.
    """
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_filepath = os.path.join(image_dir, f"timelapse_{timestamp_str}{IMAGE_EXT}")

    print(f"--> Capturing image: {os.path.basename(image_filepath)}")

    try:
        # Command: libcamera-still --raw -o <filepath>
        # --raw requests a raw capture (DNG/CR3 format depending on sensor)
        # Using shell=False and list format is safer than shell=True
        result = subprocess.run(
            [CAMERA_CMD, '--raw', '-o', image_filepath],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Image successfully saved to {image_filepath}")
        if result.stderr:
            print(f"Camera command warnings/info: {result.stderr.strip()}")

    except subprocess.CalledProcessError as e:
        print(f"ERROR: Camera command failed (Exit Code {e.returncode}). STDOUT: {e.stdout.strip()} STDERR: {e.stderr.strip()}")
        # This often fails if the camera is not connected or already in use.
    except FileNotFoundError:
        print(f"ERROR: Camera command '{CAMERA_CMD}' not found. Is your camera software installed and in your system's PATH?")
    except Exception as e:
        print(f"An unexpected error occurred during photo capture: {e}")


# --- File Setup ---

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

initialize_log_file(LOG_FILE)


# --- Logging Loop ---

print(f"\nBME680 logging started. Readings every {LOG_INTERVAL_SECONDS} seconds.")
print(f"Timelapse photos taken every {IMAGE_INTERVAL_SECONDS} seconds.")
print("Press Ctrl+C to stop.")

# Initialize the last capture time to ensure a photo is taken immediately or after first interval
last_image_time = time.time() - IMAGE_INTERVAL_SECONDS # Ensures photo is taken on first run

try:
    while True:
        # 1. Get current time
        current_time = time.time()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 2. Image Capture Check (Every 60 seconds)
        if current_time - last_image_time >= IMAGE_INTERVAL_SECONDS:
            capture_timelapse_photo(LOG_DIR)
            last_image_time = current_time # Reset timer

        # 3. Read sensor data
        temperature = bme680.temperature
        humidity = bme680.relative_humidity
        pressure = bme680.pressure
        altitude = bme680.altitude
        gas = bme680.gas

        # Wait until the gas sensor has completed a reading
        if gas is None:
            # Gas data is not immediately available; skip this cycle
            print(f"[{timestamp}] Waiting for gas reading...")
            time.sleep(LOG_INTERVAL_SECONDS)
            continue

        # 3. Prepare data row
        data_row = [
            timestamp,
            f"{temperature:.2f}",
            f"{humidity:.2f}",
            f"{pressure:.2f}",
            f"{altitude:.2f}",
            f"{gas}", # Gas is typically an integer/long resistance value
        ]

        # 4. Log to file
        with open(LOG_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(data_row)

        # 5. Print to console for monitoring (optional)
        print(f"[{timestamp}] Temp: {temperature:.2f} C | Hum: {humidity:.2f} % | Pres: {pressure:.2f} hPa | Gas: {gas} ohms")

        # 6. Wait for the next log interval
        time.sleep(LOG_INTERVAL_SECONDS)

except KeyboardInterrupt:
    print("\nLogging stopped by user.")
except Exception as e:
    print(f"\nAn error occurred: {e}")
finally:
    print(f"Sensor data saved to {LOG_FILE}.")
    print(f"Images saved to {LOG_DIR}.")