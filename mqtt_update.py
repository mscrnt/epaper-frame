#!/usr/bin/env python3
import os
import json
import logging
import subprocess
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
LOG_FILE = os.getenv("LOG_FILE", "/mnt/photos/epaper_logs.txt")

# ✅ Human-readable mapping for PiSugar keys
SENSOR_LABELS = {
    "firmware_version": "Firmware Version",
    "battery": "Battery Level (%)",
    "battery_i": "Battery Current (A)",
    "battery_v": "Battery Voltage (V)",
    "battery_charging": "Battery Charging",
    "model": "PiSugar Model",
    "battery_led_amount": "Battery LED Count",
    "battery_power_plugged": "Battery USB Plugged",
    "battery_charging_range": "Battery Charging Range (%)",
    "battery_allow_charging": "Battery Allow Charging",
    "battery_output_enabled": "Battery Output Enabled",
    "rtc_time": "RTC Clock Time",
    "rtc_alarm_enabled": "RTC Alarm Enabled",
    "rtc_alarm_time": "RTC Alarm Time",
    "alarm_repeat": "RTC Alarm Repeat (Weekdays)",
    "safe_shutdown_level": "Safe Shutdown Level (%)",
    "safe_shutdown_delay": "Safe Shutdown Delay (s)",
    "auth_username": "HTTP Auth Username",
    "anti_mistouch": "Anti-Mistouch Protection",
    "soft_poweroff": "Software Poweroff Enabled",
    "temperature": "Device Temperature (°C)",
}

def run_command(command):
    """Helper function to execute shell commands and get output."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        return result.stdout.strip() if result.stdout else None
    except Exception as e:
        logging.error(f"❌ Failed to run command {command}: {e}")
        return None

def parse_pisugar_response(response):
    """Extracts only the value from the PiSugar response."""
    if not response or "Invalid request" in response:
        return "Unknown"
    
    parts = response.split(": ", 1)  # Split only at the first occurrence
    if len(parts) == 2:
        return parts[1].strip()
    return response.strip()

def get_pisugar_status():
    """Retrieve all PiSugar-related metrics and properly format responses."""
    commands = {key: f"get {key}" for key in SENSOR_LABELS.keys()}

    status = {}
    for key, command in commands.items():
        response = run_command(f"echo '{command}' | nc -q 0 127.0.0.1 8423")
        status[key] = parse_pisugar_response(response)

    return status

def publish_mqtt(topic, payload, retain=True):
    """Send MQTT message to Home Assistant using discovery format."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)

        full_topic = f"{MQTT_TOPIC_PREFIX}/{topic}"
        discovery_topic = f"homeassistant/sensor/{MQTT_TOPIC_PREFIX}_{topic}/config"

        # ✅ Determine sensor type (binary_sensor or sensor)
        sensor_type = "sensor"
        if payload in ["true", "false"]:  # Convert true/false to binary_sensor
            sensor_type = "binary_sensor"

        # ✅ Use human-readable names for Home Assistant
        sensor_name = SENSOR_LABELS.get(topic, topic.replace("_", " ").title())

        # ✅ Publish Discovery message
        discovery_payload = {
            "name": f"{sensor_name}",
            "state_topic": full_topic,
            "unique_id": f"{MQTT_TOPIC_PREFIX}_{topic}",
            "device": {
                "identifiers": [MQTT_TOPIC_PREFIX],
                "name": "PiSugar ePaper Frame",
                "model": "Raspberry Pi ePaper Frame",
                "manufacturer": "Mscrnt LLC",
            },
        }

        if sensor_type == "binary_sensor":
            discovery_payload["payload_on"] = "true"
            discovery_payload["payload_off"] = "false"

        client.publish(discovery_topic, json.dumps(discovery_payload), retain=True)
        client.publish(full_topic, json.dumps(payload), retain=retain)

        logging.info(f"✅ Sent MQTT update to {full_topic}: {payload}")
        client.disconnect()
    except Exception as e:
        logging.error(f"❌ Failed to send MQTT message: {e}")

def get_last_displayed_image():
    """Extract the last image displayed from the log file, preserving spaces."""
    if not os.path.exists(LOG_FILE):
        logging.error(f"❌ Log file not found: {LOG_FILE}")
        return "Unknown"

    last_image = "Unknown"
    try:
        with open(LOG_FILE, "r") as log_file:
            for line in log_file:
                if "🖼️ Last Image Displayed:" in line:
                    last_image = line.split("🖼️ Last Image Displayed: ")[1].strip()
    except Exception as e:
        logging.error(f"❌ Error reading log file: {e}")

    return last_image

if __name__ == "__main__":
    # ✅ Retrieve values automatically
    last_image = get_last_displayed_image()
    pisugar_status = get_pisugar_status()

    # ✅ Send last displayed image
    publish_mqtt("last_image", last_image)

    # ✅ Send each PiSugar metric separately
    for key, value in pisugar_status.items():
        publish_mqtt(key, value)
