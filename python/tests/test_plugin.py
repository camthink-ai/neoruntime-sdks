"""
Tests for Plugin SDK
"""

import pytest
import tempfile
import json
import os
from pathlib import Path

from hailo_ipc_sdk import PluginDiscovery, PluginServer, PluginEndpoint


class TestPluginEndpoint:
    def test_creation(self):
        ep = PluginEndpoint(
            app_id="test-app",
            capability_id="rtsp-server",
            version="1.0.0",
            transport="grpc",
            socket_path="/run/aipc/plugins/test.sock",
            state="running"
        )
        assert ep.app_id == "test-app"
        assert ep.capability_id == "rtsp-server"
        assert ep.is_available is True
    
    def test_is_available(self):
        ep_running = PluginEndpoint(
            app_id="test",
            capability_id="test",
            version="1.0",
            transport="grpc",
            state="running"
        )
        assert ep_running.is_available is True
        
        ep_stopped = PluginEndpoint(
            app_id="test",
            capability_id="test",
            version="1.0",
            transport="grpc",
            state="stopped"
        )
        assert ep_stopped.is_available is False


class TestPluginDiscovery:
    def test_empty_discovery(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            discovery = PluginDiscovery(discovery_dir=tmpdir)
            plugins = discovery.list_plugins()
            assert plugins == {}
    
    def test_discovery_with_plugins(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            discovery_file = Path(tmpdir) / "discovery.json"
            discovery_data = {
                "plugins": {
                    "rtsp-app": {
                        "app_id": "rtsp-app",
                        "state": "running",
                        "capabilities": [
                            {
                                "id": "rtsp-server",
                                "version": "1.0.0",
                                "transport": "grpc",
                                "grpc": {
                                    "socket_path": "/run/aipc/plugins/rtsp-app.sock",
                                    "service": "RTSPService"
                                }
                            }
                        ]
                    }
                }
            }
            
            discovery_file.write_text(json.dumps(discovery_data))
            
            discovery = PluginDiscovery(discovery_dir=tmpdir)
            
            plugins = discovery.list_plugins()
            assert "rtsp-app" in plugins
            
            capabilities = discovery.list_capabilities()
            assert "rtsp-server" in capabilities
            
            ep = discovery.get("rtsp-server")
            assert ep is not None
            assert ep.app_id == "rtsp-app"
            assert ep.capability_id == "rtsp-server"
    
    def test_get_nonexistent_capability(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            discovery = PluginDiscovery(discovery_dir=tmpdir)
            ep = discovery.get("nonexistent")
            assert ep is None


class TestPluginServer:
    def test_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            server = PluginServer("test-plugin", socket_dir=tmpdir)
            assert server.plugin_id == "test-plugin"
            assert server.socket_path == os.path.join(tmpdir, "test-plugin.sock")
    
    def test_create_server(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            server = PluginServer("test-plugin", socket_dir=tmpdir)
            grpc_server = server.create_server()
            assert grpc_server is not None