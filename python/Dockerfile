# AIPC Platform ARM64 SDK Docker Image
# For ARM architecture (aarch64)

FROM python:3.10-slim-bookworm

LABEL maintainer="aipc@example.com"
LABEL version="0.2.0"
LABEL description="AIPC Platform Python SDK - ARM64"
LABEL architecture="arm64"

# Set platform
ARG TARGETPLATFORM=linux/arm64

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy SDK
COPY hailo_ipc_sdk /app/hailo_ipc_sdk
COPY setup.py /app/
COPY README.md /app/
COPY requirements.txt /app/

# Install SDK and dependencies
RUN pip install --no-cache-dir -e .

# Install optional dependencies for examples
RUN pip install --no-cache-dir \
    numpy \
    opencv-python-headless

# Copy examples
COPY examples /app/examples

# Create directories
RUN mkdir -p /app/logs /app/data

# Set environment variables
ENV APP_ID=sdk_example
ENV DEBUG=0
ENV LOG_LEVEL=INFO
ENV PYTHONUNBUFFERED=1

# Default entry point
CMD ["python3", "-m", "hailo_ipc_sdk"]