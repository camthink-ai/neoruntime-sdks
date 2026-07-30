"""
App Manager Client

Provides API for managing application containers:
- Install, start, stop, uninstall applications
- Get application info and stats
- Stream application logs
"""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator, List, Optional

import grpc

from .proto import app_pb2, app_pb2_grpc


@dataclass
class AppInfo:
    """Application information"""
    id: str
    name: str
    version: str
    state: str  # installed, running, stopped, failed
    container_id: str
    pid: int
    installed_at: int
    started_at: int
    stopped_at: int
    restart_count: int
    manifest_path: str
    instance_path: str


@dataclass
class AppStats:
    """Application runtime statistics"""
    app_id: str
    cpu_usage_percent: float
    memory_usage_bytes: int
    memory_limit_bytes: int
    thread_count: int
    uptime_seconds: int


@dataclass
class LogLine:
    """Single log line"""
    timestamp: int  # Unix timestamp in nanoseconds
    level: str      # info, warn, error, debug
    message: str

    @property
    def datetime(self) -> datetime:
        """Convert timestamp to datetime"""
        return datetime.fromtimestamp(self.timestamp / 1e9)

    def __str__(self) -> str:
        dt = self.datetime.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        return f"[{dt}] [{self.level.upper():5}] {self.message}"


class AppClient:
    """
    Application Container Management Client

    Usage::

        app_client = AppClient()

        # List all apps
        apps = app_client.list_apps()
        for app in apps:
            print(f"{app.name}: {app.state}")

        # Get logs (last 100 lines)
        for line in app_client.get_logs("my_app", max_lines=100):
            print(line)

        # Follow logs in real-time
        for line in app_client.get_logs("my_app", follow=True):
            print(line)
    """

    def __init__(self, endpoint: Optional[str] = None):
        if endpoint is None:
            endpoint = self._get_default_endpoint()

        self.endpoint = endpoint
        self.channel: Optional[grpc.Channel] = None
        self.stub: Optional[app_pb2_grpc.AppManagerStub] = None

    def _get_default_endpoint(self) -> str:
        import os
        return os.getenv("APP_MANAGER_ENDPOINT", "unix:///run/aipc/app-manager.sock")

    def connect(self) -> None:
        if self.channel is None:
            self.channel = grpc.insecure_channel(self.endpoint)
            self.stub = app_pb2_grpc.AppManagerStub(self.channel)

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

    def _parse_app_info(self, app: app_pb2.AppInfo) -> AppInfo:
        return AppInfo(
            id=app.id,
            name=app.name,
            version=app.version,
            state=app.state,
            container_id=app.container_id,
            pid=app.pid,
            installed_at=app.installed_at,
            started_at=app.started_at,
            stopped_at=app.stopped_at,
            restart_count=app.restart_count,
            manifest_path=app.manifest_path,
            instance_path=app.instance_path
        )

    def _parse_app_stats(self, stats: app_pb2.AppStats) -> AppStats:
        return AppStats(
            app_id=stats.app_id,
            cpu_usage_percent=stats.cpu_usage_percent,
            memory_usage_bytes=stats.memory_usage_bytes,
            memory_limit_bytes=stats.memory_limit_bytes,
            thread_count=stats.thread_count,
            uptime_seconds=stats.uptime_seconds
        )

    def _parse_log_line(self, line: app_pb2.LogLine) -> LogLine:
        return LogLine(
            timestamp=line.timestamp,
            level=line.level,
            message=line.message
        )

    def register_web_url(self, path: str = "/") -> None:
        """Register a web access path for this app.

        After calling this method, the web console will show a "Visit App"
        button linking to ``http://{device_ip}:{inbound_port}{path}``.

        Requires the ``APP_ID`` environment variable to be set (injected
        automatically by the platform when the container starts).

        Args:
            path: Web page path, default ``"/"``
        """
        if self.stub is None:
            self.connect()
        app_id = os.getenv("APP_ID")
        if not app_id:
            raise RuntimeError("APP_ID env var not set — "
                               "this method must be called inside an app container")
        request = app_pb2.RegisterWebUrlRequest(app_id=app_id, path=path)
        response = self.stub.RegisterWebUrl(request)
        if not response.success:
            raise RuntimeError(f"RegisterWebUrl failed: {response.message}")

    def install_app(self, manifest_path: str, image_path: str) -> str:
        """
        Install an application from manifest and image

        Args:
            manifest_path: Path to app.yaml
            image_path: Path to container image tar

        Returns:
            app_id of installed application
        """
        if self.stub is None:
            self.connect()

        request = app_pb2.InstallRequest(
            manifest_path=manifest_path,
            image_path=image_path
        )
        response = self.stub.InstallApp(request)

        if not response.status.success:
            raise RuntimeError(f"Install failed: {response.status.message}")

        return response.app_id

    def start_app(self, app_id: str) -> None:
        """Start a stopped application"""
        if self.stub is None:
            self.connect()

        request = app_pb2.StartRequest(app_id=app_id)
        response = self.stub.StartApp(request)

        if not response.success:
            raise RuntimeError(f"Start failed: {response.message}")

    def stop_app(self, app_id: str, timeout_seconds: int = 30) -> None:
        """Stop a running application"""
        if self.stub is None:
            self.connect()

        request = app_pb2.StopRequest(
            app_id=app_id,
            timeout_seconds=timeout_seconds
        )
        response = self.stub.StopApp(request)

        if not response.success:
            raise RuntimeError(f"Stop failed: {response.message}")

    def uninstall_app(self, app_id: str, keep_logs: bool = True) -> None:
        """Uninstall an application"""
        if self.stub is None:
            self.connect()

        request = app_pb2.UninstallRequest(
            app_id=app_id,
            keep_logs=keep_logs
        )
        response = self.stub.UninstallApp(request)

        if not response.success:
            raise RuntimeError(f"Uninstall failed: {response.message}")

    def restart_app(self, app_id: str, timeout_seconds: int = 30) -> None:
        """Restart a running application (stop + start).

        This is a composite operation since the gRPC service does not expose
        a dedicated RestartApp RPC. It stops the app and then starts it again.

        Args:
            app_id: Application ID
            timeout_seconds: Seconds to wait for the app to stop (default: 30)
        """
        self.stop_app(app_id, timeout_seconds=timeout_seconds)
        self.start_app(app_id)

    def list_apps(self) -> List[AppInfo]:
        """List all installed applications"""
        if self.stub is None:
            self.connect()

        request = app_pb2.Empty()
        response = self.stub.ListApps(request)

        return [self._parse_app_info(app) for app in response.apps]

    def get_app(self, app_id: str) -> AppInfo:
        """Get application information"""
        if self.stub is None:
            self.connect()

        request = app_pb2.GetAppRequest(app_id=app_id)
        response = self.stub.GetApp(request)

        return self._parse_app_info(response)

    def get_app_stats(self, app_id: str) -> AppStats:
        """Get application runtime statistics"""
        if self.stub is None:
            self.connect()

        request = app_pb2.GetAppRequest(app_id=app_id)
        response = self.stub.GetAppStats(request)

        return self._parse_app_stats(response)

    def get_logs(self,
                 app_id: str,
                 max_lines: int = 100,
                 follow: bool = False) -> Iterator[LogLine]:
        """
        Get application logs

        Args:
            app_id: Application ID
            max_lines: Maximum number of lines to return (default: 100)
            follow: If True, stream logs continuously (default: False)

        Yields:
            LogLine objects

        Examples:

            .. code-block:: python

                # Get last 100 lines
                for line in app_client.get_logs("my_app", max_lines=100):
                    print(line)

                # Follow logs in real-time
                for line in app_client.get_logs("my_app", follow=True):
                    print(line)
        """
        if self.stub is None:
            self.connect()

        request = app_pb2.GetLogsRequest(
            app_id=app_id,
            max_lines=max_lines,
            follow=follow
        )

        for response in self.stub.GetAppLogs(request):
            yield self._parse_log_line(response)

    def get_logs_text(self,
                      app_id: str,
                      max_lines: int = 100,
                      follow: bool = False) -> Iterator[str]:
        """
        Get application logs as text lines

        Args:
            app_id: Application ID
            max_lines: Maximum number of lines to return (default: 100)
            follow: If True, stream logs continuously (default: False)

        Yields:
            Formatted log strings

        Examples:

            .. code-block:: python

                # Print logs
                for line in app_client.get_logs_text("my_app"):
                    print(line)
        """
        for log_line in self.get_logs(app_id, max_lines, follow):
            yield str(log_line)