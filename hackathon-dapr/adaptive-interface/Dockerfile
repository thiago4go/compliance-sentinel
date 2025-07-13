FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Dapr CLI
RUN wget -q https://raw.githubusercontent.com/dapr/cli/master/install/install.sh -O - | /bin/bash

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose ports for production (9150-9152)
EXPOSE 9150 9151 9152

# Default command - run the working app
CMD ["chainlit", "run", "working-chainlit-app.py", "--port", "9150", "--host", "0.0.0.0"]
