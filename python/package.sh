#!/bin/bash
# Create SDK package tarball

set -e

SDK_DIR="$(cd "$(dirname "$0")" && pwd)"
PACKAGE_NAME="aipc-sdk-0.2.0-arm64"
OUTPUT_DIR="${SDK_DIR}/dist"

echo "========================================="
echo "Creating SDK Package"
echo "========================================="
echo ""

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Create temp directory
TEMP_DIR=$(mktemp -d)
PACKAGE_DIR="${TEMP_DIR}/${PACKAGE_NAME}"

echo "Packaging to: ${PACKAGE_DIR}"

# Copy files
mkdir -p "${PACKAGE_DIR}/hailo_ipc_sdk"
mkdir -p "${PACKAGE_DIR}/examples"
mkdir -p "${PACKAGE_DIR}/tests"

cp -r "${SDK_DIR}/hailo_ipc_sdk/"* "${PACKAGE_DIR}/hailo_ipc_sdk/"
cp -r "${SDK_DIR}/examples/"* "${PACKAGE_DIR}/examples/"
cp -r "${SDK_DIR}/tests/"* "${PACKAGE_DIR}/tests/"

cp "${SDK_DIR}/setup.py" "${PACKAGE_DIR}/"
cp "${SDK_DIR}/README.md" "${PACKAGE_DIR}/"
cp "${SDK_DIR}/requirements.txt" "${PACKAGE_DIR}/"
cp "${SDK_DIR}/Dockerfile" "${PACKAGE_DIR}/"
cp "${SDK_DIR}/build_image.sh" "${PACKAGE_DIR}/"

# Create tarball
echo "Creating tarball..."
cd "${TEMP_DIR}"
tar -czvf "${OUTPUT_DIR}/${PACKAGE_NAME}.tar.gz" "${PACKAGE_NAME}"

# Cleanup
rm -rf "${TEMP_DIR}"

echo ""
echo "========================================="
echo "Package created!"
echo "========================================="
echo ""
echo "Output: ${OUTPUT_DIR}/${PACKAGE_NAME}.tar.gz"
echo ""
ls -lh "${OUTPUT_DIR}/${PACKAGE_NAME}.tar.gz"
echo ""