Application Manager Client
==========================

.. automodule:: hailo_ipc_sdk.app
    :members:
    :undoc-members:
    :show-inheritance:

Usage Examples
--------------

Application Lifecycle
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import AppClient

   app = AppClient()

   # List all applications
   apps = app.list_apps()
   for a in apps:
       print(f"{a.name}: {a.state}")

   # Install application
   app_id = app.install_app(
       manifest_path="/data/apps/my_app/app.yaml",
       image_path="/data/apps/my_app/image.tar"
   )

   # Start application
   app.start_app(app_id)

   # Restart application (stop + start)
   app.restart_app(app_id, timeout_seconds=30)

   # Stop application
   app.stop_app(app_id)

   # Uninstall application
   app.uninstall_app(app_id, keep_logs=True)

Getting Application Info
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get application details
   info = app.get_app("my_app")
   print(f"Name: {info.name}")
   print(f"Version: {info.version}")
   print(f"State: {info.state}")

   # Get application statistics
   stats = app.get_app_stats("my_app")
   print(f"CPU: {stats.cpu_usage_percent}%")
   print(f"Memory: {stats.memory_usage_bytes / 1024 / 1024:.1f} MB")

Viewing Application Logs
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get last 100 log lines
   for line in app.get_logs("my_app", max_lines=100):
       print(line)

   # Follow logs in real-time
   for line in app.get_logs("my_app", follow=True):
       print(line)

   # Get text-formatted logs
   for text in app.get_logs_text("my_app"):
       print(text)

Registering Web URL
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Register web access path (inside app container)
   # Requires APP_ID environment variable (injected by platform)
   app.register_web_url("/")

   # Register custom path
   app.register_web_url("/dashboard")

Context Manager
~~~~~~~~~~~~~~~

.. code-block:: python

   with AppClient() as app:
       apps = app.list_apps()
       for a in apps:
           print(f"{a.name}: {a.state}")
