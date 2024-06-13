import json
import random
from flask import Flask, request

app = Flask(__name__)

def get_fake_system_info():
    # Generate fake CPU load value (between 0 and 100)
    cpu_load = str(random.randint(0, 100))

    # Generate fake memory usage value (between 0 and 100)
    memory_usage = str(random.randint(0, 100))

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
                                        "Value": cpu_load,
                                        "SensorId": "cpu_load"
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
                                        "Value": memory_usage,
                                        "SensorId": "memory_usage"
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
    info = get_fake_system_info()
    return json.dumps(info)

@app.route('/data.json', methods=['GET'])
def data():
    info = get_fake_system_info()
    return json.dumps(info)

@app.route('/receive-data', methods=['POST'])
def receive_data():
    data = request.json
    # Process received data as needed
    return 'Data received successfully', 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
