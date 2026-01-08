FROM python:3.9-slim

WORKDIR /app

# Install all necessary libraries: psutil, requests, docker, prometheus_client
RUN apt-get update && apt-get install -y gcc python3-dev && \
    pip install --no-cache-dir psutil requests docker prometheus_client && \
    apt-get purge -y --auto-remove gcc python3-dev && rm -rf /var/lib/apt/lists/*

COPY monitor.py .

# Expose metrics port
EXPOSE 8000

CMD ["python", "monitor.py"]
