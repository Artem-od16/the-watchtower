import psutil
import requests
import time
import docker
import os
import logging
from prometheus_client import start_http_server, Counter, Gauge

# Configure logging for better visibility in Docker logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Prometheus Metrics
CHECKS_TOTAL = Counter('monitor_loop_iterations_total', 'Total number of monitoring loops')
PROMETHEUS_CPU_USAGE = Gauge('monitor_custom_cpu_usage', 'CPU usage measured by monitor.py')
CONTAINER_STATUS = Gauge('monitor_container_status', 'Status of docker containers', ['container_name'])

# Environment Variables
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CPU_THRESHOLD = float(os.getenv("CPU_THRESHOLD", 90.0))

# Docker Client Setup
try:
    client = docker.from_env()
    logger.info("Successfully connected to Docker socket.")
except Exception as e:
    logger.error(f"Failed to connect to Docker socket: {e}")
    client = None

def send_telegram_msg(text):
    if not TOKEN or not CHAT_ID:
        logger.warning("Telegram credentials not found in environment!")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
    except Exception as e:
        logger.error(f"Telegram Connection Error: {e}")

def monitor_system():
    logger.info("Monitoring started: CPU + Containers + Prometheus")
    send_telegram_msg("🛡️ <b>Watchtower: Monitoring is ONLINE</b> (Metrics enabled)")
    last_states = {}

    while True:
        try:
            CHECKS_TOTAL.inc()
            
            # CPU Monitoring
            cpu_usage = psutil.cpu_percent(interval=1)
            PROMETHEUS_CPU_USAGE.set(cpu_usage)
            
            if cpu_usage > CPU_THRESHOLD:
                send_telegram_msg(f"⚠️ <b>ALERT: High CPU Usage: {cpu_usage}%</b>")

            # Docker Containers Monitoring
            if client:
                containers = client.containers.list(all=True)
                for container in containers:
                    name = container.name
                    if name == "python-monitor": 
                        continue
                    
                    status = container.status
                    # Update Prometheus: 1 for running, 0 for everything else
                    val = 1 if status == 'running' else 0
                    CONTAINER_STATUS.labels(container_name=name).set(val)

                    # State change detection
                    if name in last_states:
                        if status != 'running' and last_states[name] == 'running':
                            send_telegram_msg(f"🛑 <b>CRITICAL: {name}</b> is DOWN!")
                            logger.error(f"Container {name} is DOWN!")
                        elif status == 'running' and last_states[name] != 'running':
                            send_telegram_msg(f"✅ <b>FIXED: {name}</b> is back ONLINE.")
                            logger.info(f"Container {name} is back online.")
                    
                    last_states[name] = status

        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
        
        time.sleep(30)

if __name__ == "__main__":
    # Start Prometheus metrics server on port 8000
    try:
        start_http_server(8000)
        logger.info("Prometheus metrics server started on port 8000")
    except Exception as e:
        logger.error(f"Failed to start Prometheus server: {e}")
        
    monitor_system()