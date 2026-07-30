应用镜像制作与导入指南
========================

概述
----

本指南介绍如何在开发环境中制作应用 Docker 镜像，并将镜像导入到 AIPC 设备上运行。

完整流程包括：

#. 准备应用文件（Dockerfile、app.py）
#. 构建 Docker 镜像
#. 导出镜像为 tar 文件
#. 通过 Web Console 应用安装向导导入，或使用命令行导入

.. tip::

   Web Console 提供了图形化的 **应用安装向导**，支持上传镜像文件并逐步配置应用参数，
   无需手动编辑 app.yaml 或使用 SCP 传输文件。推荐优先使用 Web Console 方式。

.. _app_image_step1:

步骤 1: 准备应用文件
--------------------

创建应用目录并准备以下两个核心文件。应用配置（元数据、权限、资源等）将在 Web Console 安装向导中填写。

创建应用目录
~~~~~~~~~~~~

.. code-block:: bash

   mkdir my-app && cd my-app

应用代码（app.py）
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   #!/usr/bin/env python3
   """My Application"""

   import signal
   import sys
   from hailo_ipc_sdk import InferenceClient, EventClient, DeviceClient, Config


   class MyApp:
       def __init__(self):
           self.running = True
           self.app_id = Config.get_app_id()

           self.inference = InferenceClient()
           self.events = EventClient()
           self.device = DeviceClient()

           signal.signal(signal.SIGINT, self.signal_handler)
           signal.signal(signal.SIGTERM, self.signal_handler)

       def signal_handler(self, signum, frame):
           self.running = False

       def run(self):
           try:
               for frame, result in self.inference.subscribe(
                   stream="cam0_main", model="person_v1", fps=10
               ):
                   if not self.running:
                       break
                   person_count = result.count_by_label("person")
                   if person_count > 0:
                       self.events.publish(f"app/{self.app_id}/detection", {
                           "count": person_count,
                       })
           except Exception as e:
               print(f"[{self.app_id}] Error: {e}")
           finally:
               self.inference.close()
               self.events.close()
               self.device.close()


   if __name__ == "__main__":
       MyApp().run()

Dockerfile
~~~~~~~~~~

.. code-block:: dockerfile

   FROM python:3.9-slim

   LABEL maintainer="your@email.com"

   # 从公开源码仓库安装 NE503 Python SDK。
   # SDK 暂未发布到 PyPI。
   RUN apt-get update \
       && apt-get install -y --no-install-recommends git \
       && rm -rf /var/lib/apt/lists/*
   RUN python -m pip install --no-cache-dir \
       "git+https://github.com/camthink-ai/ne503-aipc-sdks.git#subdirectory=python"

   WORKDIR /app
   COPY app.py app.yaml /app/

   RUN mkdir -p /app/logs /app/data

   # 非 root 用户（推荐）
   RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
   USER appuser

   ENV APP_ID=my_app
   ENV DEBUG=0
   ENV LOG_LEVEL=INFO

   HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
     CMD python3 -c "import sys; sys.exit(0)"

   CMD ["python3", "app.py"]

.. _app_image_step2:

步骤 2: 构建 Docker 镜像
-------------------------

在应用目录下执行构建命令：

.. code-block:: bash

   docker build -t my-app:1.0.0 .

构建参数说明：

- ``-t my-app:1.0.0`` — 镜像名称和标签，需与 ``app.yaml`` 中的 ``spec.image`` 一致
- ``.`` — 构建上下文为当前目录

验证镜像构建成功：

.. code-block:: bash

   docker images | grep my-app

.. note::

   如果应用需要额外依赖，可在目录中添加 ``requirements.txt`` 并在 Dockerfile 中加入
   ``RUN pip install -r requirements.txt``。如果需要离线或可重复构建，建议先构建 SDK
   wheel，将 ``hailo_ipc_sdk-*.whl`` 复制进镜像，再安装这个本地 wheel。

.. _app_image_step3:

步骤 3: 导出镜像
----------------

将构建好的镜像导出为 tar 文件：

.. code-block:: bash

   docker save my-app:1.0.0 -o my-app.tar

推荐使用 gzip 压缩以减小传输大小：

.. code-block:: bash

   docker save my-app:1.0.0 | gzip > my-app.tar.gz

压缩效果参考：

.. list-table::
   :header-rows: 1
   :widths: 25 30 30

   * - 格式
     - 大小
     - 压缩率
   * - tar
     - ~500MB
     - —
   * - tar.gz
     - ~150MB
     - ~70%
   * - tar.xz
     - ~100MB
     - ~80%

.. _app_image_step4:

步骤 4: Web Console 导入（推荐）
---------------------------------

Web Console 提供了 **6 步应用安装向导**，支持上传镜像文件并逐步配置应用参数。

.. note::

   镜像文件支持格式：``.tar``、``.tar.gz``、``.tgz``，最大 2GB。

打开安装向导
~~~~~~~~~~~~

#. 打开浏览器，访问设备 Web Console：``http://<device-ip>:8080``
#. 导航到 **应用管理** 页面
#. 点击 **导入应用** 卡片，打开安装向导

向导步骤
~~~~~~~~

**第 1 步 — 选择镜像来源**

选择以下任一方式：

- **镜像仓库**：输入 Docker 镜像地址（如 ``docker.io/library/nginx:latest``）
- **上传镜像**：拖拽或选择本地镜像文件（``.tar`` / ``.tar.gz`` / ``.tgz``），上传过程显示进度条

**第 2 步 — 基本信息**

填写应用元数据：

- **应用 ID**：唯一标识符（小写字母、数字、连字符）
- **应用名称**：显示名称
- **版本**：语义化版本号（默认 ``1.0.0``）
- **描述**：应用功能说明

**第 3 步 — 资源配置**

设置容器资源限制和运行选项：

- **CPU 限制**：如 ``50%``
- **内存限制**：从下拉菜单选择（128Mi / 256Mi / 512Mi / 1Gi / 2Gi）
- **共享内存**：启用后可使用零拷贝视频流
- **开机自启**：设备启动时自动运行
- **重启策略**：不重启 / 失败时重启 / 总是重启

**第 4 步 — 权限配置**

配置应用可使用的平台能力：

- **AI 模型**：勾选设备上可用的推理模型，设置最大 QPS
- **视频流**：勾选可访问的视频流（如主码流、子码流）
- **事件权限**：设置可发布和订阅的事件主题（逗号分隔，支持通配符）
- **网络模式**：隔离模式（无网络）或主机模式（共享主机网络）
- **设备控制**：勾选需要的硬件控制权限（补光灯、红外滤光片、云台）

**第 5 步 - 高级配置** （可选）

- **环境变量**：添加键值对，注入到容器环境
- **卷挂载**：配置主机与容器之间的目录映射

**第 6 步 — 确认安装**

检查所有配置信息，确认无误后点击 **安装** 按钮。安装完成后应用将出现在应用列表中。

.. _app_image_step5:

步骤 5: 命令行导入（备选方案）
-------------------------------

如果无法使用 Web Console，可先将镜像通过 SCP 传输到设备，再通过命令行导入。

传输镜像到设备：

.. code-block:: bash

   scp my-app.tar.gz root@<device-ip>:/tmp/

然后 SSH 登录设备使用 aipc-cli：

.. code-block:: bash

   # 安装应用
   aipc-cli app install --manifest /tmp/app.yaml --image /tmp/my-app.tar

   # 启动应用
   aipc-cli app start my_app

   # 查看应用状态
   aipc-cli app list

   # 查看应用日志
   aipc-cli app logs my_app

也可以使用 gRPC 客户端直接调用 app-manager 服务：

.. code-block:: bash

   grpcurl -plaintext \
     -d '{"manifest_path": "/tmp/app.yaml", "image_path": "/tmp/my-app.tar"}' \
     unix:///run/aipc/app-manager.sock \
     appmanager.AppManager/InstallApp

.. _app_yaml_reference:

应用清单参考（app.yaml）
------------------------

以下是 ``app.yaml`` 各字段的详细说明。

元数据（metadata）
~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 10 70

   * - 字段
     - 必填
     - 说明
   * - id
     - 是
     - 应用唯一标识符（小写字母、数字、下划线）
   * - name
     - 是
     - 应用显示名称
   * - version
     - 是
     - 语义化版本号（如 1.0.0）
   * - description
     - 是
     - 应用描述
   * - author
     - 否
     - 作者名称
   * - email
     - 否
     - 联系邮箱

资源限制（spec.resources）
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 15 15 70

   * - 字段
     - 默认值
     - 说明
   * - cpu
     - —
     - CPU 限制，如 ``"50%"`` 或 ``"0.5"``
   * - memory
     - —
     - 内存限制，如 ``"256Mi"`` 或 ``"1Gi"``
   * - shm
     - false
     - 是否启用共享内存（零拷贝视频流需要）

权限配置（spec.permissions）
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**视频流权限（video）**

指定应用可访问的视频流：

- ``cam0_main.raw`` — 原始视频流（通过 SHM 零拷贝）
- ``cam0_sub.raw`` — 子码流原始视频
- ``cam0_main`` — 编码视频流（通过 Unix socket）

**AI 推理权限（inference）**

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - 字段
     - 默认值
     - 说明
   * - models
     - []
     - 可使用的模型列表
   * - max_qps
     - —
     - 最大 QPS 限制
   * - max_concurrent
     - —
     - 最大并发推理数

**事件总线权限（events）**

- ``publish`` — 可发布的事件主题（支持通配符 ``*``）
- ``subscribe`` — 可订阅的事件主题（支持通配符 ``*``）

**设备控制权限（device）**

.. list-table::
   :header-rows: 1
   :widths: 15 15 70

   * - 字段
     - 默认值
     - 说明
   * - light
     - false
     - 补光灯控制
   * - ir_cut
     - false
     - 红外滤光片控制
   * - ptz
     - false
     - 云台控制
   * - lens
     - false
     - 镜头变焦/对焦控制

**网络权限（network）**

- ``mode`` — 网络模式：``"isolated"``（默认）或 ``"host"``
- ``outbound`` — 允许的出站地址（isolated 模式下）

生命周期配置
~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - 字段
     - 默认值
     - 说明
   * - autostart
     - false
     - 系统启动时自动启动
   * - restart_policy
     - "no"
     - 重启策略：always / on-failure / no
   * - restart_max_retries
     - 3
     - 最大重启次数（on-failure 时）

健康检查（healthcheck）
~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 15 15 70

   * - 字段
     - 默认值
     - 说明
   * - enabled
     - false
     - 启用健康检查
   * - interval
     - 30s
     - 检查间隔
   * - timeout
     - 5s
     - 超时时间
   * - retries
     - 3
     - 失败重试次数

.. _app_image_faq:

常见问题
--------

镜像构建失败
~~~~~~~~~~~~

**错误**: ``failed to solve: failed to fetch``

检查网络连接，如需代理：

.. code-block:: bash

   docker build --build-arg HTTP_PROXY=http://proxy:port \
                --build-arg HTTPS_PROXY=http://proxy:port \
                -t my-app:1.0.0 .

镜像文件过大
~~~~~~~~~~~~

使用 gzip 压缩可减少约 70% 的文件大小：

.. code-block:: bash

   docker save my-app:1.0.0 | gzip > my-app.tar.gz

导入失败
~~~~~~~~

**错误**: ``Failed to import image to containerd``

.. code-block:: bash

   # 检查 containerd 状态
   systemctl status containerd

   # 手动导入测试
   ctr -n aipc images import my-app.tar

权限错误
~~~~~~~~

**错误**: ``Permission denied``

.. code-block:: bash

   chmod 644 /tmp/app.yaml /tmp/my-app.tar
