更新日志
========

v0.8.2 (2026-11-26)
-------------------

新增功能
~~~~~~~~

- **RS-485 接收流**：新增 ``DeviceClient.subscribe_rs485_rx()``，把 RS-485 总线上收到的每一帧以事件流交付；``Rs485RxEvent`` 携带原始字节 ``data`` 与设备侧接收时间 ``timestamp_ns``。每个订阅者有独立的有界队列：``queue_size`` 设定队列深度（0 取默认值 16，超过 128 的按 128 计），``drop_old`` 决定队列满时丢最旧还是丢最新的一帧；多个订阅者共用一条上游流，camera-daemon 重启后自动重连，订阅不中断。交付语义为 at-least-once，需要精确一次的调用方自行去重。该接口需要平台固件支持 ``SubscribeRs485Rx`` RPC，不支持的固件上迭代器以 gRPC ``UNIMPLEMENTED`` 错误结束。

改进
~~~~

- 同步平台 proto：camera-control 与 device-control 新增 ``SubscribeRs485Rx`` 流式 RPC，以及 ``Rs485SubscribeRequest`` / ``Rs485RxEvent`` 消息
- 设备测试套件新增 ``test_04_subscribe_rs485_rx``，离线单元测试覆盖订阅参数与生成器语义

文档
~~~~

- README、``SDK_API_ZH.md`` 与中英 API 参考补充 ``subscribe_rs485_rx`` 的参数、生成器语义与投递契约

v0.8.1 (2026-10-15)
-------------------

改进
~~~~

- ``register_model()`` 相关测试改为以 ``model_type`` 注册检测模型，与运行时后处理链接行为对齐

文档
~~~~

- 新增中英双语「学习路径」页：按首跑、看活的、拿来用、交付、查阅五阶段组织入门路径，逐阶段指向 quickstart、教学 demo、examples 阶梯与应用镜像指南
- README 补齐 Overlay / StreamPipeline / Audio / DSP 四节 API 速览与教学 demo 章节，与 0.8.0 门面逐符号对账
- 学习路径阶段 3 与 apps 仓 ``examples/`` 的编号阶梯（01–07）互链；阶梯 05 即教学 demo 站 1 的独立 app 版
- 新增「设备开通」页（中英双语）：从购买 NE503 到首次登录——首连静态地址 ``10.0.0.1/24``、出厂凭据、SSH 与网页终端、组播发现；作为学习路径的阶段 0 反向互链

v0.8.0 (2026-09-16)
-------------------

新增功能
~~~~~~~~

- **客户端推理管线**：新增 ``Preprocessor`` / ``PreprocessMeta``、``YoloV5Postprocessor`` / ``YoloV8Postprocessor``、``InferencePipeline`` 与 ``PipelineRunner``，支持从模型规格派生预处理、结果坐标映射、可替换后处理、异步执行，以及带最新帧优先背压和统计信息的长驻运行器
- **平台调度管线**：新增 ``StreamPipeline`` / ``StreamPipelineStatus``，组合 ``InferenceClient.subscribe()`` 与 ``OverlayClient``，在像素不进入应用进程的情况下完成推理、过滤、硬件叠加和应用侧结果消费，并提供丢帧、延迟、时序偏差和错误观测
- **帧注入输出路径**：新增 ``FramePublisher`` 及 ``CameraClient.push_frame()`` / ``injection_status()`` / ``stop_injection()``，支持 replace / overlay、NV12 / RGB 发布、EOS 恢复与会话标记；写租约感知的缓冲池只复用 daemon 已释放的槽位，兼容旧版 daemon 的深度轮转模式
- **叠加层帧同步与观测**：``OverlayClient`` 支持严格对帧模式，以及 ``frame_sequence`` / ``stream_epoch`` / ``session_id`` 绑定；``StreamStatus`` 新增编码发布、叠加烘焙、严格锁帧、迟到命令和代数拒绝计数
- **部署诊断**：新增永不抛错的 ``diagnostics()`` 快照、可按应用要求验收并抛出汇总错误的 ``diagnostics.check()``，以及应用级 ``set_route_policy()`` 加速策略入口
- **推理模型信息**：``register_model()`` 支持 ``batch_size``，``ModelInfo`` 透传服务端批大小；``InferenceResult`` 新增服务端计算的 ``skew_us``
- **端到端设备驻留数据链**：DSP 路由器复用进程级客户端；``resize_hw`` / ``convert_hw`` 支持 ``out="ref"`` 返回 ``DspBufferRef``，推理可直接消费设备侧引用，NV12 预处理可直通，BLEND 可直接写入 ``FramePublisher`` 池槽，避免中间读回与重复导入
- **区域化叠加渲染**：新增 ``render_overlay_fragments()``，把描边拆成受 DSP batch 上限约束的偶数尺寸条带，减少全幅 ARGB 覆盖层的带宽和内存开销

改进
~~~~

- ``Frame`` 的裁剪 / 缩放链保留组合几何变换元数据；keep-fd 帧在预处理、推理、混合和发布路径中保持设备侧数据，媒体与编码客户端补充丢帧和连接观测
- 新增完整的设备接口与性能测试套件，以及 ``perf_demo`` 的 subscribe / keep-fd 对照链、部署脚本和运行期指标采集工具

修复
~~~~

- 修复设备实测发现的三个接口问题：DSP import id 按有符号 64 位解析导致高位 id 失效；``get_device_status()`` 读取不存在的 ``ir_led_on`` 字段；``AppClient.list_apps()`` 构造了错误的 Empty 消息类型
- 修复注入退出未发送 EOS、回调内停止引发线程自连接，以及部分叠加发布路径遗漏 ``ttl_ms`` 校验
- 修复 DSP 客户端关闭后池与引用仍可误用、路由器更换进程级客户端时过早关闭在用资源，以及 passthrough 推理完成后输入引用未释放的问题
- 收紧区域化叠加条带的偶数尺寸和 batch 上限处理，修复边缘平移前高度取整不足导致的无效几何

弃用
~~~~

- **插件系统 API** (``PluginDiscovery`` / ``PluginServer`` / ``PluginEndpoint``) 已弃用。当前平台未部署 ``/run/aipc/plugins`` 插件发现机制；v0.8.0 仍保留导入兼容并发出 ``DeprecationWarning``，文档页已下线。如有使用需求请提前反馈。

文档
~~~~

- 修正文档与 README 中的视频流示例:移除对从未存在过的 ``MediaClient`` 的引用,统一改用 ``FdMediaClient``;流 ID 由 ``cam0_main`` / ``cam0_sub`` 修正为设备实际暴露的 ``main`` / ``sub``;移除不存在的 ``get_stream_info()`` / ``get_raw_stream()`` 用法;修正 ``get_encoded_stream()`` 返回值语义与 ``frame.data`` 展平数组误用;补全 ``EncodedStreamClient`` / ``EncodedFrame`` API 文档
- 修复应用示例中的缺失导入与误导性导入:多模型融合示例补 ``import time``;英文推理页 GenAI 示例补 ``import json``;错误处理示例移除 ``from grpc import RpcError`` (SDK 实际抛出 ``RuntimeError``);清理未使用的 ``numpy`` / ``sys`` 导入
- 补译中文推理页缺失章节:自 v0.3.0 起仅存在于英文文档的分割 / OCR / CLIP 图像嵌入 / CLIP 文本编码 / 深度估计 / 运行时更新后处理配置 / GenAI 七个使用小节,以及 ``SegmentationMask`` / ``OcrLine`` / ``Embedding`` / ``DepthMap`` 四个数据类型条目,中英文档现已同步
- 新增管线、帧注入、叠加层与性能说明，补充本地推理应用和 ``perf_demo`` 示例

v0.7.4 (2026-09-08)
-------------------

新增功能
~~~~~~~~

- **便捷层硬件路由** (sdk-hardware-routing P5): ``color.rgb_to_nv12`` / ``color.nv12_to_rgb`` 与 ``draw.draw_detections``(NV12 数组)默认经 accel 路由器走 DSP 腿,不可用时自动回落软件实现并记账;``Frame.to_jpeg_bytes`` 对 keep-fd 帧硬件优先(camera-daemon ``EncodeImage`` 零拷贝导入),内存帧保持 CPU 编码直达,推流热路径不付额外拷贝与 RPC;软件腿只绑定私有实现,路由公函数不可重入
- ``Frame.resize`` 的 DSP 快路径尊重路由策略: ``SOFTWARE_ONLY`` 跳过尝试,``HARDWARE_ONLY`` 失败即抛错(拒绝静默 CPU 回落),``PREFER_HARDWARE`` 经新增的 ``AccelRouter.note_degradation()`` 记账(同时新增 ``policy`` 属性;外部上报的未注册 op 在 ``health()`` 可见,``on_degradation`` 照常触发)

修复
~~~~

- ``_encode_jpeg_hw`` 硬编码 ``fmt="rgb24"``,NV12 keep-fd 帧的提交必被 ``_resolve_source`` 以格式不匹配拒绝;帧类源现在随句柄自带格式
- ``dsp_format`` 软件腿经路由公函数重入路由器(跨 op 耦合);改为直接绑定 color 私有实现
- 色彩转换两腿的 ``ValueError`` 契约统一(ndim / 声明尺寸 / 偶数校验先于任何 daemon 提交,调用方错误不再计入降级计数)

v0.7.3 (2026-09-07)
-------------------

新增功能
~~~~~~~~

- **硬件优先加速路由器** (``accel`` 模块): ``AccelRouter`` / ``RoutePolicy`` / ``health()`` 降级记账 + ``on_degradation`` 钩子 / ``get_default_router()``;默认路由注册 ``resize_nv12`` / ``rgb_to_nv12`` / ``nv12_to_rgb`` / ``encode_jpeg`` / ``draw_detections`` 的 DSP 腿与 ``nms`` 软件腿
- **DSP 标注合成** (dsp-offload P1): ``DspClient.blend_hw`` 把 ARGB32 覆盖层在 DSP 上原位合成回 NV12;``draw.render_overlay_rgba`` 将框+文字渲染为最小 straight-alpha 画布,复现软件光栅输出
- **异步 DSP 作业** (dsp-offload P2): 全部 ``*_hw`` 操作支持 ``wait=False``,``PendingDspJob`` 提供 ``wait()`` / ``done()`` / ``release()``;``blend_hw`` 零拷贝 keep-fd 链(默认拒用——当前固件上为状态依赖的致命路径);``encode_jpeg_hw`` 支持 ``src_buffer_id`` 免像素读回;keep-fd 帧源在 resize/convert 腿免 ``ascontiguousarray`` 预拷贝;多边形与轨迹形状
- **overlay 标注**: ``annotate()`` / ``annotate_result()`` 经事件总线直推 camera-daemon 渲染器
- **色彩转换与 NMS**: BT.601 limited-range RGB↔NV12(cv2 缺失时的 numpy 路径);跨类感知 ``postprocess.nms``

修复
~~~~

- 推理 codec 重构收尾: ``_tensor_to_numpy`` / ``_parse_post_result`` 遗留 ``self`` 致相应解析必失败;删除被薄委托遮蔽的四份完整方法死实现;新增 AST 结构元测试防止同类漂移

v0.7.2 (2026-09-03)
-------------------

修复
~~~~

- ``_parse_infer_response`` codec 签名遗留 ``self``: 0.7.0 重构后所有 ``infer()`` / ``infer_batch()`` 调用抛 ``TypeError``;补充驱动真实 ``InferResponse`` 的回归测试

v0.7.1 (2026-09-03)
-------------------

- 版本号与 ``setup.py`` 对齐,无 API 变化

v0.7.0 (2026-09-02)
-------------------

新增功能
~~~~~~~~

- **应用开发工具箱** (原 0.6.0 开发版内容,未单独发布,随 0.7.0 一并发布):

  - ``Frame.crop()`` / ``Frame.resize()`` / ``Frame.to_jpeg_bytes()`` — 帧裁剪、三模式缩放(stretch/letterbox/crop)、JPEG 编码;cv2 缺失时自动降级到 numpy/PIL
  - ``draw`` 模块 — 检测结果可视化(``draw_boxes`` / ``draw_text`` / ``draw_detections``)
  - ``recording`` 模块 — 纯 Python TS 复用打包、HLS 切片、事件预录缓冲(``TsWriter`` / ``HlsWriter`` / ``PrerollBuffer``),无需 ffmpeg
  - ``web`` 模块 — MJPEG 推流(``MjpegServer`` / ``MjpegStream`` / ``mjpeg_wsgi_app``)
  - **DeviceClient** 原生对焦组 6 个方法(``start_oneshot_af`` / ``start_zoom_follow`` / ``get_autofocus_status`` / ``cancel_autofocus`` / ``set_af_windows`` / ``get_af_measurement``)
  - **CameraClient** 成像/红外/隐私遮挡/OSD/配置组 12 个方法(含红外预设管理、``get_osd`` 与 ``set_osd`` 读写对称)
- 修复 ``InferenceClient.subscribe()`` 静默丢弃失败帧的问题

重构
~~~~

- 内部架构分层:抽取 ``_transport`` 共享传输原语; ``media`` 拆分为 frame/encoded/fd_client; ``dsp`` 拆分为 dsp_wire/dsp_format; ``inference`` 拆分为 types/codec/genai。门面保持全部历史导入路径, **零公共 API 移除**
- DSP CPU 回退从静默日志改为 ``UserWarning``
- 2D 数组按灰度推理输入触发 ``DeprecationWarning`` (请显式传 ``fmt=``)
- ``EncodedStreamClient()`` 默认套接字路径改为 ``/run/aipc/encoded/{stream}.sock`` (``ENCODED_SOCK_DIR`` 环境变量可覆盖,显式路径仍优先)

修复
~~~~

- 修复 Python 3.8/3.9 下的导入崩溃(全量补齐 ``from __future__ import annotations``)

其他
~~~~

- 打包增加 ``py.typed`` 类型标记;测试扩充至 270 项全绿

v0.5.0 (2026-08-20)
-------------------

重构
~~~~

- 品牌重构:``hailo_ipc_sdk`` → ``neoruntime_ipc_sdk`` (破坏性变更,无兼容层;hailort/ne503/aipc 等功能性名称保留)

修复
~~~~

- 修复 ``audio_capture`` 流视频布局头的双布局解码

其他
~~~~

- CI 建立 TestPyPI/PyPI Trusted Publishing 双发布流程

v0.4.0 (2026-07-14)
-------------------

新增功能
~~~~~~~~

- **DeviceClient** 新增 7 个方法：
  - ``set_lens_limits(zoom_limit, focus_limit)`` — 设置镜头轴限位
  - ``oneshot_autofocus(timeout)`` — 单次自动对焦（复合操作：开启→等待收敛→关闭）
  - ``set_wiegand_out(channel, enable)`` — 韦根输出控制
  - ``get_wiegand_out(channel)`` — 韦根输出状态查询
  - ``rs485_init(baudrate, config)`` — RS-485 串口初始化
  - ``rs485_deinit()`` — RS-485 串口反初始化
  - ``rs485_tx(data)`` — RS-485 数据发送
- **AppClient** 新增 1 个方法：
  - ``restart_app(app_id, timeout_seconds)`` — 应用重启（停止+启动）

改进
~~~~

- 更新 API 文档，补充 DeviceClient 镜头限位、韦根、RS-485 示例
- 更新 API 文档，补充 AppClient 完整使用示例
- 同步中英文文档

v0.2.0 (2026-03-02)
-------------------

新增功能
~~~~~~~~

- 添加插件系统支持 (PluginDiscovery, PluginServer)
- 支持插件能力发现和 gRPC 服务调用
- 新增视频流访问能力（现由 ``FdMediaClient`` / ``EncodedStreamClient`` 提供）
- 支持原始视频流和编码视频流获取

改进
~~~~

- 优化 InferenceClient 性能
- 改进事件总线通配符匹配
- 增强错误处理和日志记录
- 更新 protobuf 到 4.21.0

修复
~~~~

- 修复 EventClient 订阅时的内存泄漏
- 修复 DeviceClient GPIO 控制问题
- 修复多线程环境下的连接池问题

v0.1.0 (2025-12-15)
-------------------

初始版本
~~~~~~~~

- InferenceClient: AI 推理客户端
- EventClient: 事件总线客户端
- DeviceClient: 设备控制客户端
- Config: 配置管理
- 支持 Python 3.8+
- 基于 gRPC 通信
