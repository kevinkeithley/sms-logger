#!/bin/bash

# Start WireGuard
echo "Starting WireGuard..."
wg-quick up wg0

# Check if WireGuard is running
if wg show wg0 > /dev/null 2>&1; then
    echo "WireGuard started successfully"
    wg show
else
    echo "Failed to start WireGuard"
    exit 1
fi

# Set the backend URL using VPN address
export SMS_LOGGER_BACKEND_URL="http://10.100.0.2:10000"

# Start the Flask app
echo "Starting Flask app..."
python app.py
