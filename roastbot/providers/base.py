"""Base interfaces and data structures for vision providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from roastbot.config import RoastSeverity, RoastCategory, MascotEmotion


@dataclass
class VisionAnalysisResult:
    """Standardized output from any multimodal vision provider."""
    roast: str
    score: int
    emotion: MascotEmotion
    category: RoastCategory
    severity: RoastSeverity
    detected_items: List[str] = field(default_factory=list)
    is_celebration: bool = False
    provider_name: str = "unknown"
    raw_response: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "roast": self.roast,
            "score": self.score,
            "emotion": self.emotion.value,
            "category": self.category.value,
            "severity": self.severity.value,
            "detected_items": self.detected_items,
            "is_celebration": self.is_celebration,
            "provider_name": self.provider_name,
        }


class BaseVisionProvider(ABC):
    """Abstract base class for vision model providers."""

    name: str = "base"

    @abstractmethod
    async def analyze_frame(
        self,
        frame_bytes: bytes,
        severity: RoastSeverity,
        category: RoastCategory,
    ) -> VisionAnalysisResult:
        """Analyze the captured camera frame and generate a humorous critique."""
        pass
