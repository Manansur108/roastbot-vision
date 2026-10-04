"""Tests for core RoastEngine orchestrator."""

import pytest
from roastbot.config import RoastCategory, RoastSeverity, MascotEmotion
from roastbot.engine.roaster import RoastEngine


def test_roast_pipeline_execution(test_engine):
    import asyncio
    async def _run():
        result = await test_engine.roast_now(
            category=RoastCategory.DESK_CLUTTER,
            severity=RoastSeverity.SNARKY,
        )

        assert result is not None
        assert len(result.roast) > 0
        assert result.category == RoastCategory.DESK_CLUTTER
        assert result.severity == RoastSeverity.SNARKY
        assert len(test_engine.history) == 1
        assert test_engine.speech.last_spoken == result.roast
        assert test_engine.mascot.current_dialog == result.roast

    asyncio.run(_run())


def test_roast_hydration_celebration(test_engine):
    import asyncio
    async def _run():
        result = await test_engine.roast_now(
            category=RoastCategory.HYDRATION_HERO,
            severity=RoastSeverity.GENTLE,
        )

        assert result.is_celebration is True
        assert result.emotion == MascotEmotion.CELEBRATING
        assert test_engine.stats["total_celebrations"] == 1

    asyncio.run(_run())


def test_roast_engine_stats_and_preview(test_engine):
    stats = test_engine.get_stats()
    assert "total_roasts" in stats
    assert "mascot_mood" in stats
    assert "provider" in stats

    preview_bytes = test_engine.capture_preview()
    assert isinstance(preview_bytes, bytes)
    assert len(preview_bytes) > 0
