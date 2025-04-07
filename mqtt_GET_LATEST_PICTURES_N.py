import paho.mqtt.client as mqtt
from mqtt_topics import Topics  # Import Topics enum
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# MQTT-inställningar
MQTT_BROKER = 'localhost'  # Byt till din broker-URL om den inte är lokal
MQTT_PORT = 1883

# Callback när vi får ett svar från MQTT-brokern
def on_connect(client, userdata, flags, rc):
    print(f"Ansluten till MQTT-broker med rc={rc}")
    
    # Skicka begäran om 5 bilder
    request_payload = '5'  # Begär 5 senaste bilder
    client.publish(Topics.GET_LATEST_PICTURES.value, request_payload)
    print(f"Skickade begäran om {request_payload} senaste bilder till {Topics.GET_LATEST_PICTURES.value}.")

def on_message(client, userdata, msg):
    # Skriv ut när vi får ett svar på ämnet SEND_LATEST_PICTURES
    if msg.topic == Topics.SEND_LATEST_PICTURES.value:
        print(f"Mottog svar på {Topics.SEND_LATEST_PICTURES.value}: {msg.payload.decode()}")
        # Här kan vi exempelvis parse och hantera svaret (en JSON-lista med bildvägar)

# Starta MQTT-klienten
def start_mqtt_client():
    client = mqtt.Client()

    client.on_connect = on_connect
    client.on_message = on_message

    # Anslut till broker
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    # Lyssna på svar från SEND_LATEST_PICTURES
    client.subscribe(Topics.SEND_LATEST_PICTURES.value)

    # Kör MQTT-loopen (blockerande)
    client.loop_forever()

if __name__ == "__main__":
    start_mqtt_client()
