"""Mock speech engine for tests and headless verification."""

from __future__ import annotations

import time
from typing import List, Tuple


class MockSpeechEngine:
    """Mock speech synthesizer that captures spoken text history in memory."""

    def __init__(self, rate: int = 175, volume: float = 0.9, enabled: bool = True):
        self.rate = rate
        self.volume = volume
        self.enabled = enabled
        self.muted = not enabled
        self.history: List[Tuple[float, str]] = []

    def speak(self, text: str, interrupt: bool = False) -> None:
        if not text or self.muted or not self.enabled:
            return
        if interrupt:
            self.history.clear()
        self.history.append((time.time(), text))

    def set_muted(self, muted: bool) -> None:
        self.muted = muted

    def toggle_mute(self) -> bool:
        self.muted = not self.muted
        return self.muted

    def is_available(self) -> bool:
        return True

    def shutdown(self) -> None:
        pass

    @property
    def last_spoken(self) -> str | None:
        return self.history[-1][1] if self.history else None
