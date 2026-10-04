"""Tests for prompt engineering and vision JSON parser."""

from roastbot.config import RoastSeverity, RoastCategory
from roastbot.engine.prompts import build_vision_prompt, parse_vision_json


def test_build_vision_prompt_severities():
    for sev in RoastSeverity:
        prompt = build_vision_prompt(sev, RoastCategory.DESK_CLUTTER)
        assert "OUTPUT FORMAT REQUIREMENTS" in prompt
        assert "Bytey" in prompt
        if sev == RoastSeverity.GORDON_RAMSAY:
            assert "RAMSAY" in prompt


def test_parse_vision_json_clean():
    json_text = '{"roast": "Hilarious roast here.", "score": 42, "emotion": "shocked", "detected_items": ["mug"], "is_celebration": false}'
    parsed = parse_vision_json(json_text)
    assert parsed["roast"] == "Hilarious roast here."
    assert parsed["score"] == 42
    assert parsed["emotion"] == "shocked"
    assert parsed["detected_items"] == ["mug"]
    assert parsed["is_celebration"] is False


def test_parse_vision_json_markdown_blocks():
    json_text = '```json\n{"roast": "Markdown wrapped roast.", "score": 90, "emotion": "celebrating", "detected_items": ["water bottle"], "is_celebration": true}\n```'
    parsed = parse_vision_json(json_text)
    assert parsed["roast"] == "Markdown wrapped roast."
    assert parsed["score"] == 90
    assert parsed["is_celebration"] is True


def test_parse_vision_json_plain_text_fallback():
    raw_text = "I see a disaster of cables on your desk! Absolutely horrific setup."
    parsed = parse_vision_json(raw_text)
    assert "disaster of cables" in parsed["roast"]
    assert parsed["score"] == 50
    assert parsed["emotion"] in ("shocked", "snarky")
