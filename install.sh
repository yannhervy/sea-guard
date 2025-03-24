#!/bin/bash

echo "🔧 Sea Guard Installationsskript kör igång..."
echo "============================================"

# Uppdatera systemet
echo "📦 Uppdaterar paketlistor..."
sudo apt update && sudo apt upgrade -y

# Installera Mosquitto broker + clients
echo "📡 Installerar Mosquitto broker och klientverktyg..."
sudo apt install -y mosquitto mosquitto-clients

# Starta och aktivera mosquitto-tjänsten
echo "🛠️ Startar och aktiverar mosquitto-tjänsten..."
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

# Installera Python + pip + venv (om inte redan installerat)
echo "🐍 Installerar Python3, pip3 och venv om de saknas..."
sudo apt install -y python3 python3-pip python3-venv python3-full

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

# Avsluta med att visa status
echo "🚀 Allt klart! Sea Guard är redo att patrullera."
echo "Tips! Aktivera din venv med: source ~/sea-guard/venv/bin/activate"

# Färdigt!
