"""Phase 4 — DSP offload interfaces (DspClient).

The DSP path rides the fd-publisher UDS via camera-daemon; a probe
allocation in ``setUpClass`` gates the module — an unreachable service
records SKIP-NA rather than a wall of failures. Every op records
``client.last_used_hw`` so the report can attribute hardware-path vs
CPU-fallback per call, and CPU-fallback warnings are captured as
evidence instead of polluting the log.
"""

from __future__ import annotations

import os
import unittest
import warnings

import numpy as np

from neoruntime_ipc_sdk import DspClient, PendingDspJob

from common import DEVICE_TMP_DIR, DeviceTestCase

W, H = 64, 64


def _nv12(w: int, h: int) -> np.ndarray:
    """Deterministic synthetic NV12 frame: gradient Y, neutral UV."""
    y = np.frombuffer(
        bytes((x * 255) // max(w - 1, 1) for x in range(w)) * h, np.uint8
    ).reshape(h, w)
    uv = np.tile(np.array([128, 128], np.uint8), (h // 2, w // 2))
    return np.vstack([y, uv])


# A stacked (h*3//2, w) uint8 array is shape-identical to a gray8 frame
# (dsp.py: "NV12 array is indistinguishable from gray8 by shape alone"),
# so EVERY op call below passes fmt="nv12" explicitly — without it the
# SDK treats the 2-D array as gray8 and HAL rejects or misinterprets it.
FMT = "nv12"


class _DspArea(DeviceTestCase):
    area = "dsp"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = DspClient()
        try:  # liveness probe: one trivial buffer round-trip
            pool = cls.client.alloc_buffers(W, H, "nv12", 1)
            pool.release()
        except Exception as exc:  # noqa: BLE001
            raise unittest.SkipTest(
                f"DSP service unreachable via camera sock: "
                f"{type(exc).__name__}: {exc}"
            )

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def _run(self, fn, *args, **kwargs):
        """Call a *_hw op, timing it and capturing the fallback warning."""
        label = kwargs.pop("label", fn.__name__)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = self.timed(fn, *args, label=label, **kwargs)
        note = None
        for w in caught:
            if issubclass(w.category, UserWarning) and "fallback" in str(w.message):
                note = str(w.message)
        self.evidence(used_hw=self.client.last_used_hw, fallback_warning=note)
        return result


class T01Buffers(_DspArea):
    def test_01_alloc_write_read_release(self):
        self.mark("DspClient.alloc_buffers/DspBufferPool")
        pool = self.timed(self.client.alloc_buffers, W, H, "nv12", 2,
                          label="alloc_buffers")
        src = _nv12(W, H)
        pool.write(0, src)
        back = self.timed(pool.read, 0, label="pool_read")
        self.evidence(count=pool.count, ids=[pool.buffer_id(0),
                                             pool.buffer_id(1)],
                      strides=pool.strides, plane_sizes=pool.plane_sizes,
                      roundtrip_equal=bool(np.array_equal(src, back)))
        self.assertEqual(pool.count, 2)
        self.assertEqual(back.shape, (H * 3 // 2, W))
        self.assertTrue(np.array_equal(src, back),
                        "pool write->read lost data")
        pool.release()
        pool.release()  # idempotent by contract
        self.evidence(released_twice_ok=True)


class T02Resize(_DspArea):
    def test_01_resize_hw(self):
        self.mark("DspClient.resize_hw")
        out = self._run(self.client.resize_hw, _nv12(W, H), 32, 24,
                        fmt=FMT, label="resize_hw")
        self.evidence(out_shape=out.shape)
        self.assertEqual(out.shape, (24 * 3 // 2, 32))

    def test_02_resize_hw_async(self):
        self.mark("DspClient.resize_hw(wait=False)/PendingDspJob")
        job = self._run(self.client.resize_hw, _nv12(W, H), 16, 16,
                        fmt=FMT, wait=False, label="resize_hw_async")
        self.assertIsInstance(job, PendingDspJob)
        # buffer_id is a property fed by job._reads, which wait() and
        # wait_result() consume — it must be captured before any waiting
        # or it raises IndexError afterwards.
        buffer_id = job.buffer_id
        done = job.done(timeout_s=5.0)
        chained = job.wait_result(timeout_s=10.0)
        out = job.wait(timeout_s=10.0)
        self.evidence(done=done, chain_type=type(chained).__name__,
                      out_shape=out.shape, job_buffer_id=buffer_id)
        self.assertEqual(out.shape, (16 * 3 // 2, 16))
        job.release()


class T03Crop(_DspArea):
    def test_01_crop_hw(self):
        self.mark("DspClient.crop_hw")
        out = self._run(self.client.crop_hw, _nv12(W, H), 8, 8, 32, 32,
                        fmt=FMT, label="crop_hw")
        self.evidence(out_shape=out.shape)
        self.assertEqual(out.shape, (32 * 3 // 2, 32))

    def test_02_crop_hw_scaled(self):
        self.mark("DspClient.crop_hw (crop+scale)")
        out = self._run(self.client.crop_hw, _nv12(W, H), 8, 8, 32, 32,
                        16, 16, fmt=FMT, label="crop_hw_scaled")
        self.evidence(out_shape=out.shape)
        self.assertEqual(out.shape, (16 * 3 // 2, 16))


class T04MultiCrop(_DspArea):
    def test_01_multi_crop_hw(self):
        self.mark("DspClient.multi_crop_hw")
        rects = [(0, 0, 32, 32, 16, 16), (32, 0, 32, 32, 16, 16),
                 (0, 32, 32, 32, 32, 32)]
        outs = self._run(self.client.multi_crop_hw, _nv12(W, H), rects,
                         fmt=FMT, label="multi_crop_hw")
        self.evidence(n=len(outs), shapes=[list(o.shape) for o in outs])
        self.assertEqual(len(outs), 3)
        self.assertEqual(outs[0].shape, (16 * 3 // 2, 16))
        self.assertEqual(outs[2].shape, (32 * 3 // 2, 32))

    def test_02_multi_crop_hw_async(self):
        self.mark("DspClient.multi_crop_hw(wait=False)")
        rects = [(0, 0, 32, 32, 16, 16), (32, 32, 32, 32, 16, 16)]
        job = self._run(self.client.multi_crop_hw, _nv12(W, H), rects,
                        fmt=FMT, wait=False, label="multi_crop_async")
        outs = job.wait(timeout_s=10.0)
        self.evidence(n=len(outs), shapes=[list(o.shape) for o in outs])
        self.assertEqual(len(outs), 2)
        job.release()


class T05Convert(_DspArea):
    def test_01_convert_hw_nv12_to_rgb(self):
        self.mark("DspClient.convert_hw")
        out = self._run(self.client.convert_hw, _nv12(W, H), "rgb24",
                        fmt=FMT, label="convert_hw")
        self.evidence(out_shape=out.shape, dtype=str(out.dtype))
        self.assertEqual(out.shape, (H, W, 3))
        # Sanity: neutral UV chroma must map to (near-)equal RGB channels.
        self.assertLess(int(np.abs(
            out[:, :, 0].astype(int) - out[:, :, 2].astype(int)
        ).max()), 8, "neutral-chroma NV12 converted to wildly tinted RGB")


class T06Blend(_DspArea):
    def test_01_blend_hw(self):
        self.mark("DspClient.blend_hw")
        base = _nv12(W, H)
        snapshot = base.copy()
        rgba = np.zeros((8, 8, 4), np.uint8)
        rgba[:, :, 3] = 255  # opaque black: input is RGBA (alpha LAST) —
        # blend_hw packs the wire's ARGB32 order internally (dsp.py)
        out = self._run(self.client.blend_hw, base, [(rgba, 4, 4)],
                        fmt=FMT, label="blend_hw")
        self.evidence(out_shape=out.shape,
                      input_unmodified=bool(np.array_equal(base, snapshot)))
        self.assertEqual(out.shape, (H * 3 // 2, W))
        # The blend must not be a silent no-op: some pixel must differ.
        self.assertFalse(np.array_equal(out, snapshot),
                         "blend output identical to input — op was a no-op")


class T07EncodeJpeg(_DspArea):
    def test_01_encode_jpeg_hw(self):
        self.mark("DspClient.encode_jpeg_hw")
        jpeg = self._run(self.client.encode_jpeg_hw, _nv12(W, H), 80,
                         fmt=FMT, label="encode_jpeg_hw")
        path = os.path.join(DEVICE_TMP_DIR, "dsp_evidence.jpg")
        with open(path, "wb") as fh:
            fh.write(jpeg)
        self.evidence(bytes=len(jpeg), magic=jpeg[:2].hex(), saved=path)
        self.assertEqual(jpeg[:2], b"\xff\xd8", "not a JPEG (no SOI)")
        self.assertGreater(len(jpeg), 100)

    def test_02_encode_jpeg_hw_after_pipeline_reinit(self):
        """F5 regression: the standalone JPEG HW encoder must survive a
        rotation_full_reinit. set_transform(rotation±1) destructs and
        rebuilds medialib, which nulls the plugin's interactor slot; a
        re-created JPEG ctx then re-registers the standalone interactor
        and, on unfixed builds, trips the vendor registry uniqueness
        check ("ConfigManagerInteractor::create failed (1)") forever —
        only a daemon restart revived it. The 128x128 shot forces a ctx
        rebuild (the daemon caches per WxH:fmt:q) instead of riding the
        64x64 cache from test_01."""
        from neoruntime_ipc_sdk import CameraClient, TransformConfig

        self.mark("DspClient.encode_jpeg_hw after pipeline reinit")
        warm = self._run(self.client.encode_jpeg_hw, _nv12(W, H), 80,
                         fmt=FMT, label="encode_jpeg_hw_warm")
        self.assertEqual(warm[:2], b"\xff\xd8")

        camera = CameraClient()
        try:
            original = camera.get_transform()
            camera.set_transform(TransformConfig(
                rotation=(original.rotation + 1) % 4, flip=original.flip,
                dewarp=original.dewarp, grayscale=original.grayscale))
            camera.set_transform(original)
        finally:
            camera.close()
        self.evidence(restored_rotation=original.rotation)

        # Fresh client: the reinit restarted the fd publisher, so sockets
        # opened before it are dead (BrokenPipe on next exchange).
        fresh = DspClient()
        try:
            jpeg = self._run(fresh.encode_jpeg_hw, _nv12(128, 128), 80,
                             fmt=FMT, label="encode_jpeg_hw_after_reinit")
        finally:
            fresh.close()
        self.evidence(bytes=len(jpeg), magic=jpeg[:2].hex())
        self.assertEqual(jpeg[:2], b"\xff\xd8", "not a JPEG (no SOI)")
        self.assertGreater(len(jpeg), 100)


if __name__ == "__main__":
    unittest.main()
