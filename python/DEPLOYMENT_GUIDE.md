# SDK文档部署集成指南

## 概述

SDK文档构建已集成到AIPC平台的打包和部署流程中。文档通过Sphinx自动生成，作为静态HTML文件部署到设备的 `/opt/aipc/web/docs/` 目录。

## 架构

```
┌─────────────────────────────────────────────────┐
│           构建阶段 (开发机)                      │
├─────────────────────────────────────────────────┤
│  1. pack_release.sh                            │
│     ├── 构建Web Console (web/dist)             │
│     └── 构建SDK文档 (sdk/python/docs/_build)   │
│                                                  │
│  2. 打包到发布tarball                           │
│     └── opt/aipc/web/{console, docs}           │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│           部署阶段 (目标设备)                    │
├─────────────────────────────────────────────────┤
│  deploy.sh 自动部署整个 /opt/aipc/web/ 目录    │
│                                                  │
│  访问: http://<device-ip>:8080/docs/            │
└─────────────────────────────────────────────────┘
```

## 使用方式

### 方式1: 集成到发布包 (推荐)

**打包时自动包含SDK文档：**

```bash
cd /home/work/ne503
./scripts/pack_release.sh --sdk-path /path/to/hailo-sdk

# 生成的tarball会包含:
# - opt/aipc/web/           # Web控制台
# - opt/aipc/web/docs/      # SDK文档 (新增)
```

**部署到设备：**

```bash
# 复制到设备
scp build/release/aipc-hailo15-*.tar.gz root@<device>:/tmp/

# 在设备上执行
ssh root@<device>
cd /tmp && tar xzf aipc-hailo15-*.tar.gz
cd aipc-hailo15-*
./deploy.sh

# 文档自动部署到 /opt/aipc/web/docs/
```

**访问文档：**

```
http://<device-ip>:8080/docs/
```

### 方式2: 单独部署SDK文档

**本地构建并部署：**

```bash
# 构建并部署到本地
./scripts/deploy_sdk_docs.sh

# 仅构建不部署
./scripts/deploy_sdk_docs.sh -b

# 清理后重新构建
./scripts/deploy_sdk_docs.sh -c
```

**远程部署：**

```bash
# 部署到远程设备 (SSH密钥认证)
./scripts/deploy_sdk_docs.sh -t root@192.168.1.100

# 使用密码认证
SSHPASS='password' ./scripts/deploy_sdk_docs.sh -t root@device

# 清理后构建并部署
./scripts/deploy_sdk_docs.sh -c -t root@device
```

**本地查看（调试用）：**

```bash
# 仅构建
./scripts/deploy_sdk_docs.sh -b

# 启动本地服务器
cd sdk/python/docs/_build/html
python3 -m http.server 8000

# 访问: http://localhost:8000
```

### 方式3: 使用deploy_web.sh (Web控制台一起)

deploy_web.sh已支持Web控制台部署，可以扩展为同时部署文档：

```bash
# 构建Web控制台和SDK文档
./scripts/deploy_web.sh -b

# 部署到远程设备
./scripts/deploy_web.sh -t root@device
```

## 文件结构

### 构建产物

```
sdk/python/docs/_build/html/
├── index.html              # 文档首页
├── installation.html       # 安装指南
├── quickstart.html         # 快速开始
├── api/                    # API参考
│   ├── inference.html
│   ├── media.html
│   └── ...
├── examples.html           # 示例代码
├── _static/                # 静态资源
│   ├── css/
│   ├── js/
│   └── fonts/
└── search.html             # 搜索页面
```

### 部署位置

```
设备上:
/opt/aipc/web/
├── index.html              # Web控制台主页
├── assets/                 # Web控制台资源
└── docs/                   # SDK文档 (新增)
    ├── index.html
    ├── installation.html
    └── ...
```

## 依赖要求

### 构建依赖

```bash
# Sphinx文档框架
pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints

# Python SDK依赖 (用于autodoc)
pip install -e sdk/python

# 文档依赖
pip install -r sdk/python/docs/requirements.txt
```

### 系统依赖

```bash
# 基础工具
apt install python3-pip

# SSH工具 (远程部署)
apt install openssh-client sshpass
```

## CI/CD集成

### GitLab CI示例

```yaml
stages:
  - build
  - deploy

build_docs:
  stage: build
  script:
    - pip install -r sdk/python/docs/requirements.txt
    - cd sdk/python/docs && ./build_docs.sh
  artifacts:
    paths:
      - sdk/python/docs/_build/html/
    expire_in: 1 week

deploy_device:
  stage: deploy
  dependencies:
    - build_docs
  script:
    - ./scripts/deploy_sdk_docs.sh -t root@$DEVICE_IP
  only:
    - tags
```

### Makefile集成

```makefile
.PHONY: docs docs-deploy

docs:
	cd sdk/python/docs && ./build_docs.sh

docs-deploy:
	./scripts/deploy_sdk_docs.sh -t root@$(DEVICE_IP)

docs-view:
	cd sdk/python/docs/_build/html && python3 -m http.server 8000
```

## 故障排除

### 构建失败

```bash
# 检查Sphinx安装
pip install sphinx sphinx-rtd-theme

# 清理后重新构建
rm -rf sdk/python/docs/_build
cd sdk/python/docs && ./build_docs.sh

# 检查SDK安装
pip install -e sdk/python
```

### 部署失败

```bash
# 检查SSH连接
ssh root@<device-ip>

# 检查目录权限
ssh root@<device-ip> "ls -la /opt/aipc/web/"

# 手动创建目录
ssh root@<device-ip> "mkdir -p /opt/aipc/web/docs"
```

### 无法访问文档

```bash
# 检查platform-api状态
ssh root@<device-ip> "systemctl status platform-api"

# 检查文件是否存在
ssh root@<device-ip> "ls -la /opt/aipc/web/docs/index.html"

# 检查配置
ssh root@<device-ip> "cat /opt/aipc/etc/platform-api.yaml | grep static_path"
```

## 维护指南

### 更新文档内容

1. 编辑RST源文件: `sdk/python/docs/*.rst`
2. 重新构建: `./scripts/deploy_sdk_docs.sh -c`
3. 重新部署: `./scripts/deploy_sdk_docs.sh`

### 更新API文档

API文档通过autodoc自动从代码docstring生成，只需：

1. 更新代码中的docstring
2. 重新构建部署

### 版本控制

建议将构建后的HTML文档也纳入版本控制：

```bash
# 添加到.gitignore (开发时)
echo "sdk/python/docs/_build/" >> .gitignore

# 但在发布时包含
# pack_release.sh会自动打包
```

## 相关文档

- [SDK文档开发指南](sdk/python/README.md)
- [Sphinx文档](https://www.sphinx-doc.org/)
- [平台部署指南](scripts/README.md)
