import time
import board
import adafruit_bme680
import csv
import os
import sys
import logging
from datetime import datetime
import app.epaper_display.epd_module as epd_module


# Import the display module
try:
    import epd_module as epd_display
except ImportError as e:
    print(f"Failed to import epd_module.py. Display will be disabled. Error: {e}")
    epd_display = None # Set to None if import fails

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

    # Initialize EPD only if the module was imported successfully
    epd_kit = None
    if epd_display:
        epd_kit = epd_display.initialize_epd_and_fonts()
        if epd_kit is None and epd_display.EPD_DRIVER_LOADED:
            print("Fatal: EPD failed to initialize. Disabling display updates.")
            global epd_display
            epd_display = None
            
    print(f"\nBME680 logging started. Readings every {LOG_INTERVAL_SECONDS} seconds.")

    try:
        while True:
            temperature = bme680.temperature
            humidity = bme680.relative_humidity
            pressure = bme680.pressure
            gas = bme680.gas
            altitude = bme680.altitude

            if gas is None:
                time.sleep(1) 
                continue
            
            # --- Sensor Ready: Log and Display ---
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data_row = [timestamp, f"{temperature:.2f}", f"{humidity:.2f}", f"{pressure:.2f}", f"{altitude:.2f}", f"{gas}"]

            # 1. Log to file
            with open(LOG_FILE, 'a', newline='') as f:
                csv.writer(f).writerow(data_row)

            # 2. Update display
            if epd_display and epd_kit is not None:
                epd_display.update_sensor_display(epd_kit, temperature, humidity, pressure, gas)

            print(f"[{timestamp}] Temp: {temperature:.2f} C | Hum: {humidity:.2f} % | Pres: {pressure:.2f} hPa | Gas: {gas} ohms")

            time.sleep(LOG_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\nLogging stopped by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        logging.exception("Unhandled error in main loop.")
    finally:
        # 3. Cleanup EPD
        if epd_display and epd_kit is not None:
            epd_display.cleanup_epd(epd_kit)
        print(f"Data saved to {LOG_FILE}.")

if __name__ == "__main__":
    main_loop()