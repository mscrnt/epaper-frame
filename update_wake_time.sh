#!/bin/bash

# Set the time offset in minutes (e.g., 15 for 15 minutes, 90 for an hour and a half)
OFFSET_MINUTES=480 # 8 hours

# Sync RTC with web time (this updates both the RTC and system time)
echo "Syncing RTC with web time..."
echo "rtc_web" | nc -q 0 127.0.0.1 8423

# Optional: wait a couple seconds to ensure the sync is complete
sleep 5

# Convert the offset from minutes to seconds
OFFSET_SECONDS=$((OFFSET_MINUTES * 60))

# Get the current time (in seconds since epoch)
CURRENT_TIME=$(date +%s)

# Add the offset seconds to set the wakeup time
NEW_WAKE_TIME=$(date -d "@$((CURRENT_TIME + OFFSET_SECONDS))" --iso-8601=seconds)
echo "Setting RTC wakeup alarm to: $NEW_WAKE_TIME"

# Set the RTC wakeup alarm using the rtc command via netcat
echo "rtc_alarm_set $NEW_WAKE_TIME" 127 | nc -q 0 127.0.0.1 8423

echo "✅ RTC wakeup alarm set successfully!"
