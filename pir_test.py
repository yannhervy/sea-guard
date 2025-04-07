import RPi.GPIO as GPIO
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# ----------- KONFIGURATION -----------
# Physical pin usage:
# - Pin 2: 5V Power (for powering the PIR sensor)
# - Pin 6: Ground (for grounding the PIR sensor)
# - Pin 11: GPIO 17 (used for detecting motion)

PIR_PIN = 17  # GPIO pin for the PIR sensor (physical pin 11)

# ----------- SETUP -----------
def setup_pir_sensor():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIR_PIN, GPIO.IN)
    print("PIR sensor initialized. Monitoring status...")

# ----------- MAIN LOOP -----------
def monitor_pir_sensor():
    try:
        while True:
            if GPIO.input(PIR_PIN):
                print("Status: Motion detected!")
            else:
                print("Status: No motion.")
            time.sleep(1)  # Check status every second
    except KeyboardInterrupt:
        print("\nExiting PIR test script...")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    setup_pir_sensor()
    monitor_pir_sensor()
