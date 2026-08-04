Examples
========

This page provides complete example code for common use cases.

Person Detection Application
----------------------------

Real-time detection of persons in a video stream with alert publishing.

.. code-block:: python

   #!/usr/bin/env python3
   """
   Person Detection Application
   Real-time detection of persons in a video stream, sending alerts when persons are detected
   """

   from hailo_ipc_sdk import InferenceClient, EventClient
   import time
   import logging

   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)

   def main():
       # Initialize clients
       inf = InferenceClient()
       events = EventClient()

       logger.info("Starting person detection...")

       # Subscribe to video stream inference results
       for frame_seq, result in inf.subscribe(
           stream="cam0_main",
           model="person_v1",
           fps=10
       ):
           # Filter person detection results
           persons = [
               obj for obj in result.objects
               if obj.label == "person" and obj.score > 0.8
           ]

           if persons:
               logger.info(f"Frame {frame_seq}: detected {len(persons)} person(s)")

               # Publish alert event
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
           logger.info("Application stopped")

Vehicle Counting Application
----------------------------

Count vehicles entering and exiting.

.. code-block:: python

   #!/usr/bin/env python3
   """
   Vehicle Counting Application
   Count vehicles crossing a detection line
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
           """Update vehicle tracking"""
           current_ids = set()

           for vehicle in vehicles:
               center_y = vehicle.bbox.y + vehicle.bbox.height / 2
               vehicle_id = f"{vehicle.bbox.x}_{vehicle.bbox.y}"
               current_ids.add(vehicle_id)

               if vehicle_id in self.tracked_vehicles:
                   prev_y = self.tracked_vehicles[vehicle_id]
                   if prev_y < self.detection_line <= center_y:
                       self.count_in += 1
                       logger.info(f"Vehicle entered: total {self.count_in}")
                   elif prev_y > self.detection_line >= center_y:
                       self.count_out += 1
                       logger.info(f"Vehicle exited: total {self.count_out}")

               self.tracked_vehicles[vehicle_id] = center_y

           for vid in list(self.tracked_vehicles.keys()):
               if vid not in current_ids:
                   del self.tracked_vehicles[vid]

   def main():
       inf = InferenceClient()
       events = EventClient()
       counter = VehicleCounter()

       logger.info("Starting vehicle counting...")

       for frame_seq, result in inf.subscribe(
           stream="cam0_main",
           model="vehicle_v1",
           fps=15
       ):
           vehicles = [
               obj for obj in result.objects
               if obj.label in ["car", "truck", "bus"] and obj.score > 0.7
           ]

           counter.update(frame_seq, vehicles)

           if frame_seq % 150 == 0:  # Every 10 seconds
               events.publish("app/vehicle_counter/stats", {
                   "count_in": counter.count_in,
                   "count_out": counter.count_out,
                   "current": len(vehicles)
               })

   if __name__ == "__main__":
       try:
           main()
       except KeyboardInterrupt:
           logger.info("Application stopped")

Smart Light Control
-------------------

Automatically control lighting based on detection results and ambient light.

.. code-block:: python

   #!/usr/bin/env python3
   """
   Smart Light Control
   Automatically control fill lights based on person detection and ambient light
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
           self.illuminance = 100

       def on_person_detection(self, event):
           """Handle person detection event"""
           count = event.payload.get("count", 0)
           self.person_detected = count > 0

           if self.person_detected:
               logger.info("Person detected, adjusting lights")
               self.adjust_light()

       def on_illuminance(self, event):
           """Handle light sensor event"""
           self.illuminance = event.payload.get("value", 100)
           logger.info(f"Ambient light: {self.illuminance} lux")
           self.adjust_light()

       def adjust_light(self):
           """Adjust lighting"""
           if self.illuminance < 10:  # Nighttime
               self.dev.set_ircut(IrCutMode.NIGHT)
               if self.person_detected:
                   self.dev.set_white_light(80)
                   self.dev.set_ir_led(True)
               else:
                   self.dev.set_white_light(0)
                   self.dev.set_ir_led(True)

           elif self.illuminance < 50:  # Dusk
               self.dev.set_ircut(IrCutMode.AUTO)
               if self.person_detected:
                   self.dev.set_white_light(50)
               else:
                   self.dev.set_white_light(0)
               self.dev.set_ir_led(False)

           else:  # Daytime
               self.dev.set_ircut(IrCutMode.DAY)
               self.dev.set_white_light(0)
               self.dev.set_ir_led(False)

       def run(self):
           """Run the controller"""
           logger.info("Starting smart light control...")

           self.events.on_event("app/person_detection/alert", self.on_person_detection)
           self.events.on_event("sensor/illuminance", self.on_illuminance)

           try:
               while True:
                   time.sleep(1)
           except KeyboardInterrupt:
               logger.info("Stopping controller")

   if __name__ == "__main__":
       controller = SmartLightController()
       controller.run()

Video Recording Application
---------------------------

Automatically record video when specific events are detected.

.. code-block:: python

   #!/usr/bin/env python3
   """
   Event-triggered Recording
   Automatically record video clips when alert events are detected
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
           """Start recording"""
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
           logger.info(f"Started recording: {filename}")

       def stop_recording(self):
           """Stop recording"""
           if not self.recording:
               return

           if self.writer:
               self.writer.release()
               self.writer = None

           self.recording = False
           logger.info("Stopped recording")

       def on_alert(self, event):
           """Handle alert event"""
           alert_type = event.payload.get("type")
           logger.info(f"Alert received: {alert_type}")
           self.start_recording(alert_type)

       def run(self):
           """Run the recorder"""
           logger.info("Starting event recorder...")

           self.events.on_event("app/*/alert", self.on_alert)

           frame_count = 0
           recording_frames = 0
           max_recording_frames = 300  # Record 10 seconds (30fps)

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
           logger.info("Application stopped")

Multi-Model Fusion Application
------------------------------

Combine multiple AI models for comprehensive analysis.

.. code-block:: python

   #!/usr/bin/env python3
   """
   Multi-Model Fusion Application
   Combining person detection, face recognition, and behavior analysis
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
           """Process a single frame"""
           results = {}

           # 1. Person detection
           person_result = self.inf.infer(frame_data, model_id="person_v1")
           persons = [obj for obj in person_result.objects if obj.label == "person"]
           results["persons"] = len(persons)

           # 2. If persons detected, perform face recognition
           if persons:
               face_result = self.inf.infer(frame_data, model_id="face_detection_v1")
               faces = face_result.objects
               results["faces"] = len(faces)

               # 3. Behavior analysis
               if faces:
                   behavior_result = self.inf.infer(frame_data, model_id="behavior_v1")
                   results["behaviors"] = [
                       obj.label for obj in behavior_result.objects
                   ]

           return results

       def run(self):
           """Run the application"""
           logger.info("Starting multi-model fusion application...")

           for frame_seq, _ in self.inf.subscribe(
               stream="cam0_main",
               model="person_v1",
               fps=5
           ):
               logger.info(f"Processing frame {frame_seq}")

               self.events.publish("app/multi_model/analysis", {
                   "frame_seq": frame_seq,
                   "timestamp": time.time()
               })

   if __name__ == "__main__":
       try:
           app = MultiModelApp()
           app.run()
       except KeyboardInterrupt:
           logger.info("Application stopped")
