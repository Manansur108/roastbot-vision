"""Tests for multimodal vision providers."""

import pytest
from roastbot.config import RoastCategory, RoastSeverity, VisionProviderType, AppConfig
from roastbot.providers.mock_provider import MockVisionProvider
from roastbot.providers.factory import create_vision_provider
from roastbot.providers.base import VisionAnalysisResult


def test_mock_provider_all_categories():
    import asyncio
    provider = MockVisionProvider(seed=123)
    dummy_frame = b"fake-jpeg-bytes"

    async def _run():
        for cat in RoastCategory:
            result = await provider.analyze_frame(dummy_frame, RoastSeverity.SNARKY, cat)
            assert isinstance(result, VisionAnalysisResult)
            assert len(result.roast) > 0
            assert 0 <= result.score <= 100
            assert result.category == cat
            assert result.severity == RoastSeverity.SNARKY
            assert result.provider_name == "mock"

    asyncio.run(_run())


def test_mock_provider_severities():
    import asyncio
    provider = MockVisionProvider(seed=456)
    dummy_frame = b"fake-jpeg-bytes"

    async def _run():
        for sev in RoastSeverity:
            result = await provider.analyze_frame(dummy_frame, sev, RoastCategory.DESK_CLUTTER)
            assert result.severity == sev
            assert len(result.roast) > 0

    asyncio.run(_run())


def test_provider_factory_fallback():
    config = AppConfig(provider_type=VisionProviderType.AUTO)
    provider = create_vision_provider(config)
    assert provider is not None
    # In test environment with no OpenAI/Anthropic keys, safely defaults to mock
    assert provider.name in ("mock", "openai", "anthropic")


def test_result_to_dict():
    provider = MockVisionProvider(seed=1)
    res = VisionAnalysisResult(
        roast="Nice coffee mug.",
        score=75,
        emotion=provider.rng.choice(list(RoastSeverity)),
        category=RoastCategory.CAFFEINE_RADAR,
        severity=RoastSeverity.GENTLE,
        detected_items=["mug"],
        is_celebration=False,
    )
    d = res.to_dict()
    assert d["roast"] == "Nice coffee mug."
    assert d["score"] == 75
    assert d["category"] == "caffeine_radar"
    assert "detected_items" in d
