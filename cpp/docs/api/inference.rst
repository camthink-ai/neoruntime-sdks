AI 推理 API
===========

头文件 ``inference.hpp`` （值类型在 ``inference_types.hpp``）。AI 推理
的全部入口：单次 / 异步 / 批量 / 多张量、流式订阅、模型注册与统计、
GenAI 流式。

接口一览
--------

``InferenceClient`` 公开面：

- ``connect()`` / ``close()`` / ``connected()`` —— 建立、关闭与查询
  到 ai-runtime 服务的连接
- ``infer(input, model_id, timeout_ms=5000, priority=4, session_id="")``
  —— 单帧推理。 ``input`` 接受 ``cv::Mat`` 像素或 ``InferInput``
  （零拷贝：keep-fd 帧 / 守护进程侧缓冲 id），返回 ``InferenceResult``
- ``infer_async(...)`` —— 同 ``infer`` 的异步版，返回
  ``std::future<InferenceResult>``
- ``infer_batch(items, timeout_ms=10000)`` 与 ``infer_batch_async(...)``
  —— 批量推理（ ``batch_size > 1`` 的模型必须走这里）
- ``infer_with_tensors(model_id, inputs, input_names={})`` —— 跳过
  预处理直接喂张量
- ``subscribe(stream, model, fps=10, session_id="", raw_output_only=false,
  max_consecutive_failures=10, queue_size=100)`` —— 流式订阅，返回
  ``InferenceStream``
- ``register_model(model_path, model_id="", owner_id="", model_type="",
  model_variant="", inputs={}, outputs={}, batch_size=1)`` —— 注册
  应用自带模型，返回实际 model_id。配套： ``unregister_model(model_id)``
  / ``list_models()`` / ``get_model_info(model_id)``
- ``get_stats()`` / ``get_stats(sampling_window_ms)`` —— 系统统计
  （NPU 利用率、温度、请求计数， ``InferenceSystemStats`` ）
- ``create_session(session_id, app_id="", allowed_models={}, max_qps=0,
  max_concurrent=0, priority=4)`` / ``destroy_session(session_id)``
  —— 服务端会话（限流 / 隔离）
- ``update_postprocess_config(model_id, config_json)`` —— 运行时改
  后处理参数（如检测阈值，仅家族后处理模型生效）
- ``encode_text(text, timeout_ms=5000)`` —— 文本编码（CLIP 系模型）
- ``genai_create_session(hef_path, kind=Llm, lora_name="",
  optimize_memory=false)`` / ``genai_generate(session_id, messages,
  images={}, stop_tokens={}, temperature=0.0, top_p=1.0, top_k=0,
  max_tokens=512, do_sample=false)`` / ``genai_abort(session_id)`` /
  ``genai_destroy_session(session_id)`` —— GenAI 会话与逐 token 流

``InferenceStream`` （ ``subscribe`` 的返回值）：

- ``next()`` —— 拉取 ``(frame_sequence, InferenceResult)``；失败帧
  跳过，流干净结束返回 ``std::nullopt``
- ``cancel()`` / ``close()`` —— 任意线程停止 / 关闭订阅
- ``dropped()`` —— 客户端侧丢弃计数（消费太慢丢最旧）
- ``last_latency_ms()`` / ``avg_latency_ms()`` —— 单次 / EMA 时延
- ``last_skew_us()`` / ``avg_skew_us()`` —— 单次 / EMA 帧序偏移

``GenaiStream`` （ ``genai_generate`` 的返回值）：

- ``next()`` —— 拉取下一个 token，流结束返回 ``std::nullopt``
- ``finish_reason()`` —— 结束原因（stop / 长度截断等）

每个方法的完整参数文档见 `Doxygen 参考 <../../en/index.html>`_；
客户端面与 Python 侧逐位对齐，语义细节可参照
`/python/zh/ <../../../python/zh/index.html>`_ 对应章节。

使用示例
--------

单次与异步推理
~~~~~~~~~~~~~~

``infer()`` 接受 ``cv::Mat`` 像素或 ``InferInput`` （零拷贝输入：keep-fd
NV12 帧 / 守护进程侧 ``BufferRefInput``）：

.. code-block:: cpp

   neoruntime_ipc_sdk::InferenceClient inference;
   inference.connect();

   cv::Mat probe = cv::imread("probe.jpg");
   auto result = inference.infer(probe, "person_v1");

   // 异步版（std::async / std::future，调用方负责 wait）
   auto fut = inference.infer_async(probe, "person_v1");

.. tip::

   超时（默认 5000 ms）、优先级（默认 4）与 ``session_id`` 是 ``infer()``
   的可选尾参；批量用 ``infer_batch`` （超时默认 10000 ms）。

结果对象 ``InferenceResult`` 按模型类型携带 ``objects`` /
``classifications`` / ``landmarks`` / ``ocr_lines``，并提供标签过滤：

.. code-block:: cpp

   auto persons = result.get_objects_by_label("person");
   for (const auto& p : persons) {
       double cx = p.bbox.x + p.bbox.width / 2.0;
       double cy = p.bbox.y + p.bbox.height / 2.0;
       // p.score、p.track_id（>= 0 时随 overlay 渲染为 "#id"）
   }

流式订阅
~~~~~~~~

对相机流订阅推理，后台 pump 线程把服务端流读进 **有界丢最旧** 队列；
``next()`` 返回 ``(frame_sequence, InferenceResult)``，跳过失败帧，
流干净结束返回 ``std::nullopt``：

.. code-block:: cpp

   auto stream = inference.subscribe(
       "cam0_main", "person_v1",
       /*fps=*/15,
       /*session_id=*/"",
       /*raw_output_only=*/false,
       /*max_consecutive_failures=*/10,
       /*queue_size=*/100);

   while (auto item = stream.next()) {
       const auto frame_seq = item->first;
       const auto& result   = item->second;
       if (!result.objects.empty()) { /* ... */ }
   }

健康遥测直接挂在流对象上——消费太慢时最先看这里：

.. code-block:: cpp

   std::printf("dropped=%llu avg_latency=%.1fms avg_skew=%.0fus\n",
               (unsigned long long)stream.dropped(),
               stream.avg_latency_ms(), stream.avg_skew_us());

.. note::

   ``dropped()`` 计的是 **客户端侧** 因消费慢被丢弃的最旧结果；时延与
   偏移是 EMA（alpha 0.1）。连续失败达 ``max_consecutive_failures``
   （默认 10；``std::nullopt`` 关闭）后 ``next()`` 抛
   ``std::runtime_error`` 而非无限跳帧。``cancel()`` 可从任意线程停止
   订阅（阻塞在 ``next()`` 的消费者会醒来拿到 ``nullopt``）。

模型注册
~~~~~~~~

应用自带模型在启动时注册一次，全设备共享：

.. code-block:: cpp

   const std::string model_id =
       inference.register_model("/app/models/person_v1.hef",
                                "person_v1", "", "detection");

.. warning::

   手动注册 **必须留空 owner_id**：带 owner_id 的注册不进全局模型表，
   其他客户端 ``subscribe()`` / ``list_models()`` 会报 "Model not
   found"。批量模型（``batch_size > 1``，需要 batch 能力的 HEF）只能用
   ``infer_batch()``，单图 ``infer()`` 会被拒绝。

系统统计与 GenAI
~~~~~~~~~~~~~~~~

.. code-block:: cpp

   auto stats = inference.get_stats();
   std::printf("NPU util %.0f%%, temp %.1f°C\n",
               stats.device_utilization, stats.device_temperature);

   // GenAI：建会话 → 逐 token 流
   auto sid = inference.genai_create_session("/app/models/llm.hef");
   auto gen = inference.genai_generate(sid, {"用一句话介绍边缘计算"});
   while (auto token = gen.next()) std::fputs(token->c_str(), stdout);
   inference.genai_destroy_session(sid);
