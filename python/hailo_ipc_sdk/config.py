"""
Configuration Management
"""

import os


class Config:
    """
    SDK Configuration

    Automatically reads configuration from environment variables
    """

    @staticmethod
    def get_app_id() -> str:
        """Get application ID"""
        return os.getenv("APP_ID", "unknown")

    @staticmethod
    def get_inference_endpoint() -> str:
        """Get AI Runtime endpoint"""
        return os.getenv("AI_RUNTIME_ENDPOINT", "unix:///run/aipc/ai-runtime.sock")

    @staticmethod
    def get_event_bus_endpoint() -> str:
        """Get Event Bus endpoint"""
        return os.getenv("EVENT_BUS_ENDPOINT", "unix:///run/aipc/event-bus.sock")

    @staticmethod
    def get_device_control_endpoint() -> str:
        """Get Device Control endpoint"""
        return os.getenv("DEVICE_CONTROL_ENDPOINT", "unix:///run/aipc/device-control.sock")

    @staticmethod
    def get_shm_base_path() -> str:
        """Get base path for shared-memory IPC sockets"""
        return os.getenv("SHM_BASE_PATH", "/run/aipc/shm")


    @staticmethod
    def get_camera_control_endpoint() -> str:
        """Get Camera Control gRPC endpoint"""
        return os.getenv("CAMERA_CONTROL_ENDPOINT", "unix:///run/aipc/camera-control.sock")

    @staticmethod
    def get_app_manager_endpoint() -> str:
        """Get App Manager gRPC endpoint"""
        return os.getenv("APP_MANAGER_ENDPOINT", "unix:///run/aipc/app-manager.sock")

    @staticmethod
    def get_encoded_socket_dir() -> str:
        """Get directory containing EncodedPublisher UDS sockets"""
        return os.getenv("ENCODED_SOCKET_DIR", "/run/aipc/encoded")

    @staticmethod
    def get_host_prefix() -> str:
        """Get host install prefix (canonical root: /data/aipc).

        The container sees /opt/aipc via volume mounts, but ai-runtime on the
        host resolves paths under the real install root. AIPC_HOST_PREFIX
        overrides for non-standard deployments (e.g. /opt/aipc legacy)."""
        return os.getenv("AIPC_HOST_PREFIX", "/data/aipc")

    @staticmethod
    def translate_path_to_host(container_path: str) -> str:
        """Translate a container-internal path to the host filesystem path.

        The container sees /opt/aipc via volume mounts even when the platform
        is installed under the canonical /data/aipc host root; ai-runtime on
        the host needs the actual host path. This function translates container
        paths to host paths using AIPC_HOST_PREFIX (default /data/aipc).

        Also handles /data/ paths for devices where the platform is
        installed under /data/ instead of /opt/.
        """
        host_prefix = Config.get_host_prefix()
        if host_prefix and container_path.startswith("/opt/aipc"):
            return container_path.replace("/opt/aipc", host_prefix, 1)
        if host_prefix and container_path.startswith("/data/aipc"):
            return container_path.replace("/data/aipc", host_prefix, 1)
        return container_path

    @staticmethod
    def is_debug() -> bool:
        """Check if debug mode is enabled"""
        return os.getenv("DEBUG", "0") == "1"

    @staticmethod
    def get_log_level() -> str:
        """Get log level"""
        return os.getenv("LOG_LEVEL", "INFO")
