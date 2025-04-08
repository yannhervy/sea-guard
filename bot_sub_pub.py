import os
import time
import json
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Bot
from mqtt_client import get_mqtt_client
from mqtt_topics import Topics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROUP_CHAT_ID = -4664318067  # Replace with your group ID if needed

bot = Bot(token=TOKEN)

loop = None  # Will hold the global event loop

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("bot_sub_pub: Connected to MQTT broker.")
        client.subscribe([
            (Topics.SEND_LATEST_PICTURES.value, 0),
            (Topics.SEND_MESSAGE.value, 0)
        ])
        logging.info(f"bot_sub_pub: Subscribed to {Topics.SEND_LATEST_PICTURES.value} and {Topics.SEND_MESSAGE.value}.")
    else:
        logging.error(f"bot_sub_pub: Connection failed with rc={rc}")

async def send_pictures_async(pictures):
    """
    Coroutine to send pictures asynchronously to Telegram.
    """
    for picture_path in pictures:
        
        try:
            with open(picture_path, 'rb') as photo_file:
                await bot.send_photo(chat_id=GROUP_CHAT_ID, photo=photo_file)
                logging.info(f"bot_sub_pub: Sent picture {picture_path} to group {GROUP_CHAT_ID}")
        except FileNotFoundError:
            logging.error(f"bot_sub_pub: Picture file not found: {picture_path}")
async def send_message_async(message):
    """
    Coroutine to send a message asynchronously to Telegram.
    """
    try:
        await bot.send_message(chat_id=GROUP_CHAT_ID, text=message)
        logging.info(f"bot_sub_pub: Sent message to group {GROUP_CHAT_ID}: {message}")
    except Exception as e:
        logging.error(f"bot_sub_pub: Failed to send message: {e}")

def on_message(client, userdata, msg):
    """
    Receives an array of picture paths from SEND_LATEST_PICTURES and sends them to the Telegram group.
    """
    logging.info(f"bot_sub_pub: Received message on {msg.topic}: {msg.payload.decode()}")
    try:
        if msg.topic == Topics.SEND_LATEST_PICTURES:
            payload_str = msg.payload.decode()
            logging.info(f"bot_sub_pub: Received message on {msg.topic}: {payload_str}")
            data = json.loads(payload_str)
            pictures = data.get("data", {}).get("pictures", [])
            if not pictures:
                logging.info("bot_sub_pub: No pictures array found in payload.")
                return
            asyncio.run_coroutine_threadsafe(send_pictures_async(pictures), loop)
        elif msg.topic == Topics.SEND_MESSAGE:
            payload_str = msg.payload.decode()
            data = json.loads(payload_str)
            message = data.get("data", {}).get("message", "")
            if not message:
                logging.info("bot_sub_pub: No message found in payload.")
                return
            asyncio.run_coroutine_threadsafe(send_message_async(message), loop)

        # Schedule the async send in the global loop
    except Exception as e:
        logging.error(f"bot_sub_pub: Failed to process pictures: {e}")

def main():
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    client = get_mqtt_client(
        subscriptions=[Topics.SEND_LATEST_PICTURES.value],
        client_id="bot_sub_pub"
    )
    if client is None:
        logging.error("bot_sub_pub: No MQTT client available.")
        return

    client.on_connect = on_connect
    client.on_message = on_message

    logging.info("bot_sub_pub: Starting MQTT loop in background.")
    # Start MQTT on a separate thread so we can use our own async event loop here
    client.loop_start()

    # Keep the main thread alive with an endless loop
    logging.info("bot_sub_pub: Running main asyncio event loop forever.")
    loop.run_forever()

if __name__ == "__main__":
    main()
