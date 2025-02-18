#!/usr/bin/env python3
import os
import json
import logging
import subprocess
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# ✅ Load environment variables from .env and .secrets
load_dotenv()
if os.path.exists(".secrets"):
    load_dotenv(".secrets")

# Configure logging
logging.basicConfig(level=logging.INFO)

# ✅ MQTT Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "homeassistant.local")  # Home Assistant server
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", None)
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", None)
MQTT_TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "epaper_frame")  # Base topic
LOG_FILE = "/mnt/photos/epaper_logs.txt"
IMAGE_DIR = "/mnt/photos"  # Local directory for images

# ✅ Track last known power state
LAST_POWER_PLUGGED = None

def run_command(command):
    """Helper function to execute shell commands."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        return result.stdout.strip() if result.stdout else None
    except Exception as e:
        logging.error(f"❌ Failed to run command {command}: {e}")
        return None

def get_last_displayed_image():
    """Extract the last image displayed from the log file."""
    if not os.path.exists(LOG_FILE):
        logging.error(f"❌ Log file not found: {LOG_FILE}")
        return "Unknown"

    try:
        with open(LOG_FILE, "r") as log_file:
            for line in reversed(log_file.readlines()):
                if "📂 Selected Drive image:" in line:
                    return line.split("📂 Selected Drive image: ")[1].strip()
    except Exception as e:
        logging.error(f"❌ Error reading log file: {e}")

    return "Unknown"

def get_battery_status():
    """Retrieve battery status from PiSugar."""
    battery = run_command("echo 'get battery' | nc -q 0 127.0.0.1 8423")
    battery_v = run_command("echo 'get battery_v' | nc -q 0 127.0.0.1 8423")
    battery_i = run_command("echo 'get battery_i' | nc -q 0 127.0.0.1 8423")
    battery_charging = run_command("echo 'get battery_charging' | nc -q 0 127.0.0.1 8423")
    battery_power_plugged = run_command("echo 'get battery_power_plugged' | nc -q 0 127.0.0.1 8423")

    return {
        "charge": battery,
        "voltage": battery_v,
        "current": battery_i,
        "charging": battery_charging,
        "power_plugged": battery_power_plugged
    }

def publish_mqtt(topic, payload):
    """Send MQTT message to Home Assistant."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)  # ✅ Use correct API version

    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        full_topic = f"{MQTT_TOPIC_PREFIX}/{topic}"
        client.publish(full_topic, json.dumps(payload, ensure_ascii=False), retain=True)  # ✅ Allow Unicode
        logging.info(f"✅ Sent MQTT update to {full_topic}: {payload}")
        client.disconnect()
    except Exception as e:
        logging.error(f"❌ Failed to send MQTT message: {e}")

def on_message(client, userdata, msg):
    """Handle incoming MQTT messages for controlling the ePaper frame."""
    payload = msg.payload.decode("utf-8").strip()
    logging.info(f"📥 Received MQTT command: {msg.topic} → {payload}")

    if payload == "shutdown":
        logging.info("🛑 Shutting down system via MQTT...")
        subprocess.run("sudo shutdown now", shell=True)
    elif payload == "display":
        logging.info("📺 Running display.py via MQTT...")
        subprocess.run("python3 /home/kenneth/epaper-frame/display.py", shell=True)
    elif payload.startswith("set_image:"):
        image_name = payload.replace("set_image:", "").strip()
        image_path = os.path.join(IMAGE_DIR, image_name)
        
        if os.path.exists(image_path):
            logging.info(f"🖼️ Setting display to {image_name} via MQTT...")
            subprocess.run(f"python3 /home/kenneth/epaper-frame/display.py --image '{image_path}'", shell=True)
            publish_mqtt("last_image", {"image": image_name})
        else:
            logging.error(f"❌ Image not found: {image_path}")
    else:
        logging.warning(f"⚠️ Unknown command received: {payload}")

def monitor_and_report():
    """Monitor PiSugar status and send updates via MQTT."""
    global LAST_POWER_PLUGGED
    status = get_battery_status()

    # ✅ Publish battery status
    publish_mqtt("battery_status", status)

    # ✅ Detect and send power-plugged status only if changed
    if LAST_POWER_PLUGGED != status["power_plugged"]:
        publish_mqtt("power_event", {"plugged_in": status["power_plugged"]})
        LAST_POWER_PLUGGED = status["power_plugged"]

def mqtt_listen():
    """Listen for MQTT commands (shutdown, display, set_image)."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.subscribe(f"{MQTT_TOPIC_PREFIX}/command")
        logging.info(f"📡 Listening for MQTT commands on {MQTT_TOPIC_PREFIX}/command...")
        client.loop_forever()
    except Exception as e:
        logging.error(f"❌ Failed to start MQTT listener: {e}")

if __name__ == "__main__":
    monitor_and_report()
    mqtt_listen()
