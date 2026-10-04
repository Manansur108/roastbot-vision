"""Anthropic Claude 3.5 Sonnet multimodal vision provider."""

from __future__ import annotations

import base64
import logging
from typing import Optional
import httpx

from roastbot.config import RoastSeverity, RoastCategory, MascotEmotion
from roastbot.providers.base import BaseVisionProvider, VisionAnalysisResult
from roastbot.engine.prompts import build_vision_prompt, parse_vision_json

logger = logging.getLogger(__name__)


class AnthropicVisionProvider(BaseVisionProvider):
    """Integrates with Anthropic Claude 3.5 Sonnet multimodal vision API."""

    name: str = "anthropic"

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022", timeout_seconds: float = 25.0):
        if not api_key:
            raise ValueError("Anthropic API key must be provided.")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout_seconds

    async def analyze_frame(
        self,
        frame_bytes: bytes,
        severity: RoastSeverity,
        category: RoastCategory,
    ) -> VisionAnalysisResult:
        prompt_text = build_vision_prompt(severity, category)
        b64_image = base64.b64encode(frame_bytes).decode("ascii")

        payload = {
            "model": self.model,
            "max_tokens": 250,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": b64_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt_text,
                        },
                    ],
                }
            ],
        }

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            result_json = resp.json()

        # Claude returns content array with text blocks
        raw_text = ""
        for block in result_json.get("content", []):
            if block.get("type") == "text":
                raw_text += block.get("text", "")

        parsed = parse_vision_json(raw_text)

        emotion_str = str(parsed.get("emotion", "snarky")).lower()
        try:
            emotion = MascotEmotion(emotion_str)
        except ValueError:
            emotion = MascotEmotion.SNARKY

        return VisionAnalysisResult(
            roast=str(parsed.get("roast", "No roast returned.")),
            score=int(parsed.get("score", 50)),
            emotion=emotion,
            category=category,
            severity=severity,
            detected_items=list(parsed.get("detected_items", [])),
            is_celebration=bool(parsed.get("is_celebration", False)),
            provider_name=f"anthropic ({self.model})",
            raw_response=raw_text,
        )
