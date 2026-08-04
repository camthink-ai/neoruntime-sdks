Changelog
=========

v0.4.0 (2026-07-14)
-------------------

New Features
~~~~~~~~~~~~

- **DeviceClient** — 7 new methods:
  - ``set_lens_limits(zoom_limit, focus_limit)`` — Set lens axis position limits
  - ``oneshot_autofocus(timeout)`` — One-shot autofocus (composite: enable → wait for convergence → disable)
  - ``set_wiegand_out(channel, enable)`` — Wiegand output control
  - ``get_wiegand_out(channel)`` — Wiegand output state query
  - ``rs485_init(baudrate, config)`` — RS-485 serial initialization
  - ``rs485_deinit()`` — RS-485 serial deinitialization
  - ``rs485_tx(data)`` — RS-485 data transmission
- **AppClient** — 1 new method:
  - ``restart_app(app_id, timeout_seconds)`` — Restart application (stop + start)

Improvements
~~~~~~~~~~~~

- Updated API docs with DeviceClient lens limits, Wiegand, and RS-485 examples
- Updated API docs with complete AppClient usage examples
- Synchronized Chinese and English documentation

v0.3.0 (2026-05-18)
-------------------

New Features
~~~~~~~~~~~~

- Added segmentation mask support (``SegmentationMask`` with RLE decoding via ``to_numpy_mask()``)
- Added OCR result support (``OcrLine`` with text, confidence, bounding box)
- Added embedding vector support (``Embedding`` for CLIP and similar models)
- Added depth map support (``DepthMap`` with float32 numpy array)
- Added CLIP text encoding via ``encode_text()`` — encode text strings to NPU embeddings
- Added runtime postprocess config update via ``update_postprocess_config()``
- Added GenAI (LLM/VLM) support:
  - ``genai_create_session()`` — create LLM or VLM sessions with HEF models
  - ``genai_generate()`` — stream generated tokens with sampling parameters
  - ``genai_abort()`` — abort ongoing generation
  - ``genai_destroy_session()`` — clean up session resources
- Added LoRA adapter support for GenAI sessions (``lora_name`` parameter)
- Added memory optimization option for GenAI tokenization (``optimize_memory``)

Improvements
~~~~~~~~~~~~

- Enhanced ``subscribe()`` with ``raw_output_only`` parameter for raw tensor streaming
- Enhanced ``register_model()`` with ``model_type``, ``model_variant``, and explicit ``inputs``/``outputs`` specs
- Improved tensor type handling with full dtype mapping (uint8, int8, uint16, int16, float16, float32, int32, uint32)

Bug Fixes
~~~~~~~~~

- Fixed tensor shape mismatch when output shape does not match data size
- Fixed ``InferenceResult`` missing new result types (masks, ocr, embeddings, depth)

v0.2.0 (2026-03-02)
-------------------

New Features
~~~~~~~~~~~~

- Added plugin system support (PluginDiscovery, PluginServer)
- Support for plugin capability discovery and gRPC service invocation
- Added MediaClient for video stream access
- Support for raw and encoded video stream retrieval

Improvements
~~~~~~~~~~~~

- Optimized InferenceClient performance
- Improved event bus wildcard matching
- Enhanced error handling and logging
- Updated protobuf to 4.21.0

Bug Fixes
~~~~~~~~~

- Fixed memory leak in EventClient subscription
- Fixed DeviceClient GPIO control issue
- Fixed connection pool issue in multi-threaded environments

v0.1.0 (2025-12-15)
-------------------

Initial Release
~~~~~~~~~~~~~~~~

- InferenceClient: AI inference client
- EventClient: Event bus client
- DeviceClient: Device control client
- Config: Configuration management
- Support for Python 3.8+
- gRPC-based communication
