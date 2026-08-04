AIPC Platform Python SDK Documentation
=======================================

Welcome to the AIPC Platform Python SDK! This is a Python development toolkit for the AIPC Edge AI Computing Platform.

.. only:: html

   .. image:: https://img.shields.io/badge/version-0.3.0-blue.svg
      :target: https://github.com/camthink-ai/ne503-aipc-sdks
      :alt: Version

   .. image:: https://img.shields.io/badge/python-3.8+-blue.svg
      :target: https://www.python.org/downloads/
      :alt: Python Version

Overview
--------

The AIPC Platform Python SDK provides clean APIs to access platform capabilities:

- **Video Stream Access**: Raw and encoded video streams (zero-copy SHM)
- **AI Inference Service**: Model registration, single-shot and streaming inference
- **Event Bus**: Publish/subscribe pattern with wildcard topic support
- **Device Control**: Light, PTZ, lens, and GPIO control
- **Plugin System**: Plugin discovery and gRPC server hosting

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   git clone https://github.com/camthink-ai/ne503-aipc-sdks.git
   cd ne503-aipc-sdks
   python -m pip install -e ./python

Basic Usage
~~~~~~~~~~~

AI Inference
^^^^^^^^^^^^

.. code-block:: python

   from hailo_ipc_sdk import InferenceClient
   import numpy as np

   # Create inference client
   inf = InferenceClient()

   # Single-shot inference
   image = np.zeros((1080, 1920, 3), dtype=np.uint8)
   result = inf.infer(image, model_id="person_v1")

   print(f"Detected {len(result.objects)} objects")
   for obj in result.objects:
       print(f"  - {obj.label}: {obj.score:.2f}")

Event Bus
^^^^^^^^^

.. code-block:: python

   from hailo_ipc_sdk import EventClient

   events = EventClient()

   # Publish event
   events.publish("app/alert", {"type": "person_detected"})

   # Subscribe to events (supports wildcards)
   for event in events.subscribe("model/*/detections"):
       print(f"Received event: {event.topic}")

Device Control
^^^^^^^^^^^^^^

.. code-block:: python

   from hailo_ipc_sdk import DeviceClient, IrCutMode

   dev = DeviceClient()

   # Light control
   dev.set_white_light(80)
   dev.set_ir_led(True)
   dev.set_ircut(IrCutMode.NIGHT)

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   quickstart
   app_image_guide
   examples

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/inference
   api/media
   api/events
   api/device
   api/app
   api/plugin
   api/config

.. toctree::
   :maxdepth: 1
   :caption: Other

   changelog
   contributing
   license

Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
