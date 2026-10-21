设备控制 API
============

头文件 ``device.hpp`` 。执行器与传感器的全部入口：灯光 / 红外 /
IRCUT、云台、变焦 / 对焦与自动对焦套件、GPIO、RS485、Wiegand、整机
状态与设备事件。

接口一览
--------

``DeviceClient`` 公开面（按功能分组）：

连接 —— ``connect()`` / ``close()`` / ``connected()``

灯光与红外：

- ``set_white_light(level)`` —— 白光补光灯（0 关）
- ``set_ir_led(level)`` —— 红外灯等级
- ``set_ircut(mode)`` —— ``IrCutMode::Auto`` / ``IrCutMode::Day`` /
  ``IrCutMode::Night``

云台：

- ``pan_left(speed=50)`` / ``pan_right`` / ``pan_stop`` / ``tilt_up`` /
  ``tilt_down`` / ``tilt_stop`` / ``ptz_stop()``
- ``save_preset(preset_id)`` / ``call_preset(preset_id)`` —— 预置位

镜头（变焦 / 对焦 / 光圈）：

- ``zoom_in(speed=50)`` / ``zoom_out`` / ``zoom_stop`` / ``zoom(speed)``
  / ``set_zoom_level(level)``
- ``focus_in(speed=50)`` / ``focus_out`` / ``focus_stop`` /
  ``focus(speed)`` / ``focus_auto(enable=true)`` /
  ``set_focus_level(level)``
- ``get_lens_status()`` —— ``LensStatus`` ：电机状态、当前位置、
  上下限、光圈 ADC
- ``set_lens_limits(zoom_limit=nullopt, focus_limit=nullopt)`` ——
  限制行程
- ``oneshot_autofocus(timeout_seconds=20.0)`` —— 阻塞式一次自动对焦
- ``lens_reset_zero(zoom=true, focus=true)`` / ``lens_init()`` /
  ``lens_goto_ratio_distance(zoom_ratio, focus_distance_m)``
- ``control_iris(speed)`` / ``set_iris_target(target)`` —— 光圈

原生自动对焦作业（立即返回，轮询状态）：

- ``start_oneshot_af()`` / ``start_zoom_follow(ratio)`` —— 一次对焦 /
  锁定变焦比的连续对焦，返回 ``AfJob``
- ``get_autofocus_status()`` —— ``AfStatus`` （进度、置信度、最佳
  对焦位置）
- ``cancel_autofocus(job_id=0)`` —— 取消（0 = 当前作业）
- ``set_af_windows(enabled, windows, stream_id="main")`` —— 1-3 个
  像素矩形限定对焦区域
- ``get_af_measurement()`` —— ``AfMeasurement`` （对焦能量曲线等）

报警 I/O 与总线：

- ``set_wiegand_out(channel, enable)`` / ``get_wiegand_out(channel)``
- ``rs485_init(baudrate, config="")`` / ``rs485_deinit()`` /
  ``rs485_tx(data)``
- ``gpio_set(pin, value)`` / ``gpio_get(pin)``

状态与事件：

- ``get_device_status()`` —— ``DeviceStatus`` ：SoC / MCU 温度、
  光感、云台与镜头位置、IRCUT 模式、灯等级、MCU 版本与运行时长
- ``subscribe_events()`` —— 返回 ``DeviceEventStream`` ， ``next()``
  出 GPIO 变化 / 光感变化 / 温度告警 / 云台移动完成 / 对焦完成事件

完整参数文档见 `Doxygen 参考 <../../en/index.html>`_。

使用示例
--------

.. code-block:: cpp

   neoruntime_ipc_sdk::DeviceClient device;

   device.set_white_light(100);   // 0 关；告警联动灯的常见写法
   // ... 无人在画面后延时关灯
   device.set_white_light(0);

   auto status = device.get_device_status();   // 整机状态
   auto lens   = device.get_lens_status();     // soc_temp_c、
   // zoom_pos / focus_pos 与镜头上下限对照

.. tip::

   事件 + 设备联动是平台的惯用组合——参考
   ``examples/event_subscriber.cpp`` （收到 person 检测事件即点灯）
   与 ``examples/perimeter_guard.cpp`` （越线告警 + 5 秒冷却 + 10 秒
   后自动关灯，完整可编译）；事件面见 :doc:`events`。
