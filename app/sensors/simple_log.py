import time
import board
import adafruit_bme680
import csv
import os
import sys
import logging
from datetime import datetime
from typing import Optional, Tuple

# --- Path Setup for Module Import ---
# This block helps Python find the 'app' directory regardless of the execution context.
# Since bme_logger_main.py is now in 'app/sensors/', we go two levels up ('../../') 
# to find the main project root which contains the 'app' directory.
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, '..', '..') # Correct path for app/sensors/ location
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except:
    pass # Ignore path setup errors if running in an odd environment

# --- EPD Module Import and Availability Check ---
# Attempt to import the module from the specified path and alias it to epd_display.
try:
    import app.epaper_display.epd_module as epd_display
    
    # Check if the module internally flagged driver failure (Mock objects active)
    # EPD_DRIVER_LOADED is an attribute expected to be exposed by epd_module.py
    if not epd_display.EPD_DRIVER_LOADED:
        print("Warning: EPD module imported, but drivers/PIL failed internally. Display is mocked.")
        EPD_MODULE_AVAILABLE = False
    else:
        EPD_MODULE_AVAILABLE = True
        
except ImportError as e:
    # This message is shown if the module cannot be found or loaded.
    print(f"Failed to import EPD module from path 'app.epaper_display.epd_module': {e}.")
    epd_display = None
    EPD_MODULE_AVAILABLE = False


# --- Configuration ---
LOG_DIR = os.path.join(os.path.expanduser('~'), 'capture_image')
LOG_FILE = os.path.join(LOG_DIR, 'bme680_data.csv')
LOG_INTERVAL_SECONDS = 10 
SEA_LEVEL_HPA = 1013.25 

# --- Sensor Setup ---
try:
    i2c = board.I2C()
    bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c)
except Exception as e:
    print(f"Error initializing BME680 sensor: {e}")
    sys.exit(1)

bme680.sea_level_pressure = SEA_LEVEL_HPA
bme680.set_gas_heater(320, 150)

# --- File Setup (unchanged) ---
def initialize_log_file(filename):
    os.makedirs(LOG_DIR, exist_ok=True)
    if not os.path.exists(filename):
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            header = ['Timestamp', 'Temperature_C', 'Humidity_perc', 'Pressure_hPa', 'Altitude_m', 'Gas_resistance_ohms']
            writer.writerow(header)
            print(f"Created new log file: {filename} with header.")
    else:
        print(f"Appending to existing log file: {filename}.")

initialize_log_file(LOG_FILE)


# --- Main Logging Loop ---
def main_loop():
    """Main loop for reading BME680, logging data, and updating the display."""

    # 1. Initialize EPD Hardware
    epd_kit: Optional[Tuple] = None
    
    # Use a local flag to track if the display is connected and initialized successfully
    display_enabled = EPD_MODULE_AVAILABLE 

    if display_enabled:
        print("Attempting to initialize EPD hardware...")
        # epd_kit will contain (epd, HBlackimage, HRYimage, font_section) or None on failure
        epd_kit = epd_display.initialize_epd_and_fonts()
        
        if epd_kit is None:
            print("Fatal: EPD hardware initialization failed (e.g., bad wiring, SPI error). Disabling display updates.")
            # Set local flag to False to prevent display calls in the loop/finally block
            display_enabled = False
        else:
            print("EPD hardware initialized successfully.")
            
    print(f"\nBME680 logging started. Readings every {LOG_INTERVAL_SECONDS} seconds.")

    try:
        while True:
            temperature = bme680.temperature
            humidity = bme680.relative_humidity
            pressure = bme680.pressure
            gas = bme680.gas
            altitude = bme680.altitude

            # Ensure gas reading is available before logging/displaying
            if gas is None:
                time.sleep(1) 
                continue
            
            # --- Sensor Ready: Log and Display ---
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data_row = [timestamp, f"{temperature:.2f}", f"{humidity:.2f}", f"{pressure:.2f}", f"{altitude:.2f}", f"{gas}"]

            # 1. Log to file
            with open(LOG_FILE, 'a', newline='') as f:
                csv.writer(f).writerow(data_row)

            # 2. Update display: Check local flag and epd_kit presence
            if display_enabled and epd_kit is not None:
                # Calls update_sensor_display from the imported module
                epd_display.update_sensor_display(epd_kit, temperature, humidity, pressure, gas)

            print(f"[{timestamp}] Temp: {temperature:.2f} C | Hum: {humidity:.2f} % | Pres: {pressure:.2f} hPa | Gas: {gas} ohms")

            time.sleep(LOG_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\nLogging stopped by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        logging.exception("Unhandled error in main loop.")
    finally:
        # 3. Cleanup EPD: Only if initialization was successful
        if display_enabled and epd_kit is not None:
            epd_display.cleanup_epd(epd_kit)
        print(f"Data saved to {LOG_FILE}.")

if __name__ == "__main__":
    main_loop()