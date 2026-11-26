"""
NE503 EdgeCam AI Platform Python SDK

Provides clean API to access platform capabilities:
- Video streams (Raw DMA-BUF + Encoded H.264/H.265)
- Audio streams (PCM/AAC via UDS + two-way talk via gRPC)
- AI inference service
- Event bus
- Device control (lights, PTZ, GPIO)
- Camera control (ISP, encoder, RTSP, OSD, profiles)
- App container management
- AI overlay control (detection boxes on RTSP/Web)
- App toolkit: frame crop/resize/JPEG, detection drawing, TS/HLS
  recording, MJPEG serving
- DSP offload: hardware resize/crop/multi-crop with CPU fallback
"""

from __future__ import annotations

__version__ = "0.8.2"

from .accel import (
    AccelRouter,
    DegradationRecord,
    HardwareUnavailable,
    RouteDecision,
    RoutePolicy,
    get_default_router,
    set_route_policy,
)
from .app import (
    AppClient,
    AppInfo,
    AppStats,
    LogLine,
)
from .audio import (
    AudioClient,
    AudioDevice,
    AudioStatus,
)
from .audio_stream import (
    AudioFrame,
    AudioStreamClient,
)
from .camera import (
    CameraClient,
    Capabilities,
    EncoderReconfigResult,
    EnvStatus,
    HardwareStatus,
    InfraredStatus,
    InjectionResult,
    InjectionStatus,
    IrPreset,
    ISPConfig,
    PipelineStreamConfig,
    PrivacyMaskSettings,
    SensorInfo,
    StreamStatus,
    TransformConfig,
)
from .color import (
    bgr_to_nv12,
    nv12_resize,
    nv12_to_bgr,
    nv12_to_rgb,
    rgb_to_nv12,
)
from .config import Config
from .device import (
    AfJob,
    AfMeasurement,
    AfStatus,
    DeviceClient,
    DeviceEvent,
    DeviceStatus,
    IrCutMode,
    Rs485RxEvent,
)
from .diagnostics import diagnostics
from .draw import (
    draw_boxes,
    draw_detections,
    draw_polygons,
    draw_text,
    render_overlay_fragments,
    render_overlay_rgba,
)
from .dsp import (
    DspBufferPool,
    DspBufferRef,
    DspClient,
    DspError,
    PendingDspJob,
)
from .events import (
    Event,
    EventClient,
    TopicInfo,
)
from .inference import (
    BatchInferItem,
    BoundingBox,
    Classification,
    DepthMap,
    DetectedObject,
    Embedding,
    InferenceClient,
    InferenceResult,
    LandmarkPoint,
    LandmarkSet,
    ModelInfo,
    OcrLine,
    SegmentationMask,
)
from .injection import FramePublisher
from .media import (
    FRAME_FLAG_DPM_BAKED,
    FRAME_FLAG_OVERLAY_BAKED,
    EncodedFrame,
    EncodedStreamClient,
    FdMediaClient,
    Frame,
    FrameHandle,
    PixelFormat,
    StreamInfo,
)
from .overlay import (
    OverlayClient,
    OverlayConfig,
)
from .pipeline import InferencePipeline, PipelineResult
from .plugin import PluginDiscovery, PluginEndpoint, PluginServer
from .postprocess import (
    Postprocessor,
    YoloV5Postprocessor,
    YoloV8Postprocessor,
    nms,
)
from .preprocess import PreprocessMeta, Preprocessor
from .recording import (
    HlsWriter,
    PrerollBuffer,
    TsWriter,
)
from .runner import PipelineRunner
from .stream_pipeline import StreamPipeline, StreamPipelineStatus
from .web import (
    MjpegServer,
    MjpegStream,
    mjpeg_wsgi_app,
    platform_stream_url,
)

__all__ = [
    # Version
    "__version__",
    # Inference
    "InferenceClient",
    "BatchInferItem",
    "BoundingBox",
    "DetectedObject",
    "InferenceResult",
    "ModelInfo",
    "LandmarkPoint",
    "LandmarkSet",
    "Classification",
    "SegmentationMask",
    "OcrLine",
    "Embedding",
    "DepthMap",
    # Injection (frame output)
    "FramePublisher",
    # Media
    "FdMediaClient",
    "Frame",
    "FrameHandle",
    "FRAME_FLAG_DPM_BAKED",
    "FRAME_FLAG_OVERLAY_BAKED",
    "StreamInfo",
    "PixelFormat",
    "EncodedFrame",
    "EncodedStreamClient",
    # Events
    "EventClient",
    "Event",
    "TopicInfo",
    # Device
    "DeviceClient",
    "DeviceStatus",
    "DeviceEvent",
    "IrCutMode",
    # Autofocus (device)
    "AfJob",
    "AfStatus",
    "AfMeasurement",
    # App toolkit: draw / recording / web
    "draw_boxes",
    "draw_text",
    "draw_detections",
    "draw_polygons",
    "render_overlay_rgba",
    "render_overlay_fragments",
    # App toolkit: color conversion / NMS / accel routing
    "nv12_to_rgb",
    "nv12_to_bgr",
    "rgb_to_nv12",
    "bgr_to_nv12",
    "nv12_resize",
    "nms",
    "Postprocessor",
    "YoloV5Postprocessor",
    "YoloV8Postprocessor",
    # Preprocessing & pipeline (client-side pre/post)
    "Preprocessor",
    "PreprocessMeta",
    "InferencePipeline",
    "PipelineResult",
    "PipelineRunner",
    # Whole pipeline (platform-scheduled)
    "StreamPipeline",
    "StreamPipelineStatus",
    "AccelRouter",
    "RoutePolicy",
    "RouteDecision",
    "DegradationRecord",
    "HardwareUnavailable",
    "get_default_router",
    "set_route_policy",
    "TsWriter",
    "HlsWriter",
    "PrerollBuffer",
    "MjpegStream",
    "mjpeg_wsgi_app",
    "platform_stream_url",
    "MjpegServer",
    # DSP offload
    "DspClient",
    "DspBufferPool",
    "DspBufferRef",
    "DspError",
    "PendingDspJob",
    # Config & Plugin
    "Config",
    "diagnostics",
    "PluginDiscovery",
    "PluginServer",
    "PluginEndpoint",
    # App
    "AppClient",
    "AppInfo",
    "AppStats",
    "LogLine",
    # Overlay
    "OverlayClient",
    "OverlayConfig",
    # Audio
    "AudioClient",
    "AudioDevice",
    "AudioStatus",
    # Audio Stream (UDS)
    "AudioStreamClient",
    "AudioFrame",
    # Camera
    "CameraClient",
    "ISPConfig",
    "TransformConfig",
    "EncoderReconfigResult",
    "StreamStatus",
    "Capabilities",
    "SensorInfo",
    "HardwareStatus",
    "PipelineStreamConfig",
    "EnvStatus",
    # Imaging / infrared / privacy mask (camera)
    "InfraredStatus",
    "InjectionResult",
    "InjectionStatus",
    "IrPreset",
    "PrivacyMaskSettings",
]
