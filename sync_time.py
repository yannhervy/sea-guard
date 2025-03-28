import subprocess
import sys

# Set time using ntpdate (must be installed)
def sync_time():
    try:
        # Sync system time using ntpdate and pool.ntp.org
        subprocess.run(["sudo", "ntpdate", "-u", "pool.ntp.org"], check=True)
        print("System time successfully synced to UTC.")
    except subprocess.CalledProcessError as e:
        print("Time sync failed:", e)
        sys.exit(1)

if __name__ == "__main__":
    sync_time()
