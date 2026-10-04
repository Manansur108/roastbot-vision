"""Tests for speech synthesis queue and mock audio engine."""

from roastbot.tts.mock_speech import MockSpeechEngine


def test_mock_speech_speak():
    speech = MockSpeechEngine(enabled=True)
    assert speech.history == []

    speech.speak("Stand up straight, you cashew nut.")
    assert len(speech.history) == 1
    assert speech.last_spoken == "Stand up straight, you cashew nut."

    # Interrupt clears history
    speech.speak("New priority roast", interrupt=True)
    assert len(speech.history) == 1
    assert speech.last_spoken == "New priority roast"


def test_mock_speech_mute():
    speech = MockSpeechEngine(enabled=True)
    speech.set_muted(True)
    speech.speak("This should not be spoken.")
    assert len(speech.history) == 0

    speech.toggle_mute()
    assert speech.muted is False
    speech.speak("Now I can speak!")
    assert speech.last_spoken == "Now I can speak!"
