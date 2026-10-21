学习路径
========

从零到产出可部署应用的推荐顺序。每步都对应仓库 ``cpp/examples/``
里一个可编译的完整程序——卡住时直接读源码。

.. only:: html

   .. image:: https://img.shields.io/badge/examples-9-blue.svg
      :target: https://github.com/camthink-ai/neoruntime-sdks/tree/main/cpp/examples
      :alt: examples

第一阶段：连通与环境（半天）
----------------------------

:doc:`quickstart` 全篇：tarball 装包（或源码构建）→ 跑
``connectivity_smoke`` 确认 UDS 通路 → 第一个 ``infer()`` 程序。

- 目标：``connectivity_smoke`` 全绿，理解应用容器 + 本地 UDS 的部署
  形态。
- 对应示例：``connectivity_smoke.cpp``。

第二阶段：事件与设备（半天）
----------------------------

不碰像素，先用最便宜的两个客户端把"平台感知"建起来：

- ``EventClient`` 订阅 ``model/+/detections`` 等主题（通配符 +、#），
  看别的应用 / 系统在发什么；
- ``DeviceClient`` 点灯、读镜头与整机状态。
- 对应示例：``event_subscriber.cpp`` （事件驱动点灯）。
- 手册： :doc:`api/events` 与 :doc:`api/device`。

第三阶段：推理流（一天）
------------------------

- ``subscribe()`` + ``next()`` 拉推理流，盯 ``dropped()`` /
  ``avg_latency_ms()`` 理解健康遥测；
- 标签过滤 ``get_objects_by_label`` + 简单业务规则（越线判定）；
- 告警走 ``publish(..., persistent=true)``
- 对应示例：``person_detection.cpp`` → ``perimeter_guard.cpp``
  （后者含灯光联动与冷却逻辑，是"小而全"的参考应用）。
- 手册： :doc:`api/inference`。

第四阶段：像素与硬件（一到两天）
--------------------------------

按需求二选一或都走：

- **要结果不要像素**：``StreamPipeline`` 一步到位（订阅 → 推理 →
  硬件 overlay → 结果队列），配 ``OverlayPolygon`` 区域多边形；
- **要像素**：``FdMediaClient`` 零拷贝取帧（keep-fd 纪律！），
  ``DspClient`` 把缩放 / JPEG 编码推给 DSP，玩 ``buffer_id`` 零读回链。
- 对应示例：``stream_pipeline.cpp`` / ``video_processor.cpp`` /
  ``dsp_resize.cpp``。
- 手册： :doc:`api/pipeline` / :doc:`api/media` / :doc:`api/overlay`
  / :doc:`api/dsp`。

第五阶段：全模块漫游与部署（持续）
----------------------------------

- ``api_tour.cpp`` 把每个客户端的核心调用过一遍——迁移到 C++ 的
  Python 老用户可直接对照 :doc:`python-diff`；
- 进阶面：帧注入（``injection.hpp``）、音频流、GenAI、诊断报告
  （``diagnostics.hpp``）；
- 版本与升级注意：:doc:`versioning`。

.. tip::

   写业务逻辑前先想清楚 **像素要不要进你的进程**——这个决定同时选定了
   流水线形态（``StreamPipeline`` vs ``InferencePipeline``）、几何约束
   和 DSP 用法，返工成本最高。
