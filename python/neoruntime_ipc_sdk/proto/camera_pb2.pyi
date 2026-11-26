from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ConfigFieldType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CONFIG_FIELD_BOOL: _ClassVar[ConfigFieldType]
    CONFIG_FIELD_INT32: _ClassVar[ConfigFieldType]
    CONFIG_FIELD_UINT32: _ClassVar[ConfigFieldType]
    CONFIG_FIELD_FLOAT64: _ClassVar[ConfigFieldType]
    CONFIG_FIELD_STRING: _ClassVar[ConfigFieldType]

class DspOp(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DSP_OP_RESIZE: _ClassVar[DspOp]
    DSP_OP_CROP_AND_RESIZE: _ClassVar[DspOp]
    DSP_OP_MULTI_CROP_AND_RESIZE: _ClassVar[DspOp]
    DSP_OP_CONVERT_FORMAT: _ClassVar[DspOp]
    DSP_OP_BLEND: _ClassVar[DspOp]

class DspInterpolation(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DSP_INTERP_NEAREST: _ClassVar[DspInterpolation]
    DSP_INTERP_BILINEAR: _ClassVar[DspInterpolation]
    DSP_INTERP_AREA: _ClassVar[DspInterpolation]
    DSP_INTERP_BICUBIC: _ClassVar[DspInterpolation]

class DspScalingMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DSP_SCALING_STRETCH: _ClassVar[DspScalingMode]
    DSP_SCALING_LETTERBOX_MIDDLE: _ClassVar[DspScalingMode]
    DSP_SCALING_LETTERBOX_UP_LEFT: _ClassVar[DspScalingMode]
    DSP_SCALING_SCALE_AND_CROP: _ClassVar[DspScalingMode]

class DspPriority(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DSP_PRIORITY_BACKGROUND: _ClassVar[DspPriority]
    DSP_PRIORITY_NORMAL: _ClassVar[DspPriority]

class InjectionMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    INJECT_REPLACE: _ClassVar[InjectionMode]
    INJECT_OVERLAY: _ClassVar[InjectionMode]
CONFIG_FIELD_BOOL: ConfigFieldType
CONFIG_FIELD_INT32: ConfigFieldType
CONFIG_FIELD_UINT32: ConfigFieldType
CONFIG_FIELD_FLOAT64: ConfigFieldType
CONFIG_FIELD_STRING: ConfigFieldType
DSP_OP_RESIZE: DspOp
DSP_OP_CROP_AND_RESIZE: DspOp
DSP_OP_MULTI_CROP_AND_RESIZE: DspOp
DSP_OP_CONVERT_FORMAT: DspOp
DSP_OP_BLEND: DspOp
DSP_INTERP_NEAREST: DspInterpolation
DSP_INTERP_BILINEAR: DspInterpolation
DSP_INTERP_AREA: DspInterpolation
DSP_INTERP_BICUBIC: DspInterpolation
DSP_SCALING_STRETCH: DspScalingMode
DSP_SCALING_LETTERBOX_MIDDLE: DspScalingMode
DSP_SCALING_LETTERBOX_UP_LEFT: DspScalingMode
DSP_SCALING_SCALE_AND_CROP: DspScalingMode
DSP_PRIORITY_BACKGROUND: DspPriority
DSP_PRIORITY_NORMAL: DspPriority
INJECT_REPLACE: InjectionMode
INJECT_OVERLAY: InjectionMode

class Empty(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Status(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...

class HalError(_message.Message):
    __slots__ = ("code", "name", "description")
    CODE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    code: int
    name: str
    description: str
    def __init__(self, code: _Optional[int] = ..., name: _Optional[str] = ..., description: _Optional[str] = ...) -> None: ...

class ISPUpdateRequest(_message.Message):
    __slots__ = ("manual_mode", "brightness", "contrast", "saturation", "sharpness", "auto_exposure", "backlight", "exposure_time_us", "gain", "noise_reduction", "wdr_value", "powerline_freq", "awb_index")
    MANUAL_MODE_FIELD_NUMBER: _ClassVar[int]
    BRIGHTNESS_FIELD_NUMBER: _ClassVar[int]
    CONTRAST_FIELD_NUMBER: _ClassVar[int]
    SATURATION_FIELD_NUMBER: _ClassVar[int]
    SHARPNESS_FIELD_NUMBER: _ClassVar[int]
    AUTO_EXPOSURE_FIELD_NUMBER: _ClassVar[int]
    BACKLIGHT_FIELD_NUMBER: _ClassVar[int]
    EXPOSURE_TIME_US_FIELD_NUMBER: _ClassVar[int]
    GAIN_FIELD_NUMBER: _ClassVar[int]
    NOISE_REDUCTION_FIELD_NUMBER: _ClassVar[int]
    WDR_VALUE_FIELD_NUMBER: _ClassVar[int]
    POWERLINE_FREQ_FIELD_NUMBER: _ClassVar[int]
    AWB_INDEX_FIELD_NUMBER: _ClassVar[int]
    manual_mode: bool
    brightness: int
    contrast: int
    saturation: int
    sharpness: int
    auto_exposure: bool
    backlight: int
    exposure_time_us: int
    gain: int
    noise_reduction: int
    wdr_value: int
    powerline_freq: int
    awb_index: int
    def __init__(self, manual_mode: bool = ..., brightness: _Optional[int] = ..., contrast: _Optional[int] = ..., saturation: _Optional[int] = ..., sharpness: _Optional[int] = ..., auto_exposure: bool = ..., backlight: _Optional[int] = ..., exposure_time_us: _Optional[int] = ..., gain: _Optional[int] = ..., noise_reduction: _Optional[int] = ..., wdr_value: _Optional[int] = ..., powerline_freq: _Optional[int] = ..., awb_index: _Optional[int] = ...) -> None: ...

class ISPUpdateResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: Status
    def __init__(self, status: _Optional[_Union[Status, _Mapping]] = ...) -> None: ...

class ISPConfigResponse(_message.Message):
    __slots__ = ("success", "message", "current")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    CURRENT_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    current: ISPUpdateRequest
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., current: _Optional[_Union[ISPUpdateRequest, _Mapping]] = ...) -> None: ...

class TransformConfig(_message.Message):
    __slots__ = ("rotation", "flip", "dewarp", "grayscale", "dis", "eis")
    ROTATION_FIELD_NUMBER: _ClassVar[int]
    FLIP_FIELD_NUMBER: _ClassVar[int]
    DEWARP_FIELD_NUMBER: _ClassVar[int]
    GRAYSCALE_FIELD_NUMBER: _ClassVar[int]
    DIS_FIELD_NUMBER: _ClassVar[int]
    EIS_FIELD_NUMBER: _ClassVar[int]
    rotation: int
    flip: int
    dewarp: bool
    grayscale: bool
    dis: bool
    eis: bool
    def __init__(self, rotation: _Optional[int] = ..., flip: _Optional[int] = ..., dewarp: bool = ..., grayscale: bool = ..., dis: bool = ..., eis: bool = ...) -> None: ...

class EncoderConfigRequest(_message.Message):
    __slots__ = ("stream_name", "bitrate_bps", "framerate", "gop")
    STREAM_NAME_FIELD_NUMBER: _ClassVar[int]
    BITRATE_BPS_FIELD_NUMBER: _ClassVar[int]
    FRAMERATE_FIELD_NUMBER: _ClassVar[int]
    GOP_FIELD_NUMBER: _ClassVar[int]
    stream_name: str
    bitrate_bps: int
    framerate: int
    gop: int
    def __init__(self, stream_name: _Optional[str] = ..., bitrate_bps: _Optional[int] = ..., framerate: _Optional[int] = ..., gop: _Optional[int] = ...) -> None: ...

class RtspEnabledRequest(_message.Message):
    __slots__ = ("enabled",)
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    enabled: bool
    def __init__(self, enabled: bool = ...) -> None: ...

class AiOverlayConfig(_message.Message):
    __slots__ = ("enabled", "box_color", "label_color", "font_size", "line_thickness", "show_confidence", "show_label", "enable_face_blur", "strict_frame_lock", "strict_wait_cap_ms")
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    BOX_COLOR_FIELD_NUMBER: _ClassVar[int]
    LABEL_COLOR_FIELD_NUMBER: _ClassVar[int]
    FONT_SIZE_FIELD_NUMBER: _ClassVar[int]
    LINE_THICKNESS_FIELD_NUMBER: _ClassVar[int]
    SHOW_CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    SHOW_LABEL_FIELD_NUMBER: _ClassVar[int]
    ENABLE_FACE_BLUR_FIELD_NUMBER: _ClassVar[int]
    STRICT_FRAME_LOCK_FIELD_NUMBER: _ClassVar[int]
    STRICT_WAIT_CAP_MS_FIELD_NUMBER: _ClassVar[int]
    enabled: bool
    box_color: int
    label_color: int
    font_size: int
    line_thickness: int
    show_confidence: bool
    show_label: bool
    enable_face_blur: bool
    strict_frame_lock: bool
    strict_wait_cap_ms: int
    def __init__(self, enabled: bool = ..., box_color: _Optional[int] = ..., label_color: _Optional[int] = ..., font_size: _Optional[int] = ..., line_thickness: _Optional[int] = ..., show_confidence: bool = ..., show_label: bool = ..., enable_face_blur: bool = ..., strict_frame_lock: bool = ..., strict_wait_cap_ms: _Optional[int] = ...) -> None: ...

class OsdTextOverlayConfig(_message.Message):
    __slots__ = ("id", "text", "x", "y", "font_size", "text_color", "enabled", "h_align", "v_align")
    ID_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    FONT_SIZE_FIELD_NUMBER: _ClassVar[int]
    TEXT_COLOR_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    H_ALIGN_FIELD_NUMBER: _ClassVar[int]
    V_ALIGN_FIELD_NUMBER: _ClassVar[int]
    id: str
    text: str
    x: float
    y: float
    font_size: float
    text_color: int
    enabled: bool
    h_align: int
    v_align: int
    def __init__(self, id: _Optional[str] = ..., text: _Optional[str] = ..., x: _Optional[float] = ..., y: _Optional[float] = ..., font_size: _Optional[float] = ..., text_color: _Optional[int] = ..., enabled: bool = ..., h_align: _Optional[int] = ..., v_align: _Optional[int] = ...) -> None: ...

class OsdDateTimeOverlayConfig(_message.Message):
    __slots__ = ("id", "x", "y", "format", "font_size", "text_color", "enabled", "h_align", "v_align")
    ID_FIELD_NUMBER: _ClassVar[int]
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    FONT_SIZE_FIELD_NUMBER: _ClassVar[int]
    TEXT_COLOR_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    H_ALIGN_FIELD_NUMBER: _ClassVar[int]
    V_ALIGN_FIELD_NUMBER: _ClassVar[int]
    id: str
    x: float
    y: float
    format: str
    font_size: float
    text_color: int
    enabled: bool
    h_align: int
    v_align: int
    def __init__(self, id: _Optional[str] = ..., x: _Optional[float] = ..., y: _Optional[float] = ..., format: _Optional[str] = ..., font_size: _Optional[float] = ..., text_color: _Optional[int] = ..., enabled: bool = ..., h_align: _Optional[int] = ..., v_align: _Optional[int] = ...) -> None: ...

class OsdImageOverlayConfig(_message.Message):
    __slots__ = ("id", "image_path", "x", "y", "width", "height", "enabled", "h_align", "v_align")
    ID_FIELD_NUMBER: _ClassVar[int]
    IMAGE_PATH_FIELD_NUMBER: _ClassVar[int]
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    H_ALIGN_FIELD_NUMBER: _ClassVar[int]
    V_ALIGN_FIELD_NUMBER: _ClassVar[int]
    id: str
    image_path: str
    x: float
    y: float
    width: float
    height: float
    enabled: bool
    h_align: int
    v_align: int
    def __init__(self, id: _Optional[str] = ..., image_path: _Optional[str] = ..., x: _Optional[float] = ..., y: _Optional[float] = ..., width: _Optional[float] = ..., height: _Optional[float] = ..., enabled: bool = ..., h_align: _Optional[int] = ..., v_align: _Optional[int] = ...) -> None: ...

class StreamOsdConfig(_message.Message):
    __slots__ = ("stream_name", "text_overlays", "datetime_overlays", "image_overlays")
    STREAM_NAME_FIELD_NUMBER: _ClassVar[int]
    TEXT_OVERLAYS_FIELD_NUMBER: _ClassVar[int]
    DATETIME_OVERLAYS_FIELD_NUMBER: _ClassVar[int]
    IMAGE_OVERLAYS_FIELD_NUMBER: _ClassVar[int]
    stream_name: str
    text_overlays: _containers.RepeatedCompositeFieldContainer[OsdTextOverlayConfig]
    datetime_overlays: _containers.RepeatedCompositeFieldContainer[OsdDateTimeOverlayConfig]
    image_overlays: _containers.RepeatedCompositeFieldContainer[OsdImageOverlayConfig]
    def __init__(self, stream_name: _Optional[str] = ..., text_overlays: _Optional[_Iterable[_Union[OsdTextOverlayConfig, _Mapping]]] = ..., datetime_overlays: _Optional[_Iterable[_Union[OsdDateTimeOverlayConfig, _Mapping]]] = ..., image_overlays: _Optional[_Iterable[_Union[OsdImageOverlayConfig, _Mapping]]] = ...) -> None: ...

class OsdConfigRequest(_message.Message):
    __slots__ = ("streams", "suppress_bake")
    STREAMS_FIELD_NUMBER: _ClassVar[int]
    SUPPRESS_BAKE_FIELD_NUMBER: _ClassVar[int]
    streams: _containers.RepeatedCompositeFieldContainer[StreamOsdConfig]
    suppress_bake: bool
    def __init__(self, streams: _Optional[_Iterable[_Union[StreamOsdConfig, _Mapping]]] = ..., suppress_bake: bool = ...) -> None: ...

class OsdConfigResponse(_message.Message):
    __slots__ = ("streams",)
    STREAMS_FIELD_NUMBER: _ClassVar[int]
    streams: _containers.RepeatedCompositeFieldContainer[StreamOsdConfig]
    def __init__(self, streams: _Optional[_Iterable[_Union[StreamOsdConfig, _Mapping]]] = ...) -> None: ...

class EncoderReconfigRequest(_message.Message):
    __slots__ = ("stream_name", "width", "height", "codec", "bitrate_bps", "fps", "gop")
    STREAM_NAME_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    CODEC_FIELD_NUMBER: _ClassVar[int]
    BITRATE_BPS_FIELD_NUMBER: _ClassVar[int]
    FPS_FIELD_NUMBER: _ClassVar[int]
    GOP_FIELD_NUMBER: _ClassVar[int]
    stream_name: str
    width: int
    height: int
    codec: str
    bitrate_bps: int
    fps: int
    gop: int
    def __init__(self, stream_name: _Optional[str] = ..., width: _Optional[int] = ..., height: _Optional[int] = ..., codec: _Optional[str] = ..., bitrate_bps: _Optional[int] = ..., fps: _Optional[int] = ..., gop: _Optional[int] = ...) -> None: ...

class EncoderReconfigResponse(_message.Message):
    __slots__ = ("success", "message", "interrupt_ms", "hal_error")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    INTERRUPT_MS_FIELD_NUMBER: _ClassVar[int]
    HAL_ERROR_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    interrupt_ms: int
    hal_error: HalError
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., interrupt_ms: _Optional[int] = ..., hal_error: _Optional[_Union[HalError, _Mapping]] = ...) -> None: ...

class GetProfileResponse(_message.Message):
    __slots__ = ("profile_name",)
    PROFILE_NAME_FIELD_NUMBER: _ClassVar[int]
    profile_name: str
    def __init__(self, profile_name: _Optional[str] = ...) -> None: ...

class ListProfilesResponse(_message.Message):
    __slots__ = ("profiles", "current_profile")
    PROFILES_FIELD_NUMBER: _ClassVar[int]
    CURRENT_PROFILE_FIELD_NUMBER: _ClassVar[int]
    profiles: _containers.RepeatedScalarFieldContainer[str]
    current_profile: str
    def __init__(self, profiles: _Optional[_Iterable[str]] = ..., current_profile: _Optional[str] = ...) -> None: ...

class SwitchProfileRequest(_message.Message):
    __slots__ = ("profile_name",)
    PROFILE_NAME_FIELD_NUMBER: _ClassVar[int]
    profile_name: str
    def __init__(self, profile_name: _Optional[str] = ...) -> None: ...

class BackupProfileRequest(_message.Message):
    __slots__ = ("path",)
    PATH_FIELD_NUMBER: _ClassVar[int]
    path: str
    def __init__(self, path: _Optional[str] = ...) -> None: ...

class BackupProfileResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...

class PipelineStreamConfig(_message.Message):
    __slots__ = ("stream_id", "input_width", "input_height", "input_framerate", "codec", "encoder_width", "encoder_height", "encoder_framerate", "encoder_bitrate", "encoder_gop")
    STREAM_ID_FIELD_NUMBER: _ClassVar[int]
    INPUT_WIDTH_FIELD_NUMBER: _ClassVar[int]
    INPUT_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    INPUT_FRAMERATE_FIELD_NUMBER: _ClassVar[int]
    CODEC_FIELD_NUMBER: _ClassVar[int]
    ENCODER_WIDTH_FIELD_NUMBER: _ClassVar[int]
    ENCODER_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    ENCODER_FRAMERATE_FIELD_NUMBER: _ClassVar[int]
    ENCODER_BITRATE_FIELD_NUMBER: _ClassVar[int]
    ENCODER_GOP_FIELD_NUMBER: _ClassVar[int]
    stream_id: str
    input_width: int
    input_height: int
    input_framerate: int
    codec: str
    encoder_width: int
    encoder_height: int
    encoder_framerate: int
    encoder_bitrate: int
    encoder_gop: int
    def __init__(self, stream_id: _Optional[str] = ..., input_width: _Optional[int] = ..., input_height: _Optional[int] = ..., input_framerate: _Optional[int] = ..., codec: _Optional[str] = ..., encoder_width: _Optional[int] = ..., encoder_height: _Optional[int] = ..., encoder_framerate: _Optional[int] = ..., encoder_bitrate: _Optional[int] = ..., encoder_gop: _Optional[int] = ...) -> None: ...

class ReconfigurePipelineRequest(_message.Message):
    __slots__ = ("streams",)
    STREAMS_FIELD_NUMBER: _ClassVar[int]
    streams: _containers.RepeatedCompositeFieldContainer[PipelineStreamConfig]
    def __init__(self, streams: _Optional[_Iterable[_Union[PipelineStreamConfig, _Mapping]]] = ...) -> None: ...

class ReconfigurePipelineResponse(_message.Message):
    __slots__ = ("success", "message", "interrupt_ms", "hal_error", "applied_streams")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    INTERRUPT_MS_FIELD_NUMBER: _ClassVar[int]
    HAL_ERROR_FIELD_NUMBER: _ClassVar[int]
    APPLIED_STREAMS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    interrupt_ms: int
    hal_error: HalError
    applied_streams: _containers.RepeatedCompositeFieldContainer[PipelineStreamConfig]
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., interrupt_ms: _Optional[int] = ..., hal_error: _Optional[_Union[HalError, _Mapping]] = ..., applied_streams: _Optional[_Iterable[_Union[PipelineStreamConfig, _Mapping]]] = ...) -> None: ...

class GetSensorInfoRequest(_message.Message):
    __slots__ = ("sensor_index",)
    SENSOR_INDEX_FIELD_NUMBER: _ClassVar[int]
    sensor_index: int
    def __init__(self, sensor_index: _Optional[int] = ...) -> None: ...

class SensorInfoResponse(_message.Message):
    __slots__ = ("available", "sensor_model", "i2c_bus", "i2c_address", "pixel_format")
    AVAILABLE_FIELD_NUMBER: _ClassVar[int]
    SENSOR_MODEL_FIELD_NUMBER: _ClassVar[int]
    I2C_BUS_FIELD_NUMBER: _ClassVar[int]
    I2C_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    PIXEL_FORMAT_FIELD_NUMBER: _ClassVar[int]
    available: bool
    sensor_model: str
    i2c_bus: int
    i2c_address: str
    pixel_format: int
    def __init__(self, available: bool = ..., sensor_model: _Optional[str] = ..., i2c_bus: _Optional[int] = ..., i2c_address: _Optional[str] = ..., pixel_format: _Optional[int] = ...) -> None: ...

class GetStreamStatusRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class StreamStatusInfo(_message.Message):
    __slots__ = ("stream_id", "status", "has_encoder", "codec", "width", "height", "fps", "bitrate_bps", "gop", "ms_since_last_frame", "measured_fps", "status_detail", "packets_published", "queue_overflow_drops", "client_send_drops", "client_send_failures", "client_disconnects", "last_packet_seq", "publisher_clients", "bake_skips", "strict_locked", "strict_degraded", "strict_skips", "stream_epoch", "overlay_layer_count", "overlay_late_commands", "overlay_epoch_rejects", "overlay_no_binding_drops")
    STREAM_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    HAS_ENCODER_FIELD_NUMBER: _ClassVar[int]
    CODEC_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    FPS_FIELD_NUMBER: _ClassVar[int]
    BITRATE_BPS_FIELD_NUMBER: _ClassVar[int]
    GOP_FIELD_NUMBER: _ClassVar[int]
    MS_SINCE_LAST_FRAME_FIELD_NUMBER: _ClassVar[int]
    MEASURED_FPS_FIELD_NUMBER: _ClassVar[int]
    STATUS_DETAIL_FIELD_NUMBER: _ClassVar[int]
    PACKETS_PUBLISHED_FIELD_NUMBER: _ClassVar[int]
    QUEUE_OVERFLOW_DROPS_FIELD_NUMBER: _ClassVar[int]
    CLIENT_SEND_DROPS_FIELD_NUMBER: _ClassVar[int]
    CLIENT_SEND_FAILURES_FIELD_NUMBER: _ClassVar[int]
    CLIENT_DISCONNECTS_FIELD_NUMBER: _ClassVar[int]
    LAST_PACKET_SEQ_FIELD_NUMBER: _ClassVar[int]
    PUBLISHER_CLIENTS_FIELD_NUMBER: _ClassVar[int]
    BAKE_SKIPS_FIELD_NUMBER: _ClassVar[int]
    STRICT_LOCKED_FIELD_NUMBER: _ClassVar[int]
    STRICT_DEGRADED_FIELD_NUMBER: _ClassVar[int]
    STRICT_SKIPS_FIELD_NUMBER: _ClassVar[int]
    STREAM_EPOCH_FIELD_NUMBER: _ClassVar[int]
    OVERLAY_LAYER_COUNT_FIELD_NUMBER: _ClassVar[int]
    OVERLAY_LATE_COMMANDS_FIELD_NUMBER: _ClassVar[int]
    OVERLAY_EPOCH_REJECTS_FIELD_NUMBER: _ClassVar[int]
    OVERLAY_NO_BINDING_DROPS_FIELD_NUMBER: _ClassVar[int]
    stream_id: str
    status: str
    has_encoder: bool
    codec: str
    width: int
    height: int
    fps: int
    bitrate_bps: int
    gop: int
    ms_since_last_frame: int
    measured_fps: int
    status_detail: str
    packets_published: int
    queue_overflow_drops: int
    client_send_drops: int
    client_send_failures: int
    client_disconnects: int
    last_packet_seq: int
    publisher_clients: int
    bake_skips: int
    strict_locked: int
    strict_degraded: int
    strict_skips: int
    stream_epoch: int
    overlay_layer_count: int
    overlay_late_commands: int
    overlay_epoch_rejects: int
    overlay_no_binding_drops: int
    def __init__(self, stream_id: _Optional[str] = ..., status: _Optional[str] = ..., has_encoder: bool = ..., codec: _Optional[str] = ..., width: _Optional[int] = ..., height: _Optional[int] = ..., fps: _Optional[int] = ..., bitrate_bps: _Optional[int] = ..., gop: _Optional[int] = ..., ms_since_last_frame: _Optional[int] = ..., measured_fps: _Optional[int] = ..., status_detail: _Optional[str] = ..., packets_published: _Optional[int] = ..., queue_overflow_drops: _Optional[int] = ..., client_send_drops: _Optional[int] = ..., client_send_failures: _Optional[int] = ..., client_disconnects: _Optional[int] = ..., last_packet_seq: _Optional[int] = ..., publisher_clients: _Optional[int] = ..., bake_skips: _Optional[int] = ..., strict_locked: _Optional[int] = ..., strict_degraded: _Optional[int] = ..., strict_skips: _Optional[int] = ..., stream_epoch: _Optional[int] = ..., overlay_layer_count: _Optional[int] = ..., overlay_late_commands: _Optional[int] = ..., overlay_epoch_rejects: _Optional[int] = ..., overlay_no_binding_drops: _Optional[int] = ...) -> None: ...

class GetStreamStatusResponse(_message.Message):
    __slots__ = ("streams",)
    STREAMS_FIELD_NUMBER: _ClassVar[int]
    streams: _containers.RepeatedCompositeFieldContainer[StreamStatusInfo]
    def __init__(self, streams: _Optional[_Iterable[_Union[StreamStatusInfo, _Mapping]]] = ...) -> None: ...

class AddStreamRequest(_message.Message):
    __slots__ = ("stream_id", "width", "height", "fps", "codec", "bitrate", "gop")
    STREAM_ID_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    FPS_FIELD_NUMBER: _ClassVar[int]
    CODEC_FIELD_NUMBER: _ClassVar[int]
    BITRATE_FIELD_NUMBER: _ClassVar[int]
    GOP_FIELD_NUMBER: _ClassVar[int]
    stream_id: str
    width: int
    height: int
    fps: int
    codec: str
    bitrate: int
    gop: int
    def __init__(self, stream_id: _Optional[str] = ..., width: _Optional[int] = ..., height: _Optional[int] = ..., fps: _Optional[int] = ..., codec: _Optional[str] = ..., bitrate: _Optional[int] = ..., gop: _Optional[int] = ...) -> None: ...

class RemoveStreamRequest(_message.Message):
    __slots__ = ("stream_name",)
    STREAM_NAME_FIELD_NUMBER: _ClassVar[int]
    stream_name: str
    def __init__(self, stream_name: _Optional[str] = ...) -> None: ...

class StreamOperationResponse(_message.Message):
    __slots__ = ("success", "message", "hal_error")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    HAL_ERROR_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    hal_error: HalError
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., hal_error: _Optional[_Union[HalError, _Mapping]] = ...) -> None: ...

class SetIrCutRequest(_message.Message):
    __slots__ = ("mode",)
    MODE_FIELD_NUMBER: _ClassVar[int]
    mode: int
    def __init__(self, mode: _Optional[int] = ...) -> None: ...

class SetIrCutResponse(_message.Message):
    __slots__ = ("success", "message", "current_mode")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    CURRENT_MODE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    current_mode: int
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., current_mode: _Optional[int] = ...) -> None: ...

class SetLedDutyRequest(_message.Message):
    __slots__ = ("led_id", "duty_percent")
    LED_ID_FIELD_NUMBER: _ClassVar[int]
    DUTY_PERCENT_FIELD_NUMBER: _ClassVar[int]
    led_id: int
    duty_percent: int
    def __init__(self, led_id: _Optional[int] = ..., duty_percent: _Optional[int] = ...) -> None: ...

class GetLedDutyRequest(_message.Message):
    __slots__ = ("led_id",)
    LED_ID_FIELD_NUMBER: _ClassVar[int]
    led_id: int
    def __init__(self, led_id: _Optional[int] = ...) -> None: ...

class LedStatus(_message.Message):
    __slots__ = ("success", "message", "duty_percent")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    DUTY_PERCENT_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    duty_percent: int
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., duty_percent: _Optional[int] = ...) -> None: ...

class ImagingModeRequest(_message.Message):
    __slots__ = ("mode",)
    MODE_FIELD_NUMBER: _ClassVar[int]
    mode: str
    def __init__(self, mode: _Optional[str] = ...) -> None: ...

class InfraredSettingsRequest(_message.Message):
    __slots__ = ("auto_follow", "near_pwm", "far_pwm", "night_enter", "day_enter")
    AUTO_FOLLOW_FIELD_NUMBER: _ClassVar[int]
    NEAR_PWM_FIELD_NUMBER: _ClassVar[int]
    FAR_PWM_FIELD_NUMBER: _ClassVar[int]
    NIGHT_ENTER_FIELD_NUMBER: _ClassVar[int]
    DAY_ENTER_FIELD_NUMBER: _ClassVar[int]
    auto_follow: bool
    near_pwm: int
    far_pwm: int
    night_enter: int
    day_enter: int
    def __init__(self, auto_follow: bool = ..., near_pwm: _Optional[int] = ..., far_pwm: _Optional[int] = ..., night_enter: _Optional[int] = ..., day_enter: _Optional[int] = ...) -> None: ...

class InfraredStatusResponse(_message.Message):
    __slots__ = ("success", "message", "mode", "transition", "output_source", "auto_follow", "follow_active", "manual_override", "degraded", "requested_near_pwm", "requested_far_pwm", "applied_near_pwm", "applied_far_pwm", "zoom_ratio", "active_profile", "selected_mode", "light_percent", "light_mv", "light_milli", "light_valid", "night_enter", "day_enter")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    TRANSITION_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_SOURCE_FIELD_NUMBER: _ClassVar[int]
    AUTO_FOLLOW_FIELD_NUMBER: _ClassVar[int]
    FOLLOW_ACTIVE_FIELD_NUMBER: _ClassVar[int]
    MANUAL_OVERRIDE_FIELD_NUMBER: _ClassVar[int]
    DEGRADED_FIELD_NUMBER: _ClassVar[int]
    REQUESTED_NEAR_PWM_FIELD_NUMBER: _ClassVar[int]
    REQUESTED_FAR_PWM_FIELD_NUMBER: _ClassVar[int]
    APPLIED_NEAR_PWM_FIELD_NUMBER: _ClassVar[int]
    APPLIED_FAR_PWM_FIELD_NUMBER: _ClassVar[int]
    ZOOM_RATIO_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_PROFILE_FIELD_NUMBER: _ClassVar[int]
    SELECTED_MODE_FIELD_NUMBER: _ClassVar[int]
    LIGHT_PERCENT_FIELD_NUMBER: _ClassVar[int]
    LIGHT_MV_FIELD_NUMBER: _ClassVar[int]
    LIGHT_MILLI_FIELD_NUMBER: _ClassVar[int]
    LIGHT_VALID_FIELD_NUMBER: _ClassVar[int]
    NIGHT_ENTER_FIELD_NUMBER: _ClassVar[int]
    DAY_ENTER_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    mode: str
    transition: str
    output_source: str
    auto_follow: bool
    follow_active: bool
    manual_override: bool
    degraded: bool
    requested_near_pwm: int
    requested_far_pwm: int
    applied_near_pwm: int
    applied_far_pwm: int
    zoom_ratio: float
    active_profile: str
    selected_mode: str
    light_percent: int
    light_mv: int
    light_milli: int
    light_valid: bool
    night_enter: int
    day_enter: int
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., mode: _Optional[str] = ..., transition: _Optional[str] = ..., output_source: _Optional[str] = ..., auto_follow: bool = ..., follow_active: bool = ..., manual_override: bool = ..., degraded: bool = ..., requested_near_pwm: _Optional[int] = ..., requested_far_pwm: _Optional[int] = ..., applied_near_pwm: _Optional[int] = ..., applied_far_pwm: _Optional[int] = ..., zoom_ratio: _Optional[float] = ..., active_profile: _Optional[str] = ..., selected_mode: _Optional[str] = ..., light_percent: _Optional[int] = ..., light_mv: _Optional[int] = ..., light_milli: _Optional[int] = ..., light_valid: bool = ..., night_enter: _Optional[int] = ..., day_enter: _Optional[int] = ...) -> None: ...

class IrPreset(_message.Message):
    __slots__ = ("name", "zoom_ratio", "near_pwm", "far_pwm")
    NAME_FIELD_NUMBER: _ClassVar[int]
    ZOOM_RATIO_FIELD_NUMBER: _ClassVar[int]
    NEAR_PWM_FIELD_NUMBER: _ClassVar[int]
    FAR_PWM_FIELD_NUMBER: _ClassVar[int]
    name: str
    zoom_ratio: float
    near_pwm: int
    far_pwm: int
    def __init__(self, name: _Optional[str] = ..., zoom_ratio: _Optional[float] = ..., near_pwm: _Optional[int] = ..., far_pwm: _Optional[int] = ...) -> None: ...

class IrPresetListResponse(_message.Message):
    __slots__ = ("success", "message", "presets")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    PRESETS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    presets: _containers.RepeatedCompositeFieldContainer[IrPreset]
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., presets: _Optional[_Iterable[_Union[IrPreset, _Mapping]]] = ...) -> None: ...

class DeleteIrPresetRequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class DeviceHardwareStatus(_message.Message):
    __slots__ = ("success", "message", "light_sensor_mv", "light_sensor_lux", "mcu_temp_millic", "ain_mv", "mcu_version", "white_light_duty", "ir_led_duty", "ircut_mode")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    LIGHT_SENSOR_MV_FIELD_NUMBER: _ClassVar[int]
    LIGHT_SENSOR_LUX_FIELD_NUMBER: _ClassVar[int]
    MCU_TEMP_MILLIC_FIELD_NUMBER: _ClassVar[int]
    AIN_MV_FIELD_NUMBER: _ClassVar[int]
    MCU_VERSION_FIELD_NUMBER: _ClassVar[int]
    WHITE_LIGHT_DUTY_FIELD_NUMBER: _ClassVar[int]
    IR_LED_DUTY_FIELD_NUMBER: _ClassVar[int]
    IRCUT_MODE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    light_sensor_mv: int
    light_sensor_lux: int
    mcu_temp_millic: int
    ain_mv: int
    mcu_version: str
    white_light_duty: int
    ir_led_duty: int
    ircut_mode: int
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., light_sensor_mv: _Optional[int] = ..., light_sensor_lux: _Optional[int] = ..., mcu_temp_millic: _Optional[int] = ..., ain_mv: _Optional[int] = ..., mcu_version: _Optional[str] = ..., white_light_duty: _Optional[int] = ..., ir_led_duty: _Optional[int] = ..., ircut_mode: _Optional[int] = ...) -> None: ...

class EnvCtrlRequest(_message.Message):
    __slots__ = ("enable",)
    ENABLE_FIELD_NUMBER: _ClassVar[int]
    enable: bool
    def __init__(self, enable: bool = ...) -> None: ...

class EnvCtrlStatus(_message.Message):
    __slots__ = ("success", "message", "enabled")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    enabled: bool
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., enabled: bool = ...) -> None: ...

class AlarmOutRequest(_message.Message):
    __slots__ = ("channel", "enable")
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    ENABLE_FIELD_NUMBER: _ClassVar[int]
    channel: int
    enable: bool
    def __init__(self, channel: _Optional[int] = ..., enable: bool = ...) -> None: ...

class AlarmOutStatus(_message.Message):
    __slots__ = ("success", "message", "enabled")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    enabled: bool
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., enabled: bool = ...) -> None: ...

class WiegandOutRequest(_message.Message):
    __slots__ = ("channel", "enable")
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    ENABLE_FIELD_NUMBER: _ClassVar[int]
    channel: int
    enable: bool
    def __init__(self, channel: _Optional[int] = ..., enable: bool = ...) -> None: ...

class AlarmOutputsState(_message.Message):
    __slots__ = ("success", "message", "alarm_out0", "alarm_out1", "wiegand0", "wiegand1")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ALARM_OUT0_FIELD_NUMBER: _ClassVar[int]
    ALARM_OUT1_FIELD_NUMBER: _ClassVar[int]
    WIEGAND0_FIELD_NUMBER: _ClassVar[int]
    WIEGAND1_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    alarm_out0: bool
    alarm_out1: bool
    wiegand0: bool
    wiegand1: bool
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., alarm_out0: bool = ..., alarm_out1: bool = ..., wiegand0: bool = ..., wiegand1: bool = ...) -> None: ...

class Rs485InitRequest(_message.Message):
    __slots__ = ("baudrate", "config")
    BAUDRATE_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    baudrate: int
    config: str
    def __init__(self, baudrate: _Optional[int] = ..., config: _Optional[str] = ...) -> None: ...

class Rs485TxRequest(_message.Message):
    __slots__ = ("data",)
    DATA_FIELD_NUMBER: _ClassVar[int]
    data: bytes
    def __init__(self, data: _Optional[bytes] = ...) -> None: ...

class Rs485RxEvent(_message.Message):
    __slots__ = ("data", "timestamp_ns")
    DATA_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_NS_FIELD_NUMBER: _ClassVar[int]
    data: bytes
    timestamp_ns: int
    def __init__(self, data: _Optional[bytes] = ..., timestamp_ns: _Optional[int] = ...) -> None: ...

class McuRawRequestMessage(_message.Message):
    __slots__ = ("cmd", "payload")
    CMD_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    cmd: int
    payload: bytes
    def __init__(self, cmd: _Optional[int] = ..., payload: _Optional[bytes] = ...) -> None: ...

class McuRawResponseMessage(_message.Message):
    __slots__ = ("success", "message", "payload", "hal_code")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    HAL_CODE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    payload: bytes
    hal_code: int
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., payload: _Optional[bytes] = ..., hal_code: _Optional[int] = ...) -> None: ...

class AutofocusJobResponse(_message.Message):
    __slots__ = ("accepted", "job_id", "message")
    ACCEPTED_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    accepted: bool
    job_id: int
    message: str
    def __init__(self, accepted: bool = ..., job_id: _Optional[int] = ..., message: _Optional[str] = ...) -> None: ...

class AutofocusZoomFollowRequest(_message.Message):
    __slots__ = ("ratio",)
    RATIO_FIELD_NUMBER: _ClassVar[int]
    ratio: float
    def __init__(self, ratio: _Optional[float] = ...) -> None: ...

class AutofocusJobRequest(_message.Message):
    __slots__ = ("job_id",)
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    job_id: int
    def __init__(self, job_id: _Optional[int] = ...) -> None: ...

class AutofocusInvalidateRequest(_message.Message):
    __slots__ = ("reason",)
    REASON_FIELD_NUMBER: _ClassVar[int]
    reason: str
    def __init__(self, reason: _Optional[str] = ...) -> None: ...

class AutofocusStatusResponse(_message.Message):
    __slots__ = ("job_id", "operation", "state", "progress", "busy", "anchor_valid", "requested_ratio", "effective_ratio", "zoom_pos", "focus_pos", "best_focus", "metric", "confidence", "reproducibility", "estimated_distance_m", "elapsed_ms", "error_code", "message")
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    BUSY_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_VALID_FIELD_NUMBER: _ClassVar[int]
    REQUESTED_RATIO_FIELD_NUMBER: _ClassVar[int]
    EFFECTIVE_RATIO_FIELD_NUMBER: _ClassVar[int]
    ZOOM_POS_FIELD_NUMBER: _ClassVar[int]
    FOCUS_POS_FIELD_NUMBER: _ClassVar[int]
    BEST_FOCUS_FIELD_NUMBER: _ClassVar[int]
    METRIC_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    REPRODUCIBILITY_FIELD_NUMBER: _ClassVar[int]
    ESTIMATED_DISTANCE_M_FIELD_NUMBER: _ClassVar[int]
    ELAPSED_MS_FIELD_NUMBER: _ClassVar[int]
    ERROR_CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
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
    def __init__(self, job_id: _Optional[int] = ..., operation: _Optional[str] = ..., state: _Optional[str] = ..., progress: _Optional[float] = ..., busy: bool = ..., anchor_valid: bool = ..., requested_ratio: _Optional[float] = ..., effective_ratio: _Optional[float] = ..., zoom_pos: _Optional[int] = ..., focus_pos: _Optional[int] = ..., best_focus: _Optional[int] = ..., metric: _Optional[float] = ..., confidence: _Optional[float] = ..., reproducibility: _Optional[float] = ..., estimated_distance_m: _Optional[float] = ..., elapsed_ms: _Optional[int] = ..., error_code: _Optional[int] = ..., message: _Optional[str] = ...) -> None: ...

class SetConfigFieldRequest(_message.Message):
    __slots__ = ("field_path", "type", "value")
    FIELD_PATH_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    field_path: str
    type: ConfigFieldType
    value: str
    def __init__(self, field_path: _Optional[str] = ..., type: _Optional[_Union[ConfigFieldType, str]] = ..., value: _Optional[str] = ...) -> None: ...

class GetConfigFieldRequest(_message.Message):
    __slots__ = ("field_path",)
    FIELD_PATH_FIELD_NUMBER: _ClassVar[int]
    field_path: str
    def __init__(self, field_path: _Optional[str] = ...) -> None: ...

class GetConfigFieldResponse(_message.Message):
    __slots__ = ("success", "message", "type", "value")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    type: ConfigFieldType
    value: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., type: _Optional[_Union[ConfigFieldType, str]] = ..., value: _Optional[str] = ...) -> None: ...

class ConfigFieldValue(_message.Message):
    __slots__ = ("type", "value")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    type: ConfigFieldType
    value: str
    def __init__(self, type: _Optional[_Union[ConfigFieldType, str]] = ..., value: _Optional[str] = ...) -> None: ...

class MediaConfigFields(_message.Message):
    __slots__ = ("fields",)
    class FieldsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: ConfigFieldValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[ConfigFieldValue, _Mapping]] = ...) -> None: ...
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    fields: _containers.MessageMap[str, ConfigFieldValue]
    def __init__(self, fields: _Optional[_Mapping[str, ConfigFieldValue]] = ...) -> None: ...

class CapabilitiesResponse(_message.Message):
    __slots__ = ("has_video", "has_codec", "has_led", "has_sensor", "has_mcu", "has_env_ctrl", "has_alarm", "has_rs485", "has_osd", "has_draw", "has_audio")
    HAS_VIDEO_FIELD_NUMBER: _ClassVar[int]
    HAS_CODEC_FIELD_NUMBER: _ClassVar[int]
    HAS_LED_FIELD_NUMBER: _ClassVar[int]
    HAS_SENSOR_FIELD_NUMBER: _ClassVar[int]
    HAS_MCU_FIELD_NUMBER: _ClassVar[int]
    HAS_ENV_CTRL_FIELD_NUMBER: _ClassVar[int]
    HAS_ALARM_FIELD_NUMBER: _ClassVar[int]
    HAS_RS485_FIELD_NUMBER: _ClassVar[int]
    HAS_OSD_FIELD_NUMBER: _ClassVar[int]
    HAS_DRAW_FIELD_NUMBER: _ClassVar[int]
    HAS_AUDIO_FIELD_NUMBER: _ClassVar[int]
    has_video: bool
    has_codec: bool
    has_led: bool
    has_sensor: bool
    has_mcu: bool
    has_env_ctrl: bool
    has_alarm: bool
    has_rs485: bool
    has_osd: bool
    has_draw: bool
    has_audio: bool
    def __init__(self, has_video: bool = ..., has_codec: bool = ..., has_led: bool = ..., has_sensor: bool = ..., has_mcu: bool = ..., has_env_ctrl: bool = ..., has_alarm: bool = ..., has_rs485: bool = ..., has_osd: bool = ..., has_draw: bool = ..., has_audio: bool = ...) -> None: ...

class PrivacyMaskRegion(_message.Message):
    __slots__ = ("id", "name", "enabled", "points_x", "points_y")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    POINTS_X_FIELD_NUMBER: _ClassVar[int]
    POINTS_Y_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    enabled: bool
    points_x: _containers.RepeatedScalarFieldContainer[float]
    points_y: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., enabled: bool = ..., points_x: _Optional[_Iterable[float]] = ..., points_y: _Optional[_Iterable[float]] = ...) -> None: ...

class PrivacyMaskConfig(_message.Message):
    __slots__ = ("color", "blur_radius", "enabled", "regions", "dpm_enabled", "dpm_labels", "dpm_mode", "dpm_color")
    COLOR_FIELD_NUMBER: _ClassVar[int]
    BLUR_RADIUS_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    REGIONS_FIELD_NUMBER: _ClassVar[int]
    DPM_ENABLED_FIELD_NUMBER: _ClassVar[int]
    DPM_LABELS_FIELD_NUMBER: _ClassVar[int]
    DPM_MODE_FIELD_NUMBER: _ClassVar[int]
    DPM_COLOR_FIELD_NUMBER: _ClassVar[int]
    color: int
    blur_radius: int
    enabled: bool
    regions: _containers.RepeatedCompositeFieldContainer[PrivacyMaskRegion]
    dpm_enabled: bool
    dpm_labels: str
    dpm_mode: str
    dpm_color: int
    def __init__(self, color: _Optional[int] = ..., blur_radius: _Optional[int] = ..., enabled: bool = ..., regions: _Optional[_Iterable[_Union[PrivacyMaskRegion, _Mapping]]] = ..., dpm_enabled: bool = ..., dpm_labels: _Optional[str] = ..., dpm_mode: _Optional[str] = ..., dpm_color: _Optional[int] = ...) -> None: ...

class AudioDeviceInfo(_message.Message):
    __slots__ = ("name", "description")
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    name: str
    description: str
    def __init__(self, name: _Optional[str] = ..., description: _Optional[str] = ...) -> None: ...

class ListAudioDevicesResponse(_message.Message):
    __slots__ = ("success", "message", "devices")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    DEVICES_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    devices: _containers.RepeatedCompositeFieldContainer[AudioDeviceInfo]
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., devices: _Optional[_Iterable[_Union[AudioDeviceInfo, _Mapping]]] = ...) -> None: ...

class AudioConfigRequest(_message.Message):
    __slots__ = ("device", "sample_rate", "channels", "codec", "bitrate", "volume", "mute")
    DEVICE_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
    CHANNELS_FIELD_NUMBER: _ClassVar[int]
    CODEC_FIELD_NUMBER: _ClassVar[int]
    BITRATE_FIELD_NUMBER: _ClassVar[int]
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    MUTE_FIELD_NUMBER: _ClassVar[int]
    device: str
    sample_rate: int
    channels: int
    codec: str
    bitrate: int
    volume: float
    mute: bool
    def __init__(self, device: _Optional[str] = ..., sample_rate: _Optional[int] = ..., channels: _Optional[int] = ..., codec: _Optional[str] = ..., bitrate: _Optional[int] = ..., volume: _Optional[float] = ..., mute: bool = ...) -> None: ...

class AudioStatusResponse(_message.Message):
    __slots__ = ("success", "message", "capturing", "playing", "device", "sample_rate", "channels", "codec", "volume", "mute")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    CAPTURING_FIELD_NUMBER: _ClassVar[int]
    PLAYING_FIELD_NUMBER: _ClassVar[int]
    DEVICE_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
    CHANNELS_FIELD_NUMBER: _ClassVar[int]
    CODEC_FIELD_NUMBER: _ClassVar[int]
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    MUTE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    capturing: bool
    playing: bool
    device: str
    sample_rate: int
    channels: int
    codec: str
    volume: float
    mute: bool
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., capturing: bool = ..., playing: bool = ..., device: _Optional[str] = ..., sample_rate: _Optional[int] = ..., channels: _Optional[int] = ..., codec: _Optional[str] = ..., volume: _Optional[float] = ..., mute: bool = ...) -> None: ...

class AudioPcmChunk(_message.Message):
    __slots__ = ("data", "sample_rate", "channels", "format")
    DATA_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
    CHANNELS_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    data: bytes
    sample_rate: int
    channels: int
    format: str
    def __init__(self, data: _Optional[bytes] = ..., sample_rate: _Optional[int] = ..., channels: _Optional[int] = ..., format: _Optional[str] = ...) -> None: ...

class DspRect(_message.Message):
    __slots__ = ("x", "y", "width", "height", "dst_width", "dst_height")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    DST_WIDTH_FIELD_NUMBER: _ClassVar[int]
    DST_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    x: int
    y: int
    width: int
    height: int
    dst_width: int
    dst_height: int
    def __init__(self, x: _Optional[int] = ..., y: _Optional[int] = ..., width: _Optional[int] = ..., height: _Optional[int] = ..., dst_width: _Optional[int] = ..., dst_height: _Optional[int] = ...) -> None: ...

class DspJobRequest(_message.Message):
    __slots__ = ("op", "src_buffer_id", "dst_buffer_ids", "rects", "interpolation", "scaling_mode", "priority")
    OP_FIELD_NUMBER: _ClassVar[int]
    SRC_BUFFER_ID_FIELD_NUMBER: _ClassVar[int]
    DST_BUFFER_IDS_FIELD_NUMBER: _ClassVar[int]
    RECTS_FIELD_NUMBER: _ClassVar[int]
    INTERPOLATION_FIELD_NUMBER: _ClassVar[int]
    SCALING_MODE_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    op: DspOp
    src_buffer_id: int
    dst_buffer_ids: _containers.RepeatedScalarFieldContainer[int]
    rects: _containers.RepeatedCompositeFieldContainer[DspRect]
    interpolation: DspInterpolation
    scaling_mode: DspScalingMode
    priority: DspPriority
    def __init__(self, op: _Optional[_Union[DspOp, str]] = ..., src_buffer_id: _Optional[int] = ..., dst_buffer_ids: _Optional[_Iterable[int]] = ..., rects: _Optional[_Iterable[_Union[DspRect, _Mapping]]] = ..., interpolation: _Optional[_Union[DspInterpolation, str]] = ..., scaling_mode: _Optional[_Union[DspScalingMode, str]] = ..., priority: _Optional[_Union[DspPriority, str]] = ...) -> None: ...

class DspJobResponse(_message.Message):
    __slots__ = ("success", "message", "error_code", "elapsed_ms", "job_id", "done")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ERROR_CODE_FIELD_NUMBER: _ClassVar[int]
    ELAPSED_MS_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    DONE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    error_code: int
    elapsed_ms: int
    job_id: int
    done: bool
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., error_code: _Optional[int] = ..., elapsed_ms: _Optional[int] = ..., job_id: _Optional[int] = ..., done: bool = ...) -> None: ...

class DspWaitRequest(_message.Message):
    __slots__ = ("job_id", "timeout_ms")
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_MS_FIELD_NUMBER: _ClassVar[int]
    job_id: int
    timeout_ms: int
    def __init__(self, job_id: _Optional[int] = ..., timeout_ms: _Optional[int] = ...) -> None: ...

class EncodeImageRequest(_message.Message):
    __slots__ = ("src_buffer_id", "quality")
    SRC_BUFFER_ID_FIELD_NUMBER: _ClassVar[int]
    QUALITY_FIELD_NUMBER: _ClassVar[int]
    src_buffer_id: int
    quality: int
    def __init__(self, src_buffer_id: _Optional[int] = ..., quality: _Optional[int] = ...) -> None: ...

class EncodeImageResponse(_message.Message):
    __slots__ = ("success", "message", "error_code", "elapsed_ms", "jpeg")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ERROR_CODE_FIELD_NUMBER: _ClassVar[int]
    ELAPSED_MS_FIELD_NUMBER: _ClassVar[int]
    JPEG_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    error_code: int
    elapsed_ms: int
    jpeg: bytes
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., error_code: _Optional[int] = ..., elapsed_ms: _Optional[int] = ..., jpeg: _Optional[bytes] = ...) -> None: ...

class PushFrameRequest(_message.Message):
    __slots__ = ("buffer_id", "width", "height", "stride", "mode", "pts_ns", "dest_x", "dest_y", "end_of_stream", "stream_id", "session_id")
    BUFFER_ID_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    STRIDE_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    PTS_NS_FIELD_NUMBER: _ClassVar[int]
    DEST_X_FIELD_NUMBER: _ClassVar[int]
    DEST_Y_FIELD_NUMBER: _ClassVar[int]
    END_OF_STREAM_FIELD_NUMBER: _ClassVar[int]
    STREAM_ID_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    buffer_id: int
    width: int
    height: int
    stride: int
    mode: InjectionMode
    pts_ns: int
    dest_x: int
    dest_y: int
    end_of_stream: bool
    stream_id: str
    session_id: str
    def __init__(self, buffer_id: _Optional[int] = ..., width: _Optional[int] = ..., height: _Optional[int] = ..., stride: _Optional[int] = ..., mode: _Optional[_Union[InjectionMode, str]] = ..., pts_ns: _Optional[int] = ..., dest_x: _Optional[int] = ..., dest_y: _Optional[int] = ..., end_of_stream: bool = ..., stream_id: _Optional[str] = ..., session_id: _Optional[str] = ...) -> None: ...

class PushFrameResponse(_message.Message):
    __slots__ = ("success", "message", "error_code", "injected_frame_id", "accepted_frame_count", "session_id", "in_flight_buffer_ids")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ERROR_CODE_FIELD_NUMBER: _ClassVar[int]
    INJECTED_FRAME_ID_FIELD_NUMBER: _ClassVar[int]
    ACCEPTED_FRAME_COUNT_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    IN_FLIGHT_BUFFER_IDS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    error_code: int
    injected_frame_id: int
    accepted_frame_count: int
    session_id: str
    in_flight_buffer_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., error_code: _Optional[int] = ..., injected_frame_id: _Optional[int] = ..., accepted_frame_count: _Optional[int] = ..., session_id: _Optional[str] = ..., in_flight_buffer_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class InjectionStatusResponse(_message.Message):
    __slots__ = ("success", "message", "active", "mode", "frames_injected", "frames_dropped", "queue_depth", "session_id", "in_flight_buffer_ids", "reports_in_flight_buffers")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    FRAMES_INJECTED_FIELD_NUMBER: _ClassVar[int]
    FRAMES_DROPPED_FIELD_NUMBER: _ClassVar[int]
    QUEUE_DEPTH_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    IN_FLIGHT_BUFFER_IDS_FIELD_NUMBER: _ClassVar[int]
    REPORTS_IN_FLIGHT_BUFFERS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    active: bool
    mode: InjectionMode
    frames_injected: int
    frames_dropped: int
    queue_depth: int
    session_id: str
    in_flight_buffer_ids: _containers.RepeatedScalarFieldContainer[int]
    reports_in_flight_buffers: bool
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., active: bool = ..., mode: _Optional[_Union[InjectionMode, str]] = ..., frames_injected: _Optional[int] = ..., frames_dropped: _Optional[int] = ..., queue_depth: _Optional[int] = ..., session_id: _Optional[str] = ..., in_flight_buffer_ids: _Optional[_Iterable[int]] = ..., reports_in_flight_buffers: _Optional[bool] = ...) -> None: ...
