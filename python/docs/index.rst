AIPC Platform Python SDK 文档
================================

欢迎使用 AIPC Platform Python SDK！这是一个用于 AIPC 边缘 AI 计算平台的 Python 开发工具包。

.. only:: html

   .. image:: https://img.shields.io/badge/version-0.3.0-blue.svg
      :target: https://github.com/camthink-ai/ne503-aipc-sdks
      :alt: Version

   .. image:: https://img.shields.io/badge/python-3.8+-blue.svg
      :target: https://www.python.org/downloads/
      :alt: Python Version

概述
----

AIPC Platform Python SDK 提供了简洁的 API 来访问平台能力：

- **视频流访问**: 原始视频流和编码视频流（零拷贝 SHM）
- **AI 推理服务**: 模型注册、单次推理、流式推理
- **事件总线**: 发布/订阅模式，支持通配符主题
- **设备控制**: 灯光、云台、镜头、GPIO 控制
- **插件系统**: 插件发现和 gRPC 服务端

快速开始
--------

安装
~~~~

.. code-block:: bash

   git clone https://github.com/camthink-ai/ne503-aipc-sdks.git
   cd ne503-aipc-sdks
   python -m pip install -e ./python

基本使用
~~~~~~~~

AI 推理
^^^^^^^

.. code-block:: python

   from hailo_ipc_sdk import InferenceClient
   import numpy as np

   # 创建推理客户端
   inf = InferenceClient()

   # 单次推理
   image = np.zeros((1080, 1920, 3), dtype=np.uint8)
   result = inf.infer(image, model_id="person_v1")

   print(f"检测到 {len(result.objects)} 个对象")
   for obj in result.objects:
       print(f"  - {obj.label}: {obj.score:.2f}")

事件总线
^^^^^^^^

.. code-block:: python

   from hailo_ipc_sdk import EventClient

   events = EventClient()

   # 发布事件
   events.publish("app/alert", {"type": "person_detected"})

   # 订阅事件（支持通配符）
   for event in events.subscribe("model/*/detections"):
       print(f"收到事件: {event.topic}")

设备控制
^^^^^^^^

.. code-block:: python

   from hailo_ipc_sdk import DeviceClient, IrCutMode

   dev = DeviceClient()

   # 灯光控制
   dev.set_white_light(80)
   dev.set_ir_led(True)
   dev.set_ircut(IrCutMode.NIGHT)

目录
----

.. toctree::
   :maxdepth: 2
   :caption: 用户指南

   installation
   quickstart
   app_image_guide
   examples

.. toctree::
   :maxdepth: 2
   :caption: API 参考

   api/inference
   api/media
   api/events
   api/device
   api/app
   api/plugin
   api/config

.. toctree::
   :maxdepth: 1
   :caption: 其他

   changelog
   contributing
   license

索引和表格
----------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
