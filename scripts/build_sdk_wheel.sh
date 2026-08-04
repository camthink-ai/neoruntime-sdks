#!/bin/bash
#
# 构建 AIPC SDK wheel 包
#
# 用法:
#   ./build_sdk_wheel.sh
#
# 输出:
#   dist/hailo_ipc_sdk-<version>-py3-none-any.whl
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SDK_DIR="$PROJECT_ROOT/python"
OUTPUT_DIR="$PROJECT_ROOT/dist"

echo "=== 构建 AIPC SDK wheel 包 ==="

# 检查 SDK 目录
if [ ! -d "$SDK_DIR" ]; then
    echo "错误: SDK 目录不存在: $SDK_DIR"
    exit 1
fi

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 进入 SDK 目录
cd "$SDK_DIR"

# 清理旧的构建文件
rm -rf build/ dist/ *.egg-info/

# 安装构建工具
pip install --quiet build wheel

# 构建 wheel
echo "正在构建 wheel..."
python -m build --wheel --outdir "$OUTPUT_DIR"

# 显示结果
echo ""
echo "=== 构建完成 ==="
ls -lh "$OUTPUT_DIR"/*.whl 2>/dev/null || echo "警告: 未找到 wheel 文件"

echo ""
echo "wheel 文件位置: $OUTPUT_DIR/"
echo ""
echo "使用方法:"
echo "  1. 复制到应用目录: cp $OUTPUT_DIR/hailo_ipc_sdk-*.whl ./my-app/"
echo "  2. 在 Dockerfile 中安装:"
echo "     COPY hailo_ipc_sdk-*.whl /tmp/"
echo "     RUN pip install --no-cache-dir /tmp/hailo_ipc_sdk-*.whl"
