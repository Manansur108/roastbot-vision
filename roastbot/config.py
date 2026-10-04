"""Configuration models and enumeration definitions for RoastBot-Vision."""

from __future__ import annotations

import os
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class RoastSeverity(str, Enum):
    """Roast intensity levels ranging from friendly banter to total culinary devastation."""
    GENTLE = "gentle"              # Friendly ribbing, light teasing
    SNARKY = "snarky"              # Sarcastic tech teammate / cynical peer review
    SAVAGE = "savage"              # Brutal comedy roast, unhinged burns
    GORDON_RAMSAY = "gordon_ramsay"  # Kitchen Nightmares / Full Rage shouting mode


class RoastCategory(str, Enum):
    """Roast evaluation targets."""
    DESK_CLUTTER = "desk_clutter"       # Cables, old dishes, dust, chaotic organization
    POSTURE_CHECK = "posture_check"     # Spine curvature, shrimp slouching, ergonomics
    DRIP_CHECK = "drip_check"           # Outfit rating, wrinkly hoodie, developer aesthetic
    HYDRATION_HERO = "hydration_hero"   # Water sipping recognition and triumphant celebration
    CODE_ROAST = "code_roast"           # Terminal tabs, IDE chaos, debugging despair
    CAFFEINE_RADAR = "caffeine_radar"   # Mug graveyard, caffeine overload detection
    GENERAL_ROAST = "general_roast"     # Autonomous ambient observation


class MascotEmotion(str, Enum):
    """Expressive emotional states for the pixel mascot."""
    IDLE = "idle"               # Casual bouncing, blinking
    THINKING = "thinking"       # Scanning camera feed, antenna pulsing
    SNARKY = "snarky"           # Smug smirk, arched eyebrow
    SHOCKED = "shocked"         # Wide glowing eyes, dropped jaw, CRT static
    CELEBRATING = "celebrating" # Confetti, dancing, thumbs up (hydration!)
    ROASTING = "roasting"       # Fire breath, megaphone, intense glare
    SLEEPING = "sleeping"       # Floating Z's, dimmed CRT screen


class PrivacyMode(str, Enum):
    """Camera privacy masking levels."""
    NORMAL = "normal"               # Full resolution frame without redaction
    BLUR_FACES = "blur_faces"       # Local edge face detection & Gaussian blur
    REDACT_SCREENS = "redact_screens" # Blackout screen / display regions
    LOCAL_ONLY = "local_only"       # Never sends frames outside localhost (Mock/Ollama only)


class VisionProviderType(str, Enum):
    """Supported multimodal vision model backends."""
    MOCK = "mock"             # Deterministic high-humor offline mock (no API key needed)
    OPENAI = "openai"         # OpenAI GPT-4o / GPT-4o-mini
    ANTHROPIC = "anthropic"   # Anthropic Claude 3.5 Sonnet
    OLLAMA = "ollama"         # Local Ollama endpoint (LLaVA / Moondream2)
    AUTO = "auto"             # Auto-detect available credentials or fallback to mock


class AppConfig(BaseModel):
    """Central configuration for RoastBot-Vision application."""

    # Roasting behaviors
    severity: RoastSeverity = Field(
        default=RoastSeverity.SNARKY,
        description="Current roast severity level."
    )
    category: RoastCategory = Field(
        default=RoastCategory.GENERAL_ROAST,
        description="Target category for vision evaluation."
    )
    auto_roast_interval_seconds: int = Field(
        default=45,
        ge=5,
        le=3600,
        description="Interval in seconds for periodic autonomous roasts."
    )
    auto_roast_enabled: bool = Field(
        default=False,
        description="Whether periodic autonomous camera roaster is running."
    )

    # Vision provider settings
    provider_type: VisionProviderType = Field(
        default=VisionProviderType.AUTO,
        description="Vision model provider to use."
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API Key (defaults to OPENAI_API_KEY environment variable)."
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI vision model name."
    )
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API Key (defaults to ANTHROPIC_API_KEY environment variable)."
    )
    anthropic_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Anthropic vision model name."
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama REST endpoint URL."
    )
    ollama_model: str = Field(
        default="llava:latest",
        description="Ollama multimodal vision model tag."
    )

    # Privacy and Camera settings
    privacy_mode: PrivacyMode = Field(
        default=PrivacyMode.BLUR_FACES,
        description="Privacy masking level for captured frames."
    )
    camera_index: int = Field(
        default=0,
        description="System webcam index for cv2.VideoCapture."
    )
    use_mock_camera: bool = Field(
        default=False,
        description="Force usage of simulated test camera even if real camera is present."
    )
    frame_width: int = Field(
        default=640,
        description="Webcam frame capture width."
    )
    frame_height: int = Field(
        default=480,
        description="Webcam frame capture height."
    )

    # Audio & Speech synthesis settings
    speech_enabled: bool = Field(
        default=True,
        description="Whether text-to-speech engine speaks roasts out loud."
    )
    voice_rate: int = Field(
        default=175,
        ge=80,
        le=350,
        description="Speech synthesis rate (words per minute)."
    )
    voice_volume: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Speech synthesis volume level."
    )

    # Server and companion dashboard
    server_host: str = Field(
        default="127.0.0.1",
        description="FastAPI host address."
    )
    server_port: int = Field(
        default=8420,
        description="FastAPI companion server port."
    )

    @classmethod
    def from_env(cls) -> AppConfig:
        """Create AppConfig populated with environment variables if present."""
        return cls(
            severity=RoastSeverity(os.getenv("ROASTBOT_SEVERITY", RoastSeverity.SNARKY.value)),
            category=RoastCategory(os.getenv("ROASTBOT_CATEGORY", RoastCategory.GENERAL_ROAST.value)),
            provider_type=VisionProviderType(os.getenv("ROASTBOT_PROVIDER", VisionProviderType.AUTO.value)),
            privacy_mode=PrivacyMode(os.getenv("ROASTBOT_PRIVACY", PrivacyMode.BLUR_FACES.value)),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "llava:latest"),
            speech_enabled=os.getenv("ROASTBOT_SPEECH", "true").lower() in ("1", "true", "yes"),
            use_mock_camera=os.getenv("ROASTBOT_MOCK_CAMERA", "false").lower() in ("1", "true", "yes"),
        )
