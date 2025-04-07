# sea-guard

## Overview

Sea Guard is an IoT security monitoring solution that uses:
• A motion-sensing PIR sensor.  
• A camera to capture and store images.  
• MQTT messaging for event-driven communication.  
• A Telegram bot to send alerts & pictures to a configured group.

## Installation

1. Make sure your system is up to date and Python 3 is installed.
2. Run ./install.sh (on Linux) to install dependencies and set up a Python virtual environment.
3. Activate the virtual environment and adjust scripts as needed.

## Usage

• Start the system by running python main.py.  
• The application launches multiple subprocesses for the bot, PIR sensor, camera, and a picture manager.  
• A Telegram bot listens to commands:

- /arm & /disarm to control the PIR sensor.
- /takepicture to capture a new image.
- /latestphoto [n] to request the latest n images.

## Architecture

• main.py manages the subprocesses and ensures they’re always running.  
• picturemanager.py handles image storage, cleanup, and provides images on request.  
• camera.py captures images on TAKE_PICTURE requests.  
• bot.py provides Telegram commands, publishing MQTT messages for other services to handle.  
• bot_sub_pub.py listens for incoming MQTT messages containing images and sends them to Telegram.

## Key Files

• camera.py – Captures images using libcamera.  
• picturemanager.py – Maintains pictures, removes old files.  
• pir_sensor.py – Detects motion and triggers alerts.  
• bot.py – Telegram bot commands.  
• bot_sub_pub.py – Receives and sends images to Telegram.

## Contributing

Feel free to open issues or propose pull requests. Use the code style and guidelines in this repository for consistent contributions.
