"""
AI Overlay Control Client

Control the platform's AI overlay system that draws detection boxes,
labels, and confidence scores directly on NV12 frames before encoding.
Zero CPU cost — drawing happens in camera-daemon before encoding.

Uses gRPC over Unix domain socket, consistent with other SDK clients.
"""

import logging
import os
from dataclasses import dataclass
from typing import Optional

import grpc

from .proto import camera_pb2, camera_pb2_grpc

logger = logging.getLogger("hailo_ipc_sdk.overlay")


@dataclass
class OverlayConfig:
    """AI overlay configuration."""
    enabled: bool = True
    show_label: bool = True
    show_confidence: bool = True
    line_thickness: int = 2
    box_color: int = 0
    label_color: int = 0
    font_size: int = 0

    def to_proto(self) -> camera_pb2.AiOverlayConfig:
        cfg = camera_pb2.AiOverlayConfig(
            enabled=self.enabled,
            show_label=self.show_label,
            show_confidence=self.show_confidence,
            line_thickness=self.line_thickness,
        )
        if self.box_color:
            cfg.box_color = self.box_color
        if self.label_color:
            cfg.label_color = self.label_color
        if self.font_size:
            cfg.font_size = self.font_size
        return cfg


class OverlayClient:
    """
    AI Overlay Control Client

    Uses gRPC to communicate with camera-daemon's CameraControl service.

    Usage::

        from hailo_ipc_sdk import OverlayClient

        oc = OverlayClient()

        # Enable overlay with default settings
        oc.enable()

        # Customize appearance
        oc.configure(
            show_label=True,
            show_confidence=True,
            line_thickness=3,
        )

        # Disable overlay
        oc.disable()

    Environment variables:
        CAMERA_CONTROL_ENDPOINT: Camera control gRPC endpoint
                                  (default: unix:///run/aipc/camera-control.sock)
    """

    def __init__(self, endpoint: Optional[str] = None):
        self.endpoint = (
            endpoint
            or os.getenv("CAMERA_CONTROL_ENDPOINT", "unix:///run/aipc/camera-control.sock")
        )
        self.channel: Optional[grpc.Channel] = None
        self.stub: Optional[camera_pb2_grpc.CameraControlStub] = None

    def connect(self) -> None:
        if self.channel is None:
            self.channel = grpc.insecure_channel(self.endpoint)
            self.stub = camera_pb2_grpc.CameraControlStub(self.channel)

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

    def _update(self, config: camera_pb2.AiOverlayConfig) -> None:
        if self.stub is None:
            self.connect()
        resp = self.stub.UpdateAiOverlay(config)
        if not resp.success:
            raise RuntimeError(f"UpdateAiOverlay failed: {resp.message}")

    def enable(
        self,
        show_label: bool = True,
        show_confidence: bool = True,
        line_thickness: int = 2,
    ) -> None:
        """Enable AI overlay with specified settings."""
        self._update(camera_pb2.AiOverlayConfig(
            enabled=True,
            show_label=show_label,
            show_confidence=show_confidence,
            line_thickness=line_thickness,
        ))
        logger.info("AI overlay enabled")

    def disable(self) -> None:
        """Disable AI overlay."""
        self._update(camera_pb2.AiOverlayConfig(enabled=False))
        logger.info("AI overlay disabled")

    def configure(
        self,
        enabled: bool = True,
        show_label: bool = True,
        show_confidence: bool = True,
        line_thickness: int = 2,
        box_color: int = 0,
        label_color: int = 0,
        font_size: int = 0,
    ) -> None:
        """
        Configure AI overlay with full control.

        Args:
            enabled: Enable or disable overlay
            show_label: Show class label on detections
            show_confidence: Show confidence score on detections
            line_thickness: Box line thickness (1-10)
            box_color: Box color in ARGB format (e.g. 0xFFFF0000 for red)
            label_color: Label color in ARGB format
            font_size: Font size (8-72)
        """
        cfg = camera_pb2.AiOverlayConfig(
            enabled=enabled,
            show_label=show_label,
            show_confidence=show_confidence,
            line_thickness=line_thickness,
        )
        if box_color:
            cfg.box_color = box_color
        if label_color:
            cfg.label_color = label_color
        if font_size:
            cfg.font_size = font_size
        self._update(cfg)
        logger.info("AI overlay configured")

    def apply(self, config: OverlayConfig) -> None:
        """Apply an OverlayConfig object."""
        self._update(config.to_proto())
        logger.info("AI overlay config applied")
