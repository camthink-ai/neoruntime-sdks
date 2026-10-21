NeoRuntime Platform C++ SDK 文档
==================================

欢迎使用 NeoRuntime C++ SDK！这是 NeoRuntime 边缘 AI 相机平台（NE503）
的 C++17 客户端开发包——Python SDK（``neoruntime_ipc_sdk``）的
**完整 API 镜像**：同一套平台能力、同一套传输协议，只是把 numpy 换成了
OpenCV ``cv::Mat``。

.. only:: html

   .. image:: https://img.shields.io/badge/cpp-0.8.0-blue.svg
      :target: https://github.com/camthink-ai/neoruntime-sdks/releases/tag/cpp-v0.8.0
      :alt: C++ SDK Version
   .. image:: https://img.shields.io/badge/tests-375-brightgreen.svg
      :target: https://github.com/camthink-ai/neoruntime-sdks/actions/workflows/cpp.yml
      :alt: Tests
   .. image:: https://img.shields.io/badge/license-MIT-green.svg
      :target: https://github.com/camthink-ai/neoruntime-sdks/blob/main/LICENSE
      :alt: License

概述
----

用 C++ SDK 构建的应用运行在设备上的应用容器内，通过本地 Unix Domain
Socket 与平台守护进程通信：

- **AI 推理**：单次 / 批量 / 流式推理（含健康度跟踪：时延与偏移 EMA、
  丢帧计数、连续失败上限），模型注册与统计，GenAI 流式
- **零拷贝取流**：``SCM_RIGHTS`` fd 传递的 DMA-BUF 帧、编码流
  （H.264/H.265）、音频流（PCM/AAC）
- **硬件能力**：DSP 作业（缩放 / 裁剪 / 转换 / 合成 / JPEG 编码）、
  硬件 overlay、流水线加速路由
- **设备控制**：灯光 / 红外 / IRCUT、云台 / 变焦 / 对焦、GPIO、RS485、
  Wiegand、自动对焦套件
- **事件总线**：发布 / 订阅（通配符主题）/ 批量
- **工程化**：C++17 / CMake ≥ 3.20 / vcpkg manifest，发布即装 arm64
  tarball，375 项无守护进程依赖的单元测试

文档导航
--------

- 第一次上手？从 :doc:`quickstart` 开始：装包（或源码构建）→ 连接
  冒烟 → 第一个推理程序。
- 想按阶段推进？:doc:`learning-path` 给出从连通到硬件加速的五阶段
  路线，每步对应仓库里一个可编译示例。
- 逐模块的用法手册（接口一览 + 真实代码示例，与 Python 手册同名对齐）：

  - :doc:`api/inference` —— AI 推理：单次 / 批量 / 流式 / 注册 / GenAI
  - :doc:`api/media` —— 视频流：零拷贝取帧、编码流、音频流
  - :doc:`api/overlay` —— AI 叠加层：硬件 overlay
  - :doc:`api/dsp` —— DSP 硬件加速：作业面与零读回链
  - :doc:`api/pipeline` —— 整管线：StreamPipeline / InferencePipeline /
    Runner
  - :doc:`api/events` —— 事件总线：发布 / 订阅 / 通配符 / 持久事件
  - :doc:`api/device` —— 设备控制：灯光 / 云台 / 镜头 / GPIO / RS485

- 想知道每个头文件负责什么？看 :doc:`modules` 模块总览。
- 从 Python SDK 迁移过来？:doc:`python-diff` 给出逐项对照。
- 版本线与发布节奏见 :doc:`versioning`。
- 英文 API 参考（Doxygen，按公共头文件生成）在
  `cpp/en/ <../en/index.html>`_。

.. toctree::
   :maxdepth: 2
   :caption: 用户指南

   learning-path
   quickstart
   modules
   python-diff
   versioning

.. toctree::
   :maxdepth: 2
   :caption: 模块手册

   api/inference
   api/media
   api/overlay
   api/dsp
   api/pipeline
   api/events
   api/device

索引和表格
----------

* :ref:`search`
