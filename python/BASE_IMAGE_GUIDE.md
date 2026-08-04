# AIPC SDK Base Image - 使用指南

## 概述

这是 AIPC Platform Python SDK 的基础镜像，预装了 SDK 和常用依赖，供应用开发使用。

## 镜像信息

- **基础镜像**: python:3.10-slim-bookworm
- **架构**: linux/arm64 (支持 Hailo-15, RK3588, Jetson)
- **SDK 版本**: 0.2.0
- **预装依赖**:
  - hailo-ipc-sdk
  - numpy
  - Pillow
  - opencv-python-headless

## 构建基础镜像

### 方法 1: 使用构建脚本（推荐）

```bash
cd sdk/python

# 构建 ARM64 镜像
./build_base_image.sh

# 自定义镜像名称和标签
IMAGE_NAME=my-registry/aipc-sdk IMAGE_TAG=1.0.0 ./build_base_image.sh

# 构建 AMD64 镜像（用于开发测试）
PLATFORM=linux/amd64 ./build_base_image.sh
```

### 方法 2: 手动构建

```bash
cd sdk/python

# ARM64
docker buildx build \
    --platform linux/arm64 \
    --tag registry.local/aipc-sdk:0.2.0 \
    --tag registry.local/aipc-sdk:latest \
    --file Dockerfile.base \
    --load \
    .

# AMD64（开发测试）
docker build \
    --tag registry.local/aipc-sdk:0.2.0-amd64 \
    --file Dockerfile.base \
    .
```

## 使用基础镜像开发应用

### 示例 1: 简单应用

```dockerfile
# apps/my-app/Dockerfile
FROM registry.local/aipc-sdk:0.2.0

# 复制应用代码
COPY app.py app.yaml ./

# 应用已经以 appuser 运行，无需额外配置
CMD ["python3", "app.py"]
```

### 示例 2: 带额外依赖的应用

```dockerfile
FROM registry.local/aipc-sdk:0.2.0

# 切换到 root 安装依赖
USER root

# 安装额外的 Python 包
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装系统包（如果需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfoo-dev \
    && rm -rf /var/lib/apt/lists/*

# 切换回 appuser
USER appuser

# 复制应用代码
COPY app.py app.yaml ./

CMD ["python3", "app.py"]
```

### 示例 3: 多文件应用

```dockerfile
FROM registry.local/aipc-sdk:0.2.0

USER root

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

USER appuser

# 复制应用目录
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser config/ ./config/
COPY --chown=appuser:appuser app.py app.yaml ./

# 设置 Python 路径
ENV PYTHONPATH=/app

CMD ["python3", "app.py"]
```

## 应用开发模板

### 完整的应用 Dockerfile

```dockerfile
# ============================================
# Stage 1: Dependencies (optional)
# ============================================
FROM registry.local/aipc-sdk:0.2.0 AS builder

USER root

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ make \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================
# Stage 2: Runtime
# ============================================
FROM registry.local/aipc-sdk:0.2.0

USER root

# 从 builder 复制依赖
COPY --from=builder /app/.local /app/.local

USER appuser

# 设置 PATH
ENV PATH=/app/.local/bin:$PATH

# 复制应用代码
COPY --chown=appuser:appuser . .

# 应用配置
ENV APP_ID=my_app \
    LOG_LEVEL=INFO

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)"

CMD ["python3", "app.py"]
```

### 应用代码示例 (app.py)

```python
#!/usr/bin/env python3
"""
AIPC 应用示例
"""

from hailo_ipc_sdk import InferenceClient, EventClient, DeviceClient
import logging
import signal
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MyApp:
    def __init__(self):
        self.running = True
        self.inf = InferenceClient()
        self.events = EventClient()
        self.dev = DeviceClient()

        # 注册信号处理
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def shutdown(self, signum, frame):
        logger.info("收到停止信号，正在关闭...")
        self.running = False

    def run(self):
        logger.info("应用启动")

        try:
            # 订阅视频流推理
            for frame_seq, result in self.inf.subscribe(
                stream="cam0_main",
                model="person_v1",
                fps=10
            ):
                if not self.running:
                    break

                # 处理推理结果
                if result.objects:
                    logger.info(f"帧 {frame_seq}: 检测到 {len(result.objects)} 个对象")

                    # 发布事件
                    self.events.publish("app/my_app/detection", {
                        "frame": frame_seq,
                        "count": len(result.objects)
                    })

        except Exception as e:
            logger.error(f"应用错误: {e}", exc_info=True)
            sys.exit(1)

        logger.info("应用停止")

if __name__ == "__main__":
    app = MyApp()
    app.run()
```

## 构建和测试应用

```bash
# 构建应用镜像
cd apps/my-app
docker build -t registry.local/my-app:1.0.0 .

# 本地测试
docker run --rm \
    -v /run/aipc:/run/aipc \
    -e APP_ID=my_app \
    -e DEBUG=1 \
    registry.local/my-app:1.0.0

# 推送到仓库
docker push registry.local/my-app:1.0.0
```

## 环境变量

基础镜像预设了以下环境变量：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SDK_VERSION` | 0.2.0 | SDK 版本 |
| `APP_ID` | unknown | 应用 ID |
| `DEBUG` | 0 | 调试模式 |
| `LOG_LEVEL` | INFO | 日志级别 |
| `AI_RUNTIME_ENDPOINT` | unix:///run/aipc/ai-runtime.sock | AI Runtime 端点 |
| `EVENT_BUS_ENDPOINT` | unix:///run/aipc/event-bus.sock | Event Bus 端点 |
| `DEVICE_CONTROL_ENDPOINT` | unix:///run/aipc/device-control.sock | Device Control 端点 |
| `SHM_BASE_PATH` | /run/aipc/shm | 共享内存路径 |
| `PYTHONUNBUFFERED` | 1 | Python 输出不缓冲 |

## 目录结构

```
/app/               # 应用工作目录
├── data/          # 数据目录
├── logs/          # 日志目录
└── [your files]   # 你的应用文件
```

## 用户和权限

- 默认用户: `appuser` (UID: 1000, GID: 1000)
- 工作目录: `/app` (属主: appuser)
- 建议: 保持使用非 root 用户运行应用

## 推送到私有仓库

```bash
# 登录仓库
docker login registry.local

# 推送镜像
docker push registry.local/aipc-sdk:0.2.0
docker push registry.local/aipc-sdk:latest

# 在其他机器拉取
docker pull registry.local/aipc-sdk:0.2.0
```

## 故障排除

### 镜像构建失败

```bash
# 检查 Docker 版本
docker --version

# 检查 buildx
docker buildx version

# 清理构建缓存
docker builder prune -af
```

### 应用运行失败

```bash
# 检查镜像
docker run --rm registry.local/aipc-sdk:0.2.0 python3 -c "import hailo_ipc_sdk; print(hailo_ipc_sdk.__version__)"

# 进入容器调试
docker run --rm -it registry.local/aipc-sdk:0.2.0 /bin/bash

# 查看日志
docker logs <container_id>
```

## 最佳实践

1. **使用多阶段构建**: 减小最终镜像体积
2. **固定版本**: 使用具体版本号而非 latest
3. **最小权限**: 使用非 root 用户运行
4. **健康检查**: 添加 HEALTHCHECK 指令
5. **环境变量**: 通过环境变量配置应用
6. **日志输出**: 输出到 stdout/stderr
7. **优雅退出**: 处理 SIGTERM 信号

## 相关文档

- [SDK 文档](../docs/_build/html/index.html)
- [应用开发指南](../../docs/APP_DEVELOPMENT.md)
- [app.yaml 配置](../../docs/APP_MANIFEST.md)
