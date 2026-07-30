# AIPC Platform Python SDK

Python SDK for AIPC EdgeCam AI Platform

## Installation

The SDK is not published to PyPI yet. Install it from this repository:

```bash
git clone https://github.com/camthink-ai/ne503-aipc-sdks.git
cd ne503-aipc-sdks
python -m pip install -e ./python
```

Or build and install a local wheel:

```bash
cd ne503-aipc-sdks/python
python -m pip install --upgrade build
python -m build --wheel
python -m pip install dist/hailo_ipc_sdk-*.whl
```

## Quick Start

### 1. AI Inference

```python
from hailo_ipc_sdk import InferenceClient

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
from hailo_ipc_sdk import EventClient

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
from hailo_ipc_sdk import DeviceClient, IrCutMode

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
from hailo_ipc_sdk import MediaClient

media = MediaClient()

# List available streams
streams = media.list_streams()
print(f"Available streams: {streams}")

# Get single frame
frame = media.get_frame("cam0_main")
if frame:
    print(f"Frame size: {frame.width}x{frame.height}, format: {frame.format}")
    rgb_image = frame.to_rgb()  # Convert to RGB format

# Subscribe to video stream
for frame in media.subscribe_raw("cam0_main"):
    # frame.image is numpy array
    process_frame(frame.image)

# Use callback
def process(frame):
    print(f"Frame: {frame.sequence}")

media.on_frame("cam0_main", process)
```

### 5. Plugin System

```python
from hailo_ipc_sdk import PluginDiscovery, PluginServer

# Discover plugins
discovery = PluginDiscovery()

# Find specific capability
endpoint = discovery.get("rtsp-server")
if endpoint and endpoint.is_available:
    channel = endpoint.connect()
    # Use gRPC channel to call plugin service

# Wait for plugin to be available
endpoint = discovery.require("video-recorder", timeout=30.0)

# Create plugin server
server = PluginServer("my-plugin")
grpc_server = server.create_server()
# Register gRPC service
grpc_server.start()
```

### 6. Complete Example: AI + Device Linkage

```python
from hailo_ipc_sdk import InferenceClient, DeviceClient, EventClient

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
| `subscribe(stream, model, fps, session_id, raw_output_only)` | str, str, int, str, bool | Iterator[Tuple[int, InferenceResult]] | Streaming inference |
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

### MediaClient

Video stream client for accessing video frames from shared memory.

**Methods:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `subscribe_raw(stream_id, skip_frames)` | str, bool | Iterator[Frame] | Subscribe to video stream |
| `get_frame(stream_id, timeout_ms)` | str, int | Frame | Get single frame |
| `get_stream_info(stream_id)` | str | StreamInfo | Get stream info |
| `list_streams()` | - | List[str] | List available streams |
| `on_frame(stream_id, callback)` | str, Callable | Thread | Callback subscription |
| `close()` | - | - | Close connection |

**Data Classes:**

- `Frame`: sequence, timestamp_ns, width, height, format, image, metadata
- `StreamInfo`: stream_id, width, height, format, fps, buffer_count
- `PixelFormat`: NV12, NV21, RGB, BGR, RGBA, BGRA, GRAY8, YUYV

### PluginDiscovery / PluginServer

Plugin system for service discovery and server implementation.

**PluginDiscovery:**
- `get(capability_id)` - Find plugin
- `require(capability_id, timeout)` - Wait for plugin availability
- `list_plugins()` - List all plugins
- `list_capabilities()` - List all capabilities
- `watch(callback)` - Watch for changes

**PluginEndpoint:**
- `connect()` - Create gRPC connection
- `is_available` - Availability status

**PluginServer:**
- `create_server(max_workers)` - Create gRPC server
- `start()` - Start service
- `stop(grace)` - Stop service

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

The generated protobuf stubs in `hailo_ipc_sdk/proto/` (`*_pb2.py` / `*_pb2_grpc.py`)
are **committed to the repo** so the SDK imports cleanly on a fresh clone, editable
install, and inside packaged wheels. They are re-included via `sdk/python/.gitignore`
and do not affect the global "no generated artifacts" policy for Go services.

If you change any `.proto` source, regenerate and re-commit them:

```bash
make sdk-proto           # regenerate stubs (inference/event/device/app/camera)
make sdk-proto-check     # verify committed stubs match .proto sources
git add sdk/python/hailo_ipc_sdk/proto/*_pb2*.py
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
pip install dist/hailo_ipc_sdk-*.whl
```

For older tooling, this also works:

```bash
python setup.py bdist_wheel
```

Do not commit files from `dist/`; publish them as release artifacts instead.

### Automated Wheel Builds

In the public `ne503-aipc-sdks` repository, GitHub Actions builds a wheel for
pull requests, pushes to `main`, and manual workflow runs. The wheel is uploaded
as a workflow artifact named `python-sdk-wheel`.

To create or update a GitHub Release, either push a version tag or run the
workflow manually with release publishing enabled:

```bash
git tag v0.3.0
git push origin v0.3.0
```

The release tag version must match the package version in `setup.py`.

PyPI and tarball packages are not published yet. Until they are available, use
source installs, local wheels, or GitHub Actions wheel artifacts.

## License

MIT License. See the repository `LICENSE` file.
