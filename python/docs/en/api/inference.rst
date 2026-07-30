AI Inference API
================

.. automodule:: hailo_ipc_sdk.inference
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

InferenceClient
---------------

.. autoclass:: hailo_ipc_sdk.InferenceClient
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Data Types
----------

InferenceResult
~~~~~~~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.InferenceResult
   :members:
   :undoc-members:
   :no-index:

DetectedObject
~~~~~~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.DetectedObject
   :members:
   :undoc-members:

BoundingBox
~~~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.BoundingBox
   :members:
   :undoc-members:
   :no-index:

LandmarkPoint
~~~~~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.LandmarkPoint
   :members:
   :undoc-members:

LandmarkSet
~~~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.LandmarkSet
   :members:
   :undoc-members:

SegmentationMask
~~~~~~~~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.SegmentationMask
   :members:
   :undoc-members:

OcrLine
~~~~~~~

.. autoclass:: hailo_ipc_sdk.OcrLine
   :members:
   :undoc-members:

Embedding
~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.Embedding
   :members:
   :undoc-members:

DepthMap
~~~~~~~~

.. autoclass:: hailo_ipc_sdk.DepthMap
   :members:
   :undoc-members:

Classification
~~~~~~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.Classification
   :members:
   :undoc-members:

ModelInfo
~~~~~~~~~

.. autoclass:: hailo_ipc_sdk.ModelInfo
   :members:
   :undoc-members:

Usage Examples
--------------

Single-shot Inference
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from hailo_ipc_sdk import InferenceClient
   import numpy as np

   inf = InferenceClient()

   # Prepare image (numpy array)
   image = np.zeros((1080, 1920, 3), dtype=np.uint8)

   # Execute inference
   result = inf.infer(image, model_id="person_v1")

   # Process results
   for obj in result.objects:
       print(f"{obj.label}: {obj.score:.2f}")
       print(f"  Position: ({obj.bbox.x}, {obj.bbox.y})")
       print(f"  Size: {obj.bbox.width}x{obj.bbox.height}")

   # Convenience methods
   if result.has_person():
       print("Person detected")

   person_count = result.count_by_label("person")
   print(f"Person count: {person_count}")

   persons = result.get_objects_by_label("person")

Streaming Inference
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Subscribe to video stream inference results
   for frame_seq, result in inf.subscribe(
       stream="cam0_main",
       model="person_v1",
       fps=15
   ):
       print(f"Frame {frame_seq}: detected {len(result.objects)} object(s)")

       for obj in result.objects:
           if obj.score > 0.8:
               print(f"  High confidence: {obj.label} ({obj.score:.2f})")

Tensor Inference
~~~~~~~~~~~~~~~~

.. code-block:: python

   import numpy as np

   inf = InferenceClient()

   # Prepare input tensors
   input1 = np.random.randn(1, 3, 224, 224).astype(np.float32)
   input2 = np.random.randn(1, 3, 112, 112).astype(np.float32)

   # Execute inference
   outputs = inf.infer_with_tensors(
       model_id="custom_model",
       inputs=[input1, input2],
       input_names=["input_main", "input_sub"]
   )

   # Process output tensors
   for i, output in enumerate(outputs):
       print(f"Output {i}: shape={output.shape}")

Model Management
~~~~~~~~~~~~~~~~

.. code-block:: python

   # List all models
   models = inf.list_models()
   for model in models:
       print(f"Model ID: {model.model_id}")
       print(f"Path: {model.model_path}")
       print(f"Version: {model.version}")
       print(f"Inputs: {model.inputs}")
       print(f"Outputs: {model.outputs}")
       print(f"Estimated TOPS: {model.estimated_tops}")
       print(f"Estimated Memory: {model.estimated_memory} bytes")

   # Get model details
   info = inf.get_model_info("person_v1")
   if info:
       print(f"Model ID: {info.model_id}")
       print(f"Path: {info.model_path}")
       print(f"Version: {info.version}")

   # Register new model
   model_id = inf.register_model(
       model_path="/opt/models/custom.hef",
       model_id="custom_v1"
   )
   print(f"Registered model ID: {model_id}")

   # Unregister model
   inf.unregister_model("custom_v1")

Getting Statistics
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   stats = inf.get_stats()

   print(f"Device utilization: {stats['device_utilization']}%")
   print(f"Device temperature: {stats['device_temperature']}°C")
   print(f"Total memory: {stats['total_memory_bytes']} bytes")
   print(f"Used memory: {stats['used_memory_bytes']} bytes")

   for model_stat in stats['model_stats']:
       print(f"Model: {model_stat['model_id']}")
       print(f"  Total inferences: {model_stat['total_inferences']}")
       print(f"  Total errors: {model_stat['total_errors']}")
       print(f"  Average latency: {model_stat['avg_latency_us']}us")
       print(f"  Current QPS: {model_stat['current_qps']}")
       print(f"  Queue depth: {model_stat['queue_depth']}")

Session Management
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Create session
   session_id = inf.create_session(
       session_id="my_session",
       app_id="my_app",
       allowed_models=["person_v1", "car_v1"],
       max_qps=10,
       max_concurrent=2,
       priority=4
   )
   print(f"Session ID: {session_id}")

   # Use session for inference
   result = inf.infer(image, model_id="person_v1", session_id=session_id)

   # Destroy session
   inf.destroy_session(session_id)

Handling Different Result Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   result = inf.infer(image, model_id="face_detection")

   # Detection results
   for obj in result.objects:
       # Bounding box
       x1, y1, x2, y2 = obj.bbox.to_xyxy()
       print(f"Bounding box: ({x1}, {y1}) - ({x2}, {y2})")

   # Classification results
   for cls in result.classifications:
       print(f"Classification: {cls.type} - {cls.label}: {cls.confidence:.2f}")

   # Landmarks
   for lm_set in result.landmarks:
       print(f"Landmark set type: {lm_set.type}")
       for point in lm_set.points:
           print(f"  Point: ({point.x}, {point.y}), confidence: {point.confidence}")

   # Raw outputs
   if result.raw_outputs:
       print(f"Raw output count: {len(result.raw_outputs)}")

   # Performance info
   print(f"Inference time: {result.infer_time_us}us")
   print(f"Queue time: {result.queue_time_us}us")

Context Manager
~~~~~~~~~~~~~~~

.. code-block:: python

   # Use context manager for automatic connection management
   with InferenceClient() as inf:
       result = inf.infer(image, model_id="person_v1")
       print(f"Detected {len(result.objects)} object(s)")

Error Handling
~~~~~~~~~~~~~~

.. code-block:: python

   from grpc import RpcError

   try:
       result = inf.infer(image, model_id="nonexistent_model")
   except RpcError as e:
       print(f"Inference failed: {e.details()}")
   except RuntimeError as e:
       print(f"Runtime error: {e}")

Segmentation Results
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   result = inf.infer(image, model_id="segmentation_v1")

   for mask in result.masks:
       print(f"Mask: {mask.label} (confidence: {mask.confidence:.2f})")
       print(f"  BBox: ({mask.bbox.x}, {mask.bbox.y}, {mask.bbox.width}, {mask.bbox.height})")

       # Decode RLE mask to numpy bool array (H x W)
       np_mask = mask.to_numpy_mask()
       print(f"  Mask shape: {np_mask.shape}, pixels: {np_mask.sum()}")

OCR Results
~~~~~~~~~~~

.. code-block:: python

   result = inf.infer(image, model_id="ocr_v1")

   for line in result.ocr_lines:
       print(f"Text: '{line.text}' (confidence: {line.confidence:.2f})")
       print(f"  Position: ({line.bbox.x}, {line.bbox.y})")

Embedding (CLIP Image)
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   result = inf.infer(image, model_id="clip_vit_b32")

   for emb in result.embeddings:
       print(f"Embedding dim: {emb.dim}")
       # Use for similarity search, etc.
       import numpy as np
       vec = np.array(emb.data)
       print(f"  L2 norm: {np.linalg.norm(vec):.4f}")

CLIP Text Encoding
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Encode text to CLIP embedding via NPU
   embedding = inf.encode_text("a person walking in the park")
   print(f"Embedding length: {len(embedding)}")

   # Encode multiple texts and compute similarity
   import numpy as np
   emb1 = np.array(inf.encode_text("a cat"))
   emb2 = np.array(inf.encode_text("a dog"))
   similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
   print(f"Similarity: {similarity:.4f}")

Depth Estimation
~~~~~~~~~~~~~~~~

.. code-block:: python

   result = inf.infer(image, model_id="depth_v1")

   for dm in result.depth_maps:
       print(f"Depth map: {dm.width}x{dm.height}")
       print(f"  Min depth: {dm.data.min():.2f}, Max: {dm.data.max():.2f}")

Update Postprocess Config
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import json

   # Update CLIP text prompts at runtime
   config = json.dumps({
       "prompts": ["a person", "a car", "a bicycle"],
       "score_threshold": 0.3
   })
   inf.update_postprocess_config("clip_vit_b32", config)

GenAI (LLM/VLM)
~~~~~~~~~~~~~~~

.. code-block:: python

   # Create a GenAI session
   session_id = inf.genai_create_session(
       hef_path="/opt/models/llm.hef",
       kind="llm"
   )

   # Stream generated tokens
   messages = [json.dumps({"role": "user", "content": "Hello, who are you?"})]
   full_response = ""
   for token in inf.genai_generate(
       session_id=session_id,
       messages=messages,
       max_tokens=256,
       temperature=0.7,
       do_sample=True
   ):
       print(token, end="", flush=True)
       full_response += token

   # VLM: generate with image input
   with open("image.jpg", "rb") as f:
       img_data = f.read()

   vlm_session = inf.genai_create_session("/opt/models/vlm.hef", kind="vlm")
   messages = [json.dumps({"role": "user", "content": "Describe this image."})]
   for token in inf.genai_generate(
       session_id=vlm_session,
       messages=messages,
       images=[img_data]
   ):
       print(token, end="", flush=True)

   # Abort ongoing generation
   inf.genai_abort(session_id)

   # Clean up
   inf.genai_destroy_session(session_id)
   inf.genai_destroy_session(vlm_session)
