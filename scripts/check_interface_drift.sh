#!/usr/bin/env bash
#
# Verify that committed SDK proto sources and generated Python stubs match the
# platform repository.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

if ! git diff --quiet -- . || ! git diff --cached --quiet -- .; then
    echo "ERROR: tracked working tree changes exist before interface drift check" >&2
    git status --short
    exit 2
fi

"$SCRIPT_DIR/sync_platform_protos.sh"

if git diff --quiet -- proto python/hailo_ipc_sdk/proto; then
    echo "Interface check passed: SDK proto files match the platform repository."
    exit 0
fi

echo "ERROR: SDK proto files drifted from the platform repository." >&2
git diff --stat -- proto python/hailo_ipc_sdk/proto >&2
exit 1
