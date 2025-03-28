import sys
import os
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
    "pir_sensor.py",  # Added PIR sensor script
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

# Check if internet is available
def has_internet(host="8.8.8.8", port=53, timeout=3) -> bool:
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

def wait_for_internet(check_interval=600):
    while not has_internet():
        print(f"[{datetime.now(timezone.utc).isoformat()}] No internet. Retrying in {check_interval // 60} minutes...")
        time.sleep(check_interval)
    print(f"[{datetime.now(timezone.utc).isoformat()}] Internet is available.")

def sync_system_time():
    print("Syncing system time to UTC...")
    if platform.system() == "Windows":
        print("Time sync is not supported on Windows. Skipping...")
        return

    result = subprocess.run(["sudo", "python3", "sync_time.py"])
    if result.returncode != 0:
        print("Time sync failed, aborting startup.")
        sys.exit(1)
    print("Time sync completed.\n")

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
        print(f"[{datetime.now(timezone.utc).isoformat()}] Launching {script} → logging to {log_path}")

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
    print(f"[{datetime.now(timezone.utc).isoformat()}] Shutting down all subprocesses...")
    for p, log_file in processes:
        try:
            if platform.system() == "Windows":
                p.terminate()
            else:
                os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        except Exception as e:
            print(f"Failed to terminate {p.pid}: {e}")
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
        print(f"[{datetime.now(timezone.utc).isoformat()}] Starting all subprocesses...")
        start_all()

        while True:
            time.sleep(600)  # Check every 10 minutes
            if not has_internet():
                print(f"[{datetime.now(timezone.utc).isoformat()}] Lost internet connection. Killing subprocesses and waiting...")
                terminate_all()
                break  # Break out of inner loop, go back to waiting for internet

if __name__ == "__main__":
    main_loop()
