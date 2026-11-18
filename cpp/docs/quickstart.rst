快速上手
========

环境要求
--------

- C++17 编译器（GCC ≥ 9 / Clang ≥ 10）
- CMake ≥ 3.20
- vcpkg（manifest 模式，依赖自动解析：protobuf、grpc、opencv4
  headless、nlohmann-json）
- 设备端运行：NE503 应用容器（SDK 通过 ``/run/aipc/*.sock`` 与平台
  守护进程通信，无需网络配置）

方式一：消费发布 tarball（推荐）
--------------------------------

每个 ``cpp-v*`` 发布都附带
``ne503-aipc-cpp-sdk-<version>-linux-arm64.tar.gz`` （含头文件、静态库、
CMake 包文件与预编译示例）：

.. code-block:: sh

   # 1. 解包并让 find_package 指向它
   tar xf ne503-aipc-cpp-sdk-0.8.0-linux-arm64.tar.gz

   # 2. 你的 CMakeLists.txt：
   #    find_package(ne503_aipc_sdk 0.8.0 REQUIRED CONFIG)
   #    target_link_libraries(app PRIVATE ne503::ne503_aipc_sdk)

   # 3. 导出目标仍会链接 protobuf/gRPC/OpenCV/nlohmann_json——
   #    用声明了这些依赖的 vcpkg manifest 构建
   #    （镜像 cpp/vcpkg.json 的 opencv4 feature 集可复用二进制缓存）

   # 4. 交叉编译时显式传包目录——CMAKE_FIND_ROOT_PATH ONLY 模式会忽略
   #    sysroot 之外的 CMAKE_PREFIX_PATH：
   cmake -S myapp -B build-arm64 \
     -DCMAKE_TOOLCHAIN_FILE=$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake \
     -DVCPKG_CHAINLOAD_TOOLCHAIN_FILE=<sdk>/cpp/cmake/aarch64-toolchain.cmake \
     -DVCPKG_TARGET_TRIPLET=arm64-linux \
     -Dne503_aipc_sdk_DIR=<unpacked>/lib/cmake/ne503_aipc_sdk

.. note::

   设备端 Yocto 的 libstdc++ 早于 GLIBCXX_3.4.30，链接时加
   ``-static-libstdc++`` （tarball 自带示例即如此链接）。

方式二：仓库内构建
------------------

.. code-block:: sh

   git clone https://github.com/camthink-ai/neoruntime-sdks.git
   cd neoruntime-sdks

   # 本机构建 + 测试（x86_64）
   cmake -S cpp -B build-x64 -DCMAKE_BUILD_TYPE=Release
   cmake --build build-x64 -j && ctest --test-dir build-x64

   # aarch64 设备交叉编译
   cmake -S cpp -B build-arm64 \
     -DCMAKE_TOOLCHAIN_FILE=$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake \
     -DVCPKG_CHAINLOAD_TOOLCHAIN_FILE=$PWD/cpp/cmake/aarch64-toolchain.cmake \
     -DVCPKG_TARGET_TRIPLET=arm64-linux
   cmake --build build-arm64 -j

构建选项：``NE503_BUILD_EXAMPLES`` （默认 ON）、``NE503_BUILD_TESTS``
（默认 ON）、``NE503_REGEN_PROTOS`` （默认 ON——构建期从仓库根
``proto/`` 重新生成 protobuf/gRPC 桩）。

连接冒烟
--------

``connectivity_smoke`` 示例对设备上全部守护进程做 **只读** 往返查询
（不改任何状态，随时可安全运行）：

.. code-block:: console

   $ ./connectivity_smoke
   === NE503 C++ SDK connectivity smoke ===
   app_id    : my-app
   ai-runtime: unix:/run/aipc/ai-runtime.sock
   event-bus : unix:/run/aipc/event-bus.sock
   device-ctl: unix:/run/aipc/device-control.sock

   [InferenceClient] get_stats() OK
   [EventClient] get_stats() OK
   ...

退出码 0 = 全部守护进程应答。

第一个推理程序
--------------

.. code-block:: cpp

   #include <opencv2/core.hpp>
   #include <cstdio>

   #include "neoruntime_ipc_sdk/inference.hpp"

   int main() {
       using namespace neoruntime_ipc_sdk;

       InferenceClient inference;   // 端点默认取自环境，app 容器内开箱即连
       cv::Mat image(1080, 1920, CV_8UC3, cv::Scalar(0, 0, 0));

       InferenceResult result = inference.infer(image, "person_v1");
       std::printf("检测到 %zu 个对象\n", result.objects.size());
       for (const auto& obj : result.objects) {
           std::printf("  - %s: %.2f\n", obj.label.c_str(), obj.score);
       }
       return 0;
   }

流式推理与事件发布
------------------

流式推理返回 ``InferenceStream``，用 ``next()`` 拉取（SDK 全线统一的
拉取约定：流类型一律 ``next()`` 返回 ``std::optional``，空即流结束；
流水线类型用 ``next_result()``）；检测结果可直接经 ``EventClient``
发布：

.. code-block:: cpp

   #include "neoruntime_ipc_sdk/inference.hpp"
   #include "neoruntime_ipc_sdk/events.hpp"

   neoruntime_ipc_sdk::InferenceClient inference;
   neoruntime_ipc_sdk::EventClient events;

   auto stream = inference.subscribe("main", "person_v1");
   while (auto item = stream.next()) {
       const auto& result = item->second;
       if (!result.objects.empty()) {
           events.publish("app/alert",
                          {{"count", result.objects.size()}});
       }
   }

更完整的例子（区域布防 + 硬件 overlay + 结果循环）见仓库
``cpp/examples/stream_pipeline.cpp``；全部示例清单见
`cpp/README.md <https://github.com/camthink-ai/neoruntime-sdks/blob/main/cpp/README.md#examples>`_。

下一步
------

.. tip::

   冒烟与第一个程序跑通后，按 :doc:`learning-path` 的阶段推进——事件
   与设备 → 推理流 → 像素与硬件加速。每个模块的接口一览与完整用法
   （含真实代码示例）见手册章节 :doc:`api/inference` /
   :doc:`api/media` / :doc:`api/overlay` / :doc:`api/dsp` /
   :doc:`api/pipeline` / :doc:`api/events` / :doc:`api/device`。
