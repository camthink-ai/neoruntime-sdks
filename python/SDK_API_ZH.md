# NeoRuntime Python SDK 中文接口使用手册

本文档对应 `neoruntime-ipc-sdk 0.8.1`，以
`neoruntime_ipc_sdk.__all__` 中公开导出的接口为准。文中的服务端点默认指向
NeoRuntime 设备上的 Unix Domain Socket；在非设备环境中调用硬件接口通常会收到
连接错误。

## 目录

1. 安装与公共约定
2. AI 推理
3. 视频帧与编码流
4. 预处理、后处理与推理管线
5. 事件总线
6. 设备控制
7. 相机控制
8. 音频
9. 叠加与绘图
10. 帧注入
11. DSP、颜色转换与加速路由
12. 录像与 Web 预览
13. 应用管理
14. 插件
15. 配置与诊断
16. 常见组合

## 1. 安装与公共约定

```bash
python -m pip install neoruntime-ipc-sdk

# 从本仓库安装开发版本
python -m pip install -e ./python
```

建议从包顶层导入公开接口：

```python
import neoruntime_ipc_sdk as sdk

print(sdk.__version__)
```

大多数客户端都支持上下文管理器。离开 `with` 块时会关闭 gRPC 通道、Unix
Socket 或设备缓冲区：

```python
from neoruntime_ipc_sdk import CameraClient

with CameraClient() as camera:
    print(camera.get_stream_status())
```

通用错误约定：

- 参数错误通常抛出 `ValueError`。
- 平台返回失败状态时通常抛出 `RuntimeError`。
- gRPC 通信错误抛出 `grpc.RpcError` 的子类。
- Unix Socket 断开可能抛出 `ConnectionError` 或 `OSError`；流式订阅接口通常会自动重连。
- 超时接口返回 `None` 或抛出超时异常，具体以各接口说明为准。

## 2. AI 推理

### 2.1 `InferenceClient`

创建方式：`InferenceClient(endpoint=None)`。未指定 `endpoint` 时读取
`AI_RUNTIME_ENDPOINT`，默认 `unix:///run/aipc/ai-runtime.sock`。首次业务调用会自动
连接，也可以显式调用 `connect()`。

```python
import numpy as np
from neoruntime_ipc_sdk import InferenceClient

image = np.zeros((640, 640, 3), dtype=np.uint8)
with InferenceClient() as client:
    result = client.infer(image, model_id="person_v1", timeout_ms=5000)
    for obj in result.objects:
        print(obj.label, obj.score, obj.bbox.to_xyxy())
```

| 接口 | 使用方法 |
| --- | --- |
| `connect()` / `close()` / `connected` | 建立连接、释放连接、查询连接状态。优先使用 `with` 自动管理。 |
| `infer(image, model_id, timeout_ms=5000, priority=4, session_id="")` | 对一张 `numpy.ndarray`、保留 DMA-BUF 的 NV12 `Frame`/`FrameHandle` 或 NV12 `DspBufferRef` 同步推理，返回 `InferenceResult`。后两类输入走 buffer ID 零拷贝路径；普通复制帧应传 `frame.to_array()` 或 `frame.to_rgb()`。 |
| `infer_async(...)` | 参数同 `infer`，立即返回 `concurrent.futures.Future`；调用 `future.result()` 取得结果。 |
| `infer_batch(items, timeout_ms=10000)` | 批量提交 `list[BatchInferItem]`，按输入顺序返回 `list[InferenceResult]`。 |
| `infer_batch_async(...)` | `infer_batch` 的异步版本，返回 `Future`。 |
| `infer_with_tensors(model_id, inputs, input_names=None, timeout_ms=5000)` | 直接传入一个或多个输入张量，返回原始输出张量列表，适合多输入模型。 |
| `subscribe(stream, model, fps=10, session_id="", raw_output_only=False, max_consecutive_failures=10, queue_size=100)` | 订阅平台调度的流式推理，迭代产生 `(frame_sequence, InferenceResult)`。消费者过慢时有界队列丢弃最旧结果；可从迭代器的 `dropped`、`last_latency_ms`、`avg_latency_ms`、`last_skew_us` 读取观测数据。 |
| `register_model(model_path, model_id=None, owner_id=None, model_type=None, model_variant=None, inputs=None, outputs=None, batch_size=1)` | 向 ai-runtime 注册模型，返回实际模型 ID。路径必须是设备/容器可访问的模型文件。 |
| `unregister_model(model_id)` | 注销模型。仍在使用中的模型是否允许注销由平台决定。 |
| `list_models()` | 返回全部 `ModelInfo`。 |
| `get_model_info(model_id)` | 返回指定 `ModelInfo`；不存在时返回 `None`。 |
| `get_stats(sampling_window_ms=None)` | 返回系统和各模型的负载、延迟、错误等统计字典。 |
| `create_session(session_id, app_id="", allowed_models=None, max_qps=0, max_concurrent=0, priority=4)` | 创建受配额约束的推理会话，返回会话 ID。0 表示不限制相应配额。 |
| `destroy_session(session_id)` | 销毁会话并释放关联资源。 |
| `update_postprocess_config(model_id, config_json)` | 在线更新模型后处理 JSON 配置，成功返回 `True`。 |

流式推理：

```python
with InferenceClient() as client:
    subscription = client.subscribe("main", "person_v1", fps=10, queue_size=8)
    try:
        for sequence, result in subscription:
            print(sequence, result.count_by_label("person"))
    finally:
        subscription.cancel()       # 可从任意线程安全停止
```

批量和异步推理：

```python
from neoruntime_ipc_sdk import BatchInferItem

items = [
    BatchInferItem(image=image, model_id="person_v1"),
    BatchInferItem(image=image, model_id="vehicle_v1", priority=3),
]
with InferenceClient() as client:
    results = client.infer_batch(items)
    future = client.infer_async(image, "person_v1")
    one_result = future.result(timeout=6)
```

### 2.2 GenAI 接口

以下方法由 `InferenceClient` 直接提供：

| 接口 | 使用方法 |
| --- | --- |
| `encode_text(text, timeout_ms=5000)` | 使用 NPU 上的 CLIP 文本编码器生成 `list[float]` 向量。 |
| `genai_create_session(hef_path, kind="llm", lora_name="", optimize_memory=False)` | 创建 LLM/VLM 会话，返回会话 ID。 |
| `genai_generate(session_id, messages, images=None, stop_tokens=None, temperature=0.0, top_p=1.0, top_k=0, max_tokens=512, do_sample=False)` | 流式产生文本 token；VLM 可同时传入图片字节列表。 |
| `genai_abort(session_id)` | 中止正在生成的请求。 |
| `genai_destroy_session(session_id)` | 释放 GenAI 会话和模型资源。 |

```python
with InferenceClient() as client:
    sid = client.genai_create_session("/data/models/llm.hef")
    try:
        for token in client.genai_generate(sid, ["请介绍这张图片"], max_tokens=128):
            print(token, end="", flush=True)
    finally:
        client.genai_destroy_session(sid)
```

### 2.3 推理数据类型

| 类型 | 主要字段或方法 |
| --- | --- |
| `BatchInferItem` | `image`、`model_id`、`timeout_ms`、`priority`，用于批量推理。 |
| `BoundingBox` | `x, y, width, height`；`to_xyxy()` 转为 `(x1,y1,x2,y2)`，`to_xywh()` 返回原表示。 |
| `DetectedObject` | `label, score, bbox, class_id, track_id`。 |
| `Classification` | `type, class_id, label, confidence`。 |
| `LandmarkPoint` | `x, y, confidence`。 |
| `LandmarkSet` | `type, points`。 |
| `SegmentationMask` | 类别、置信度、边框和 RLE 掩码；`to_numpy_mask()` 解码为 NumPy 掩码。 |
| `OcrLine` | `text, confidence, bbox`。 |
| `Embedding` | `dim, data`。 |
| `DepthMap` | `width, height, data`。 |
| `InferenceResult` | 包含上述结果列表以及 `raw_outputs`、推理/排队/硬件耗时和 `skew_us`；提供 `has_person()`、`count_by_label(label)`、`get_objects_by_label(label)`。 |
| `ModelInfo` | `model_id, model_path, version, inputs, outputs, batch_size` 及资源估算信息。 |

## 3. 视频帧与编码流

### 3.1 `FdMediaClient`

创建方式：`FdMediaClient(socket_path=None)`。默认读取 `CAMERA_SOCK_PATH`，否则
连接 `/run/aipc/camera.sock`。

| 接口 | 使用方法 |
| --- | --- |
| `get_frame(stream_id, timeout_ms=5000, keep_fd=False)` | 获取一帧；超时返回 `None`。`keep_fd=False` 会复制像素并立即归还平台缓冲；`True` 保留 DMA-BUF，使用后必须 `frame.release()`。 |
| `subscribe(stream_id, skip_frames=1, keep_fd=False)` | 连续读取帧并自动重连。`skip_frames=N` 表示每 N 帧取一帧。 |
| `subscribe_raw(...)` | 与 `subscribe` 等价的底层兼容入口。 |
| `on_frame(stream_id, callback)` | 在后台守护线程中逐帧调用回调，返回线程对象。 |
| `retained_frames` | 当前仍未释放的 `keep_fd` 帧数量。数量持续升高会耗尽相机缓冲池。 |
| `get_encoded_stream(stream_id="main", socket_dir=None)` | 返回 `EncodedStreamClient`，读取 H.264/H.265 Annex-B 包。 |
| `list_streams()` | 查询活动流 ID；控制服务不可用时回退为 `main`、`sub`。 |
| `get_rtsp_url(stream_id="main", host="192.0.2.72", port=8554)` | 组合 RTSP URL；使用前需通过相机接口启用 RTSP。 |
| `close()` | 释放保留帧并关闭所有流连接。 |

复制取帧与零拷贝取帧：

```python
from neoruntime_ipc_sdk import FdMediaClient

with FdMediaClient() as media:
    frame = media.get_frame("main", timeout_ms=1000)
    if frame is not None:
        rgb = frame.to_rgb()

    for frame in media.subscribe("sub", skip_frames=2, keep_fd=True):
        with frame:                 # 退出时自动 release DMA-BUF
            run_zero_copy(frame)
        break
```

### 3.2 `Frame`、`FrameHandle` 和像素格式

| 接口 | 使用方法 |
| --- | --- |
| `Frame.to_array()` | 返回原始像素数组；对 `keep_fd` 帧会做一次带 DMA 同步的映射和拷贝并缓存。 |
| `Frame.to_rgb()` | 转换为 RGB 数组。支持 RGB、BGR、NV12、GRAY8。 |
| `Frame.crop(x, y, width, height)` | 返回新帧，不修改原帧。NV12/NV21 的坐标和尺寸必须为偶数。 |
| `Frame.resize(width, height, mode="letterbox", pad_value=114)` | 返回新帧；`mode` 可为 `stretch`、`letterbox`、`crop`。几何映射保存在 `metadata["transform"]`。 |
| `Frame.to_jpeg_bytes(quality=85)` | 编码为 JPEG 字节。 |
| `Frame.save(path)` | 根据文件名保存图像。 |
| `Frame.release()` | 幂等释放 `keep_fd` 句柄；复制帧调用该方法无副作用。 |
| `Frame.baked_overlay` / `baked_dpm` | 判断平台 AI 叠加或隐私遮罩是否已烘焙进该帧。 |
| `Frame.data` | 原始图像的扁平数组兼容属性；新代码优先使用 `to_array()`。 |
| `FrameHandle.fd` / `fds` | 第一平面 FD / 全部平面 FD，仅供零拷贝硬件链路使用。 |
| `FrameHandle.close()` / `closed` | 归还底层 DMA-BUF / 查询是否已释放。 |

`PixelFormat` 枚举包含 `NV12`、`NV21`、`RGB`、`BGR`、`RGBA`、`BGRA`、
`GRAY8`、`YUYV`。`StreamInfo` 描述 `stream_id`、分辨率、格式、帧率和缓冲数。
`FRAME_FLAG_OVERLAY_BAKED` 与 `FRAME_FLAG_DPM_BAKED` 是 `Frame.flags` 的位标记。

### 3.3 `EncodedStreamClient` 与 `EncodedFrame`

```python
from neoruntime_ipc_sdk import EncodedStreamClient

with EncodedStreamClient(stream_id="main") as stream:
    packet = stream.get_frame(timeout_ms=2000)
    if packet:
        print(packet.codec_name, packet.is_keyframe, len(packet.data))

    for packet in stream.subscribe(reconnect=True):
        consume_annex_b(packet.data)
```

`EncodedStreamClient(socket_path=None, stream_id="main", socket_dir=None)` 提供：

- `get_frame(timeout_ms=5000)`：获取一个编码包，超时返回 `None`。
- `subscribe(reconnect=True)`：连续迭代编码包，可自动重连。
- `on_frame(callback)`：后台线程回调。
- `close()`：关闭 Socket。
- `seq_packets`、`seq_gap_events`、`seq_missing`、`last_seq`：包序号与丢包观测数据。

`EncodedFrame` 的主要字段为 `codec`、`flags`、`pts_ns`、`dts_ns`、`width`、
`height`、`data`、`seq`；`codec_name` 和 `is_keyframe` 是属性，不需要加括号。

## 4. 预处理、后处理与推理管线

### 4.1 `Preprocessor` 与 `PreprocessMeta`

创建方式：

```python
from neoruntime_ipc_sdk import Preprocessor

pre = Preprocessor(
    size=(640, 640), color="RGB", resize_mode="letterbox",
    pad_value=114, normalize=True, layout="NCHW"
)
tensor, meta = pre(frame)
source_x, source_y = meta.to_source(320, 320)
```

`Preprocessor.from_model(client, model_id, **overrides)` 会读取模型输入规格并推导尺寸、
布局和归一化参数。`PreprocessMeta.to_source(x, y)` 与
`to_source_box((x1,y1,x2,y2))` 把模型输入坐标映射回原图。

### 4.2 后处理

| 接口 | 使用方法 |
| --- | --- |
| `nms(boxes, scores, iou_threshold=0.5, class_ids=None)` | 对 `xyxy` 候选框做贪心非极大值抑制，返回保留索引。传 `class_ids` 时按类别独立抑制。 |
| `Postprocessor` | 自定义后处理器应遵循的可调用协议：输入原始输出和 `PreprocessMeta`，返回检测对象列表。 |
| `YoloV8Postprocessor(...)` | 解码 YOLOv8 输出，可配置标签、分数阈值和 IoU 阈值。 |
| `YoloV5Postprocessor(...)` | 解码 YOLOv5 输出，可配置标签、分数阈值和 IoU 阈值。 |

```python
from neoruntime_ipc_sdk import InferencePipeline, YoloV8Postprocessor

post = YoloV8Postprocessor(
    labels=["person", "car"], score_threshold=0.30, iou_threshold=0.45
)
pipeline = InferencePipeline.from_model("custom_yolov8", postprocessor=post)
output = pipeline.run(frame)
print(output.objects)
```

### 4.3 `InferencePipeline` 与 `PipelineResult`

`InferencePipeline` 在应用进程内同步组合“预处理 → 推理 → 后处理”。

| 接口 | 使用方法 |
| --- | --- |
| `InferencePipeline(client=None, model_id=None, preprocessor=None, postprocessor=None, infer_timeout_ms=5000, retain_input=False)` | 手动组装管线。`retain_input=True` 时结果可能持有输入引用，使用后调用 `PipelineResult.release()`。 |
| `from_model(model_id, client=None, postprocessor=None, **preprocess_kwargs)` | 从模型元数据创建预处理器并绑定模型。 |
| `run(source, model_id=None)` | 同步运行一次，返回 `PipelineResult`。 |
| `run_async(source, model_id=None)` | 返回 `Future[PipelineResult]`。 |

`PipelineResult` 提供 `objects`、原始 `result`、`meta`、`latency_ms`、`tensor` 和
`release()`。

### 4.4 `PipelineRunner`

`PipelineRunner` 把帧源和 `InferencePipeline` 放入读取线程与工作线程，默认采用
latest-wins 背压策略。

```python
from neoruntime_ipc_sdk import FdMediaClient, InferencePipeline, PipelineRunner

media = FdMediaClient()
runner = PipelineRunner(
    source=media.subscribe("sub", keep_fd=True),
    pipeline=InferencePipeline.from_model("person_v1"),
    sink=lambda output, frame: print(output.objects),
    queue_size=1,
    drop_policy="latest",
)
with runner:
    do_other_work()
print(runner.stats)
media.close()
```

接口：`start()` 启动并返回自身；`stop(timeout_s=5.0)` 停止并返回是否成功收尾；
`running` 查询状态；`stats` 返回 FPS、丢帧、延迟和错误计数。`sink` 在工作线程执行，
不要在回调结束后继续持有输入帧。

### 4.5 `StreamPipeline`

`StreamPipeline` 是平台调度管线：视频像素不进入应用，平台直接做流式推理，应用可将
结果推入硬件叠加层并同时消费结果。

```python
from neoruntime_ipc_sdk import StreamPipeline

with StreamPipeline(
    "main", "person_v1", fps=10, min_score=0.5,
    labels=["person"], draw=True
) as pipe:
    for sequence, result in pipe.results():
        print(sequence, len(result.objects))
        if sequence > 100:
            break
    print(pipe.status())
```

接口：`start()` 单次启动；`results()` 迭代应用侧结果；`status()` 返回
`StreamPipelineStatus`；`stop()` 幂等停止、清理绘制并关闭自身创建的客户端。
状态包含运行标志、已见/已绘制结果数、两级队列丢弃数、叠加错误、最近/平均延迟和
skew。一个实例只允许启动一次，需要重启时创建新实例。

## 5. 事件总线

### 5.1 `EventClient`

创建方式：`EventClient(endpoint=None)`，默认使用 `EVENT_BUS_ENDPOINT`。

| 接口 | 使用方法 |
| --- | --- |
| `publish(topic, payload, persistent=False, ttl_ms=None, metadata=None, compact=False)` | 发布 JSON 兼容字典，返回事件 ID。`persistent` 请求持久化，`ttl_ms` 设置有效期，`compact` 启用主题压缩语义。 |
| `publish_batch(events, persistent=False)` | 批量发布。每个元素至少包含 `topic` 和 `payload`。 |
| `subscribe(topic, filters=None, queue_size=100, drop_old=True)` | 按主题迭代 `Event`；支持平台定义的通配符。队列满时 `drop_old=True` 丢最旧事件。 |
| `on_event(topic, callback, filters=None)` | 后台线程订阅，返回线程对象。 |
| `unsubscribe(topic)` | 取消该客户端对主题的订阅。 |
| `list_topics()` | 返回 `list[TopicInfo]`。 |
| `get_topic_info(topic)` | 返回主题信息，不存在时返回 `None`。 |
| `get_stats()` / `get_topic_stats(topic)` | 返回总线全局 / 单主题统计。 |
| `close()` | 关闭订阅和通道。 |

```python
from neoruntime_ipc_sdk import EventClient

with EventClient() as events:
    event_id = events.publish(
        "app/perimeter/alert",
        {"count": 1},
        ttl_ms=30_000,
        metadata={"camera": "main"},
    )
    for event in events.subscribe("app/perimeter/*"):
        print(event.topic, event.payload, event.metadata)
        break
```

`Event` 字段为 `topic, payload, source, event_id, timestamp_ns, metadata`，并提供
`to_json()`；`Event.from_proto(msg)` 用于把底层 protobuf 消息转换成事件对象。
`TopicInfo` 字段为主题名、订阅者数、累计消息数和最后消息时间。

## 6. 设备控制

### 6.1 `DeviceClient`

创建方式：`DeviceClient(endpoint=None)`，默认使用 `DEVICE_CONTROL_ENDPOINT`。

| 能力 | 接口与使用方法 |
| --- | --- |
| 灯光/IR-Cut | `set_white_light(level)` 设置 0–100 白光亮度；`set_ir_led(on)` 开关红外灯；`set_ircut(IrCutMode.AUTO/DAY/NIGHT)` 切换滤光片模式。 |
| 云台 | `pan_left(speed=50)`、`pan_right(speed=50)`、`tilt_up(speed=50)`、`tilt_down(speed=50)` 开始运动；`pan_stop()`、`tilt_stop()` 或 `ptz_stop()` 停止；`save_preset(id)` 保存预置位，`call_preset(id)` 调用。 |
| 变焦 | `zoom_in(speed=50)`、`zoom_out(speed=50)`、`zoom_stop()`；`zoom(speed)` 使用 -100..100 有符号速度；`set_zoom_level(level)` 设置 0..1 归一化位置。 |
| 对焦 | `focus_in(speed=50)`、`focus_out(speed=50)`、`focus_stop()`；`focus(speed)` 使用有符号速度；`set_focus_level(level)` 设置归一化位置；`focus_auto(enable)` 开关连续自动对焦。 |
| 镜头 | `lens_init()` 初始化；`lens_reset_zero(zoom=True, focus=True)` 回零；`get_lens_status()` 返回状态字典；`set_lens_limits(zoom_limit=None, focus_limit=None)` 设置轴限位；`lens_goto_ratio_distance(zoom_ratio, focus_distance_m)` 联动变焦和焦距。 |
| 光圈 | `control_iris(open)` 开关光圈；`set_iris_target(target)` 设置目标。 |
| 原生自动对焦 | `start_oneshot_af()`、`start_zoom_follow(ratio)` 返回 `AfJob`；`get_autofocus_status()` 轮询 `AfStatus`；`cancel_autofocus(job_id=0)` 取消；`oneshot_autofocus(timeout=20)` 是阻塞便捷方法。 |
| AF 测光 | `set_af_windows(enabled, windows, stream_id="main")` 设置窗口；`get_af_measurement()` 返回 `AfMeasurement`。当前部分固件可能尚未实现这两个服务端接口。 |
| GPIO | `gpio_set(pin, value)` 输出；`gpio_get(pin)` 读取。 |
| Wiegand | `set_wiegand_out(channel, enable)` 设置；`get_wiegand_out(channel)` 查询。 |
| RS-485 | `rs485_init(baudrate, config="")` 初始化；`rs485_tx(data)` 发送；`rs485_deinit()` 释放；`subscribe_rs485_rx(queue_size=16, drop_old=True)` 迭代 `Rs485RxEvent`（总线上每帧一条，需固件支持 `SubscribeRs485Rx`）。 |
| 状态/事件 | `get_device_status()` 返回 `DeviceStatus`；`subscribe_events()` 迭代 `DeviceEvent`。 |

```python
from neoruntime_ipc_sdk import DeviceClient, IrCutMode

with DeviceClient() as device:
    device.set_white_light(60)
    device.set_ircut(IrCutMode.AUTO)
    device.pan_left(speed=30)
    try:
        wait_for_target()
    finally:
        device.ptz_stop()
    print(device.get_device_status())
```

数据类型：

- `DeviceStatus`：温度、光照、云台、变焦、对焦、IR-Cut、灯光和 MCU 状态。
- `DeviceEvent`：事件类型、时间戳以及 GPIO、光照或温度数据。
- `AfJob`：`accepted, job_id, message`。
- `AfStatus`：任务状态、进度、镜头位置、评价指标、距离、耗时和错误信息。
- `AfMeasurement`：各窗口的 `focus_energy`、`mean_luma` 和 `frame_id`。

## 7. 相机控制

### 7.1 `CameraClient`

创建方式：`CameraClient(endpoint=None)`，默认使用 `CAMERA_CONTROL_ENDPOINT`。

#### 图像、编码与叠加配置

| 接口 | 使用方法 |
| --- | --- |
| `get_isp()` / `set_isp(config=None, **kwargs)` | 读取或局部更新亮度、对比度、饱和度、锐度、曝光、增益、降噪、WDR、白平衡等。可传 `ISPConfig` 或关键字。值 `-1`/`None` 表示保持不变。 |
| `get_transform()` / `set_transform(TransformConfig)` | 查询或设置旋转、翻转、去畸变、灰度。 |
| `set_encoder(stream_name="main", bitrate_bps=0, framerate=0, gop=0)` | 动态修改编码参数，0 表示不修改。 |
| `reconfigure_encoder(stream_name, width=0, height=0, codec="", bitrate_bps=0, fps=0, gop=0)` | 重建指定编码器，返回 `EncoderReconfigResult`，会造成短暂中断。 |
| `set_rtsp_enabled(enabled)` | 开关 RTSP 服务。 |
| `set_osd(streams)` / `get_osd()` | 设置 / 读取各流的文字和时间 OSD 配置列表。 |
| `set_ai_overlay(enabled, show_label=True, show_confidence=True, line_thickness=2)` | 配置平台 AI 框叠加。更完整的绘制使用 `OverlayClient`。 |
| `get_privacy_mask()` / `set_privacy_mask(...)` | 查询或以 merge 语义更新静态区域和动态 AI 隐私遮罩。 |

#### 日夜、红外与硬件

| 接口 | 使用方法 |
| --- | --- |
| `set_imaging_mode(mode)` | 设置 `auto`、`day` 或 `night`，返回 `InfraredStatus`。 |
| `get_infrared_status()` | 查询当前模式、PWM、光感、profile 和降级状态。 |
| `set_infrared_settings(auto_follow=None, near_pwm=None, far_pwm=None, night_enter=None, day_enter=None)` | 只更新非 `None` 字段并返回新状态。 |
| `clear_infrared_manual()` | 清除手动覆盖，恢复 profile 驱动。 |
| `list_ir_presets()` / `save_ir_preset(name, zoom_ratio, near_pwm, far_pwm)` / `delete_ir_preset(name)` | 管理随变焦比工作的红外预设。 |
| `get_sensor_info(sensor_index=0)` | 返回 `SensorInfo`。 |
| `get_capabilities()` | 返回 `Capabilities`，先据此判断视频、编解码、灯、MCU、环境控制等能力。 |
| `get_hardware_status()` | 返回光感、温度、MCU 版本、灯光占空比和 IR-Cut 状态。 |
| `set_led_duty(led_id, duty_percent)` / `get_led_duty(led_id)` | 直接控制/读取灯占空比。 |
| `set_ircut(mode)` / `get_ircut()` | 低级 IR-Cut 接口，`0=day`、`1=night`。 |
| `mcu_raw_request(cmd, payload=b"")` | 发送 MCU 原始命令，返回原始响应。仅在明确掌握协议时使用。 |
| `set_fan(enable)` / `get_fan()` | 控制和读取风扇，读取返回 `EnvStatus`。 |
| `set_heat(enable)` / `get_heat()` | 控制和读取加热，读取返回 `EnvStatus`。 |
| `set_radar(enable)` / `get_radar()` | 控制和读取雷达，读取返回 `EnvStatus`。 |
| `set_alarm_out(channel, enable)` / `get_alarm_out(channel)` / `get_alarm_outputs()` | 控制和查询报警输出。 |
| `rs485_init(baudrate=9600, config="8N1")` / `rs485_tx(data)` / `rs485_deinit()` | 通过相机服务使用 RS-485。不要与 `DeviceClient` 同时争用同一总线。 |

#### 流、配置与 profile

| 接口 | 使用方法 |
| --- | --- |
| `get_stream_status(timeout_s=None)` | 返回 `list[StreamStatus]`，含编码参数、包数、丢包、客户端、叠加和 epoch 指标。 |
| `add_stream(stream_id, width, height, fps, codec="h264", bitrate=4000000, gop=30)` | 动态添加视频流。 |
| `remove_stream(stream_name)` | 移除流。 |
| `reconfigure_pipeline(streams)` | 使用 `list[PipelineStreamConfig]` 整体重配管线。 |
| `get_profile()` / `list_profiles()` | 查询当前 profile / 返回 `(profile_names, current_profile)`。 |
| `switch_profile(name)` | 切换 profile，返回 `EncoderReconfigResult`。 |
| `backup_profile(path="")` | 备份当前 profile；空路径由平台选择默认位置。 |
| `get_config_field(field_path)` / `set_config_field(field_path, value)` | 按点分路径读写 camera-daemon 配置。属于低级运维接口。 |

#### 帧注入底层接口

| 接口 | 使用方法 |
| --- | --- |
| `push_frame(buffer_id, width, height, stride, mode="replace", pts_ns=0, dest_x=0, dest_y=0, stream_id="", end_of_stream=False, session_id="", timeout_s=None)` | 把已注册 DSP 缓冲推入编码链，返回 `InjectionResult`。一般应用优先使用 `FramePublisher`。 |
| `push_frame_stream(frames, timeout_s=None)` | 在一个客户端流式 RPC 中推送多个帧描述。 |
| `injection_status(timeout_s=None)` | 返回 `InjectionStatus`，包含活动状态、队列深度、丢帧和在途 buffer ID。 |
| `stop_injection(timeout_s=None)` | 终止注入并在下个 IDR 恢复 ISP 路径。 |

```python
from neoruntime_ipc_sdk import CameraClient, ISPConfig, TransformConfig

with CameraClient() as camera:
    camera.set_isp(ISPConfig(brightness=55, contrast=50))
    camera.set_transform(TransformConfig(rotation=180, flip=0))
    camera.set_encoder("main", bitrate_bps=4_000_000, framerate=25, gop=50)
    for stream in camera.get_stream_status(timeout_s=2.0):
        print(stream.stream_id, stream.status, stream.width, stream.height)
```

相机接口的返回/配置数据类型还包括：

- `EncoderReconfigResult`：重配置是否成功、消息和中断毫秒数。
- `InjectionResult`、`InjectionStatus`：注入请求结果与当前会话状态。
- `StreamStatus`：单流状态、编码参数、发布/丢包/叠加计数和 `stream_epoch`。
- `Capabilities`：设备能力布尔标记。
- `SensorInfo`：Sensor 可用性、型号、I²C 地址和像素格式。
- `HardwareStatus`：光感、MCU 温度/版本、模拟输入、灯光占空比和 IR-Cut 状态。
- `PipelineStreamConfig`：整体重配管线时的输入和编码输出参数。
- `EnvStatus`：风扇、加热、雷达等部件的开关状态。
- `InfraredStatus`：日夜模式、PWM、光感、变焦和 profile 状态。
- `IrPreset`：红外预设名称、变焦比、近光和远光 PWM。
- `PrivacyMaskSettings`：静态区域和动态 AI 隐私遮罩配置。

`pip_dest(frame_w, frame_h, inset_w, inset_h, corner="bottom-right", margin=16)` 位于
`neoruntime_ipc_sdk.camera` 子模块，用于计算画中画贴图坐标；它不是包顶层导出项。

## 8. 音频

### 8.1 `AudioClient`

| 接口 | 使用方法 |
| --- | --- |
| `list_capture_devices()` / `list_playback_devices()` | 返回 `list[AudioDevice]`。 |
| `start_capture(device="", sample_rate=0, channels=0, codec="", bitrate=0)` | 启动采集，0 或空字符串采用平台默认值。 |
| `stop_capture()` | 停止采集。 |
| `start_playback(device="", sample_rate=0, channels=0)` / `stop_playback()` | 启动 / 停止播放。 |
| `get_status()` | 返回 `AudioStatus`。 |
| `set_config(..., volume=-1.0, mute=None)` | 局部更新设备、采样率、声道、编码、码率、音量和静音状态。 |
| `stream_pcm(pcm_iter, sample_rate=48000, channels=1, fmt="S16LE")` | 把 PCM 字节块迭代器送到设备，实现双向对讲。 |
| `stream_pcm_file(path, chunk_size=4096, sample_rate=48000, channels=1, fmt="S16LE")` | 播放裸 PCM 文件。 |

```python
from neoruntime_ipc_sdk import AudioClient

with AudioClient() as audio:
    print(audio.list_capture_devices())
    audio.start_capture(sample_rate=48_000, channels=1, codec="pcm")
    print(audio.get_status())
    audio.stop_capture()
```

`AudioDevice` 包含 `name, description`；`AudioStatus` 包含采集/播放状态、设备、采样
格式、编码、音量和静音状态。

### 8.2 `AudioStreamClient` 与 `AudioFrame`

`AudioStreamClient(socket_path=None)` 默认读取
`/run/aipc/encoded/audio_capture.sock`，接口与编码视频流相同：
`get_frame(timeout_ms)`、`subscribe(reconnect=True)`、`on_frame(callback)`、`close()`。

```python
from neoruntime_ipc_sdk import AudioStreamClient

with AudioStreamClient() as stream:
    for frame in stream.subscribe():
        print(frame.codec_name, frame.sample_rate, frame.channels, frame.duration_ms)
        consume_audio(frame.data)
```

`AudioFrame` 字段为 `codec, flags, pts_ns, sample_rate, channels, bits_per_sample,
data, dts_ns`；`codec_name`、`is_keyframe`、`duration_ms` 均为属性。部分旧固件发送的
音频头不包含采样格式，此时采样率、声道和位深会是 0。
底层协议调试可从 `neoruntime_ipc_sdk.audio_stream` 导入
`decode_audio_format(header, payload_size)`，它返回采样率、声道、位深和 DTS。

## 9. 叠加与绘图

### 9.1 `OverlayClient` 与 `OverlayConfig`

| 接口 | 使用方法 |
| --- | --- |
| `enable(show_label=True, show_confidence=True, line_thickness=2)` | 启用平台 AI 叠加。 |
| `disable()` | 禁用叠加。 |
| `configure(enabled=True, ..., strict_frame_lock=None, strict_wait_cap_ms=None)` | 完整配置颜色、字号、线宽和严格帧锁；`None` 表示不修改对应严格模式字段。 |
| `apply(config)` | 应用 `OverlayConfig`。 |
| `annotate(stream_id, detections=None, polygons=None, ttl_ms=None, session_id=None, frame_sequence=None, stream_epoch=None)` | 向指定流发布检测框或多边形，返回事件 ID。传空检测列表可清框。 |
| `annotate_result(stream_id, result, ...)` | 从 `InferenceResult` 自动选择 objects、classifications、landmarks 或 OCR 内容发布。 |
| `close()` | 关闭客户端。 |

```python
from neoruntime_ipc_sdk import OverlayClient, OverlayConfig

with OverlayClient() as overlay:
    overlay.apply(OverlayConfig(enabled=True, line_thickness=2))
    overlay.annotate_result(
        "main", result,
        frame_sequence=result.frame_sequence,
        ttl_ms=500,
        session_id="demo",
    )
```

`OverlayConfig.to_proto()` 用于生成底层 protobuf 配置；一般应用直接调用 `apply()`
即可。`OverlayClient.channel_options` 是只读 gRPC 通道参数，主要用于诊断。

严格帧同步时，建议同时传 `frame_sequence` 和从
`CameraClient.get_stream_status()` 得到的 `stream_epoch`。跨流结果的帧序号虽同尺，
但延迟可能导致结果超过绘制窗口。

### 9.2 应用侧绘图函数

这些函数返回新数组，不修改输入数组：

| 接口 | 使用方法 |
| --- | --- |
| `draw_boxes(image, boxes, labels=None, scores=None, color=(0,255,0), thickness=2)` | 在 RGB 图上画像素坐标框。 |
| `draw_text(image, text, xy, color=(255,255,255), font_scale=0.5, thickness=1)` | 在像素坐标处画文字。 |
| `draw_detections(image, result_or_objects, color=None)` | 直接绘制 `InferenceResult` 或 `DetectedObject` 列表。 |
| `draw_polygons(image, shapes, thickness=2, closed=True)` | 绘制封闭区域或开放轨迹。 |
| `render_overlay_rgba(frame_w, frame_h, boxes=..., polygons=..., tracks=...)` | 生成包含所有元素的紧凑 RGBA 叠加层，返回 `(rgba, x, y)`。 |
| `render_overlay_fragments(...)` | 将框拆成多个紧凑 RGBA 片段，返回 `(rgba, x, y)` 列表，适合 DSP blend。 |

```python
from neoruntime_ipc_sdk import draw_detections

annotated = draw_detections(frame.to_rgb(), result)
```

## 10. 帧注入

### 10.1 `FramePublisher`

创建方式：

```python
from neoruntime_ipc_sdk import CameraClient, DspClient, FramePublisher

with CameraClient() as camera, DspClient() as dsp:
    with FramePublisher(camera, dsp, stream_id="sub", mode="replace") as publisher:
        publisher.publish(frame)
        publisher.publish_eos()  # 显式恢复 ISP 路径
```

| 接口/属性 | 使用方法 |
| --- | --- |
| `publish(frame, pts_ns=0)` | 把 NumPy/Frame 数据写入下一个池槽并推送，返回 `InjectionResult`。 |
| `publish_rgb(rgb, pts_ns=0)` | 把 RGB 转为 NV12 后替换流，仅用于 `replace`。 |
| `publish_stream(frames, pts_ns=None, end_with_eos=False, timeout_s=None)` | 批量流式推送。 |
| `pool` | 取得发布器拥有的 `DspBufferPool`。 |
| `acquire_slot()` | 为设备侧写入预留一个空闲池槽。 |
| `push_slot(slot, pts_ns=0)` | 推送已由 DSP 写好的槽，避免客户端回读/重写。 |
| `publish_eos()` | 发送流结束并恢复 ISP；`close()` 本身不会自动发送 EOS。 |
| `close()` | 幂等释放缓冲池。 |
| `width, height, stream_id, session_id, mode, dest, lease_mode` | 查询发布器的几何、会话、模式、贴图位置和写租约能力。 |

构造参数 `mode` 为 `replace` 或 `overlay`。叠加模式可用 `inset=(w,h)` 与
`dest=(x,y)` 指定画中画尺寸和位置。`session_id` 用于平台在异常退出时清理该会话资源。

## 11. DSP、颜色转换与加速路由

### 11.1 `DspClient`

创建方式：`DspClient(sock_path=None, endpoint=None)`。硬件不可用时，多数 `*_hw`
接口在 `cpu_fallback=True` 下回退到 CPU。

| 接口 | 使用方法 |
| --- | --- |
| `alloc_buffers(width, height, fmt="nv12", count=1)` | 在 daemon 侧分配池，返回 `DspBufferPool`。 |
| `import_shared_buffers(width, height, fmt="argb", count=2, timeout_s=5)` | 创建可写共享 ARGB 环形池，返回 `SharedImportPool`；该类型位于 `dsp` 子模块，未从包顶层导出。 |
| `import_frame(handle)` | 导入 `FrameHandle` 的 DMA-BUF，返回 daemon buffer ID。 |
| `release_buffer(buffer_id)` | 释放导入或分配的 ID。 |
| `resize_hw(src, width, height, ..., wait=True, out=None)` | 硬件缩放；`scaling` 支持 `stretch` 等模式。 |
| `crop_hw(src, x, y, width, height, dst_width=None, dst_height=None, ...)` | 裁剪并可同时缩放。 |
| `multi_crop_hw(src, rects, ...)` | 一次任务裁剪多个窗口。每个 rect 为源区域和目标尺寸。 |
| `convert_hw(src, dst_fmt, ...)` | 在 NV12、RGB24、GRAY8 等格式间转换。 |
| `blend_hw(base, overlays, ..., zero_copy=False, out=None, dst_slot=0)` | 把 `(argb, x, y)` 叠加层合成到 NV12 底图。 |
| `encode_jpeg_hw(src, quality=85, ...)` | 使用 camera-daemon 编码 JPEG，返回字节。 |
| `has_live_pools()` | 判断该客户端分配的池是否仍在使用。 |
| `close()` | 关闭传输并释放该连接持有的 DSP 资源。 |

`wait=False` 通常返回 `PendingDspJob`：`buffer_id` 查看首个目标缓冲 ID，
`done(timeout_s=0)` 轮询，`wait_result(timeout_s=None)` 等待但保留设备侧结果，
`wait()` 等待、回读并释放，`release()` 放弃结果。`out="device"` 可返回 `DspBufferRef`，通过 `buffer_id`、
`width`、`height`、`fmt`、`released`、`read()`、`release()` 管理设备侧结果。

`DspBufferPool` 提供 `count`、`buffer_id(index)`、`write(index, array)`、
`read(index)`、`release()`。`DspError` 包含可选错误码。
`SharedImportPool` 还提供 `strides` 属性查询各平面的字节步长。

```python
from neoruntime_ipc_sdk import DspClient

with DspClient() as dsp:
    resized = dsp.resize_hw(frame, 640, 640, scaling="letterbox")
    pending = dsp.convert_hw(frame, "rgb24", wait=False)
    rgb = pending.wait(timeout_s=5)
```

### 11.2 颜色转换

| 接口 | 输入与输出 |
| --- | --- |
| `nv12_to_rgb(nv12, width, height)` | NV12 → `(H,W,3)` RGB。 |
| `nv12_to_bgr(nv12, width, height)` | NV12 → BGR。 |
| `rgb_to_nv12(rgb)` | RGB → `(H*3/2,W)` NV12；宽高应满足 YUV 偶数约束。 |
| `bgr_to_nv12(bgr)` | BGR → NV12。 |
| `nv12_resize(nv12, src_size, dst_size)` | 缩放 NV12；尺寸元组顺序为 `(width, height)`。 |

### 11.3 `AccelRouter`

`AccelRouter` 统一决定算子使用硬件还是软件：

- `RoutePolicy.PREFER_HARDWARE`：默认，硬件不可用时回退软件。
- `RoutePolicy.HARDWARE_ONLY`：禁止静默回退，失败抛 `HardwareUnavailable`。
- `RoutePolicy.SOFTWARE_ONLY`：用于基线测试或排障。

| 接口 | 使用方法 |
| --- | --- |
| `set_policy(policy)` / `policy` | 修改 / 查询当前策略。 |
| `register(op, software=None, hardware=None, note="")` | 注册某算子的软硬件实现。 |
| `use_hardware(op, hardware)` | 替换硬件实现。 |
| `add_probe(name, probe)` | 注册轻量可用性探针。 |
| `route(op)` | 返回 `RouteDecision(op, backend, provider, reason)`。 |
| `run(op, *args, **kwargs)` | 按路由执行算子。 |
| `note_degradation(op, reason)` | 记录路由外发生的回退。 |
| `probe()` / `health()` | 返回探针结果 / 完整路由健康快照。 |
| `get_default_router()` | 获取进程级默认路由器。 |
| `set_route_policy(policy)` | 设置默认路由器策略。 |

`DegradationRecord` 记录算子、原因和时间戳。

```python
from neoruntime_ipc_sdk import get_default_router, set_route_policy

set_route_policy("hardware_only")
print(get_default_router().health())
```

SDK 自身的硬件快速路径还可从 `neoruntime_ipc_sdk.accel` 导入
`shared_dsp_call(method, *args, **kwargs)`，在进程级常驻 `DspClient` 上执行单次方法；
它属于高级接口，业务代码通常直接使用 `DspClient` 或默认路由器。

## 12. 录像与 Web 预览

### 12.1 录像

| 接口 | 使用方法 |
| --- | --- |
| `TsWriter(path, codec="h264")` | 创建 MPEG-TS 文件；`write(EncodedFrame)` 追加包，`close()` 完成文件。 |
| `HlsWriter(out_dir, segment_seconds=6.0, window=5, codec="h264")` | 创建按关键帧切片的 HLS；`write()` 追加包，`close()` 完成最后分片和播放列表。 |
| `PrerollBuffer(seconds=10.0)` | `push(frame)` 维护事件前环形缓存；`frames()` 查看快照；`dump(path, on_frame=None)` 写出缓存并返回可继续追加的 `TsWriter`。 |

```python
from neoruntime_ipc_sdk import EncodedStreamClient, HlsWriter

with EncodedStreamClient(stream_id="main") as stream:
    with HlsWriter("/data/aipc/hls", segment_seconds=4, window=5) as writer:
        for packet in stream.subscribe():
            writer.write(packet)
```

`TsWriter` 写出的是 MPEG-TS，文件扩展名建议使用 `.ts`，不是 `.mp4`。

### 12.2 MJPEG 与平台流地址

| 接口 | 使用方法 |
| --- | --- |
| `MjpegStream.push_frame(frame, quality=85)` | 把 `Frame` 编码成 JPEG 并发布为最新帧。 |
| `MjpegStream.push_jpeg(data)` | 发布已经编码好的 JPEG。 |
| `latest()` / `latest_seq()` | 读取最新 JPEG / 单调递增序号。 |
| `wait_new(after_seq, timeout=1.0)` | 等待新帧；返回是否出现新帧，再调用 `latest()` 取数据。 |
| `mjpeg_wsgi_app(source, fps=15)` | 创建 `multipart/x-mixed-replace` WSGI 应用。 |
| `MjpegServer(port=8080, host="0.0.0.0", source=None, path="/", fps=15)` | 创建独立 HTTP 服务器；`start()` 启动，`stop()` 停止，`port` 返回实际监听端口。 |
| `platform_stream_url(stream_id="sub", host=None, scheme=None, token=None)` | 组合平台 H.264 WebSocket 地址；网络访问通常需要 JWT `token`。 |

```python
from neoruntime_ipc_sdk import FdMediaClient, MjpegServer, MjpegStream

source = MjpegStream()
with MjpegServer(port=8080, source=source, fps=15):
    with FdMediaClient() as media:
        for frame in media.subscribe("sub", skip_frames=2):
            source.push_frame(frame.resize(640, 360), quality=80)
```

## 13. 应用管理

### 13.1 `AppClient`

| 接口 | 使用方法 |
| --- | --- |
| `install_app(manifest_path, image_path)` | 从 manifest 和镜像安装应用，返回应用 ID。 |
| `start_app(app_id)` | 启动已安装应用。 |
| `stop_app(app_id, timeout_seconds=30)` | 优雅停止应用。 |
| `restart_app(app_id, timeout_seconds=30)` | 先停止再启动。 |
| `uninstall_app(app_id, keep_logs=True)` | 卸载应用，可保留日志。 |
| `list_apps()` | 返回 `list[AppInfo]`。 |
| `get_app(app_id)` | 返回 `AppInfo`。 |
| `get_app_stats(app_id)` | 返回 CPU、内存、线程数、运行时间等 `AppStats`。 |
| `get_logs(app_id, max_lines=100, follow=False)` | 迭代 `LogLine`；`follow=True` 持续跟踪。 |
| `get_logs_text(...)` | 与上项相同，但直接迭代字符串。 |
| `register_web_url(path="/")` | 为当前应用注册 Web 访问路径。 |

```python
from neoruntime_ipc_sdk import AppClient

with AppClient() as apps:
    for app in apps.list_apps():
        print(app.id, app.name, app.state)
    for line in apps.get_logs_text("my-app", max_lines=20):
        print(line)
```

`LogLine.datetime` 属性把纳秒/平台时间戳转换为 `datetime`。

## 14. 插件

### 14.1 插件发现

| 接口 | 使用方法 |
| --- | --- |
| `PluginDiscovery(discovery_dir=...)` | 创建发现器，默认扫描 `/run/aipc/plugins`。 |
| `reload()` | 重新加载发现文件。 |
| `get(capability_id)` | 返回第一个可用 `PluginEndpoint`，没有则为 `None`。 |
| `require(capability_id, timeout=30)` | 等待能力上线，超时抛 `TimeoutError`。 |
| `list_plugins()` / `list_capabilities()` | 列出插件字典 / 能力 ID。 |
| `watch(callback)` | 发现文件变化时回调。 |
| `close()` | 停止监听。 |

`PluginEndpoint.connect(**kwargs)` 创建 gRPC Channel，`is_available()` 检查端点；其字段
包含应用 ID、能力 ID、版本、传输方式、Socket、gRPC 服务名和事件主题。

```python
from neoruntime_ipc_sdk import PluginDiscovery

discovery = PluginDiscovery()
try:
    endpoint = discovery.require("lpr.postprocess", timeout=10)
    channel = endpoint.connect()
finally:
    discovery.close()
```

### 14.2 插件服务端

`PluginServer(plugin_id, socket_dir=...)` 为插件提供 gRPC 服务生命周期：

```python
from neoruntime_ipc_sdk import PluginServer

server = PluginServer("lpr.postprocess")
grpc_server = server.create_server(max_workers=4)
add_my_servicer(grpc_server)
server.start()
try:
    server.wait()
finally:
    server.stop(grace=5)
```

## 15. 配置与诊断

### 15.1 `Config`

`Config` 全部是静态读取接口：

| 接口 | 对应配置 |
| --- | --- |
| `get_app_id()` | `APP_ID`，默认 `unknown`。 |
| `get_inference_endpoint()` | `AI_RUNTIME_ENDPOINT`。 |
| `get_event_bus_endpoint()` | `EVENT_BUS_ENDPOINT`。 |
| `get_device_control_endpoint()` | `DEVICE_CONTROL_ENDPOINT`。 |
| `get_camera_control_endpoint()` | `CAMERA_CONTROL_ENDPOINT`。 |
| `get_app_manager_endpoint()` | `APP_MANAGER_ENDPOINT`。 |
| `get_shm_base_path()` | 共享内存 IPC 基础路径。 |
| `get_encoded_socket_dir()` | 编码流 Socket 目录。 |
| `get_host_prefix()` | 宿主机安装前缀，规范根路径为 `/data/aipc`。 |
| `translate_path_to_host(container_path)` | 把容器内路径换算成宿主机路径。 |
| `is_debug()` | 是否启用调试。 |
| `get_log_level()` | 日志级别。 |

### 15.2 `diagnostics()` 与健康检查

`diagnostics()` 返回 SDK 版本、Python、可选依赖、Socket、媒体流和加速路由等快照，
设计为不抛异常：

```python
from neoruntime_ipc_sdk import diagnostics
from neoruntime_ipc_sdk.diagnostics import check

report = diagnostics()
print(report["optional_deps"])

check(["inference", "camera_sock"]).raise_if_unhealthy()
```

`check(required=None, inference=None, model_id=None, camera=None, stream_id=None)` 位于
`neoruntime_ipc_sdk.diagnostics` 子模块，返回 `CheckReport`。传入客户端和 ID 后可做
`model_registered`、`stream_active` 等在线检查；`raise_if_unhealthy()` 会把所有失败项
合并到一个 `RuntimeError` 中。

## 16. 常见组合

### 16.1 取帧、推理、绘制并输出 JPEG

```python
from neoruntime_ipc_sdk import FdMediaClient, InferenceClient, draw_detections

with FdMediaClient() as media, InferenceClient() as inference:
    frame = media.get_frame("sub", timeout_ms=2000)
    if frame is None:
        raise RuntimeError("未收到视频帧")

    result = inference.infer(frame.to_rgb(), "person_v1")
    image = draw_detections(frame.to_rgb(), result)

    from PIL import Image
    Image.fromarray(image).save("result.jpg")
```

### 16.2 推理结果驱动灯光和事件

```python
from neoruntime_ipc_sdk import DeviceClient, EventClient, InferenceClient

with InferenceClient() as inference, DeviceClient() as device, EventClient() as events:
    for sequence, result in inference.subscribe("main", "person_v1", fps=10):
        count = result.count_by_label("person")
        device.set_white_light(100 if count else 0)
        if count:
            events.publish("app/person-alert", {"sequence": sequence, "count": count})
```

### 16.3 资源管理要点

- `keep_fd=True` 的帧必须尽快 `release()`，最稳妥的方式是 `with frame:`。
- `EncodedStreamClient` 只提供编码包；写 TS/HLS 不需要先解码。
- `FramePublisher.close()` 不等价于 `publish_eos()`；要恢复 ISP 路径时先发 EOS。
- 长时间流式任务应监控订阅丢弃数、`PipelineRunner.stats`、`StreamPipeline.status()`
  和 `CameraClient.get_stream_status()`。
- 不确定硬件能力时，先调用 `diagnostics()`、`get_capabilities()` 和
  `AccelRouter.health()`。

## 17. 进一步文档

本手册提供统一的使用入口。模块级 Sphinx 文档位于 `python/docs/api/`，其中包含更多
平台行为、严格帧同步、隐私遮罩、DSP 缓冲所有权和固件兼容说明。
