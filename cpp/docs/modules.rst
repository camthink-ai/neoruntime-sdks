模块总览
========

公共头文件全部在 ``cpp/include/neoruntime_ipc_sdk/`` 下，公共面**不含
proto** （所有 ``*.pb.h`` 都留在 ``src/``），共享值类型在 ``types.hpp``，
端点与环境配置在 ``config.hpp``。

客户端模块
----------

.. list-table::
   :header-rows: 1
   :widths: 22 24 54

   * - 头文件
     - 客户端 / 类型
     - 职责
   * - ``inference.hpp``
     - ``InferenceClient``
     - AI 推理：``infer`` / 批量 / 流式 ``subscribe`` （健康度：时延与偏移
       EMA、丢帧计数、连续失败上限）、模型注册与统计、GenAI 流式。
       ``InferInput`` 接受 ``cv::Mat`` / ``Frame`` / ``FrameHandle`` /
       ``BufferRefInput`` （守护进程侧缓冲 id）
   * - ``device.hpp``
     - ``DeviceClient``
     - 灯光 / 红外 / IRCUT、云台 / 变焦 / 对焦、GPIO、RS485、Wiegand、
       状态查询、事件订阅、自动对焦套件（``AfJob`` / ``AfStatus`` /
       ``AfMeasurement``）
   * - ``camera.hpp`` + ``camera_types.hpp``
     - ``CameraClient``
     - ISP / 编码器 / RTSP / OSD / profile、``StreamStatus``、隐私遮挡、
       红外预设、管线重配、帧注入（``push_frame``、带回租约缓冲的
       ``InjectionResult``）
   * - ``app.hpp``
     - ``AppClient``
     - 应用容器生命周期、日志、统计
   * - ``events.hpp``
     - ``EventClient``
     - 事件总线发布 / 订阅 / 批量 / 主题 / 统计
   * - ``frame.hpp``
     - ``Frame`` / ``FrameHandle``
     - 零拷贝 DMA-BUF 帧：每 plane ``mmap`` 进 ``cv::Mat``、延迟
       RELEASE、``crop`` / ``resize`` （letterbox）、色彩转换、JPEG
   * - ``fd_client.hpp`` （``media.hpp`` 门面）
     - ``FdMediaClient``
     - 零拷贝取帧（``get_frame(keep_fd)``）、后台 ``subscribe`` /
       ``on_frame``、``list_streams``、编码流句柄
   * - ``encoded.hpp``
     - ``EncodedStreamClient``
     - H.264 / H.265 编码流（V3 序号、缺口 / 重启计数）
   * - ``audio.hpp``
     - ``AudioClient``
     - 音频控制
   * - ``audio_stream.hpp``
     - ``AudioStreamClient``
     - PCM / AAC 音频采集流
   * - ``overlay.hpp``
     - ``OverlayClient``
     - 硬件 overlay：配置、``annotate`` （检测框 + 区域多边形，ttl /
       session / 绑帧）、严格帧锁
   * - ``dsp.hpp``
     - ``DspClient``
     - DSP 作业：缓冲池、``resize_hw`` / ``crop_hw`` / ``multi_crop_hw``
       / ``convert_hw`` / ``blend_hw`` / ``encode_jpeg_hw``、缓冲导入、
       硬件 / CPU 使用可见性（``last_used_hw``）
   * - ``injection.hpp``
     - ``FramePublisher``
     - 用生成帧替换 / 叠加相机流（NV12 池或 RGB staging 转换链，
       写租约感知，session 标记 EOS）
   * - ``preprocess.hpp`` / ``postprocess.hpp``
     - ``Preprocessor`` / ``Postprocessor``
     - 按模型规格 letterbox 预处理；NMS + YoloV5/V8 解码
   * - ``pipeline.hpp``
     - ``InferencePipeline``
     - 客户端侧 前处理 → 推理 → 后处理（像素进你的进程）
   * - ``stream_pipeline.hpp``
     - ``StreamPipeline``
     - 平台调度整流水线：订阅 → overlay → 应用结果队列
       （像素留在设备上）
   * - ``runner.hpp``
     - ``PipelineRunner``
     - 在帧源上运行 ``InferencePipeline``
   * - ``color.hpp`` / ``draw.hpp``
     - 工具
     - 色彩转换（cvtColor 对齐）与 overlay 栅格绘制
   * - ``diagnostics.hpp``
     - ``collect_diagnostics``
     - 环境 + 连通性报告（含 ``sdk_version`` 等）
   * - ``accel.hpp``
     - ``AccelRouter``
     - 把昂贵像素操作路由到 DSP 硬件，CPU 自动回退
   * - ``plugin.hpp``
     - —
     - **已弃用** （仅作标记保留，镜像 Python 0.8）

传输
----

SDK 与平台守护进程之间共三种传输，行为与 Python SDK 逐位对齐：

- **UDS 上的 gRPC** —— 推理、设备、相机、应用、事件、overlay、DSP
  作业面。消息上限 64 MiB。
- **Raw UDS + ``SCM_RIGHTS`` fd 传递** —— ``FdMediaClient`` （视频
  plane）与 DSP 缓冲面（``DspClient`` 同时保持一条 gRPC 和一条 UDS
  连接）。
- **Raw UDS + 长度前缀** —— ``EncodedStreamClient``、
  ``AudioStreamClient``。

暂缺范围
--------

相较 Python 0.8.1，C++ 侧**暂不提供**：web（MJPEG）、录制（TS/HLS）、
插件系统——这几块自行实现（自带 HTTP 服务器 / 封装器）。
