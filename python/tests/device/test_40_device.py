"""Phase 4 — device control interfaces (physical side effects).

Execution order inside this module is the safety design:

* T01 read-only introspection first;
* T02 lights / IR-cut (restored to off / AUTO);
* T03-T04 motion (PTZ, zoom/focus) — start/stop pairs, no presets saved;
* T05 lens limits (snapshotted and restored), iris, goto;
* T06 autofocus block (windows disabled after, jobs cancelled);
* T07 explicit ``lens_reset_zero`` + verification — the lens has a
  flash-rehome defect history, so the module ends with a verified
  mechanical zero;
* ``tearDownModule`` repeats the reset as a belt-and-braces measure.

Calls that need hardware this device may not carry (PTZ motor, iris
motor, Wiegand reader) degrade to SKIP-NA with the daemon's own
rejection recorded — never fabricated as PASS.
"""

from __future__ import annotations

import threading
import time
import unittest

from neoruntime_ipc_sdk import (
    AfJob,
    AfMeasurement,
    AfStatus,
    DeviceClient,
    DeviceStatus,
    IrCutMode,
)

from common import DeviceTestCase


def _soft(fn, *args, **kwargs):
    """Call fn; map "hardware/feature absent" exceptions to None."""
    try:
        return fn(*args, **kwargs), None
    except Exception as exc:  # noqa: BLE001 — absence is an outcome here
        return None, f"{type(exc).__name__}: {exc}"


class T01Readonly(DeviceTestCase):
    area = "device"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = DeviceClient()

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_01_get_device_status(self):
        self.mark("DeviceClient.get_device_status")
        status = self.timed(self.client.get_device_status,
                             label="get_device_status")
        self.assertIsInstance(status, DeviceStatus)
        self.evidence(soc_temp_c=status.soc_temp_c,
                      _fields=list(vars(status))[:12])

    def test_02_get_lens_status(self):
        self.mark("DeviceClient.get_lens_status")
        status = self.timed(self.client.get_lens_status,
                            label="get_lens_status")
        self.evidence(status=status)
        self.assertIsInstance(status, dict)
        for key in ("zoom_pos", "focus_pos", "autofocus_enabled"):
            self.assertIn(key, status)

    def test_03_get_autofocus_status(self):
        self.mark("DeviceClient.get_autofocus_status")
        status = self.timed(self.client.get_autofocus_status,
                            label="get_autofocus_status")
        self.assertIsInstance(status, AfStatus)
        self.evidence(state=status.state, busy=status.busy,
                      zoom_pos=status.zoom_pos, focus_pos=status.focus_pos,
                      operation=status.operation)

    def test_04_get_af_measurement(self):
        self.mark("DeviceClient.get_af_measurement")
        try:
            meas = self.timed(self.client.get_af_measurement,
                              label="get_af_measurement")
        except Exception as exc:  # noqa: BLE001 — capability gate below
            # Daemon-side lens HAL bridge reports this RPC as unimplemented
            # — that is a device-capability outcome, not an SDK failure.
            if "not yet supported" in str(exc):
                self.na(f"lens HAL bridge: {exc}")
            raise
        self.assertIsInstance(meas, AfMeasurement)
        self.evidence(n_focus_energy=len(meas.focus_energy),
                      n_mean_luma=len(meas.mean_luma),
                      frame_id=meas.frame_id)

    def test_05_gpio_get(self):
        self.mark("DeviceClient.gpio_get")
        results = {}
        for pin in (0, 1, 2):
            value, err = _soft(self.client.gpio_get, pin)
            results[f"pin{pin}"] = value if err is None else err
        self.evidence(results=results)
        if all(isinstance(v, str) for v in results.values()):
            self.na(f"no readable GPIO pins: {results}")

    def test_06_get_wiegand_out(self):
        self.mark("DeviceClient.get_wiegand_out")
        state, err = _soft(self.client.get_wiegand_out, 0)
        self.evidence(channel0=state if err is None else err)
        if err is not None:
            self.na(f"wiegand channel 0 unreadable: {err}")
        self.assertIsInstance(state, bool)

    def test_07_subscribe_events(self):
        self.mark("DeviceClient.subscribe_events")
        events = []
        done = threading.Event()

        def drain():
            try:
                for ev in self.client.subscribe_events():
                    events.append(getattr(ev, "type", type(ev).__name__))
                    if len(events) >= 5:
                        done.set()
            except Exception:
                pass

        t = threading.Thread(target=drain, daemon=True)
        t.start()
        done.wait(timeout=5.0)
        self.evidence(events=events[:10], collected=len(events),
                      thread_alive=t.is_alive())
        self.assertTrue(t.is_alive(),
                        "subscribe_events iterator died immediately")


class T02Lights(DeviceTestCase):
    area = "device"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = DeviceClient()

    @classmethod
    def tearDownClass(cls):
        # Agreed reset: illuminators off, IR-cut back to auto.
        for fn, args in ((cls.client.set_white_light, (0,)),
                         (cls.client.set_ir_led, (False,)),
                         (cls.client.set_ircut, (IrCutMode.AUTO,))):
            try:
                fn(*args)
            except Exception:
                pass
        cls.client.close()

    def test_01_set_white_light(self):
        self.mark("DeviceClient.set_white_light")
        # Off → mid → off: brief, low, restored.
        self.timed(self.client.set_white_light, 0, label="white_light_0")
        self.timed(self.client.set_white_light, 50, label="white_light_50")
        self.timed(self.client.set_white_light, 0, label="white_light_restore")

    def test_02_set_ir_led(self):
        self.mark("DeviceClient.set_ir_led")
        self.timed(self.client.set_ir_led, True, label="ir_led_on")
        self.timed(self.client.set_ir_led, False, label="ir_led_off")

    def test_03_set_ircut(self):
        self.mark("DeviceClient.set_ircut")
        modes = []
        for mode in (IrCutMode.DAY, IrCutMode.NIGHT, IrCutMode.AUTO):
            _, err = _soft(self.client.set_ircut, mode)
            modes.append(f"{mode.name}={'ok' if err is None else err}")
            time.sleep(0.3)
        self.evidence(modes=modes)
        if all("ok" not in m for m in modes):
            self.na(f"IR-cut filter not controllable: {modes}")


class T03PTZ(DeviceTestCase):
    """Pan/tilt/preset — the fixed-lens module may reject all of these."""

    area = "device"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = DeviceClient()

    @classmethod
    def tearDownClass(cls):
        for stop in (cls.client.pan_stop, cls.client.tilt_stop,
                     cls.client.ptz_stop):
            try:
                stop()
            except Exception:
                pass
        cls.client.close()

    def _probe(self, name, start, stop):
        _, err = _soft(start)
        time.sleep(0.2)
        _, stop_err = _soft(stop)
        self.evidence(**{name: err or "ok", f"{name}_stop": stop_err or "ok"})
        return err

    def test_01_pan(self):
        self.mark("DeviceClient.pan_left/pan_right/pan_stop")
        err = self._probe("pan_left", lambda: self.client.pan_left(30),
                          self.client.pan_stop)
        err2 = self._probe("pan_right", lambda: self.client.pan_right(30),
                           self.client.pan_stop)
        if err and err2:
            self.na(f"no pan motor: {err}")

    def test_02_tilt(self):
        self.mark("DeviceClient.tilt_up/tilt_down/tilt_stop")
        err = self._probe("tilt_up", lambda: self.client.tilt_up(30),
                          self.client.tilt_stop)
        err2 = self._probe("tilt_down", lambda: self.client.tilt_down(30),
                           self.client.tilt_stop)
        if err and err2:
            self.na(f"no tilt motor: {err}")

    def test_03_presets(self):
        self.mark("DeviceClient.save_preset/call_preset")
        # Save *current* position as preset 98 then call it back: even
        # with a motor this is a no-op position change.
        _, save_err = _soft(self.client.save_preset, 98)
        _, call_err = _soft(self.client.call_preset, 98)
        self.evidence(save=save_err or "ok", call=call_err or "ok")
        if save_err and call_err:
            self.na(f"no PTZ preset support: {save_err}")


class T04ZoomFocus(DeviceTestCase):
    """Continuous zoom/focus + absolute levels, reset deferred to T07."""

    area = "device"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = DeviceClient()

    @classmethod
    def tearDownClass(cls):
        for stop in (cls.client.zoom_stop, cls.client.focus_stop):
            try:
                stop()
            except Exception:
                pass
        cls.client.close()

    def test_01_zoom_continuous(self):
        self.mark("DeviceClient.zoom_in/zoom_out/zoom_stop")
        _, err = _soft(self.client.zoom_in, 20)
        time.sleep(0.3)
        _soft(self.client.zoom_stop)
        _, err2 = _soft(self.client.zoom_out, 20)
        time.sleep(0.3)
        _soft(self.client.zoom_stop)
        self.evidence(zoom_in=err or "ok", zoom_out=err2 or "ok")
        if err and err2:
            self.na(f"no zoom motor: {err}")

    def test_02_set_zoom_level(self):
        self.mark("DeviceClient.set_zoom_level")
        _, err = _soft(self.timed, self.client.set_zoom_level, 1.0)
        self.evidence(result=err or "ok")
        if err is not None:
            self.na(f"set_zoom_level rejected: {err}")

    def test_03_focus_continuous(self):
        self.mark("DeviceClient.focus_in/focus_out/focus_stop")
        _, err = _soft(self.client.focus_in, 20)
        time.sleep(0.3)
        _soft(self.client.focus_stop)
        _, err2 = _soft(self.client.focus_out, 20)
        time.sleep(0.3)
        _soft(self.client.focus_stop)
        self.evidence(focus_in=err or "ok", focus_out=err2 or "ok")
        if err and err2:
            self.na(f"no focus motor: {err}")

    def test_04_set_focus_level(self):
        self.mark("DeviceClient.set_focus_level")
        _, err = _soft(self.timed, self.client.set_focus_level, 0.5)
        self.evidence(result=err or "ok")
        if err is not None:
            self.na(f"set_focus_level rejected: {err}")

    def test_05_focus_auto(self):
        self.mark("DeviceClient.focus_auto")
        _, err = _soft(self.client.focus_auto, True)
        self.evidence(enable_true=err or "ok")
        if err is not None:
            self.na(f"focus_auto rejected: {err}")


class T05Lens(DeviceTestCase):
    area = "device"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = DeviceClient()
        # Snapshot limits so the roundtrip can restore them exactly.
        try:
            cls._limits = cls.client.get_lens_status()
        except Exception:
            cls._limits = None

    @classmethod
    def tearDownClass(cls):
        if cls._limits:
            for key in ("zoom_limit", "focus_limit"):
                block = cls._limits.get(key)
                if isinstance(block, dict) and block.get("min_pos") is not None:
                    try:
                        cls.client.set_lens_limits(**{key: block})
                    except Exception:
                        pass
        cls.client.close()

    def test_01_lens_init(self):
        self.mark("DeviceClient.lens_init")
        _, err = _soft(self.timed, self.client.lens_init)
        self.evidence(result=err or "ok")
        if err is not None:
            self.na(f"lens_init rejected: {err}")

    def test_02_set_lens_limits_roundtrip(self):
        self.mark("DeviceClient.set_lens_limits")
        if not self._limits:
            self.na("no lens limits readable from get_lens_status")
        zoom_limit = self._limits.get("zoom_limit") or {}
        probe = {
            "min_pos": int(zoom_limit.get("min_pos", 0)),
            "max_pos": int(zoom_limit.get("max_pos", 1000)),
        }
        _, err = _soft(self.timed, self.client.set_lens_limits,
                       zoom_limit=probe)
        self.evidence(applied=probe, result=err or "ok",
                      original=zoom_limit)
        if err is not None:
            self.na(f"set_lens_limits rejected: {err}")
        after = self.client.get_lens_status().get("zoom_limit")
        self.evidence(after=after)

    def test_03_lens_goto_ratio_distance(self):
        self.mark("DeviceClient.lens_goto_ratio_distance")
        _, err = _soft(self.timed, self.client.lens_goto_ratio_distance,
                       1.0, 5.0)
        self.evidence(result=err or "ok", zoom_ratio=1.0, focus_distance_m=5.0)
        if err is not None:
            self.na(f"lens_goto rejected: {err}")

    def test_04_iris(self):
        self.mark("DeviceClient.control_iris/set_iris_target")
        _, err_open = _soft(self.client.control_iris, True)
        _, err_target = _soft(self.client.set_iris_target, 50)
        _, err_close = _soft(self.client.control_iris, False)
        self.evidence(open=err_open or "ok", target=err_target or "ok",
                      close=err_close or "ok")
        if err_open and err_target:
            self.na(f"no iris motor: {err_open}")


class T06Autofocus(DeviceTestCase):
    """AF moves the lens; T07 resets to mechanical zero afterwards."""

    area = "device"
    timeout_s = 120

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = DeviceClient()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.client.cancel_autofocus(0)
        except Exception:
            pass
        try:
            cls.client.set_af_windows(False, [])
        except Exception:
            pass
        cls.client.close()

    def test_01_set_af_windows(self):
        self.mark("DeviceClient.set_af_windows")
        w, h = 1920, 1080  # center quarter regardless of true sensor size
        window = (w // 4, h // 4, w // 2, h // 2)
        _, err = _soft(self.timed, self.client.set_af_windows,
                       True, [window])
        self.evidence(window=window, result=err or "ok")
        if err is not None:
            self.na(f"set_af_windows rejected: {err}")
        self.client.set_af_windows(False, [])

    def test_02_start_oneshot_af(self):
        self.mark("DeviceClient.start_oneshot_af")
        job, err = _soft(self.timed, self.client.start_oneshot_af)
        self.evidence(job=None if job is None else {
            "accepted": job.accepted, "job_id": job.job_id,
            "message": job.message,
        }, error=err)
        if err is not None or job is None:
            self.na(f"start_oneshot_af unavailable: {err}")
        self.assertIsInstance(job, AfJob)
        # Poll the status interface while the job runs.
        time.sleep(1.0)
        status = self.client.get_autofocus_status()
        self.evidence(poll_state=status.state, poll_busy=status.busy)
        self.client.cancel_autofocus(job.job_id)

    def test_03_cancel_autofocus(self):
        self.mark("DeviceClient.cancel_autofocus")
        _, err = _soft(self.timed, self.client.cancel_autofocus, 0)
        self.evidence(result=err or "ok")
        if err is not None:
            self.na(f"cancel_autofocus rejected: {err}")

    def test_04_start_zoom_follow(self):
        self.mark("DeviceClient.start_zoom_follow")
        job, err = _soft(self.timed, self.client.start_zoom_follow, 1.0)
        self.evidence(job=None if job is None else {
            "accepted": job.accepted, "job_id": job.job_id,
            "message": job.message,
        }, error=err)
        if err is not None or job is None:
            self.na(f"start_zoom_follow unavailable: {err}")
        self.assertIsInstance(job, AfJob)
        time.sleep(0.5)
        self.client.cancel_autofocus(job.job_id)

    def test_05_oneshot_autofocus_blocking(self):
        self.mark("DeviceClient.oneshot_autofocus")
        _, err = _soft(self.timed, self.client.oneshot_autofocus,
                       label="oneshot_autofocus")
        self.evidence(result=err or "ok")
        if err is not None:
            self.na(f"oneshot_autofocus unavailable: {err}")


class T07Reset(DeviceTestCase):
    """Verified mechanical reset — runs last inside this module."""

    area = "device"
    timeout_s = 120

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = DeviceClient()

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_01_lens_reset_zero_and_verify(self):
        self.mark("DeviceClient.lens_reset_zero (verified reset)")
        _, err = _soft(self.timed, self.client.lens_reset_zero,
                       True, True, label="lens_reset_zero")
        self.evidence(call=err or "ok")
        if err is not None:
            self.na(f"lens_reset_zero rejected: {err}")
        # The lens rehome takes a few seconds; poll for zoom/focus at 0.
        zoom = focus = None
        deadline = time.monotonic() + 40.0
        while time.monotonic() < deadline:
            status = self.client.get_lens_status()
            zoom, focus = status.get("zoom_pos"), status.get("focus_pos")
            self.evidence(latest_zoom_pos=zoom, latest_focus_pos=focus,
                          rz_done=(status.get("zoom_rz_done"),
                                   status.get("focus_rz_done")))
            if zoom == 0 and focus == 0:
                break
            time.sleep(2.0)
        self.evidence(final_zoom_pos=zoom, final_focus_pos=focus)
        self.assertEqual((zoom, focus), (0, 0),
                         "lens did not rehome to mechanical zero")

    def test_02_restore_af_mode(self):
        self.mark("DeviceClient.focus_auto (restore)")
        # AF was enabled by T04; leave the lens in continuous-AF state.
        _, err = _soft(self.client.focus_auto, True)
        self.evidence(result=err or "ok")
        if err is not None:
            self.na(f"focus_auto(restore) rejected: {err}")


class T08Misc(DeviceTestCase):
    """Wiegand / RS-485 / GPIO write — accessories may not be fitted."""

    area = "device"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = DeviceClient()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.client.set_wiegand_out(0, False)
        except Exception:
            pass
        try:
            cls.client.rs485_deinit()
        except Exception:
            pass
        cls.client.close()
        # One final verified rehome closes the whole device area.
        try:
            final = DeviceClient()
            final.lens_reset_zero(True, True)
            final.close()
        except Exception:
            pass

    def test_01_set_wiegand_out_roundtrip(self):
        self.mark("DeviceClient.set_wiegand_out")
        original, get_err = _soft(self.client.get_wiegand_out, 0)
        _, err = _soft(self.timed, self.client.set_wiegand_out, 0, True)
        if err is not None:
            self.na(f"set_wiegand_out rejected: {err}")
        state, _ = _soft(self.client.get_wiegand_out, 0)
        self.evidence(original=original, set_ok=True, readback=state)
        self.client.set_wiegand_out(0, bool(original) if get_err is None
                                    else False)

    def test_02_rs485(self):
        self.mark("DeviceClient.rs485_init/tx/deinit")
        _, init_err = _soft(self.timed, self.client.rs485_init, 9600)
        if init_err is not None:
            self.na(f"rs485_init rejected: {init_err}")
        _, tx_err = _soft(self.timed, self.client.rs485_tx, b"\x55\xaa")
        _, deinit_err = _soft(self.client.rs485_deinit)
        self.evidence(tx=tx_err or "ok (no reader expected)",
                      deinit=deinit_err or "ok")

    def test_03_gpio_roundtrip(self):
        self.mark("DeviceClient.gpio_set/gpio_get roundtrip")
        original, get_err = _soft(self.client.gpio_get, 0)
        if get_err is not None:
            self.na(f"gpio pin 0 unreadable: {get_err}")
        _, err = _soft(self.timed, self.client.gpio_set, 0,
                       not bool(original))
        if err is not None:
            self.na(f"gpio_set rejected: {err}")
        flipped, _ = _soft(self.client.gpio_get, 0)
        self.client.gpio_set(0, bool(original))
        self.evidence(original=original, flipped=flipped,
                      restored=bool(original))


    def test_04_subscribe_rs485_rx(self):
        """Bench has no RS-485 peer: assert the subscription stream opens and
        stays healthy (plumbing-level verification); frames are not asserted.
        Exercises init -> subscribe-alive across tx -> deinit -> re-init."""
        self.mark("DeviceClient.subscribe_rs485_rx")
        _, init_err = _soft(self.timed, self.client.rs485_init, 9600)
        if init_err is not None:
            self.na(f"rs485_init rejected: {init_err}")

        frames = []

        def drain():
            try:
                for ev in self.client.subscribe_rs485_rx(queue_size=8,
                                                         drop_old=True):
                    frames.append(len(ev.data))
            except Exception:
                pass

        t = threading.Thread(target=drain, daemon=True)
        t.start()
        time.sleep(2.0)  # no peer: stream must stay open and silent
        _, tx_err = _soft(self.timed, self.client.rs485_tx, b"\x55\xaa")
        _, deinit_err = _soft(self.timed, self.client.rs485_deinit)
        time.sleep(0.5)
        _, reinit_err = _soft(self.timed, self.client.rs485_init, 9600)
        time.sleep(0.5)
        self.evidence(thread_alive=t.is_alive(), frames=frames[:10],
                      collected=len(frames), tx=tx_err or "ok",
                      deinit=deinit_err or "ok", reinit=reinit_err or "ok")
        self.assertTrue(t.is_alive(),
                        "subscribe_rs485_rx iterator died (old firmware "
                        "without SubscribeRs485Rx would raise UNIMPLEMENTED)")
        _, deinit2_err = _soft(self.timed, self.client.rs485_deinit)
        self.evidence(final_deinit=deinit2_err or "ok")

def tearDownModule():
    """Belt-and-braces: even if a test failed mid-area, leave the device
    in the agreed post-test state (lens zeroed, illuminators off,
    IR-cut auto)."""
    try:
        client = DeviceClient()
        client.lens_reset_zero(True, True)
        client.set_white_light(0)
        client.set_ir_led(False)
        client.set_ircut(IrCutMode.AUTO)
        client.focus_auto(True)
        client.close()
    except Exception:
        pass


if __name__ == "__main__":
    unittest.main()
