# AIPC Platform Python SDK - 文档和基础镜像

## 目录结构

```
sdk/python/
├── hailo_ipc_sdk/          # SDK 源码
├── docs/                   # Sphinx 文档
│   ├── conf.py            # Sphinx 配置
│   ├── index.rst          # 文档首页
│   ├── installation.rst   # 安装指南
│   ├── quickstart.rst     # 快速开始
│   ├── examples.rst       # 示例代码
│   ├── api/               # API 参考
│   │   ├── inference.rst
│   │   ├── media.rst
│   │   ├── events.rst
│   │   ├── device.rst
│   │   ├── plugin.rst
│   │   └── config.rst
│   ├── build_docs.sh      # 文档构建脚本
│   └── requirements.txt   # 文档依赖
├── Dockerfile.base         # SDK 基础镜像
├── build_base_image.sh     # 基础镜像构建脚本
└── BASE_IMAGE_GUIDE.md     # 基础镜像使用指南
```

## 快速开始

### 1. 构建 Sphinx 文档

```bash
cd sdk/python/docs

# 安装文档依赖
pip install -r requirements.txt

# 构建 HTML 文档
./build_docs.sh

# 查看文档
cd _build/html
python3 -m http.server 8000
# 浏览器打开 http://localhost:8000
```

或使用 Makefile:

```bash
cd sdk/python/docs
make html
```

### 2. 构建 SDK 基础镜像

```bash
cd sdk/python

# 构建 ARM64 镜像（生产环境）
./build_base_image.sh

# 构建 AMD64 镜像（开发测试）
PLATFORM=linux/amd64 ./build_base_image.sh

# 自定义镜像名称
IMAGE_NAME=my-registry/aipc-sdk IMAGE_TAG=1.0.0 ./build_base_image.sh
```

### 3. 使用基础镜像开发应用

创建应用 Dockerfile:

```dockerfile
FROM registry.local/aipc-sdk:0.2.0

# 安装额外依赖（如果需要）
USER root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
USER appuser

# 复制应用代码
COPY app.py app.yaml ./

CMD ["python3", "app.py"]
```

构建应用:

```bash
docker build -t registry.local/my-app:1.0.0 .
```

## 文档功能

### 已包含的文档

1. **安装指南** (`installation.rst`)
   - PyPI 安装
   - 源码安装
   - Tarball 安装
   - Docker 环境
   - 故障排除

2. **快速开始** (`quickstart.rst`)
   - 基本概念
   - 第一个应用
   - 核心功能示例
   - 错误处理
   - 日志记录

3. **API 参考** (`api/`)
   - InferenceClient - AI 推理
   - MediaClient - 视频流
   - EventClient - 事件总线
   - DeviceClient - 设备控制
   - PluginDiscovery/PluginServer - 插件系统
   - Config - 配置管理

4. **示例代码** (`examples.rst`)
   - 人员检测应用
   - 车辆计数应用
   - 智能灯光控制
   - 视频录制应用
   - 多模型融合
   - 插件开发示例

5. **其他**
   - 更新日志 (`changelog.rst`)
   - 贡献指南 (`contributing.rst`)
   - 许可证 (`license.rst`)

### 文档特性

- 使用 Read the Docs 主题
- 自动生成 API 文档（autodoc）
- 支持 Google/NumPy 风格的 docstring
- 中文界面
- 代码高亮
- 搜索功能
- 响应式设计

## 基础镜像功能

### 镜像特性

- **基础**: python:3.10-slim-bookworm
- **架构**: linux/arm64 (支持 Hailo-15, RK3588, Jetson)
- **大小**: ~200MB (优化后)
- **安全**: 非 root 用户运行
- **预装**:
  - hailo-ipc-sdk 0.2.0
  - numpy
  - Pillow
  - opencv-python-headless

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| SDK_VERSION | 0.2.0 | SDK 版本 |
| APP_ID | unknown | 应用 ID |
| DEBUG | 0 | 调试模式 |
| LOG_LEVEL | INFO | 日志级别 |
| AI_RUNTIME_ENDPOINT | unix:///run/aipc/ai-runtime.sock | AI Runtime |
| EVENT_BUS_ENDPOINT | unix:///run/aipc/event-bus.sock | Event Bus |
| DEVICE_CONTROL_ENDPOINT | unix:///run/aipc/device-control.sock | Device Control |

### 目录结构

```
/app/               # 工作目录 (appuser:appuser)
├── data/          # 数据目录
└── logs/          # 日志目录
```

## 集成到开发流程

### 1. 团队开发流程

```bash
# 1. 构建并推送基础镜像（由 SDK 维护者）
cd sdk/python
./build_base_image.sh
docker push registry.local/aipc-sdk:0.2.0

# 2. 开发者使用基础镜像
cd apps/my-app
cat > Dockerfile <<EOF
FROM registry.local/aipc-sdk:0.2.0
COPY app.py app.yaml ./
CMD ["python3", "app.py"]
EOF

docker build -t registry.local/my-app:1.0.0 .
```

### 2. CI/CD 集成

```yaml
# .gitlab-ci.yml 示例
stages:
  - build-sdk
  - build-app
  - test
  - deploy

build-sdk-base:
  stage: build-sdk
  script:
    - cd sdk/python
    - ./build_base_image.sh
    - docker push registry.local/aipc-sdk:${CI_COMMIT_TAG}
  only:
    - tags

build-app:
  stage: build-app
  script:
    - cd apps/my-app
    - docker build -t registry.local/my-app:${CI_COMMIT_TAG} .
    - docker push registry.local/my-app:${CI_COMMIT_TAG}
```

### 3. 本地开发

```bash
# 使用基础镜像进行交互式开发
docker run -it --rm \
    -v $(pwd):/app \
    -v /run/aipc:/run/aipc \
    -e APP_ID=dev_app \
    -e DEBUG=1 \
    registry.local/aipc-sdk:0.2.0 \
    bash

# 在容器内测试代码
python3 app.py
```

## 发布流程

### 发布新版本 SDK

```bash
# 1. 更新版本号
# - sdk/python/setup.py
# - sdk/python/hailo_ipc_sdk/__init__.py
# - sdk/python/Dockerfile.base

# 2. 更新文档
cd sdk/python/docs
# 编辑 changelog.rst
./build_docs.sh

# 3. 构建基础镜像
cd sdk/python
./build_base_image.sh

# 4. 测试镜像
docker run --rm registry.local/aipc-sdk:0.2.0 \
    python3 -c "import hailo_ipc_sdk; print(hailo_ipc_sdk.__version__)"

# 5. 推送到仓库
docker push registry.local/aipc-sdk:0.2.0
docker push registry.local/aipc-sdk:latest

# 6. 发布文档（可选）
# 上传到文档服务器或 GitHub Pages
```

## 维护建议

### 文档维护

1. **保持同步**: 代码更新时同步更新文档
2. **添加示例**: 为新功能添加使用示例
3. **更新 API**: 使用 autodoc 自动生成 API 文档
4. **版本管理**: 在 changelog.rst 中记录变更

### 镜像维护

1. **定期更新**: 更新基础镜像和依赖
2. **安全扫描**: 使用 `docker scan` 检查漏洞
3. **大小优化**: 定期检查镜像大小
4. **多架构支持**: 考虑支持 AMD64 用于开发

### 版本策略

- **SDK 版本**: 遵循语义化版本 (SemVer)
- **镜像标签**:
  - `latest` - 最新稳定版
  - `0.2.0` - 具体版本
  - `0.2.0-arm64` - 架构特定版本

## 故障排除

### 文档构建失败

```bash
# 检查 Sphinx 安装
pip install -r docs/requirements.txt

# 清理构建
cd docs
rm -rf _build
make clean
make html
```

### 镜像构建失败

```bash
# 检查 Docker buildx
docker buildx version

# 创建 builder
docker buildx create --name aipc-builder --use

# 清理缓存
docker builder prune -af
```

### 应用运行失败

```bash
# 检查 SDK 安装
docker run --rm registry.local/aipc-sdk:0.2.0 \
    python3 -c "import hailo_ipc_sdk; print(hailo_ipc_sdk.__version__)"

# 检查权限
docker run --rm registry.local/aipc-sdk:0.2.0 \
    ls -la /app

# 调试模式
docker run --rm -e DEBUG=1 registry.local/aipc-sdk:0.2.0 \
    python3 app.py
```

## 相关文档

- [SDK README](README.md) - SDK 使用说明
- [BASE_IMAGE_GUIDE.md](BASE_IMAGE_GUIDE.md) - 基础镜像详细指南
- [在线文档](http://localhost:8000) - Sphinx 生成的完整文档

## 联系方式

- 问题反馈: https://github.com/aipc/sdk-python/issues
- 邮件: support@aipc.com
