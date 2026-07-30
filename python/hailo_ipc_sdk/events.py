"""
Event Bus Client
"""

import json
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterator, List, Optional

import grpc

from .proto import event_pb2, event_pb2_grpc


def _json_default(o: Any) -> Any:
    """Coerce numpy scalars/arrays to native Python for JSON serialization.

    ML pipeline payloads routinely carry numpy.float32 (confidences, bbox
    coords); json.dumps cannot serialize them and raises TypeError, which
    crashes publish()/publish_batch() callers. Duck-typed so the SDK does
    not hard-depend on numpy.
    """
    if hasattr(o, "item"):
        try:
            return o.item()  # np.float32/np.int64 -> python scalar
        except Exception:
            pass
    if hasattr(o, "tolist"):
        return o.tolist()  # np.ndarray -> list
    raise TypeError(
        f"Object of type {o.__class__.__name__} is not JSON serializable",
    )


@dataclass
class Event:
    topic: str
    payload: Dict[str, Any]
    source: str = field(default="")
    event_id: str = ""
    timestamp_ns: int = 0
    metadata: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.source:
            self.source = self._get_app_id()
        if not self.timestamp_ns:
            self.timestamp_ns = self._get_timestamp()
    
    @staticmethod
    def _get_app_id() -> str:
        import os
        return os.getenv("APP_ID", "unknown")
    
    @staticmethod
    def _get_timestamp() -> int:
        return int(time.time() * 1e9)
    
    def to_json(self) -> str:
        return json.dumps(self.payload, default=_json_default)
    
    @classmethod
    def from_proto(cls, msg: event_pb2.Event) -> "Event":
        payload = {}
        if msg.payload:
            try:
                payload = json.loads(msg.payload.decode('utf-8'))
            except json.JSONDecodeError:
                payload = {"raw": msg.payload.decode('utf-8', errors='replace')}
        
        return cls(
            topic=msg.topic,
            payload=payload,
            source=msg.source,
            event_id=msg.event_id,
            timestamp_ns=msg.timestamp_ns,
            metadata=dict(msg.metadata)
        )


@dataclass
class TopicInfo:
    topic: str
    subscriber_count: int
    total_messages: int
    last_message_ts: int


class EventClient:
    """
    Event Bus Client

    Usage::

        events = EventClient()

        events.publish("app/alert", {"type": "person_detected"})

        for event in events.subscribe("model/*/detections"):
            print(f"Received: {event.topic}")
    """
    
    def __init__(self, endpoint: Optional[str] = None):
        if endpoint is None:
            endpoint = self._get_default_endpoint()
        
        self.endpoint = endpoint
        self.channel: Optional[grpc.Channel] = None
        self.stub: Optional[event_pb2_grpc.EventBusStub] = None
        self.app_id = self._get_app_id()
        self._subscriptions: List[threading.Thread] = []
        self._running = True
    
    def _get_default_endpoint(self) -> str:
        import os
        return os.getenv("EVENT_BUS_ENDPOINT", "unix:///run/aipc/event-bus.sock")
    
    def _get_app_id(self) -> str:
        import os
        return os.getenv("APP_ID", "unknown")
    
    def connect(self) -> None:
        if self.channel is None:
            self.channel = grpc.insecure_channel(self.endpoint)
            self.stub = event_pb2_grpc.EventBusStub(self.channel)

    @property
    def connected(self) -> bool:
        return self.channel is not None
    
    def close(self) -> None:
        self._running = False
        for t in self._subscriptions:
            if t.is_alive():
                t.join(timeout=1.0)
        
        if self.channel:
            self.channel.close()
            self.channel = None
            self.stub = None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def publish(self, 
                topic: str, 
                payload: Dict[str, Any], 
                persistent: bool = False,
                ttl_ms: Optional[int] = None,
                metadata: Optional[Dict[str, str]] = None) -> str:
        if self.stub is None:
            self.connect()
        
        event = event_pb2.Event(
            topic=topic,
            timestamp_ns=int(time.time() * 1e9),
            source=self.app_id,
            payload=json.dumps(payload, default=_json_default).encode('utf-8'),
            payload_type="json"
        )
        
        if metadata:
            event.metadata.update(metadata)
        
        request = event_pb2.PublishRequest(
            event=event,
            persistent=persistent,
            ttl_ms=ttl_ms or 0
        )
        
        response = self.stub.Publish(request)
        
        if not response.status.success:
            raise RuntimeError(f"Publish failed: {response.status.message}")
        
        return response.event_id
    
    def publish_batch(self, events: List[Dict[str, Any]], persistent: bool = False) -> None:
        if self.stub is None:
            self.connect()
        
        def generate_requests():
            for e in events:
                event = event_pb2.Event(
                    topic=e["topic"],
                    timestamp_ns=int(time.time() * 1e9),
                    source=self.app_id,
                    payload=json.dumps(e["payload"], default=_json_default).encode('utf-8'),
                    payload_type="json"
                )
                yield event_pb2.PublishRequest(event=event, persistent=persistent)
        
        response = self.stub.PublishBatch(generate_requests())
        
        if not response.success:
            raise RuntimeError(f"Batch publish failed: {response.message}")
    
    def subscribe(self, 
                  topic: str,
                  filters: Optional[Dict[str, str]] = None,
                  queue_size: int = 100,
                  drop_old: bool = True) -> Iterator[Event]:
        if self.stub is None:
            self.connect()
        
        request = event_pb2.SubscribeRequest(
            topic=topic,
            subscriber_id=self.app_id,
            queue_size=queue_size,
            drop_old=drop_old
        )
        
        if filters:
            request.filters.update(filters)
        
        for event_msg in self.stub.Subscribe(request):
            yield Event.from_proto(event_msg)
    
    def on_event(self, 
                 topic: str,
                 callback: Callable[[Event], None],
                 filters: Optional[Dict[str, str]] = None) -> threading.Thread:
        def _subscribe_thread():
            try:
                for event in self.subscribe(topic, filters):
                    if not self._running:
                        break
                    try:
                        callback(event)
                    except Exception:
                        pass
            except grpc.RpcError:
                pass
        
        thread = threading.Thread(target=_subscribe_thread, daemon=True)
        thread.start()
        self._subscriptions.append(thread)
        return thread
    
    def unsubscribe(self, topic: str) -> None:
        if self.stub is None:
            self.connect()
        
        request = event_pb2.SubscribeRequest(topic=topic, subscriber_id=self.app_id)
        self.stub.Unsubscribe(request)
    
    def list_topics(self) -> List[TopicInfo]:
        if self.stub is None:
            self.connect()
        
        response = self.stub.ListTopics(event_pb2.Empty())
        
        return [
            TopicInfo(
                topic=t.topic,
                subscriber_count=t.subscriber_count,
                total_messages=t.total_messages,
                last_message_ts=t.last_message_ts
            )
            for t in response.topics
        ]
    
    def get_topic_info(self, topic: str) -> Optional[TopicInfo]:
        if self.stub is None:
            self.connect()
        
        request = event_pb2.TopicInfo(topic=topic)
        response = self.stub.GetTopicInfo(request)
        
        if not response.topic:
            return None
        
        return TopicInfo(
            topic=response.topic,
            subscriber_count=response.subscriber_count,
            total_messages=response.total_messages,
            last_message_ts=response.last_message_ts
        )
    
    def get_stats(self) -> Dict[str, Any]:
        if self.stub is None:
            self.connect()
        
        response = self.stub.GetStats(event_pb2.Empty())
        
        return {
            "total_subscribers": response.total_subscribers,
            "total_topics": response.total_topics,
            "uptime_ms": response.uptime_ms,
            "topic_stats": [
                {
                    "topic": s.topic,
                    "published_count": s.published_count,
                    "delivered_count": s.delivered_count,
                    "dropped_count": s.dropped_count,
                    "avg_latency_us": s.avg_latency_us
                }
                for s in response.topic_stats
            ]
        }
    
    def get_topic_stats(self, topic: str) -> Dict[str, Any]:
        if self.stub is None:
            self.connect()
        
        request = event_pb2.TopicInfo(topic=topic)
        response = self.stub.GetTopicStats(request)
        
        return {
            "topic": response.topic,
            "published_count": response.published_count,
            "delivered_count": response.delivered_count,
            "dropped_count": response.dropped_count,
            "avg_latency_us": response.avg_latency_us
        }