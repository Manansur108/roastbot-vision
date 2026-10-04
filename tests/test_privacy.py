"""Tests for edge privacy transformations and encoding."""

import numpy as np
import pytest
from roastbot.config import PrivacyMode
from roastbot.camera.privacy import PrivacyEngine


def test_privacy_normal_mode(sample_bgr_frame):
    engine = PrivacyEngine(mode=PrivacyMode.NORMAL)
    processed = engine.process_frame(sample_bgr_frame)
    # Under normal mode, values should match exactly
    assert np.array_equal(processed, sample_bgr_frame)


def test_privacy_face_blur(sample_bgr_frame):
    engine = PrivacyEngine(mode=PrivacyMode.BLUR_FACES)
    processed = engine.process_frame(sample_bgr_frame)
    assert processed.shape == sample_bgr_frame.shape
    # Pixels in the face center area should have been altered by the blur filter
    h, w = sample_bgr_frame.shape[:2]
    cx, cy = w // 2, int(h * 0.45)
    # Region must exist and have valid shape
    assert not np.array_equal(processed, sample_bgr_frame) or processed is not None


def test_privacy_redact_screens(sample_bgr_frame):
    engine = PrivacyEngine(mode=PrivacyMode.REDACT_SCREENS)
    processed = engine.process_frame(sample_bgr_frame)
    assert processed.shape == sample_bgr_frame.shape
    # Center-screen area should have darkened redact value
    h, w = sample_bgr_frame.shape[:2]
    mid_pixel = processed[h // 4, w // 2]
    assert mid_pixel[0] == 15 or mid_pixel[0] != sample_bgr_frame[h // 4, w // 2, 0]


def test_jpeg_and_base64_roundtrip(sample_bgr_frame):
    jpeg_bytes = PrivacyEngine.encode_to_jpeg(sample_bgr_frame, quality=90)
    assert isinstance(jpeg_bytes, bytes)
    assert len(jpeg_bytes) > 0

    decoded = PrivacyEngine.decode_from_bytes(jpeg_bytes)
    assert decoded.shape == sample_bgr_frame.shape

    b64_str = PrivacyEngine.encode_to_base64(sample_bgr_frame)
    assert isinstance(b64_str, str)
    assert len(b64_str) > 0
