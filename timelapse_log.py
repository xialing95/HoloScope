import time
import bme680 # For BME680 sensor
from picamera2 import Picamera2 # For camera
import pandas as pd # For CSV logging
from datetime import datetime
import os # For file path management
import threading # For concurrent execution (optional, but good practice)

# --- Configuration ---
CSV_LOG_INTERVAL = 10  # Seconds between sensor readings and logging
DNG_TIMELAPSE_INTERVAL = 30  # Seconds between image captures
DNG_EXPOSURE_VALUE = 500  # Requested exposure value
CSV_FILENAME = "sensor_log.csv"
DNG_DIRECTORY = "timelapse_dng"

# --- Global Variables for Timing ---
last_log_time = time.monotonic()
last_dng_time = time.monotonic()

# --- Setup Functions ---
def setup_bme680():
    """Initializes the BME680 sensor."""
    try:
        # Pimoroni BME680 library uses the I2C address for initialization
        sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
    except IOError:
        # Try secondary address if the primary fails
        sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

    # Set oversampling and filter settings
    sensor.set_humidity_oversample(bme680.OS_2X)
    sensor.set_pressure_oversample(bme680.OS_4X)
    sensor.set_temperature_oversample(bme680.OS_8X)
    sensor.set_filter(bme680.FILTER_SIZE_3)
    # Set the gas heater profile for IAQ calculation (optional but good practice)
    sensor.set_gas_heater_profile(320, 150) # 320°C for 150ms
    
    # Start the sensor measurement
    print("BME680 setup complete. Heating up for first measurement...")
    # Wait for the first reading to be ready and gas resistance to stabilize
    time.sleep(1.0)
    
    return sensor

def setup_picam2():
    """Initializes and configures the Picamera2 for DNG capture."""
    picam2 = Picamera2()
    
    # Configure for Still Capture with RAW (DNG) output
    # The 'raw' dictionary requests a raw stream (needed for DNG)
    capture_config = picam2.create_still_configuration(
        main={"size": (3280, 2464)}, # Use a common resolution, adjust as needed
        raw={}, 
        controls={"ExposureTime": DNG_EXPOSURE_VALUE}
    )
    
    picam2.configure(capture_config)
    picam2.start()
    
    # Wait for the camera to start up and set controls
    time.sleep(2) 
    print("Picamera2 setup complete.")
    
    return picam2

def ensure_directory(path):
    """Creates a directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")

def init_csv(filename):
    """Creates the CSV file with headers if it doesn't exist."""
    if not os.path.exists(filename):
        header = "timestamp,temp_C,humidity_perc,pressure_hPa\n"
        with open(filename, 'w') as f:
            f.write(header)
        print(f"Created CSV file with header: {filename}")

# --- Core Functions ---
def log_sensor_data(sensor, filename):
    """Reads BME680 data and appends it to a CSV file."""
    if sensor.get_sensor_data() and sensor.data.heat_stable:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        temp = sensor.data.temperature
        humidity = sensor.data.humidity
        pressure = sensor.data.pressure
        
        # Format the data line
        data_line = f"{timestamp},{temp:.2f},{humidity:.2f},{pressure:.2f}\n"

        # Append to CSV
        with open(filename, 'a') as f:
            f.write(data_line)
        
        print(f"Logged sensor data: T={temp:.1f}C, H={humidity:.1f}%, P={pressure:.1f}hPa")
    else:
        # Sensor data not yet available or stable
        print("BME680 data not stable yet.")

def capture_dng(picam2, directory):
    """Captures a DNG image with the specified configuration."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(directory, f"timelapse_{timestamp}.dng")
    
    try:
        # Capture a raw image (DNG) using the configured settings
        # Picamera2 saves DNG automatically when raw stream is configured and 
        # the file extension is .dng
        picam2.capture_file(filepath)
        print(f"Captured DNG image: {filepath}")
    except Exception as e:
        print(f"Error capturing DNG: {e}")

# --- Main Loop ---
def main():
    global last_log_time, last_dng_time
    
    # 1. Setup
    ensure_directory(DNG_DIRECTORY)
    init_csv(CSV_FILENAME)
    
    bme_sensor = setup_bme680()
    picam = setup_picam2()
    
    try:
        print("\n--- Starting Combined Logger and Timelapse ---")
        while True:
            current_time = time.monotonic()
            
            # Check for Sensor Logging (Every 10 seconds)
            if current_time - last_log_time >= CSV_LOG_INTERVAL:
                log_sensor_data(bme_sensor, CSV_FILENAME)
                last_log_time = current_time
            
            # Check for DNG Timelapse (Every 30 seconds)
            if current_time - last_dng_time >= DNG_TIMELAPSE_INTERVAL:
                # Capture DNG (already configured with DNG_EXPOSURE_VALUE=500)
                capture_dng(picam, DNG_DIRECTORY)
                last_dng_time = current_time
                
            # Sleep for a short, non-blocking time to keep both loops running close to schedule
            # This value should be less than the smallest interval (10s)
            time.sleep(1) 
            
    except KeyboardInterrupt:
        print("\n--- Script Stopped by User ---")
    finally:
        # Clean up
        picam.stop()
        print("Picamera2 stopped. Cleanup complete.")

if __name__ == "__main__":
    main()