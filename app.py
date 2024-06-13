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
        children = []

        # Get CPU load for each core
        cpu_loads = psutil.cpu_percent(interval=1, percpu=True)
        cpu_children = []
        for i, load in enumerate(cpu_loads):
            cpu_children.append({
                "Text": f"CPU Core {i} Load",
                "Type": "Load",
                "Value": str(load),
                "SensorId": f"cpu_core_{i}_load"
            })
        
        # Get CPU temperature
        temperatures = psutil.sensors_temperatures()
        if 'coretemp' in temperatures:
            cpu_temp = temperatures['coretemp'][0].current
            cpu_children.append({
                "Text": "CPU Temperature",
                "Type": "Temperature",
                "Value": str(cpu_temp),
                "SensorId": "cpu_temperature"
            })

        children.append({
            "Text": "CPU",
            "Children": cpu_children
        })

        # Get memory usage
        memory = psutil.virtual_memory()
        children.append({
            "Text": "Memory",
            "Children": [
                {
                    "Text": "Memory Usage",
                    "Type": "Memory",
                    "Value": str(memory.percent),
                    "SensorId": "memory_usage"
                },
                {
                    "Text": "Swap Usage",
                    "Type": "Memory",
                    "Value": str(psutil.swap_memory().percent),
                    "SensorId": "swap_usage"
                }
            ]
        })

        # Get disk usage for all mounted partitions
        disk_partitions = psutil.disk_partitions()
        disk_children = []
        for partition in disk_partitions:
            usage = psutil.disk_usage(partition.mountpoint)
            disk_children.append({
                "Text": f"Disk {partition.device} Usage",
                "Type": "Disk",
                "Value": str(usage.percent),
                "SensorId": f"disk_{partition.device}_usage"
            })
        
        children.append({
            "Text": "Disk",
            "Children": disk_children
        })

        # Get network usage for all interfaces
        net_io = psutil.net_io_counters(pernic=True)
        net_children = []
        for iface, counters in net_io.items():
            net_children.append({
                "Text": f"Interface {iface}",
                "Type": "Network",
                "Children": [
                    {
                        "Text": "Bytes Sent",
                        "Type": "Network",
                        "Value": str(counters.bytes_sent),
                        "SensorId": f"net_{iface}_bytes_sent"
                    },
                    {
                        "Text": "Bytes Received",
                        "Type": "Network",
                        "Value": str(counters.bytes_recv),
                        "SensorId": f"net_{iface}_bytes_recv"
                    },
                    {
                        "Text": "Packets Sent",
                        "Type": "Network",
                        "Value": str(counters.packets_sent),
                        "SensorId": f"net_{iface}_packets_sent"
                    },
                    {
                        "Text": "Packets Received",
                        "Type": "Network",
                        "Value": str(counters.packets_recv),
                        "SensorId": f"net_{iface}_packets_recv"
                    }
                ]
            })
        
        children.append({
            "Text": "Network",
            "Children": net_children
        })

        # Construct the system information JSON
        system_info = {
            "DataSourceId": 1,
            "DataSourceName": "Unraid",
            "Children": [
                {
                    "Text": "System Information",
                    "Children": children
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
