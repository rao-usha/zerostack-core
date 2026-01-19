# Backend Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Build argument to choose requirements file
# Default: core (fast, no PyTorch)
# Options: core, ml, full
ARG REQUIREMENTS=core

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy all requirements files for flexibility
COPY requirements*.txt ./

# Install Python dependencies based on build arg
# - core: Fast install, no ML/PyTorch (~2 min)
# - ml: Includes SDV/PyTorch (~10 min)
# - full: Everything including test deps
RUN pip install --upgrade pip && \
    if [ "$REQUIREMENTS" = "full" ]; then \
        pip install -r requirements.txt; \
    elif [ "$REQUIREMENTS" = "ml" ]; then \
        pip install -r requirements-ml.txt; \
    else \
        pip install -r requirements-core.txt; \
    fi

# Copy application code
COPY . .

# Create data storage directory
RUN mkdir -p data_storage

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

