Changelog
=========

v0.8.2 (2026-11-26)
-------------------

New Features
~~~~~~~~~~~~

- **RS-485 receive stream**: added ``DeviceClient.subscribe_rs485_rx()``, which delivers every frame received on the RS-485 bus as an event stream; ``Rs485RxEvent`` carries the raw bytes (``data``) and the device-side receive time (``timestamp_ns``). Each subscriber owns a bounded queue: ``queue_size`` sets the queue depth (0 selects the default of 16; values above 128 are capped at 128) and ``drop_old`` selects whether the oldest or the newest frame is discarded when the queue is full. All subscribers share one upstream stream that reconnects automatically after a camera-daemon restart, so subscriptions survive the restart. Delivery is at least once; callers that need exactly-once semantics de-duplicate themselves. The call needs platform firmware that serves the ``SubscribeRs485Rx`` RPC; on firmware without it the iterator ends with a gRPC ``UNIMPLEMENTED`` error.

Improvements
~~~~~~~~~~~~

- Synced the platform protos: camera-control and device-control gain the ``SubscribeRs485Rx`` streaming RPC and the ``Rs485SubscribeRequest`` / ``Rs485RxEvent`` messages
- The device test suite gains ``test_04_subscribe_rs485_rx``; offline unit tests cover the subscription arguments and the generator semantics

Documentation
~~~~~~~~~~~~~

- README, ``SDK_API_ZH.md`` and the bilingual API reference document the ``subscribe_rs485_rx`` arguments, generator semantics and delivery contract

v0.8.1 (2026-10-15)
-------------------

Improvements
~~~~~~~~~~~~

- ``register_model()`` tests now register detection models by ``model_type``, aligned with the runtime's postprocess-linking behavior

Documentation
~~~~~~~~~~~~~

- New bilingual "learning path" page: an onboarding route organized into five stages (first run, see it live, take and reuse, ship, reference), pointing each stage at the quickstart, the teaching demo, the examples ladder, and the app image guide
- README gains Overlay / StreamPipeline / Audio / DSP API overview sections plus a teaching-demo section, reconciled symbol-by-symbol against the 0.8.0 facade
- Learning-path stage 3 cross-links the numbered ladder (01-07) in the apps repository's ``examples/``; rung 05 is the standalone-app version of teaching-demo station 1
- New bilingual "device onboarding" page: from buying an NE503 to your first login — the factory static address ``10.0.0.1/24``, default credentials, SSH and the web terminal, and multicast discovery — linked from the learning path as its stage 0

v0.8.0 (2026-09-16)
-------------------

New Features
~~~~~~~~~~~~

- **Client-side inference pipeline**: added ``Preprocessor`` / ``PreprocessMeta``, ``YoloV5Postprocessor`` / ``YoloV8Postprocessor``, ``InferencePipeline``, and ``PipelineRunner`` for model-derived preprocessing, source-coordinate mapping, replaceable postprocessing, asynchronous execution, and long-running latest-wins processing with backpressure and statistics
- **Platform-scheduled pipeline**: added ``StreamPipeline`` / ``StreamPipelineStatus``, combining ``InferenceClient.subscribe()`` with ``OverlayClient`` so inference, filtering, hardware overlay, and application-side result consumption work without bringing pixels into the application process; drop, latency, skew, and error metrics are exposed
- **Frame-injection output path**: added ``FramePublisher`` and ``CameraClient.push_frame()`` / ``injection_status()`` / ``stop_injection()`` with replace/overlay modes, NV12/RGB publishing, EOS restoration, and session tags; the write-lease-aware pool only reuses slots released by the daemon and falls back to depth-paced rotation on older daemons
- **Overlay frame sync and observability**: ``OverlayClient`` gained strict frame lock plus ``frame_sequence`` / ``stream_epoch`` / ``session_id`` binding; ``StreamStatus`` gained encoded-publisher, overlay-bake, strict-lock, late-command, and stale-epoch counters
- **Deployment diagnostics**: added the never-raising ``diagnostics()`` snapshot, requirement-based ``diagnostics.check()`` with aggregated failures, and the application-wide ``set_route_policy()`` acceleration control
- **Inference model metadata**: ``register_model()`` accepts ``batch_size``, ``ModelInfo`` passes through the server-side batch size, and ``InferenceResult`` exposes the server-computed ``skew_us``
- **End-to-end device-resident data path**: the DSP router reuses a process-wide client; ``resize_hw`` / ``convert_hw`` can return ``DspBufferRef`` with ``out="ref"``, inference consumes device-side refs directly, NV12 preprocessing can pass them through, and BLEND can target a ``FramePublisher`` pool slot without intermediate read-back or repeated imports
- **Area-bounded overlay rendering**: added ``render_overlay_fragments()``, splitting strokes into even-sized strips capped to the DSP batch limit to reduce full-frame ARGB overlay bandwidth and memory

Improvements
~~~~~~~~~~~~

- ``Frame`` crop/resize chains now retain composed geometry metadata; keep-fd frames remain device-side through preprocessing, inference, blending, and publishing, while the media and encoded clients expose additional drop and connection observability
- Added comprehensive on-device interface and performance suites plus a ``perf_demo`` with subscribe/keep-fd comparison chains, deployment scripts, and runtime metrics collection

Bug Fixes
~~~~~~~~~

- Fixed three issues found by the on-device interface suite: DSP import ids with the high bit set were parsed as signed 64-bit values; ``get_device_status()`` read a nonexistent ``ir_led_on`` field; and ``AppClient.list_apps()`` constructed the wrong Empty message type
- Fixed injection shutdown omitting EOS, stop-from-callback attempting to join its own thread, and missing ``ttl_ms`` validation on some overlay publish paths
- Fixed DSP pools and references remaining usable after client close, retiring process-wide clients closing resources still in flight, and passthrough input refs not being released after inference settled
- Tightened overlay-fragment even geometry and batch limits, including the pre-edge-slide height rounding that could otherwise produce invalid strips

Deprecated
~~~~~~~~~~

- **Plugin system API** (``PluginDiscovery`` / ``PluginServer`` / ``PluginEndpoint``) is deprecated. The platform does not ship the ``/run/aipc/plugins`` discovery mechanism; v0.8.0 still keeps the imports working, emits a ``DeprecationWarning``, and leaves the docs page offline. Speak up if you depend on it.

Documentation
~~~~~~~~~~~~~

- Fixed the video-stream examples across docs and README: dropped references to ``MediaClient`` (which never shipped), standardized on ``FdMediaClient``; stream IDs corrected from ``cam0_main`` / ``cam0_sub`` to the device-exposed ``main`` / ``sub``; removed usages of the nonexistent ``get_stream_info()`` / ``get_raw_stream()``; corrected the ``get_encoded_stream()`` return semantics and the flattened ``frame.data`` misuse; added API docs for ``EncodedStreamClient`` / ``EncodedFrame``
- Fixed missing and misleading imports in the application examples: added ``import time`` to the multi-model example, ``import json`` to the GenAI example; dropped ``from grpc import RpcError`` from the error-handling example (the SDK raises ``RuntimeError``); removed unused ``numpy`` / ``sys`` imports
- Synced the Chinese inference page with the English one: translated the seven Usage sections that had been English-only since v0.3.0 (segmentation, OCR, CLIP image embeddings, CLIP text encoding, depth estimation, runtime postprocess-config update, GenAI) and added the ``SegmentationMask`` / ``OcrLine`` / ``Embedding`` / ``DepthMap`` data-type entries
- Added pipeline, frame-injection, overlay, and performance documentation, plus the local-inference application and ``perf_demo`` examples

v0.7.4 (2026-09-08)
-------------------

New Features
~~~~~~~~~~~~

- **Convenience-layer hardware routing** (sdk-hardware-routing P5): ``color.rgb_to_nv12`` / ``color.nv12_to_rgb`` and ``draw.draw_detections`` (NV12 arrays) ride the accel router's DSP legs by default, degrading to the software impls with accounting when unavailable; ``Frame.to_jpeg_bytes`` is hardware-first for keep-fd frames (zero-copy camera-daemon ``EncodeImage`` import) while in-memory frames keep the direct CPU encode so streaming hot loops pay no extra copy or RPC; software legs bind private impls only — the routing public functions cannot re-enter the router
- ``Frame.resize``'s DSP fast path now respects the router policy: ``SOFTWARE_ONLY`` skips the attempt, ``HARDWARE_ONLY`` raises on failure (refusing the silent CPU fallback), ``PREFER_HARDWARE`` reports via the new ``AccelRouter.note_degradation()`` (plus a typed ``policy`` property; externally reported fallbacks on unregistered ops stay visible in ``health()`` and fire ``on_degradation``)

Bug Fixes
~~~~~~~~~

- ``_encode_jpeg_hw`` hardcoded ``fmt="rgb24"``, so every NV12 keep-fd frame submit was rejected by ``_resolve_source`` as a format mismatch; frame-like sources now carry their handle's format
- ``dsp_format``'s software leg re-entered the router through the routing public functions (cross-op coupling); it now binds the color impls directly
- unified the color legs' ``ValueError`` contract (ndim / declared dims / even-size checks run before any daemon submit — caller errors no longer land in the degradation counters)

v0.7.3 (2026-09-07)
-------------------

New Features
~~~~~~~~~~~~

- **Hardware-first accel router** (``accel`` module): ``AccelRouter`` / ``RoutePolicy`` / ``health()`` degradation accounting + ``on_degradation`` hook / ``get_default_router()``; the default router registers DSP legs for ``resize_nv12`` / ``rgb_to_nv12`` / ``nv12_to_rgb`` / ``encode_jpeg`` / ``draw_detections`` plus the ``nms`` software leg
- **DSP annotation compositing** (dsp-offload P1): ``DspClient.blend_hw`` composites ARGB32 overlays onto NV12 in place on the DSP; ``draw.render_overlay_rgba`` renders boxes+captions as a minimal straight-alpha canvas reproducing the software raster's output
- **Async DSP jobs** (dsp-offload P2): every ``*_hw`` op takes ``wait=False`` with ``PendingDspJob`` exposing ``wait()`` / ``done()`` / ``release()``; ``blend_hw`` zero-copy keep-fd chain (refused by default — a state-dependent fatal path on current firmware); ``encode_jpeg_hw`` ``src_buffer_id`` passthrough skips the pixel read-back; keep-fd frame sources skip the ``ascontiguousarray`` pre-copy in the resize/convert legs; polygon and track shapes
- **Overlay annotation**: ``annotate()`` / ``annotate_result()`` push detections straight to camera-daemon's renderer over the event bus
- **Color conversion and NMS**: BT.601 limited-range RGB↔NV12 (numpy path when cv2 is missing); cross-class-aware ``postprocess.nms``

Bug Fixes
~~~~~~~~~

- Finished the inference codec refactor: stray ``self`` in ``_tensor_to_numpy`` / ``_parse_post_result`` broke the respective parse paths; removed the four full method implementations the thin codec delegates silently shadowed; added AST structural meta-tests to catch this class of drift

v0.7.2 (2026-09-03)
-------------------

Bug Fixes
~~~~~~~~~

- Stray ``self`` in the ``_parse_infer_response`` codec signature: after the 0.7.0 refactor every ``infer()`` / ``infer_batch()`` call raised ``TypeError``; added a regression test driving a real ``InferResponse``

v0.7.1 (2026-09-03)
-------------------

- Version aligned with ``setup.py``; no API changes

v0.7.0 (2026-09-02)
-------------------

New Features
~~~~~~~~~~~~

- **App developer toolkit** (developed as 0.6.0, never released separately, shipped with 0.7.0):

  - ``Frame.crop()`` / ``Frame.resize()`` / ``Frame.to_jpeg_bytes()`` — crop, three resize modes (stretch/letterbox/crop), JPEG encoding; falls back to numpy/PIL when cv2 is missing
  - ``draw`` module — detection visualization (``draw_boxes`` / ``draw_text`` / ``draw_detections``)
  - ``recording`` module — pure-Python TS muxing, HLS segments, event pre-record buffer (``TsWriter`` / ``HlsWriter`` / ``PrerollBuffer``), no ffmpeg required
  - ``web`` module — MJPEG streaming (``MjpegServer`` / ``MjpegStream`` / ``mjpeg_wsgi_app``)
  - **DeviceClient** native autofocus group of 6 methods (``start_oneshot_af`` / ``start_zoom_follow`` / ``get_autofocus_status`` / ``cancel_autofocus`` / ``set_af_windows`` / ``get_af_measurement``)
  - **CameraClient** imaging/infrared/privacy-mask/OSD/config group of 12 methods (incl. IR preset management, ``get_osd`` symmetric with ``set_osd``)
- Fixed ``InferenceClient.subscribe()`` silently dropping failed frames

Refactoring
~~~~~~~~~~~

- Internal layering: extracted the shared ``_transport`` primitives; split ``media`` into frame/encoded/fd_client, ``dsp`` into dsp_wire/dsp_format, ``inference`` into types/codec/genai. Facades keep every historical import path — **zero public API removals**
- DSP CPU fallback now raises a ``UserWarning`` instead of a silent log
- 2D-array grayscale inference input emits a ``DeprecationWarning`` (pass ``fmt=`` explicitly)
- ``EncodedStreamClient()`` default socket path is now ``/run/aipc/encoded/{stream}.sock`` (``ENCODED_SOCK_DIR`` env override; explicit paths still win)

Fixes
~~~~~

- Fixed an import crash on Python 3.8/3.9 (``from __future__ import annotations`` everywhere)

Other
~~~~~

- Added ``py.typed`` marker to the package; test suite grown to 270 green tests

v0.5.0 (2026-08-20)
-------------------

Refactoring
~~~~~~~~~~~

- Rebrand: ``hailo_ipc_sdk`` → ``neoruntime_ipc_sdk`` (breaking, no shim; functional names such as hailort/ne503/aipc are preserved)

Fixes
~~~~~

- Fixed dual-layout decoding of ``audio_capture`` video-layout headers

Other
~~~~~

- CI gained TestPyPI/PyPI trusted-publishing dual release flow

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
- Added video stream access (now provided by ``FdMediaClient`` / ``EncodedStreamClient``)
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
