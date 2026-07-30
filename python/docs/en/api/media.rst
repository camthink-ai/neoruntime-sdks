Video Stream API
================

.. automodule:: hailo_ipc_sdk.media
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

FdMediaClient
-------------

.. autoclass:: hailo_ipc_sdk.FdMediaClient
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Data Types
----------

Frame
~~~~~

.. autoclass:: hailo_ipc_sdk.Frame
   :members:
   :undoc-members:
   :no-index:

StreamInfo
~~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.StreamInfo
   :members:
   :undoc-members:

PixelFormat
~~~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.PixelFormat
   :members:
   :undoc-members:

Usage Examples
--------------

Getting Raw Video Stream
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import MediaClient
   import cv2

   media = MediaClient()

   # Get main stream
   for frame in media.subscribe("cam0_main"):
       print(f"Frame {frame.sequence}: {frame.width}x{frame.height}")
       print(f"Format: {frame.format}, Timestamp: {frame.timestamp_ns}")

       # frame.image is a numpy array (H, W, C) or (H*3//2, W) for NV12
       # Can be used directly with OpenCV or other image processing libraries
       cv2.imshow("Camera", frame.image)
       if cv2.waitKey(1) & 0xFF == ord('q'):
           break

   cv2.destroyAllWindows()

No Frame Skipping
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get every frame (no skipping)
   for frame in media.subscribe("cam0_main", skip_frames=False):
       process_frame(frame.image)

Getting a Single Frame
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get a single frame
   frame = media.get_frame("cam0_main", timeout_ms=1000)

   if frame:
       print(f"Frame: {frame.width}x{frame.height}")
       print(f"Format: {frame.format}")

Getting Stream Info
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get stream configuration info
   info = media.get_stream_info("cam0_main")

   if info:
       print(f"Resolution: {info.width}x{info.height}")
       print(f"Frame rate: {info.fps}")
       print(f"Format: {info.format}")
       print(f"Buffer count: {info.buffer_count}")

Listing Available Streams
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # List all available streams
   streams = media.list_streams()
   for stream_id in streams:
       print(f"Stream: {stream_id}")

Frame Callback
~~~~~~~~~~~~~~

.. code-block:: python

   def handle_frame(frame):
       print(f"Received frame: {frame.sequence}")

   # Use callback for frame processing
   thread = media.on_frame("cam0_main", handle_frame)

   # Keep running
   import time
   while True:
       time.sleep(1)

Image Processing
~~~~~~~~~~~~~~~~

.. code-block:: python

   import cv2
   import numpy as np

   media = MediaClient()

   for frame in media.subscribe("cam0_main"):
       # Convert to RGB
       rgb = frame.to_rgb()

       # Grayscale
       gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

       # Edge detection
       edges = cv2.Canny(gray, 100, 200)

       # Display results
       cv2.imshow("Original", rgb)
       cv2.imshow("Edges", edges)

       if cv2.waitKey(1) & 0xFF == ord('q'):
           break

Saving Images
~~~~~~~~~~~~~

.. code-block:: python

   media = MediaClient()

   for frame in media.subscribe("cam0_main"):
       # Save as image
       frame.save("frame.jpg")
       break

Multi-Stream Processing
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import threading

   def process_main_stream():
       media = MediaClient()
       for frame in media.subscribe("cam0_main"):
           # Process main stream (high resolution)
           process_high_res(frame.image)

   def process_sub_stream():
       media = MediaClient()
       for frame in media.subscribe("cam0_sub"):
           # Process sub stream (low resolution)
           process_low_res(frame.image)

   # Process multiple streams in parallel
   t1 = threading.Thread(target=process_main_stream)
   t2 = threading.Thread(target=process_sub_stream)

   t1.start()
   t2.start()

   t1.join()
   t2.join()

Frame Rate Control
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import time

   media = MediaClient()
   target_fps = 10
   frame_interval = 1.0 / target_fps

   last_time = time.time()

   for frame in media.subscribe("cam0_main"):
       current_time = time.time()
       elapsed = current_time - last_time

       if elapsed >= frame_interval:
           # Process frame
           process_frame(frame.image)
           last_time = current_time

Saving Video
~~~~~~~~~~~~

.. code-block:: python

   import cv2

   media = MediaClient()
   info = media.get_stream_info("cam0_main")

   # Create video writer
   fourcc = cv2.VideoWriter_fourcc(*'mp4v')
   out = cv2.VideoWriter(
       'output.mp4',
       fourcc,
       info.fps,
       (info.width, info.height)
   )

   frame_count = 0
   max_frames = 300  # Record 10 seconds (30fps)

   for frame in media.subscribe("cam0_main"):
       rgb = frame.to_rgb()
       bgr = rgb[:, :, ::-1]  # RGB to BGR
       out.write(bgr)
       frame_count += 1

       if frame_count >= max_frames:
           break

   out.release()
   print(f"Saved {frame_count} frames to output.mp4")

Context Manager
~~~~~~~~~~~~~~~

.. code-block:: python

   # Use context manager for automatic resource management
   with MediaClient() as media:
       for frame in media.subscribe("cam0_main"):
           process_frame(frame.image)

Zero-Copy Access
~~~~~~~~~~~~~~~~

.. code-block:: python

   # The SDK uses shared memory (SHM) for zero-copy access
   # frame.image directly maps to SHM without additional copying

   media = MediaClient()

   for frame in media.subscribe("cam0_main"):
       # frame.image is a numpy array that directly references SHM
       # Can be efficiently passed to AI inference or other processing modules
       result = inference_engine.process(frame.image)

Error Handling
~~~~~~~~~~~~~~

.. code-block:: python

   media = MediaClient()

   try:
       for frame in media.subscribe("invalid_stream"):
           process_frame(frame.image)
   except Exception as e:
       print(f"Stream access failed: {e}")
   except KeyboardInterrupt:
       print("User interrupted")
   finally:
       media.close()
