事件总线 API
============

.. automodule:: hailo_ipc_sdk.events
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

EventClient
-----------

.. autoclass:: hailo_ipc_sdk.EventClient
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

数据类型
--------

Event
~~~~~

.. autoclass:: hailo_ipc_sdk.Event
   :members:
   :undoc-members:

TopicInfo
~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.TopicInfo
   :members:
   :undoc-members:

使用示例
--------

发布事件
~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import EventClient

   events = EventClient()

   # 发布简单事件
   events.publish("app/status", {"status": "running"})

   # 发布带元数据的事件
   events.publish("app/detection", {
       "timestamp": 1234567890,
       "objects": [
           {"label": "person", "score": 0.95, "bbox": [100, 200, 50, 100]},
           {"label": "car", "score": 0.88, "bbox": [300, 400, 80, 120]}
       ]
   }, metadata={"camera": "cam0", "model": "person_vehicle_v1"})

   # 发布持久化事件
   events.publish("app/alert", {"type": "person_detected"}, persistent=True)

   # 批量发布
   events.publish_batch([
       {"topic": "app/event1", "payload": {"data": "value1"}},
       {"topic": "app/event2", "payload": {"data": "value2"}}
   ])

订阅事件
~~~~~~~~

.. code-block:: python

   # 订阅单个主题
   for event in events.subscribe("system/temperature"):
       temp = event.payload.get("value")
       print(f"当前温度: {temp}°C")

   # 订阅多个主题（通配符）
   for event in events.subscribe("model/*/detections"):
       model_name = event.topic.split('/')[1]
       count = len(event.payload.get("objects", []))
       print(f"模型 {model_name} 检测到 {count} 个对象")

   # 带过滤订阅
   for event in events.subscribe("app/alerts", filters={"severity": "high"}):
       print(f"高严重性告警: {event.payload}")

使用回调函数
~~~~~~~~~~~~

.. code-block:: python

   def on_alert(event):
       alert_type = event.payload.get("type")
       print(f"收到告警: {alert_type}")

   def on_detection(event):
       objects = event.payload.get("objects", [])
       print(f"检测到 {len(objects)} 个对象")

   # 注册回调
   events.on_event("app/alert", on_alert)
   events.on_event("model/*/detections", on_detection)

   # 保持运行
   import time
   while True:
       time.sleep(1)

主题通配符
~~~~~~~~~~

事件总线支持通配符：

.. code-block:: python

   # 匹配 model/person_v1/detections, model/car_v1/detections
   events.subscribe("model/*/detections")

   # 匹配 app/my_app/alert, app/my_app/status/running
   events.subscribe("app/my_app/**")

列出主题
~~~~~~~~

.. code-block:: python

   # 列出所有活跃主题
   topics = events.list_topics()
   for topic in topics:
       print(f"{topic.topic}: {topic.subscriber_count} 订阅者, {topic.total_messages} 条消息")

   # 获取特定主题信息
   info = events.get_topic_info("app/alerts")
   if info:
       print(f"订阅者: {info.subscriber_count}")

获取统计信息
~~~~~~~~~~~~

.. code-block:: python

   # 获取全局统计
   stats = events.get_stats()
   print(f"总订阅者数: {stats['total_subscribers']}")
   print(f"总主题数: {stats['total_topics']}")
   print(f"运行时间: {stats['uptime_ms']}ms")

   # 获取特定主题统计
   topic_stats = events.get_topic_stats("app/alerts")
   print(f"发布数: {topic_stats['published_count']}")
   print(f"投递数: {topic_stats['delivered_count']}")
   print(f"丢弃数: {topic_stats['dropped_count']}")
   print(f"平均延迟: {topic_stats['avg_latency_us']}us")

取消订阅
~~~~~~~~

.. code-block:: python

   # 取消订阅
   events.unsubscribe("app/alert")

事件过滤
~~~~~~~~

.. code-block:: python

   # 订阅并过滤
   for event in events.subscribe("model/*/detections"):
       # 只处理高置信度检测
       objects = event.payload.get("objects", [])
       high_conf = [obj for obj in objects if obj.get("score", 0) > 0.9]

       if high_conf:
           print(f"高置信度检测: {len(high_conf)} 个对象")

上下文管理器
~~~~~~~~~~~~

.. code-block:: python

   # 使用上下文管理器自动管理连接
   with EventClient() as events:
       events.publish("app/status", {"status": "running"})
       for event in events.subscribe("app/*"):
           print(f"收到: {event.topic}")

错误处理
~~~~~~~~

.. code-block:: python

   from grpc import RpcError

   try:
       events.publish("app/status", {"status": "running"})
   except RpcError as e:
       print(f"发布失败: {e.details()}")

   try:
       for event in events.subscribe("invalid/topic"):
           process_event(event)
   except RpcError as e:
       print(f"订阅失败: {e.details()}")