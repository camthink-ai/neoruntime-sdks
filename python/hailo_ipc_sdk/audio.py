"""
Audio Client

Provides audio capture, playback, and device enumeration through
the camera-daemon gRPC service.
"""

from dataclasses import dataclass
from typing import Iterator, List, Optional

import grpc

from .config import Config
from .proto import camera_pb2, camera_pb2_grpc


@dataclass
class AudioDevice:
    name: str
    description: str


@dataclass
class AudioStatus:
    capturing: bool
    playing: bool
    device: str
    sample_rate: int
    channels: int
    codec: str
    volume: float
    mute: bool


class AudioClient:
    """
    Audio control client for the camera-daemon audio HAL.

    Usage:
        audio = AudioClient()

        # List capture devices
        devices = audio.list_capture_devices()

        # Start capture
        audio.start_capture(codec="aac", sample_rate=48000)

        # Check status
        status = audio.get_status()
        print(status.capturing)

        # Adjust volume
        audio.set_config(volume=0.8)

        # Stop capture
        audio.stop_capture()
    """

    def __init__(self, endpoint: Optional[str] = None):
        if endpoint is None:
            endpoint = Config.get_camera_control_endpoint()
        self.endpoint = endpoint
        self._channel: Optional[grpc.Channel] = None
        self._stub: Optional[camera_pb2_grpc.CameraControlStub] = None

    def _connect(self):
        if self._stub is not None:
            return
        self._channel = grpc.insecure_channel(self.endpoint)
        self._stub = camera_pb2_grpc.CameraControlStub(self._channel)

    def close(self):
        if self._channel is not None:
            self._channel.close()
            self._channel = None
            self._stub = None

    def __enter__(self):
        self._connect()
        return self

    def __exit__(self, *args):
        self.close()

    def _ensure_connected(self) -> camera_pb2_grpc.CameraControlStub:
        self._connect()
        return self._stub

    # -- Device enumeration --

    def list_capture_devices(self) -> List[AudioDevice]:
        """List available audio capture devices."""
        stub = self._ensure_connected()
        resp: camera_pb2.ListAudioDevicesResponse = stub.ListAudioCaptureDevices(
            camera_pb2.Empty()
        )
        return [
            AudioDevice(name=d.name, description=d.description)
            for d in resp.devices
        ]

    def list_playback_devices(self) -> List[AudioDevice]:
        """List available audio playback devices."""
        stub = self._ensure_connected()
        resp: camera_pb2.ListAudioDevicesResponse = stub.ListAudioPlaybackDevices(
            camera_pb2.Empty()
        )
        return [
            AudioDevice(name=d.name, description=d.description)
            for d in resp.devices
        ]

    # -- Capture --

    def start_capture(
        self,
        device: str = "",
        sample_rate: int = 0,
        channels: int = 0,
        codec: str = "",
        bitrate: int = 0,
    ) -> None:
        """Start audio capture. Leave parameters at 0/empty to use defaults."""
        stub = self._ensure_connected()
        resp = stub.StartAudioCapture(
            camera_pb2.AudioConfigRequest(
                device=device,
                sample_rate=sample_rate,
                channels=channels,
                codec=codec,
                bitrate=bitrate,
            )
        )
        if not resp.success:
            raise RuntimeError(f"StartAudioCapture failed: {resp.message}")

    def stop_capture(self) -> None:
        """Stop audio capture."""
        stub = self._ensure_connected()
        resp = stub.StopAudioCapture(camera_pb2.Empty())
        if not resp.success:
            raise RuntimeError(f"StopAudioCapture failed: {resp.message}")

    # -- Playback --

    def start_playback(
        self,
        device: str = "",
        sample_rate: int = 0,
        channels: int = 0,
    ) -> None:
        """Start audio playback."""
        stub = self._ensure_connected()
        resp = stub.StartAudioPlayback(
            camera_pb2.AudioConfigRequest(
                device=device,
                sample_rate=sample_rate,
                channels=channels,
            )
        )
        if not resp.success:
            raise RuntimeError(f"StartAudioPlayback failed: {resp.message}")

    def stop_playback(self) -> None:
        """Stop audio playback."""
        stub = self._ensure_connected()
        resp = stub.StopAudioPlayback(camera_pb2.Empty())
        if not resp.success:
            raise RuntimeError(f"StopAudioPlayback failed: {resp.message}")

    # -- Status & Config --

    def get_status(self) -> AudioStatus:
        """Get current audio status."""
        stub = self._ensure_connected()
        resp: camera_pb2.AudioStatusResponse = stub.GetAudioStatus(
            camera_pb2.Empty()
        )
        return AudioStatus(
            capturing=resp.capturing,
            playing=resp.playing,
            device=resp.device,
            sample_rate=resp.sample_rate,
            channels=resp.channels,
            codec=resp.codec,
            volume=resp.volume,
            mute=resp.mute,
        )

    def set_config(
        self,
        device: str = "",
        sample_rate: int = 0,
        channels: int = 0,
        codec: str = "",
        bitrate: int = 0,
        volume: float = -1.0,
        mute: Optional[bool] = None,
    ) -> None:
        """Update audio configuration (volume, mute, codec, etc.).

        Leave parameters at defaults to keep current values.
        Volume -1.0 means don't change; mute None means don't change.
        """
        stub = self._ensure_connected()
        req = camera_pb2.AudioConfigRequest(
            device=device,
            sample_rate=sample_rate,
            channels=channels,
            codec=codec,
            bitrate=bitrate,
        )
        if volume >= 0:
            req.volume = volume
        if mute is not None:
            req.mute = mute

        resp = stub.SetAudioConfig(req)
        if not resp.success:
            raise RuntimeError(f"SetAudioConfig failed: {resp.message}")

    # -- Two-way talk (PCM streaming to device) --

    def stream_pcm(
        self,
        pcm_iter: Iterator[bytes],
        sample_rate: int = 48000,
        channels: int = 1,
        fmt: str = "S16LE",
    ) -> None:
        """Stream PCM audio chunks to device for two-way talk (playback).

        Args:
            pcm_iter: Iterator yielding raw PCM byte chunks.
            sample_rate: Sample rate (default 48000).
            channels: Channel count (default 1 = mono).
            fmt: Sample format (default "S16LE").
        """
        stub = self._ensure_connected()

        def request_gen():
            for chunk in pcm_iter:
                yield camera_pb2.AudioPcmChunk(
                    data=chunk,
                    sample_rate=sample_rate,
                    channels=channels,
                    format=fmt,
                )

        resp = stub.StreamAudioPcm(request_gen())
        if not resp.success:
            raise RuntimeError(f"StreamAudioPcm failed: {resp.message}")

    def stream_pcm_file(
        self,
        path: str,
        chunk_size: int = 4096,
        sample_rate: int = 48000,
        channels: int = 1,
        fmt: str = "S16LE",
    ) -> None:
        """Stream a raw PCM file to device for playback.

        Args:
            path: Path to raw PCM file.
            chunk_size: Bytes per chunk (default 4096).
            sample_rate: Sample rate.
            channels: Channel count.
            fmt: Sample format.
        """

        def file_iter():
            with open(path, "rb") as f:
                while True:
                    data = f.read(chunk_size)
                    if not data:
                        break
                    yield data

        self.stream_pcm(file_iter(), sample_rate, channels, fmt)
