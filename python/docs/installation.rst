安装指南
========

系统要求
--------

- Python 3.8 或更高版本
- SDK 开发和测试支持 Linux x86_64 或 ARM64
- 连接真实设备能力时需要 NE503 AIPC Platform 运行环境

依赖项
------

SDK 依赖以下 Python 包：

- ``grpcio >= 1.50.0`` - gRPC 通信
- ``protobuf >= 4.21.0`` - Protocol Buffers
- ``numpy >= 1.20.0`` - 数组处理
- ``Pillow >= 9.0.0`` - 图像处理

安装方法
--------

从源码安装
~~~~~~~~~~

SDK 暂未发布到 PyPI。当前请从公开仓库源码安装：

.. code-block:: bash

   git clone https://github.com/camthink-ai/ne503-aipc-sdks.git
   cd ne503-aipc-sdks
   python -m pip install -e ./python

构建 Wheel 包
~~~~~~~~~~~~~

.. code-block:: bash

   cd ne503-aipc-sdks/python
   python -m pip install --upgrade build
   python -m build --wheel
   ls dist/*.whl

生成的 ``.whl`` 文件位于 ``dist/`` 目录，可直接安装验证：

.. code-block:: bash

   python -m pip install dist/hailo_ipc_sdk-*.whl

GitHub Actions Wheel Artifact
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

公开仓库会通过 GitHub Actions 构建 Python wheel。进入
``Actions`` -> ``Build Python SDK wheel``，可在成功运行中下载
``python-sdk-wheel`` artifact。

维护者也可以推送匹配版本的 tag，或手动运行 workflow 并开启 release
发布选项，生成 GitHub Release。

计划中的发布渠道
~~~~~~~~~~~~~~~~

PyPI 和 tarball 包目前尚未发布。在正式公告前，不要使用
``pip install hailo-ipc-sdk`` 或 tarball URL。

后续启用 PyPI 发布后，安装方式会是：

.. code-block:: bash

   python -m pip install hailo-ipc-sdk

验证安装
--------

.. code-block:: python

   import hailo_ipc_sdk
   print(hailo_ipc_sdk.__version__)
   # 输出: 0.3.0

开发环境安装
------------

如果你需要开发或测试 SDK，可以安装开发依赖：

.. code-block:: bash

   pip install -e ".[dev]"

这将安装额外的工具：

- ``pytest`` - 单元测试
- ``pytest-cov`` - 测试覆盖率
- ``black`` - 代码格式化
- ``flake8`` - 代码检查
- ``mypy`` - 类型检查

Docker 环境
-----------

使用当前公开源码仓库：

.. code-block:: dockerfile

   FROM python:3.11-slim
   RUN apt-get update \
       && apt-get install -y --no-install-recommends git \
       && rm -rf /var/lib/apt/lists/*
   RUN python -m pip install --no-cache-dir \
       "git+https://github.com/camthink-ai/ne503-aipc-sdks.git#subdirectory=python"

或者构建自己的镜像：

.. code-block:: dockerfile

   FROM python:3.10-slim
   COPY hailo_ipc_sdk-0.3.0-py3-none-any.whl /tmp/
   RUN python -m pip install --no-cache-dir /tmp/hailo_ipc_sdk-0.3.0-py3-none-any.whl
   WORKDIR /app
   COPY app.py .
   CMD ["python3", "app.py"]

故障排除
--------

权限问题
~~~~~~~~

如果遇到 Unix socket 权限错误：

.. code-block:: bash

   # 确保用户在 aipc 组中
   sudo usermod -aG aipc $USER

   # 重新登录或刷新组
   newgrp aipc

gRPC 连接失败
~~~~~~~~~~~~~

检查平台服务是否运行：

.. code-block:: bash

   # 检查服务状态
   systemctl status ai-runtime
   systemctl status event-bus
   systemctl status device-control

   # 检查 socket 文件
   ls -l /run/aipc/*.sock

依赖冲突
~~~~~~~~

如果遇到依赖版本冲突，建议使用虚拟环境：

.. code-block:: bash

   python3 -m venv venv
   source venv/bin/activate
   git clone https://github.com/camthink-ai/ne503-aipc-sdks.git
   python -m pip install -e ne503-aipc-sdks/python
