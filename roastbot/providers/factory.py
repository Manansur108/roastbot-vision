"""Provider factory with intelligent auto-discovery and offline fallback."""

from __future__ import annotations

import logging
import os
from roastbot.config import AppConfig, VisionProviderType
from roastbot.providers.base import BaseVisionProvider
from roastbot.providers.mock_provider import MockVisionProvider
from roastbot.providers.openai_provider import OpenAIVisionProvider
from roastbot.providers.anthropic_provider import AnthropicVisionProvider
from roastbot.providers.ollama_provider import OllamaVisionProvider

logger = logging.getLogger(__name__)


def create_vision_provider(config: AppConfig) -> BaseVisionProvider:
    """Instantiate the appropriate vision provider based on configuration and available API keys."""
    ptype = config.provider_type

    if ptype == VisionProviderType.MOCK:
        logger.info("Using offline MockVisionProvider.")
        return MockVisionProvider()

    if ptype == VisionProviderType.OPENAI:
        key = config.openai_api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            logger.warning("OPENAI_API_KEY is not set. Falling back to MockVisionProvider.")
            return MockVisionProvider()
        return OpenAIVisionProvider(api_key=key, model=config.openai_model)

    if ptype == VisionProviderType.ANTHROPIC:
        key = config.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            logger.warning("ANTHROPIC_API_KEY is not set. Falling back to MockVisionProvider.")
            return MockVisionProvider()
        return AnthropicVisionProvider(api_key=key, model=config.anthropic_model)

    if ptype == VisionProviderType.OLLAMA:
        return OllamaVisionProvider(base_url=config.ollama_base_url, model=config.ollama_model)

    # AUTO mode: Check OpenAI -> Anthropic -> Fallback to Mock
    openai_key = config.openai_api_key or os.getenv("OPENAI_API_KEY")
    if openai_key:
        logger.info("Auto-selected OpenAI provider via detected OPENAI_API_KEY.")
        return OpenAIVisionProvider(api_key=openai_key, model=config.openai_model)

    anthropic_key = config.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        logger.info("Auto-selected Anthropic provider via detected ANTHROPIC_API_KEY.")
        return AnthropicVisionProvider(api_key=anthropic_key, model=config.anthropic_model)

    logger.info("No vision API keys detected in environment; running seamlessly on offline MockVisionProvider.")
    return MockVisionProvider()
