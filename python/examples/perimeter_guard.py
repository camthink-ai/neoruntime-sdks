#!/usr/bin/env python3
"""
周界防护示例应用

功能：
- 人形检测 + 越界判断
- 设备联动（灯光控制）
- 事件发布与告警
"""

import time
import signal
from typing import List, Tuple
from hailo_ipc_sdk import (
    InferenceClient, EventClient, DeviceClient,
    Config, InferenceResult, DetectedObject
)


class PerimeterGuardApp:
    """周界防护应用"""
    
    def __init__(self):
        self.running = True
        self.app_id = Config.get_app_id()
        self.debug = Config.is_debug()
        
        self.inference = InferenceClient()
        self.events = EventClient()
        self.device = DeviceClient()
        
        self.alert_cooldown = 5.0
        self.last_alert_time = 0
        
        self.detection_line = (0.3, 0.7)
        
        self.light_on = False
        self.light_timeout = 10.0
        self.light_on_time = 0
        
        print(f"[{self.app_id}] Perimeter Guard App initialized")
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print(f"\n[{self.app_id}] Shutting down...")
        self.running = False
    
    def run(self):
        print(f"[{self.app_id}] Starting perimeter guard...")
        
        try:
            for frame_seq, result in self.inference.subscribe(
                stream="cam0_main",
                model="person_v1",
                fps=15
            ):
                if not self.running:
                    break
                
                self._process_frame(frame_seq, result)
                self._update_device_state()
                
        except Exception as e:
            print(f"[{self.app_id}] Error: {e}")
        finally:
            self._cleanup()
    
    def _process_frame(self, frame_seq: int, result: InferenceResult):
        persons = result.get_objects_by_label("person")
        
        if not persons:
            return
        
        crossed_persons = [
            p for p in persons 
            if self._is_crossing_line(p)
        ]
        
        if crossed_persons:
            current_time = time.time()
            if current_time - self.last_alert_time >= self.alert_cooldown:
                self._trigger_alert(frame_seq, crossed_persons)
                self.last_alert_time = current_time
        
        if persons and not self.light_on:
            self._turn_on_light()
    
    def _is_crossing_line(self, person: DetectedObject) -> bool:
        center_x = person.bbox.x + person.bbox.width / 2
        center_y = person.bbox.y + person.bbox.height / 2
        
        return center_x > self.detection_line[0] and center_y > self.detection_line[1]
    
    def _trigger_alert(self, frame_seq: int, persons: List[DetectedObject]):
        print(f"[ALERT] {len(persons)} person(s) crossed the boundary!")
        
        self.events.publish(f"app/{self.app_id}/perimeter_alert", {
            "type": "boundary_crossing",
            "frame_sequence": frame_seq,
            "person_count": len(persons),
            "confidence": [p.score for p in persons]
        }, persistent=True)
        
        self._turn_on_light()
    
    def _turn_on_light(self):
        try:
            self.device.set_white_light(100)
            self.light_on = True
            self.light_on_time = time.time()
            print(f"[{self.app_id}] Light turned ON")
        except Exception as e:
            print(f"[{self.app_id}] Failed to control light: {e}")
    
    def _turn_off_light(self):
        try:
            self.device.set_white_light(0)
            self.light_on = False
            print(f"[{self.app_id}] Light turned OFF")
        except Exception as e:
            print(f"[{self.app_id}] Failed to control light: {e}")
    
    def _update_device_state(self):
        if self.light_on and time.time() - self.light_on_time >= self.light_timeout:
            self._turn_off_light()
    
    def _cleanup(self):
        if self.light_on:
            self._turn_off_light()
        
        self.inference.close()
        self.events.close()
        self.device.close()
        print(f"[{self.app_id}] Cleanup complete")


def main():
    app = PerimeterGuardApp()
    app.run()


if __name__ == "__main__":
    main()