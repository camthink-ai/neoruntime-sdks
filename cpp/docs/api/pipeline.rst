整管线 API
==========

三种由重到轻的编排： ``stream_pipeline.hpp`` 让平台调度全链（像素留在
设备上）， ``pipeline.hpp`` 是客户端侧 前处理 → 推理 → 后处理（像素进
你的进程）， ``runner.hpp`` 把后者跑在任意帧源上。

接口一览
--------

``StreamPipeline`` （ ``stream_pipeline.hpp`` ）：

- 构造参数即全部策略： ``stream`` / ``model`` / ``fps=10`` /
  ``session_id=""`` / ``raw_output_only=false`` /
  ``max_consecutive_failures=10`` / ``queue_size=100`` / ``draw=true``
  / ``overlay_config=nullopt`` / ``ttl_ms=nullopt`` / ``min_score=0.0``
  / ``labels=nullopt`` / ``polygons=nullopt`` / ``on_result=nullptr``
  / ``result_queue_size=100`` ，末尾还可注入自备的
  ``InferenceClient*`` / ``OverlayClient*`` （缺省自建）
- ``start()`` / ``stop()`` —— 启动 / 收摊（清掉 overlay 上的框与
  多边形）
- ``next_result()`` —— 阻塞拉取 ``(frame_sequence, InferenceResult)``
  ，流水线停止后返回 ``std::nullopt``
- ``status()`` —— ``StreamPipelineStatus`` ：运行标志、结果计数、
  overlay 计数与错误、结果队列丢弃、透传订阅健康
  （ ``subscribe_dropped`` ）、时延与偏移 EMA

``InferencePipeline`` （ ``pipeline.hpp`` ）：

- ``InferencePipeline(client={}, model_id="", preprocessor=nullopt,
  postprocessor=nullptr, infer_timeout_ms=5000, retain_input=false)``
- ``from_model(model_id, client={}, postprocessor=nullptr,
  preprocess_overrides={})`` —— 按模型输入规格自动派生预处理
- ``run(source, model_id="")`` —— 同步跑一帧（ ``source`` 为 keep-fd
  ``Frame`` 或 ``cv::Mat`` ），返回 ``PipelineResult``
- ``run_async(source, model_id="")`` —— 异步版（ ``std::future`` ）；
  future 必须取值，流水线对象必须活过 future
- ``client()`` —— 访问内部 ``InferenceClient``
- 组件可单用： ``preprocess.hpp`` （letterbox 预处理）与
  ``postprocess.hpp`` （NMS + YoloV5/V8 解码）

``PipelineRunner`` （ ``runner.hpp`` ）：

- ``PipelineRunner(source, pipeline, sink=nullptr, queue_size=1,
  drop_policy="latest", on_error=nullptr, max_consecutive_errors=10,
  name="pipeline")`` —— 在帧源上持续跑流水线； ``source`` 是返回
  ``std::optional<Frame>`` 的函数， ``sink`` 收 ``(result, frame)``
- ``start()`` / ``stop(timeout_s=5.0)`` —— 启停双线程
- ``stats()`` —— ``RunnerStats`` ：吞吐 / 丢弃 / 时延 EMA / 错误计数
- ``take_last_results()`` —— 取走最近 16 次结果（无 sink 时的捕获）

完整参数文档见 `Doxygen 参考 <../../en/index.html>`_。

使用示例
--------

StreamPipeline——平台调度整链
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

一个对象包办 订阅 → 推理 → overlay → 应用结果队列。构造参数即全部
策略，来自 ``examples/stream_pipeline.cpp``：

.. code-block:: cpp

   using neoruntime_ipc_sdk::StreamPipeline;
   using neoruntime_ipc_sdk::OverlayPolygon;

   OverlayPolygon zone;
   zone.points = {{0.10f, 0.10f}, {0.90f, 0.10f},
                  {0.90f, 0.90f}, {0.10f, 0.90f}};
   zone.label  = "watch zone";

   StreamPipeline pipe(
       "third",          // 流 id
       model_id,         // 已注册的模型
       /*fps=*/5,
       "stream-pipeline-example",           // session_id
       /*raw_output_only=*/false,
       /*max_consecutive_failures=*/10,
       /*queue_size=*/8,
       /*draw=*/true,                        // 推理结果上硬件 overlay
       /*overlay_config=*/std::nullopt,
       /*ttl_ms=*/2000,                      // overlay 内容有效期
       /*min_score=*/0.35,                   // 分数门槛
       /*labels=*/std::nullopt,              // nullopt = 全部标签
       /*polygons=*/std::vector<OverlayPolygon>{zone},
       /*on_result=*/[](const InferenceResult&) -> std::optional<InferenceResult> {
           return std::nullopt;  // nullopt = 不改写结果
       });

   pipe.start();
   while (auto result = pipe.next_result()) {   // 阻塞拉取
       // *result 已过 min_score / labels 过滤
   }

``next_result()`` 阻塞直到下一结果；``std::nullopt`` 表示流水线已停。
``on_result`` 回调可改写或否决每个结果再入队。``status()`` 报队列
深度 / 丢弃计数；``stop()`` 收摊并清掉 overlay 上的框与多边形。

.. note::

   **流几何约束**：``StreamPipeline`` / ``subscribe`` 不做缩放——流
   几何必须等于模型输入几何。主码流 1080p 需模型支持 DMA 输入；
   ``third`` 子流 640x384 可直接喂。喂主码流的模型请用
   ``.bin`` + ``spec.models`` 形态注册。

客户端侧 InferencePipeline
~~~~~~~~~~~~~~~~~~~~~~~~~~

需要亲手摸像素（自研后处理、编码上云、逐帧旁路）时用
``pipeline.hpp``：按模型规格 letterbox 预处理、推理、NMS +
YoloV5/V8 解码都在你进程里串好，``preprocess.hpp`` /
``postprocess.hpp`` 的组件也可单独用。``runner.hpp`` 的
``PipelineRunner`` 再包一层"在帧源上持续跑这条流水线"的循环。

.. tip::

   经验法则：结果只用于告警 / 事件 / overlay → ``StreamPipeline``；
   结果要进自己的像素处理 → ``InferencePipeline`` + ``FdMediaClient``
   （零拷贝取帧见 :doc:`media`）。
