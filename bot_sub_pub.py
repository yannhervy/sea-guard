import os
import json
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Bot
from mqtt_client import get_mqtt_client
from mqtt_topics import Topics

logging.basicConfig(level=logging.INFO)
load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROUP_CHAT_ID = -4664318067  # Replace with your group ID if needed

bot = Bot(token=TOKEN)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("bot_sub_pub: Connected to MQTT broker.")
        client.subscribe(Topics.SEND_LATEST_PICTURES.value)
        logging.info(f"bot_sub_pub: Subscribed to {Topics.SEND_LATEST_PICTURES.value}")
    else:
        logging.error(f"bot_sub_pub: Connection failed with rc={rc}")

def on_message(client, userdata, msg):
    """
    Receives an array of picture paths from SEND_LATEST_PICTURES and sends them to the Telegram group.
    """
    try:
        payload_str = msg.payload.decode()
        logging.info(f"bot_sub_pub: Received message on {msg.topic}: {payload_str}")
        data = json.loads(payload_str)
        pictures = data.get("data", {}).get("pictures", [])
        if not pictures:
            logging.info("bot_sub_pub: No pictures array found in payload.")
            return
        
        async def send_pictures_async():
            for picture_path in pictures:
                try:
                    with open(picture_path, 'rb') as photo_file:
                        await bot.send_photo(chat_id=GROUP_CHAT_ID, photo=photo_file)
                        logging.info(f"bot_sub_pub: Sent picture {picture_path} to group {GROUP_CHAT_ID}")
                except FileNotFoundError:
                    logging.error(f"bot_sub_pub: Picture file not found: {picture_path}")

        asyncio.run(send_pictures_async())
    except Exception as e:
        logging.error(f"bot_sub_pub: Failed to process pictures: {e}")

def main():
    client = get_mqtt_client(
        subscriptions=[Topics.SEND_LATEST_PICTURES.value],
        client_id="bot_sub_pub"
    )
    if client is None:
        logging.error("bot_sub_pub: No MQTT client available.")
        return
    client.on_connect = on_connect
    client.on_message = on_message

    logging.info("bot_sub_pub: Starting MQTT event loop.")
    client.loop_forever()

if __name__ == "__main__":
    main()
