#!/bin/bash
#
# 设备端 SDK 接口测试编排:本地构建 wheel → 部署到目标设备 → 执行 → 取回报告
#
# 用法:
#   ./scripts/run-device-tests.sh <ssh-target> [ssh-port] [--perf]
#   例: ./scripts/run-device-tests.sh root@<目标设备IP>
#       SSHPASS=root ./scripts/run-device-tests.sh root@<备用设备IP>      # 公钥不通的设备
#       SSHPASS=root PERF_SOAK_S=600 ./scripts/run-device-tests.sh root@<备用设备IP> 22 --perf
#
# --perf: 跑性能套件 test_60..64(推理/媒体与加速层/事件/设备面/长稳),
#   产出 dist/device-perf-report.json(与功能套件的 device-report.json 分开);
#   PERF_SAMPLE_N / PERF_SAMPLE_ROUNDS / PERF_STREAM_S / PERF_SOAK_S 透传
#   到设备,用于校准跑(小样本短 soak)。
#
# SSHPASS: 非空时经 sshpass -e 认证(去掉 BatchMode),覆盖 rsync 与 ssh。
#
# 设备侧约定(与测试骨架一致):
#   /data/venv-sdk      设备 venv(备用设备无此目录时需先从主设备中继同路径;
#                       python3.10 同款,见 perf 部署预案)
#   /data/aipc-data/models/yolo_world_v2s.hef   perf 模式的主被测模型(缺失则推理/soak NA)
#   /data/sdk-test/     测试代码与报告落点
#   /data/sdk-test/tmp  测试写文件的唯一目录
#
# 回滚预案(测试后恢复设备 venv):
#   ssh <target> '/data/venv-sdk/bin/pip install --no-deps neoruntime-ipc-sdk==0.6.0'
#
# 退出码: 0 = 全部通过(含 NA/KNOWN-ISSUE);1 = 存在 FAIL/ERROR 或流程失败

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SDK_DIR="$PROJECT_ROOT/python"
DEVICE_TESTS_DIR="$SDK_DIR/tests/device"
OUTPUT_DIR="$PROJECT_ROOT/dist"

TARGET="${1:-}"
PORT="${2:-22}"
MODE=functional
for arg in "${@:3}"; do
    case "$arg" in
        --perf) MODE=perf ;;
        *) echo "未知参数: $arg(仅支持 --perf)" >&2; exit 1 ;;
    esac
done

if [ -z "$TARGET" ]; then
    echo "用法: $0 <ssh-target> [ssh-port] [--perf]   例: $0 root@<目标设备IP>" >&2
    exit 1
fi

# SSHPASS 非空且本机有 sshpass → 密码认证(备用设备公钥不通);
# 否则保持 BatchMode(主设备等已布公钥的设备)。
if [ -n "${SSHPASS:-}" ]; then
    if ! command -v sshpass >/dev/null 2>&1; then
        echo "错误: SSHPASS 已设置但本机缺少 sshpass" >&2
        exit 1
    fi
    SSH_OPTS=(-p "$PORT" -o ConnectTimeout=8)
    SSH=(sshpass -e ssh "${SSH_OPTS[@]}" "$TARGET")
    RSYNC_SSH="sshpass -e ssh -p $PORT -o ConnectTimeout=8"
else
    SSH_OPTS=(-p "$PORT" -o BatchMode=yes -o ConnectTimeout=8)
    SSH=(ssh "${SSH_OPTS[@]}" "$TARGET")
    RSYNC_SSH="ssh -p $PORT -o BatchMode=yes -o ConnectTimeout=8"
fi
RSYNC=(rsync -e "$RSYNC_SSH")
# 部分新刷 OS 镜像设备端没有 rsync;探测一次,缺失则部署/取回走 tar-over-ssh
# (语义等价:push 前清旧测试目录,拉取只取 report-test_*.json)
DEV_HAS_RSYNC="$("${SSH[@]}" 'command -v rsync 2>/dev/null || true')"
push_tree() { # $1=本地目录(尾斜杠) $2=target:远端目录
    if [ -n "$DEV_HAS_RSYNC" ]; then
        "${RSYNC[@]}" -a --delete "$1" "$2"
    else
        local remote="${2#*:}"
        "${SSH[@]}" "rm -rf '$remote'/* && mkdir -p '$remote'" >/dev/null
        ( cd "$1" && tar czf - . ) | "${SSH[@]}" "tar xzf - -C '$remote'"
    fi
}
pull_reports() { # $1=target:远端glob $2=本地目录
    if [ -n "$DEV_HAS_RSYNC" ]; then
        "${RSYNC[@]}" -a "$1" "$2"
    else
        "${SSH[@]}" "cd $DEVICE_BASE && tar czf - report-test_*.json" \
            | tar xzf - -C "$2"
    fi
}
DEVICE_BASE=/data/sdk-test
DEVICE_VENV=/data/venv-sdk

echo "== [1/5] 构建 SDK wheel(纯 Python,设备可用)=="
mkdir -p "$OUTPUT_DIR"
( cd "$SDK_DIR" && python3 -m build --wheel --outdir "$OUTPUT_DIR" --skip-dependency-check >/dev/null )
WHEEL="$(ls -t "$OUTPUT_DIR"/neoruntime_ipc_sdk-*.whl | head -1)"
WHEEL_VERSION="$(basename "$WHEEL" | sed -E 's/^neoruntime_ipc_sdk-([^-]+)-.*/\1/')"
echo "   wheel: $(basename "$WHEEL")"

echo "== [2/5] 部署测试代码 + wheel 到设备 =="
if ! "${SSH[@]}" "mkdir -p $DEVICE_BASE/tmp"; then
    echo "错误: SSH 连接失败(公钥设备省略 SSHPASS;备用设备需 SSHPASS=root)" >&2
    exit 1
fi
if [ "$MODE" = perf ] && ! "${SSH[@]}" "test -f /data/aipc-data/models/yolo_world_v2s.hef"; then
    echo "警告: 设备缺 /data/aipc-data/models/yolo_world_v2s.hef — 推理/soak 模块将 NA(部署预案:从主设备拷贝精选 HEF)" >&2
fi
push_tree "$DEVICE_TESTS_DIR"/ "$TARGET:$DEVICE_BASE/"
if [ -n "$DEV_HAS_RSYNC" ]; then
    "${RSYNC[@]}" -a "$WHEEL" "$TARGET:$DEVICE_BASE/"
else
    "${SSH[@]}" "cat > $DEVICE_BASE/$(basename "$WHEEL")" < "$WHEEL"
fi

if ! "${SSH[@]}" "test -x $DEVICE_VENV/bin/python"; then
    echo "错误: 设备缺 $DEVICE_VENV — 备用设备需先从主设备中继整个 venv 到同路径" >&2
    exit 1
fi

echo "== [3/5] 设备 venv 安装被测版本并校验 =="
"${SSH[@]}" "$DEVICE_VENV/bin/pip install --quiet --no-deps --force-reinstall \
    $DEVICE_BASE/$(basename "$WHEEL")"
DEVICE_VERSION="$("${SSH[@]}" "$DEVICE_VENV/bin/python -c 'import neoruntime_ipc_sdk as s; print(s.__version__)'")"
if [ "$DEVICE_VERSION" != "$WHEEL_VERSION" ]; then
    echo "错误: 设备侧 SDK 版本校验失败 (期望 $WHEEL_VERSION, 实际 $DEVICE_VERSION)" >&2
    exit 1
fi
echo "   设备 SDK 版本: $DEVICE_VERSION"

echo "== [4/5] 逐模块执行(每模块独立看门狗 + 独立报告)=="
# Architecture proven necessary on 2026-09-08: a wedged interface call
# (subscribe against a silent stream) parks the main thread in a lock
# acquire, and the in-process repeating-itimer alarm is process-directed
# — with ~15 grpc/asyncio threads alive the ticks land on other threads
# and the Python-level timeout never fires. So each module runs as its
# OWN process under `timeout -k 30 <budget>`; a wedge loses only that
# module's report, and the runner's per-test incremental flush still
# yields a partial report for the killed module. rc 124/137 (watchdog)
# or a crash is recorded and the loop CONTINUES.
if [ "$MODE" = perf ]; then
    MODULES=(test_60_perf_inference 1800
             test_61_perf_media_accel 900
             test_62_perf_events 600
             test_63_perf_device 600
             test_64_perf_soak 2400
             test_65_perf_overlay 900
             test_66_perf_injection 1800
             test_67_perf_events_hub 1500)
    REPORT_JSON=device-perf-report.json
else
    MODULES=(test_10_env_survey 300
             test_20_inference 1200
             test_21_inference_genai 600
             test_30_media 1200
             test_31_events 900
             test_40_device 1500
             test_41_camera 2400
             test_42_dsp 1200
             test_43_audio 900
             test_44_overlay 900
             test_45_app 900
             test_46_plugin 900
             test_50_toolkit 900
             test_51_recording_web 1500)
    REPORT_JSON=device-report.json
fi

# 校准参数透传:设置了的 PERF_* 才进设备命令(未设置的不覆盖默认)。
PERF_ENV=()
for v in PERF_SAMPLE_N PERF_SAMPLE_ROUNDS PERF_STREAM_S PERF_SOAK_S; do
    val="${!v:-}"
    [ -n "$val" ] && PERF_ENV+=("$v=$val")
done
PERF_ENV_STR="${PERF_ENV[*]-}"

TIMEOUT_BIN="$("${SSH[@]}" 'command -v timeout 2>/dev/null || true')"

# Drop stale per-module reports so a merge can never mix two runs.
"${SSH[@]}" "rm -f $DEVICE_BASE/report-test_*.json"

AGG_RC=0
for ((i = 0; i < ${#MODULES[@]}; i += 2)); do
    MOD="${MODULES[$i]}"
    BUDGET="${MODULES[$((i + 1))]}"
    echo "-- 模块 $MOD (预算 ${BUDGET}s)"
    MOD_RC=0
    MOD_CMD="env NEORUNTIME_DEVICE=1 $PERF_ENV_STR $DEVICE_VENV/bin/python \
$DEVICE_BASE/run_device_tests.py $DEVICE_BASE/report-$MOD.json $MOD"
    if [ -n "$TIMEOUT_BIN" ]; then
        MOD_CMD="$TIMEOUT_BIN -k 30 $BUDGET $MOD_CMD"
    fi
    "${SSH[@]}" "$MOD_CMD" || MOD_RC=$?
    if [ "$MOD_RC" -eq 124 ] || [ "$MOD_RC" -eq 137 ]; then
        echo "   模块 $MOD: 看门狗超时 (rc=$MOD_RC) — 取部分报告,继续后续模块"
    elif [ "$MOD_RC" -ne 0 ] && [ "$MOD_RC" -ne 1 ]; then
        echo "   模块 $MOD: 异常退出 rc=$MOD_RC — 继续后续模块"
    fi
    [ "$MOD_RC" -ne 0 ] && AGG_RC=1
done

echo "== [5/5] 取回报告并合并 =="
# 本地暂存必须先清:否则上一次(可能是另一台设备/另一模式)取回的
# report-test_*.json 会被 merge glob 一起吞进本次报告。
mkdir -p "$OUTPUT_DIR/device-reports"
rm -f "$OUTPUT_DIR"/device-reports/report-test_*.json
pull_reports "$TARGET:$DEVICE_BASE/report-test_*.json" "$OUTPUT_DIR/device-reports/"
MERGE_RC=0
python3 - "$OUTPUT_DIR/device-reports" "$OUTPUT_DIR/$REPORT_JSON" <<'EOF' || MERGE_RC=$?
import glob
import json
import os
import sys

parts_dir, out_path = sys.argv[1], sys.argv[2]
files = sorted(glob.glob(os.path.join(parts_dir, "report-test_*.json")))
if not files:
    sys.exit("no per-module reports retrieved")

cases, env, wall, missing = [], None, 0.0, []
for path in files:
    with open(path) as fh:
        part = json.load(fh)
    env = env or part.get("env")
    wall += part.get("summary", {}).get("wall_time_s", 0.0)
    cases.extend(part.get("cases", []))
    name = os.path.basename(path)[len("report-"):-len(".json")]
    if not part.get("cases"):
        missing.append(name)

verdicts: dict[str, int] = {}
for row in cases:
    verdicts[row["verdict"]] = verdicts.get(row["verdict"], 0) + 1

report = {
    "schema": "neoruntime-device-test-report/1",
    "env": env,
    "summary": {
        "total": len(cases),
        "verdicts": verdicts,
        "wall_time_s": round(wall, 1),
        "modules": [os.path.basename(f) for f in files],
        "modules_without_cases": missing,
    },
    "cases": cases,
}
tmp = out_path + ".tmp"
with open(tmp, "w", encoding="utf-8") as fh:
    json.dump(report, fh, ensure_ascii=False, indent=1)
os.replace(tmp, out_path)
print(f"merged {len(files)} module reports -> {out_path}")
print("verdicts:", json.dumps(verdicts), "total:", len(cases),
      "wall_s:", round(wall, 1))
if missing:
    print("modules with zero recorded cases (watchdog-killed early?):",
          ", ".join(missing))
EOF
MERGE_RC=$?
echo "   本地报告: $OUTPUT_DIR/$REPORT_JSON"

if [ "$MERGE_RC" -ne 0 ]; then
    echo "错误: 报告合并失败" >&2
    exit "$MERGE_RC"
fi
if [ "$AGG_RC" -ne 0 ]; then
    echo "注意: 存在 FAIL/ERROR/超时模块(聚合退出码 $AGG_RC)— 详见报告 JSON"
fi
if [ "$MODE" = perf ]; then
    echo "生成性能报告: python3 scripts/gen_perf_report.py dist/$REPORT_JSON"
else
    echo "生成报告页: python3 scripts/gen_device_report.py dist/$REPORT_JSON"
fi
exit "$AGG_RC"
