import os
import psutil
import json
import logging
import threading
import time
from collections import deque
from flask import Flask, jsonify, request, abort
from datetime import timedelta
import subprocess
import shutil  # Import shutil

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Read the refresh rate from environment variable, default to 5 seconds if not set
REFRESH_RATE = int(os.getenv('REFRESH_RATE', 5))
WEB_SERVER_PORT = int(os.getenv('WEB_SERVER_PORT', 5000))  # Default to 5000 if not set
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')  # Get the access token if set
LOGGING_HISTORY_TIMEFRAME = int(os.getenv('LOGGING_HISTORY_TIMEFRAME', 1))  # Default to 1 hour if not set

sensors_data = []
disk_io_previous = {}
disk_io_max = {}
disk_io_history = {}

def get_system_sensors():
    global disk_io_previous, disk_io_max, disk_io_history
    sensors = []
    current_time = time.time()

    # CPU usage per core
    for i, percentage in enumerate(psutil.cpu_percent(percpu=True)):
        sensors.append({
            "Text": f"CPU Core {i} Load",
            "Type": "Load",
            "Value": str(percentage),
            "SensorId": f"cpu_core_{i}_load",
            "ComponentName": "CPU"
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
                    "SensorId": f"{name}_{entry.label or 'temperature'}",
                    "ComponentName": "CPU"
                })

    # Memory usage
    mem = psutil.virtual_memory()
    sensors.append({
        "Text": "Memory Usage",
        "Type": "Memory",
        "Value": str(mem.percent),
        "SensorId": "memory_usage",
        "ComponentName": "Memory"
    })

    # Swap usage
    swap = psutil.swap_memory()
    sensors.append({
        "Text": "Swap Usage",
        "Type": "Memory",
        "Value": str(swap.percent),
        "SensorId": "swap_usage",
        "ComponentName": "Memory"
    })

    # Disk usage and I/O statistics
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            sensors.append({
                "Text": f"Disk {part.device} Usage",
                "Type": "Disk",
                "Value": str(usage.percent),
                "SensorId": f"disk_{part.device.replace('/', '_')}_usage",
                "ComponentName": "Disk"
            })
        except PermissionError:
            logging.warning(f"Permission error accessing disk usage for {part.device}")

    disk_io = psutil.disk_io_counters(perdisk=True)
    for disk, stats in disk_io.items():
        if disk not in disk_io_previous:
            disk_io_previous[disk] = stats
            disk_io_max[disk] = {'read_speed': 0, 'write_speed': 0}
            disk_io_history[disk] = deque(maxlen=int((LOGGING_HISTORY_TIMEFRAME * 3600) / REFRESH_RATE))

        prev_stats = disk_io_previous[disk]
        read_speed = (stats.read_bytes - prev_stats.read_bytes) / REFRESH_RATE
        write_speed = (stats.write_bytes - prev_stats.write_bytes) / REFRESH_RATE

        disk_io_previous[disk] = stats
        disk_io_history[disk].append((current_time, read_speed, write_speed))

        max_read_speed = max([data[1] for data in disk_io_history[disk]])
        max_write_speed = max([data[2] for data in disk_io_history[disk]])

        sensors.append({
            "Text": f"Disk {disk} Current Read Speed",
            "Type": "DiskIO",
            "Value": str(read_speed),
            "SensorId": f"disk_{disk.replace('/', '_')}_current_read_speed",
            "ComponentName": "Disk"
        })
        sensors.append({
            "Text": f"Disk {disk} Current Write Speed",
            "Type": "DiskIO",
            "Value": str(write_speed),
            "SensorId": f"disk_{disk.replace('/', '_')}_current_write_speed",
            "ComponentName": "Disk"
        })
        sensors.append({
            "Text": f"Disk {disk} Max Read Speed",
            "Type": "DiskIO",
            "Value": str(max_read_speed),
            "SensorId": f"disk_{disk.replace('/', '_')}_max_read_speed",
            "ComponentName": "Disk"
        })
        sensors.append({
            "Text": f"Disk {disk} Max Write Speed",
            "Type": "DiskIO",
            "Value": str(max_write_speed),
            "SensorId": f"disk_{disk.replace('/', '_')}_max_write_speed",
            "ComponentName": "Disk"
        })

    # Network usage
    net_io = psutil.net_io_counters(pernic=True)
    for interface, stats in net_io.items():
        sensors.append({
            "Text": f"Bytes Sent on {interface}",
            "Type": "Network",
            "Value": str(stats.bytes_sent),
            "SensorId": f"net_{interface}_bytes_sent",
            "ComponentName": "Network"
        })
        sensors.append({
            "Text": f"Bytes Received on {interface}",
            "Type": "Network",
            "Value": str(stats.bytes_recv),
            "SensorId": f"net_{interface}_bytes_recv",
            "ComponentName": "Network"
        })
        sensors.append({
            "Text": f"Packets Sent on {interface}",
            "Type": "Network",
            "Value": str(stats.packets_sent),
            "SensorId": f"net_{interface}_packets_sent",
            "ComponentName": "Network"
        })
        sensors.append({
            "Text": f"Packets Received on {interface}",
            "Type": "Network",
            "Value": str(stats.packets_recv),
            "SensorId": f"net_{interface}_packets_recv",
            "ComponentName": "Network"
        })

    # GPU usage (Example: Using NVIDIA-SMI for NVIDIA GPUs)
    if shutil.which("nvidia-smi") is not None:
        try:
            gpu_stats = subprocess.check_output(['nvidia-smi', '--query-gpu=utilization.gpu,temperature.gpu', '--format=csv,noheader,nounits'])
            gpu_stats = gpu_stats.decode('utf-8').strip().split('\n')
            for idx, stat in enumerate(gpu_stats):
                gpu_util, gpu_temp = stat.split(',')
                sensors.append({
                    "Text": f"GPU {idx} Utilization",
                    "Type": "GPU",
                    "Value": str(gpu_util.strip()),
                    "SensorId": f"gpu_{idx}_utilization",
                    "ComponentName": "GPU"
                })
                sensors.append({
                    "Text": f"GPU {idx} Temperature",
                    "Type": "GPU",
                    "Value": str(gpu_temp.strip()),
                    "SensorId": f"gpu_{idx}_temperature",
                    "ComponentName": "GPU"
                })
        except Exception as e:
            logging.warning(f"Failed to get GPU stats: {e}")
    else:
        logging.warning("nvidia-smi command not found. Skipping GPU stats.")

    # System uptime
    try:
        uptime_seconds = float(subprocess.check_output(['cat', '/proc/uptime']).decode().split()[0])
        uptime_string = str(timedelta(seconds=uptime_seconds))
        sensors.append({
            "Text": "System Uptime",
            "Type": "System",
            "Value": uptime_string,
            "SensorId": "system_uptime",
            "ComponentName": "System"
        })
    except Exception as e:
        logging.warning(f"Failed to get system uptime: {e}")

    # Network latency (Ping example)
    if shutil.which("ping") is not None:
        try:
            hostname = "google.com"  # You can change this to any reliable host
            ping_response = subprocess.check_output(['ping', '-c', '1', hostname]).decode()
            latency = float([line for line in ping_response.split('\n') if 'time=' in line][0].split('time=')[1].split(' ')[0])
            sensors.append({
                "Text": f"Latency to {hostname}",
                "Type": "Network",
                "Value": str(latency),
                "SensorId": f"latency_{hostname}",
                "ComponentName": "Network"
            })
        except Exception as e:
            logging.warning(f"Failed to get network latency: {e}")
    else:
        logging.warning("ping command not found. Skipping network latency.")

    return sensors

def update_system_info():
    global sensors_data

    sensors_data = get_system_sensors()

    logging.info("Initial sensor detection:")
    for sensor in sensors_data:
        logging.info(f"Name: {sensor['Text']}, Value: {sensor['Value']}, SensorId: {sensor['SensorId']}, Type: {sensor['Type']}, ComponentName: {sensor['ComponentName']}")

    while True:
        sensors_data = get_system_sensors()
        logging.info(f"Sensor data refresh completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info(f"Sleeping for {REFRESH_RATE} seconds before next refresh")
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
    logging.info(f"Starting server with refresh rate: {REFRESH_RATE} seconds")
    update_thread = threading.Thread(target=update_system_info)
    update_thread.daemon = True
    update_thread.start()
    app.run(host='0.0.0.0', port=WEB_SERVER_PORT)
