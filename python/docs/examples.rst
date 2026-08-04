示例代码
========

本页面提供了常见使用场景的完整示例代码。

人员检测应用
------------

实时检测视频流中的人员并发送告警。

.. code-block:: python

   #!/usr/bin/env python3
   """
   人员检测应用
   实时检测视频流中的人员，当检测到人员时发送告警事件
   """

   from hailo_ipc_sdk import InferenceClient, EventClient
   import time
   import logging

   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)

   def main():
       # 初始化客户端
       inf = InferenceClient()
       events = EventClient()

       logger.info("开始人员检测...")

       # 订阅视频流推理结果
       for frame_seq, result in inf.subscribe(
           stream="cam0_main",
           model="person_v1",
           fps=10
       ):
           # 过滤出人员检测结果
           persons = [
               obj for obj in result.objects
               if obj.label == "person" and obj.score > 0.8
           ]

           if persons:
               logger.info(f"帧 {frame_seq}: 检测到 {len(persons)} 个人")

               # 发布告警事件
               events.publish("app/person_detection/alert", {
                   "timestamp": time.time(),
                   "frame_seq": frame_seq,
                   "count": len(persons),
                   "objects": [
                       {
                           "score": p.score,
                           "bbox": {
                               "x": p.bbox.x,
                               "y": p.bbox.y,
                               "width": p.bbox.width,
                               "height": p.bbox.height
                           }
                       }
                       for p in persons
                   ]
               })

   if __name__ == "__main__":
       try:
           main()
       except KeyboardInterrupt:
           logger.info("应用停止")

车辆计数应用
------------

统计进出车辆数量。

.. code-block:: python

   #!/usr/bin/env python3
   """
   车辆计数应用
   统计通过检测线的车辆数量
   """

   from hailo_ipc_sdk import InferenceClient, EventClient
   import logging

   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)

   class VehicleCounter:
       def __init__(self, detection_line_y=540):
           self.detection_line = detection_line_y
           self.tracked_vehicles = {}
           self.count_in = 0
           self.count_out = 0

       def update(self, frame_seq, vehicles):
           """更新车辆跟踪"""
           current_ids = set()

           for vehicle in vehicles:
               center_y = vehicle.bbox.y + vehicle.bbox.height / 2
               vehicle_id = f"{vehicle.bbox.x}_{vehicle.bbox.y}"
               current_ids.add(vehicle_id)

               if vehicle_id in self.tracked_vehicles:
                   # 检查是否穿越检测线
                   prev_y = self.tracked_vehicles[vehicle_id]
                   if prev_y < self.detection_line <= center_y:
                       self.count_in += 1
                       logger.info(f"车辆进入: 总计 {self.count_in}")
                   elif prev_y > self.detection_line >= center_y:
                       self.count_out += 1
                       logger.info(f"车辆离开: 总计 {self.count_out}")

               self.tracked_vehicles[vehicle_id] = center_y

           # 清理旧的跟踪
           for vid in list(self.tracked_vehicles.keys()):
               if vid not in current_ids:
                   del self.tracked_vehicles[vid]

   def main():
       inf = InferenceClient()
       events = EventClient()
       counter = VehicleCounter()

       logger.info("开始车辆计数...")

       for frame_seq, result in inf.subscribe(
           stream="cam0_main",
           model="vehicle_v1",
           fps=15
       ):
           # 过滤车辆
           vehicles = [
               obj for obj in result.objects
               if obj.label in ["car", "truck", "bus"] and obj.score > 0.7
           ]

           # 更新计数
           counter.update(frame_seq, vehicles)

           # 定期发布统计
           if frame_seq % 150 == 0:  # 每 10 秒
               events.publish("app/vehicle_counter/stats", {
                   "count_in": counter.count_in,
                   "count_out": counter.count_out,
                   "current": len(vehicles)
               })

   if __name__ == "__main__":
       try:
           main()
       except KeyboardInterrupt:
           logger.info("应用停止")

智能灯光控制
------------

根据检测结果和环境光自动控制灯光。

.. code-block:: python

   #!/usr/bin/env python3
   """
   智能灯光控制
   根据人员检测和环境光自动控制补光灯
   """

   from hailo_ipc_sdk import DeviceClient, EventClient, IrCutMode
   import logging
   import time

   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)

   class SmartLightController:
       def __init__(self):
           self.dev = DeviceClient()
           self.events = EventClient()
           self.person_detected = False
           self.illuminance = 100  # 默认光照值

       def on_person_detection(self, event):
           """处理人员检测事件"""
           count = event.payload.get("count", 0)
           self.person_detected = count > 0

           if self.person_detected:
               logger.info("检测到人员，调整灯光")
               self.adjust_light()

       def on_illuminance(self, event):
           """处理光照传感器事件"""
           self.illuminance = event.payload.get("value", 100)
           logger.info(f"环境光照: {self.illuminance} lux")
           self.adjust_light()

       def adjust_light(self):
           """调整灯光"""
           if self.illuminance < 10:  # 夜间
               self.dev.set_ircut(IrCutMode.NIGHT)
               if self.person_detected:
                   self.dev.set_white_light(80)  # 有人时开启补光
                   self.dev.set_ir_led(True)
               else:
                   self.dev.set_white_light(0)
                   self.dev.set_ir_led(True)  # 保持红外灯

           elif self.illuminance < 50:  # 黄昏
               self.dev.set_ircut(IrCutMode.AUTO)
               if self.person_detected:
                   self.dev.set_white_light(50)
               else:
                   self.dev.set_white_light(0)
               self.dev.set_ir_led(False)

           else:  # 白天
               self.dev.set_ircut(IrCutMode.DAY)
               self.dev.set_white_light(0)
               self.dev.set_ir_led(False)

       def run(self):
           """运行控制器"""
           logger.info("启动智能灯光控制...")

           # 订阅事件
           self.events.on_event("app/person_detection/alert", self.on_person_detection)
           self.events.on_event("sensor/illuminance", self.on_illuminance)

           # 保持运行
           try:
               while True:
                   time.sleep(1)
           except KeyboardInterrupt:
               logger.info("停止控制器")

   if __name__ == "__main__":
       controller = SmartLightController()
       controller.run()

视频录制应用
------------

检测到特定事件时自动录制视频。

.. code-block:: python

   #!/usr/bin/env python3
   """
   事件触发录制
   当检测到告警事件时自动录制视频片段
   """

   from hailo_ipc_sdk import MediaClient, EventClient
   import cv2
   import time
   import logging
   from pathlib import Path

   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)

   class EventRecorder:
       def __init__(self, output_dir="/app/recordings"):
           self.media = MediaClient()
           self.events = EventClient()
           self.output_dir = Path(output_dir)
           self.output_dir.mkdir(parents=True, exist_ok=True)
           self.recording = False
           self.writer = None

       def start_recording(self, event_type):
           """开始录制"""
           if self.recording:
               return

           timestamp = int(time.time())
           filename = self.output_dir / f"{event_type}_{timestamp}.mp4"

           info = self.media.get_stream_info("cam0_main")
           fourcc = cv2.VideoWriter_fourcc(*'mp4v')
           self.writer = cv2.VideoWriter(
               str(filename),
               fourcc,
               info.fps,
               (info.width, info.height)
           )

           self.recording = True
           logger.info(f"开始录制: {filename}")

       def stop_recording(self):
           """停止录制"""
           if not self.recording:
               return

           if self.writer:
               self.writer.release()
               self.writer = None

           self.recording = False
           logger.info("停止录制")

       def on_alert(self, event):
           """处理告警事件"""
           alert_type = event.payload.get("type")
           logger.info(f"收到告警: {alert_type}")
           self.start_recording(alert_type)

       def run(self):
           """运行录制器"""
           logger.info("启动事件录制器...")

           # 订阅告警事件
           self.events.on_event("app/*/alert", self.on_alert)

           # 处理视频流
           frame_count = 0
           recording_frames = 0
           max_recording_frames = 300  # 录制 10 秒 (30fps)

           for frame in self.media.get_raw_stream("cam0_main"):
               if self.recording:
                   self.writer.write(frame.data)
                   recording_frames += 1

                   if recording_frames >= max_recording_frames:
                       self.stop_recording()
                       recording_frames = 0

               frame_count += 1

   if __name__ == "__main__":
       try:
           recorder = EventRecorder()
           recorder.run()
       except KeyboardInterrupt:
           logger.info("应用停止")

多模型融合应用
--------------

结合多个 AI 模型进行综合分析。

.. code-block:: python

   #!/usr/bin/env python3
   """
   多模型融合应用
   结合人员检测、人脸识别和行为分析
   """

   from hailo_ipc_sdk import InferenceClient, EventClient
   import logging

   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)

   class MultiModelApp:
       def __init__(self):
           self.inf = InferenceClient()
           self.events = EventClient()

       def process_frame(self, frame_data):
           """处理单帧"""
           results = {}

           # 1. 人员检测
           person_result = self.inf.infer(frame_data, model_id="person_v1")
           persons = [obj for obj in person_result.objects if obj.label == "person"]
           results["persons"] = len(persons)

           # 2. 如果检测到人员，进行人脸识别
           if persons:
               face_result = self.inf.infer(frame_data, model_id="face_detection_v1")
               faces = face_result.objects
               results["faces"] = len(faces)

               # 3. 行为分析
               if faces:
                   behavior_result = self.inf.infer(frame_data, model_id="behavior_v1")
                   results["behaviors"] = [
                       obj.label for obj in behavior_result.objects
                   ]

           return results

       def run(self):
           """运行应用"""
           logger.info("启动多模型融合应用...")

           for frame_seq, _ in self.inf.subscribe(
               stream="cam0_main",
               model="person_v1",
               fps=5
           ):
               # 获取原始帧数据进行多模型推理
               # 这里简化处理，实际应该从 MediaClient 获取
               logger.info(f"处理帧 {frame_seq}")

               # 发布综合分析结果
               self.events.publish("app/multi_model/analysis", {
                   "frame_seq": frame_seq,
                   "timestamp": time.time()
               })

   if __name__ == "__main__":
       try:
           app = MultiModelApp()
           app.run()
       except KeyboardInterrupt:
           logger.info("应用停止")
