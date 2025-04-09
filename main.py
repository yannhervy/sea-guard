import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import subprocess
import signal
from datetime import datetime, timedelta, timezone
import time
import threading
import socket
import platform

scripts = [
    "bot.py",
    "picturemanager.py",
    "pir_sensor.py",
    "controller.py",
    "camera.py",  # Added camera script
    "bot_sub_pub.py",  # Added bot_publisher script
    # "intercept-all-mqtt.py"
]

COLORS = [
    "\033[96m",  # Cyan
    "\033[95m",  # Magenta
    "\033[93m",  # Yellow
    "\033[92m",  # Green
    "\033[94m",  # Blue
    "\033[91m",  # Red
]

RESET = "\033[0m"
log_dir = "logs"
processes = []

def setup_logging():
    """Set up logging to both a file and standard output."""
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "main.log")
    logger = logging.getLogger("main")
    logger.setLevel(logging.INFO)

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # Stream handler (standard output)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(stream_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger

# Initialize the logger
logger = setup_logging()

# Check if internet is available
def has_internet(timeout=3) -> bool:
    try:
        # Försök göra en DNS-lookup
        socket.setdefaulttimeout(timeout)
        socket.gethostbyname("pool.ntp.org")
        # Och sen även testa TCP-anslutning till IP
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except socket.error:
        return False

def wait_for_internet(check_interval=600):
    fast_retry_duration = 60  # sekunder
    start_time = time.time()
    while not has_internet():
        logger.info("No internet. Retrying soon...")
        if time.time() - start_time < fast_retry_duration:
            time.sleep(5)  # snabba retry första 60 sekunder
        else:
            time.sleep(check_interval)
    logger.info("Internet is available.")

def sync_system_time(max_attempts=5, delay=5):
    logger.info("Syncing system time to UTC...")
    for attempt in range(max_attempts):
        result = subprocess.run(["sudo", "ntpdate", "-u", "pool.ntp.org"])
        if result.returncode == 0:
            logger.info("Time sync completed.")
            return
        logger.error(f"Time sync failed (attempt {attempt + 1}/{max_attempts}). Retrying in {delay} sec...")
        time.sleep(delay)
    logger.error("Time sync failed too many times, aborting startup.")
    sys.exit(1)

def ensure_log_dir():
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

def get_log_path(script_name):
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    script_base = os.path.splitext(os.path.basename(script_name))[0]
    return os.path.join(log_dir, f"{date_str}_{script_base}.log")

def stream_output(process, log_file, script_name, color):
    for line in iter(process.stdout.readline, b''):
        decoded = line.decode("utf-8", errors="replace").rstrip()
        timestamp = datetime.now().strftime("%H:%M:%S")
        terminal_line = f"{color}[{timestamp}] [{script_name}]{RESET} {decoded}"
        print(terminal_line)
        log_file.write(f"[{timestamp}] [{script_name}] {decoded}\n")
        log_file.flush()

def start_all():
    ensure_log_dir()
    # Determine the Python interpreter from the virtual environment
    venv_python = os.path.join("venv", "bin", "python") if platform.system() != "Windows" else os.path.join("venv", "Scripts", "python.exe")
    for i, script in enumerate(scripts):
        log_path = get_log_path(script)
        log_file = open(log_path, "a")
        logger.info(f"Launching {script} → logging to {log_path}")

        if platform.system() == "Windows":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            p = subprocess.Popen(
                [venv_python, script],  # Use the virtual environment's Python
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=creationflags
            )
        else:
            p = subprocess.Popen(
                [venv_python, script],  # Use the virtual environment's Python
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid
            )

        color = COLORS[i % len(COLORS)]
        thread = threading.Thread(target=stream_output, args=(p, log_file, script, color), daemon=True)
        thread.start()
        processes.append((p, log_file))

def terminate_all():
    logger.info("Shutting down all subprocesses...")
    for p, log_file in processes:
        try:
            if platform.system() == "Windows":
                p.terminate()
            else:
                os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        except Exception as e:
            logger.error(f"Failed to terminate {p.pid}: {e}")
        log_file.close()
    processes.clear()

def signal_handler(sig, frame):
    terminate_all()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main_loop():
    while True:
        wait_for_internet()
        sync_system_time()
        logger.info("Starting all subprocesses...")
        start_all()

        while True:
            time.sleep(600)  # Check every 10 minutes
            if not has_internet():
                logger.info("Lost internet connection. Killing subprocesses and waiting...")
                terminate_all()
                break  # Break out of inner loop, go back to waiting for internet

if __name__ == "__main__":
    main_loop()
