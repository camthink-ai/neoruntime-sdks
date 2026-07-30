设备控制 API
============

.. automodule:: hailo_ipc_sdk.device
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

DeviceClient
------------

.. autoclass:: hailo_ipc_sdk.DeviceClient
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

数据类型
--------

DeviceStatus
~~~~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.DeviceStatus
   :members:
   :undoc-members:

DeviceEvent
~~~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.DeviceEvent
   :members:
   :undoc-members:

IrCutMode
~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.IrCutMode
   :members:
   :undoc-members:

使用示例
--------

灯光控制
~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import DeviceClient, IrCutMode

   dev = DeviceClient()

   # 白光灯控制
   dev.set_white_light(0)      # 关闭
   dev.set_white_light(50)     # 50% 亮度
   dev.set_white_light(100)    # 100% 亮度

   # 红外灯控制
   dev.set_ir_led(True)        # 打开
   dev.set_ir_led(False)       # 关闭

   # 红外滤光片控制
   dev.set_ircut(IrCutMode.DAY)    # 日间模式（滤光片开启）
   dev.set_ircut(IrCutMode.NIGHT)  # 夜间模式（滤光片关闭）
   dev.set_ircut(IrCutMode.AUTO)   # 自动模式

云台控制 (PTZ)
~~~~~~~~~~~~~~

.. code-block:: python

   # 左右移动
   dev.pan_left(speed=50)   # 向左移动
   dev.pan_right(speed=50)  # 向右移动
   dev.pan_stop()           # 停止水平移动

   # 上下移动
   dev.tilt_up(speed=50)    # 向上移动
   dev.tilt_down(speed=50)  # 向下移动
   dev.tilt_stop()          # 停止垂直移动

   # 停止所有云台运动
   dev.ptz_stop()

预置位控制
~~~~~~~~~~

.. code-block:: python

   # 保存预置位
   dev.save_preset(1)  # 保存当前位置到预置位 1

   # 调用预置位
   dev.call_preset(1)  # 移动到预置位 1

镜头控制
~~~~~~~~

.. code-block:: python

   # 镜头初始化
   dev.lens_init()             # 初始化镜头模组

   # 变焦
   dev.zoom_in(speed=50)       # 放大
   dev.zoom_out(speed=50)      # 缩小
   dev.zoom_stop()             # 停止变焦

   # 设置变焦级别 (0.0 ~ 1.0)
   dev.set_zoom_level(0.5)     # 50% 变焦位置

   # 对焦
   dev.focus_in(speed=50)      # 远焦
   dev.focus_out(speed=50)     # 近焦
   dev.focus_stop()            # 停止对焦

   # 设置对焦级别 (0.0 ~ 1.0)
   dev.set_focus_level(0.5)    # 50% 对焦位置

   # 自动对焦
   dev.focus_auto(enable=True)   # 开启自动对焦
   dev.focus_auto(enable=False)  # 关闭自动对焦

   # 单次自动对焦（复合操作：开启→等待收敛→关闭）
   dev.oneshot_autofocus(timeout=20.0)

   # 变焦+对焦联动 (按光学变焦比和对焦距离)
   dev.lens_goto_ratio_distance(zoom_ratio=2.0, focus_distance_m=3.0)

   # 光圈控制
   dev.control_iris(open=True)   # 打开光圈
   dev.set_iris_target(128)      # 设置光圈目标值

   # 镜头归零
   dev.lens_reset_zero(zoom=True, focus=True)   # 双轴归零

   # 设置镜头限位
   dev.set_lens_limits(zoom_limit={"min_pos": 0, "max_pos": 1000})
   dev.set_lens_limits(
       zoom_limit={"min_pos": 0, "max_pos": 1000},
       focus_limit={"min_pos": 0, "max_pos": 800},
   )

   # 获取镜头状态
   status = dev.get_lens_status()
   print(f"变焦位置: {status['zoom_pos']}")
   print(f"对焦位置: {status['focus_pos']}")
   print(f"变焦状态: {status['zoom_state']}")  # 0=未就绪, 1=空闲, 2=运行中
   print(f"自动对焦: {status['autofocus_enabled']}")

GPIO 控制
~~~~~~~~~

.. code-block:: python

   # 读取 GPIO
   value = dev.gpio_get(12)
   print(f"GPIO 12 状态: {'高' if value else '低'}")

   # 写入 GPIO
   dev.gpio_set(21, True)   # 设置为高电平
   dev.gpio_set(21, False)  # 设置为低电平

   # 控制继电器
   dev.gpio_set(22, True)   # 打开继电器

韦根 (Wiegand) 控制
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # 设置韦根输出
   dev.set_wiegand_out(channel=0, enable=True)   # 启用韦根通道 0
   dev.set_wiegand_out(channel=1, enable=False)  # 禁用韦根通道 1

   # 查询韦根输出状态
   enabled = dev.get_wiegand_out(channel=0)
   print(f"韦根通道 0: {'启用' if enabled else '禁用'}")

RS-485 串口控制
~~~~~~~~~~~~~~~

.. code-block:: python

   # 初始化 RS-485
   dev.rs485_init(baudrate=9600)

   # 发送数据
   dev.rs485_tx(b"hello")

   # 反初始化
   dev.rs485_deinit()

获取设备状态
~~~~~~~~~~~~

.. code-block:: python

   # 获取完整状态
   status = dev.get_device_status()

   print(f"SoC 温度: {status.soc_temp_c}°C")
   print(f"MCU 温度: {status.mcu_temp_c}°C")
   print(f"光照传感器: {status.light_sensor}")
   print(f"白光灯: {status.white_light_level}%")
   print(f"红外灯: {'开' if status.ir_led_on else '关'}")
   print(f"IR-Cut: {status.ircut_mode}")
   print(f"云台位置: Pan={status.ptz_pan_pos}, Tilt={status.ptz_tilt_pos}")
   print(f"变焦位置: {status.zoom_pos}")
   print(f"对焦位置: {status.focus_pos}")
   print(f"自动对焦: {'启用' if status.autofocus_enabled else '禁用'}")
   print(f"MCU 版本: {status.mcu_version}")
   print(f"MCU 运行时间: {status.mcu_uptime_ms}ms")

监控设备事件
~~~~~~~~~~~~

.. code-block:: python

   # 订阅设备事件
   for event in dev.subscribe_events():
       print(f"事件类型: {event.type}")
       print(f"时间戳: {event.timestamp_ns}")

       if event.type == DeviceEvent.EventType.GPIO_CHANGE:
           print(f"GPIO 引脚: {event.gpio_pin}, 值: {event.gpio_value}")
       elif event.type == DeviceEvent.EventType.LIGHT_SENSOR_CHANGE:
           print(f"光照传感器值: {event.light_sensor_value}")
       elif event.type == DeviceEvent.EventType.TEMPERATURE_ALERT:
           print(f"温度告警: {event.temperature}°C")
       elif event.type == DeviceEvent.EventType.PTZ_MOVE_COMPLETE:
           print("PTZ 移动完成")
       elif event.type == DeviceEvent.EventType.FOCUS_COMPLETE:
           print("对焦完成")

上下文管理器
~~~~~~~~~~~~

.. code-block:: python

   # 使用上下文管理器自动管理连接
   with DeviceClient() as dev:
       dev.set_white_light(80)
       status = dev.get_device_status()
       print(f"灯光: {status.white_light_level}%")

错误处理
~~~~~~~~

.. code-block:: python

   from grpc import RpcError

   try:
       dev.set_white_light(150)  # 无效的值
   except RuntimeError as e:
       print(f"设置失败: {e}")

   try:
       value = dev.gpio_get(99)  # 无效引脚
   except RuntimeError as e:
       print(f"GPIO 读取失败: {e}")