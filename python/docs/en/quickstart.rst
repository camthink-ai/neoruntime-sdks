Quick Start
===========

This guide will help you get started with the AIPC Platform Python SDK.

Basic Concepts
--------------

AIPC Platform provides the following core services:

- **AI Runtime**: AI inference service with model registration and inference
- **Event Bus**: Event bus with publish/subscribe pattern
- **Device Control**: Device control service for hardware management
- **Camera Daemon**: Camera service providing video streams

All services communicate via gRPC over Unix Domain Sockets.

First Application
-----------------

Create a simple person detection application:

.. code-block:: python

   from hailo_ipc_sdk import InferenceClient, EventClient
   import time

   def main():
       # Initialize clients
       inf = InferenceClient()
       events = EventClient()

       print("Starting person detection...")

       # Subscribe to video stream inference results
       for frame_seq, result in inf.subscribe(
           stream="cam0_main",
           model="person_v1",
           fps=10
       ):
           # Count detected persons
           person_count = len([
               obj for obj in result.objects
               if obj.label == "person"
           ])

           if person_count > 0:
               print(f"Frame {frame_seq}: detected {person_count} person(s)")

               # Publish alert event
               events.publish("app/alert", {
                   "type": "person_detected",
                   "count": person_count,
                   "timestamp": time.time()
               })

   if __name__ == "__main__":
       main()

Configuring Environment Variables
---------------------------------

The SDK uses environment variables to configure connection parameters:

.. code-block:: bash

   export APP_ID=my_app
   export AI_RUNTIME_ENDPOINT=unix:///run/aipc/ai-runtime.sock
   export EVENT_BUS_ENDPOINT=unix:///run/aipc/event-bus.sock
   export DEVICE_CONTROL_ENDPOINT=unix:///run/aipc/device-control.sock
   export DEBUG=0
   export LOG_LEVEL=INFO

Or configure in code:

.. code-block:: python

   from hailo_ipc_sdk import Config

   config = Config(
       app_id="my_app",
       ai_runtime_endpoint="unix:///run/aipc/ai-runtime.sock",
       debug=True
   )

Core Feature Examples
---------------------

AI Inference
~~~~~~~~~~~~

Single-shot Inference
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from hailo_ipc_sdk import InferenceClient
   import numpy as np

   inf = InferenceClient()

   # Prepare image data
   image = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)

   # Execute inference
   result = inf.infer(image, model_id="person_v1")

   # Process results
   for obj in result.objects:
       print(f"{obj.label}: {obj.score:.2f} at ({obj.bbox.x}, {obj.bbox.y})")

Streaming Inference
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Subscribe to video stream inference results
   for frame_seq, result in inf.subscribe(
       stream="cam0_main",
       model="person_v1",
       fps=15
   ):
       print(f"Frame {frame_seq}: {len(result.objects)} object(s)")

Model Management
^^^^^^^^^^^^^^^^

.. code-block:: python

   # List available models
   models = inf.list_models()
   for model in models:
       print(f"{model.id}: {model.name} v{model.version}")

   # Get model info
   model_info = inf.get_model_info("person_v1")
   print(f"Input size: {model_info.input_width}x{model_info.input_height}")

Event Bus
~~~~~~~~~

Publish Events
^^^^^^^^^^^^^^

.. code-block:: python

   from hailo_ipc_sdk import EventClient

   events = EventClient()

   # Publish simple event
   events.publish("app/status", {"status": "running"})

   # Publish complex event
   events.publish("app/detection", {
       "objects": [
           {"label": "person", "score": 0.95},
           {"label": "car", "score": 0.88}
       ],
       "timestamp": 1234567890
   })

Subscribe to Events
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Subscribe to a single topic
   for event in events.subscribe("system/temperature"):
       print(f"Temperature: {event.payload['value']}°C")

   # Subscribe with wildcard topics
   for event in events.subscribe("model/*/detections"):
       print(f"Model {event.topic.split('/')[1]} detection results")

   # Use callback function
   def on_alert(event):
       print(f"Alert: {event.payload}")

   events.on_event("app/alert", on_alert)

Device Control
~~~~~~~~~~~~~~

Light Control
^^^^^^^^^^^^^

.. code-block:: python

   from hailo_ipc_sdk import DeviceClient, IrCutMode

   dev = DeviceClient()

   # White light
   dev.set_white_light(80)  # 80% brightness

   # IR LED
   dev.set_ir_led(True)

   # IR cut filter
   dev.set_ircut(IrCutMode.NIGHT)  # Night vision mode

PTZ Control
^^^^^^^^^^^

.. code-block:: python

   # Absolute position
   dev.ptz_goto(pan=45.0, tilt=30.0, zoom=2.0)

   # Relative movement
   dev.ptz_move(pan_speed=10, tilt_speed=5)

   # Stop movement
   dev.ptz_stop()

GPIO Control
^^^^^^^^^^^^

.. code-block:: python

   # Read GPIO
   value = dev.gpio_read(12)
   print(f"GPIO 12: {value}")

   # Write GPIO
   dev.gpio_write(21, True)

Video Stream Access
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import MediaClient, PixelFormat

   media = MediaClient()

   # Get raw video stream
   for frame in media.get_raw_stream("cam0_main"):
       print(f"Frame {frame.sequence}: {frame.width}x{frame.height}")
       # frame.data is a numpy array
       process_frame(frame.data)

   # Get encoded video stream
   for packet in media.get_encoded_stream("cam0_main"):
       print(f"H.264 packet: {len(packet.data)} bytes")

Error Handling
--------------

The SDK uses standard Python exceptions:

.. code-block:: python

   from hailo_ipc_sdk import InferenceClient
   from grpc import RpcError

   inf = InferenceClient()

   try:
       result = inf.infer(image, model_id="invalid_model")
   except RpcError as e:
       print(f"gRPC error: {e.code()} - {e.details()}")
   except ValueError as e:
       print(f"Parameter error: {e}")
   except Exception as e:
       print(f"Unknown error: {e}")

Logging
-------

The SDK uses the Python standard logging module:

.. code-block:: python

   import logging

   # Set log level
   logging.basicConfig(level=logging.DEBUG)

   # Or set SDK logging only
   logger = logging.getLogger('hailo_ipc_sdk')
   logger.setLevel(logging.DEBUG)

Next Steps
----------

- Check :doc:`examples` for more examples
- Read :doc:`api/inference` for the complete API
- See :doc:`api/events` to learn the event system
