#!/bin/bash
#
# 构建 AIPC 基础镜像
#
# 用法:
#   ./build_base_images.sh [--push]
#
# 选项:
#   --push    构建后推送到镜像仓库
#
# 前置条件:
#   1. 已安装 Docker
#   2. 已构建 SDK wheel (运行 ./scripts/build_sdk_wheel.sh)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$PROJECT_ROOT/python"
DIST_DIR="$PROJECT_ROOT/dist"
BUILD_DIR="$DOCKER_DIR/build"

PUSH=false
REGISTRY="${AIPC_REGISTRY:-}"  # 可选的私有仓库地址

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --push)
            PUSH=true
            shift
            ;;
        *)
            echo "未知参数: $1"
            exit 1
            ;;
    esac
done

echo "=== 构建 AIPC 基础镜像 ==="

# 检查 SDK wheel 是否存在
SDK_WHEEL=$(ls "$DIST_DIR"/hailo_ipc_sdk-*.whl 2>/dev/null | head -1 || true)
if [ -z "$SDK_WHEEL" ]; then
    echo "错误: 未找到 SDK wheel 文件"
    echo "请先运行: ./scripts/build_sdk_wheel.sh"
    exit 1
fi

echo "使用 SDK wheel: $SDK_WHEEL"

# 创建构建目录
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/sdk"

# 复制 SDK wheel 到构建目录
cp "$SDK_WHEEL" "$BUILD_DIR/sdk/"

# 定义要构建的镜像
IMAGES=(
    "Dockerfile.base:aipc/python-base:1.0"
)

# 构建每个镜像
for item in "${IMAGES[@]}"; do
    DOCKERFILE="${item%%:*}"
    IMAGE_TAG="${item#*:}"

    echo ""
    echo "--- 构建 $IMAGE_TAG ---"

    # 如果指定了私有仓库，添加前缀
    FULL_TAG="$IMAGE_TAG"
    if [ -n "$REGISTRY" ]; then
        FULL_TAG="$REGISTRY/$IMAGE_TAG"
    fi

    docker build \
        -f "$DOCKER_DIR/$DOCKERFILE" \
        -t "$FULL_TAG" \
        "$BUILD_DIR"

    echo "构建完成: $FULL_TAG"

    # 推送镜像
    if [ "$PUSH" = true ]; then
        echo "推送镜像: $FULL_TAG"
        docker push "$FULL_TAG"
    fi
done

# 清理构建目录
rm -rf "$BUILD_DIR"

echo ""
echo "=== 构建完成 ==="
echo ""
echo "可用的基础镜像:"
for item in "${IMAGES[@]}"; do
    IMAGE_TAG="${item#*:}"
    if [ -n "$REGISTRY" ]; then
        echo "  $REGISTRY/$IMAGE_TAG"
    else
        echo "  $IMAGE_TAG"
    fi
done

echo ""
echo "导出镜像到 tar 文件:"
echo "  docker save aipc/python-base:1.0 -o python-base.tar"
