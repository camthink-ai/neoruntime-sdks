"""
Media Client - Zero-copy video stream access via DMA-BUF FD passing
and encoded stream access via EncodedPublisher UDS sockets.
"""

import logging
import os
import socket
import struct
import threading
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Dict, Iterator, List, Optional

import numpy as np

logger = logging.getLogger("hailo_ipc_sdk.media")


class PixelFormat(IntEnum):
    NV12 = 0
    NV21 = 1
    RGB = 2
    BGR = 3
    RGBA = 4
    BGRA = 5
    GRAY8 = 6
    YUYV = 7


PIXEL_FORMAT_NAMES = {
    PixelFormat.NV12: "NV12",
    PixelFormat.NV21: "NV21",
    PixelFormat.RGB: "RGB",
    PixelFormat.BGR: "BGR",
    PixelFormat.RGBA: "RGBA",
    PixelFormat.BGRA: "BGRA",
    PixelFormat.GRAY8: "GRAY8",
    PixelFormat.YUYV: "YUYV",
}


@dataclass
class Frame:
    sequence: int
    timestamp_ns: int
    width: int
    height: int
    format: str
    image: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def data(self) -> Optional[np.ndarray]:
        """Alias for image, returns raw frame data as flat numpy array."""
        if self.image is None:
            return None
        return self.image.flatten()

    def to_rgb(self) -> np.ndarray:
        if self.format == "RGB":
            return self.image
        elif self.format == "BGR":
            return self.image[:, :, ::-1]
        elif self.format == "NV12":
            return self._nv12_to_rgb()
        elif self.format == "GRAY8":
            return np.stack([self.image] * 3, axis=-1)
        else:
            raise ValueError(f"Unsupported format: {self.format}")
    
    def _nv12_to_rgb(self) -> np.ndarray:
        try:
            import cv2
            return cv2.cvtColor(self.image, cv2.COLOR_YUV2RGB_NV12)
        except ImportError:
            return self._nv12_to_rgb_pure()
    
    def _nv12_to_rgb_pure(self) -> np.ndarray:
        h, w = self.height, self.width
        y = self.image[:h, :].astype(np.float32)
        uv = self.image[h:, :].reshape(h // 2, w // 2, 2)
        u, v = uv[:, :, 0], uv[:, :, 1]
        
        u = u.repeat(2, axis=0).repeat(2, axis=1)
        v = v.repeat(2, axis=0).repeat(2, axis=1)
        
        y = y - 16
        u = u - 128
        v = v - 128
        
        r = np.clip(1.164 * y + 1.596 * v, 0, 255).astype(np.uint8)
        g = np.clip(1.164 * y - 0.813 * v - 0.391 * u, 0, 255).astype(np.uint8)
        b = np.clip(1.164 * y + 2.018 * u, 0, 255).astype(np.uint8)
        
        return np.stack([r, g, b], axis=-1)
    
    def save(self, path: str) -> None:
        try:
            import cv2
            rgb = self.to_rgb()
            bgr = rgb[:, :, ::-1]
            cv2.imwrite(path, bgr)
        except ImportError:
            from PIL import Image
            rgb = self.to_rgb()
            Image.fromarray(rgb).save(path)


@dataclass
class StreamInfo:
    stream_id: str
    width: int
    height: int
    format: str
    fps: float
    buffer_count: int


# ---------------------------------------------------------------------------
# FD Protocol constants (must match fd_protocol.h)
# ---------------------------------------------------------------------------

_FD_PUB_MSG_SUBSCRIBE   = 1
_FD_PUB_MSG_UNSUBSCRIBE = 2
_FD_PUB_MSG_FRAME       = 3
_FD_PUB_MSG_RELEASE     = 4
_FD_PUB_MSG_OK          = 5
_FD_PUB_MSG_ERROR       = 6

_FD_PUB_MAX_STREAM_NAME = 64
_FD_PUB_MAX_FDS         = 3
_FD_PUB_PROTOCOL_VERSION = 1

# struct FdPubMsgHeader { uint32 type; uint32 size; }
_HDR_FMT = '<II'
_HDR_SIZE = struct.calcsize(_HDR_FMT)

# struct FdPubSubscribeMsg { header(8) + uint32 version + char[64] stream_name }
_SUB_FMT = '<II I 64s'
_SUB_SIZE = struct.calcsize(_SUB_FMT)

# struct FdPubFrameMsg (aarch64 pads to 8-byte alignment: 76 data + 4 padding = 80)
_FRAME_FMT = '<II QQQ IIII 3I 3I I 4x'
_FRAME_SIZE = struct.calcsize(_FRAME_FMT)

# struct FdPubReleaseMsg { header(8) + uint64 frame_id }
_REL_FMT = '<II Q'
_REL_SIZE = struct.calcsize(_REL_FMT)

# struct FdPubResponseMsg { header(8) + int32 code }
_RESP_FMT = '<II i'
_RESP_SIZE = struct.calcsize(_RESP_FMT)

@dataclass
class EncodedFrame:
    """Encoded video frame (H.264/H.265) from the EncodedPublisher."""
    codec: int          # 0=h264, 1=h265
    flags: int          # bit0 = keyframe
    pts_ns: int         # Presentation timestamp (nanoseconds)
    width: int
    height: int
    dts_ns: int         # Decode timestamp (nanoseconds)
    data: bytes         # Encoded NALU payload

    @property
    def is_keyframe(self) -> bool:
        return bool(self.flags & 0x01)

    @property
    def codec_name(self) -> str:
        return {0: "h264", 1: "h265"}.get(self.codec, f"unknown({self.codec})")


# Encoded video header: 30 bytes, little-endian
# [0:4]   uint32  total_size (header + payload)
# [4]     uint8   codec (0=h264, 1=h265)
# [5]     uint8   flags (bit0 = keyframe)
# [6:14]  uint64  pts_ns
# [14:18] uint32  width
# [18:22] uint32  height
# [22:30] uint64  dts_ns
_ENC_HEADER_SIZE = 30
_ENC_HEADER_FMT = "<I BB Q II Q"


class EncodedStreamClient:
    """Read encoded video frames from an EncodedPublisher UDS socket.

    Connects to sockets like ``/run/aipc/encoded/main.sock`` and yields
    :class:`EncodedFrame` objects containing H.264/H.265 NAL units.

    Usage::

        client = EncodedStreamClient("/run/aipc/encoded/main.sock")
        for frame in client.subscribe():
            print(f"{frame.codec_name} {frame.width}x{frame.height} "
                  f"keyframe={frame.is_keyframe} {len(frame.data)}B")
    """

    def __init__(self, socket_path: str):
        self.socket_path = socket_path
        self._sock: Optional[socket.socket] = None
        self._lock = threading.Lock()

    def _connect(self) -> socket.socket:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self.socket_path)
        sock.settimeout(5.0)
        logger.info("EncodedStreamClient: connected to %s", self.socket_path)
        return sock

    def _get_sock(self) -> socket.socket:
        with self._lock:
            if self._sock is None:
                self._sock = self._connect()
            return self._sock

    def _recv_exact(self, sock: socket.socket, n: int) -> bytes:
        buf = bytearray()
        while len(buf) < n:
            chunk = sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("EncodedStreamClient: socket closed")
            buf.extend(chunk)
        return bytes(buf)

    def _recv_frame(self, sock: socket.socket) -> Optional[EncodedFrame]:
        try:
            header_data = self._recv_exact(sock, _ENC_HEADER_SIZE)
        except (ConnectionError, OSError):
            return None

        if len(header_data) < _ENC_HEADER_SIZE:
            return None

        values = struct.unpack(_ENC_HEADER_FMT, header_data)
        total_size = values[0]
        codec = values[1]
        flags = values[2]
        pts_ns = values[3]
        width = values[4]
        height = values[5]
        dts_ns = values[6]

        payload_size = total_size - _ENC_HEADER_SIZE
        if payload_size < 0 or payload_size > 50 * 1024 * 1024:
            logger.warning("EncodedStreamClient: bogus payload_size=%d", payload_size)
            return None

        try:
            payload = self._recv_exact(sock, payload_size) if payload_size > 0 else b""
        except (ConnectionError, OSError):
            return None

        return EncodedFrame(
            codec=codec, flags=flags, pts_ns=pts_ns,
            width=width, height=height, dts_ns=dts_ns,
            data=payload,
        )

    def _reconnect(self) -> socket.socket:
        with self._lock:
            if self._sock is not None:
                try:
                    self._sock.close()
                except OSError:
                    pass
                self._sock = None
            self._sock = self._connect()
            return self._sock

    def get_frame(self, timeout_ms: int = 5000) -> Optional[EncodedFrame]:
        """Get a single encoded frame. Returns None on timeout."""
        sock = self._get_sock()
        sock.settimeout(timeout_ms / 1000.0)
        try:
            return self._recv_frame(sock)
        except socket.timeout:
            return None

    def subscribe(self, reconnect: bool = True) -> Iterator[EncodedFrame]:
        """Yield encoded frames continuously. Auto-reconnects if enabled."""
        sock = self._get_sock()
        while True:
            frame = self._recv_frame(sock)
            if frame is not None:
                yield frame
                continue
            if not reconnect:
                break
            logger.info("EncodedStreamClient: reconnecting...")
            time.sleep(0.5)
            try:
                sock = self._reconnect()
            except OSError:
                logger.warning("EncodedStreamClient: reconnect failed, retrying in 2s")
                time.sleep(2.0)

    def on_frame(self, callback: Callable[[EncodedFrame], None]) -> threading.Thread:
        """Start a background thread that calls callback for each frame."""
        def _run():
            for frame in self.subscribe():
                try:
                    callback(frame)
                except Exception:
                    logger.exception("EncodedStreamClient: callback error")
        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return t

    def close(self) -> None:
        with self._lock:
            if self._sock is not None:
                try:
                    self._sock.close()
                except OSError:
                    pass
                self._sock = None
        logger.info("EncodedStreamClient: closed")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


import mmap  # noqa: E402
import socket as _socket  # noqa: E402


def _recvmsg_with_fds(sock: _socket.socket, bufsize: int, max_fds: int = _FD_PUB_MAX_FDS):
    """Receive data + SCM_RIGHTS file descriptors via recvmsg."""
    fds_space = _socket.CMSG_SPACE(max_fds * struct.calcsize('i'))
    data, ancdata, _flags, _addr = sock.recvmsg(bufsize, fds_space)
    fds: list[int] = []
    for cmsg_level, cmsg_type, cmsg_data in ancdata:
        if cmsg_level == _socket.SOL_SOCKET and cmsg_type == _socket.SCM_RIGHTS:
            n = len(cmsg_data) // struct.calcsize('i')
            fds.extend(struct.unpack(f'{n}i', cmsg_data[:n * struct.calcsize('i')]))
    return data, fds


def _sendmsg_plain(sock: _socket.socket, data: bytes) -> None:
    sock.sendall(data)


class FdMediaClient:
    """Zero-copy media client using DMA-BUF FD passing over Unix Domain Socket."""

    def __init__(self, socket_path: str | None = None):
        if socket_path is None:
            socket_path = os.getenv("CAMERA_SOCK_PATH", "/run/aipc/camera.sock")
        self.socket_path = socket_path
        self._streams: dict[str, _socket.socket] = {}
        self._lock = threading.Lock()

    # PLACEHOLDER_FDMEDIACLIENT_METHODS

    def _connect_stream(self, stream_id: str) -> _socket.socket:
        logger.info("FdMediaClient: connecting to %s for stream '%s'", self.socket_path, stream_id)

        sock = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
        sock.connect(self.socket_path)
        logger.info("FdMediaClient: socket fd=%d connected", sock.fileno())

        name_bytes = stream_id.encode('utf-8')[:_FD_PUB_MAX_STREAM_NAME - 1]
        name_padded = name_bytes.ljust(_FD_PUB_MAX_STREAM_NAME, b'\x00')
        sub_msg = struct.pack(_SUB_FMT, _FD_PUB_MSG_SUBSCRIBE, _SUB_SIZE,
                              _FD_PUB_PROTOCOL_VERSION, name_padded)
        _sendmsg_plain(sock, sub_msg)

        resp_data = sock.recv(_RESP_SIZE)
        if len(resp_data) < _RESP_SIZE:
            sock.close()
            raise ConnectionError(f"FdMediaClient: no response for stream '{stream_id}'")

        msg_type, msg_size, code = struct.unpack(_RESP_FMT, resp_data[:_RESP_SIZE])
        if msg_type != _FD_PUB_MSG_OK:
            sock.close()
            raise ConnectionError(f"FdMediaClient: subscribe rejected for '{stream_id}' (code={code})")

        logger.info("FdMediaClient: subscribed to '%s' successfully", stream_id)
        return sock

    def _get_sock(self, stream_id: str) -> _socket.socket:
        with self._lock:
            if stream_id not in self._streams:
                self._streams[stream_id] = self._connect_stream(stream_id)
            return self._streams[stream_id]

    def _release_frame(self, sock: _socket.socket, frame_id: int) -> None:
        rel = struct.pack(_REL_FMT, _FD_PUB_MSG_RELEASE, _REL_SIZE, frame_id)
        try:
            _sendmsg_plain(sock, rel)
        except OSError:
            pass

    def _recv_frame(self, sock: _socket.socket) -> Frame | None:
        skipped = 0
        eof_count = 0
        for _attempt in range(32):
            data, fds = _recvmsg_with_fds(sock, _FRAME_SIZE)

            # Detect EOF (server closed connection)
            if len(data) == 0:
                eof_count += 1
                if eof_count >= 3:
                    raise ConnectionError("FdMediaClient: socket EOF (server closed connection)")
                continue

            if len(data) < _FRAME_SIZE:
                for fd in fds:
                    os.close(fd)
                skipped += 1
                continue

            values = struct.unpack(_FRAME_FMT, data[:_FRAME_SIZE])
            msg_type = values[0]
            if msg_type != _FD_PUB_MSG_FRAME:
                for fd in fds:
                    os.close(fd)
                skipped += 1
                continue

            break
        else:
            if skipped > 0:
                logger.warning("FdMediaClient: skipped %d non-frame messages, giving up", skipped)
            return None

        if skipped > 0:
            logger.debug("FdMediaClient: skipped %d non-frame messages before frame", skipped)

        frame_id = values[2]
        timestamp_ns = values[3]
        sequence = values[4]
        width = values[5]
        height = values[6]
        fmt_code = values[7]
        num_planes = values[8]
        _strides = values[9:12]
        sizes = values[12:15]
        _num_fds_expected = values[15]

        # PLACEHOLDER_FDMEDIACLIENT_RECV_CONT

        fmt_name = PIXEL_FORMAT_NAMES.get(fmt_code, f"UNKNOWN({fmt_code})")

        try:
            if not fds:
                self._release_frame(sock, frame_id)
                return None

            # DMA-BUF fds must be mmapped per-plane using the fd's actual size,
            # not the protocol-reported plane size (which excludes alignment padding).
            planes = []
            for i in range(min(num_planes, len(fds))):
                fd = fds[i]
                actual_size = os.fstat(fd).st_size
                buf = mmap.mmap(fd, actual_size, access=mmap.ACCESS_READ)
                plane_data = np.frombuffer(buf, dtype=np.uint8)[:sizes[i]].copy()
                buf.close()
                planes.append(plane_data)
            raw = np.concatenate(planes) if len(planes) > 1 else planes[0]
        finally:
            for fd in fds:
                os.close(fd)

        self._release_frame(sock, frame_id)

        logger.debug(
            "FdMediaClient: frame seq=%d %dx%d %s released (frame_id=%d)",
            sequence, width, height, fmt_name, frame_id,
        )

        image = self._decode(raw, width, height, fmt_name)
        return Frame(
            sequence=sequence,
            timestamp_ns=timestamp_ns,
            width=width,
            height=height,
            format=fmt_name,
            image=image,
        )

    @staticmethod
    def _decode(raw: np.ndarray, w: int, h: int, fmt: str) -> np.ndarray:
        if fmt in ("NV12", "NV21"):
            return raw.reshape(h * 3 // 2, w)
        elif fmt in ("RGB", "BGR"):
            return raw.reshape(h, w, 3)
        elif fmt in ("RGBA", "BGRA"):
            return raw.reshape(h, w, 4)
        elif fmt == "GRAY8":
            return raw.reshape(h, w)
        elif fmt == "YUYV":
            return raw.reshape(h, w, 2)
        return raw.reshape(h, w, 3)

    def get_frame(self, stream_id: str, timeout_ms: int = 5000) -> Frame | None:
        sock = self._get_sock(stream_id)
        sock.settimeout(timeout_ms / 1000.0)
        try:
            return self._recv_frame(sock)
        except _socket.timeout:
            return None
        except (ConnectionError, OSError):
            # Stale socket — clear cache so next call reconnects
            with self._lock:
                old = self._streams.pop(stream_id, None)
                if old:
                    try:
                        old.close()
                    except OSError:
                        pass
            raise

    def subscribe_raw(self, stream_id: str, skip_frames: bool = True) -> Iterator[Frame]:
        sock = self._get_sock(stream_id)
        sock.settimeout(5.0)
        while True:
            try:
                frame = self._recv_frame(sock)
                if frame is not None:
                    yield frame
            except _socket.timeout:
                continue
            except (ConnectionError, OSError):
                with self._lock:
                    self._streams.pop(stream_id, None)
                try:
                    sock.close()
                except OSError:
                    pass
                time.sleep(0.5)
                sock = self._get_sock(stream_id)
                sock.settimeout(5.0)

    def subscribe(self, stream_id: str, skip_frames: bool = True) -> Iterator[Frame]:
        return self.subscribe_raw(stream_id, skip_frames)

    def on_frame(self, stream_id: str, callback: Callable[[Frame], None]) -> threading.Thread:
        def _run():
            for frame in self.subscribe_raw(stream_id):
                try:
                    callback(frame)
                except Exception:
                    pass
        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return t

    def close(self) -> None:
        logger.info(
            "FdMediaClient: closing %d stream connections", len(self._streams),
        )
        with self._lock:
            for sock in self._streams.values():
                try:
                    unsub = struct.pack(_HDR_FMT, _FD_PUB_MSG_UNSUBSCRIBE, _HDR_SIZE)
                    sock.sendall(unsub)
                except OSError:
                    pass
                try:
                    sock.close()
                except OSError:
                    pass
            self._streams.clear()

    # -- Encoded stream convenience methods --

    def get_encoded_stream(self, stream_id: str = "main",
                           socket_dir: str = "/run/aipc/encoded") -> EncodedStreamClient:
        """Return an :class:`EncodedStreamClient` for the given encoded stream.

        Args:
            stream_id: Stream name (e.g. ``"main"``, ``"sub"``).
            socket_dir: Directory containing EncodedPublisher UDS sockets.

        Returns:
            A connected :class:`EncodedStreamClient` reading from
            ``{socket_dir}/{stream_id}.sock``.
        """
        path = os.path.join(socket_dir, f"{stream_id}.sock")
        return EncodedStreamClient(path)

    def list_streams(self) -> List[str]:
        """List available raw stream IDs by scanning the camera socket.

        Returns common stream IDs. For detailed status use
        :class:`CameraClient.get_stream_status`.
        """
        return ["main", "sub"]

    def get_rtsp_url(self, stream_id: str = "main",
                     host: str = "192.0.2.72", port: int = 8554) -> str:
        """Return an RTSP URL for the given stream.

        Note: RTSP must be enabled on the device first (via CameraClient
        or REST API).
        """
        return f"rtsp://{host}:{port}/{stream_id}"

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()