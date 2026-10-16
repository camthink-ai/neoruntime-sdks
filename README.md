# NeoRuntime SDKs

SDKs for building applications on the NeoRuntime edge AI platform.

This repository publishes the Python SDK, the C++ SDK and shared protocol
definitions for NeoRuntime applications.

## Contents

- `proto/` - source protocol definitions copied from the platform repository
- `python/` - Python SDK package, examples, tests, and Sphinx documentation
- `cpp/` - C++ SDK mirror of the Python SDK (clients, transports, tests,
  examples)
- `docs/sdk-module-framework.md` - current cross-language SDK module map and
  extension rules
- `.github/workflows/pages.yml` - GitHub Pages documentation publishing
- `.github/workflows/sync-platform-protos.yml` - platform proto synchronization
- `.github/workflows/wheel.yml` - Python SDK release artifact publishing
- `.github/workflows/cpp.yml` - C++ SDK CI and `cpp-v*` release publishing

## Documentation

New to the SDK? Start with the [learning path](https://camthink-ai.github.io/neoruntime-sdks/python/en/learning-path.html) ([中文](https://camthink-ai.github.io/neoruntime-sdks/python/zh/learning-path.html)) — five stages from first inference to your first installed app.

No device yet? The [device onboarding](https://camthink-ai.github.io/neoruntime-sdks/python/en/device-onboarding.html) ([中文](https://camthink-ai.github.io/neoruntime-sdks/python/zh/device-onboarding.html)) page covers buying an NE503 and logging in for the first time.

- [Python SDK 中文接口使用手册](python/SDK_API_ZH.md)

The SDK documentation is published at:

- `https://camthink-ai.github.io/neoruntime-sdks/`
- `https://camthink-ai.github.io/neoruntime-sdks/python/en/`
- `https://camthink-ai.github.io/neoruntime-sdks/python/zh/`
- `https://camthink-ai.github.io/neoruntime-sdks/cpp/en/` (Doxygen API reference)
- `https://camthink-ai.github.io/neoruntime-sdks/cpp/zh/` (Chinese quick-start)

## Python SDK

Install from PyPI:

```bash
python -m pip install neoruntime-ipc-sdk
```

Pre-release builds are staged on TestPyPI for validation (dependencies still
come from PyPI):

```bash
python -m pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ neoruntime-ipc-sdk
```

Install from source:

```bash
python -m pip install -e ./python
```

Run tests:

```bash
python -m pytest -q python/tests
```

Build a Python wheel:

```bash
cd python
python -m pip install --upgrade build
python -m build --wheel
ls dist/*.whl
```

Generated wheels are written to `python/dist/` and should not be committed.

The repository also builds release artifacts automatically with GitHub Actions:

- Pull requests, pushes to `main`, and manual runs build and upload Python
  distributions (wheel + sdist) as an artifact named `python-sdk-dist`.
- Tags matching `v*` build the Python distributions, attach them to a GitHub
  Release, upload them to TestPyPI, and then to PyPI once the protected `pypi`
  environment is approved.
- Manual runs can also publish a GitHub Release, TestPyPI, or PyPI when the
  corresponding dispatch inputs are enabled.

Release a version by pushing a tag that matches `python/setup.py` (and
`python/neoruntime_ipc_sdk/__init__.py`, which must stay in sync).

```bash
git tag v0.5.0
git push origin v0.5.0
```

The GitHub Release assets are:

- `neoruntime_ipc_sdk-0.5.0-py3-none-any.whl`
- `neoruntime_ipc_sdk-0.5.0.tar.gz`

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full release and publishing
runbook.

Build local documentation:

```bash
python -m pip install -r python/docs/requirements.txt
python -m sphinx -b html python/docs /tmp/neoruntime-sdk-docs/python/zh
python -m sphinx -b html python/docs/en /tmp/neoruntime-sdk-docs/python/en
python -m sphinx -b html cpp/docs /tmp/neoruntime-sdk-docs/cpp/zh
(cd cpp && doxygen Doxyfile)   # → cpp/doxy-out/html
```

## Interactive teaching demo

The fastest way to learn the SDK is to drive it. **sdk-teaching-demo** is a
single installable app with five live stations against real camera streams —
subscribe + infer + draw (B form), platform overlay vs your own pixels,
hardware routing (including a deliberate refusal), A-form `StreamPipeline`,
and cooldown-gated event publishing. Every station also shows the real code
behind it (copy button included) and the error lesson for that station —
DMA -2811, `None` vs `[]` overlay cleanup, exit codes under
`restart_policy: on-failure`.

```bash
# on the device, after downloading the bundle:
aipc-cli app install sdk-teaching-demo <path-to-app.yaml> <path-to-image.tar>
aipc-cli app start sdk-teaching-demo
```

- Bundle: [sdk-teaching-demo-latest-arm64.neoapp](https://github.com/camthink-ai/neoruntime-apps/releases/download/showcase-bundles-latest/sdk-teaching-demo-latest-arm64.neoapp)
- Source: [showcases/sdk-teaching-demo](https://github.com/camthink-ai/neoruntime-apps/tree/main/showcases/sdk-teaching-demo) · starter skeleton: [templates/basic](https://github.com/camthink-ai/neoruntime-apps/tree/main/templates/basic)

## C++ SDK

`cpp/` is a native C++17 mirror of the Python SDK for on-device development —
the same daemon clients over gRPC-on-UDS and raw-UDS transports, with a
daemon-independent GoogleTest suite. See [cpp/README.md](cpp/README.md) for
the client surface, build instructions (native and aarch64 cross-compile) and
examples.

C++ releases are tagged with the `cpp-v*` prefix and versioned independently
of the Python SDK (the version line tracks the mirrored Python API surface —
see `cpp/include/neoruntime_ipc_sdk/version.hpp`). A release attaches the
installable aarch64 (NE503) package:

- `ne503-aipc-cpp-sdk-<version>-linux-arm64.tar.gz`

## Protocol Sync

`proto/` mirrors the protobuf interfaces from `camthink-ai/neoruntime`.
When platform proto files change, the platform repository can dispatch
`.github/workflows/sync-platform-protos.yml` in this repository. The sync job
copies the latest proto files, regenerates Python stubs, runs tests, and opens
a pull request when committed SDK files changed.

If the platform repository is private, configure `PLATFORM_REPO_TOKEN` in this
repository's Actions secrets. The token only needs read access to
`camthink-ai/neoruntime` contents.

Run the same check locally against a sibling platform checkout:

```bash
PLATFORM_WORKTREE=../neoruntime scripts/check_interface_drift.sh
```

Regenerate SDK interfaces locally:

```bash
PLATFORM_WORKTREE=../neoruntime scripts/sync_platform_protos.sh
```

## Related Repositories

- `camthink-ai/neoruntime` - NeoRuntime platform core
- `camthink-ai/neoruntime-apps` - sample apps and app templates

## License

This repository is licensed under the MIT License. See [LICENSE](./LICENSE).
