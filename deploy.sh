#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

PROJECT_DIR="/home/ubuntu/YoloService"
VENV_DIR="$PROJECT_DIR/.venv"

echo "📁 Navigating to project directory: $PROJECT_DIR"
cd "$PROJECT_DIR"

# Step 1: Set up virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
  echo "🐍 Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

# Step 2: Activate virtual environment and install dependencies
echo "📦 Installing Python dependencies..."
source "$VENV_DIR/bin/activate"
#pip install --upgrade pip
#pip install -r requirements.txt
#pip install -r torch-requirements.txt
#deactivate

# Step 3: Copy the systemd service file
echo "🛠️  Setting up systemd service..."
sudo cp "$PROJECT_DIR/yolo.service" /etc/systemd/system/yolo.service

# Step 4: Reload systemd and restart the service
echo "🔄 Reloading systemd and restarting YOLO service..."
sudo systemctl daemon-reload
sudo systemctl restart yolo.service
sudo systemctl enable yolo.service

# Step 5: Check service status
echo "🔍 Checking yolo.service status..."
if systemctl is-active --quiet yolo.service; then
  echo "✅ yolo.service is running."
else
  echo "❌ yolo.service failed to start."
  sudo systemctl status yolo.service --no-pager
  exit 1
fi
