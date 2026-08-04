配置 API
========

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

使用示例
--------

静态方法
~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import Config

   # 获取应用 ID
   app_id = Config.get_app_id()

   # 获取各服务 endpoint
   ai_runtime_endpoint = Config.get_inference_endpoint()
   event_bus_endpoint = Config.get_event_bus_endpoint()
   device_control_endpoint = Config.get_device_control_endpoint()

   # 获取 SHM 路径
   shm_base_path = Config.get_shm_base_path()

   # 调试和日志
   is_debug = Config.is_debug()
   log_level = Config.get_log_level()

环境变量配置
~~~~~~~~~~~~

SDK 自动从环境变量读取配置：

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

   # 自动从环境变量加载
   print(Config.get_app_id())  # 输出: my_app
   print(Config.get_inference_endpoint())  # 输出: unix:///run/aipc/ai-runtime.sock