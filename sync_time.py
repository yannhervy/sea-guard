import subprocess
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# Set time using ntpdate (must be installed)
def sync_time():
    try:
        # Sync system time using ntpdate and pool.ntp.org
        subprocess.run(["sudo", "ntpdate", "-u", "pool.ntp.org"], check=True)
        print("System time successfully synced to UTC.")
    except FileNotFoundError:
        print("Error: 'ntpdate' is not installed. Please install it and try again.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print("Time sync failed:", e)
        sys.exit(1)

if __name__ == "__main__":
    sync_time()
