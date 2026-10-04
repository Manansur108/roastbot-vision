"""Speech synthesis engine wrapping pyttsx3 with non-blocking queueing and mute controls."""

from __future__ import annotations

import logging
import queue
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None  # type: ignore


class SpeechEngine:
    """Threaded text-to-speech engine supporting rate/volume modulation and mute states."""

    def __init__(self, rate: int = 175, volume: float = 0.9, enabled: bool = True):
        self.rate = rate
        self.volume = volume
        self.enabled = enabled
        self.muted = not enabled

        self._queue: queue.Queue[Optional[str]] = queue.Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._engine = None
        self._available = False

        self._init_tts_engine()
        self._start_worker()

    def _init_tts_engine(self) -> None:
        """Safely initialize pyttsx3 driver without crashing on headless systems."""
        if pyttsx3 is None:
            logger.info("pyttsx3 module not installed; audio synthesis disabled.")
            return

        try:
            # We initialize pyttsx3 engine inside worker thread or test availability here
            engine = pyttsx3.init()
            engine.setProperty("rate", self.rate)
            engine.setProperty("volume", self.volume)
            self._engine = engine
            self._available = True
            logger.info("pyttsx3 speech engine successfully initialized.")
        except Exception as e:
            logger.warning(f"pyttsx3 initialization failed (audio driver not present?): {e}")
            self._engine = None
            self._available = False

    def _start_worker(self) -> None:
        """Launch background worker processing spoken speech jobs."""
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True, name="RoastBot-TTS")
        self._worker_thread.start()

    def _process_queue(self) -> None:
        """Background thread consuming utterances."""
        while not self._stop_event.is_set():
            try:
                text = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue

            if text is None:  # Sentinel to shutdown
                break

            if self.muted or not self.enabled or not self._available:
                self._queue.task_done()
                continue

            try:
                if self._engine is not None:
                    self._engine.say(text)
                    self._engine.runAndWait()
            except Exception as e:
                logger.debug(f"TTS synthesis error: {e}")
            finally:
                self._queue.task_done()

    def speak(self, text: str, interrupt: bool = False) -> None:
        """Queue text to be spoken out loud. If interrupt=True, clears pending utterances."""
        if not text or self.muted or not self.enabled:
            return

        if interrupt:
            # Clear pending queue
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                    self._queue.task_done()
                except queue.Empty:
                    break

        self._queue.put(text)

    def set_muted(self, muted: bool) -> None:
        """Mute or unmute voice audio output."""
        self.muted = muted

    def toggle_mute(self) -> bool:
        """Toggle audio mute state; returns new muted state."""
        self.muted = not self.muted
        return self.muted

    def is_available(self) -> bool:
        """Check if active TTS system driver is functional."""
        return self._available

    def shutdown(self) -> None:
        """Stop worker thread and cleanup engine resources."""
        self._stop_event.set()
        self._queue.put(None)
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)
        if self._engine:
            try:
                self._engine.stop()
            except Exception:
                pass
            self._engine = None
