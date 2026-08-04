#!/bin/bash
#
# AIPC SDK Documentation Build & Deploy Script
# 用于构建和部署SDK文档到本地或远程设备
#
# Usage:
#   ./scripts/deploy_sdk_docs.sh                  # 本地构建并部署
#   ./scripts/deploy_sdk_docs.sh -t root@device   # 部署到远程设备
#   ./scripts/deploy_sdk_docs.sh -b              # 仅构建不部署
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DOCS_DIR="$PROJECT_ROOT/python/docs"
BUILD_DIR="$DOCS_DIR/_build/html"
DEPLOY_PATH="${INSTALL_PREFIX:-/data/aipc}/web/docs"

# ---------- defaults ----------
BUILD_ONLY=false
LOCAL=true
TARGET=""
CLEAN=0

# ---------- colors ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${GREEN}[sdk-docs]${NC} $*"; }
warn() { echo -e "${YELLOW}[sdk-docs]${NC} $*"; }
err()  { echo -e "${RED}[sdk-docs]${NC} $*" >&2; }
info() { echo -e "${CYAN}[sdk-docs]${NC} $*"; }

usage() {
    cat <<'USAGE'
Usage: deploy_sdk_docs.sh [OPTIONS]

Options:
  -t, --target HOST    部署到远程主机 (user@host)
  -b, --build-only     仅构建，不部署
  -c, --clean          构建前清理
  -l, --local          本地部署 (默认)
  -h, --help           显示帮助

Environment:
  SSHPASS              SSH 密码 (配合 sshpass 使用)

Examples:
  # 本地构建并部署
  ./scripts/deploy_sdk_docs.sh

  # 仅构建不部署
  ./scripts/deploy_sdk_docs.sh -b

  # 部署到远程设备
  ./scripts/deploy_sdk_docs.sh -t root@192.168.1.100

  # 清理后重新构建并部署
  ./scripts/deploy_sdk_docs.sh -c -t root@device

Output:
  文档构建位置: python/docs/_build/html/
  部署访问地址: http://<device-ip>:8080/docs/
USAGE
}

# ---------- parse args ----------
while [[ $# -gt 0 ]]; do
    case "$1" in
        -t|--target)
            TARGET="$2"
            LOCAL=false
            shift 2
            ;;
        -b|--build-only)
            BUILD_ONLY=true
            shift
            ;;
        -c|--clean)
            CLEAN=1
            shift
            ;;
        -l|--local)
            LOCAL=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            err "未知选项: $1"
            usage
            exit 1
            ;;
    esac
done

# ---------- check sphinx ----------
if ! command -v sphinx-build &> /dev/null; then
    err "sphinx-build 未安装"
    info "请安装: pip install sphinx sphinx-rtd-theme"
    exit 1
fi

# ---------- build ----------
log "========================================"
log "  构建SDK文档"
log "========================================"

cd "$DOCS_DIR"

# Clean if requested
if [[ $CLEAN -eq 1 ]]; then
    log "清理旧的构建..."
    rm -rf "$DOCS_DIR/_build"
fi

# Install documentation dependencies
log "安装文档依赖..."
pip install -q -r "$DOCS_DIR/requirements.txt" 2>/dev/null || {
    warn "部分依赖安装失败，继续..."
}

# Install SDK (required for autodoc)
log "安装SDK..."
pip install -q -e "$PROJECT_ROOT/python" 2>/dev/null || {
    warn "SDK安装失败，文档可能不完整"
}

# Build HTML documentation
log "构建HTML文档..."
sphinx-build -b html -q . "$BUILD_DIR" || {
    err "文档构建失败"
    info "请检查错误信息: cd $DOCS_DIR && sphinx-build -b html . _build/html"
    exit 1
}

# Get build size
BUILD_SIZE=$(du -sh "$BUILD_DIR" 2>/dev/null | cut -f1)
log "文档构建成功: $BUILD_DIR ($BUILD_SIZE)"

# Check if index.html exists
if [[ ! -f "$BUILD_DIR/index.html" ]]; then
    err "构建失败: index.html 不存在"
    exit 1
fi

log "  入口文件: $BUILD_DIR/index.html"
log ""

# ---------- deploy ----------
if [[ "$BUILD_ONLY" == true ]]; then
    log "仅构建模式，跳过部署"
    log ""
    log "本地查看文档:"
    log "  cd $BUILD_DIR && python3 -m http.server 8000"
    log "  访问: http://localhost:8000"
    exit 0
fi

if [[ "$LOCAL" == true ]]; then
    # ---------- local deploy ----------
    log "========================================"
    log "  本地部署"
    log "========================================"
    log "目标路径: $DEPLOY_PATH"

    if [[ $EUID -ne 0 ]]; then
        warn "本地部署需要root权限，使用sudo..."
        if ! sudo -n true 2>/dev/null; then
            sudo mkdir -p "$DEPLOY_PATH"
            sudo rm -rf "$DEPLOY_PATH"/*
            sudo cp -r "$BUILD_DIR"/* "$DEPLOY_PATH/"
            sudo chown -R root:root "$DEPLOY_PATH"
        else
            err "需要sudo权限"
            exit 1
        fi
    else
        mkdir -p "$DEPLOY_PATH"
        rm -rf "$DEPLOY_PATH"/*
        cp -r "$BUILD_DIR"/* "$DEPLOY_PATH/"
    fi

    log "部署完成"
    log "访问地址: http://$(hostname -I | awk '{print $1}'):8080/docs/"

else
    # ---------- remote deploy ----------
    log "========================================"
    log "  远程部署"
    log "========================================"
    log "目标主机: $TARGET"
    log "部署路径: $DEPLOY_PATH"

    # 支持 sshpass 或 SSH 密钥认证
    ssh_prefix=""
    if command -v sshpass &> /dev/null && [ -n "$SSHPASS" ]; then
        ssh_prefix="sshpass -e"
        log "使用sshpass密码认证"
    else
        log "使用SSH密钥认证"
    fi

    # 创建远程目录
    info "创建远程目录..."
    $ssh_prefix ssh -o StrictHostKeyChecking=no "$TARGET" "mkdir -p $DEPLOY_PATH" || {
        err "SSH连接失败"
        exit 1
    }

    # 清空并复制文件
    info "复制文件..."
    $ssh_prefix ssh -o StrictHostKeyChecking=no "$TARGET" "rm -rf $DEPLOY_PATH/*"
    $ssh_prefix scp -o StrictHostKeyChecking=no -r "$BUILD_DIR"/* "$TARGET:$DEPLOY_PATH/" || {
        err "文件复制失败"
        exit 1
    }

    # Verify deployment
    info "验证部署..."
    REMOTE_FILES=$($ssh_prefix ssh -o StrictHostKeyChecking=no "$TARGET" "ls -1 $DEPLOY_PATH/index.html 2>/dev/null" || echo "")
    if [[ -z "$REMOTE_FILES" ]]; then
        warn "部署验证失败，但文件可能已复制"
    fi

    # Extract IP from target
    REMOTE_IP=$(echo "$TARGET" | cut -d@ -f2 | cut -d: -f1)

    log "部署完成"
    log "访问地址: http://$REMOTE_IP:8080/docs/"
fi

log ""
log "========================================"
log "  完成!"
log "========================================"
