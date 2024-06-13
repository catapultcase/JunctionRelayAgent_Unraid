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
        cpu_load = psutil.cpu_percent(interval=1, percpu=True)

        # Get memory usage
        memory = psutil.virtual_memory()
        memory_usage = memory.percent

        # Get swap memory usage
        swap = psutil.swap_memory()
        swap_usage = swap.percent

        # Get disk usage for all mounted partitions
        disk_partitions = psutil.disk_partitions()
        disk_usage = {}
        for partition in disk_partitions:
            usage = psutil.disk_usage(partition.mountpoint)
            disk_usage[partition.device] = usage.percent

        # Get CPU temperature
        temperatures = psutil.sensors_temperatures()
        cpu_temp = None
        if 'coretemp' in temperatures:
            cpu_temp = temperatures['coretemp'][0].current

        # Get network usage
        net_io = psutil.net_io_counters(pernic=True)
        network_usage = {}
        for iface, counters in net_io.items():
            network_usage[iface] = {
                'bytes_sent': counters.bytes_sent,
                'bytes_recv': counters.bytes_recv,
                'packets_sent': counters.packets_sent,
                'packets_recv': counters.packets_recv
            }

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
                                            "Text": f"CPU Core {i} Load",
                                            "Type": "Load",
                                            "Value": str(load),
                                            "SensorId": f"cpu_core_{i}_load"
                                        } for i, load in enumerate(cpu_load)
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
                                        },
                                        {
                                            "Text": "Swap Usage",
                                            "Type": "Memory",
                                            "Value": str(swap_usage),
                                            "SensorId": "swap_usage"
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "Text": "Disk",
                            "Children": [
                                {
                                    "Text": f"Disk {partition} Usage",
                                    "Type": "Disk",
                                    "Value": str(usage),
                                    "SensorId": f"disk_{partition}_usage"
                                } for partition, usage in disk_usage.items()
                            ]
                        },
                        {
                            "Text": "Network",
                            "Children": [
                                {
                                    "Text": f"Interface {iface}",
                                    "Type": "Network",
                                    "Children": [
                                        {
                                            "Text": "Bytes Sent",
                                            "Type": "Network",
                                            "Value": str(counters['bytes_sent']),
                                            "SensorId": f"net_{iface}_bytes_sent"
                                        },
                                        {
                                            "Text": "Bytes Received",
                                            "Type": "Network",
                                            "Value": str(counters['bytes_recv']),
                                            "SensorId": f"net_{iface}_bytes_recv"
                                        },
                                        {
                                            "Text": "Packets Sent",
                                            "Type": "Network",
                                            "Value": str(counters['packets_sent']),
                                            "SensorId": f"net_{iface}_packets_sent"
                                        },
                                        {
                                            "Text": "Packets Received",
                                            "Type": "Network",
                                            "Value": str(counters['packets_recv']),
                                            "SensorId": f"net_{iface}_packets_recv"
                                        }
                                    ]
                                } for iface, counters in network_usage.items()
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
