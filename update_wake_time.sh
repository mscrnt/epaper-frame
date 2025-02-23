#!/bin/bash

# Sync RTC with web time (this updates both the RTC and system time)
echo "Syncing RTC with web time..."
echo "rtc_web" | nc -q 0 127.0.0.1 8423

# Optional: wait a couple seconds to ensure the sync is complete
sleep 5

# Get the current time (in seconds since epoch)
CURRENT_TIME=$(date +%s)

# Add 8 hours (28800 seconds) to set the wakeup time
NEW_WAKE_TIME=$(date -d "@$((CURRENT_TIME + 28800))" --iso-8601=seconds)
echo "Setting RTC wakeup alarm to: $NEW_WAKE_TIME"

# Set the RTC wakeup alarm using the rtc command via netcat
# The command format is: rtc_alarm_set [ISO8601 time string] [repeat]
# If you don't need a repeating alarm, you can omit the repeat argument
echo "rtc_alarm_set $NEW_WAKE_TIME" | nc -q 0 127.0.0.1 8423

echo "✅ RTC wakeup alarm set successfully!"
