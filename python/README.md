# NeoRuntime Platform Python SDK

Python SDK for NeoRuntime EdgeCam AI Platform

中文接口使用手册：[SDK_API_ZH.md](SDK_API_ZH.md)

No device yet? The [device onboarding](https://camthink-ai.github.io/neoruntime-sdks/python/en/device-onboarding.html) page in the docs covers buying an NE503 and first-time login.

## Installation

Install from PyPI:

```bash
python -m pip install neoruntime-ipc-sdk
```

Pre-release builds are staged on TestPyPI for validation (dependencies still
come from PyPI):

```bash
python -m pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ neoruntime-ipc-sdk
```

Install from source:

```bash
git clone https://github.com/camthink-ai/neoruntime-sdks.git
cd neoruntime-sdks
python -m pip install -e ./python
```

Or build and install a local wheel:

```bash
cd neoruntime-sdks/python
python -m pip install --upgrade build
python -m build --wheel
python -m pip install dist/neoruntime_ipc_sdk-*.whl
```

## Learn it hands-on

**sdk-teaching-demo** is an installable interactive lesson for this SDK:
five live stations against real camera streams (subscribe + infer + draw,
platform overlay, hardware routing, `StreamPipeline`, events), each showing
the real code behind it plus the error lesson it prevents (DMA -2811,
overlay `None` vs `[]`, exit codes). Download
[sdk-teaching-demo-latest-arm64.neoapp](https://github.com/camthink-ai/neoruntime-apps/releases/download/showcase-bundles-latest/sdk-teaching-demo-latest-arm64.neoapp)
from the apps repository, or browse
[its source](https://github.com/camthink-ai/neoruntime-apps/tree/main/showcases/sdk-teaching-demo).

## Quick Start

### 1. AI Inference

```python
from neoruntime_ipc_sdk import InferenceClient

# Create inference client
inf = InferenceClient()

# Single inference
import numpy as np
image = np.zeros((1080, 1920, 3), dtype=np.uint8)
result = inf.infer(image, model_id="person_v1")
print(f"Detected {len(result.objects)} objects")

# Subscribe to video stream inference results
for frame_seq, result in inf.subscribe(stream="cam0_main", model="person_v1", fps=10):
    print(f"Frame {frame_seq}: Detected {len(result.objects)} objects")

    for obj in result.objects:
        print(f"  - {obj.label}: {obj.score:.2f} @ [{obj.bbox.x:.2f}, {obj.bbox.y:.2f}]")
```

### 2. Event Bus

```python
from neoruntime_ipc_sdk import EventClient

events = EventClient()

# Publish event
events.publish("app/alert", {
    "type": "person_detected",
    "zone": "A",
    "confidence": 0.95
})

# Subscribe to events (supports wildcards)
for event in events.subscribe("model/*/detections"):
    print(f"Received event: {event.topic}")
    print(f"Data: {event.payload}")

# Subscribe with callback
def on_alert(event):
    print(f"Alert: {event.payload}")

events.on_event("app/alert", on_alert)
```

### 3. Device Control

```python
from neoruntime_ipc_sdk import DeviceClient, IrCutMode

dev = DeviceClient()

# Light control
dev.set_white_light(80)           # White light brightness 80%
dev.set_ir_led(True)               # Turn on IR LED
dev.set_ircut(IrCutMode.NIGHT)     # Night vision mode

# PTZ control
dev.pan_left(speed=50)
dev.tilt_up(speed=30)
dev.ptz_stop()
dev.save_preset(1)                 # Save preset
dev.call_preset(1)                 # Call preset

# Zoom and focus
dev.zoom_in(speed=50)
dev.zoom_out(speed=50)
dev.set_zoom_level(0.5)             # Set zoom to 50%
dev.set_focus_level(0.5)            # Set focus to 50%
dev.focus_auto(True)
dev.lens_init()                     # Initialize lens module
dev.lens_reset_zero(zoom=True, focus=True)  # Reset both axes
dev.oneshot_autofocus()             # One-shot autofocus
dev.set_lens_limits(zoom_limit={"min_pos": 0, "max_pos": 1000})  # Set lens limits
status = dev.get_lens_status()      # Get lens status dict
dev.lens_goto_ratio_distance(2.0, 3.0)      # Zoom+focus linked move

# GPIO
dev.gpio_set(pin=10, value=True)
value = dev.gpio_get(pin=11)

# Get device status
status = dev.get_device_status()
print(f"SoC Temperature: {status.soc_temp_c}C")
print(f"White light level: {status.white_light_level}")
```

### 4. Video Stream Access

```python
from neoruntime_ipc_sdk import FdMediaClient

media = FdMediaClient()

# List available streams
streams = media.list_streams()
print(f"Available streams: {streams}")  # ['main', 'sub']

# Get single frame
frame = media.get_frame("main")
if frame:
    print(f"Frame size: {frame.width}x{frame.height}, format: {frame.format}")
    rgb_image = frame.to_rgb()  # Convert to RGB format

# Subscribe to video stream
for frame in media.subscribe("main"):
    # frame.image is the decoded numpy array
    process_frame(frame.image)

# Encoded stream (H.264/H.265): get_encoded_stream() returns a client
for packet in media.get_encoded_stream("main").subscribe():
    print(f"{packet.codec_name()} packet: {len(packet.data)} bytes")

# Use callback
def process(frame):
    print(f"Frame: {frame.sequence}")

media.on_frame("main", process)
```

### 5. Complete Example: AI + Device Linkage

```python
from neoruntime_ipc_sdk import InferenceClient, DeviceClient, EventClient

# Initialize clients
inf = InferenceClient()
dev = DeviceClient()
events = EventClient()

# Subscribe to person detection results
for frame_seq, result in inf.subscribe(stream="cam0_main", model="person_v1"):

    # Person detected
    if result.has_person():
        # Turn on white light
        dev.set_white_light(100)

        # Publish alert event
        events.publish("app/perimeter_alert", {
            "person_count": result.count_by_label("person"),
            "objects": [
                {"label": obj.label, "score": obj.score}
                for obj in result.objects
            ]
        })
    else:
        # Turn off white light
        dev.set_white_light(0)
```

### 7. Inference Pipeline (client-side pre/post)

For custom models whose postprocess is not handled server-side, or apps
that need their own thresholds — `InferencePipeline` composes
preprocessing (derived from the model's input spec, DSP-scaled for
keep-fd frames), inference, and a client-side YOLO decoder whose
thresholds are yours:

```python
from neoruntime_ipc_sdk import (
    FdMediaClient, InferencePipeline, YoloV8Postprocessor,
)

pipe = InferencePipeline.from_model(
    "custom_yolov8n",
    postprocessor=YoloV8Postprocessor(labels=["person", "car"], score_threshold=0.3),
)
for frame in FdMediaClient().subscribe("sub", keep_fd=True):
    out = pipe.run(frame)          # out.objects in source-frame coordinates
```

`Preprocessor` also works standalone: `tensor, meta = pre(frame)` with
`meta.to_source(x, y)` mapping model-input coordinates back to the frame.
When a family model fits, `InferenceClient.subscribe` remains the cheaper
path — see [PERFORMANCE.md](PERFORMANCE.md) for the decision table.

For long-running apps, `PipelineRunner` productises the whole loop — a
reader thread pulling frames into a latest-wins queue, a worker thread
running the pipeline and handing results to a sink, keep-fd handles
released on consumption, drops/latency/errors visible in `stats`:

```python
from neoruntime_ipc_sdk import FdMediaClient, InferencePipeline, PipelineRunner

media = FdMediaClient()
runner = PipelineRunner(
    source=media.subscribe("sub", keep_fd=True),
    pipeline=InferencePipeline.from_model("person_v1"),
    sink=lambda out, frame: print(out.objects),
    queue_size=1,            # latest-wins: always infer the newest frame
)
runner.start()
print(runner.stats)          # {"fps": ..., "dropped": ..., "recent_latency_ms": ...}
runner.stop()                # or: with PipelineRunner(...) as runner: ...
```

Sinks receive `(result, frame)` on the worker thread and must not retain
the frame beyond the call — the runner releases it right after.

### 8. App Toolkit: Drawing, Recording, and Web Streaming

Detection visualization on a live frame (pure numpy/PIL, cv2 optional):

```python
from neoruntime_ipc_sdk import FdMediaClient, draw_detections

frame = FdMediaClient().get_frame("main")
img = frame.crop(0, 0, 1920, 1080).resize(960, 540).to_rgb()

for seq, result in inf.subscribe(stream="cam0_main", model="person_v1"):
    annotated = draw_detections(img, result)      # boxes + labels + scores
    break
```

HLS recording from the encoded stream — no ffmpeg on the device needed:

```python
from neoruntime_ipc_sdk import EncodedStreamClient, HlsWriter

with HlsWriter("/srv/hls", segment_seconds=4.0, window=5) as hls:
    for frame in EncodedStreamClient("/run/aipc/encoded/main.sock").subscribe():
        hls.write(frame)                          # cuts on keyframes
# serve /srv/hls/ over HTTP and point hls.js at index.m3u8
```

MJPEG preview page — one WSGI app (mount in Flask) or a standalone server:

```python
from neoruntime_ipc_sdk import FdMediaClient, MjpegServer, MjpegStream

source = MjpegStream()
MjpegServer(port=8080, source=source).start()     # http://device:8080/
for frame in FdMediaClient().subscribe("sub"):
    source.push_frame(frame.resize(640, 360))     # slow clients just drop frames
```

## API Reference

### InferenceClient

AI inference client for model inference and streaming inference subscription.

**Methods:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `connect()` | - | - | Connect to service |
| `close()` | - | - | Close connection |
| `infer(image, model_id, timeout_ms, priority, session_id)` | ndarray, str, int, int, str | InferenceResult | Single inference |
| `infer_with_tensors(model_id, inputs, input_names, timeout_ms)` | str, List[ndarray], List[str], int | List[ndarray] | Multi-tensor inference |
| `subscribe(stream, model, fps, session_id, raw_output_only, max_consecutive_failures, queue_size)` | str, str, int, str, bool, Optional[int], Optional[int] | Iterator[Tuple[int, InferenceResult]] | Streaming inference; failed frames are skipped with a warning and a `RuntimeError` is raised after 10 consecutive failures (0/None disables). The client-side queue is bounded (`queue_size`, default 100): a slow consumer drops its *oldest* queued results — counted on the iterator's `dropped` attribute and reported in a throttled warning — instead of growing memory without bound (0/None = unbounded) |
| `register_model(model_path, model_id, inputs, outputs)` | str, str, List[Dict], List[Dict] | str | Register model |
| `unregister_model(model_id)` | str | - | Unregister model |
| `list_models()` | - | List[ModelInfo] | List models |
| `get_model_info(model_id)` | str | ModelInfo | Get model info |
| `get_stats()` | - | Dict | Get statistics |
| `create_session(session_id, ...)` | str, ... | str | Create session |
| `destroy_session(session_id)` | str | - | Destroy session |

**Data Classes:**

- `BoundingBox`: x, y, width, height
- `DetectedObject`: label, score, bbox, class_id, track_id
- `InferenceResult`: frame_sequence, timestamp_ns, objects, classifications, landmarks, raw_outputs
- `ModelInfo`: model_id, model_path, version, inputs, outputs

### EventClient

Event bus client for publishing and subscribing to events.

**Methods:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `publish(topic, payload, persistent, ttl_ms, metadata)` | str, dict, bool, int, dict | str | Publish event |
| `publish_batch(events, persistent)` | List[dict], bool | - | Batch publish |
| `subscribe(topic, filters, queue_size, drop_old)` | str, dict, int, bool | Iterator[Event] | Subscribe to events |
| `on_event(topic, callback, filters)` | str, Callable, dict | Thread | Callback subscription |
| `unsubscribe(topic)` | str | - | Unsubscribe |
| `list_topics()` | - | List[TopicInfo] | List topics |
| `get_topic_info(topic)` | str | TopicInfo | Get topic info |
| `get_stats()` | - | Dict | Get statistics |

**Data Classes:**

- `Event`: topic, payload, source, event_id, timestamp_ns, metadata
- `TopicInfo`: topic, subscriber_count, total_messages, last_message_ts

### DeviceClient

Device control client for controlling camera peripherals.

**Light Control:**
- `set_white_light(level: int)` - Set white light brightness (0-100)
- `set_ir_led(on: bool)` - IR LED switch
- `set_ircut(mode: IrCutMode)` - IR-Cut mode

**PTZ Control:**
- `pan_left(speed: int)` / `pan_right(speed: int)` - Pan left/right
- `tilt_up(speed: int)` / `tilt_down(speed: int)` - Tilt up/down
- `ptz_stop()` - Stop PTZ
- `save_preset(preset_id: int)` / `call_preset(preset_id: int)` - Preset operations

**Lens Control:**
- `zoom(speed: int)` - Zoom (-100 ~ 100)
- `zoom_in(speed: int)` / `zoom_out(speed: int)` - Zoom in/out
- `set_zoom_level(level: float)` - Set zoom level (0-1)
- `focus(speed: int)` - Focus (-100 ~ 100)
- `focus_in(speed: int)` / `focus_out(speed: int)` - Focus in/out
- `set_focus_level(level: float)` - Set focus level (0-1)
- `focus_auto(enable: bool)` - Auto focus
- `oneshot_autofocus(timeout: float)` - One-shot autofocus (enable → wait → disable)
- `lens_init()` - Initialize lens module
- `lens_reset_zero(zoom: bool, focus: bool)` - Reset lens axes to zero
- `set_lens_limits(zoom_limit, focus_limit)` - Set lens axis position limits
- `lens_goto_ratio_distance(zoom_ratio: float, focus_distance_m: float)` - Zoom+focus linked move
- `control_iris(open: bool)` - Open/close iris
- `set_iris_target(target: int)` - Set iris target value
- `get_lens_status()` - Get lens status dict (positions, states, limits)

**Autofocus (native jobs):**
- `start_oneshot_af()` - Start a one-shot AF job, returns `AfJob`
- `start_zoom_follow(ratio: float)` - Start continuous AF following a zoom ratio, returns `AfJob`
- `get_autofocus_status()` - Poll the AF engine, returns `AfStatus(state, progress, busy, ...)`
- `cancel_autofocus(job_id: int = 0)` - Cancel a running AF job
- `set_af_windows(enabled, windows, stream_id: str = "main")` - Restrict AF metering to windows
- `get_af_measurement()` - Read AF statistics, returns `AfMeasurement(focus_energy, mean_luma, ...)`

> **Known device limitation:** on current firmware (verified on
> a test device, 2026-08) the lens HAL bridge rejects `set_af_windows`
> and `get_af_measurement` with *"not yet supported"*. The SDK-side
> plumbing is complete; both calls will start working once the device
> firmware adds bridge support. Oneshot, zoom-follow, status, and cancel
> all work today.

**GPIO:**
- `gpio_set(pin: int, value: bool)` - GPIO output
- `gpio_get(pin: int)` - GPIO input

**Wiegand:**
- `set_wiegand_out(channel: int, enable: bool)` - Wiegand output control
- `get_wiegand_out(channel: int)` - Wiegand output state query

**RS-485:**
- `rs485_init(baudrate: int, config: str)` - RS-485 initialization
- `rs485_deinit()` - RS-485 deinitialization
- `rs485_tx(data: bytes)` - RS-485 data transmission

**Status Query:**
- `get_device_status()` - Get device status
- `subscribe_events()` - Subscribe to device events

**Enums:**
- `IrCutMode`: AUTO, DAY, NIGHT

### AppClient

Application container management client.

**Lifecycle:**
- `install_app(manifest_path, image_path)` - Install application
- `start_app(app_id)` - Start application
- `stop_app(app_id, timeout_seconds)` - Stop application
- `restart_app(app_id, timeout_seconds)` - Restart application (stop + start)
- `uninstall_app(app_id, keep_logs)` - Uninstall application

**Query:**
- `list_apps()` - List all applications
- `get_app(app_id)` - Get application info
- `get_app_stats(app_id)` - Get application statistics
- `get_logs(app_id, max_lines, follow)` - Stream application logs
- `get_logs_text(app_id, max_lines, follow)` - Stream logs as text

**Other:**
- `register_web_url(path)` - Register web access path

### FdMediaClient (`media`)

Video stream client receiving frames over UDS (dma-buf fds, decoded on receive by default).

**Methods:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `subscribe(stream_id, skip_frames, keep_fd)` | str, int/bool, bool | Iterator[Frame] | Subscribe to video stream; `skip_frames` is a decimation interval — 1 (or the historical `True`/`False`) yields every frame, N>1 yields every Nth (decimated keep-fd frames are released back to the daemon immediately) |
| `subscribe_raw(stream_id, skip_frames, keep_fd)` | str, int/bool, bool | Iterator[Frame] | Same as `subscribe` |
| `get_frame(stream_id, timeout_ms, keep_fd)` | str, int, bool | Frame \| None | Get single frame |
| `get_encoded_stream(stream_id)` | str | EncodedStreamClient | H.264/H.265 Annex-B stream client |
| `list_streams()` | - | List[str] | List active stream IDs from the camera daemon (falls back to `main` / `sub` when the service is unreachable) |
| `get_rtsp_url(stream_id, host, port)` | str, str, int | str | RTSP playback URL (needs RTSP enabled) |
| `on_frame(stream_id, callback)` | str, Callable | Thread | Callback subscription |
| `close()` | - | - | Close connection |

**Data Classes:**

- `Frame`: sequence, timestamp_ns, width, height, format, image, metadata, handle
- `frame.image` / `frame.to_array()` - Decoded numpy array (H, W, C) or (H*3//2, W) for NV12
- `Frame.crop(x, y, w, h)` - New cropped Frame (NV12 needs even x/y/w/h)
- `Frame.resize(width, height, mode="letterbox", pad_value=114)` - New resized Frame (`stretch` / `letterbox` / `crop`)
- `Frame.to_jpeg_bytes(quality=85)` - JPEG bytes (cv2 fast path, PIL fallback)
- `frame.release()` - Return a `keep_fd=True` buffer to the daemon (idempotent)
- `frame.metadata["transform"]` - Affine geometry of the last crop/resize chain: `dst = src * scale + origin` per axis (composed across chained calls). Map model-input coordinates back to the source frame with `src = (dst - origin) / scale` — no hand-derived letterbox maths in the app
- `EncodedStreamClient` / `EncodedFrame`: encoded stream subscription; `EncodedFrame.data` (Annex-B bytes), `.is_keyframe()`, `.codec_name()`
- `StreamInfo`, `PixelFormat`: NV12, NV21, RGB, BGR, RGBA, BGRA, GRAY8, YUYV

### OverlayClient (`overlay`)

Draws results on the device's **hardware overlay**: camera-daemon bakes boxes and zone polygons into the encoded stream, so the app never rasterizes pixels (use the `draw` module instead when you own the pixels, e.g. your own MJPEG preview). The overlay must be enabled first.

**Methods:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `enable(show_label, show_confidence, line_thickness)` | bool, bool, int | - | Turn the overlay on with the given appearance |
| `disable()` | - | - | Turn the overlay off |
| `configure(enabled, show_label, show_confidence, line_thickness, box_color, label_color, font_size, strict_frame_lock, strict_wait_cap_ms)` | see notes | - | Full appearance control. Colors are ARGB ints. `strict_frame_lock=True` binds each box to the frame it was computed from (the bake site waits, bounded by `strict_wait_cap_ms`); `None` keeps the daemon's current setting |
| `apply(config)` | OverlayConfig | - | Apply an `OverlayConfig` object |
| `annotate(stream_id, detections, polygons, ttl_ms, ...)` | str, list, list, int | str | Push detections and/or zone polygons for one stream (event id) |
| `annotate_result(stream_id, result, ttl_ms, ...)` | str, InferenceResult | str | Push whichever section of an `InferenceResult` is populated (detections, then classifications, landmarks, OCR lines) |
| `close()` | - | - | Close connection |

**Data Classes:**

- `OverlayConfig`: enabled, show_label, show_confidence, line_thickness, box_color, label_color, font_size, strict_frame_lock, strict_wait_cap_ms

Results expire ~two frame periods after the last event, so call `annotate` at a few Hz while detections are fresh. The None-vs-empty distinction matters: `detections=None` leaves the stream's previous boxes untouched (polygons can ride alone), while `detections=[]` **clears** them — same for polygons. Polygon points are normalized [0, 1] floats (2-128 points each, at most 16 polygons per call); `ttl_ms` must be a positive int (omitted = derived from the stream fps).

```python
from neoruntime_ipc_sdk import OverlayClient

oc = OverlayClient()
oc.enable()
for result in inference.subscribe("main", "person_v1"):
    oc.annotate("main", result.objects)   # fresh boxes every frame
oc.annotate("main", detections=[])        # done: clear stale boxes
oc.annotate("main", polygons=[{"points": ZONE, "label": "yard"}])
```

### StreamPipeline (`stream_pipeline`)

One-call pipeline: subscribe a registered model to a camera stream, draw every result on the hardware overlay, and yield the same results to the app. Single-shot (create a new instance per run) and usable as a context manager.

```python
from neoruntime_ipc_sdk import StreamPipeline

pipe = StreamPipeline(
    "main", "person_v1", fps=10,
    polygons=[{"points": [[0, 0], [1, 0], [1, 1], [0, 1]], "label": "zone"}],
)
pipe.start()
for sequence, result in pipe.results():
    ...   # drawing already happened on the overlay
pipe.stop()   # clears boxes and zones
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `start()` | - | StreamPipeline | Subscribe, apply overlay config / static zones, start drawing |
| `stop()` | - | - | Stop the worker, clear what was drawn, close owned clients. Idempotent, safe to call from `on_result` |
| `results()` | - | Iterator[(int, InferenceResult)] | Yield `(frame_sequence, result)`; bounded drop-oldest queue (counted in `status()`) |
| `status()` | - | StreamPipelineStatus | Health snapshot incl. pass-through subscribe stats |

**Constructor notes:** `draw=False` keeps the encoded stream clean (results still flow to `results()`); `min_score` / `labels` filter *drawing only* — a fully-filtered result still publishes an empty detection list, clearing stale boxes; `on_result` (worker thread) may replace or drop each result; `overlay_config` accepts an `OverlayConfig`; `ttl_ms` overrides per-event validity; the subscription runs at stream geometry, so register the model for the stream's dimensions.

**Data Classes:**

- `StreamPipelineStatus`: running, results_seen, results_annotated, annotate_errors, result_queue_drops, subscribe_dropped, last_error, last_latency_ms, avg_latency_ms, last_skew_us, avg_skew_us

### Diagnostics

`diagnostics()` (never raises) snapshots the SDK's execution environment — the first stop when an app feels slow:

```python
from neoruntime_ipc_sdk import diagnostics

report = diagnostics()
report["optional_deps"]["cv2"]          # {"available": bool, "version": ...}
report["services"]["camera_control"]    # {"path", "exists", "connectable"}
report["media"]["encoded_dir"]["streams"]
report["accel_router"]["ops"]["nv12_to_rgb"]["backend"]   # "hardware" | "software"
```

Without cv2 installed, conversions/resize/JPEG run on pure-numpy fallbacks that are 10-50x slower at frame rate — the SDK warns once per operation on that path.

`diagnostics.check()` grades the snapshot against an app's requirements — a deployment gate:

```python
from neoruntime_ipc_sdk.diagnostics import check

check(["inference", "camera_sock"]).raise_if_unhealthy()   # RuntimeError listing failures
# live model/stream probes are opt-in:
check(["model_registered", "stream_active"],
      inference=InferenceClient(), model_id="person_v1",
      camera=CameraClient(), stream_id="main").raise_if_unhealthy()
```

Hardware/software routing is one app-wide knob (see `AccelRouter.health()` for what is actually serving each operation):

```python
from neoruntime_ipc_sdk import set_route_policy

set_route_policy("software_only")   # baseline/benchmark; "prefer_hardware" (default), "hardware_only" (refuse silent CPU fallback)
```

### Architecture and stability

The SDK is layered, and the middle layer is a stability contract:

1. **Daemon clients** — `InferenceClient`, `FdMediaClient`, `CameraClient`, `DeviceClient`, `EventClient`, `AppClient`, `OverlayClient`, `AudioClient`: communication, timeouts, reconnection, resource release.
2. **Data & algorithm primitives** *(stable contract)* — `Frame`/`FrameHandle`, `PreprocessMeta`, `DetectedObject`, and the callable protocols `preprocessor(frame) -> (tensor, meta)` / `postprocessor(raw_outputs, meta) -> objects`. The built-in `Preprocessor` and `YoloV5/V8Postprocessor` implement them; custom decoders (RetinaFace, OCR, pose...) can replace them freely. Breaking changes here are gated behind a minor-version bump with deprecation warnings.
3. **App pipeline** — `InferencePipeline` (single pass) and `PipelineRunner` (long-running): composition, backpressure (latest-wins with drop counters), latency/error stats, frame ownership.

### Recording (`recording`)

Pure-python MPEG-TS muxing of `EncodedFrame` Annex-B payloads — no ffmpeg required.

- `TsWriter(path, codec="h264")` - Single-file .ts event clip
- `HlsWriter(out_dir, segment_seconds=6.0, window=5)` - Keyframe-aligned HLS segments + live `index.m3u8`
- `PrerollBuffer(seconds=10.0)` - Ring buffer; `push(frame)`, `dump("event.ts")` writes "seconds before the event"

### Web Streaming (`web`)

MJPEG helpers for app preview pages.

- `MjpegStream()` - Thread-safe latest-frame holder; `push_frame(frame, quality=85)` / `push_jpeg(data)`
- `mjpeg_wsgi_app(source, fps=15)` - WSGI callable — mount straight into Flask
- `MjpegServer(port=8080, host="0.0.0.0", source=...)` - Standalone threaded HTTP server

### Drawing (`draw`)

Detection visualization on RGB numpy arrays (returns new arrays, input untouched).

- `draw_boxes(image, boxes, labels=None, scores=None, color=(0,255,0), thickness=2)`
- `draw_text(image, text, xy, color=(255,255,255), font_scale=0.5, thickness=1)`
- `draw_detections(image, result_or_objects, color=None)` - Accepts `InferenceResult` / `DetectedObject` / raw `(x1,y1,x2,y2)` tuples

### Audio (`audio`, `audio_stream`)

Audio HAL via camera-daemon: device enumeration, capture/playback control, and two-way-talk PCM streaming (`AudioClient`); captured frames arrive over UDS (`AudioStreamClient`).

**Methods (`AudioClient`):**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `list_capture_devices()` / `list_playback_devices()` | - | List[AudioDevice] | Enumerate audio devices |
| `start_capture(device, sample_rate, channels, codec, bitrate)` | str, int, int, str, int | - | Start capture (0/empty = daemon defaults) |
| `stop_capture()` | - | - | Stop capture |
| `start_playback(device, sample_rate, channels)` | str, int, int | - | Start playback |
| `stop_playback()` | - | - | Stop playback |
| `get_status()` | - | AudioStatus | Current audio status |
| `set_config(volume, mute, ...)` | float, bool | - | Update volume/mute/codec (defaults keep current values) |
| `stream_pcm(pcm_iter, sample_rate, channels, fmt)` | Iterator[bytes], int, int, str | - | Stream PCM chunks to the device (two-way talk) |
| `stream_pcm_file(path, chunk_size, ...)` | str, int | - | Stream a raw PCM file |

**Data Classes:**

- `AudioDevice`: name, description
- `AudioStatus`: capturing, playing, device, sample_rate, channels, codec, volume, mute
- `AudioFrame` (from `AudioStreamClient`): codec (0=pcm, 1=aac, 2=g711a, 3=g711u), flags (bit0 = keyframe), pts_ns, sample_rate, channels, bits_per_sample, `data` bytes; helpers `is_keyframe()`, `codec_name()`, `duration_ms()`
- `AudioStreamClient(socket_path=None)`: `subscribe()` → Iterator[AudioFrame], `on_frame(cb)`, `close()`; default socket `/run/aipc/encoded/audio_capture.sock` (env `AUDIO_CAPTURE_SOCK_PATH`)

```python
from neoruntime_ipc_sdk import AudioClient, AudioStreamClient

audio = AudioClient()
audio.start_capture(codec="aac", sample_rate=48000)
for frame in AudioStreamClient().subscribe():
    print(frame.codec_name, len(frame.data))
audio.stop_capture()
```

### DSP Offload (`dsp`)

Hardware image ops on the camera-daemon DSP service: resize, crop, convert, blend, and JPEG encode without burning CPU. Apps usually reach this indirectly through the accel router (`set_route_policy` / `AccelRouter.health()`); use `DspClient` directly for ops the router does not cover, or to pre-allocate buffer pools in hot loops.

- `DspClient.resize_hw(src, width, height, fmt=None, ...)` - HW resize (bilinear; `stretch` scaling)
- `DspClient.crop_hw(src, x, y, width, height, dst_width=None, dst_height=None, ...)` - HW crop, optional resize in the same job
- `DspClient.multi_crop_hw(src, rects, ...)` - Many crop/resize windows in one job
- `DspClient.convert_hw(src, dst_fmt, ...)` - `nv12`/`rgb24`/`gray8` conversion, dimensions kept; the supported pair matrix is device-dependent, and a pair the firmware refuses falls back to CPU when `cpu_fallback=True` (the default)
- `DspClient.blend_hw(base, overlays, ...)` - Composite ARGB32 overlays onto an NV12 base
- `DspClient.encode_jpeg_hw(src, quality=85)` - One JPEG frame, returns bytes
- `DspClient.alloc_buffers(width, height, fmt="nv12", count=1)` → `DspBufferPool` - Pre-allocate daemon-side buffers so hot-loop calls only write, submit, read
- `DspClient.import_frame(handle)` / `release_buffer(buffer_id)` - Import a `FrameHandle`'s dma-bufs into the daemon registry / free an id

Every `*_hw` method takes `cpu_fallback=True` by default: when the daemon lacks the DSP surface, array-source calls warn and compute on CPU; pass `False` to make unavailability raise instead. With `wait=False` a call returns a `PendingDspJob` (`done(timeout_s)`, `wait_result()`, `wait()`) instead of blocking.

**Data Classes:**

- `DspBufferPool`: `write(index, arr)` / `read(index)` / `release()` - Pre-allocated daemon-side buffers
- `DspBufferRef`: buffer_id, width, height, fmt; `read()` / `release()` - Zero-copy result handle (`out="ref"`)
- `PendingDspJob`: `done(timeout_s)` / `wait_result()` / `wait()` - Async job handle (`wait=False`)
- `DspError` - DSP failures (allocation, import, firmware refusals)

```python
from neoruntime_ipc_sdk import DspClient

dsp = DspClient()
small = dsp.resize_hw(frame.image, 640, 384, fmt="nv12")
# hot loop: allocate once, then every call only writes / submits / reads
pool = dsp.alloc_buffers(frame.width, frame.height, fmt="nv12", count=2)
```

### Config

Configuration management, reads from environment variables.

**Static Methods:**
- `get_app_id()` - Get application ID
- `get_inference_endpoint()` - AI Runtime endpoint
- `get_event_bus_endpoint()` - Event Bus endpoint
- `get_device_control_endpoint()` - Device Control endpoint
- `get_shm_base_path()` - SHM base path
- `is_debug()` - Debug mode
- `get_log_level()` - Log level

## Environment Variables

SDK automatically reads configuration from environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ID` | unknown | Application ID |
| `AI_RUNTIME_ENDPOINT` | unix:///run/aipc/ai-runtime.sock | AI Runtime endpoint |
| `EVENT_BUS_ENDPOINT` | unix:///run/aipc/event-bus.sock | Event Bus endpoint |
| `DEVICE_CONTROL_ENDPOINT` | unix:///run/aipc/device-control.sock | Device Control endpoint |
| `SHM_BASE_PATH` | /run/aipc/shm | SHM base path |
| `DEBUG` | 0 | Debug mode |
| `LOG_LEVEL` | INFO | Log level |

## Development

### Protobuf Stubs

The generated protobuf stubs in `neoruntime_ipc_sdk/proto/` (`*_pb2.py` / `*_pb2_grpc.py`)
are **committed to the repo** so the SDK imports cleanly on a fresh clone, editable
install, and inside packaged wheels. They are re-included via `sdk/python/.gitignore`
and do not affect the global "no generated artifacts" policy for Go services.

If you change any `.proto` source, regenerate and re-commit them:

```bash
make sdk-proto           # regenerate stubs (inference/event/device/app/camera)
make sdk-proto-check     # verify committed stubs match .proto sources
git add sdk/python/neoruntime_ipc_sdk/proto/*_pb2*.py
```

### Run Tests

```bash
cd sdk/python
pip install -e ".[dev]"
pytest tests/
```

### Build Package

```bash
python setup.py build
```

### Build Wheel

The recommended way to build a distributable wheel is:

```bash
python -m pip install --upgrade build
python -m build --wheel
ls dist/*.whl
```

The generated wheel is written to `dist/`, for example:

```bash
pip install dist/neoruntime_ipc_sdk-*.whl
```

For older tooling, this also works:

```bash
python setup.py bdist_wheel
```

Do not commit files from `dist/`; publish them as release artifacts instead.

### Automated Wheel Builds

In the public `neoruntime-sdks` repository, GitHub Actions builds and tests
the wheel and sdist for pull requests, relevant pushes to `main`, and manual
workflow runs. Pull request and `main` builds do not retain a workflow artifact;
tags matching `v*` and manual runs upload one named `python-sdk-dist`.

Pushing a `v*` tag (or running the workflow manually with publishing enabled)
creates a GitHub Release with the distributions attached and publishes to
TestPyPI and then PyPI:

```bash
git tag v0.8.1
git push origin v0.8.1
```

The release tag version must match the package version in `setup.py` and
`neoruntime_ipc_sdk/__init__.py`.

## License

MIT License. See the repository `LICENSE` file.
