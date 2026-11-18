"""Phase 1 — environment survey (read-only).

Runs before everything else so a missing daemon or socket surfaces as a
visible FAIL row instead of a wall of connection errors in later areas.
Also pins the endpoint topology via Config, which every later client
relies on.
"""

from __future__ import annotations

import glob
import os
import unittest

import neoruntime_ipc_sdk

from common import DEVICE_TMP_DIR, MODEL_DIR, DeviceTestCase


class T01SdkIdentity(DeviceTestCase):
    area = "env"

    def test_01_version(self):
        self.mark("__version__")
        expected = os.environ.get("SDK_EXPECTED_VERSION")
        self.evidence(version=neoruntime_ipc_sdk.__version__,
                      expected=expected or "(unset)")
        if not expected:
            self.skipTest(
                "SDK_EXPECTED_VERSION not set — run via run-device-tests.sh, "
                "which pins it to the wheel version it installs")
        self.assertEqual(neoruntime_ipc_sdk.__version__, expected)

    def test_02_module_path(self):
        self.mark("package import")
        path = os.path.dirname(neoruntime_ipc_sdk.__file__)
        self.evidence(path=path)
        self.assertTrue(os.path.isdir(path))


class T02ConfigEndpoints(DeviceTestCase):
    """Config is the single source of endpoint truth — verify every getter."""

    area = "env"

    def test_01_endpoint_getters(self):
        from neoruntime_ipc_sdk import Config

        self.mark("Config.get_*_endpoint")
        getters = [
            "get_inference_endpoint",
            "get_event_bus_endpoint",
            "get_device_control_endpoint",
            "get_camera_control_endpoint",
            "get_app_manager_endpoint",
        ]
        found = {}
        for name in getters:
            value = getattr(Config, name)()
            found[name] = value
            self.assertIsInstance(value, str, f"{name} returned {value!r}")
            self.assertTrue(value, f"{name} empty")
        self.evidence(endpoints=found)

    def test_02_path_helpers(self):
        from neoruntime_ipc_sdk import Config

        self.mark("Config.get_host_prefix/translate_path_to_host")
        prefix = Config.get_host_prefix()
        translated = Config.translate_path_to_host("/app/data/x")
        shm = Config.get_shm_base_path()
        sock_dir = Config.get_encoded_socket_dir()
        self.evidence(
            host_prefix=prefix,
            translated=translated,
            shm_base=shm,
            encoded_socket_dir=sock_dir,
        )
        self.assertIsInstance(prefix, str)

    def test_03_app_id(self):
        from neoruntime_ipc_sdk import Config

        self.mark("Config.get_app_id")
        app_id = Config.get_app_id()
        self.evidence(app_id=app_id)
        self.assertIsInstance(app_id, str)


class T03DaemonsAndSockets(DeviceTestCase):
    area = "env"

    def test_01_required_sockets(self):
        self.mark("/run/aipc sockets")
        required = [
            "/run/aipc/ai-runtime.sock",
            "/run/aipc/event-bus.sock",
            "/run/aipc/camera-control.sock",
            "/run/aipc/device-control.sock",
        ]
        status = {s: os.path.exists(s) for s in required}
        extra = sorted(glob.glob("/run/aipc/**/*.sock", recursive=True))
        self.evidence(required=status, all_sockets=extra)
        missing = [s for s, ok in status.items() if not ok]
        self.assertFalse(missing, f"missing required sockets: {missing}")

    def test_02_model_inventory(self):
        self.mark("model inventory")
        if not os.path.isdir(MODEL_DIR):
            self.na(f"no model directory at {MODEL_DIR}")
        models = sorted(os.listdir(MODEL_DIR))
        self.evidence(models=models)
        self.assertTrue(any(m.endswith(".hef") for m in models),
                        f"no .hef models in {MODEL_DIR}: {models}")

    def test_03_scratch_dir(self):
        self.mark("scratch dir")
        os.makedirs(DEVICE_TMP_DIR, exist_ok=True)
        self.assertTrue(os.path.isdir(DEVICE_TMP_DIR))


if __name__ == "__main__":
    unittest.main()
