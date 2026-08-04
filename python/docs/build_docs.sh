#!/bin/bash
# Build Sphinx documentation for AIPC Platform Python SDK

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOCS_DIR="${SCRIPT_DIR}"
BUILD_DIR="${DOCS_DIR}/_build"

echo "========================================="
echo "Building AIPC SDK Documentation"
echo "========================================="
echo ""

# Check if sphinx-build is available
if ! command -v sphinx-build &> /dev/null; then
    echo "Error: sphinx-build not found"
    echo "Please install Sphinx: pip install -r requirements.txt"
    exit 1
fi

# Install documentation dependencies
echo "Installing documentation dependencies..."
pip install -q -r "${DOCS_DIR}/requirements.txt"

# Install SDK dependencies (required for autodoc to import hailo_ipc_sdk)
echo "Installing SDK dependencies..."
pip install -q -e "${SCRIPT_DIR}/.."

# Clean previous build
if [ -d "${BUILD_DIR}" ]; then
    echo "Cleaning previous build..."
    rm -rf "${BUILD_DIR}"
fi

# Build HTML documentation
echo ""
echo "Building HTML documentation..."
cd "${DOCS_DIR}"
sphinx-build -b html . "${BUILD_DIR}/html"

# Build PDF documentation (optional)
if command -v make &> /dev/null && command -v pdflatex &> /dev/null; then
    echo ""
    echo "Building PDF documentation..."
    make latexpdf
fi

echo ""
echo "========================================="
echo "Documentation built successfully!"
echo "========================================="
echo ""
echo "HTML: ${BUILD_DIR}/html/index.html"
if [ -f "${BUILD_DIR}/latex/aipcplatformpythonsdk.pdf" ]; then
    echo "PDF:  ${BUILD_DIR}/latex/aipcplatformpythonsdk.pdf"
fi
echo ""
echo "To view the documentation:"
echo "  cd ${BUILD_DIR}/html && python3 -m http.server 8000"
echo "  Then open http://localhost:8000 in your browser"
echo ""
