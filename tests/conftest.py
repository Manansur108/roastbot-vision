"""Pytest fixtures for RoastBot-Vision tests."""

import pytest
import numpy as np

from roastbot.config import AppConfig, RoastSeverity, RoastCategory, PrivacyMode
from roastbot.camera.sampler import MockCameraSampler
from roastbot.camera.privacy import PrivacyEngine
from roastbot.providers.mock_provider import MockVisionProvider
from roastbot.mascot.state import MascotStateMachine
from roastbot.tts.mock_speech import MockSpeechEngine
from roastbot.engine.roaster import RoastEngine


@pytest.fixture
def sample_bgr_frame():
    """Create a 480x640 synthetic BGR test image."""
    frame = np.full((480, 640, 3), 100, dtype=np.uint8)
    # Add simple visual distinction
    frame[200:300, 250:350] = (200, 180, 160)
    return frame


@pytest.fixture
def mock_camera():
    return MockCameraSampler(width=320, height=240, initial_scenario="messy_desk")


@pytest.fixture
def mock_speech():
    return MockSpeechEngine(enabled=True)


@pytest.fixture
def mock_provider():
    return MockVisionProvider(seed=42)


@pytest.fixture
def test_config():
    return AppConfig(
        severity=RoastSeverity.SNARKY,
        category=RoastCategory.DESK_CLUTTER,
        privacy_mode=PrivacyMode.BLUR_FACES,
        use_mock_camera=True,
        speech_enabled=True,
    )


@pytest.fixture
def test_engine(test_config, mock_camera, mock_speech, mock_provider):
    mascot = MascotStateMachine(idle_timeout_seconds=1.0)
    privacy = PrivacyEngine(mode=test_config.privacy_mode)
    return RoastEngine(
        config=test_config,
        camera=mock_camera,
        privacy=privacy,
        provider=mock_provider,
        mascot=mascot,
        speech=mock_speech,
    )
