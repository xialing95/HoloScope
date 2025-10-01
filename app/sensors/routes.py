from flask import render_template, request, jsonify
from . import sensors_bp
import time
# import board
# import adafruit_bme680
import json
import os
import threading

# Define the directory where logs will be saved
# Get the path to the user's home directory.
home_dir = os.path.expanduser('~')
# Define the full path for the new directory.
LOG_DIR = os.path.join(home_dir, "capture_image")
# Create the directories if they do not exist
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Global variables for sensor and status
bme680 = None
bme680_initialized = False

# Function to initialize or re-initialize the BME680 sensor
def initialize_bme680():
    global bme680, bme680_initialized
    try:
        i2c = board.I2C()
        bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)
        bme680.sea_level_pressure = 1013.25
        bme680_initialized = True
        return True, "BME680 sensor initialized successfully."
    except Exception as e:
        bme680_initialized = False
        return False, f"Error initializing BME680 sensor: {e}"

# Initial sensor setup on app start
success, message = initialize_bme680()
if not success:
    print(message)

# This route serves the initial HTML page
@sensors_bp.route('/')
def index():
    return render_template('sensors.html', temp='...', humidity='...', pressure='...')

# This new route provides the sensor data as JSON
@sensors_bp.route('/sensor_data')
def get_sensor_data():
    if not bme680_initialized:
        return jsonify({
            "status": "error", 
            "message": "BME680 sensor not initialized."
            })
    
    data = {
        "temperature": f'{bme680.temperature:.2f}',
        "humidity": f'{bme680.relative_humidity:.2f}',
        "pressure": f'{bme680.pressure:.2f}'
    }
    return jsonify(data)

# This new route resets the I2C bus and sensor
@sensors_bp.route('/reset_i2c', methods=['POST'])
def reset_i2c():
    print("Resetting I2C bus and BME680 sensor...")
    success, message = initialize_bme680()
    if success:
        return jsonify({
            "status": "success", 
            "message": "I2C bus and sensor reset successfully."
            })
    else:
        return jsonify({
            "status": "error", 
            "message": f"Failed to reset I2C bus: {message}"
            })

# This is the function that will run in a separate thread
def log_sensor_data(duration, interval):
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

# This route now starts the logging in a separate thread and returns immediately
@sensors_bp.route('/startEnvSensor', methods=['POST'])
def start_env_sensor():
    if not bme680_initialized:
        return jsonify({
            "status": "error", 
            "message": "BME680 sensor not initialized."
            })
    
    try:
        duration = int(request.form.get('sensor_duration', 60))
        interval = int(request.form.get('sensor_interval', 10))
    except (ValueError, TypeError):
        return jsonify({
            "status": "error", 
            "message": "Invalid duration or interval values."
            })

    logging_thread = threading.Thread(target=log_sensor_data, args=(duration, interval))
    logging_thread.start()
    
    return jsonify({
        "status": "success", 
        "message": "Environmental sensor log started in the background."
        })

# # This route stops the env sensors
# @sensors_bp.route('/stopEnvSensor', methods=['POST'])
# def stop_env_sensor():
#     global logging_stop_event
#     logging_stop_event.set() # Signal the thread to stop
#     return jsonify({"status": "success", "message": "Environmental sensor log stop signal sent."})