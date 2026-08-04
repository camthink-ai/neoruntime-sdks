#!/usr/bin/env bash
#
# Sync protobuf definitions from the platform repository and regenerate Python
# protobuf stubs committed with the SDK.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PLATFORM_REPO="${PLATFORM_REPO:-https://github.com/camthink-ai/ne503-aipc.git}"
PLATFORM_REF="${PLATFORM_REF:-main}"
PLATFORM_REPO_TOKEN="${PLATFORM_REPO_TOKEN:-}"
PLATFORM_WORKTREE="${PLATFORM_WORKTREE:-}"
PYTHON="${PYTHON:-python3}"

PROTO_OUT="$REPO_ROOT/python/hailo_ipc_sdk/proto"

copy_proto() {
    local src="$1"
    local dst="$2"

    if [ ! -f "$PLATFORM_DIR/$src" ]; then
        echo "ERROR: missing platform proto: $src" >&2
        exit 1
    fi

    mkdir -p "$(dirname "$REPO_ROOT/$dst")"
    cp "$PLATFORM_DIR/$src" "$REPO_ROOT/$dst"
    echo "  + $dst"
}

generate_python_proto() {
    local proto_dir="$1"
    local proto_file="$2"
    local grpc_include

    grpc_include="$("$PYTHON" - <<'PY'
from pathlib import Path
import grpc_tools

print(Path(grpc_tools.__file__).resolve().parent / "_proto")
PY
)"

    (
        cd "$REPO_ROOT/$proto_dir"
        "$PYTHON" -m grpc_tools.protoc \
            -I . \
            -I "$grpc_include" \
            --python_out="$PROTO_OUT" \
            --grpc_python_out="$PROTO_OUT" \
            "$proto_file"
    )
}

if [ -n "$PLATFORM_WORKTREE" ]; then
    PLATFORM_DIR="$PLATFORM_WORKTREE"
else
    TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/ne503-platform-protos.XXXXXX")"
    trap 'rm -rf "$TMP_DIR"' EXIT

    PLATFORM_DIR="$TMP_DIR/platform"
    git init -q "$PLATFORM_DIR"
    git -C "$PLATFORM_DIR" remote add origin "$PLATFORM_REPO"
    if [ -n "$PLATFORM_REPO_TOKEN" ]; then
        auth_header="$(printf 'x-access-token:%s' "$PLATFORM_REPO_TOKEN" | base64 | tr -d '\n')"
        fetch_status=0
        git -C "$PLATFORM_DIR" \
            -c "http.https://github.com/.extraheader=AUTHORIZATION: basic $auth_header" \
            fetch --depth 1 origin "$PLATFORM_REF" || fetch_status=$?
    else
        fetch_status=0
        git -C "$PLATFORM_DIR" fetch --depth 1 origin "$PLATFORM_REF" || fetch_status=$?
    fi

    if [ "$fetch_status" -ne 0 ]; then
        echo "ERROR: failed to fetch $PLATFORM_REPO at $PLATFORM_REF." >&2
        echo "       If the platform repository is private, set PLATFORM_REPO_TOKEN with read access to it." >&2
        exit "$fetch_status"
    fi

    git -C "$PLATFORM_DIR" checkout -q FETCH_HEAD
fi

echo "==> Syncing platform proto definitions"
copy_proto "platform/ai-runtime/proto/inference.proto" "proto/ai-runtime/inference.proto"
copy_proto "platform/app-manager/proto/app.proto" "proto/app-manager/app.proto"
copy_proto "platform/camera-daemon/proto/camera.proto" "proto/camera-daemon/camera.proto"
copy_proto "platform/camera-daemon/proto/lens_hal.proto" "proto/camera-daemon/lens_hal.proto"
copy_proto "platform/device-control/proto/device.proto" "proto/device-control/device.proto"
copy_proto "platform/device-discovery/proto/discovery.proto" "proto/device-discovery/discovery.proto"
copy_proto "platform/event-bus/proto/event.proto" "proto/event-bus/event.proto"

echo "==> Regenerating Python protobuf stubs"
rm -f "$PROTO_OUT"/*_pb2.py "$PROTO_OUT"/*_pb2_grpc.py
touch "$PROTO_OUT/__init__.py"

generate_python_proto "proto/ai-runtime" "inference.proto"
generate_python_proto "proto/app-manager" "app.proto"
generate_python_proto "proto/camera-daemon" "camera.proto"
generate_python_proto "proto/device-control" "device.proto"
generate_python_proto "proto/event-bus" "event.proto"

"$PYTHON" - "$PROTO_OUT" <<'PY'
from pathlib import Path
import re
import sys

proto_out = Path(sys.argv[1])
pattern = re.compile(r"^import ([A-Za-z0-9_]+_pb2) as ([A-Za-z0-9_]+__pb2)$", re.MULTILINE)

for path in proto_out.glob("*_pb2_grpc.py"):
    text = path.read_text(encoding="utf-8")
    text = pattern.sub(r"from . import \1 as \2", text)
    path.write_text(text, encoding="utf-8")
PY

"$PYTHON" -m compileall -q "$PROTO_OUT"
echo "==> Proto sync complete"
