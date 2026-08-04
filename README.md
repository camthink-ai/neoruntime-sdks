# NE503 AIPC SDKs

SDKs for building applications on the NE503 AIPC edge AI platform.

This repository currently publishes the Python SDK and shared protocol
definitions. Additional language SDKs, including C++, can be added under this
repository as the platform API stabilizes.

## Contents

- `proto/` - source protocol definitions copied from the platform repository
- `python/` - Python SDK package, examples, tests, and Sphinx documentation
- `cpp/` - reserved location for the future C++ SDK
- `.github/workflows/pages.yml` - GitHub Pages documentation publishing
- `.github/workflows/sync-platform-protos.yml` - platform proto synchronization
- `.github/workflows/wheel.yml` - Python wheel build and release publishing

## Documentation

After GitHub Pages is enabled for this repository, the SDK documentation is
published at:

- `https://camthink-ai.github.io/ne503-aipc-sdks/`
- `https://camthink-ai.github.io/ne503-aipc-sdks/python/en/`
- `https://camthink-ai.github.io/ne503-aipc-sdks/python/zh/`
- `https://camthink-ai.github.io/ne503-aipc-sdks/cpp/en/`
- `https://camthink-ai.github.io/ne503-aipc-sdks/cpp/zh/`

## Python SDK

The SDK is not published to PyPI yet. Use one of the current install paths
below.

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

The repository also builds wheels automatically with GitHub Actions:

- Pull requests, pushes to `main`, and manual runs build and upload a wheel
  artifact named `python-sdk-wheel`.
- Tags matching `v*` build the wheel and attach it to a GitHub Release.
- Manual runs can also publish a GitHub Release when release publishing is
  enabled.

Release a version by pushing a tag that matches `python/setup.py`:

```bash
git tag v0.3.0
git push origin v0.3.0
```

PyPI and tarball packages are not published yet. Until those channels are
available, use source installs, local wheels, or GitHub Actions wheel artifacts.

Build local documentation:

```bash
python -m pip install -r python/docs/requirements.txt
python -m sphinx -b html python/docs /tmp/ne503-sdk-docs/python/zh
python -m sphinx -b html python/docs/en /tmp/ne503-sdk-docs/python/en
```

## Protocol Sync

`proto/` mirrors the protobuf interfaces from `camthink-ai/ne503-aipc`.
When platform proto files change, the platform repository can dispatch
`.github/workflows/sync-platform-protos.yml` in this repository. The sync job
copies the latest proto files, regenerates Python stubs, runs tests, and opens
a pull request when committed SDK files changed.

If the platform repository is private, configure `PLATFORM_REPO_TOKEN` in this
repository's Actions secrets. The token only needs read access to
`camthink-ai/ne503-aipc` contents.

Run the same check locally against a sibling platform checkout:

```bash
PLATFORM_WORKTREE=../ne503-aipc scripts/check_interface_drift.sh
```

Regenerate SDK interfaces locally:

```bash
PLATFORM_WORKTREE=../ne503-aipc scripts/sync_platform_protos.sh
```

## Related Repositories

- `camthink-ai/ne503-aipc` - NE503 AIPC platform core
- `camthink-ai/ne503-aipc-apps` - sample apps and app templates

## License

This repository is licensed under the MIT License. See [LICENSE](./LICENSE).
