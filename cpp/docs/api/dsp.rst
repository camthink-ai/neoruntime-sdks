DSP 硬件加速 API
================

头文件 ``dsp.hpp`` 。把昂贵的像素操作交给 DSP：缩放 / 裁剪 / 转换 /
合成 / JPEG 编码。客户端同时保持一条 gRPC 与一条 UDS 连接；固件
不支持的操作自动落 CPU 回退（ ``last_used_hw()`` 如实报告上一作业
走的路径）。

接口一览
--------

``DspClient`` 作业面 —— 全部接受 ``DspJobSource`` （ ``cv::Mat`` /
``Frame`` / ``FrameHandle`` / ``DspBufferRef*`` ），共用 ``DspJobParams``
（ ``interpolation`` / ``scaling`` / ``priority`` / ``timeout_s`` /
``cpu_fallback`` / ``wait`` / ``out_ref`` ）：

- ``resize_hw(src, width, height, fmt="", params, src_pool, dst_pool)``
  —— 硬件缩放
- ``crop_hw(src, x, y, width, height, dst_width=-1, dst_height=-1, ...)``
  —— 裁剪（可同时缩放）
- ``multi_crop_hw(src, rects, ...)`` —— 多窗口裁剪，一次作业出多张
- ``convert_hw(src, dst_fmt, ...)`` —— 色彩转换（rgb ↔ nv12）
- ``blend_hw(base, overlays, fmt, blend_params)`` —— 多层合成
  （ ``DspOverlay`` 携带 ARGB 帧与落点， ``DspBlendParams`` 控零拷贝
  与目标池）
- ``encode_jpeg_hw(src, quality=85, fmt="", timeout_s=5.0, src_pool,
  cpu_fallback=true, buffer_id=0)`` —— JPEG 编码； ``src=nullptr`` 且
  给 ``buffer_id`` 时直接编码设备侧缓冲，零读回
- ``last_used_hw()`` —— 上一作业走硬件还是 CPU 回退
  （ ``std::optional<bool>`` ，首作业前为空）

缓冲管理：

- ``alloc_buffers(width, height, fmt="nv12", count=1)`` —— 分配
  daemon 侧缓冲池，返回 ``DspBufferPool``
- ``import_shared_buffers(width, height, fmt="argb", count=2,
  timeout_s=5.0)`` —— 导入共享可写 ARGB32 环（ ``SharedImportPool`` ，
  daemon 直接从这些页 blend）
- ``import_frame(FrameHandle&)`` —— 把帧的 dma-buf 导入 daemon
  注册表，返回 buffer_id
- ``release_buffer(buffer_id)`` —— 释放注册 id

作业的三种返回形状（由 ``DspJobParams`` 决定）：

- 同步 —— ``cv::Mat`` （ ``multi_crop_hw`` 为向量）
- ``wait=false`` —— ``PendingDspJob`` ： ``done(timeout_s=0)`` 非阻塞
  轮询； ``wait(timeout_s)`` 阻塞读回并释放； ``wait_all(timeout_s)``
  多裁剪读回； ``wait_result(timeout_s)`` 阻塞但产物留在设备侧；
  ``buffer_id()`` / ``job_id()`` / ``release()``
- ``out_ref=true`` —— ``DspBufferRef`` ： ``buffer_id()`` 链入下一个
  作业 / 编码； ``read()`` 按需读回像素； ``width()`` / ``height()`` /
  ``fmt()`` / ``released()`` / ``release()``

``DspBufferPool`` 暴露 ``width`` / ``height`` / ``fmt`` / ``ids`` /
``strides`` / ``plane_sizes`` 与 ``release()`` 。完整参数文档见
`Doxygen 参考 <../../en/index.html>`_。

使用示例
--------

.. code-block:: cpp

   neoruntime_ipc_sdk::DspClient dsp;

   // 硬件缩放：输入 cv::Mat，输出 variant（Mat 或错误）
   auto out = dsp.resize_hw(input_nv12, 320, 240, "nv12");
   if (auto* mat = std::get_if<cv::Mat>(&out)) {
       std::printf("resize done, hw=%d\n", (int)dsp.last_used_hw());
   }

**零读回链** 是 DSP 面的杀手锏——产物以 daemon 侧缓冲 id 存在，下一
个作业直接引用，应用进程不过像素：

.. code-block:: cpp

   neoruntime_ipc_sdk::DspJobParams ref_out;
   ref_out.out_ref = true;

   auto ref_variant = dsp.resize_hw(big_nv12, 1280, 720, "nv12",
                                    nullptr, ref_out);
   if (auto* ref = std::get_if<neoruntime_ipc_sdk::DspBufferRef>(
           &ref_variant)) {
       // JPEG 编码直接吃 buffer_id，无读回
       auto jpeg = dsp.encode_jpeg_hw(nullptr, 85, "nv12", 5.0,
                                      nullptr, false, ref->buffer_id());
       if (auto* bytes = std::get_if<std::vector<std::uint8_t>>(&jpeg)) {
           /* *bytes 即完整 JPEG */
       }
   }

.. tip::

   缓冲池（ ``DspClient::alloc_buffers`` ）适合反复提交同尺寸中间帧的
   场景；一次性作业直接喂 ``cv::Mat`` 即可，daemon 会导入。gray8 输入
   走 DSP 会被固件拒绝——路由层自动落 CPU 腿，无需分支处理。

.. warning::

   keep-fd 帧 + blend 的零拷贝链在当前固件上有 DSP 级致命问题，SDK
   默认拒绝；安全面（resize / convert / encode 的 keep-fd 直通）
   不受影响。
