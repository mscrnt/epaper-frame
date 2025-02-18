#!/usr/bin/env python3
import os
import json
import logging
import subprocess
import time
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()
if os.path.exists(".secrets"):
    load_dotenv(".secrets")

# Configure logging
logging.basicConfig(level=logging.INFO)

# ✅ MQTT Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "homeassistant.local")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", None)
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", None)
MQTT_TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "epaper_frame")
IMAGE_DIR = os.getenv("LOCAL_IMAGE_DIR", "/mnt/photos")

def run_command(command):
    """Helper function to execute shell commands."""
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Command failed: {command}, Error: {e}")

def send_mqtt_response(topic, message):
    """Send a response message back to MQTT for command acknowledgment."""
    client = mqtt.Client()
    
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        response_topic = f"{MQTT_TOPIC_PREFIX}/response/{topic}"
        client.publish(response_topic, message, retain=False)
        client.disconnect()
        logging.info(f"📡 Sent MQTT response: {response_topic} → {message}")
    except Exception as e:
        logging.error(f"❌ Failed to send MQTT response: {e}")

def on_message(client, userdata, msg):
    """Handle incoming MQTT messages for controlling the ePaper frame."""
    payload = msg.payload.decode("utf-8").strip()
    logging.info(f"📥 Received MQTT command: {msg.topic} → {payload}")

    if payload == "shutdown":
        logging.info("🛑 Shutting down system via MQTT...")
        send_mqtt_response("shutdown", "Shutting down...")
        run_command("sudo shutdown now")

    elif payload == "display":
        logging.info("📺 Running display.py via MQTT...")
        send_mqtt_response("display", "Updating display...")
        run_command("python3 /home/kenneth/epaper-frame/display.py")

    elif payload.startswith("set_image:"):
        image_name = payload.replace("set_image:", "").strip()
        image_path = os.path.join(IMAGE_DIR, image_name)

        if os.path.exists(image_path):
            logging.info(f"🖼️ Setting display to {image_name} via MQTT...")
            send_mqtt_response("set_image", f"Displaying {image_name}")
            run_command(f"python3 /home/kenneth/epaper-frame/display.py --image '{image_path}'")
        else:
            logging.error(f"❌ Image not found: {image_path}")
            send_mqtt_response("set_image", f"Error: {image_name} not found.")

    elif payload.startswith("set_pisugar:"):
        """Set PiSugar parameters via MQTT, e.g., set_pisugar:battery_output_enabled:true"""
        try:
            _, setting, value = payload.split(":")
            setting = setting.strip()
            value = value.strip().lower()

            # Convert value for PiSugar compatibility
            if value in ["true", "on", "enable", "enabled"]:
                value = "true"
            elif value in ["false", "off", "disable", "disabled"]:
                value = "false"

            command = f"echo 'set_{setting} {value}' | nc -q 0 127.0.0.1 8423"
            logging.info(f"🔧 Setting PiSugar {setting} → {value} via MQTT...")
            send_mqtt_response(f"set_pisugar_{setting}", f"Setting {setting} → {value}")
            run_command(command)
        except ValueError:
            logging.error(f"❌ Invalid set_pisugar command format: {payload}")
            send_mqtt_response("set_pisugar", "Error: Invalid command format.")

    else:
        logging.warning(f"⚠️ Unknown command received: {payload}")
        send_mqtt_response("unknown", "Error: Unknown command.")

def mqtt_listen():
    """Listen for MQTT commands (shutdown, display, set_image, set_pisugar)."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    client.on_message = on_message

    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            client.subscribe(f"{MQTT_TOPIC_PREFIX}/command")
            logging.info(f"📡 Listening for MQTT commands on {MQTT_TOPIC_PREFIX}/command...")
            client.loop_forever()
        except Exception as e:
            logging.error(f"❌ MQTT Connection failed: {e}. Retrying in 10 seconds...")
            time.sleep(10)  # Wait before retrying

if __name__ == "__main__":
    try:
        mqtt_listen()
    except KeyboardInterrupt:
        logging.info("🛑 MQTT Command Listener Stopped by User.")
