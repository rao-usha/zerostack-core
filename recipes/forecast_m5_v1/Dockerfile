# M5 Forecasting Recipe Container
# Trains a LightGBM model on M5 retail data and produces forecasts

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY run.py .

# Environment variables (set at runtime by compute adapter)
ENV RUN_ID=""
ENV INPUT_URI=""
ENV OUTPUT_URI=""
ENV PARAMS_JSON="{}"
ENV S3_ENDPOINT=""
ENV S3_ACCESS_KEY=""
ENV S3_SECRET_KEY=""
ENV S3_BUCKET=""

# Run the forecasting script
ENTRYPOINT ["python", "run.py"]
