"""State machine and animation ticker for the expressive pixel mascot."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional, Callable, List
from roastbot.config import MascotEmotion


@dataclass
class MascotSnapshot:
    """Read-only view of the mascot's live state."""
    emotion: MascotEmotion
    current_dialog: Optional[str]
    mood_score: int
    animation_frame: int
    is_speaking: bool
    idle_seconds: float


class MascotStateMachine:
    """Manages emotional transitions, dialog speech bubble lifetime, and idle decay."""

    def __init__(self, idle_timeout_seconds: float = 8.0, sleep_timeout_seconds: float = 60.0):
        self.emotion: MascotEmotion = MascotEmotion.IDLE
        self.current_dialog: Optional[str] = None
        self.dialog_expires_at: float = 0.0
        self.last_interaction_time: float = time.time()
        self.mood_score: int = 75  # 0 to 100
        self.animation_frame: int = 0
        self.idle_timeout_seconds = idle_timeout_seconds
        self.sleep_timeout_seconds = sleep_timeout_seconds
        self._listeners: List[Callable[[MascotSnapshot], None]] = []

    def set_emotion(self, emotion: MascotEmotion, dialog: Optional[str] = None, dialog_duration_seconds: float = 10.0) -> None:
        """Trigger an emotion change with optional spoken dialog."""
        self.emotion = emotion
        self.last_interaction_time = time.time()
        if dialog:
            self.current_dialog = dialog
            self.dialog_expires_at = time.time() + dialog_duration_seconds
        self._notify_listeners()

    def update_mood(self, delta: int) -> None:
        """Adjust overall happiness/morale (e.g. hydration boosts mood, extreme clutter drops it)."""
        self.mood_score = max(0, min(100, self.mood_score + delta))
        self._notify_listeners()

    def tick(self) -> MascotSnapshot:
        """Advance animation ticker and handle idle/dialog timeout transitions."""
        now = time.time()
        self.animation_frame = (self.animation_frame + 1) % 60
        idle_duration = now - self.last_interaction_time

        # Expire spoken speech bubble dialog
        if self.current_dialog and now > self.dialog_expires_at:
            self.current_dialog = None

        # Return to IDLE after active emotional reaction
        if self.emotion not in (MascotEmotion.IDLE, MascotEmotion.SLEEPING):
            if idle_duration > self.idle_timeout_seconds:
                self.emotion = MascotEmotion.IDLE

        # Fall asleep after prolonged inactivity
        if self.emotion == MascotEmotion.IDLE and idle_duration > self.sleep_timeout_seconds:
            self.emotion = MascotEmotion.SLEEPING

        snapshot = self.get_snapshot()
        return snapshot

    def wake_up(self) -> None:
        """Wake mascot from sleep."""
        self.last_interaction_time = time.time()
        if self.emotion == MascotEmotion.SLEEPING:
            self.emotion = MascotEmotion.IDLE
            self._notify_listeners()

    def get_snapshot(self) -> MascotSnapshot:
        """Return snapshot of current state."""
        return MascotSnapshot(
            emotion=self.emotion,
            current_dialog=self.current_dialog,
            mood_score=self.mood_score,
            animation_frame=self.animation_frame,
            is_speaking=self.current_dialog is not None,
            idle_seconds=max(0.0, time.time() - self.last_interaction_time),
        )

    def add_listener(self, callback: Callable[[MascotSnapshot], None]) -> None:
        """Register state change callback."""
        self._listeners.append(callback)

    def _notify_listeners(self) -> None:
        snapshot = self.get_snapshot()
        for listener in self._listeners:
            try:
                listener(snapshot)
            except Exception:
                pass
