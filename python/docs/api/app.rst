应用管理器客户端
================

.. automodule:: hailo_ipc_sdk.app
    :members:
    :undoc-members:
    :show-inheritance:

使用示例
--------

应用生命周期管理
~~~~~~~~~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import AppClient

   app = AppClient()

   # 列出所有应用
   apps = app.list_apps()
   for a in apps:
       print(f"{a.name}: {a.state}")

   # 安装应用
   app_id = app.install_app(
       manifest_path="/data/apps/my_app/app.yaml",
       image_path="/data/apps/my_app/image.tar"
   )

   # 启动应用
   app.start_app(app_id)

   # 重启应用（停止+启动）
   app.restart_app(app_id, timeout_seconds=30)

   # 停止应用
   app.stop_app(app_id)

   # 卸载应用
   app.uninstall_app(app_id, keep_logs=True)

获取应用信息
~~~~~~~~~~~~

.. code-block:: python

   # 获取应用详情
   info = app.get_app("my_app")
   print(f"名称: {info.name}")
   print(f"版本: {info.version}")
   print(f"状态: {info.state}")

   # 获取应用统计
   stats = app.get_app_stats("my_app")
   print(f"CPU: {stats.cpu_usage_percent}%")
   print(f"内存: {stats.memory_usage_bytes / 1024 / 1024:.1f} MB")

查看应用日志
~~~~~~~~~~~~

.. code-block:: python

   # 获取最近 100 行日志
   for line in app.get_logs("my_app", max_lines=100):
       print(line)

   # 实时跟踪日志
   for line in app.get_logs("my_app", follow=True):
       print(line)

   # 获取文本格式日志
   for text in app.get_logs_text("my_app"):
       print(text)

注册 Web 访问路径
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # 在应用容器内注册 Web 访问路径
   # 需要环境变量 APP_ID（平台自动注入）
   app.register_web_url("/")

   # 注册自定义路径
   app.register_web_url("/dashboard")

上下文管理器
~~~~~~~~~~~~

.. code-block:: python

   with AppClient() as app:
       apps = app.list_apps()
       for a in apps:
           print(f"{a.name}: {a.state}")
