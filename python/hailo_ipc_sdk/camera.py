"""
Camera Control Client

Comprehensive camera pipeline control: ISP, encoder, RTSP, OSD,
stream management, profiles, capabilities, and hardware status.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

import grpc

from .config import Config
from .proto import camera_pb2, camera_pb2_grpc

logger = logging.getLogger("hailo_ipc_sdk.camera")


# -- Data classes --

@dataclass
class ISPConfig:
    brightness: int = -1       # [0..100], -1 = no change
    contrast: int = -1         # [0..100]
    saturation: int = -1       # [0..100]
    sharpness: int = -1        # [0..100]
    manual_mode: Optional[bool] = None
    auto_exposure: Optional[bool] = None
    backlight: int = -1        # [0..100]
    exposure_time_us: int = -1
    gain: int = -1
    noise_reduction: int = -1  # [0..100]
    wdr_value: int = -1        # [0..100]
    powerline_freq: int = -1   # 0=off, 1=50Hz, 2=60Hz
    awb_index: int = -1


@dataclass
class TransformConfig:
    rotation: int = 0   # 0/1/2/3 => 0/90/180/270
    flip: int = 0       # 0=none, 1=H, 2=V, 3=both
    dewarp: bool = False
    grayscale: bool = False


@dataclass
class EncoderReconfigResult:
    success: bool
    message: str
    interrupt_ms: int = 0


@dataclass
class StreamStatus:
    stream_id: str
    status: str
    has_encoder: bool
    codec: str
    width: int
    height: int
    fps: int
    bitrate_bps: int
    gop: int


@dataclass
class Capabilities:
    has_video: bool = False
    has_codec: bool = False
    has_led: bool = False
    has_sensor: bool = False
    has_mcu: bool = False
    has_env_ctrl: bool = False
    has_alarm: bool = False
    has_rs485: bool = False
    has_osd: bool = False
    has_draw: bool = False
    has_audio: bool = False


@dataclass
class SensorInfo:
    available: bool
    sensor_model: str
    i2c_bus: int
    i2c_address: str
    pixel_format: int


@dataclass
class HardwareStatus:
    light_sensor_mv: int
    light_sensor_lux: int
    mcu_temp_millic: int
    ain_mv: int
    mcu_version: str
    white_light_duty: int
    ir_led_duty: int
    ircut_mode: int  # 0=day, 1=night


@dataclass
class PipelineStreamConfig:
    stream_id: str
    input_width: int = 0
    input_height: int = 0
    input_framerate: int = 0
    codec: str = "h264"
    encoder_width: int = 0
    encoder_height: int = 0
    encoder_framerate: int = 0
    encoder_bitrate: int = 0
    encoder_gop: int = 0


@dataclass
class EnvStatus:
    enabled: bool


def _check_status(resp, label: str) -> None:
    """Check a Status-bearing response."""
    s = resp.status if hasattr(resp, "status") and hasattr(resp.status, "success") else resp
    if hasattr(s, "success") and not s.success:
        msg = s.message if hasattr(s, "message") else "unknown error"
        raise RuntimeError(f"{label} failed: {msg}")


class CameraClient:
    """
    Camera pipeline control client.

    Usage::

        cam = CameraClient()

        # ISP
        cam.set_isp(brightness=60, contrast=50)
        isp = cam.get_isp()

        # Encoder
        cam.set_encoder("main", bitrate_bps=8_000_000)

        # RTSP
        cam.set_rtsp_enabled(True)

        # Streams
        streams = cam.get_stream_status()
        cam.add_stream("third", 1920, 1080, 30, "h264", 4_000_000, 30)

        # Profiles
        cam.switch_profile("night")
        cam.backup_profile()

        # Capabilities
        caps = cam.get_capabilities()
    """

    def __init__(self, endpoint: Optional[str] = None):
        if endpoint is None:
            endpoint = Config.get_camera_control_endpoint()
        self.endpoint = endpoint
        self._channel: Optional[grpc.Channel] = None
        self._stub: Optional[camera_pb2_grpc.CameraControlStub] = None

    def _connect(self) -> camera_pb2_grpc.CameraControlStub:
        if self._stub is not None:
            return self._stub
        self._channel = grpc.insecure_channel(self.endpoint)
        self._stub = camera_pb2_grpc.CameraControlStub(self._channel)
        return self._stub

    def close(self) -> None:
        if self._channel is not None:
            self._channel.close()
            self._channel = None
            self._stub = None

    def __enter__(self):
        self._connect()
        return self

    def __exit__(self, *args):
        self.close()

    # -- ISP --

    def set_isp(self, config: Optional[ISPConfig] = None, **kwargs) -> None:
        """Update ISP image pipeline settings."""
        cfg = config or ISPConfig()
        for k, v in kwargs.items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)

        req = camera_pb2.ISPUpdateRequest()
        if cfg.brightness >= 0:
            req.brightness = cfg.brightness
        if cfg.contrast >= 0:
            req.contrast = cfg.contrast
        if cfg.saturation >= 0:
            req.saturation = cfg.saturation
        if cfg.sharpness >= 0:
            req.sharpness = cfg.sharpness
        if cfg.manual_mode is not None:
            req.manual_mode = cfg.manual_mode
        if cfg.auto_exposure is not None:
            req.auto_exposure = cfg.auto_exposure
        if cfg.backlight >= 0:
            req.backlight = cfg.backlight
        if cfg.exposure_time_us >= 0:
            req.exposure_time_us = cfg.exposure_time_us
        if cfg.gain >= 0:
            req.gain = cfg.gain
        if cfg.noise_reduction >= 0:
            req.noise_reduction = cfg.noise_reduction
        if cfg.wdr_value >= 0:
            req.wdr_value = cfg.wdr_value
        if cfg.powerline_freq >= 0:
            req.powerline_freq = cfg.powerline_freq
        if cfg.awb_index >= 0:
            req.awb_index = cfg.awb_index

        stub = self._connect()
        resp = stub.UpdateISPSettings(req)
        _check_status(resp, "UpdateISPSettings")

    def get_isp(self) -> ISPConfig:
        """Get current ISP configuration."""
        stub = self._connect()
        resp = stub.GetISPConfig(camera_pb2.Empty())
        if not resp.success:
            raise RuntimeError(f"GetISPConfig failed: {resp.message}")
        c = resp.current
        return ISPConfig(
            brightness=c.brightness,
            contrast=c.contrast,
            saturation=c.saturation,
            sharpness=c.sharpness,
            manual_mode=c.manual_mode if c.HasField("manual_mode") else None,
            auto_exposure=c.auto_exposure if c.HasField("auto_exposure") else None,
            backlight=c.backlight,
            exposure_time_us=c.exposure_time_us,
            gain=c.gain,
            noise_reduction=c.noise_reduction,
            wdr_value=c.wdr_value,
            powerline_freq=c.powerline_freq,
            awb_index=c.awb_index,
        )

    # -- Transform --

    def get_transform(self) -> TransformConfig:
        stub = self._connect()
        resp = stub.GetTransformConfig(camera_pb2.Empty())
        return TransformConfig(
            rotation=resp.rotation,
            flip=resp.flip,
            dewarp=resp.dewarp,
            grayscale=resp.grayscale,
        )

    def set_transform(self, cfg: TransformConfig) -> None:
        stub = self._connect()
        resp = stub.SetTransformConfig(camera_pb2.TransformConfig(
            rotation=cfg.rotation,
            flip=cfg.flip,
            dewarp=cfg.dewarp,
            grayscale=cfg.grayscale,
        ))
        _check_status(resp, "SetTransformConfig")

    # -- Encoder --

    def set_encoder(self, stream_name: str = "main", bitrate_bps: int = 0,
                    framerate: int = 0, gop: int = 0) -> None:
        """Dynamic encoder config (no restart)."""
        stub = self._connect()
        resp = stub.UpdateEncoderConfig(camera_pb2.EncoderConfigRequest(
            stream_name=stream_name,
            bitrate_bps=bitrate_bps,
            framerate=framerate,
            gop=gop,
        ))
        _check_status(resp, "UpdateEncoderConfig")

    def reconfigure_encoder(self, stream_name: str, width: int = 0, height: int = 0,
                            codec: str = "", bitrate_bps: int = 0,
                            fps: int = 0, gop: int = 0) -> EncoderReconfigResult:
        """Full encoder reconfiguration (brief restart, ~100ms)."""
        stub = self._connect()
        resp = stub.ReconfigureEncoder(camera_pb2.EncoderReconfigRequest(
            stream_name=stream_name,
            width=width, height=height,
            codec=codec,
            bitrate_bps=bitrate_bps,
            fps=fps, gop=gop,
        ))
        if not resp.success:
            raise RuntimeError(f"ReconfigureEncoder failed: {resp.message}")
        return EncoderReconfigResult(
            success=resp.success,
            message=resp.message,
            interrupt_ms=resp.interrupt_ms,
        )

    # -- RTSP --

    def set_rtsp_enabled(self, enabled: bool) -> None:
        stub = self._connect()
        resp = stub.SetRtspEnabled(camera_pb2.RtspEnabledRequest(enabled=enabled))
        _check_status(resp, "SetRtspEnabled")

    # -- OSD --

    def set_osd(self, streams: List[dict]) -> None:
        """Update OSD text and datetime overlays per stream.

        Args:
            streams: list of dicts with keys:
                stream_name, text_overlays (list of dicts), datetime_overlays (list of dicts)
        """
        req = camera_pb2.OsdConfigRequest()
        for s in streams:
            sc = req.streams.add()
            sc.stream_name = s.get("stream_name", "main")
            for t in s.get("text_overlays", []):
                tc = sc.text_overlays.add()
                for k, v in t.items():
                    setattr(tc, k, v)
            for d in s.get("datetime_overlays", []):
                dc = sc.datetime_overlays.add()
                for k, v in d.items():
                    setattr(dc, k, v)
        stub = self._connect()
        resp = stub.UpdateOsdConfig(req)
        _check_status(resp, "UpdateOsdConfig")

    # -- AI Overlay (convenience) --

    def set_ai_overlay(self, enabled: bool, show_label: bool = True,
                       show_confidence: bool = True, line_thickness: int = 2) -> None:
        stub = self._connect()
        resp = stub.UpdateAiOverlay(camera_pb2.AiOverlayConfig(
            enabled=enabled,
            show_label=show_label,
            show_confidence=show_confidence,
            line_thickness=line_thickness,
        ))
        _check_status(resp, "UpdateAiOverlay")

    # -- Stream management --

    def get_stream_status(self) -> List[StreamStatus]:
        stub = self._connect()
        resp = stub.GetStreamStatus(camera_pb2.GetStreamStatusRequest())
        return [
            StreamStatus(
                stream_id=s.stream_id,
                status=s.status,
                has_encoder=s.has_encoder,
                codec=s.codec,
                width=s.width,
                height=s.height,
                fps=s.fps,
                bitrate_bps=s.bitrate_bps,
                gop=s.gop,
            )
            for s in resp.streams
        ]

    def add_stream(self, stream_id: str, width: int, height: int, fps: int,
                   codec: str = "h264", bitrate: int = 4_000_000,
                   gop: int = 30) -> None:
        stub = self._connect()
        resp = stub.AddStream(camera_pb2.AddStreamRequest(
            stream_id=stream_id,
            width=width, height=height, fps=fps,
            codec=codec, bitrate=bitrate, gop=gop,
        ))
        if not resp.success:
            raise RuntimeError(f"AddStream failed: {resp.message}")

    def remove_stream(self, stream_name: str) -> None:
        stub = self._connect()
        resp = stub.RemoveStream(camera_pb2.RemoveStreamRequest(stream_name=stream_name))
        if not resp.success:
            raise RuntimeError(f"RemoveStream failed: {resp.message}")

    # -- Pipeline reconfiguration --

    def reconfigure_pipeline(self, streams: List[PipelineStreamConfig]) -> EncoderReconfigResult:
        req = camera_pb2.ReconfigurePipelineRequest()
        for s in streams:
            sc = req.streams.add()
            sc.stream_id = s.stream_id
            sc.input_width = s.input_width
            sc.input_height = s.input_height
            sc.input_framerate = s.input_framerate
            sc.codec = s.codec
            sc.encoder_width = s.encoder_width
            sc.encoder_height = s.encoder_height
            sc.encoder_framerate = s.encoder_framerate
            sc.encoder_bitrate = s.encoder_bitrate
            sc.encoder_gop = s.encoder_gop

        stub = self._connect()
        resp = stub.ReconfigurePipeline(req)
        if not resp.success:
            raise RuntimeError(f"ReconfigurePipeline failed: {resp.message}")
        return EncoderReconfigResult(
            success=resp.success,
            message=resp.message,
            interrupt_ms=resp.interrupt_ms,
        )

    # -- Profiles --

    def get_profile(self) -> str:
        stub = self._connect()
        resp = stub.GetProfile(camera_pb2.Empty())
        return resp.profile_name

    def list_profiles(self) -> tuple[list[str], str]:
        """Returns (profile_names, current_profile)."""
        stub = self._connect()
        resp = stub.ListProfiles(camera_pb2.Empty())
        return list(resp.profiles), resp.current_profile

    def switch_profile(self, name: str) -> EncoderReconfigResult:
        stub = self._connect()
        resp = stub.SwitchProfile(camera_pb2.SwitchProfileRequest(profile_name=name))
        if not resp.success:
            raise RuntimeError(f"SwitchProfile failed: {resp.message}")
        return EncoderReconfigResult(
            success=resp.success,
            message=resp.message,
            interrupt_ms=resp.interrupt_ms,
        )

    def backup_profile(self, path: str = "") -> None:
        stub = self._connect()
        resp = stub.BackupProfile(camera_pb2.BackupProfileRequest(path=path))
        if not resp.success:
            raise RuntimeError(f"BackupProfile failed: {resp.message}")

    # -- Sensor --

    def get_sensor_info(self, sensor_index: int = 0) -> SensorInfo:
        stub = self._connect()
        resp = stub.GetSensorInfo(camera_pb2.GetSensorInfoRequest(sensor_index=sensor_index))
        return SensorInfo(
            available=resp.available,
            sensor_model=resp.sensor_model,
            i2c_bus=resp.i2c_bus,
            i2c_address=resp.i2c_address,
            pixel_format=resp.pixel_format,
        )

    # -- Capabilities --

    def get_capabilities(self) -> Capabilities:
        stub = self._connect()
        resp = stub.GetCapabilities(camera_pb2.Empty())
        return Capabilities(
            has_video=resp.has_video,
            has_codec=resp.has_codec,
            has_led=resp.has_led,
            has_sensor=resp.has_sensor,
            has_mcu=resp.has_mcu,
            has_env_ctrl=resp.has_env_ctrl,
            has_alarm=resp.has_alarm,
            has_rs485=resp.has_rs485,
            has_osd=resp.has_osd,
            has_draw=resp.has_draw,
            has_audio=resp.has_audio,
        )

    # -- Hardware status --

    def get_hardware_status(self) -> HardwareStatus:
        stub = self._connect()
        resp = stub.GetDeviceHardwareStatus(camera_pb2.Empty())
        if not resp.success:
            raise RuntimeError(f"GetDeviceHardwareStatus failed: {resp.message}")
        return HardwareStatus(
            light_sensor_mv=resp.light_sensor_mv,
            light_sensor_lux=resp.light_sensor_lux,
            mcu_temp_millic=resp.mcu_temp_millic,
            ain_mv=resp.ain_mv,
            mcu_version=resp.mcu_version,
            white_light_duty=resp.white_light_duty,
            ir_led_duty=resp.ir_led_duty,
            ircut_mode=resp.ircut_mode,
        )

    # -- LED --

    def set_led_duty(self, led_id: int, duty_percent: int) -> None:
        stub = self._connect()
        resp = stub.SetLedDuty(camera_pb2.SetLedDutyRequest(
            led_id=led_id, duty_percent=duty_percent,
        ))
        if not resp.success:
            raise RuntimeError(f"SetLedDuty failed: {resp.message}")

    def get_led_duty(self, led_id: int) -> int:
        stub = self._connect()
        resp = stub.GetLedDuty(camera_pb2.GetLedDutyRequest(led_id=led_id))
        if not resp.success:
            raise RuntimeError(f"GetLedDuty failed: {resp.message}")
        return resp.duty_percent

    # -- IR-Cut --

    def set_ircut(self, mode: int) -> int:
        """Set IR-cut filter. mode: 0=day, 1=night. Returns current mode."""
        stub = self._connect()
        resp = stub.SetIrCut(camera_pb2.SetIrCutRequest(mode=mode))
        if not resp.success:
            raise RuntimeError(f"SetIrCut failed: {resp.message}")
        return resp.current_mode

    def get_ircut(self) -> int:
        stub = self._connect()
        resp = stub.GetIrCut(camera_pb2.Empty())
        return resp.current_mode

    # -- MCU raw --

    def mcu_raw_request(self, cmd: int, payload: bytes = b"") -> bytes:
        stub = self._connect()
        resp = stub.McuRawRequest(camera_pb2.McuRawRequestMessage(cmd=cmd, payload=payload))
        if not resp.success:
            raise RuntimeError(f"McuRawRequest failed: {resp.message}")
        return resp.payload

    # -- Environment control --

    def set_fan(self, enable: bool) -> bool:
        stub = self._connect()
        resp = stub.SetFan(camera_pb2.EnvCtrlRequest(enable=enable))
        if not resp.success:
            raise RuntimeError(f"SetFan failed: {resp.message}")
        return resp.enabled

    def get_fan(self) -> EnvStatus:
        stub = self._connect()
        resp = stub.GetFan(camera_pb2.Empty())
        return EnvStatus(enabled=resp.enabled)

    def set_heat(self, enable: bool) -> bool:
        stub = self._connect()
        resp = stub.SetHeat(camera_pb2.EnvCtrlRequest(enable=enable))
        if not resp.success:
            raise RuntimeError(f"SetHeat failed: {resp.message}")
        return resp.enabled

    def get_heat(self) -> EnvStatus:
        stub = self._connect()
        resp = stub.GetHeat(camera_pb2.Empty())
        return EnvStatus(enabled=resp.enabled)

    def set_radar(self, enable: bool) -> bool:
        stub = self._connect()
        resp = stub.SetRadar(camera_pb2.EnvCtrlRequest(enable=enable))
        if not resp.success:
            raise RuntimeError(f"SetRadar failed: {resp.message}")
        return resp.enabled

    def get_radar(self) -> EnvStatus:
        stub = self._connect()
        resp = stub.GetRadar(camera_pb2.Empty())
        return EnvStatus(enabled=resp.enabled)

    # -- Alarm I/O --

    def set_alarm_out(self, channel: int, enable: bool) -> bool:
        stub = self._connect()
        resp = stub.SetAlarmOut(camera_pb2.AlarmOutRequest(channel=channel, enable=enable))
        if not resp.success:
            raise RuntimeError(f"SetAlarmOut failed: {resp.message}")
        return resp.enabled

    def get_alarm_out(self, channel: int) -> bool:
        stub = self._connect()
        resp = stub.GetAlarmOut(camera_pb2.AlarmOutRequest(channel=channel))
        if not resp.success:
            raise RuntimeError(f"GetAlarmOut failed: {resp.message}")
        return resp.enabled

    def get_alarm_outputs(self) -> dict:
        stub = self._connect()
        resp = stub.GetAlarmOutputs(camera_pb2.Empty())
        if not resp.success:
            raise RuntimeError(f"GetAlarmOutputs failed: {resp.message}")
        return {
            "alarm_out0": resp.alarm_out0,
            "alarm_out1": resp.alarm_out1,
            "wiegand0": resp.wiegand0,
            "wiegand1": resp.wiegand1,
        }

    # -- RS485 --

    def rs485_init(self, baudrate: int = 9600, config: str = "8N1") -> None:
        stub = self._connect()
        resp = stub.Rs485Init(camera_pb2.Rs485InitRequest(baudrate=baudrate, config=config))
        _check_status(resp, "Rs485Init")

    def rs485_deinit(self) -> None:
        stub = self._connect()
        resp = stub.Rs485Deinit(camera_pb2.Empty())
        _check_status(resp, "Rs485Deinit")

    def rs485_tx(self, data: bytes) -> None:
        stub = self._connect()
        resp = stub.Rs485Tx(camera_pb2.Rs485TxRequest(data=data))
        _check_status(resp, "Rs485Tx")
