"""
Tests for CameraClient, ISPConfig, TransformConfig
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from hailo_ipc_sdk import CameraClient, ISPConfig, TransformConfig


class TestISPConfig:
    def test_defaults(self):
        cfg = ISPConfig()
        assert cfg.brightness == -1
        assert cfg.contrast == -1
        assert cfg.saturation == -1
        assert cfg.sharpness == -1
        assert cfg.manual_mode is None
        assert cfg.auto_exposure is None
        assert cfg.backlight == -1
        assert cfg.exposure_time_us == -1
        assert cfg.gain == -1
        assert cfg.noise_reduction == -1
        assert cfg.wdr_value == -1
        assert cfg.powerline_freq == -1
        assert cfg.awb_index == -1

    def test_custom_values(self):
        cfg = ISPConfig(brightness=60, contrast=50, manual_mode=True)
        assert cfg.brightness == 60
        assert cfg.contrast == 50
        assert cfg.manual_mode is True

    def test_no_change_semantics(self):
        """-1 means 'no change' — fields with -1 are skipped in proto request."""
        cfg = ISPConfig(brightness=80)
        assert cfg.brightness == 80  # explicitly set
        assert cfg.contrast == -1    # no change


class TestTransformConfig:
    def test_defaults(self):
        cfg = TransformConfig()
        assert cfg.rotation == 0
        assert cfg.flip == 0
        assert cfg.dewarp is False
        assert cfg.grayscale is False

    def test_custom_values(self):
        cfg = TransformConfig(rotation=1, flip=2, dewarp=True, grayscale=True)
        assert cfg.rotation == 1
        assert cfg.flip == 2
        assert cfg.dewarp is True
        assert cfg.grayscale is True


class TestCameraClient:
    def test_default_endpoint(self):
        client = CameraClient()
        assert "camera-control" in client.endpoint

    def test_custom_endpoint(self):
        client = CameraClient(endpoint="unix:///custom/camera.sock")
        assert client.endpoint == "unix:///custom/camera.sock"

    def test_context_manager(self):
        with CameraClient() as client:
            assert client._channel is not None


class TestCameraClientISP:
    @patch('hailo_ipc_sdk.camera.grpc.insecure_channel')
    def test_set_isp_with_kwargs(self, mock_channel):
        mock_stub = Mock()
        mock_resp = Mock()
        mock_resp.status = Mock(success=True, message="")
        mock_stub.UpdateISPSettings.return_value = mock_resp

        client = CameraClient()
        client._stub = mock_stub

        client.set_isp(brightness=60, contrast=50)

        mock_stub.UpdateISPSettings.assert_called_once()
        call_args = mock_stub.UpdateISPSettings.call_args
        req = call_args[0][0]
        assert req.brightness == 60
        assert req.contrast == 50

    @patch('hailo_ipc_sdk.camera.grpc.insecure_channel')
    def test_set_isp_skips_no_change_fields(self, mock_channel):
        mock_stub = Mock()
        mock_resp = Mock()
        mock_resp.status = Mock(success=True, message="")
        mock_stub.UpdateISPSettings.return_value = mock_resp

        client = CameraClient()
        client._stub = mock_stub

        # Only set brightness, others should be -1 and skipped
        client.set_isp(brightness=80)

        call_args = mock_stub.UpdateISPSettings.call_args
        req = call_args[0][0]
        assert req.brightness == 80
        # Fields with -1 default are not set on proto (protobuf default=0)

    @patch('hailo_ipc_sdk.camera.grpc.insecure_channel')
    def test_set_isp_zero_value_is_valid(self, mock_channel):
        """Zero values are legitimate (brightness=0, noise_reduction=0).
        Proto optional means the field IS set, even when value=0."""
        mock_stub = Mock()
        mock_resp = Mock()
        mock_resp.status = Mock(success=True, message="")
        mock_stub.UpdateISPSettings.return_value = mock_resp

        client = CameraClient()
        client._stub = mock_stub

        # brightness=0 and noise_reduction=0 are valid values
        client.set_isp(brightness=0, noise_reduction=0)

        call_args = mock_stub.UpdateISPSettings.call_args
        req = call_args[0][0]
        assert req.brightness == 0
        assert req.noise_reduction == 0

    @patch('hailo_ipc_sdk.camera.grpc.insecure_channel')
    def test_set_isp_manual_mode_false_is_valid(self, mock_channel):
        """manual_mode=False must be sent, not skipped.
        Proto optional distinguishes 'not set' (None) from 'set to False'."""
        mock_stub = Mock()
        mock_resp = Mock()
        mock_resp.status = Mock(success=True, message="")
        mock_stub.UpdateISPSettings.return_value = mock_resp

        client = CameraClient()
        client._stub = mock_stub

        client.set_isp(manual_mode=False)

        call_args = mock_stub.UpdateISPSettings.call_args
        req = call_args[0][0]
        assert req.manual_mode is False

    @patch('hailo_ipc_sdk.camera.grpc.insecure_channel')
    def test_set_isp_partial_update_merges(self, mock_channel):
        """Partial update: only changed fields sent; others stay at -1 (no change).
        Combined with proto optional, daemon only applies explicitly set fields."""
        mock_stub = Mock()
        mock_resp = Mock()
        mock_resp.status = Mock(success=True, message="")
        mock_stub.UpdateISPSettings.return_value = mock_resp

        client = CameraClient()
        client._stub = mock_stub

        # Send only brightness and contrast; all other fields default to -1
        cfg = ISPConfig(brightness=70, contrast=30)
        client.set_isp(config=cfg)

        call_args = mock_stub.UpdateISPSettings.call_args
        req = call_args[0][0]
        assert req.brightness == 70
        assert req.contrast == 30

    @patch('hailo_ipc_sdk.camera.grpc.insecure_channel')
    def test_get_isp(self, mock_channel):
        mock_stub = Mock()

        # Build a mock response with .success and .current attributes
        mock_current = Mock()
        mock_current.brightness = 50
        mock_current.contrast = 60
        mock_current.saturation = 70
        mock_current.sharpness = 80
        mock_current.manual_mode = Mock()
        mock_current.HasField = lambda name: name == "manual_mode"
        mock_current.auto_exposure = Mock()
        mock_current.HasField = lambda name: name in ("manual_mode", "auto_exposure")
        mock_current.backlight = 40
        mock_current.exposure_time_us = 10000
        mock_current.gain = 200
        mock_current.noise_reduction = 30
        mock_current.wdr_value = 50
        mock_current.powerline_freq = 1
        mock_current.awb_index = 5

        mock_resp = Mock()
        mock_resp.success = True
        mock_resp.message = ""
        mock_resp.current = mock_current
        mock_stub.GetISPConfig.return_value = mock_resp

        client = CameraClient()
        client._stub = mock_stub

        isp = client.get_isp()
        assert isinstance(isp, ISPConfig)
        assert isp.brightness == 50
        assert isp.contrast == 60
        assert isp.powerline_freq == 1

    @patch('hailo_ipc_sdk.camera.grpc.insecure_channel')
    def test_get_isp_optional_fields_unset(self, mock_channel):
        """When proto optional fields are NOT set, HasField returns False
        and get_isp() should map them to None (not False)."""
        mock_stub = Mock()

        mock_current = Mock()
        mock_current.brightness = 50
        mock_current.contrast = 60
        mock_current.saturation = 70
        mock_current.sharpness = 80
        mock_current.manual_mode = False  # default value but NOT set
        mock_current.auto_exposure = True  # default value but NOT set
        mock_current.HasField = lambda name: False  # no optional field is set
        mock_current.backlight = 40
        mock_current.exposure_time_us = 10000
        mock_current.gain = 200
        mock_current.noise_reduction = 30
        mock_current.wdr_value = 50
        mock_current.powerline_freq = 1
        mock_current.awb_index = 5

        mock_resp = Mock()
        mock_resp.success = True
        mock_resp.message = ""
        mock_resp.current = mock_current
        mock_stub.GetISPConfig.return_value = mock_resp

        client = CameraClient()
        client._stub = mock_stub

        isp = client.get_isp()
        assert isp.manual_mode is None  # HasField("manual_mode") = False → None
        assert isp.auto_exposure is None  # HasField("auto_exposure") = False → None
        assert isp.brightness == 50  # non-optional fields always have values


class TestCameraClientTransform:
    @patch('hailo_ipc_sdk.camera.grpc.insecure_channel')
    def test_get_transform(self, mock_channel):
        mock_stub = Mock()
        mock_resp = Mock()
        mock_resp.rotation = 1
        mock_resp.flip = 2
        mock_resp.dewarp = True
        mock_resp.grayscale = False
        mock_stub.GetTransformConfig.return_value = mock_resp

        client = CameraClient()
        client._stub = mock_stub

        transform = client.get_transform()
        assert isinstance(transform, TransformConfig)
        assert transform.rotation == 1
        assert transform.flip == 2
        assert transform.dewarp is True
        assert transform.grayscale is False

    @patch('hailo_ipc_sdk.camera.grpc.insecure_channel')
    def test_set_transform(self, mock_channel):
        mock_stub = Mock()
        mock_resp = Mock()
        mock_resp.status = Mock(success=True, message="")
        mock_stub.SetTransformConfig.return_value = mock_resp

        client = CameraClient()
        client._stub = mock_stub

        cfg = TransformConfig(rotation=2, flip=3, dewarp=True, grayscale=False)
        client.set_transform(cfg)

        mock_stub.SetTransformConfig.assert_called_once()
        call_args = mock_stub.SetTransformConfig.call_args
        req = call_args[0][0]
        assert req.rotation == 2
        assert req.flip == 3
        assert req.dewarp is True
        assert req.grayscale is False


class TestCameraClientEncoder:
    @patch('hailo_ipc_sdk.camera.grpc.insecure_channel')
    def test_set_encoder(self, mock_channel):
        mock_stub = Mock()
        mock_resp = Mock()
        mock_resp.status = Mock(success=True, message="")
        mock_stub.UpdateEncoderConfig.return_value = mock_resp

        client = CameraClient()
        client._stub = mock_stub

        client.set_encoder("main", bitrate_bps=8000000, gop=30)

        mock_stub.UpdateEncoderConfig.assert_called_once()
        call_args = mock_stub.UpdateEncoderConfig.call_args
        req = call_args[0][0]
        assert req.stream_name == "main"
        assert req.bitrate_bps == 8000000
        assert req.gop == 30