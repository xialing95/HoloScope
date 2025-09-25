from flask import render_template, request, jsonify
from . import sensors_bp
import time
import board
import adafruit_bme680
import json
import os

# Define the directory where logs will be saved
LOG_DIR = 'sensor_logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Initialize BME680 sensor
try:
    i2c = board.I2C()  # Use default I2C bus
    bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)
    
    # change this to match the sensor's data sheet
    bme680.sea_level_pressure = 1013.25
    bme680_initialized = True
except ValueError as e:
    print(f"Error initializing BME680 sensor: {e}")
    bme680_initialized = False
    
# Global variables for sensor data
temp = 0
humidity = 0
pressure = 0

# This route serves the initial HTML page
@sensors_bp.route('/')
def index():
    # Pass initial values, they will be updated by JavaScript
    return render_template('sensors.html', temp='...', humidity='...', pressure='...')
    
@sensors_bp.route('/reset_i2c', methods=['POST'])
def handle_post():
    if 'reset_i2c' in request.form:
        # Code to reset I2C bus can be added here
        print("I2C bus reset requested.")
    
    return index()

# This new route provides the sensor data as JSON
@sensors_bp.route('/sensor_data')
def get_sensor_data():
    if not bme680_initialized:
        return jsonify({"status": "error", "message": "BME680 sensor not initialized."})

    data = {
        "temperature": f'{bme680.temperature:.2f}',
        "humidity": f'{bme680.relative_humidity:.2f}',
        "pressure": f'{bme680.pressure:.2f}'
    }
    return jsonify(data)

@sensors_bp.route('/startEnvSensor', methods=['POST'])
def start_env_sensor():
    if not bme680_initialized:
        return jsonify({"status": "error", "message": "BME680 sensor not initialized."})
    
    try:
        duration = int(request.form.get('sensor_duration', 60))
        interval = int(request.form.get('sensor_interval', 10))
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Invalid duration or interval values."})
    
    start_time = time.time()
    log_data = []
    
    while (time.time() - start_time) < duration:
        log_entry = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "temperature": f'{bme680.temperature:.2f}',
            "humidity": f'{bme680.relative_humidity:.2f}',
            "pressure": f'{bme680.pressure:.2f}'
        }
        log_data.append(log_entry)
        print(f"Logging data: {log_entry}")
        time.sleep(interval)

    # Generate a filename with a timestamp
    filename = f"sensor_log_{time.strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(LOG_DIR, filename)
    
    # Save the log data to a JSON file
    try:
        with open(filepath, 'w') as f:
            json.dump(log_data, f, indent=4)
        print(f"Environmental sensor log saved to {filepath}")
    except IOError as e:
        print(f"Error saving log file: {e}")
        return jsonify({"status": "error", "message": "Failed to save log file."})
    
    return jsonify({"status": "success", "message": "Environmental sensor log finished and saved.", "filename": filename, "data": log_data})