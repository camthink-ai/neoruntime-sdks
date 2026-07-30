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
"""

__version__ = "0.3.0"

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
    ISPConfig,
    PipelineStreamConfig,
    SensorInfo,
    StreamStatus,
    TransformConfig,
)
from .config import Config
from .device import (
    DeviceClient,
    DeviceEvent,
    DeviceStatus,
    IrCutMode,
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
from .media import (
    EncodedFrame,
    EncodedStreamClient,
    FdMediaClient,
    Frame,
    PixelFormat,
    StreamInfo,
)
from .overlay import (
    OverlayClient,
    OverlayConfig,
)
from .plugin import PluginDiscovery, PluginEndpoint, PluginServer

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
    # Media
    "FdMediaClient",
    "Frame",
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
    # Config & Plugin
    "Config",
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
]