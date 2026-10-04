"""Text-to-speech engine module."""

from roastbot.tts.speech import SpeechEngine
from roastbot.tts.mock_speech import MockSpeechEngine

__all__ = ["SpeechEngine", "MockSpeechEngine"]
