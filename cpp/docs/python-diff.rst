Python → C++ 对照
=================

同一套架构，Python 习语换成 C++ 原生习语。从 Python SDK 迁移时按下表
逐项替换：

.. list-table::
   :header-rows: 1
   :widths: 30 34 36

   * - Python
     - C++
     - 说明
   * - numpy 数组
     - ``cv::Mat``
     - 布局校验（NV12 = ``(h*3/2, w)`` 8UC1）
   * - ``results()`` 迭代器
     - ``next() → std::optional<...>``
     - SDK 全线拉取约定（每条流类型都有 ``next()``）
   * - dict 多边形
     - ``OverlayPolygon`` / ``OverlayPoint``
     - 强类型，边界处校验
   * - ``queue.Queue`` + 哨兵
     - 有界丢最旧 ``ResultQueue``
     - 丢弃数计入 ``status()``
   * - daemon 线程
     - 可 join 的 ``std::thread``
     - ``stop()`` 负责回收；允许从回调内自停
   * - ``grpc.aio`` 线程
     - 同步 stub + ``std::future``
     - 同步 stub 本就停在 futex 上（实测 20ms 调用占 17% 单核）
   * - ``RuntimeError`` / ``ValueError``
     - ``std::runtime_error`` / ``std::invalid_argument``
     - 断言过的报错文本逐字一致
   * - ``DspError`` / ``HardwareUnavailable``
     - ``DspError`` （code −1..−7）/ ``std::runtime_error``
     -

阅读指引
--------

- Python 文档站（`/python/zh/ <../../python/zh/index.html>`_）的模块
  说明对 C++ 同样适用——两侧客户端面一一对应。
- 报错信息、事件主题、模型注册语义、帧几何契约两侧共享；差异只在
  语言绑定层（上面表格）。
- C++ 特有：公共头文件 proto-free（``*.pb.h`` 全在 ``src/``），头文件
  即完整公共 API 面。
