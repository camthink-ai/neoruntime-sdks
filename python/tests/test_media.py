"""
Tests for Frame, PixelFormat
"""

import pytest
import numpy as np
import tempfile
import os
import json
from unittest.mock import Mock, patch

from hailo_ipc_sdk import Frame, PixelFormat


class TestFrame:
    def test_creation(self):
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        frame = Frame(
            sequence=1,
            timestamp_ns=1000000,
            width=100,
            height=100,
            format="RGB",
            image=image
        )
        assert frame.sequence == 1
        assert frame.width == 100
        assert frame.height == 100
        assert frame.format == "RGB"
    
    def test_to_rgb_from_rgb(self):
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        frame = Frame(
            sequence=1,
            timestamp_ns=1000000,
            width=100,
            height=100,
            format="RGB",
            image=image
        )
        rgb = frame.to_rgb()
        assert rgb.shape == (100, 100, 3)
        np.testing.assert_array_equal(rgb, image)
    
    def test_to_rgb_from_gray8(self):
        image = np.ones((100, 100), dtype=np.uint8) * 128
        frame = Frame(
            sequence=1,
            timestamp_ns=1000000,
            width=100,
            height=100,
            format="GRAY8",
            image=image
        )
        rgb = frame.to_rgb()
        assert rgb.shape == (100, 100, 3)


class TestPixelFormat:
    def test_values(self):
        assert PixelFormat.NV12.value == 0
        assert PixelFormat.RGB.value == 2
        assert PixelFormat.BGR.value == 3


