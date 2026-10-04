"""Local Ollama multimodal vision provider (LLaVA / Moondream2)."""

from __future__ import annotations

import base64
import logging
import httpx

from roastbot.config import RoastSeverity, RoastCategory, MascotEmotion
from roastbot.providers.base import BaseVisionProvider, VisionAnalysisResult
from roastbot.engine.prompts import build_vision_prompt, parse_vision_json

logger = logging.getLogger(__name__)


class OllamaVisionProvider(BaseVisionProvider):
    """Integrates with local Ollama daemon hosting vision models like llava or moondream."""

    name: str = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llava:latest", timeout_seconds: float = 45.0):
        self.base_url = base_url.rstrip("/")
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
            "prompt": prompt_text,
            "images": [b64_image],
            "stream": False,
            "format": "json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )
            resp.raise_for_status()
            result_json = resp.json()

        raw_text = result_json.get("response", "")
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
            provider_name=f"ollama ({self.model})",
            raw_response=raw_text,
        )
