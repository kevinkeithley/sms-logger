# syntax=docker/dockerfile:1

# Use official Python slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of app
COPY . .

# Expose the Flask port
EXPOSE 5000

# Run your app directly
CMD ["python", "app.py"]

