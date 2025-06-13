# Start with slim Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install OS-level dependencies (e.g., for OpenCV, torch, etc.)
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirement files first (for Docker cache)
COPY requirements.txt .
COPY torch-requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r torch-requirements.txt \
 && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the source code
COPY . .

# Start the YOLO app
CMD ["python", "-m", "app"]
