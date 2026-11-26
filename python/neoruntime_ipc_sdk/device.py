"""
Device Control Client
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterator

import grpc  # noqa: F401 — tests patch device.grpc.insecure_channel

from ._transport import GrpcClient
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


@dataclass
class Rs485RxEvent:
    """One RS-485 frame received on the bus (idle-delimited, <= 512 bytes).

    timestamp_ns is the device-side receive time (host clock), not the MCU
    capture time.
    """

    data: bytes
    timestamp_ns: int


@dataclass
class AfJob:
    """Result of starting an autofocus job (native AF RPCs)."""

    accepted: bool
    job_id: int
    message: str


@dataclass
class AfStatus:
    """Full snapshot of the autofocus engine state."""

    job_id: int
    operation: str
    state: str
    progress: float
    busy: bool
    anchor_valid: bool
    requested_ratio: float
    effective_ratio: float
    zoom_pos: int
    focus_pos: int
    best_focus: int
    metric: float
    confidence: float
    reproducibility: float
    estimated_distance_m: float
    elapsed_ms: int
    error_code: int
    message: str


@dataclass
class AfMeasurement:
    """Per-window focus telemetry from the last AF measurement."""

    focus_energy: list
    mean_luma: list
    frame_id: int


class DeviceClient(GrpcClient):
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

    _stub_factory = device_pb2_grpc.DeviceControlStub
    _endpoint_env = "DEVICE_CONTROL_ENDPOINT"
    _endpoint_default = "unix:///run/aipc/device-control.sock"
    # Channel lifecycle, stub caching, connect/close/__enter__ live in GrpcClient.

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

    def get_lens_status(self) -> dict[str, Any]:
        if self.stub is None:
            self.connect()

        response = self.stub.GetLensStatus(device_pb2.Empty())
        result: dict[str, Any] = {
            "zoom_pos": response.zoom_pos,
            "focus_pos": response.focus_pos,
            "zoom_state": response.zoom_state,
            "focus_state": response.focus_state,
            "zoom_rz_done": response.zoom_rz_done,
            "focus_rz_done": response.focus_rz_done,
            "autofocus_enabled": response.autofocus_enabled,
        }
        if response.HasField("zoom_limit"):
            result["zoom_limit"] = {
                "min_pos": response.zoom_limit.min_pos,
                "max_pos": response.zoom_limit.max_pos,
            }
        if response.HasField("focus_limit"):
            result["focus_limit"] = {
                "min_pos": response.focus_limit.min_pos,
                "max_pos": response.focus_limit.max_pos,
            }
        return result

    def set_lens_limits(
        self,
        zoom_limit: dict[str, int] | None = None,
        focus_limit: dict[str, int] | None = None,
    ) -> None:
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

    # ------------------------------------------------------------------
    # Native autofocus job APIs (device-control StartOneShotAf family)
    # ------------------------------------------------------------------

    def start_oneshot_af(self) -> AfJob:
        """Start a one-shot autofocus job and return its handle immediately.

        Unlike :meth:`oneshot_autofocus` (a blocking composite over the
        legacy SetAutofocus RPC), this returns at once; pair it with
        :meth:`get_autofocus_status` to poll for convergence.
        """
        if self.stub is None:
            self.connect()

        response = self.stub.StartOneShotAf(device_pb2.Empty())
        if not response.accepted:
            raise RuntimeError(f"StartOneShotAf rejected: {response.message}")
        return AfJob(accepted=response.accepted, job_id=response.job_id, message=response.message)

    def start_zoom_follow(self, ratio: float) -> AfJob:
        """Start continuous autofocus locked to a zoom ratio.

        Args:
            ratio: Zoom ratio the focus engine should track (e.g. 1.5).
        """
        if self.stub is None:
            self.connect()

        request = device_pb2.ZoomFollowRequest(ratio=ratio)
        response = self.stub.StartZoomFollow(request)
        if not response.accepted:
            raise RuntimeError(f"StartZoomFollow rejected: {response.message}")
        return AfJob(accepted=response.accepted, job_id=response.job_id, message=response.message)

    def get_autofocus_status(self) -> AfStatus:
        """Snapshot of the autofocus engine (job, progress, lens positions)."""
        if self.stub is None:
            self.connect()

        r = self.stub.GetAutofocusStatus(device_pb2.Empty())
        return AfStatus(
            job_id=r.job_id,
            operation=r.operation,
            state=r.state,
            progress=r.progress,
            busy=r.busy,
            anchor_valid=r.anchor_valid,
            requested_ratio=r.requested_ratio,
            effective_ratio=r.effective_ratio,
            zoom_pos=r.zoom_pos,
            focus_pos=r.focus_pos,
            best_focus=r.best_focus,
            metric=r.metric,
            confidence=r.confidence,
            reproducibility=r.reproducibility,
            estimated_distance_m=r.estimated_distance_m,
            elapsed_ms=r.elapsed_ms,
            error_code=r.error_code,
            message=r.message,
        )

    def cancel_autofocus(self, job_id: int = 0) -> None:
        """Cancel an autofocus job.

        Args:
            job_id: Job to cancel; 0 (default) cancels the active job.
        """
        if self.stub is None:
            self.connect()

        request = device_pb2.AfJobRequest(job_id=job_id)
        response = self.stub.CancelAutofocus(request)
        if not response.success:
            raise RuntimeError(f"CancelAutofocus failed: {response.message}")

    def set_af_windows(self, enabled: bool, windows, stream_id: str = "main") -> None:
        """Set autofocus measurement windows for a stream.

        Args:
            enabled: Whether AF windows are active.
            windows: 1-3 ``(x, y, w, h)`` pixel rectangles. An AF window
                restricts the image region the focus metric is computed on.
            stream_id: Stream the windows apply to (default "main").
        """
        if self.stub is None:
            self.connect()

        if len(windows) > 3:
            raise ValueError("at most 3 AF windows are supported")
        request = device_pb2.SetAfWindowsRequest(enabled=enabled, stream_id=stream_id)
        for x, y, w, h in windows:
            request.windows.add(x=x, y=y, w=w, h=h)
        response = self.stub.SetAfWindows(request)
        if not response.success:
            raise RuntimeError(f"SetAfWindows failed: {response.message}")

    def get_af_measurement(self) -> AfMeasurement:
        """Latest per-window focus telemetry (focus energy / luma)."""
        if self.stub is None:
            self.connect()

        r = self.stub.GetAfMeasurement(device_pb2.Empty())
        return AfMeasurement(
            focus_energy=list(r.focus_energy), mean_luma=list(r.mean_luma), frame_id=r.frame_id
        )

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

    def subscribe_rs485_rx(
        self, queue_size: int = 16, drop_old: bool = True
    ) -> Iterator[Rs485RxEvent]:
        """Stream RS-485 RX frames; one event per received bus frame.

        Valid before rs485_init() as well — the stream simply stays silent
        until the device's RS-485 driver produces frames. The iterator ends
        with a grpc.RpcError when the stream breaks (e.g. old firmware
        without SubscribeRs485Rx, or the service stopping).

        This is a generator, so the subscription is only established when
        the returned iterator is first advanced (same as subscribe_events()):
        frames received before that are not delivered. Close the client to
        end the subscription.

        Args:
            queue_size: per-subscriber backlog depth (0 selects the
                default of 16; values above 128 are capped at 128)
            drop_old: when the backlog is full, drop the oldest frame
                (keep newest) instead of dropping the newest (keep order)
        """
        if self.stub is None:
            self.connect()

        request = device_pb2.Rs485SubscribeRequest(
            queue_size=queue_size, drop_old=drop_old
        )
        for event_msg in self.stub.SubscribeRs485Rx(request):
            yield Rs485RxEvent(
                data=bytes(event_msg.data), timestamp_ns=event_msg.timestamp_ns
            )

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

        request = device_pb2.GotoRatioDistanceRequest(
            zoom_ratio=zoom_ratio, focus_distance_m=focus_distance_m
        )
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
            ir_led_on=bool(response.ir_led_level),
            mcu_version=response.mcu_version,
            mcu_uptime_ms=response.mcu_uptime_ms,
        )

    def subscribe_events(self) -> Iterator[DeviceEvent]:
        if self.stub is None:
            self.connect()

        for event_msg in self.stub.SubscribeEvents(device_pb2.Empty()):
            event = DeviceEvent(
                type=DeviceEvent.EventType(event_msg.type), timestamp_ns=event_msg.timestamp_ns
            )

            if event_msg.HasField("gpio_state"):
                event.gpio_pin = event_msg.gpio_state.pin
                event.gpio_value = event_msg.gpio_state.value

            if event_msg.HasField("light_sensor_value"):
                event.light_sensor_value = event_msg.light_sensor_value

            if event_msg.HasField("temperature"):
                event.temperature = event_msg.temperature

            yield event
