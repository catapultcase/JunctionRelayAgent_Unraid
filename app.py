import os
import json
import psutil
import threading
import time
import logging
from flask import Flask, jsonify

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variable to store system info
system_info = {}

def update_system_info():
    global system_info
    while True:
        # Get CPU load
        cpu_load = psutil.cpu_percent(interval=1)

        # Get memory usage
        memory = psutil.virtual_memory()
        memory_usage = memory.percent

        # Get disk usage
        disk = psutil.disk_usage('/')
        disk_usage = disk.percent

        # Get CPU temperature
        temperatures = psutil.sensors_temperatures()
        cpu_temp = None
        if 'coretemp' in temperatures:
            cpu_temp = temperatures['coretemp'][0].current

        # Construct the system information JSON
        system_info = {
            "DataSourceId": 1,
            "DataSourceName": "Unraid",
            "Children": [
                {
                    "Text": "System Information",
                    "Children": [
                        {
                            "Text": "CPU",
                            "Children": [
                                {
                                    "Text": "Load",
                                    "Children": [
                                        {
                                            "Text": "CPU Load",
                                            "Type": "Load",
                                            "Value": str(cpu_load),
                                            "SensorId": "cpu_load"
                                        }
                                    ]
                                },
                                {
                                    "Text": "Temperature",
                                    "Children": [
                                        {
                                            "Text": "CPU Temperature",
                                            "Type": "Temperature",
                                            "Value": str(cpu_temp) if cpu_temp is not None else "N/A",
                                            "SensorId": "cpu_temperature"
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "Text": "Memory",
                            "Children": [
                                {
                                    "Text": "Usage",
                                    "Children": [
                                        {
                                            "Text": "Memory Usage",
                                            "Type": "Memory",
                                            "Value": str(memory_usage),
                                            "SensorId": "memory_usage"
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "Text": "Disk",
                            "Children": [
                                {
                                    "Text": "Usage",
                                    "Children": [
                                        {
                                            "Text": "Disk Usage",
                                            "Type": "Disk",
                                            "Value": str(disk_usage),
                                            "SensorId": "disk_usage"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        logging.debug("Sensor data refreshed")

        # Sleep for the refresh rate duration
        time.sleep(int(os.getenv('REFRESH_RATE', '60')))  # Refresh rate in seconds

@app.route('/system-info', methods=['GET'])
def system_info_route():
    return jsonify(system_info)

@app.route('/data.json', methods=['GET'])
def data():
    return jsonify(system_info)

@app.route('/receive-data', methods=['POST'])
def receive_data():
    data = request.json
    # Process received data as needed
    return 'Data received successfully', 200

if __name__ == "__main__":
    refresh_rate = int(os.getenv('REFRESH_RATE', '60'))  # Default refresh rate is 60 seconds
    threading.Thread(target=update_system_info, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
