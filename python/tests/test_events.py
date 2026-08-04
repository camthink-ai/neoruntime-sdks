"""
Tests for EventClient
"""

import pytest
from unittest.mock import Mock, patch

from hailo_ipc_sdk import EventClient, Event, TopicInfo


class TestEvent:
    def test_creation(self):
        event = Event(
            topic="app/alert",
            payload={"type": "test"},
            source="test-app",
            event_id="123",
            timestamp_ns=1000000
        )
        assert event.topic == "app/alert"
        assert event.payload == {"type": "test"}
        assert event.source == "test-app"
    
    def test_to_json(self):
        event = Event(
            topic="test",
            payload={"key": "value"}
        )
        json_str = event.to_json()
        assert '{"key": "value"}' in json_str
    
    def test_default_source_from_env(self):
        import os
        os.environ["APP_ID"] = "my-app"
        event = Event(topic="test", payload={})
        assert event.source == "my-app"
        del os.environ["APP_ID"]


class TestTopicInfo:
    def test_creation(self):
        info = TopicInfo(
            topic="test/topic",
            subscriber_count=5,
            total_messages=100,
            last_message_ts=1000000
        )
        assert info.topic == "test/topic"
        assert info.subscriber_count == 5
        assert info.total_messages == 100


class TestEventClient:
    def test_default_endpoint(self):
        client = EventClient()
        assert "event-bus.sock" in client.endpoint
    
    def test_custom_endpoint(self):
        client = EventClient(endpoint="unix:///custom/event.sock")
        assert client.endpoint == "unix:///custom/event.sock"
    
    def test_context_manager(self):
        with EventClient() as client:
            assert client.channel is not None
    
    @patch('hailo_ipc_sdk.events.grpc.insecure_channel')
    def test_connect(self, mock_channel):
        client = EventClient()
        client.connect()
        
        assert client.channel is not None
        mock_channel.assert_called_once()


class TestEventClientPublish:
    @patch('hailo_ipc_sdk.events.grpc.insecure_channel')
    def test_publish_success(self, mock_channel):
        mock_stub = Mock()
        mock_stub.Publish.return_value = Mock(
            status=Mock(success=True, message=""),
            event_id="evt-123"
        )
        
        client = EventClient()
        client.stub = mock_stub
        
        event_id = client.publish("test/topic", {"key": "value"})
        
        assert event_id == "evt-123"
        mock_stub.Publish.assert_called_once()
    
    @patch('hailo_ipc_sdk.events.grpc.insecure_channel')
    def test_publish_with_metadata(self, mock_channel):
        mock_stub = Mock()
        mock_stub.Publish.return_value = Mock(
            status=Mock(success=True, message=""),
            event_id="evt-123"
        )
        
        client = EventClient()
        client.stub = mock_stub
        
        event_id = client.publish(
            "test/topic",
            {"key": "value"},
            persistent=True,
            ttl_ms=60000,
            metadata={"priority": "high"}
        )
        
        assert event_id == "evt-123"
        call_args = mock_stub.Publish.call_args
        request = call_args[0][0]
        assert request.persistent is True
        assert request.ttl_ms == 60000