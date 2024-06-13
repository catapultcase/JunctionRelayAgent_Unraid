import os
import psutil
import json
import logging
import threading
import time
from flask import Flask, jsonify, request, abort

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

REFRESH_RATE = 5  # Refresh rate in seconds
WEB_SERVER_PORT = int(os.getenv('WEB_SERVER_PORT', 5000))  # Default to 5000 if not set
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')  # Get the access token if set

sensors_data = []

def get_system_sensors():
    sensors = []

    # CPU usage per core
    for i, percentage in enumerate(psutil.cpu_percent(percpu=True)):
        sensors.append({
            "Text": f"CPU Core {i} Load",
            "Type": "Load",
            "Value": str(percentage),
            "SensorId": f"cpu_core_{i}_load"
        })

    # CPU temperatures
    if hasattr(psutil, "sensors_temperatures"):
        temps = psutil.sensors_temperatures()
        for name, entries in temps.items():
            for entry in entries:
                sensors.append({
                    "Text": f"{name} {entry.label or 'Temperature'}",
                    "Type": "Temperature",
                    "Value": str(entry.current),
                    "SensorId": f"{name}_{entry.label or 'temperature'}"
                })

    # Memory usage
    mem = psutil.virtual_memory()
    sensors.append({
        "Text": "Memory Usage",
        "Type": "Memory",
        "Value": str(mem.percent),
        "SensorId": "memory_usage"
    })

    # Swap usage
    swap = psutil.swap_memory()
    sensors.append({
        "Text": "Swap Usage",
        "Type": "Memory",
        "Value": str(swap.percent),
        "SensorId": "swap_usage"
    })

    # Disk usage
    for part in psutil.disk_partitions():
        usage = psutil.disk_usage(part.mountpoint)
        sensors.append({
            "Text": f"Disk {part.device} Usage",
            "Type": "Disk",
            "Value": str(usage.percent),
            "SensorId": f"disk_{part.device.replace('/', '_')}_usage"
        })

    # Network usage
    net_io = psutil.net_io_counters(pernic=True)
    for interface, stats in net_io.items():
        sensors.append({
            "Text": f"Bytes Sent on {interface}",
            "Type": "Network",
            "Value": str(stats.bytes_sent),
            "SensorId": f"net_{interface}_bytes_sent"
        })
        sensors.append({
            "Text": f"Bytes Received on {interface}",
            "Type": "Network",
            "Value": str(stats.bytes_recv),
            "SensorId": f"net_{interface}_bytes_recv"
        })
        sensors.append({
            "Text": f"Packets Sent on {interface}",
            "Type": "Network",
            "Value": str(stats.packets_sent),
            "SensorId": f"net_{interface}_packets_sent"
        })
        sensors.append({
            "Text": f"Packets Received on {interface}",
            "Type": "Network",
            "Value": str(stats.packets_recv),
            "SensorId": f"net_{interface}_packets_recv"
        })

    return sensors

def update_system_info():
    global sensors_data

    sensors_data = get_system_sensors()

    logging.info("Initial sensor detection:")
    for sensor in sensors_data:
        logging.info(f"Name: {sensor['Text']}, Value: {sensor['Value']}, SensorId: {sensor['SensorId']}, Type: {sensor['Type']}")

    while True:
        sensors_data = get_system_sensors()
        logging.info("Sensor data refresh completed")
        time.sleep(REFRESH_RATE)

@app.route('/data.json')
def data_json():
    # Check for access token
    if ACCESS_TOKEN:
        token = request.headers.get('Authorization')
        if not token or token != f"Bearer {ACCESS_TOKEN}":
            abort(401)  # Unauthorized if token is missing or incorrect

    return jsonify(sensors_data)

if __name__ == '__main__':
    update_thread = threading.Thread(target=update_system_info)
    update_thread.daemon = True
    update_thread.start()
    app.run(host='0.0.0.0', port=WEB_SERVER_PORT)
