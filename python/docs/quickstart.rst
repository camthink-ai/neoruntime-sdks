快速开始
========

本指南将帮助你快速上手 AIPC Platform Python SDK。

基本概念
--------

AIPC Platform 提供以下核心服务：

- **AI Runtime**: AI 推理服务，支持模型注册和推理
- **Event Bus**: 事件总线，支持发布/订阅模式
- **Device Control**: 设备控制服务，管理硬件设备
- **Camera Daemon**: 摄像头服务，提供视频流

所有服务通过 gRPC over Unix Domain Socket 通信。

第一个应用
----------

创建一个简单的人员检测应用：

.. code-block:: python

   from hailo_ipc_sdk import InferenceClient, EventClient
   import time

   def main():
       # 初始化客户端
       inf = InferenceClient()
       events = EventClient()

       print("开始人员检测...")

       # 订阅视频流推理结果
       for frame_seq, result in inf.subscribe(
           stream="cam0_main",
           model="person_v1",
           fps=10
       ):
           # 统计检测到的人数
           person_count = len([
               obj for obj in result.objects
               if obj.label == "person"
           ])

           if person_count > 0:
               print(f"帧 {frame_seq}: 检测到 {person_count} 个人")

               # 发布告警事件
               events.publish("app/alert", {
                   "type": "person_detected",
                   "count": person_count,
                   "timestamp": time.time()
               })

   if __name__ == "__main__":
       main()

配置环境变量
------------

SDK 通过环境变量配置连接参数：

.. code-block:: bash

   export APP_ID=my_app
   export AI_RUNTIME_ENDPOINT=unix:///run/aipc/ai-runtime.sock
   export EVENT_BUS_ENDPOINT=unix:///run/aipc/event-bus.sock
   export DEVICE_CONTROL_ENDPOINT=unix:///run/aipc/device-control.sock
   export DEBUG=0
   export LOG_LEVEL=INFO

或者在代码中配置：

.. code-block:: python

   from hailo_ipc_sdk import Config

   config = Config(
       app_id="my_app",
       ai_runtime_endpoint="unix:///run/aipc/ai-runtime.sock",
       debug=True
   )

核心功能示例
------------

AI 推理
~~~~~~~

单次推理
^^^^^^^^

.. code-block:: python

   from hailo_ipc_sdk import InferenceClient
   import numpy as np

   inf = InferenceClient()

   # 准备图像数据
   image = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)

   # 执行推理
   result = inf.infer(image, model_id="person_v1")

   # 处理结果
   for obj in result.objects:
       print(f"{obj.label}: {obj.score:.2f} at ({obj.bbox.x}, {obj.bbox.y})")

流式推理
^^^^^^^^

.. code-block:: python

   # 订阅视频流推理结果
   for frame_seq, result in inf.subscribe(
       stream="cam0_main",
       model="person_v1",
       fps=15
   ):
       print(f"帧 {frame_seq}: {len(result.objects)} 个对象")

模型管理
^^^^^^^^

.. code-block:: python

   # 列出可用模型
   models = inf.list_models()
   for model in models:
       print(f"{model.id}: {model.name} v{model.version}")

   # 获取模型信息
   model_info = inf.get_model_info("person_v1")
   print(f"输入尺寸: {model_info.input_width}x{model_info.input_height}")

事件总线
~~~~~~~~

发布事件
^^^^^^^^

.. code-block:: python

   from hailo_ipc_sdk import EventClient

   events = EventClient()

   # 发布简单事件
   events.publish("app/status", {"status": "running"})

   # 发布复杂事件
   events.publish("app/detection", {
       "objects": [
           {"label": "person", "score": 0.95},
           {"label": "car", "score": 0.88}
       ],
       "timestamp": 1234567890
   })

订阅事件
^^^^^^^^

.. code-block:: python

   # 订阅单个主题
   for event in events.subscribe("system/temperature"):
       print(f"温度: {event.payload['value']}°C")

   # 订阅通配符主题
   for event in events.subscribe("model/*/detections"):
       print(f"模型 {event.topic.split('/')[1]} 检测结果")

   # 使用回调函数
   def on_alert(event):
       print(f"告警: {event.payload}")

   events.on_event("app/alert", on_alert)

设备控制
~~~~~~~~

灯光控制
^^^^^^^^

.. code-block:: python

   from hailo_ipc_sdk import DeviceClient, IrCutMode

   dev = DeviceClient()

   # 白光灯
   dev.set_white_light(80)  # 80% 亮度

   # 红外灯
   dev.set_ir_led(True)

   # 红外滤光片
   dev.set_ircut(IrCutMode.NIGHT)  # 夜视模式

云台控制
^^^^^^^^

.. code-block:: python

   # 绝对位置
   dev.ptz_goto(pan=45.0, tilt=30.0, zoom=2.0)

   # 相对移动
   dev.ptz_move(pan_speed=10, tilt_speed=5)

   # 停止移动
   dev.ptz_stop()

GPIO 控制
^^^^^^^^^

.. code-block:: python

   # 读取 GPIO
   value = dev.gpio_read(12)
   print(f"GPIO 12: {value}")

   # 写入 GPIO
   dev.gpio_write(21, True)

视频流访问
~~~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import MediaClient, PixelFormat

   media = MediaClient()

   # 获取原始视频流
   for frame in media.get_raw_stream("cam0_main"):
       print(f"帧 {frame.sequence}: {frame.width}x{frame.height}")
       # frame.data 是 numpy array
       process_frame(frame.data)

   # 获取编码视频流
   for packet in media.get_encoded_stream("cam0_main"):
       print(f"H.264 包: {len(packet.data)} 字节")

错误处理
--------

SDK 使用标准的 Python 异常：

.. code-block:: python

   from hailo_ipc_sdk import InferenceClient
   from grpc import RpcError

   inf = InferenceClient()

   try:
       result = inf.infer(image, model_id="invalid_model")
   except RpcError as e:
       print(f"gRPC 错误: {e.code()} - {e.details()}")
   except ValueError as e:
       print(f"参数错误: {e}")
   except Exception as e:
       print(f"未知错误: {e}")

日志记录
--------

SDK 使用 Python 标准 logging 模块：

.. code-block:: python

   import logging

   # 设置日志级别
   logging.basicConfig(level=logging.DEBUG)

   # 或者只设置 SDK 日志
   logger = logging.getLogger('hailo_ipc_sdk')
   logger.setLevel(logging.DEBUG)

下一步
------

- 查看 :doc:`examples` 了解更多示例
- 阅读 :doc:`api/inference` 了解完整 API
- 参考 :doc:`api/events` 学习事件系统
