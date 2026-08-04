Configuration API
=================

.. automodule:: hailo_ipc_sdk.config
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Config
------

.. autoclass:: hailo_ipc_sdk.Config
   :members:
   :undoc-members:
   :show-inheritance:

Usage Examples
--------------

Static Methods
~~~~~~~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import Config

   # Get application ID
   app_id = Config.get_app_id()

   # Get service endpoints
   ai_runtime_endpoint = Config.get_inference_endpoint()
   event_bus_endpoint = Config.get_event_bus_endpoint()
   device_control_endpoint = Config.get_device_control_endpoint()

   # Get SHM path
   shm_base_path = Config.get_shm_base_path()

   # Debug and logging
   is_debug = Config.is_debug()
   log_level = Config.get_log_level()

Environment Variable Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The SDK automatically reads configuration from environment variables:

.. code-block:: bash

   export APP_ID=my_app
   export AI_RUNTIME_ENDPOINT=unix:///run/aipc/ai-runtime.sock
   export EVENT_BUS_ENDPOINT=unix:///run/aipc/event-bus.sock
   export DEVICE_CONTROL_ENDPOINT=unix:///run/aipc/device-control.sock
   export SHM_BASE_PATH=/run/aipc/shm
   export DEBUG=1
   export LOG_LEVEL=DEBUG

.. code-block:: python

   from hailo_ipc_sdk import Config

   # Automatically loaded from environment variables
   print(Config.get_app_id())  # Output: my_app
   print(Config.get_inference_endpoint())  # Output: unix:///run/aipc/ai-runtime.sock
