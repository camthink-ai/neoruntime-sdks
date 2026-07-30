#!/usr/bin/env python3
"""
事件订阅示例应用

功能：
- 订阅多个事件主题
- 事件过滤与处理
- 设备联动
"""

import time
import signal
import threading
from hailo_ipc_sdk import EventClient, DeviceClient, Config, Event


class EventSubscriberApp:
    def __init__(self):
        self.running = True
        self.app_id = Config.get_app_id()
        self.debug = Config.is_debug()
        
        self.events = EventClient()
        self.device = DeviceClient()
        
        self.subscriptions = []
        
        print(f"[{self.app_id}] Event Subscriber App initialized")
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print(f"\n[{self.app_id}] Shutting down...")
        self.running = False
        self.events.close()
    
    def run(self):
        print(f"[{self.app_id}] Starting event subscriptions...")
        
        self._subscribe_topics()
        
        while self.running:
            time.sleep(1)
        
        self._cleanup()
    
    def _subscribe_topics(self):
        topics = [
            ("model/+/detections", self._on_detection),
            ("app/+/alert", self._on_alert),
            ("system/device/#", self._on_system_event),
        ]
        
        for topic, callback in topics:
            try:
                thread = self.events.on_event(topic, callback)
                self.subscriptions.append(thread)
                print(f"[{self.app_id}] Subscribed to: {topic}")
            except Exception as e:
                print(f"[{self.app_id}] Failed to subscribe {topic}: {e}")
    
    def _on_detection(self, event: Event):
        print(f"[{self.app_id}] Detection event: {event.topic}")
        
        if self.debug:
            print(f"  Payload: {event.payload}")
        
        if "person" in str(event.payload).lower():
            self._on_person_detection(event)
    
    def _on_person_detection(self, event: Event):
        print(f"[{self.app_id}] Person detected!")
        
        try:
            self.device.set_white_light(80)
        except Exception as e:
            print(f"[{self.app_id}] Failed to control device: {e}")
    
    def _on_alert(self, event: Event):
        print(f"[{self.app_id}] Alert received: {event.topic}")
        print(f"  Source: {event.source}")
        print(f"  Data: {event.payload}")
        
        self.events.publish(f"app/{self.app_id}/alert_ack", {
            "original_topic": event.topic,
            "original_event_id": event.event_id,
            "acknowledged": True
        })
    
    def _on_system_event(self, event: Event):
        if self.debug:
            print(f"[{self.app_id}] System event: {event.topic}")
    
    def _cleanup(self):
        self.events.close()
        self.device.close()
        print(f"[{self.app_id}] Cleanup complete")


def main():
    app = EventSubscriberApp()
    app.run()


if __name__ == "__main__":
    main()