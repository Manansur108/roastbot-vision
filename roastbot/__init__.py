"""RoastBot-Vision: Real-Time Multimodal Vision Sidekick & Desk Critic."""

__version__ = "0.1.0"
__author__ = "Manan Sur"

from roastbot.config import (
    AppConfig,
    RoastSeverity,
    RoastCategory,
    MascotEmotion,
    PrivacyMode,
    VisionProviderType,
)
from roastbot.engine.roaster import RoastEngine
from roastbot.providers.base import VisionAnalysisResult
from roastbot.mascot.sprites import PixelSpriteRenderer

__all__ = [
    "__version__",
    "AppConfig",
    "RoastSeverity",
    "RoastCategory",
    "MascotEmotion",
    "PrivacyMode",
    "VisionProviderType",
    "RoastEngine",
    "VisionAnalysisResult",
    "PixelSpriteRenderer",
]
