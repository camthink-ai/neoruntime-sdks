事件总线 API
============

头文件 ``events.hpp`` 。跨应用 / 跨系统的发布订阅总线：JSON 载荷
（ ``nlohmann::json`` ）、通配符主题（ ``+`` 单层、 ``#`` 多层）、
持久事件与批量发布。

接口一览
--------

``EventClient`` 公开面：

- ``connect()`` / ``close()`` / ``connected()`` —— 连接管理
- ``publish(topic, payload, persistent=false, ttl_ms=nullopt,
  metadata={})`` —— 发布 JSON 事件，返回 event_id；
  ``persistent=true`` 配合 ``ttl_ms`` 让事件在总线内持久，离线消费者
  补得回
- ``publish_batch(events, persistent=false)`` —— ``{topic, payload}``
  对的向量，一次流式 RPC
- ``subscribe(topic, filters={}, queue_size=100, drop_old=true)`` ——
  拉取订阅，返回 ``EventStream``
- ``on_event(topic, cb, filters={})`` —— 回调订阅（后台分离线程）
- ``unsubscribe(topic)`` —— 退订
- ``list_topics()`` / ``get_topic_info(topic)`` —— 主题清单 / 详情
  （ ``TopicInfo`` ：订阅数、累计消息、最后消息时间）
- ``get_stats()`` / ``get_topic_stats(topic)`` —— 系统级
  （ ``SystemStats`` ）与单主题（ ``EventStats`` ：published /
  delivered / dropped 与平均时延）

``EventStream`` 只有一个拉取口： ``next()`` 出 ``std::optional<Event>``
，流结束返回空。

值类型 ``Event`` ： ``topic`` / ``payload`` / ``source`` / ``event_id``
/ ``timestamp_ns`` / ``metadata`` （ ``source`` 与时间戳留空时自动填
APP_ID / 当前时刻）。完整参数文档见
`Doxygen 参考 <../../en/index.html>`_。

使用示例
--------

发布：JSON 载荷用 ``nlohmann::json``；``persistent=true`` 让事件在
总线内持久（配合 ``ttl_ms``），离线消费者补得回：

.. code-block:: cpp

   neoruntime_ipc_sdk::EventClient events;

   std::string event_id = events.publish(
       "app/" + app_id + "/perimeter_alert",
       {{"type", "boundary_crossing"},
        {"frame_sequence", frame_seq},
        {"person_count", crossed.size()}},
       /*persistent=*/true);

   // 批量：{topic, payload} 对的向量，一次流式 RPC
   events.publish_batch({{"app/tick", {{"n", 1}}},
                         {"app/tick", {{"n", 2}}}});

订阅两种形状。回调版是后台分离线程（镜像 Python 的 on_event daemon
线程）；拉取版 ``subscribe()`` 返回 ``EventStream``，``next()`` 出
``std::optional<Event>``，同样支持通配符与 filters：

.. code-block:: cpp

   // 通配符主题：+ 单层，# 多层
   events.on_event("model/+/detections", on_detection);
   events.on_event("app/+/alert",        on_alert);
   events.on_event("system/device/#",    on_system);

   auto sub = events.subscribe("model/+/detections");
   while (auto ev = sub.next()) {
       std::printf("%s <- %s\n", ev->topic.c_str(), ev->source.c_str());
   }

.. warning::

   ``on_event`` 的回调在 **分离线程** 里跑且可能活过客户端析构（事件
   still in flight）——回调必须自包含，别捕获指向栈对象或客户端本身
   的引用。``source`` 与 ``timestamp_ns`` 留空时自动填（APP_ID /
   当前时刻）。

观测面：``list_topics()`` / ``get_topic_info()`` / ``get_stats()``
（``SystemStats`` 含 per-topic 的 published / delivered / dropped 与
平均时延）。

.. tip::

   事件 + 设备联动是平台的惯用组合——参考
   ``examples/event_subscriber.cpp`` （收到 person 检测事件即点灯）；
   设备侧执行器见 :doc:`device`。
