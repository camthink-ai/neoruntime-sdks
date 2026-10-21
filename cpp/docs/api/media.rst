视频流 API
==========

三个客户端一条主线： ``fd_client.hpp`` （ ``media.hpp`` 门面）零拷贝取
视频帧， ``encoded.hpp`` 拉 H.264 / H.265 编码流， ``audio_stream.hpp``
拉音频采集流。

接口一览
--------

``FdMediaClient`` 公开面：

- ``close()`` —— 关闭连接并归还全部 keep-fd 帧
- ``get_frame(stream_id, timeout_ms=5000, keep_fd=false)`` —— 单帧
  快照，返回 ``std::optional<Frame>``
- ``subscribe(stream_id, skip_frames=1, keep_fd=false, reconnect=true)``
  —— 拉流订阅，返回 ``FdMediaStream``
- ``on_frame(stream_id, cb, skip_frames=1, keep_fd=false)`` —— 后台
  线程回调版，返回 ``std::thread``
- ``retained_frames()`` —— 当前持有的 keep-fd 帧数
- ``get_encoded_stream(stream_id="main", socket_dir="")`` —— 取编码流
  客户端句柄
- ``list_streams()`` —— 活动管线流 id 列表
- ``get_rtsp_url(stream_id="main", host, port=8554)`` —— RTSP 拉流
  地址

``FdMediaStream`` 只有一个拉取口： ``next()`` 出 ``std::optional<Frame>``
，断流有界自动重连，重试耗尽后返回空。

``EncodedStreamClient`` （从 ``get_encoded_stream`` 取得）：

- ``connect()`` / ``close()`` / ``connected()`` —— 连接管理（不主动
  connect 时首个读取会懒连接）
- ``get_frame(timeout_ms=5000)`` —— 单包，超时 / EOF 返回
  ``std::nullopt``
- ``subscribe(reconnect=true)`` —— 拉取流，返回 ``EncodedStream``
  （ ``next()`` 逐包出 ``EncodedFrame`` ）
- ``on_frame(cb, reconnect=true)`` —— 后台线程回调版
- ``seq_stats()`` —— V3 序号观测：缺口 / 重启计数
  （ ``EncodedSeqStats`` ）

``EncodedFrame`` 携带 ``codec`` / ``flags`` / ``pts_ns`` / ``dts_ns`` /
``width`` / ``height`` / ``data`` / ``seq`` 与便捷方法 ``codec_name()``
/ ``is_keyframe()`` 。

``AudioStreamClient`` 公开面：

- ``get_frame(timeout_ms=5000)`` —— 拉一帧 ``AudioFrame``
- ``next_frame(reconnect=true)`` —— 拉取流（有界自动重连）
- ``close()`` —— 关闭

``AudioFrame`` 携带 ``sample_rate`` / ``channels`` / ``bits_per_sample``
/ ``pts_ns`` / ``dts_ns`` / ``data`` 与 ``codec_name()`` （pcm / aac /
g711a / g711u）、 ``duration_ms()`` 。

完整参数文档见 `Doxygen 参考 <../../en/index.html>`_。

使用示例
--------

零拷贝视频帧
~~~~~~~~~~~~

``FdMediaClient`` 说 FdPublisher UDS 协议：每帧是 80 字节
``FdPubFrameMsg`` + 最多 3 个 DMA-BUF fd 经 ``SCM_RIGHTS`` 传来。默认
路径把 plane ``mmap`` 后拷进 ``cv::Mat`` 立即归还；``keep_fd=true``
保留 dma-buf fd，daemon 侧 RELEASE 推迟到最后一帧副本消失。

拉流（有界自动重连，断流重试耗尽后 ``next()`` 返回 ``std::nullopt``）：

.. code-block:: cpp

   neoruntime_ipc_sdk::FdMediaClient media;

   auto streams = media.list_streams();          // 活动管线流 id
   auto stream  = media.subscribe(streams[0]);   // skip_frames 可抽帧
   while (auto frame = stream.next()) {
       std::printf("seq=%llu %dx%d\n",
                   (unsigned long long)frame->sequence,
                   frame->width, frame->height);
   }

单帧快照带超时；``Frame`` 自带 ``to_rgb()`` / ``crop`` / ``resize`` /
JPEG 编码：

.. code-block:: cpp

   if (auto frame = media.get_frame("main", /*timeout_ms=*/2000)) {
       cv::Mat bgr;
       cv::cvtColor(frame->to_rgb(), bgr, cv::COLOR_RGB2BGR);
       cv::imwrite("snapshot.jpg", bgr);
   }

.. tip::

   只需要每 N 帧处理一次时，用 ``subscribe(stream_id, /*skip_frames=*/N)``
   让 SDK 在源头抽帧，而不是收下全部再自己丢——被抽掉的 keep-fd 帧
   会立即归还 daemon，不占缓冲池。

keep-fd 与缓冲池纪律
~~~~~~~~~~~~~~~~~~~~

.. code-block:: cpp

   // 后台线程版：回调每帧一次（cb 异常被吞；自行 detach/join）
   std::thread t = media.on_frame("main", [&](const Frame& f) {
       // 零拷贝持有 dma-buf 的处理路径
   });

.. warning::

   ``retained_frames()`` 报告当前持有的 keep-fd 帧数。camera daemon
   的缓冲池是个位数——持有量逼近池容量会 **饿死直播流**。用完的帧尽快
   ``release()``，退出前调用 ``media.close()`` 归还全部。

编码流与音频流
~~~~~~~~~~~~~~

编码流客户端从 ``FdMediaClient`` 拿句柄，V3 序号自带缺口 / 重启计数：

.. code-block:: cpp

   auto enc = media.get_encoded_stream("main");   // H.264 / H.265
   while (auto packet = enc.get_frame(2000)) {
       std::printf("codec=%s bytes=%zu\n",
                   packet->codec_name().c_str(), packet->data.size());
   }

音频采集流同一拉取形状，帧携带 ``sample_rate`` / ``channels`` /
``bits_per_sample`` / ``dts_ns``：

.. code-block:: cpp

   neoruntime_ipc_sdk::AudioStreamClient audio;
   if (auto chunk = audio.get_frame(2000)) {
       std::printf("%d Hz %d ch %d-bit\n", chunk->sample_rate,
                   chunk->channels, chunk->bits_per_sample);
   }

.. note::

   RTSP 拉流需先在设备上开启 RTSP （``CameraClient`` 或 REST API），
   然后 ``media.get_rtsp_url("main")`` 取地址。流能力查询用
   ``CameraClient::get_capabilities`` / ``get_stream_status`` （ISP、
   编码器、profile、隐私遮挡——见 :doc:`../modules` 总览）。
