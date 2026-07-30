"""
Tests for Config
"""

import os
import pytest

from hailo_ipc_sdk import Config


class TestConfig:
    def test_get_app_id_default(self):
        if "APP_ID" in os.environ:
            del os.environ["APP_ID"]
        assert Config.get_app_id() == "unknown"
    
    def test_get_app_id_from_env(self):
        os.environ["APP_ID"] = "my-test-app"
        assert Config.get_app_id() == "my-test-app"
        del os.environ["APP_ID"]
    
    def test_get_inference_endpoint_default(self):
        if "AI_RUNTIME_ENDPOINT" in os.environ:
            del os.environ["AI_RUNTIME_ENDPOINT"]
        assert Config.get_inference_endpoint() == "unix:///run/aipc/ai-runtime.sock"
    
    def test_get_inference_endpoint_from_env(self):
        os.environ["AI_RUNTIME_ENDPOINT"] = "unix:///custom/ai-runtime.sock"
        assert Config.get_inference_endpoint() == "unix:///custom/ai-runtime.sock"
        del os.environ["AI_RUNTIME_ENDPOINT"]
    
    def test_get_event_bus_endpoint_default(self):
        if "EVENT_BUS_ENDPOINT" in os.environ:
            del os.environ["EVENT_BUS_ENDPOINT"]
        assert Config.get_event_bus_endpoint() == "unix:///run/aipc/event-bus.sock"
    
    def test_get_device_control_endpoint_default(self):
        if "DEVICE_CONTROL_ENDPOINT" in os.environ:
            del os.environ["DEVICE_CONTROL_ENDPOINT"]
        assert Config.get_device_control_endpoint() == "unix:///run/aipc/device-control.sock"
    
    def test_get_shm_base_path_default(self):
        if "SHM_BASE_PATH" in os.environ:
            del os.environ["SHM_BASE_PATH"]
        assert Config.get_shm_base_path() == "/run/aipc/shm"
    
    def test_is_debug_default(self):
        if "DEBUG" in os.environ:
            del os.environ["DEBUG"]
        assert Config.is_debug() is False
    
    def test_is_debug_true(self):
        os.environ["DEBUG"] = "1"
        assert Config.is_debug() is True
        del os.environ["DEBUG"]
    
    def test_get_log_level_default(self):
        if "LOG_LEVEL" in os.environ:
            del os.environ["LOG_LEVEL"]
        assert Config.get_log_level() == "INFO"
    
    def test_get_log_level_from_env(self):
        os.environ["LOG_LEVEL"] = "DEBUG"
        assert Config.get_log_level() == "DEBUG"
        del os.environ["LOG_LEVEL"]