"""
Tests for InferenceClient
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from hailo_ipc_sdk import InferenceClient, BoundingBox, DetectedObject, InferenceResult


class TestBoundingBox:
    def test_to_xyxy(self):
        bbox = BoundingBox(x=0.1, y=0.2, width=0.3, height=0.4)
        xyxy = bbox.to_xyxy()
        assert abs(xyxy[0] - 0.1) < 1e-6
        assert abs(xyxy[1] - 0.2) < 1e-6
        assert abs(xyxy[2] - 0.4) < 1e-6
        assert abs(xyxy[3] - 0.6) < 1e-6
    
    def test_to_xywh(self):
        bbox = BoundingBox(x=0.1, y=0.2, width=0.3, height=0.4)
        xywh = bbox.to_xywh()
        assert xywh == (0.1, 0.2, 0.3, 0.4)


class TestDetectedObject:
    def test_creation(self):
        bbox = BoundingBox(x=0.1, y=0.2, width=0.3, height=0.4)
        obj = DetectedObject(
            label="person",
            score=0.95,
            bbox=bbox,
            class_id=1,
            track_id=100
        )
        assert obj.label == "person"
        assert obj.score == 0.95
        assert obj.bbox == bbox
        assert obj.class_id == 1
        assert obj.track_id == 100


class TestInferenceResult:
    def test_has_person_true(self):
        bbox = BoundingBox(x=0, y=0, width=1, height=1)
        objects = [
            DetectedObject(label="person", score=0.9, bbox=bbox),
            DetectedObject(label="car", score=0.8, bbox=bbox),
        ]
        result = InferenceResult(frame_sequence=1, timestamp_ns=1000, objects=objects)
        assert result.has_person() is True
    
    def test_has_person_false(self):
        bbox = BoundingBox(x=0, y=0, width=1, height=1)
        objects = [
            DetectedObject(label="car", score=0.8, bbox=bbox),
        ]
        result = InferenceResult(frame_sequence=1, timestamp_ns=1000, objects=objects)
        assert result.has_person() is False
    
    def test_count_by_label(self):
        bbox = BoundingBox(x=0, y=0, width=1, height=1)
        objects = [
            DetectedObject(label="person", score=0.9, bbox=bbox),
            DetectedObject(label="person", score=0.8, bbox=bbox),
            DetectedObject(label="car", score=0.7, bbox=bbox),
        ]
        result = InferenceResult(frame_sequence=1, timestamp_ns=1000, objects=objects)
        assert result.count_by_label("person") == 2
        assert result.count_by_label("car") == 1
        assert result.count_by_label("dog") == 0
    
    def test_get_objects_by_label(self):
        bbox = BoundingBox(x=0, y=0, width=1, height=1)
        obj1 = DetectedObject(label="person", score=0.9, bbox=bbox)
        obj2 = DetectedObject(label="person", score=0.8, bbox=bbox)
        obj3 = DetectedObject(label="car", score=0.7, bbox=bbox)
        objects = [obj1, obj2, obj3]
        
        result = InferenceResult(frame_sequence=1, timestamp_ns=1000, objects=objects)
        persons = result.get_objects_by_label("person")
        
        assert len(persons) == 2
        assert persons[0].score == 0.9
        assert persons[1].score == 0.8


class TestInferenceClient:
    def test_default_endpoint(self):
        client = InferenceClient()
        assert "ai-runtime.sock" in client.endpoint
    
    def test_custom_endpoint(self):
        client = InferenceClient(endpoint="unix:///custom/path.sock")
        assert client.endpoint == "unix:///custom/path.sock"
    
    def test_context_manager(self):
        with InferenceClient() as client:
            assert client.channel is not None
    
    @patch('hailo_ipc_sdk.inference.grpc.insecure_channel')
    def test_connect(self, mock_channel):
        client = InferenceClient()
        client.connect()
        
        assert client.channel is not None
        mock_channel.assert_called_once()
    
    def test_numpy_to_tensor(self):
        from hailo_ipc_sdk.proto import inference_pb2
        client = InferenceClient()
        arr = np.zeros((100, 100, 3), dtype=np.uint8)
        
        tensor = client._numpy_to_tensor(arr, "test")
        
        assert list(tensor.shape) == [100, 100, 3]
        assert tensor.dtype == inference_pb2.UINT8
    
    def test_dtype_conversion(self):
        client = InferenceClient()
        
        from hailo_ipc_sdk.proto import inference_pb2
        
        assert client._dtype_str_to_enum("uint8") == inference_pb2.UINT8
        assert client._dtype_str_to_enum("float32") == inference_pb2.FLOAT32
        assert client._dtype_str_to_enum("int32") == inference_pb2.INT32
        assert client._dtype_str_to_enum("unknown") == inference_pb2.FLOAT32