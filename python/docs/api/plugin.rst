插件系统 API
============

.. automodule:: hailo_ipc_sdk.plugin
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

PluginDiscovery
----------------

.. autoclass:: hailo_ipc_sdk.PluginDiscovery
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

PluginServer
------------

.. autoclass:: hailo_ipc_sdk.PluginServer
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

数据类型
--------

PluginEndpoint
~~~~~~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.PluginEndpoint
   :members:
   :undoc-members:

使用示例
--------

发现插件
~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import PluginDiscovery

   discovery = PluginDiscovery()

   # 查找提供特定能力的插件
   endpoint = discovery.get("rtsp-server")

   if endpoint:
       print(f"找到插件: {endpoint.app_id}")
       print(f"能力ID: {endpoint.capability_id}")
       print(f"版本: {endpoint.version}")
       print(f"传输: {endpoint.transport}")
       print(f"状态: {endpoint.state}")
       print(f"是否可用: {endpoint.is_available}")

       if endpoint.socket_path:
           print(f"Socket 路径: {endpoint.socket_path}")
       if endpoint.grpc_service:
           print(f"gRPC 服务: {endpoint.grpc_service}")

       # 事件主题
       print(f"发布事件: {endpoint.event_publish}")
       print(f"订阅事件: {endpoint.event_subscribe}")

等待插件就绪
~~~~~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import PluginDiscovery

   discovery = PluginDiscovery()

   # 等待插件可用（阻塞直到插件就绪或超时）
   try:
       endpoint = discovery.require("rtsp-server", timeout=30.0)
       print(f"插件已就绪: {endpoint.app_id}")
   except TimeoutError:
       print("插件在超时时间内未就绪")

列出所有插件
~~~~~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import PluginDiscovery

   discovery = PluginDiscovery()

   # 列出所有已知插件
   plugins = discovery.list_plugins()
   for app_id, plugin_info in plugins.items():
       print(f"应用ID: {app_id}")
       print(f"状态: {plugin_info.get('state')}")
       print(f"能力: {plugin_info.get('capabilities')}")

   # 列出所有已知能力ID
   capabilities = discovery.list_capabilities()
   print(f"所有能力: {capabilities}")

调用插件服务
~~~~~~~~~~~~

.. code-block:: python

   import grpc
   from hailo_ipc_sdk import PluginDiscovery

   # 发现插件
   discovery = PluginDiscovery()
   endpoint = discovery.get("rtsp-server")

   if endpoint and endpoint.socket_path:
       # 连接到插件的 gRPC 服务
       channel = endpoint.connect()

       # 导入插件的 proto stub
       from rtsp_pb2_grpc import RtspServiceStub

       stub = RtspServiceStub(channel)

       # 调用插件方法
       response = stub.GetStreamUrl(...)
       print(f"RTSP URL: {response.url}")

       channel.close()

创建插件服务端
~~~~~~~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import PluginServer
   from concurrent import futures
   import grpc

   # 导入你的 gRPC service
   from my_plugin_pb2_grpc import MyPluginServiceServicer

   class MyPluginService(MyPluginServiceServicer):
       def MyMethod(self, request, context):
           # 实现你的插件逻辑
           return response

   # 创建插件服务器
   server = PluginServer("my-plugin")

   # 创建 gRPC 服务器
   grpc_server = server.create_server(max_workers=4)

   # 注册 gRPC 服务
   grpc_server.addservicer(MyPluginService(), None)

   # 启动服务器
   server.start()

   print("插件服务已启动")

   # 保持运行
   try:
       server.wait()
   except KeyboardInterrupt:
       server.stop()

完整插件示例
~~~~~~~~~~~~

.. code-block:: python

   # my_plugin.py
   from hailo_ipc_sdk import PluginServer, EventClient
   from my_plugin_pb2_grpc import MyPluginServiceServicer
   import logging

   logger = logging.getLogger(__name__)

   class MyPluginService(MyPluginServiceServicer):
       def __init__(self):
           self.events = EventClient()

       def ProcessData(self, request, context):
           logger.info(f"处理数据: {request.data}")

           # 发布事件
           self.events.publish("plugin/my-plugin/processed", {
               "status": "success",
               "result": "processed"
           })

           return response

   def main():
       # 配置日志
       logging.basicConfig(level=logging.INFO)

       # 创建插件服务器
       server = PluginServer("my-plugin")

       # 创建 gRPC 服务器
       grpc_server = server.create_server()

       # 注册服务
       service = MyPluginService()
       grpc_server.addservicer(service, None)

       # 启动
       logger.info("启动插件服务...")
       server.start()

       try:
           server.wait()
       except KeyboardInterrupt:
           logger.info("停止插件服务...")
           server.stop()

   if __name__ == "__main__":
       main()

插件依赖
~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import PluginDiscovery
   import grpc

   # 运行时发现依赖的插件
   discovery = PluginDiscovery()
   rtsp_endpoint = discovery.get("rtsp-server")

   if not rtsp_endpoint:
       raise RuntimeError("依赖的 RTSP 插件未找到")

   if not rtsp_endpoint.is_available:
       raise RuntimeError("RTSP 插件未运行")

   # 使用插件
   channel = rtsp_endpoint.connect()
   # ... 调用插件服务

监控插件变化
~~~~~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import PluginDiscovery

   discovery = PluginDiscovery()

   def on_change():
       print("插件配置已更改")
       # 重新获取插件信息
       endpoint = discovery.get("rtsp-server")
       if endpoint:
           print(f"插件状态: {endpoint.state}")

   # 注册监视回调
   discovery.watch(on_change)

错误处理
~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import PluginDiscovery

   discovery = PluginDiscovery()

   # 插件未找到
   endpoint = discovery.get("non-existent-plugin")
   if not endpoint:
       print("插件未找到")

   # 超时等待
   try:
       endpoint = discovery.require("rtsp-server", timeout=5.0)
   except TimeoutError:
       print("等待插件超时")

   # 连接失败
   try:
       endpoint = discovery.get("rtsp-server")
       if endpoint and endpoint.socket_path:
           channel = endpoint.connect()
   except Exception as e:
       print(f"连接插件失败: {e}")