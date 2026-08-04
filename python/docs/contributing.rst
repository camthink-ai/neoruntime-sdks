贡献指南
========

感谢你对 AIPC Platform Python SDK 的关注！

开发环境设置
------------

1. 克隆仓库：

.. code-block:: bash

   git clone https://github.com/camthink-ai/ne503-aipc-sdks.git
   cd sdk-python

2. 创建虚拟环境：

.. code-block:: bash

   python3 -m venv venv
   source venv/bin/activate

3. 安装开发依赖：

.. code-block:: bash

   pip install -e ".[dev]"

代码规范
--------

我们使用以下工具确保代码质量：

- **black**: 代码格式化
- **flake8**: 代码检查
- **mypy**: 类型检查

运行检查：

.. code-block:: bash

   # 格式化代码
   black hailo_ipc_sdk tests

   # 代码检查
   flake8 hailo_ipc_sdk tests

   # 类型检查
   mypy hailo_ipc_sdk

测试
----

运行所有测试：

.. code-block:: bash

   pytest tests/

运行特定测试：

.. code-block:: bash

   pytest tests/test_inference.py

生成覆盖率报告：

.. code-block:: bash

   pytest --cov=hailo_ipc_sdk --cov-report=html tests/

提交代码
--------

1. 创建新分支：

.. code-block:: bash

   git checkout -b feature/my-feature

2. 提交更改：

.. code-block:: bash

   git add .
   git commit -m "feat: add new feature"

3. 推送分支：

.. code-block:: bash

   git push origin feature/my-feature

4. 创建 Pull Request

提交信息规范
~~~~~~~~~~~~

使用 Conventional Commits 规范：

- ``feat:``: 新功能
- ``fix:``: 修复 bug
- ``docs:``: 文档更新
- ``style:``: 代码格式调整
- ``refactor:``: 代码重构
- ``test:``: 测试相关
- ``chore:``: 构建/工具相关

文档
----

构建文档：

.. code-block:: bash

   cd docs
   make html

查看文档：

.. code-block:: bash

   open _build/html/index.html

问题反馈
--------

如果你发现 bug 或有功能建议，请在 GitHub 上创建 issue：

https://github.com/camthink-ai/ne503-aipc-sdks/issues

许可证
------

本项目采用 MIT 许可证。
