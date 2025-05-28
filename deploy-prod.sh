#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

PROJECT_DIR="/home/ubuntu/YoloService"
VENV_DIR="$PROJECT_DIR/.venv"
SERVICE_NAME="yolo-prod-service"

echo "📁 Navigating to project directory: $PROJECT_DIR"
cd "$PROJECT_DIR"

# Step 1: Set up virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
  echo "🐍 Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

# Step 2: Activate virtual environment
echo "🔌 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Step 3: Check if dependencies are installed
# We'll check if a key package from requirements.txt is installed (e.g., fastapi)
# Modify PACKAGE_TO_CHECK if needed
PACKAGE_TO_CHECK="fastapi"

if ! pip show "$PACKAGE_TO_CHECK" > /dev/null 2>&1; then
  echo "📦 Installing Python dependencies..."
  pip install --upgrade pip
  pip install -r requirements.txt
  pip install -r torch-requirements.txt
else
  echo "✅ Dependencies already installed, skipping pip install."
fi

# Step 4: Copy the systemd service file
echo "🛠️  Setting up systemd service..."
sudo cp "$PROJECT_DIR/$SERVICE_NAME" /etc/systemd/system/$SERVICE_NAME

# Step 4: Reload systemd and restart the service
echo "🔄 Reloading systemd and restarting YOLO service..."
sudo systemctl daemon-reload
sudo systemctl restart $SERVICE_NAME
sudo systemctl enable $SERVICE_NAME

# Step 5: Check service status
echo "🔍 Checking yolo.service status..."
if systemctl is-active --quiet $SERVICE_NAME  ; then
  echo "✅ yolo.service is running."
else
  echo "❌ yolo.service failed to start."
  sudo systemctl status $SERVICE_NAME --no-pager
  exit 1
fi
