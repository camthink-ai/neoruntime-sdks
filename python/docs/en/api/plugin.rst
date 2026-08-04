Plugin System API
=================

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

Data Types
----------

PluginEndpoint
~~~~~~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.PluginEndpoint
   :members:
   :undoc-members:

Usage Examples
--------------

Discovering Plugins
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import PluginDiscovery

   discovery = PluginDiscovery()

   # Find a plugin providing a specific capability
   endpoint = discovery.get("rtsp-server")

   if endpoint:
       print(f"Found plugin: {endpoint.app_id}")
       print(f"Capability ID: {endpoint.capability_id}")
       print(f"Version: {endpoint.version}")
       print(f"Transport: {endpoint.transport}")
       print(f"State: {endpoint.state}")
       print(f"Available: {endpoint.is_available}")

       if endpoint.socket_path:
           print(f"Socket path: {endpoint.socket_path}")
       if endpoint.grpc_service:
           print(f"gRPC service: {endpoint.grpc_service}")

       # Event topics
       print(f"Publish events: {endpoint.event_publish}")
       print(f"Subscribe events: {endpoint.event_subscribe}")

Waiting for Plugin Ready
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import PluginDiscovery

   discovery = PluginDiscovery()

   # Wait for plugin to become available (blocks until ready or timeout)
   try:
       endpoint = discovery.require("rtsp-server", timeout=30.0)
       print(f"Plugin ready: {endpoint.app_id}")
   except TimeoutError:
       print("Plugin did not become ready within the timeout period")

Listing All Plugins
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import PluginDiscovery

   discovery = PluginDiscovery()

   # List all known plugins
   plugins = discovery.list_plugins()
   for app_id, plugin_info in plugins.items():
       print(f"App ID: {app_id}")
       print(f"State: {plugin_info.get('state')}")
       print(f"Capabilities: {plugin_info.get('capabilities')}")

   # List all known capability IDs
   capabilities = discovery.list_capabilities()
   print(f"All capabilities: {capabilities}")

Invoking Plugin Services
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import grpc
   from hailo_ipc_sdk import PluginDiscovery

   # Discover plugin
   discovery = PluginDiscovery()
   endpoint = discovery.get("rtsp-server")

   if endpoint and endpoint.socket_path:
       # Connect to the plugin's gRPC service
       channel = endpoint.connect()

       # Import the plugin's proto stub
       from rtsp_pb2_grpc import RtspServiceStub

       stub = RtspServiceStub(channel)

       # Call plugin method
       response = stub.GetStreamUrl(...)
       print(f"RTSP URL: {response.url}")

       channel.close()

Creating a Plugin Server
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import PluginServer
   from concurrent import futures
   import grpc

   # Import your gRPC service
   from my_plugin_pb2_grpc import MyPluginServiceServicer

   class MyPluginService(MyPluginServiceServicer):
       def MyMethod(self, request, context):
           # Implement your plugin logic
           return response

   # Create plugin server
   server = PluginServer("my-plugin")

   # Create gRPC server
   grpc_server = server.create_server(max_workers=4)

   # Register gRPC service
   grpc_server.addservicer(MyPluginService(), None)

   # Start the server
   server.start()

   print("Plugin service started")

   # Keep running
   try:
       server.wait()
   except KeyboardInterrupt:
       server.stop()

Complete Plugin Example
~~~~~~~~~~~~~~~~~~~~~~~

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
           logger.info(f"Processing data: {request.data}")

           # Publish event
           self.events.publish("plugin/my-plugin/processed", {
               "status": "success",
               "result": "processed"
           })

           return response

   def main():
       # Configure logging
       logging.basicConfig(level=logging.INFO)

       # Create plugin server
       server = PluginServer("my-plugin")

       # Create gRPC server
       grpc_server = server.create_server()

       # Register service
       service = MyPluginService()
       grpc_server.addservicer(service, None)

       # Start
       logger.info("Starting plugin service...")
       server.start()

       try:
           server.wait()
       except KeyboardInterrupt:
           logger.info("Stopping plugin service...")
           server.stop()

   if __name__ == "__main__":
       main()

Plugin Dependencies
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import PluginDiscovery
   import grpc

   # Discover dependent plugins at runtime
   discovery = PluginDiscovery()
   rtsp_endpoint = discovery.get("rtsp-server")

   if not rtsp_endpoint:
       raise RuntimeError("Required RTSP plugin not found")

   if not rtsp_endpoint.is_available:
       raise RuntimeError("RTSP plugin is not running")

   # Use the plugin
   channel = rtsp_endpoint.connect()
   # ... invoke plugin services

Monitoring Plugin Changes
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import PluginDiscovery

   discovery = PluginDiscovery()

   def on_change():
       print("Plugin configuration changed")
       # Re-fetch plugin info
       endpoint = discovery.get("rtsp-server")
       if endpoint:
           print(f"Plugin state: {endpoint.state}")

   # Register watch callback
   discovery.watch(on_change)

Error Handling
~~~~~~~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import PluginDiscovery

   discovery = PluginDiscovery()

   # Plugin not found
   endpoint = discovery.get("non-existent-plugin")
   if not endpoint:
       print("Plugin not found")

   # Timeout waiting
   try:
       endpoint = discovery.require("rtsp-server", timeout=5.0)
   except TimeoutError:
       print("Timeout waiting for plugin")

   # Connection failure
   try:
       endpoint = discovery.get("rtsp-server")
       if endpoint and endpoint.socket_path:
           channel = endpoint.connect()
   except Exception as e:
       print(f"Failed to connect to plugin: {e}")
