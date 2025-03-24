import paho.mqtt.client as mqtt

# MQTT-inställningar
MQTT_BROKER = 'localhost'  # Byt till din broker-URL om den inte är lokal
MQTT_PORT = 1883
MQTT_TOPIC_GET = 'GET_LATEST_PICTURES_N'
MQTT_TOPIC_SEND = 'SEND_LATEST_PICTURES'

# Callback när vi får ett svar från MQTT-brokern
def on_connect(client, userdata, flags, rc):
    print(f"Ansluten till MQTT-broker med rc={rc}")
    
    # Skicka begäran om 5 bilder
    request_payload = '5'  # Begär 5 senaste bilder
    client.publish(MQTT_TOPIC_GET, request_payload)
    print(f"Skickade begäran om {request_payload} senaste bilder till {MQTT_TOPIC_GET}.")

def on_message(client, userdata, msg):
    # Skriv ut när vi får ett svar på ämnet SEND_LATEST_PICTURES
    if msg.topic == MQTT_TOPIC_SEND:
        print(f"Mottog svar på {MQTT_TOPIC_SEND}: {msg.payload.decode()}")
        # Här kan vi exempelvis parse och hantera svaret (en JSON-lista med bildvägar)

# Starta MQTT-klienten
def start_mqtt_client():
    client = mqtt.Client()

    client.on_connect = on_connect
    client.on_message = on_message

    # Anslut till broker
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    # Lyssna på svar från SEND_LATEST_PICTURES
    client.subscribe(MQTT_TOPIC_SEND)

    # Kör MQTT-loopen (blockerande)
    client.loop_forever()

if __name__ == "__main__":
    start_mqtt_client()
