AI 推理 API
===========

.. automodule:: hailo_ipc_sdk.inference
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

InferenceClient
---------------

.. autoclass:: hailo_ipc_sdk.InferenceClient
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

数据类型
--------

InferenceResult
~~~~~~~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.InferenceResult
   :members:
   :undoc-members:
   :no-index:

DetectedObject
~~~~~~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.DetectedObject
   :members:
   :undoc-members:

BoundingBox
~~~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.BoundingBox
   :members:
   :undoc-members:
   :no-index:

LandmarkPoint
~~~~~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.LandmarkPoint
   :members:
   :undoc-members:

LandmarkSet
~~~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.LandmarkSet
   :members:
   :undoc-members:

Classification
~~~~~~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.Classification
   :members:
   :undoc-members:

ModelInfo
~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.ModelInfo
   :members:
   :undoc-members:

使用示例
--------

单次推理
~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import InferenceClient
   import numpy as np

   inf = InferenceClient()

   # 准备图像 (numpy array)
   image = np.zeros((1080, 1920, 3), dtype=np.uint8)

   # 执行推理
   result = inf.infer(image, model_id="person_v1")

   # 处理结果
   for obj in result.objects:
       print(f"{obj.label}: {obj.score:.2f}")
       print(f"  位置: ({obj.bbox.x}, {obj.bbox.y})")
       print(f"  大小: {obj.bbox.width}x{obj.bbox.height}")

   # 便捷方法
   if result.has_person():
       print("检测到人员")

   person_count = result.count_by_label("person")
   print(f"人员数量: {person_count}")

   persons = result.get_objects_by_label("person")

流式推理
~~~~~~~~

.. code-block:: python

   # 订阅视频流推理结果
   for frame_seq, result in inf.subscribe(
       stream="cam0_main",
       model="person_v1",
       fps=15
   ):
       print(f"帧 {frame_seq}: 检测到 {len(result.objects)} 个对象")

       for obj in result.objects:
           if obj.score > 0.8:
               print(f"  高置信度: {obj.label} ({obj.score:.2f})")

张量推理
~~~~~~~~

.. code-block:: python

   import numpy as np

   inf = InferenceClient()

   # 准备输入张量
   input1 = np.random.randn(1, 3, 224, 224).astype(np.float32)
   input2 = np.random.randn(1, 3, 112, 112).astype(np.float32)

   # 执行推理
   outputs = inf.infer_with_tensors(
       model_id="custom_model",
       inputs=[input1, input2],
       input_names=["input_main", "input_sub"]
   )

   # 处理输出张量
   for i, output in enumerate(outputs):
       print(f"输出 {i}: shape={output.shape}")

模型管理
~~~~~~~~

.. code-block:: python

   # 列出所有模型
   models = inf.list_models()
   for model in models:
       print(f"模型ID: {model.model_id}")
       print(f"路径: {model.model_path}")
       print(f"版本: {model.version}")
       print(f"输入: {model.inputs}")
       print(f"输出: {model.outputs}")
       print(f"估算 TOPS: {model.estimated_tops}")
       print(f"估算内存: {model.estimated_memory} bytes")

   # 获取模型详情
   info = inf.get_model_info("person_v1")
   if info:
       print(f"模型ID: {info.model_id}")
       print(f"路径: {info.model_path}")
       print(f"版本: {info.version}")

   # 注册新模型
   model_id = inf.register_model(
       model_path="/opt/models/custom.hef",
       model_id="custom_v1"
   )
   print(f"注册模型 ID: {model_id}")

   # 注销模型
   inf.unregister_model("custom_v1")

获取统计信息
~~~~~~~~~~~~

.. code-block:: python

   stats = inf.get_stats()

   print(f"设备利用率: {stats['device_utilization']}%")
   print(f"设备温度: {stats['device_temperature']}°C")
   print(f"总内存: {stats['total_memory_bytes']} bytes")
   print(f"已用内存: {stats['used_memory_bytes']} bytes")

   for model_stat in stats['model_stats']:
       print(f"模型: {model_stat['model_id']}")
       print(f"  总推理次数: {model_stat['total_inferences']}")
       print(f"  总错误数: {model_stat['total_errors']}")
       print(f"  平均延迟: {model_stat['avg_latency_us']}us")
       print(f"  当前 QPS: {model_stat['current_qps']}")
       print(f"  队列深度: {model_stat['queue_depth']}")

会话管理
~~~~~~~~

.. code-block:: python

   # 创建会话
   session_id = inf.create_session(
       session_id="my_session",
       app_id="my_app",
       allowed_models=["person_v1", "car_v1"],
       max_qps=10,
       max_concurrent=2,
       priority=4
   )
   print(f"会话ID: {session_id}")

   # 使用会话进行推理
   result = inf.infer(image, model_id="person_v1", session_id=session_id)

   # 销毁会话
   inf.destroy_session(session_id)

处理不同类型的结果
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   result = inf.infer(image, model_id="face_detection")

   # 检测结果
   for obj in result.objects:
       # 边界框
       x1, y1, x2, y2 = obj.bbox.to_xyxy()
       print(f"边界框: ({x1}, {y1}) - ({x2}, {y2})")

   # 分类结果
   for cls in result.classifications:
       print(f"分类: {cls.type} - {cls.label}: {cls.confidence:.2f}")

   # 关键点
   for lm_set in result.landmarks:
       print(f"关键点集类型: {lm_set.type}")
       for point in lm_set.points:
           print(f"  点: ({point.x}, {point.y}), 置信度: {point.confidence}")

   # 原始输出
   if result.raw_outputs:
       print(f"原始输出数量: {len(result.raw_outputs)}")

   # 性能信息
   print(f"推理时间: {result.infer_time_us}us")
   print(f"排队时间: {result.queue_time_us}us")

上下文管理器
~~~~~~~~~~~~

.. code-block:: python

   # 使用上下文管理器自动管理连接
   with InferenceClient() as inf:
       result = inf.infer(image, model_id="person_v1")
       print(f"检测到 {len(result.objects)} 个对象")

错误处理
~~~~~~~~

.. code-block:: python

   from grpc import RpcError

   try:
       result = inf.infer(image, model_id="nonexistent_model")
   except RpcError as e:
       print(f"推理失败: {e.details()}")
   except RuntimeError as e:
       print(f"运行时错误: {e}")