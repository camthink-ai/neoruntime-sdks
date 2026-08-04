#!/usr/bin/env python3
"""
人形检测示例应用

功能：
- 订阅视频流推理结果
- 检测到人时发布事件
- 联动设备控制（可选）
"""

import time
import signal
import sys
from hailo_ipc_sdk import (
    InferenceClient, EventClient, DeviceClient, 
    Config, BoundingBox, DetectedObject, InferenceResult
)


class PersonDetectionApp:
    def __init__(self):
        self.running = True
        self.app_id = Config.get_app_id()
        self.debug = Config.is_debug()
        
        self.inference = InferenceClient()
        self.events = EventClient()
        self.device = None
        self.media = None
        
        print(f"[{self.app_id}] Person Detection App initialized")
        print(f"[{self.app_id}] AI Runtime: {Config.get_inference_endpoint()}")
        print(f"[{self.app_id}] Event Bus: {Config.get_event_bus_endpoint()}")
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print(f"\n[{self.app_id}] Received signal {signum}, shutting down...")
        self.running = False
    
    def run(self):
        print(f"[{self.app_id}] Starting person detection...")
        
        try:
            for frame_seq, result in self.inference.subscribe(
                stream="cam0_main",
                model="person_v1",
                fps=10
            ):
                if not self.running:
                    break
                
                self._process_result(frame_seq, result)
                
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"[{self.app_id}] Error: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
        finally:
            self._cleanup()
    
    def _process_result(self, frame_seq: int, result: InferenceResult):
        person_count = result.count_by_label("person")
        
        if person_count > 0:
            print(f"[Frame {frame_seq}] Detected {person_count} person(s)")
            
            for obj in result.get_objects_by_label("person"):
                if self.debug:
                    bbox = obj.bbox
                    print(f"  - confidence: {obj.score:.2f}")
                    print(f"    position: ({bbox.x:.2f}, {bbox.y:.2f})")
                    print(f"    size: {bbox.width:.2f} x {bbox.height:.2f}")
            
            self.events.publish(f"app/{self.app_id}/person_detected", {
                "frame_sequence": frame_seq,
                "timestamp_ns": result.timestamp_ns,
                "person_count": person_count,
                "objects": [
                    {
                        "confidence": obj.score,
                        "bbox": [obj.bbox.x, obj.bbox.y, obj.bbox.width, obj.bbox.height]
                    }
                    for obj in result.get_objects_by_label("person")
                ]
            })
            
            self._on_person_detected(result)
    
    def _on_person_detected(self, result: InferenceResult):
        pass
    
    def _cleanup(self):
        print(f"[{self.app_id}] Cleaning up...")
        self.inference.close()
        self.events.close()
        if self.device:
            self.device.close()
        print(f"[{self.app_id}] Shutdown complete")


def main():
    app = PersonDetectionApp()
    app.run()


if __name__ == "__main__":
    main()