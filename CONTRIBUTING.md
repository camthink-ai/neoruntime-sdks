# Contributing to NE503 AIPC SDKs

Thanks for helping improve the NE503 AIPC SDKs.

## Repository Layout

- `proto/` - platform API protocol definitions
- `python/` - Python SDK package, examples, tests, and documentation

Future language SDKs should live in their own top-level directories, such as
`go/`, `cpp/`, or `typescript/`.

## Python SDK Checks

Run these before opening a pull request:

```bash
python -m pip install -e ./python
python -m pytest -q python/tests
python -m pip install -r python/docs/requirements.txt
python -m sphinx -b html python/docs /tmp/ne503-sdk-docs/python/zh
python -m sphinx -b html python/docs/en /tmp/ne503-sdk-docs/python/en
```

## Pull Request Checklist

- [ ] Keep changes scoped to the SDK or protocol definitions.
- [ ] Add or update tests for behavior changes.
- [ ] Update documentation when public APIs change.
- [ ] Do not commit secrets, private IPs, model files, build artifacts, or vendor SDKs.
- [ ] Keep generated packages such as wheels, tarballs, and local caches out of Git.

## Security Issues

See [SECURITY.md](./SECURITY.md). Please do not open public issues for security
findings.
