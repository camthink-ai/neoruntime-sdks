"""
Device Control Client
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterator, Optional

import grpc

from .proto import device_pb2, device_pb2_grpc


class IrCutMode(Enum):
    AUTO = 0
    DAY = 1
    NIGHT = 2


@dataclass
class DeviceStatus:
    soc_temp_c: float
    mcu_temp_c: float
    light_sensor: int
    ptz_pan_pos: int
    ptz_tilt_pos: int
    zoom_pos: int
    focus_pos: int
    autofocus_enabled: bool
    ircut_mode: IrCutMode
    white_light_level: int
    ir_led_on: bool
    mcu_version: str
    mcu_uptime_ms: int


@dataclass
class DeviceEvent:
    class EventType(Enum):
        GPIO_CHANGE = 0
        LIGHT_SENSOR_CHANGE = 1
        TEMPERATURE_ALERT = 2
        PTZ_MOVE_COMPLETE = 3
        FOCUS_COMPLETE = 4
    
    type: EventType
    timestamp_ns: int
    gpio_pin: int = 0
    gpio_value: bool = False
    light_sensor_value: int = 0
    temperature: float = 0.0


class DeviceClient:
    """
    Device Control Client
    
    Usage:
        dev = DeviceClient()
        
        dev.set_white_light(80)
        dev.set_ir_led(True)
        dev.set_ircut(IrCutMode.NIGHT)
        
        dev.pan_left(speed=50)
        dev.call_preset(3)
        
        dev.zoom_in()
        dev.focus_auto()
    """
    
    def __init__(self, endpoint: Optional[str] = None):
        if endpoint is None:
            endpoint = self._get_default_endpoint()
        
        self.endpoint = endpoint
        self.channel: Optional[grpc.Channel] = None
        self.stub: Optional[device_pb2_grpc.DeviceControlStub] = None
    
    def _get_default_endpoint(self) -> str:
        import os
        return os.getenv("DEVICE_CONTROL_ENDPOINT", "unix:///run/aipc/device-control.sock")
    
    def connect(self) -> None:
        if self.channel is None:
            self.channel = grpc.insecure_channel(self.endpoint)
            self.stub = device_pb2_grpc.DeviceControlStub(self.channel)

    @property
    def connected(self) -> bool:
        return self.channel is not None
    
    def close(self) -> None:
        if self.channel:
            self.channel.close()
            self.channel = None
            self.stub = None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def set_white_light(self, level: int) -> None:
        if self.stub is None:
            self.connect()
        
        request = device_pb2.LightLevelRequest(level=level)
        response = self.stub.SetWhiteLight(request)
        
        if not response.success:
            raise RuntimeError(f"SetWhiteLight failed: {response.message}")
    
    def set_ir_led(self, on: bool) -> None:
        if self.stub is None:
            self.connect()
        
        request = device_pb2.LightSwitchRequest(on=on)
        response = self.stub.SetIrLed(request)
        
        if not response.success:
            raise RuntimeError(f"SetIrLed failed: {response.message}")
    
    def set_ircut(self, mode: IrCutMode) -> None:
        if self.stub is None:
            self.connect()
        
        request = device_pb2.IrCutRequest(mode=mode.value)
        response = self.stub.SetIrCut(request)
        
        if not response.success:
            raise RuntimeError(f"SetIrCut failed: {response.message}")
    
    def pan_left(self, speed: int = 50) -> None:
        self._pan(device_pb2.PAN_LEFT, speed)
    
    def pan_right(self, speed: int = 50) -> None:
        self._pan(device_pb2.PAN_RIGHT, speed)
    
    def pan_stop(self) -> None:
        self._pan(device_pb2.PAN_STOP, 0)
    
    def _pan(self, direction: int, speed: int) -> None:
        if self.stub is None:
            self.connect()
        
        request = device_pb2.PanRequest(direction=direction, speed=speed)
        response = self.stub.Pan(request)
        
        if not response.success:
            raise RuntimeError(f"Pan failed: {response.message}")
    
    def tilt_up(self, speed: int = 50) -> None:
        self._tilt(device_pb2.TILT_UP, speed)
    
    def tilt_down(self, speed: int = 50) -> None:
        self._tilt(device_pb2.TILT_DOWN, speed)
    
    def tilt_stop(self) -> None:
        self._tilt(device_pb2.TILT_STOP, 0)
    
    def _tilt(self, direction: int, speed: int) -> None:
        if self.stub is None:
            self.connect()
        
        request = device_pb2.TiltRequest(direction=direction, speed=speed)
        response = self.stub.Tilt(request)
        
        if not response.success:
            raise RuntimeError(f"Tilt failed: {response.message}")
    
    def ptz_stop(self) -> None:
        if self.stub is None:
            self.connect()
        
        request = device_pb2.PTZStopRequest()
        response = self.stub.PTZStop(request)
        
        if not response.success:
            raise RuntimeError(f"PTZStop failed: {response.message}")
    
    def save_preset(self, preset_id: int) -> None:
        if self.stub is None:
            self.connect()
        
        request = device_pb2.PresetRequest(preset_id=preset_id)
        response = self.stub.SavePreset(request)
        
        if not response.success:
            raise RuntimeError(f"SavePreset failed: {response.message}")
    
    def call_preset(self, preset_id: int) -> None:
        if self.stub is None:
            self.connect()
        
        request = device_pb2.PresetRequest(preset_id=preset_id)
        response = self.stub.CallPreset(request)
        
        if not response.success:
            raise RuntimeError(f"CallPreset failed: {response.message}")
    
    def zoom_in(self, speed: int = 50) -> None:
        self.zoom(speed)
    
    def zoom_out(self, speed: int = 50) -> None:
        self.zoom(-speed)
    
    def zoom_stop(self) -> None:
        self.zoom(0)
    
    def zoom(self, speed: int) -> None:
        if self.stub is None:
            self.connect()
        
        request = device_pb2.ZoomRequest(speed=speed)
        response = self.stub.Zoom(request)
        
        if not response.success:
            raise RuntimeError(f"Zoom failed: {response.message}")
    
    def set_zoom_level(self, level: float) -> None:
        if self.stub is None:
            self.connect()
        
        request = device_pb2.ZoomLevelRequest(level=level)
        response = self.stub.SetZoomLevel(request)
        
        if not response.success:
            raise RuntimeError(f"SetZoomLevel failed: {response.message}")
    
    def focus_in(self, speed: int = 50) -> None:
        self.focus(speed)
    
    def focus_out(self, speed: int = 50) -> None:
        self.focus(-speed)
    
    def focus_stop(self) -> None:
        self.focus(0)
    
    def focus(self, speed: int) -> None:
        if self.stub is None:
            self.connect()
        
        request = device_pb2.FocusRequest(speed=speed)
        response = self.stub.Focus(request)
        
        if not response.success:
            raise RuntimeError(f"Focus failed: {response.message}")
    
    def focus_auto(self, enable: bool = True) -> None:
        if self.stub is None:
            self.connect()

        request = device_pb2.AutofocusRequest(enable=enable)
        response = self.stub.SetAutofocus(request)

        if not response.success:
            raise RuntimeError(f"SetAutofocus failed: {response.message}")

    def set_focus_level(self, level: float) -> None:
        if self.stub is None:
            self.connect()

        request = device_pb2.FocusLevelRequest(level=level)
        response = self.stub.SetFocusLevel(request)

        if not response.success:
            raise RuntimeError(f"SetFocusLevel failed: {response.message}")

    def get_lens_status(self) -> Dict[str, Any]:
        if self.stub is None:
            self.connect()

        response = self.stub.GetLensStatus(device_pb2.Empty())
        result: Dict[str, Any] = {
            "zoom_pos": response.zoom_pos,
            "focus_pos": response.focus_pos,
            "zoom_state": response.zoom_state,
            "focus_state": response.focus_state,
            "zoom_rz_done": response.zoom_rz_done,
            "focus_rz_done": response.focus_rz_done,
            "autofocus_enabled": response.autofocus_enabled,
        }
        if response.HasField("zoom_limit"):
            result["zoom_limit"] = {"min_pos": response.zoom_limit.min_pos, "max_pos": response.zoom_limit.max_pos}
        if response.HasField("focus_limit"):
            result["focus_limit"] = {"min_pos": response.focus_limit.min_pos, "max_pos": response.focus_limit.max_pos}
        return result

    def set_lens_limits(self,
                        zoom_limit: Optional[Dict[str, int]] = None,
                        focus_limit: Optional[Dict[str, int]] = None) -> None:
        """Set lens axis position limits.

        Args:
            zoom_limit: Dict with ``min_pos`` and ``max_pos`` keys, or None to skip.
            focus_limit: Dict with ``min_pos`` and ``max_pos`` keys, or None to skip.

        Example::

            dev.set_lens_limits(zoom_limit={"min_pos": 0, "max_pos": 1000})
            dev.set_lens_limits(
                zoom_limit={"min_pos": 0, "max_pos": 1000},
                focus_limit={"min_pos": 0, "max_pos": 800},
            )
        """
        if self.stub is None:
            self.connect()

        request = device_pb2.LensLimitsRequest()
        if zoom_limit is not None:
            request.zoom_limit.min_pos = zoom_limit["min_pos"]
            request.zoom_limit.max_pos = zoom_limit["max_pos"]
        if focus_limit is not None:
            request.focus_limit.min_pos = focus_limit["min_pos"]
            request.focus_limit.max_pos = focus_limit["max_pos"]

        response = self.stub.SetLensLimits(request)
        if not response.success:
            raise RuntimeError(f"SetLensLimits failed: {response.message}")

    def oneshot_autofocus(self, timeout: float = 20.0) -> None:
        """Perform a single autofocus cycle: enable → wait for convergence → disable.

        This is a composite operation that:
        1. Enables continuous autofocus
        2. Polls lens status until focus motor settles (or timeout)
        3. Disables continuous autofocus

        Args:
            timeout: Maximum seconds to wait for focus convergence (default: 20.0)

        Raises:
            RuntimeError: If autofocus fails to converge within timeout
            TimeoutError: If focus motor does not settle within timeout
        """
        import time

        if self.stub is None:
            self.connect()

        # Step 1: Enable autofocus
        af_req = device_pb2.AutofocusRequest(enable=True)
        response = self.stub.SetAutofocus(af_req)
        if not response.success:
            raise RuntimeError(f"Enable autofocus failed: {response.message}")

        # Step 2: Wait for focus motor to settle
        # Give initial settling time (matching backend's 1500ms)
        time.sleep(1.5)

        deadline = time.monotonic() + timeout
        settled = False

        while time.monotonic() < deadline:
            status = self.stub.GetLensStatus(device_pb2.Empty())
            # Focus is settled when motor is stopped (state=1) or NoCfg (state=0)
            # MotorState: NoCfg=0, Stopped=1, Running=2, ResetZero=3, Error=4
            if status.focus_state in (1, 0):
                settled = True
                break
            if status.focus_state == 4:  # Error
                raise RuntimeError("Autofocus failed: focus motor error")
            time.sleep(0.2)

        # Step 3: Disable autofocus (regardless of convergence)
        af_req = device_pb2.AutofocusRequest(enable=False)
        self.stub.SetAutofocus(af_req)

        if not settled:
            raise TimeoutError(f"Autofocus did not converge within {timeout}s")

    def set_wiegand_out(self, channel: int, enable: bool) -> None:
        """Enable or disable a Wiegand output channel.

        Args:
            channel: Wiegand channel number (typically 0 or 1)
            enable: True to enable, False to disable
        """
        if self.stub is None:
            self.connect()

        request = device_pb2.AlarmChannelRequest(channel=channel, enable=enable)
        response = self.stub.SetWiegandOut(request)

        if not response.success:
            raise RuntimeError(f"SetWiegandOut failed: {response.message}")

    def get_wiegand_out(self, channel: int) -> bool:
        """Get the enabled state of a Wiegand output channel.

        Args:
            channel: Wiegand channel number (typically 0 or 1)

        Returns:
            True if the channel is enabled
        """
        if self.stub is None:
            self.connect()

        request = device_pb2.AlarmChannelRequest(channel=channel)
        response = self.stub.GetWiegandOut(request)

        if not response.success:
            raise RuntimeError(f"GetWiegandOut failed: {response.message}")

        return response.enabled

    def rs485_init(self, baudrate: int, config: str = "") -> None:
        """Initialize RS-485 serial interface.

        Args:
            baudrate: Baud rate (e.g. 9600, 115200)
            config: Optional configuration string
        """
        if self.stub is None:
            self.connect()

        request = device_pb2.Rs485InitRequest(baudrate=baudrate, config=config)
        response = self.stub.Rs485Init(request)

        if not response.success:
            raise RuntimeError(f"Rs485Init failed: {response.message}")

    def rs485_deinit(self) -> None:
        """Deinitialize RS-485 serial interface."""
        if self.stub is None:
            self.connect()

        response = self.stub.Rs485Deinit(device_pb2.Empty())

        if not response.success:
            raise RuntimeError(f"Rs485Deinit failed: {response.message}")

    def rs485_tx(self, data: bytes) -> None:
        """Transmit data over RS-485.

        Args:
            data: Bytes to transmit
        """
        if self.stub is None:
            self.connect()

        request = device_pb2.Rs485TxRequest(data=data)
        response = self.stub.Rs485Tx(request)

        if not response.success:
            raise RuntimeError(f"Rs485Tx failed: {response.message}")

    def lens_reset_zero(self, zoom: bool = True, focus: bool = True) -> None:
        if self.stub is None:
            self.connect()

        request = device_pb2.LensResetRequest(zoom=zoom, focus=focus)
        response = self.stub.LensResetZero(request)

        if not response.success:
            raise RuntimeError(f"LensResetZero failed: {response.message}")

    def control_iris(self, open: bool) -> None:
        if self.stub is None:
            self.connect()

        request = device_pb2.IrisRequest(open=open)
        response = self.stub.ControlIris(request)

        if not response.success:
            raise RuntimeError(f"ControlIris failed: {response.message}")

    def set_iris_target(self, target: int) -> None:
        if self.stub is None:
            self.connect()

        request = device_pb2.IrisTargetRequest(target=target)
        response = self.stub.SetIrisTarget(request)

        if not response.success:
            raise RuntimeError(f"SetIrisTarget failed: {response.message}")

    def lens_init(self) -> None:
        if self.stub is None:
            self.connect()

        request = device_pb2.LensInitRequest()
        response = self.stub.LensInit(request)

        if not response.success:
            raise RuntimeError(f"LensInit failed: {response.message}")

    def lens_goto_ratio_distance(self, zoom_ratio: float, focus_distance_m: float) -> None:
        if self.stub is None:
            self.connect()

        request = device_pb2.GotoRatioDistanceRequest(zoom_ratio=zoom_ratio, focus_distance_m=focus_distance_m)
        response = self.stub.LensGotoRatioDistance(request)

        if not response.success:
            raise RuntimeError(f"LensGotoRatioDistance failed: {response.message}")

    def gpio_set(self, pin: int, value: bool) -> None:
        if self.stub is None:
            self.connect()
        
        request = device_pb2.GPIOWriteRequest(pin=pin, value=value)
        response = self.stub.GPIOWrite(request)
        
        if not response.success:
            raise RuntimeError(f"GPIOWrite failed: {response.message}")
    
    def gpio_get(self, pin: int) -> bool:
        if self.stub is None:
            self.connect()
        
        request = device_pb2.GPIOReadRequest(pin=pin)
        response = self.stub.GPIORead(request)
        
        if not response.status.success:
            raise RuntimeError(f"GPIORead failed: {response.status.message}")
        
        return response.value
    
    def get_device_status(self) -> DeviceStatus:
        if self.stub is None:
            self.connect()
        
        response = self.stub.GetDeviceStatus(device_pb2.Empty())
        
        return DeviceStatus(
            soc_temp_c=response.soc_temp_c,
            mcu_temp_c=response.mcu_temp_c,
            light_sensor=response.light_sensor,
            ptz_pan_pos=response.ptz_pan_pos,
            ptz_tilt_pos=response.ptz_tilt_pos,
            zoom_pos=response.zoom_pos,
            focus_pos=response.focus_pos,
            autofocus_enabled=response.autofocus_enabled,
            ircut_mode=IrCutMode(response.ircut_mode),
            white_light_level=response.white_light_level,
            ir_led_on=response.ir_led_on,
            mcu_version=response.mcu_version,
            mcu_uptime_ms=response.mcu_uptime_ms
        )
    
    def subscribe_events(self) -> Iterator[DeviceEvent]:
        if self.stub is None:
            self.connect()
        
        for event_msg in self.stub.SubscribeEvents(device_pb2.Empty()):
            event = DeviceEvent(
                type=DeviceEvent.EventType(event_msg.type),
                timestamp_ns=event_msg.timestamp_ns
            )
            
            if event_msg.HasField('gpio_state'):
                event.gpio_pin = event_msg.gpio_state.pin
                event.gpio_value = event_msg.gpio_state.value
            
            if event_msg.HasField('light_sensor_value'):
                event.light_sensor_value = event_msg.light_sensor_value
            
            if event_msg.HasField('temperature'):
                event.temperature = event_msg.temperature
            
            yield event