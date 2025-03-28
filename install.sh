#!/bin/bash

echo "🔧 Sea Guard Installationsskript kör igång..."
echo "============================================"

# Uppdatera systemet
echo "📦 Uppdaterar paketlistor..."
if ! sudo apt update && sudo apt upgrade -y; then
    echo "❌ Misslyckades att uppdatera systemet."
    exit 1
fi

# Installera Mosquitto broker + clients
echo "📡 Installerar Mosquitto broker och klientverktyg..."
if ! sudo apt install -y mosquitto mosquitto-clients; then
    echo "❌ Misslyckades att installera Mosquitto."
    exit 1
fi

# Starta och aktivera mosquitto-tjänsten
echo "🛠️ Startar och aktiverar mosquitto-tjänsten..."
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

# Installera Python + pip + venv (om inte redan installerat)
echo "🐍 Installerar Python3, pip3 och venv om de saknas..."
if ! sudo apt install -y python3 python3-pip python3-venv python3-full; then
    echo "❌ Misslyckades att installera Python och dess verktyg."
    exit 1
fi

# Skapa och aktivera en virtuell miljö
echo "🌱 Skapar virtuell miljö för Python..."
cd ~/sea-guard || exit
python3 -m venv venv

echo "✅ Aktiverar venv..."
source venv/bin/activate

# Installera Python dependencies
echo "📜 Installerar Python-dependencies från requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# Ensure python-dotenv is installed
pip install python-dotenv

# Install RPi.GPIO for Raspberry Pi
echo "📡 Installerar RPi.GPIO för PIR-sensorn..."
if ! pip install RPi.GPIO; then
    echo "❌ Misslyckades att installera RPi.GPIO."
    exit 1
fi

# Avsluta med att visa status
echo "🚀 Allt klart! Sea Guard är redo att patrullera."
echo "Tips! Aktivera din venv med: source ~/sea-guard/venv/bin/activate"

# Färdigt!
