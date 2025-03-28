import os
import re
import json
import time
import threading
import logging
from datetime import datetime, timedelta
from pathlib import Path
import paho.mqtt.client as mqtt

# ----------- KONFIGURATION -----------

BASE_DIR = Path(__file__).parent.resolve()
PICTURE_FOLDER = BASE_DIR / 'pics'
LOG_FOLDER = BASE_DIR / 'logs'
LOG_FILE = LOG_FOLDER / 'picture_manager.log'

FILENAME_PATTERN = r'^(\d{4})-(\d{2})-(\d{2})_(\d{6})\.jpg$'
RETENTION_DAYS = 3

MQTT_BROKER = 'localhost'
MQTT_PORT = 1883
MQTT_TOPIC_GET = 'GET_LATEST_PICTURES_N'
MQTT_TOPIC_SEND = 'SEND_LATEST_PICTURES'

# ----------- LOGGNING -----------

def setup_logging():
    LOG_FOLDER.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()  # Konsolen
        ]
    )

setup_logging()
logger = logging.getLogger(__name__)

# ----------- BILDFUNKTIONER -----------

def delete_old_pictures():
    logger.info("Startar bildrensning...")

    if not PICTURE_FOLDER.exists():
        logger.warning(f"Katalogen '{PICTURE_FOLDER}' finns inte!")
        return

    files = os.listdir(PICTURE_FOLDER)
    now = datetime.now()
    cutoff_date = now - timedelta(days=RETENTION_DAYS)

    deleted_files = 0
    for file_name in files:
        match = re.match(FILENAME_PATTERN, file_name)
        if not match:
            continue

        year, month, day, time_str = match.groups()
        hour = time_str[:2]
        minute = time_str[2:4]
        second = time_str[4:6]

        try:
            file_datetime = datetime(
                int(year), int(month), int(day),
                int(hour), int(minute), int(second)
            )
        except ValueError as e:
            logger.error(f"Kunde inte tolka datum från '{file_name}': {e}")
            continue

        if file_datetime < cutoff_date:
            file_path = PICTURE_FOLDER / file_name
            try:
                file_path.unlink()
                deleted_files += 1
                logger.info(f"Raderade: {file_name}")
            except Exception as e:
                logger.error(f"Fel vid borttagning av '{file_name}': {e}")

    logger.info(f"Rensning klar. {deleted_files} filer borttagna.")

def get_latest_pictures(n):
    """Hämtar sökvägarna till de N senaste bilderna."""
    if not PICTURE_FOLDER.exists():
        logger.warning(f"Katalogen '{PICTURE_FOLDER}' finns inte!")
        return []

    files = os.listdir(PICTURE_FOLDER)
    picture_files = []

    for file_name in files:
        match = re.match(FILENAME_PATTERN, file_name)
        if not match:
            continue

        year, month, day, time_str = match.groups()
        hour = time_str[:2]
        minute = time_str[2:4]
        second = time_str[4:6]

        try:
            file_datetime = datetime(
                int(year), int(month), int(day),
                int(hour), int(minute), int(second)
            )
            file_path = str((PICTURE_FOLDER / file_name).resolve())
            picture_files.append((file_datetime, file_path))
        except ValueError:
            continue

    picture_files.sort(reverse=True, key=lambda x: x[0])
    latest_paths = [path for _, path in picture_files[:n]]

    logger.info(f"Hittade {len(latest_paths)} senaste bilder.")

    return latest_paths

# ----------- MQTT CALLBACKS -----------

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Ansluten till MQTT-broker.")
        client.subscribe(MQTT_TOPIC_GET)
    else:
        logger.error(f"Misslyckades att ansluta till MQTT, rc={rc}")

def on_message(client, userdata, msg):
    logger.info(f"Meddelande mottaget på ämnet '{msg.topic}': {msg.payload.decode()}")

    if msg.topic == MQTT_TOPIC_GET:
        try:
            payload = msg.payload.decode().strip()
            n = int(payload)
            logger.info(f"Hämtar de {n} senaste bilderna...")

            latest_pictures = get_latest_pictures(n)

            response_payload = json.dumps(latest_pictures)
            client.publish(MQTT_TOPIC_SEND, response_payload)
            logger.info(f"Skickade {len(latest_pictures)} bilder på ämnet '{MQTT_TOPIC_SEND}'.")
        except Exception as e:
            logger.error(f"Fel vid hantering av meddelande: {e}")

# ----------- TASK LOOPAR -----------

def run_daily_cleanup():
    while True:
        delete_old_pictures()
        logger.info("Väntar i 24 timmar till nästa rensning...")
        time.sleep(24 * 60 * 60)

def start_mqtt_client():
    client = mqtt.Client()

    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        logger.info(f"Ansluter till MQTT-broker på {MQTT_BROKER}:{MQTT_PORT}...")
    except Exception as e:
        logger.error(f"Misslyckades att ansluta till MQTT-broker: {e}")
        return

    client.loop_forever()

# ----------- MAIN -----------

if __name__ == "__main__":
    logger.info("Startar picture_manager.py")
    logger.info(f"Bildmapp: {PICTURE_FOLDER}")
    logger.info(f"Loggfil: {LOG_FILE}")

    cleanup_thread = threading.Thread(target=run_daily_cleanup, daemon=True)
    cleanup_thread.start()

    start_mqtt_client()
