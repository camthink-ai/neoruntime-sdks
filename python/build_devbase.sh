#!/bin/bash
# Build AIPC SDK dev base image and import to containerd
# 在设备上构建开发工作台基础镜像

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
IMAGE_NAME="aipc/sdk-python"
IMAGE_TAG="1.0.0"
NAMESPACE="aipc"

echo "========================================="
echo "Building AIPC SDK Dev Base Image"
echo "========================================="
echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""

# Check if running on target device
if ! command -v ctr &> /dev/null; then
    echo "Error: containerd (ctr) not found. Run this on target device."
    exit 1
fi

# Build with docker/nerdctl if available, otherwise use buildah
if command -v docker &> /dev/null; then
    BUILD_CMD="docker"
elif command -v nerdctl &> /dev/null; then
    BUILD_CMD="nerdctl"
elif command -v buildah &> /dev/null; then
    BUILD_CMD="buildah"
else
    echo "Error: No container build tool found (docker/nerdctl/buildah)"
    exit 1
fi

echo "Using build tool: ${BUILD_CMD}"
echo ""

# Build the image
echo "Building image..."
cd "${SCRIPT_DIR}"

if [ "${BUILD_CMD}" = "buildah" ]; then
    buildah bud -t "${IMAGE_NAME}:${IMAGE_TAG}" -f Dockerfile.devbase .
    buildah push "${IMAGE_NAME}:${IMAGE_TAG}" oci-archive:/tmp/sdk-python.tar
    ctr -n ${NAMESPACE} images import /tmp/sdk-python.tar
    rm -f /tmp/sdk-python.tar
else
    ${BUILD_CMD} build -t "${IMAGE_NAME}:${IMAGE_TAG}" -f Dockerfile.devbase .

    # Export and import to containerd
    echo "Importing to containerd namespace ${NAMESPACE}..."
    ${BUILD_CMD} save "${IMAGE_NAME}:${IMAGE_TAG}" | ctr -n ${NAMESPACE} images import -
fi

echo ""
echo "========================================="
echo "Build completed!"
echo "========================================="
echo ""
echo "Verify with:"
echo "  ctr -n ${NAMESPACE} images list | grep sdk-python"
echo ""
