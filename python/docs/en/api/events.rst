Event Bus API
=============

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

Data Types
----------

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

Usage Examples
--------------

Publishing Events
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import EventClient

   events = EventClient()

   # Publish simple event
   events.publish("app/status", {"status": "running"})

   # Publish event with metadata
   events.publish("app/detection", {
       "timestamp": 1234567890,
       "objects": [
           {"label": "person", "score": 0.95, "bbox": [100, 200, 50, 100]},
           {"label": "car", "score": 0.88, "bbox": [300, 400, 80, 120]}
       ]
   }, metadata={"camera": "cam0", "model": "person_vehicle_v1"})

   # Publish persistent event
   events.publish("app/alert", {"type": "person_detected"}, persistent=True)

   # Batch publish
   events.publish_batch([
       {"topic": "app/event1", "payload": {"data": "value1"}},
       {"topic": "app/event2", "payload": {"data": "value2"}}
   ])

Subscribing to Events
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Subscribe to a single topic
   for event in events.subscribe("system/temperature"):
       temp = event.payload.get("value")
       print(f"Current temperature: {temp}°C")

   # Subscribe to multiple topics (wildcards)
   for event in events.subscribe("model/*/detections"):
       model_name = event.topic.split('/')[1]
       count = len(event.payload.get("objects", []))
       print(f"Model {model_name} detected {count} object(s)")

   # Subscribe with filters
   for event in events.subscribe("app/alerts", filters={"severity": "high"}):
       print(f"High severity alert: {event.payload}")

Using Callback Functions
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def on_alert(event):
       alert_type = event.payload.get("type")
       print(f"Alert received: {alert_type}")

   def on_detection(event):
       objects = event.payload.get("objects", [])
       print(f"Detected {len(objects)} object(s)")

   # Register callbacks
   events.on_event("app/alert", on_alert)
   events.on_event("model/*/detections", on_detection)

   # Keep running
   import time
   while True:
       time.sleep(1)

Topic Wildcards
~~~~~~~~~~~~~~~

The event bus supports wildcards:

.. code-block:: python

   # Matches model/person_v1/detections, model/car_v1/detections
   events.subscribe("model/*/detections")

   # Matches app/my_app/alert, app/my_app/status/running
   events.subscribe("app/my_app/**")

Listing Topics
~~~~~~~~~~~~~~

.. code-block:: python

   # List all active topics
   topics = events.list_topics()
   for topic in topics:
       print(f"{topic.topic}: {topic.subscriber_count} subscribers, {topic.total_messages} messages")

   # Get specific topic info
   info = events.get_topic_info("app/alerts")
   if info:
       print(f"Subscribers: {info.subscriber_count}")

Getting Statistics
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get global statistics
   stats = events.get_stats()
   print(f"Total subscribers: {stats['total_subscribers']}")
   print(f"Total topics: {stats['total_topics']}")
   print(f"Uptime: {stats['uptime_ms']}ms")

   # Get specific topic statistics
   topic_stats = events.get_topic_stats("app/alerts")
   print(f"Published: {topic_stats['published_count']}")
   print(f"Delivered: {topic_stats['delivered_count']}")
   print(f"Dropped: {topic_stats['dropped_count']}")
   print(f"Average latency: {topic_stats['avg_latency_us']}us")

Unsubscribing
~~~~~~~~~~~~~

.. code-block:: python

   # Unsubscribe
   events.unsubscribe("app/alert")

Event Filtering
~~~~~~~~~~~~~~~

.. code-block:: python

   # Subscribe and filter
   for event in events.subscribe("model/*/detections"):
       # Only process high-confidence detections
       objects = event.payload.get("objects", [])
       high_conf = [obj for obj in objects if obj.get("score", 0) > 0.9]

       if high_conf:
           print(f"High confidence detections: {len(high_conf)} object(s)")

Context Manager
~~~~~~~~~~~~~~~

.. code-block:: python

   # Use context manager for automatic connection management
   with EventClient() as events:
       events.publish("app/status", {"status": "running"})
       for event in events.subscribe("app/*"):
           print(f"Received: {event.topic}")

Error Handling
~~~~~~~~~~~~~~

.. code-block:: python

   from grpc import RpcError

   try:
       events.publish("app/status", {"status": "running"})
   except RpcError as e:
       print(f"Publish failed: {e.details()}")

   try:
       for event in events.subscribe("invalid/topic"):
           process_event(event)
   except RpcError as e:
       print(f"Subscription failed: {e.details()}")
