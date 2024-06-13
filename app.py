import json
import psutil
from flask import Flask, request

app = Flask(__name__)

def get_system_info():
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
    info = {
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
    return info

@app.route('/system-info', methods=['GET'])
def system_info():
    info = get_system_info()
    return json.dumps(info)

@app.route('/data.json', methods=['GET'])
def data():
    info = get_system_info()
    return json.dumps(info)

@app.route('/receive-data', methods=['POST'])
def receive_data():
    data = request.json
    # Process received data as needed
    return 'Data received successfully', 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
