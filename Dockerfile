# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Install WireGuard and dependencies
RUN apt-get update && apt-get install -y \
    wireguard-tools \
    iptables \
    iproute2 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of app
COPY . .

# Copy WireGuard config
COPY wg0.conf /etc/wireguard/wg0.conf

# Create start script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Expose the Flask port (note: your app.py runs on 8080 for Fly)
EXPOSE 8080

# Use start script to start WireGuard then app
CMD ["/start.sh"]
