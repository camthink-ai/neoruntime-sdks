"""
Plugin SDK - Client and server helpers for the AIPC plugin system.

For plugin providers:
    server = PluginServer("my-plugin")
    server.start(my_grpc_servicer)

For plugin consumers:
    discovery = PluginDiscovery()
    endpoint = discovery.get("rtsp-server")
    channel = endpoint.connect()
"""

import json
import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

import grpc

DISCOVERY_DIR = "/run/aipc/plugins"
DISCOVERY_FILE = "discovery.json"


@dataclass
class PluginEndpoint:
    """Resolved endpoint for a discovered plugin capability."""
    app_id: str
    capability_id: str
    version: str
    transport: str
    socket_path: Optional[str] = None
    grpc_service: Optional[str] = None
    event_publish: List[str] = field(default_factory=list)
    event_subscribe: List[str] = field(default_factory=list)
    state: str = "unknown"

    def connect(self, **kwargs) -> grpc.Channel:
        """Create a gRPC channel to this plugin."""
        if not self.socket_path:
            raise RuntimeError(f"Plugin {self.app_id} capability {self.capability_id} has no gRPC endpoint")
        return grpc.insecure_channel(f"unix://{self.socket_path}", **kwargs)

    @property
    def is_available(self) -> bool:
        return self.state == "running"


class PluginDiscovery:
    """Client-side plugin discovery using discovery.json + optional file watcher."""

    def __init__(self, discovery_dir: str = DISCOVERY_DIR):
        self._dir = Path(discovery_dir)
        self._file = self._dir / DISCOVERY_FILE
        self._data: Dict = {}
        self._lock = threading.Lock()
        self._watchers: List[Callable] = []
        self._watch_thread: Optional[threading.Thread] = None
        self._running = False
        self.reload()

    def reload(self):
        """Reload discovery data from file."""
        with self._lock:
            try:
                if self._file.exists():
                    self._data = json.loads(self._file.read_text())
                else:
                    self._data = {"plugins": {}}
            except (json.JSONDecodeError, OSError):
                self._data = {"plugins": {}}

    def get(self, capability_id: str) -> Optional[PluginEndpoint]:
        """Find the first running plugin providing a capability."""
        with self._lock:
            plugins = self._data.get("plugins", {})
            for _app_id, entry in plugins.items():
                for cap in entry.get("capabilities", []):
                    if cap.get("id") == capability_id:
                        ep = PluginEndpoint(
                            app_id=entry["app_id"],
                            capability_id=cap["id"],
                            version=cap.get("version", ""),
                            transport=cap.get("transport", ""),
                            state=entry.get("state", "unknown"),
                        )
                        grpc_info = cap.get("grpc")
                        if grpc_info:
                            ep.socket_path = grpc_info.get("socket_path")
                            ep.grpc_service = grpc_info.get("service")
                        event_info = cap.get("event")
                        if event_info:
                            ep.event_publish = event_info.get("publish", [])
                            ep.event_subscribe = event_info.get("subscribe", [])
                        return ep
        return None

    def require(self, capability_id: str, timeout: float = 30.0) -> PluginEndpoint:
        """Wait for a capability to become available. Raises TimeoutError."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.reload()
            ep = self.get(capability_id)
            if ep and ep.is_available:
                return ep
            time.sleep(1.0)
        raise TimeoutError(f"Plugin capability {capability_id!r} not available within {timeout}s")

    def list_plugins(self) -> Dict[str, dict]:
        """Return all known plugins."""
        with self._lock:
            return dict(self._data.get("plugins", {}))

    def list_capabilities(self) -> List[str]:
        """Return all known capability IDs."""
        result = []
        with self._lock:
            for entry in self._data.get("plugins", {}).values():
                for cap in entry.get("capabilities", []):
                    cap_id = cap.get("id")
                    if cap_id and cap_id not in result:
                        result.append(cap_id)
        return result

    def watch(self, callback: Callable[[], None]):
        """Register a callback invoked when discovery.json changes."""
        self._watchers.append(callback)
        if not self._running:
            self._start_watch()

    def _start_watch(self):
        self._running = True
        self._watch_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._watch_thread.start()

    def _watch_loop(self):
        last_mtime = 0.0
        while self._running:
            try:
                if self._file.exists():
                    mtime = self._file.stat().st_mtime
                    if mtime != last_mtime:
                        last_mtime = mtime
                        self.reload()
                        for cb in self._watchers:
                            try:
                                cb()
                            except Exception:
                                pass
            except OSError:
                pass
            time.sleep(2.0)

    def close(self):
        self._running = False


class PluginServer:
    """Helper for plugin containers to set up a gRPC server on the standard socket path."""

    def __init__(self, plugin_id: str, socket_dir: str = DISCOVERY_DIR):
        self.plugin_id = plugin_id
        self.socket_path = os.path.join(socket_dir, f"{plugin_id}.sock")
        self._server: Optional[grpc.Server] = None

    def create_server(self, max_workers: int = 4, **kwargs) -> grpc.Server:
        """Create a gRPC server bound to the plugin socket."""
        from concurrent import futures
        self._server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers), **kwargs)
        self._server.add_insecure_port(f"unix://{self.socket_path}")
        return self._server

    def start(self):
        """Start the gRPC server."""
        if self._server is None:
            raise RuntimeError("Call create_server() first")
        self._server.start()

    def wait(self):
        """Block until server terminates."""
        if self._server:
            self._server.wait_for_termination()

    def stop(self, grace: float = 5.0):
        """Gracefully stop the server."""
        if self._server:
            self._server.stop(grace)
        # Clean up socket file
        try:
            os.unlink(self.socket_path)
        except OSError:
            pass
