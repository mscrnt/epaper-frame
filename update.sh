#!/bin/bash

# Explicitly set the correct project directory
PROJECT_DIR="/home/kenneth/epaper-frame"  # Change this to match your setup
REPO_URL="https://github.com/mscrnt/epepar-frame.git"

echo "🌐 Waiting for internet connection..."

# Wait up to 60 seconds for an internet connection
TIMEOUT=60
ELAPSED=0

while ! ping -c 1 -W 3 google.com &> /dev/null; do
    echo "🔄 No internet connection. Retrying in 10 seconds..."
    sleep 10
    ((ELAPSED+=10))
    
    if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
        echo "❌ No internet detected after $TIMEOUT seconds. Exiting."
        exit 1
    fi
done

echo "✅ Internet connection established!"

# ✅ Ensure Git recognizes the project directory as safe
echo "🔒 Configuring Git safe directory..."
git config --global --add safe.directory "$PROJECT_DIR"

echo "📡 Pulling latest updates for the EPD project..."
cd "$PROJECT_DIR" || { echo "❌ Failed to navigate to project directory."; exit 1; }

# Ensure Git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi

# Check if the project is already a git repo
if [ ! -d .git ]; then
    echo "🚀 Cloning repository..."
    git clone "$REPO_URL" "$PROJECT_DIR"
else
    echo "🔄 Pulling latest changes..."
    git reset --hard origin/main  # Ensure a clean update
    git pull origin main
fi

# Make sure the config directory exists
if [ ! -d "$PROJECT_DIR/config" ]; then
    echo "⚠ Config directory missing. Creating it..."
    mkdir -p "$PROJECT_DIR/config"
fi

echo "✅ Update complete!"
