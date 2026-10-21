AI 叠加层 API
=============

头文件 ``overlay.hpp`` 。把检测框 / 区域多边形画到设备编码侧——渲染
发生在 camera daemon，应用 CPU 零开销，RTSP / 录像 / Web 预览里看到
的就是带标注的画面。

接口一览
--------

``OverlayClient`` 公开面：

- ``connect()`` / ``close()`` / ``connected()`` —— 连接管理
- ``enable(show_label=true, show_confidence=true, line_thickness=2)``
  —— 开启 overlay 渲染
- ``disable()`` —— 关闭渲染
- ``configure(enabled=true, show_label=true, show_confidence=true,
  line_thickness=2, box_color=0, label_color=0, font_size=0,
  strict_frame_lock=nullopt, strict_wait_cap_ms=nullopt)`` —— 一次性
  配置； ``apply(config)`` 直接送整个 ``OverlayConfig``
- ``annotate(stream_id, detections=nullopt, polygons=nullopt,
  ttl_ms=nullopt, session_id="", frame_sequence=nullopt,
  stream_epoch=nullopt)`` —— 推检测框 + 区域多边形内容事件
- ``annotate_result(stream_id, result, ttl_ms=nullopt, session_id="",
  frame_sequence=nullopt, stream_epoch=nullopt)`` —— 整包推
  ``InferenceResult`` （自动挑已填的那一节）

配置与值类型：

- ``OverlayConfig`` —— ``enabled`` / ``show_label`` / ``show_confidence``
  / ``line_thickness`` / ``box_color`` / ``label_color`` / ``font_size``
  / ``strict_frame_lock`` / ``strict_wait_cap_ms``
- ``OverlayPolygon`` —— ``points`` （归一化 [0,1] 顶点，2..128 个） /
  ``label`` / ``closed`` / ``color`` / ``thickness``

完整参数文档见 `Doxygen 参考 <../../en/index.html>`_。

使用示例
--------

两个半面：**配置** 走 camera-control RPC，**内容** 走事件总线——
daemon 的 overlay 订阅者把检测框画到 NV12 帧上再编码。

.. code-block:: cpp

   neoruntime_ipc_sdk::OverlayClient overlay;
   overlay.connect();
   overlay.enable(/*show_label=*/true, /*show_confidence=*/true, 2);

   // 检测框 + 区域多边形一次推齐（均归一化 [0,1] 坐标）
   std::vector<neoruntime_ipc_sdk::OverlayPolygon> zones;
   neoruntime_ipc_sdk::OverlayPolygon zone;
   zone.points = {{0.10f, 0.10f}, {0.90f, 0.10f},
                  {0.90f, 0.90f}, {0.10f, 0.90f}};
   zone.label  = "watch zone";
   zones.push_back(zone);

   overlay.annotate("main", result.objects, zones, /*ttl_ms=*/2000);

   // 或整包推送 InferenceResult（自动挑 objects/classifications/
   // landmarks/ocr_lines 中已填的那一节）
   overlay.annotate_result("main", result);

.. note::

   内容事件在最后一次推送 ``ttl_ms`` 后过期（缺省按流 fps 推导），所以
   检测新鲜期间要以几 Hz 持续调 ``annotate``；overlay 本身必须先
   ``enable()``。``detections`` 传 ``{}`` 是 **清空** 框，传
   ``std::nullopt`` 是保持不动（只想推多边形时用后者）。

绑帧与会话：``session_id`` 作生命周期标签；``frame_sequence`` /
``stream_epoch`` （取自 ``InferenceResult`` / ``get_stream_status()``）
把事件绑到具体帧 / 流代际。严格帧锁（每帧在烘焙点等 **自己的** 推理
结果，上限 ``strict_wait_cap_ms``，范围 [0, 5000]）用 ``configure()``
开启。

.. tip::

   想要 "订阅 → 推理 → overlay → 结果" 一步成型，直接用
   :doc:`pipeline` 的 ``StreamPipeline`` （多边形随构造参数直送）。
