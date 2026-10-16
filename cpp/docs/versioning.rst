版本线与发布
============

独立版本线
----------

C++ SDK 与 Python SDK **各自独立演进**：

- 发布 tag 用 ``cpp-v*`` 前缀（如 ``cpp-v0.8.0``）
- 版本号跟随所镜像的 Python API 面：**major.minor 对齐**，patch 独立
  演进——例如 C++ 0.8.0 镜像 Python 0.8.x
- ``version.hpp`` 的 ``kMirroredPythonSdk`` 记录镜像来源的确切 Python
  版本（0.8.0 对应 ``kMirroredPythonSdk = "0.8.1"``）
- Python 的 ``v*`` tag（触发 wheel.yml → PyPI）与 C++ 的 ``cpp-v*``
  tag（触发 cpp.yml → arm64 tarball）**永不互相触发**对方的发布链
- 里程碑可以同天双 tag、两份 release notes 互指，但不锁号

发布链
------

推送 ``cpp-v*`` tag 后 CI 自动执行：

1. x86_64 全量构建 + 375 项测试
2. 版本校验（tag 剥前缀 == ``CMakeLists.txt`` ``VERSION`` ==
   ``kVersion`` == ``vcpkg.json`` version-string）
3. aarch64 交叉编译 + 打包即装 tarball
4. GitHub Release 附
   ``ne503-aipc-cpp-sdk-<version>-linux-arm64.tar.gz``

每个版本的确切变更见仓库
`cpp/CHANGELOG.md <https://github.com/camthink-ai/neoruntime-sdks/blob/main/cpp/CHANGELOG.md>`_。

依赖契约
--------

C++ SDK 按仓库根 ``proto/`` 定义与该 tag 当时的平台固件契约构建。
每个版本在 CHANGELOG 里写明确切依赖；从源码构建需要 ``proto/`` 加
宿主机上的 ``protoc`` 与 ``grpc_cpp_plugin``。
