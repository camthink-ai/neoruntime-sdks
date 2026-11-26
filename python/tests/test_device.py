"""
Tests for DeviceClient
"""

from unittest.mock import Mock, patch

import pytest

from neoruntime_ipc_sdk import DeviceClient, IrCutMode


class TestIrCutMode:
    def test_values(self):
        assert IrCutMode.AUTO.value == 0
        assert IrCutMode.DAY.value == 1
        assert IrCutMode.NIGHT.value == 2


class TestDeviceClient:
    def test_default_endpoint(self):
        client = DeviceClient()
        assert "device-control.sock" in client.endpoint
    
    def test_custom_endpoint(self):
        client = DeviceClient(endpoint="unix:///custom/device.sock")
        assert client.endpoint == "unix:///custom/device.sock"
    
    def test_context_manager(self):
        with DeviceClient() as client:
            assert client.channel is not None
    
    @patch('neoruntime_ipc_sdk.device.grpc.insecure_channel')
    def test_connect(self, mock_channel):
        client = DeviceClient()
        client.connect()
        
        assert client.channel is not None
        mock_channel.assert_called_once()


class TestDeviceClientLight:
    @patch('neoruntime_ipc_sdk.device.grpc.insecure_channel')
    def test_set_white_light(self, mock_channel):
        mock_stub = Mock()
        mock_stub.SetWhiteLight.return_value = Mock(success=True, message="")
        
        client = DeviceClient()
        client.stub = mock_stub
        
        client.set_white_light(80)
        
        mock_stub.SetWhiteLight.assert_called_once()
        call_args = mock_stub.SetWhiteLight.call_args
        assert call_args[0][0].level == 80
    
    @patch('neoruntime_ipc_sdk.device.grpc.insecure_channel')
    def test_set_ir_led(self, mock_channel):
        mock_stub = Mock()
        mock_stub.SetIrLed.return_value = Mock(success=True, message="")
        
        client = DeviceClient()
        client.stub = mock_stub
        
        client.set_ir_led(True)
        
        mock_stub.SetIrLed.assert_called_once()
        call_args = mock_stub.SetIrLed.call_args
        assert call_args[0][0].on is True
    
    @patch('neoruntime_ipc_sdk.device.grpc.insecure_channel')
    def test_set_ircut(self, mock_channel):
        mock_stub = Mock()
        mock_stub.SetIrCut.return_value = Mock(success=True, message="")
        
        client = DeviceClient()
        client.stub = mock_stub
        
        client.set_ircut(IrCutMode.NIGHT)
        
        mock_stub.SetIrCut.assert_called_once()
        call_args = mock_stub.SetIrCut.call_args
        assert call_args[0][0].mode == IrCutMode.NIGHT.value


class TestDeviceClientPTZ:
    @patch('neoruntime_ipc_sdk.device.grpc.insecure_channel')
    def test_pan_left(self, mock_channel):
        mock_stub = Mock()
        mock_stub.Pan.return_value = Mock(success=True, message="")
        
        client = DeviceClient()
        client.stub = mock_stub
        
        client.pan_left(speed=50)
        
        mock_stub.Pan.assert_called_once()
    
    @patch('neoruntime_ipc_sdk.device.grpc.insecure_channel')
    def test_tilt_up(self, mock_channel):
        mock_stub = Mock()
        mock_stub.Tilt.return_value = Mock(success=True, message="")
        
        client = DeviceClient()
        client.stub = mock_stub
        
        client.tilt_up(speed=30)
        
        mock_stub.Tilt.assert_called_once()
    
    @patch('neoruntime_ipc_sdk.device.grpc.insecure_channel')
    def test_ptz_stop(self, mock_channel):
        mock_stub = Mock()
        mock_stub.PTZStop.return_value = Mock(success=True, message="")
        
        client = DeviceClient()
        client.stub = mock_stub
        
        client.ptz_stop()
        
        mock_stub.PTZStop.assert_called_once()
    
    @patch('neoruntime_ipc_sdk.device.grpc.insecure_channel')
    def test_save_preset(self, mock_channel):
        mock_stub = Mock()
        mock_stub.SavePreset.return_value = Mock(success=True, message="")
        
        client = DeviceClient()
        client.stub = mock_stub
        
        client.save_preset(5)
        
        mock_stub.SavePreset.assert_called_once()
        call_args = mock_stub.SavePreset.call_args
        assert call_args[0][0].preset_id == 5
    
    @patch('neoruntime_ipc_sdk.device.grpc.insecure_channel')
    def test_call_preset(self, mock_channel):
        mock_stub = Mock()
        mock_stub.CallPreset.return_value = Mock(success=True, message="")
        
        client = DeviceClient()
        client.stub = mock_stub
        
        client.call_preset(3)
        
        mock_stub.CallPreset.assert_called_once()
        call_args = mock_stub.CallPreset.call_args
        assert call_args[0][0].preset_id == 3


class TestDeviceClientLens:
    @patch('neoruntime_ipc_sdk.device.grpc.insecure_channel')
    def test_zoom_in(self, mock_channel):
        mock_stub = Mock()
        mock_stub.Zoom.return_value = Mock(success=True, message="")
        
        client = DeviceClient()
        client.stub = mock_stub
        
        client.zoom_in(50)
        
        mock_stub.Zoom.assert_called_once()
        call_args = mock_stub.Zoom.call_args
        assert call_args[0][0].speed == 50
    
    @patch('neoruntime_ipc_sdk.device.grpc.insecure_channel')
    def test_zoom_out(self, mock_channel):
        mock_stub = Mock()
        mock_stub.Zoom.return_value = Mock(success=True, message="")
        
        client = DeviceClient()
        client.stub = mock_stub
        
        client.zoom_out(30)
        
        mock_stub.Zoom.assert_called_once()
        call_args = mock_stub.Zoom.call_args
        assert call_args[0][0].speed == -30
    
    @patch('neoruntime_ipc_sdk.device.grpc.insecure_channel')
    def test_focus_auto(self, mock_channel):
        mock_stub = Mock()
        mock_stub.SetAutofocus.return_value = Mock(success=True, message="")
        
        client = DeviceClient()
        client.stub = mock_stub
        
        client.focus_auto(True)
        
        mock_stub.SetAutofocus.assert_called_once()


class TestDeviceClientGPIO:
    @patch('neoruntime_ipc_sdk.device.grpc.insecure_channel')
    def test_gpio_set(self, mock_channel):
        mock_stub = Mock()
        mock_stub.GPIOWrite.return_value = Mock(success=True, message="")
        
        client = DeviceClient()
        client.stub = mock_stub
        
        client.gpio_set(pin=10, value=True)
        
        mock_stub.GPIOWrite.assert_called_once()
        call_args = mock_stub.GPIOWrite.call_args
        assert call_args[0][0].pin == 10
        assert call_args[0][0].value is True
    
    @patch('neoruntime_ipc_sdk.device.grpc.insecure_channel')
    def test_gpio_get(self, mock_channel):
        mock_stub = Mock()
        mock_stub.GPIORead.return_value = Mock(
            status=Mock(success=True, message=""),
            pin=10,
            value=True
        )
        
        client = DeviceClient()
        client.stub = mock_stub
        
        value = client.gpio_get(pin=10)
        
        assert value is True
        mock_stub.GPIORead.assert_called_once()

class TestDeviceClientStatus:
    """get_device_status against the *real* response proto shape.

    Regression (device run 2026-09-09): DeviceStatus on the wire carries
    ``ir_led_level`` (uint32); the client read a nonexistent
    ``ir_led_on`` field and raised AttributeError. Plain ``Mock``
    responses auto-create any attribute, so these tests feed genuine
    ``device_pb2.DeviceStatus`` messages.
    """

    @patch('neoruntime_ipc_sdk.device.grpc.insecure_channel')
    def test_get_device_status_maps_ir_led_level(self, mock_channel):
        from neoruntime_ipc_sdk.proto import device_pb2

        client = DeviceClient()
        mock_stub = Mock()
        mock_stub.GetDeviceStatus.return_value = device_pb2.DeviceStatus(
            ir_led_level=3)
        client.stub = mock_stub

        status = client.get_device_status()

        assert status.ir_led_on is True

    @patch('neoruntime_ipc_sdk.device.grpc.insecure_channel')
    def test_get_device_status_ir_led_off_when_level_zero(self, mock_channel):
        from neoruntime_ipc_sdk.proto import device_pb2

        client = DeviceClient()
        mock_stub = Mock()
        mock_stub.GetDeviceStatus.return_value = device_pb2.DeviceStatus(
            ir_led_level=0)
        client.stub = mock_stub

        assert client.get_device_status().ir_led_on is False


class TestDeviceClientRs485Rx:
    """subscribe_rs485_rx: typed wrapper + request passthrough."""

    @patch('neoruntime_ipc_sdk.device.grpc.insecure_channel')
    def test_subscribe_rs485_rx_maps_events_and_request(self, mock_channel):
        from neoruntime_ipc_sdk import Rs485RxEvent
        from neoruntime_ipc_sdk.proto import device_pb2

        mock_stub = Mock()
        mock_stub.SubscribeRs485Rx.return_value = iter([
            device_pb2.Rs485RxEvent(data=b"\x01\x02", timestamp_ns=11),
            device_pb2.Rs485RxEvent(data=b"abc", timestamp_ns=22),
        ])
        client = DeviceClient()
        client.stub = mock_stub

        events = list(client.subscribe_rs485_rx(queue_size=32, drop_old=False))

        assert events == [
            Rs485RxEvent(data=b"\x01\x02", timestamp_ns=11),
            Rs485RxEvent(data=b"abc", timestamp_ns=22),
        ]
        req = mock_stub.SubscribeRs485Rx.call_args[0][0]
        assert req.queue_size == 32
        assert req.drop_old is False

    @patch('neoruntime_ipc_sdk.device.grpc.insecure_channel')
    def test_subscribe_rs485_rx_defaults(self, mock_channel):
        from neoruntime_ipc_sdk.proto import device_pb2

        mock_stub = Mock()
        mock_stub.SubscribeRs485Rx.return_value = iter([])
        client = DeviceClient()
        client.stub = mock_stub

        list(client.subscribe_rs485_rx())

        req = mock_stub.SubscribeRs485Rx.call_args[0][0]
        assert req.queue_size == 16
        assert req.drop_old is True
