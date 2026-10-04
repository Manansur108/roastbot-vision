"""Tests for configuration models and environment parsing."""

import os
from roastbot.config import (
    AppConfig,
    RoastSeverity,
    RoastCategory,
    MascotEmotion,
    PrivacyMode,
    VisionProviderType,
)


def test_config_defaults():
    config = AppConfig()
    assert config.severity == RoastSeverity.SNARKY
    assert config.category == RoastCategory.GENERAL_ROAST
    assert config.privacy_mode == PrivacyMode.BLUR_FACES
    assert config.server_port == 8420
    assert config.speech_enabled is True
    assert config.use_mock_camera is False


def test_config_from_env(monkeypatch):
    monkeypatch.setenv("ROASTBOT_SEVERITY", "gordon_ramsay")
    monkeypatch.setenv("ROASTBOT_CATEGORY", "posture_check")
    monkeypatch.setenv("ROASTBOT_PRIVACY", "redact_screens")
    monkeypatch.setenv("ROASTBOT_SPEECH", "false")
    monkeypatch.setenv("ROASTBOT_MOCK_CAMERA", "true")

    cfg = AppConfig.from_env()
    assert cfg.severity == RoastSeverity.GORDON_RAMSAY
    assert cfg.category == RoastCategory.POSTURE_CHECK
    assert cfg.privacy_mode == PrivacyMode.REDACT_SCREENS
    assert cfg.speech_enabled is False
    assert cfg.use_mock_camera is True


def test_enum_members():
    assert len(RoastSeverity) == 4
    assert len(RoastCategory) == 7
    assert len(MascotEmotion) == 7
    assert len(PrivacyMode) == 4
    assert len(VisionProviderType) == 5
