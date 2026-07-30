Device Control API
==================

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

Data Types
----------

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

Usage Examples
--------------

Light Control
~~~~~~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import DeviceClient, IrCutMode

   dev = DeviceClient()

   # White light control
   dev.set_white_light(0)      # Off
   dev.set_white_light(50)     # 50% brightness
   dev.set_white_light(100)    # 100% brightness

   # IR LED control
   dev.set_ir_led(True)        # On
   dev.set_ir_led(False)       # Off

   # IR cut filter control
   dev.set_ircut(IrCutMode.DAY)    # Day mode (filter on)
   dev.set_ircut(IrCutMode.NIGHT)  # Night mode (filter off)
   dev.set_ircut(IrCutMode.AUTO)   # Auto mode

PTZ Control
~~~~~~~~~~~

.. code-block:: python

   # Pan movement
   dev.pan_left(speed=50)   # Move left
   dev.pan_right(speed=50)  # Move right
   dev.pan_stop()           # Stop horizontal movement

   # Tilt movement
   dev.tilt_up(speed=50)    # Move up
   dev.tilt_down(speed=50)  # Move down
   dev.tilt_stop()          # Stop vertical movement

   # Stop all PTZ movement
   dev.ptz_stop()

Preset Control
~~~~~~~~~~~~~~

.. code-block:: python

   # Save preset
   dev.save_preset(1)  # Save current position to preset 1

   # Call preset
   dev.call_preset(1)  # Move to preset 1

Lens Control
~~~~~~~~~~~~

.. code-block:: python

   # Lens initialization
   dev.lens_init()              # Initialize lens module

   # Zoom
   dev.zoom_in(speed=50)        # Zoom in
   dev.zoom_out(speed=50)       # Zoom out
   dev.zoom_stop()              # Stop zoom

   # Set zoom level (0.0 ~ 1.0)
   dev.set_zoom_level(0.5)      # 50% zoom position

   # Focus
   dev.focus_in(speed=50)       # Far focus
   dev.focus_out(speed=50)      # Near focus
   dev.focus_stop()             # Stop focus

   # Set focus level (0.0 ~ 1.0)
   dev.set_focus_level(0.5)     # 50% focus position

   # Auto focus
   dev.focus_auto(enable=True)   # Enable auto focus
   dev.focus_auto(enable=False)  # Disable auto focus

   # One-shot auto focus (composite: enable → wait for convergence → disable)
   dev.oneshot_autofocus(timeout=20.0)

   # Zoom + focus linked move (by optical zoom ratio and focus distance)
   dev.lens_goto_ratio_distance(zoom_ratio=2.0, focus_distance_m=3.0)

   # Iris control
   dev.control_iris(open=True)   # Open iris
   dev.set_iris_target(128)      # Set iris target value

   # Lens reset zero
   dev.lens_reset_zero(zoom=True, focus=True)   # Reset both axes

   # Set lens limits
   dev.set_lens_limits(zoom_limit={"min_pos": 0, "max_pos": 1000})
   dev.set_lens_limits(
       zoom_limit={"min_pos": 0, "max_pos": 1000},
       focus_limit={"min_pos": 0, "max_pos": 800},
   )

   # Get lens status
   status = dev.get_lens_status()
   print(f"Zoom pos: {status['zoom_pos']}")
   print(f"Focus pos: {status['focus_pos']}")
   print(f"Zoom state: {status['zoom_state']}")  # 0=not ready, 1=idle, 2=moving
   print(f"Autofocus: {status['autofocus_enabled']}")

GPIO Control
~~~~~~~~~~~~

.. code-block:: python

   # Read GPIO
   value = dev.gpio_get(12)
   print(f"GPIO 12 state: {'high' if value else 'low'}")

   # Write GPIO
   dev.gpio_set(21, True)   # Set high
   dev.gpio_set(21, False)  # Set low

   # Control relay
   dev.gpio_set(22, True)   # Turn on relay

Wiegand Control
~~~~~~~~~~~~~~~

.. code-block:: python

   # Set Wiegand output
   dev.set_wiegand_out(channel=0, enable=True)   # Enable Wiegand channel 0
   dev.set_wiegand_out(channel=1, enable=False)  # Disable Wiegand channel 1

   # Query Wiegand output state
   enabled = dev.get_wiegand_out(channel=0)
   print(f"Wiegand channel 0: {'enabled' if enabled else 'disabled'}")

RS-485 Serial Control
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Initialize RS-485
   dev.rs485_init(baudrate=9600)

   # Transmit data
   dev.rs485_tx(b"hello")

   # Deinitialize
   dev.rs485_deinit()

Getting Device Status
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get full status
   status = dev.get_device_status()

   print(f"SoC temperature: {status.soc_temp_c}°C")
   print(f"MCU temperature: {status.mcu_temp_c}°C")
   print(f"Light sensor: {status.light_sensor}")
   print(f"White light: {status.white_light_level}%")
   print(f"IR LED: {'on' if status.ir_led_on else 'off'}")
   print(f"IR-Cut: {status.ircut_mode}")
   print(f"PTZ position: Pan={status.ptz_pan_pos}, Tilt={status.ptz_tilt_pos}")
   print(f"Zoom position: {status.zoom_pos}")
   print(f"Focus position: {status.focus_pos}")
   print(f"Auto focus: {'enabled' if status.autofocus_enabled else 'disabled'}")
   print(f"MCU version: {status.mcu_version}")
   print(f"MCU uptime: {status.mcu_uptime_ms}ms")

Monitoring Device Events
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Subscribe to device events
   for event in dev.subscribe_events():
       print(f"Event type: {event.type}")
       print(f"Timestamp: {event.timestamp_ns}")

       if event.type == DeviceEvent.EventType.GPIO_CHANGE:
           print(f"GPIO pin: {event.gpio_pin}, value: {event.gpio_value}")
       elif event.type == DeviceEvent.EventType.LIGHT_SENSOR_CHANGE:
           print(f"Light sensor value: {event.light_sensor_value}")
       elif event.type == DeviceEvent.EventType.TEMPERATURE_ALERT:
           print(f"Temperature alert: {event.temperature}°C")
       elif event.type == DeviceEvent.EventType.PTZ_MOVE_COMPLETE:
           print("PTZ move complete")
       elif event.type == DeviceEvent.EventType.FOCUS_COMPLETE:
           print("Focus complete")

Context Manager
~~~~~~~~~~~~~~~

.. code-block:: python

   # Use context manager for automatic connection management
   with DeviceClient() as dev:
       dev.set_white_light(80)
       status = dev.get_device_status()
       print(f"Light: {status.white_light_level}%")

Error Handling
~~~~~~~~~~~~~~

.. code-block:: python

   from grpc import RpcError

   try:
       dev.set_white_light(150)  # Invalid value
   except RuntimeError as e:
       print(f"Setting failed: {e}")

   try:
       value = dev.gpio_get(99)  # Invalid pin
   except RuntimeError as e:
       print(f"GPIO read failed: {e}")
