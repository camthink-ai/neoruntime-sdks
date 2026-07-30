更新日志
========

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
- 新增 MediaClient 用于视频流访问
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
