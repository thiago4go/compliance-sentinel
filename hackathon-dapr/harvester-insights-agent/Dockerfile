FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y     gcc     libpq-dev     build-essential     git     && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip cache purge
RUN pip install --no-cache-dir git+https://github.com/dapr/dapr-agents.git
RUN pip check || true
RUN pip list
RUN ls -l /usr/local/lib/python3.11/site-packages/dapr_agents
RUN pip install --no-cache-dir -r requirements.txt
RUN pip check || true
RUN pip list
RUN pip install --no-cache-dir dapr dapr-ext-grpc
RUN pip check || true
RUN pip list

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9180/health || exit 1

# Expose port
EXPOSE 9180

# Run the application
CMD ["python", "harvester_agent.py"]
