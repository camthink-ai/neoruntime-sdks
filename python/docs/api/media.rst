视频流 API
==========

.. automodule:: hailo_ipc_sdk.media
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

FdMediaClient
-------------

.. autoclass:: hailo_ipc_sdk.FdMediaClient
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

数据类型
--------

Frame
~~~~~

.. autoclass:: hailo_ipc_sdk.Frame
   :members:
   :undoc-members:
   :no-index:

StreamInfo
~~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.StreamInfo
   :members:
   :undoc-members:

PixelFormat
~~~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.PixelFormat
   :members:
   :undoc-members:

使用示例
--------

获取原始视频流
~~~~~~~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import MediaClient
   import cv2

   media = MediaClient()

   # 获取主码流
   for frame in media.subscribe("cam0_main"):
       print(f"帧 {frame.sequence}: {frame.width}x{frame.height}")
       print(f"格式: {frame.format}, 时间戳: {frame.timestamp_ns}")

       # frame.image 是 numpy array (H, W, C) 或 (H*3//2, W) 对于 NV12
       # 可以直接用于 OpenCV 或其他图像处理库
       cv2.imshow("Camera", frame.image)
       if cv2.waitKey(1) & 0xFF == ord('q'):
           break

   cv2.destroyAllWindows()

不跳过帧
~~~~~~~~

.. code-block:: python

   # 获取每一帧（不跳过）
   for frame in media.subscribe("cam0_main", skip_frames=False):
       process_frame(frame.image)

获取单帧
~~~~~~~~

.. code-block:: python

   # 获取单帧
   frame = media.get_frame("cam0_main", timeout_ms=1000)

   if frame:
       print(f"帧: {frame.width}x{frame.height}")
       print(f"格式: {frame.format}")

获取流信息
~~~~~~~~~~

.. code-block:: python

   # 获取流配置信息
   info = media.get_stream_info("cam0_main")

   if info:
       print(f"分辨率: {info.width}x{info.height}")
       print(f"帧率: {info.fps}")
       print(f"格式: {info.format}")
       print(f"缓冲数量: {info.buffer_count}")

列出可用流
~~~~~~~~~~~

.. code-block:: python

   # 列出所有可用的流
   streams = media.list_streams()
   for stream_id in streams:
       print(f"流: {stream_id}")

帧处理回调
~~~~~~~~~~

.. code-block:: python

   def handle_frame(frame):
       print(f"收到帧: {frame.sequence}")

   # 使用回调处理帧
   thread = media.on_frame("cam0_main", handle_frame)

   # 保持运行
   import time
   while True:
       time.sleep(1)

图像处理
~~~~~~~~

.. code-block:: python

   import cv2
   import numpy as np

   media = MediaClient()

   for frame in media.subscribe("cam0_main"):
       # 转换为 RGB
       rgb = frame.to_rgb()

       # 灰度图
       gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

       # 边缘检测
       edges = cv2.Canny(gray, 100, 200)

       # 显示结果
       cv2.imshow("Original", rgb)
       cv2.imshow("Edges", edges)

       if cv2.waitKey(1) & 0xFF == ord('q'):
           break

保存图像
~~~~~~~~

.. code-block:: python

   media = MediaClient()

   for frame in media.subscribe("cam0_main"):
       # 保存为图片
       frame.save("frame.jpg")
       break

多流处理
~~~~~~~~

.. code-block:: python

   import threading

   def process_main_stream():
       media = MediaClient()
       for frame in media.subscribe("cam0_main"):
           # 处理主码流（高分辨率）
           process_high_res(frame.image)

   def process_sub_stream():
       media = MediaClient()
       for frame in media.subscribe("cam0_sub"):
           # 处理子码流（低分辨率）
           process_low_res(frame.image)

   # 并行处理多个流
   t1 = threading.Thread(target=process_main_stream)
   t2 = threading.Thread(target=process_sub_stream)

   t1.start()
   t2.start()

   t1.join()
   t2.join()

帧率控制
~~~~~~~~

.. code-block:: python

   import time

   media = MediaClient()
   target_fps = 10
   frame_interval = 1.0 / target_fps

   last_time = time.time()

   for frame in media.subscribe("cam0_main"):
       current_time = time.time()
       elapsed = current_time - last_time

       if elapsed >= frame_interval:
           # 处理帧
           process_frame(frame.image)
           last_time = current_time

保存视频
~~~~~~~~

.. code-block:: python

   import cv2

   media = MediaClient()
   info = media.get_stream_info("cam0_main")

   # 创建视频写入器
   fourcc = cv2.VideoWriter_fourcc(*'mp4v')
   out = cv2.VideoWriter(
       'output.mp4',
       fourcc,
       info.fps,
       (info.width, info.height)
   )

   frame_count = 0
   max_frames = 300  # 录制 10 秒 (30fps)

   for frame in media.subscribe("cam0_main"):
       rgb = frame.to_rgb()
       bgr = rgb[:, :, ::-1]  # RGB to BGR
       out.write(bgr)
       frame_count += 1

       if frame_count >= max_frames:
           break

   out.release()
   print(f"已保存 {frame_count} 帧到 output.mp4")

上下文管理器
~~~~~~~~~~~~

.. code-block:: python

   # 使用上下文管理器自动管理资源
   with MediaClient() as media:
       for frame in media.subscribe("cam0_main"):
           process_frame(frame.image)

零拷贝访问
~~~~~~~~~~

.. code-block:: python

   # SDK 使用共享内存 (SHM) 实现零拷贝
   # frame.image 直接映射到 SHM，无需额外拷贝

   media = MediaClient()

   for frame in media.subscribe("cam0_main"):
       # frame.image 是 numpy array，直接引用 SHM
       # 可以高效地传递给 AI 推理或其他处理模块
       result = inference_engine.process(frame.image)

错误处理
~~~~~~~~

.. code-block:: python

   media = MediaClient()

   try:
       for frame in media.subscribe("invalid_stream"):
           process_frame(frame.image)
   except Exception as e:
       print(f"流访问失败: {e}")
   except KeyboardInterrupt:
       print("用户中断")
   finally:
       media.close()
