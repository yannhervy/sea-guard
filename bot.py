import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import logging
import asyncio
import signal
import json

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)
import paho.mqtt.client as mqtt
import nest_asyncio
from mqtt_topics import Topics  # Import Topics enum
from mqtt_payload import create_payload, publish_payload  # Import helper functions

# ----------------------- KONFIGURATION -----------------------
logging.basicConfig(level=logging.INFO)

load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Gruppens (eller kanalens) chat-id
GROUP_CHAT_ID = -4664318067  # Byt till ditt eget ID

# MQTT-inställningar
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = Topics.PIR_HEARTBEAT.value  # Example usage of Topics enum

# Global referens till huvudloopen, sätts i main()
MAIN_LOOP = None

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
        "/latestphoto - Skickar den senaste bilden 📸\n"
        "/latestphoto - Skickar de 3 senaste bilderna 📸📸📸\n"
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
        await update.message.reply_text("Hoppsan! Jag hittade inte bilden. 😢")
        logging.error(f"Bilden saknas: {photo_path}")

# ----------------------- HANTERA /latestphoto -----------------------

async def latest_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Begär N senaste bilder från MQTT och skickar dem till gruppen."""
    # --- Steg 0: Läs parametern (N) ---
    # Kommandot kan se ut så här i chatten: "/latestphoto 5"
    # Standard: 1 (om inget anges eller om det inte är ett tal)
    cmd_parts = update.message.text.split()
    if len(cmd_parts) > 1:
        try:
            n = int(cmd_parts[1])
        except ValueError:
            n = 1
    else:
        n = 1
    
    # 1) Skapa MQTT-klient
    mqtt_client = mqtt.Client()

    # 2) Skapa en Future i huvudloopen som vi ska vänta på
    future = asyncio.get_running_loop().create_future()

    def on_connect(client, userdata, flags, rc):
        logging.info("MQTT: Ansluten till broker (latestphoto)")
        client.subscribe(Topics.SEND_LATEST_PICTURES.value)  # Use enum value

    def on_message(client, userdata, msg):
        # Denna callback körs i paho-mqtt-tråden
        payload_str = msg.payload.decode()
        logging.info(f"All messages -> topic: '{msg.topic}', payload: '{payload_str}'")

        if msg.topic == Topics.SEND_LATEST_PICTURES.value:  # Use enum value
            # Skapa en coroutine som sätter future-resultatet
            async def _resolve():
                if not future.done():
                    future.set_result(payload_str)

            # Kör coroutinen i huvudloopen (MAIN_LOOP är en global referens i exemplet)
            asyncio.run_coroutine_threadsafe(_resolve(), MAIN_LOOP)

    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    # 3) Kör MQTT i bakgrunden (icke-blockerande)
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()

    # 4) Publicera förfrågan (N)
    request_payload = create_payload(source="bot", event="GET_LATEST_PICTURES", data={"count": n})
    publish_payload(mqtt_client, Topics.GET_LATEST_PICTURES_N.value, request_payload)  # Use standardized payload

    try:
        # 5) Vänta asynkront på att future fylls med payload
        logging.info(f"Väntar på MQTT-svar för /latestphoto (N={n}) ...")
        payload = await future
        logging.info(f"/latestphoto: Fick payload: {payload}")

        # 6) Hantera svaret (en JSON-lista med bildvägar)
        try:
            image_paths = json.loads(payload)
            if image_paths:
                # Om det finns färre bilder än N, får vi helt enkelt färre
                logging.info(f"Skickar totalt {len(image_paths)} bilder (begärde {n}).")
                
                # Skicka varje bild i tur och ordning till gruppen
                for path in image_paths:
                    await send_group_photo(context, path)
                
            else:
                await update.message.reply_text("Ingen bild funnen.")
        except json.JSONDecodeError:
            await update.message.reply_text("Fel vid JSON-dekodning av bild.")
    finally:
        # 7) Avsluta MQTT
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

# ----------------------- FUNKTIONER FÖR ATT SKICKA TILL GRUPP -----------------------

async def send_group_photo(context, photo_path):
    """Skickar en vald bildväg till gruppen via context.bot."""
    try:
        with open(photo_path, 'rb') as photo:
            await context.bot.send_photo(chat_id=GROUP_CHAT_ID, photo=photo)
        logging.info(f"Bild skickad till gruppen: {photo_path}")
    except FileNotFoundError:
        await context.bot.send_message(chat_id=GROUP_CHAT_ID, text="Hoppsan! Jag hittade inte bilden. 😢")
        logging.error(f"Bilden saknas: {photo_path}")

async def send_default_photo(app):
    """Skickar en standardbild (./pics/seahut.jpg) till gruppen via app.bot."""
    photo_path = './pics/seahut.jpg'
    try:
        with open(photo_path, 'rb') as photo:
            await app.bot.send_photo(chat_id=GROUP_CHAT_ID, photo=photo)
        logging.info(f"Standardbild skickad till gruppen: {photo_path}")
    except FileNotFoundError:
        await app.bot.send_message(chat_id=GROUP_CHAT_ID, text="Hoppsan! Jag hittade inte bilden. 😢")
        logging.error(f"Bilden saknas: {photo_path}")

async def send_group_push_message(app, text="🚀 Detta är ett push-meddelande till gruppen!"):
    """Skickar ett textmeddelande till gruppchatten."""
    await app.bot.send_message(chat_id=GROUP_CHAT_ID, text=text)

# ----------------------- BAKGRUNDSUPPGIFTER -----------------------

async def heartbeat_task(app):
    """Skickar 'heartbeat' en gång per timme."""
    while True:
        logging.info("Skickar heartbeat-meddelande")
        await send_group_push_message(app, text="💓 Heartbeat")
        await asyncio.sleep(60*60)  # var 60:e minut

async def handle_pir_event(app, payload):
    """
    Handles PIR motion events and sends a message to the group chat.
    """
    try:
        data = json.loads(payload)
        event = data.get("event", "UNKNOWN")
        timestamp = data.get("timestamp", "N/A")
        message = f"🚨 PIR Sensor Alert: {event} detected at {timestamp}."
        await send_group_push_message(app, text=message)
    except json.JSONDecodeError:
        logging.error("Failed to decode PIR event payload.")

async def mqtt_subscribe_task(app):
    """
    Subscribes to MQTT topics and handles incoming messages.
    """
    loop = asyncio.get_running_loop()

    def on_connect(client, userdata, flags, rc):
        logging.info(f"MQTT: Connected to broker ({MQTT_BROKER}:{MQTT_PORT})")
        client.subscribe(Topics.PIR_MOTION_DETECTED.value)  # Subscribe to PIR motion detected topic
        client.subscribe(MQTT_TOPIC)  # Use enum value

    def on_message(client, userdata, msg):
        payload = msg.payload.decode()
        logging.info(f"MQTT: Message received on {msg.topic}: {payload}")
        if msg.topic == Topics.PIR_MOTION_DETECTED.value:
            asyncio.run_coroutine_threadsafe(handle_pir_event(app, payload), loop)
        else:
            asyncio.run_coroutine_threadsafe(
                handle_mqtt_event(app, msg.topic, payload),
                loop
            )

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        logging.error(f"Failed to connect to MQTT broker: {e}")
        return
    client.loop_start()

    while True:
        await asyncio.sleep(1)

async def handle_mqtt_event(app, topic, payload):
    """
    Hanterar meddelanden som kommer in på topic: "sjoboden/events".
    Skickar en pushtext + en standardbild till gruppen.
    """
    await send_group_push_message(app, text=f"📡 MQTT event på {topic}: {payload}")
    await send_default_photo(app)

# ----------------------- MAIN: starta bot & tasks -----------------------

async def main():
    global MAIN_LOOP
    app = ApplicationBuilder().token(TOKEN).build()

    # Sätt vår globala MAIN_LOOP till den event-loop som kör just nu
    MAIN_LOOP = asyncio.get_running_loop()

    # Registrera kommandon
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("photo", send_photo))
    app.add_handler(CommandHandler("latestphoto", latest_photo))

    async with app:
        # Skicka ett meddelande till gruppen när boten startar
        await send_group_push_message(app, text="🚀 Botten har startat!")

        # Starta bakgrundsuppgifter
        asyncio.create_task(heartbeat_task(app))
        asyncio.create_task(mqtt_subscribe_task(app))

        print("🚀 Botten är igång! Tryck Ctrl+C för att stoppa.")
        await app.run_polling(poll_interval=5, timeout=30)

# ----------------------- INITIERING & KÖRNING -----------------------

if __name__ == '__main__':
    nest_asyncio.apply()  # Möjliggör nested asyncio-loops om det behövs
    loop = asyncio.get_event_loop()

    def shutdown_handler():
        print("\n🚦 Avslutar boten...")
        for task in asyncio.all_tasks(loop):
            task.cancel()
        loop.stop()

    signal.signal(signal.SIGINT, lambda sig, frame: shutdown_handler())

    try:
        loop.run_until_complete(main())
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        print("\n🚦 Botten avbröts med CTRL+C.")
    finally:
        tasks = asyncio.all_tasks(loop)
        for task in tasks:
            task.cancel()
        try:
            loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        except asyncio.CancelledError:
            pass
        print("✅ Botten har stängts av.")
