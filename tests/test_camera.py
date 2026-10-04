"""Tests for camera samplers."""

import numpy as np
import pytest
from roastbot.camera.sampler import MockCameraSampler


def test_mock_camera_frame_shape():
    cam = MockCameraSampler(width=320, height=240)
    frame = cam.capture_frame()
    assert frame is not None
    assert frame.shape == (240, 320, 3)
    assert frame.dtype == np.uint8
    assert cam.is_available() is True


def test_mock_camera_scenarios():
    cam = MockCameraSampler(width=320, height=240)
    for scenario in MockCameraSampler.SCENARIOS:
        cam.set_scenario(scenario)
        frame = cam.capture_frame()
        assert frame is not None
        assert frame.shape == (240, 320, 3)

    with pytest.raises(ValueError):
        cam.set_scenario("non_existent_scenario")


def test_mock_camera_release():
    cam = MockCameraSampler()
    assert cam.is_available() is True
    cam.release()
    assert cam.is_available() is False
    assert cam.capture_frame() is None
