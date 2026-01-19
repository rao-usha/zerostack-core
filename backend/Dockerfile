# syntax=docker/dockerfile:1.4
# Backend Dockerfile - Optimized for fast rebuilds
#
# Build commands:
#   DOCKER_BUILDKIT=1 docker build -t nex-backend .                    # Core (fast, no ML)
#   DOCKER_BUILDKIT=1 docker build --build-arg REQUIREMENTS=ml -t nex-backend .   # With ML
#   DOCKER_BUILDKIT=1 docker build --build-arg REQUIREMENTS=full -t nex-backend . # Everything
#
# For CPU-only PyTorch (saves ~1.5GB), use:
#   DOCKER_BUILDKIT=1 docker build --build-arg TORCH_CPU=1 --build-arg REQUIREMENTS=ml -t nex-backend .

FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies and uv (fast Python package installer)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && pip install uv

# -------------------------------------------------------------------
# Dependencies stage - cached separately from application code
# -------------------------------------------------------------------
FROM base AS dependencies

# Build arguments
# REQUIREMENTS: core (default), ml, full
# TORCH_CPU: set to 1 for CPU-only PyTorch (saves ~1.5GB)
ARG REQUIREMENTS=core
ARG TORCH_CPU=0

# Copy only requirements files (cache layer)
COPY requirements*.txt ./

# Install Python dependencies with caching
# uv is 10-100x faster than pip
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/root/.cache/pip \
    if [ "$TORCH_CPU" = "1" ] && [ "$REQUIREMENTS" != "core" ]; then \
        uv pip install --system torch --index-url https://download.pytorch.org/whl/cpu; \
    fi && \
    if [ "$REQUIREMENTS" = "full" ]; then \
        uv pip install --system -r requirements.txt; \
    elif [ "$REQUIREMENTS" = "ml" ]; then \
        uv pip install --system -r requirements-ml.txt; \
    else \
        uv pip install --system -r requirements-core.txt; \
    fi

# -------------------------------------------------------------------
# Final stage - application code (rebuilds fast when only code changes)
# -------------------------------------------------------------------
FROM dependencies AS final

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

