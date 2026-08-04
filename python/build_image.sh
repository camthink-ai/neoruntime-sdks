#!/bin/bash
# Build ARM64 Docker image for AIPC Platform SDK

set -e

SDK_DIR="$(cd "$(dirname "$0")" && pwd)"
IMAGE_NAME="aipc-sdk"
IMAGE_TAG="0.2.0-arm64"

echo "========================================="
echo "AIPC Platform SDK - ARM64 Docker Build"
echo "========================================="
echo ""
echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "Platform: linux/arm64"
echo ""

# Check if Docker supports buildx
if ! docker buildx version &> /dev/null; then
    echo "Error: Docker buildx not available"
    echo "Please enable buildx: docker buildx install"
    exit 1
fi

# Create buildx builder if not exists
if ! docker buildx inspect aipc-builder &> /dev/null; then
    echo "Creating buildx builder..."
    docker buildx create --name aipc-builder --use
fi

# Build the image
echo "Building image..."
docker buildx build \
    --platform linux/arm64 \
    --tag ${IMAGE_NAME}:${IMAGE_TAG} \
    --tag ${IMAGE_NAME}:latest \
    --load \
    -f Dockerfile \
    .

echo ""
echo "========================================="
echo "Build completed!"
echo "========================================="
echo ""
echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""
echo "Usage:"
echo "  docker run --rm ${IMAGE_NAME}:${IMAGE_TAG} python3 examples/person_detection.py"
echo ""