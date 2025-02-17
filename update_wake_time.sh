#!/bin/bash

CONFIG_FILE="/etc/pisugar-server/config.json"

# Get the current date and time
CURRENT_TIME=$(date +%s)

# Add 8 hours (28800 seconds) to the current time
NEW_WAKE_TIME=$(date -d "@$((CURRENT_TIME + 28800))" --iso-8601=seconds)

# Update the config.json file
echo "Updating PiSugar auto_wake_time to: $NEW_WAKE_TIME"

# Use jq to modify the JSON file (requires jq to be installed)
if command -v jq >/dev/null 2>&1; then
    sudo jq --arg newtime "$NEW_WAKE_TIME" '.auto_wake_time = $newtime' "$CONFIG_FILE" > /tmp/config.json && sudo mv /tmp/config.json "$CONFIG_FILE"
else
    # If jq is not installed, use sed as a fallback
    sudo sed -i "s|\"auto_wake_time\": \".*\"|\"auto_wake_time\": \"$NEW_WAKE_TIME\"|" "$CONFIG_FILE"
fi

# Restart PiSugar service to apply the changes
echo "Restarting PiSugar service..."
sudo systemctl restart pisugar-server

echo "✅ PiSugar auto_wake_time updated successfully!"
