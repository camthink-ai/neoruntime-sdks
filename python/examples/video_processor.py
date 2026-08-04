#!/usr/bin/env python3
"""
视频处理示例应用

功能：
- 订阅 Raw 视频流
- 帧处理与保存
- 性能统计
"""

import time
import signal
from pathlib import Path
from hailo_ipc_sdk import FdMediaClient, Frame, Config


class VideoProcessorApp:
    def __init__(self):
        self.running = True
        self.app_id = Config.get_app_id()
        self.debug = Config.is_debug()
        
        self.media = FdMediaClient()
        
        self.frame_count = 0
        self.start_time = None
        self.last_fps_time = None
        self.last_fps_count = 0
        
        self.save_interval = 100
        self.save_dir = Path("/app/data/frames")
        if self.debug:
            self.save_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[{self.app_id}] Video Processor App initialized")
        print(f"[{self.app_id}] SHM Base: {Config.get_shm_base_path()}")
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print(f"\n[{self.app_id}] Shutting down...")
        self.running = False
    
    def run(self):
        streams = self.media.list_streams()
        print(f"[{self.app_id}] Available streams: {streams}")
        
        if not streams:
            print(f"[{self.app_id}] No streams available, waiting...")
            while not streams and self.running:
                time.sleep(1)
                streams = self.media.list_streams()
        
        stream_id = streams[0] if streams else "cam0_main"
        print(f"[{self.app_id}] Subscribing to stream: {stream_id}")
        
        self.start_time = time.time()
        self.last_fps_time = self.start_time
        
        try:
            for frame in self.media.subscribe_raw(stream_id):
                if not self.running:
                    break
                
                self._process_frame(frame)
                self._update_stats(frame)
                
        except Exception as e:
            print(f"[{self.app_id}] Error: {e}")
        finally:
            self._cleanup()
    
    def _process_frame(self, frame: Frame):
        self.frame_count += 1
        
        if self.debug and self.frame_count % self.save_interval == 0:
            self._save_frame(frame)
    
    def _save_frame(self, frame: Frame):
        filename = self.save_dir / f"frame_{frame.sequence:08d}.jpg"
        try:
            rgb = frame.to_rgb()
            import cv2
            cv2.imwrite(str(filename), rgb[:, :, ::-1])
            print(f"[{self.app_id}] Saved: {filename}")
        except ImportError:
            print(f"[{self.app_id}] OpenCV not available, skipping save")
        except Exception as e:
            print(f"[{self.app_id}] Failed to save frame: {e}")
    
    def _update_stats(self, frame: Frame):
        current_time = time.time()
        elapsed = current_time - self.last_fps_time
        
        if elapsed >= 5.0:
            fps = (self.frame_count - self.last_fps_count) / elapsed
            total_elapsed = current_time - self.start_time
            avg_fps = self.frame_count / total_elapsed
            
            print(f"[{self.app_id}] FPS: {fps:.1f} (avg: {avg_fps:.1f}) | "
                  f"Frame: {frame.sequence} | Size: {frame.width}x{frame.height}")
            
            self.last_fps_time = current_time
            self.last_fps_count = self.frame_count
    
    def _cleanup(self):
        self.media.close()
        
        if self.start_time and self.frame_count > 0:
            total_time = time.time() - self.start_time
            avg_fps = self.frame_count / total_time
            print(f"[{self.app_id}] Total frames: {self.frame_count}")
            print(f"[{self.app_id}] Total time: {total_time:.1f}s")
            print(f"[{self.app_id}] Average FPS: {avg_fps:.2f}")
        
        print(f"[{self.app_id}] Cleanup complete")


def main():
    app = VideoProcessorApp()
    app.run()


if __name__ == "__main__":
    main()