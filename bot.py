import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import logging
import asyncio
import signal
import json
import time  # Import time module for sleep
import psutil  # Import psutil to get process information
from datetime import timedelta

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)
import paho.mqtt.client as mqtt
import nest_asyncio
from datetime import datetime
from mqtt_topics import Topics  # Import Topics enum
from mqtt_payload import create_payload, publish_payload, MQTTPayload  # Import MQTTPayload class

# ----------------------- KONFIGURATION -----------------------
logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Gruppens (eller kanalens) chat-id
GROUP_CHAT_ID = -4664318067  # Byt till ditt eget ID

# MQTT-inställningar
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# Global referens till huvudloopen, sätts i main()
MAIN_LOOP = None

# Global flags for processing logic
process_latest_photo = False
latest_photo_future = None

# Track the start time of the script
START_TIME = datetime.now()

mqtt_client = None


# ----------------------- KOMMANDON -----------------------

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logging.info(f"Chat ID: {chat_id}")
    await update.message.reply_text(
        f"Välkommen! Skriv /help för att se vad jag kan göra 🤖\nDitt chat ID är: {chat_id}"
    )

# /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🛠️ *Tillgängliga kommandon:*\n\n"
        "/start - Startar en konversation med boten 🤖\n"
        "/help - Visar denna hjälptext 📝\n"
        "/photo - Skickar en bild på sjöboden 🏝️\n"
        "/arm - Aktiverar PIR-sensorn 🔒\n"
        "/disarm - Avaktiverar PIR-sensorn 🔓\n"
        "/takepicture - Tar en ny bild 📸\n"
        "/status - Visar systemstatus 📊\n"
        "/latestphoto [antal] - Begär senaste bilderna 📸\n"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

# /photo (skickar en fast bild i aktuell konversation)
async def send_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_path = './pics/seahut.jpg'
    try:
        with open(photo_path, 'rb') as photo:
            await update.message.reply_photo(photo)
        logging.info(f"Bild skickad: {photo_path}")
    except FileNotFoundError:
        await update.message.reply_text("2. Hoppsan! Jag hittade inte bilden. 😢")
        logging.error(f"Bilden saknas: {photo_path}")

# /arm
async def arm_pir_sensor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Arms the PIR sensor by publishing to the ARM_TOPIC.
    """
    try:
        payload = create_payload(source="bot", event="ARM_PIR_SENSOR")
        publish_payload(Topics.PIR_ARM.value, payload)  # Use Topics enum
        await update.message.reply_text("🔒 PIR-sensorn är nu aktiverad.")
        logging.info(f"Published ARM message to topic: {Topics.PIR_ARM.value}")
    except Exception as e:
        logging.error(f"Failed to arm PIR sensor: {e}")
        await update.message.reply_text("❌ Misslyckades att aktivera PIR-sensorn.")

# /disarm
async def disarm_pir_sensor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Disarms the PIR sensor by publishing to the DISARM_TOPIC.
    """
    try:
        payload = create_payload(source="bot", event="DISARM_PIR_SENSOR")
        publish_payload(Topics.PIR_DISARM.value, payload)  # Use Topics enum
        await update.message.reply_text("🔓 PIR-sensorn är nu avaktiverad.")
        logging.info(f"Published DISARM message to topic: {Topics.PIR_DISARM.value}")
    except Exception as e:
        logging.error(f"Failed to disarm PIR sensor: {e}")
        await update.message.reply_text("❌ Misslyckades att avaktivera PIR-sensorn.")

# /takepicture
async def take_picture_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Sends a command to the camera to take a picture and sends the picture to the Telegram group.
    """
    try:
        payload = create_payload(source="bot", event="TAKE_PICTURE")
        await publish_payload_async(Topics.TAKE_PICTURE.value, payload)  # Use the async version of publish_payload
        await update.message.reply_text("📸 Tar en bild... Vänta ett ögonblick.")  # Correct response
        logging.info("Take picture command sent via /takepicture.")
    except Exception as e:
        logging.error(f"Failed to send take picture command: {e}")
        await update.message.reply_text("❌ Misslyckades att ta en bild.")  # Error response

# /status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Sends the script's process ID, the state of the MQTT client, how long it has been running, and subscribed topics.
    """
    try:
        # Get process ID
        process_id = os.getpid()

        # Dynamically check MQTT client state
        client = get_mqtt_client()
        mqtt_state = "Connected" if client and client.is_connected() else "Disconnected"

        # Fetch subscribed topics dynamically
        subscribed_topics = []
        if client and hasattr(client, "_userdata"):
            subscribed_topics = client._userdata.get("subscriptions", [])

        # Calculate uptime
        uptime = datetime.now() - START_TIME
        uptime_str = str(timedelta(seconds=int(uptime.total_seconds())))

        # Prepare status message
        status_message = (
            f"📊 *System Status:*\n\n"
            f"🔹 *Process ID:* {process_id}\n"
            f"🔹 *MQTT Client State:* {mqtt_state}\n"
            f"🔹 *Uptime:* {uptime_str}\n"
            f"🔹 *Subscribed Topics:*\n" +
            "\n".join([f"  - {topic}" for topic in subscribed_topics])
        )

        # Send status message
        await update.message.reply_text(status_message, parse_mode="Markdown")
        logging.info("Status command executed successfully.")
    except Exception as e:
        logging.error(f"Failed to execute /status command: {e}")
        await update.message.reply_text("❌ Misslyckades att hämta status.")

# /latestphoto
async def latest_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Requests the latest pictures from MQTT based on the count provided in the command.
    Does not wait for a response – handled by bot_publisher.
    """
    try:
        # Extract the count argument from the command (default to 1 if not provided)
        count = 1
        if context.args:
            try:
                count = int(context.args[0])
                if count < 1:
                    raise ValueError("Count must be at least 1.")
            except ValueError:
                await update.message.reply_text("❌ Ogiltigt antal. Ange ett positivt heltal.")
                return

        # Create and publish the payload
        payload = create_payload(source="bot", event="GET_LATEST_PICTURES", data={"count": count})
        publish_payload(Topics.GET_LATEST_PICTURES.value, payload)

        logging.info(f"Published GET_LATEST_PICTURES request (count={count}) to '{Topics.GET_LATEST_PICTURES.value}'")
        await update.message.reply_text(f"📸 Begär {count} senaste bilder. Vänta på respons i bot_publisher.")
    except Exception as e:
        logging.error(f"Failed to publish GET_LATEST_PICTURES request: {e}")
        await update.message.reply_text("❌ Misslyckades att begära senaste bilderna.")

# ----------------------- ASYNC MQTT PUBLISH -----------------------

async def publish_payload_async(topic: str, payload: MQTTPayload):
    """
    Publishes an MQTT payload asynchronously to avoid blocking the bot's event loop.
    """
    loop = asyncio.get_running_loop()
    client = get_mqtt_client()  # Ensure the function is defined below

    if client is None:
        logging.error("MQTT client is not available. Unable to publish payload.")
        return

    try:
        if not client.is_connected():
            logging.info("MQTT client is not connected. Attempting to reconnect...")
            await loop.run_in_executor(None, client.reconnect)
            logging.info("Reconnected to MQTT broker.")

        logging.info(f"Publishing payload to topic '{topic}': {payload.json()}")
        await loop.run_in_executor(None, client.publish, topic, payload.json())
        logging.info(f"Payload published to topic '{topic}'.")
    except Exception as e:
        logging.error(f"Failed to publish payload to topic '{topic}': {e}")

# ----------------------- MQTT CALLBACKS -----------------------

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info(f"MQTT: Connected to broker ({MQTT_BROKER}:{MQTT_PORT})")
        # Always subscribe to SEND_LATEST_PICTURES topic
        client.subscribe(Topics.SEND_LATEST_PICTURES.value)
        logging.info(f"Subscribed to topic: {Topics.SEND_LATEST_PICTURES.value}")
    else:
        logging.error(f"MQTT: Failed to connect to broker, return code {rc}")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        logging.warning("MQTT: Unexpected disconnection. Attempting to reconnect...")
        while True:
            try:
                client.reconnect()
                client.subscribe(Topics.SEND_LATEST_PICTURES.value)
                logging.info("MQTT: Reconnected to broker.")
                break
            except Exception as e:
                logging.error(f"MQTT: Reconnection failed: {e}. Retrying in 5 seconds...")
                time.sleep(5)
    else:
        logging.info("MQTT: Disconnected from broker gracefully.")

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    logging.info(f"MQTT: Message received on {msg.topic}: {payload}")

# ----------------------- MAIN: starta bot & tasks -----------------------

async def send_group_photo(app, photo_path):
    """
    Sends a photo to the Telegram group.
    """
    try:
        with open(photo_path, 'rb') as photo:
            await app.bot.send_photo(chat_id=GROUP_CHAT_ID, photo=photo)
        logging.info(f"Photo sent to group: {photo_path}")
    except FileNotFoundError:
        logging.error(f"Photo not found: {photo_path}")
        await app.bot.send_message(chat_id=GROUP_CHAT_ID, text="❌ Hoppsan! Jag hittade inte bilden. 😢")
    except Exception as e:
        logging.error(f"Failed to send photo to group: {e}")
        await app.bot.send_message(chat_id=GROUP_CHAT_ID, text="❌ Misslyckades att skicka bilden.")

async def send_group_push_message(app, text="🚀 Detta är ett push-meddelande till gruppen!"):
    """
    Sends a text message to the Telegram group.
    """
    try:
        await app.bot.send_message(chat_id=GROUP_CHAT_ID, text=text)
        logging.info(f"Push message sent to group: {text}")
    except Exception as e:
        logging.error(f"Failed to send push message to group: {e}")

# ----------------------- MQTT CLIENT SETUP -----------------------


def get_mqtt_client():
    global mqtt_client
    if mqtt_client is None:
        mqtt_client = setup_mqtt_client()
    return mqtt_client

def setup_mqtt_client():
    """
    Sets up the MQTT client with the necessary callbacks and starts the loop.
    """
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 30)
        logging.info(f"MQTT: Connected to broker at {MQTT_BROKER}:{MQTT_PORT}")
    except Exception as e:
        logging.error(f"MQTT: Failed to connect to broker: {e}")
        sys.exit(1)

    client.loop_start()
    return client

async def main():
    global MAIN_LOOP, app
    app = ApplicationBuilder().token(TOKEN).build()

    MAIN_LOOP = asyncio.get_running_loop()

    # Registrera kommandon
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("photo", send_photo))
    app.add_handler(CommandHandler("arm", arm_pir_sensor))
    app.add_handler(CommandHandler("disarm", disarm_pir_sensor))
    app.add_handler(CommandHandler("takepicture", take_picture_command))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("latestphoto", latest_photo))

    # Setup MQTT en gång
    get_mqtt_client()

    # Skicka push-meddelande när botten startar
    await send_group_push_message(app, text="🚀 Botten har startat!")

    logging.info("🚀 Botten är igång! Kör polling...")
    app.run_polling()


if __name__ == '__main__':
    nest_asyncio.apply()  # Möjliggör nested asyncio-loops om det behövs
    asyncio.run(main())
