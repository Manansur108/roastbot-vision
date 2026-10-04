"""OpenAI multimodal vision provider (GPT-4o / GPT-4o-mini)."""

from __future__ import annotations

import base64
import logging
from typing import Optional
import httpx

from roastbot.config import RoastSeverity, RoastCategory, MascotEmotion
from roastbot.providers.base import BaseVisionProvider, VisionAnalysisResult
from roastbot.engine.prompts import build_vision_prompt, parse_vision_json

logger = logging.getLogger(__name__)


class OpenAIVisionProvider(BaseVisionProvider):
    """Integrates with OpenAI GPT-4o multimodal vision API."""

    name: str = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", timeout_seconds: float = 20.0):
        if not api_key:
            raise ValueError("OpenAI API key must be provided.")
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
        data_uri = f"data:image/jpeg;base64,{b64_image}"

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {
                            "type": "image_url",
                            "image_url": {"url": data_uri, "detail": "low"},
                        },
                    ],
                }
            ],
            "max_tokens": 200,
            "temperature": 0.8,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            result_json = resp.json()

        raw_text = result_json["choices"][0]["message"]["content"]
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
            provider_name=f"openai ({self.model})",
            raw_response=raw_text,
        )
