#!/bin/bash
# Build AIPC SDK base Docker image for application development

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SDK_DIR="${SCRIPT_DIR}"
IMAGE_NAME="${IMAGE_NAME:-registry.local/aipc-sdk}"
IMAGE_TAG="${IMAGE_TAG:-0.2.0}"
PLATFORM="${PLATFORM:-linux/arm64}"

echo "========================================="
echo "AIPC SDK Base Image Builder"
echo "========================================="
echo ""
echo "Image:    ${IMAGE_NAME}:${IMAGE_TAG}"
echo "Platform: ${PLATFORM}"
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "Error: Docker not found"
    exit 1
fi

# Check if buildx is available for multi-platform builds
if [[ "${PLATFORM}" == *"arm64"* ]] || [[ "${PLATFORM}" == *"amd64"* ]]; then
    if ! docker buildx version &> /dev/null; then
        echo "Warning: Docker buildx not available, using standard build"
        USE_BUILDX=false
    else
        USE_BUILDX=true
        # Create builder if not exists
        if ! docker buildx inspect aipc-builder &> /dev/null 2>&1; then
            echo "Creating buildx builder..."
            docker buildx create --name aipc-builder --use --bootstrap
        else
            docker buildx use aipc-builder
        fi
    fi
else
    USE_BUILDX=false
fi

# Build the image
echo "Building SDK base image..."
echo ""

if [ "${USE_BUILDX}" = true ]; then
    # Multi-platform build with buildx
    docker buildx build \
        --platform "${PLATFORM}" \
        --tag "${IMAGE_NAME}:${IMAGE_TAG}" \
        --tag "${IMAGE_NAME}:latest" \
        --file "${SDK_DIR}/Dockerfile.base" \
        --load \
        "${SDK_DIR}"
else
    # Standard build
    docker build \
        --tag "${IMAGE_NAME}:${IMAGE_TAG}" \
        --tag "${IMAGE_NAME}:latest" \
        --file "${SDK_DIR}/Dockerfile.base" \
        "${SDK_DIR}"
fi

echo ""
echo "========================================="
echo "Build completed successfully!"
echo "========================================="
echo ""
echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""
echo "Image size:"
docker images "${IMAGE_NAME}:${IMAGE_TAG}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
echo ""
echo "Usage:"
echo "  # Test the image"
echo "  docker run --rm ${IMAGE_NAME}:${IMAGE_TAG} python3 -c 'import hailo_ipc_sdk; print(hailo_ipc_sdk.__version__)'"
echo ""
echo "  # Use as base image in your Dockerfile"
echo "  FROM ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""
echo "  # Push to registry"
echo "  docker push ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""
