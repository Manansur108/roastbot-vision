"""Core RoastEngine orchestrating camera capture, privacy redaction, vision inference, and mascot reactions."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional, List, Dict, Any, Callable
import numpy as np

from roastbot.config import AppConfig, RoastCategory, RoastSeverity, MascotEmotion
from roastbot.camera.sampler import BaseCameraSampler, WebcamSampler, MockCameraSampler
from roastbot.camera.privacy import PrivacyEngine
from roastbot.providers.base import BaseVisionProvider, VisionAnalysisResult
from roastbot.providers.factory import create_vision_provider
from roastbot.mascot.state import MascotStateMachine
from roastbot.tts.speech import SpeechEngine

logger = logging.getLogger(__name__)


class RoastEngine:
    """Central orchestrator for multimodal vision analysis, mascot expressions, and audio commentary."""

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        camera: Optional[BaseCameraSampler] = None,
        privacy: Optional[PrivacyEngine] = None,
        provider: Optional[BaseVisionProvider] = None,
        mascot: Optional[MascotStateMachine] = None,
        speech: Optional[SpeechEngine] = None,
    ):
        self.config = config or AppConfig()

        # Initialize or inject components
        if camera is not None:
            self.camera = camera
        elif self.config.use_mock_camera:
            self.camera = MockCameraSampler(width=self.config.frame_width, height=self.config.frame_height)
        else:
            real_cam = WebcamSampler(
                camera_index=self.config.camera_index,
                width=self.config.frame_width,
                height=self.config.frame_height,
            )
            # Graceful fallback: If real camera cannot be opened, switch to MockCameraSampler seamlessly
            if real_cam.is_available():
                self.camera = real_cam
            else:
                logger.info("Real webcam not available; initializing synthetic MockCameraSampler.")
                self.camera = MockCameraSampler(width=self.config.frame_width, height=self.config.frame_height)

        self.privacy = privacy or PrivacyEngine(mode=self.config.privacy_mode)
        self.provider = provider or create_vision_provider(self.config)
        self.mascot = mascot or MascotStateMachine()
        self.speech = speech or SpeechEngine(
            rate=self.config.voice_rate,
            volume=self.config.voice_volume,
            enabled=self.config.speech_enabled,
        )

        self.history: List[VisionAnalysisResult] = []
        self.stats: Dict[str, Any] = {
            "total_roasts": 0,
            "total_celebrations": 0,
            "average_score": 0.0,
            "category_counts": {},
            "start_time": time.time(),
        }

        self._listeners: List[Callable[[VisionAnalysisResult], None]] = []
        self._auto_task: Optional[asyncio.Task] = None
        self._running = False

    async def roast_now(
        self,
        category: Optional[RoastCategory] = None,
        severity: Optional[RoastSeverity] = None,
    ) -> VisionAnalysisResult:
        """Trigger an immediate camera capture, privacy mask, and multimodal roast analysis."""
        target_category = category or self.config.category
        target_severity = severity or self.config.severity

        # 1. Update mascot to scanning state
        self.mascot.set_emotion(MascotEmotion.THINKING, dialog="Scanning workspace with vision models...")

        # 2. Capture frame from camera
        frame = self.camera.capture_frame()
        if frame is None:
            # Fallback blank frame if camera returned empty
            frame = np.zeros((self.config.frame_height, self.config.frame_width, 3), dtype=np.uint8)

        # 3. Apply edge privacy transforms
        redacted_frame = self.privacy.process_frame(frame)

        # 4. Encode frame to JPEG
        frame_bytes = PrivacyEngine.encode_to_jpeg(redacted_frame, quality=80)

        # 5. Execute vision model inference
        try:
            result = await self.provider.analyze_frame(
                frame_bytes=frame_bytes,
                severity=target_severity,
                category=target_category,
            )
        except Exception as e:
            logger.error(f"Vision provider analysis failed: {e}")
            result = VisionAnalysisResult(
                roast=f"Vision model error: {str(e)}",
                score=50,
                emotion=MascotEmotion.SHOCKED,
                category=target_category,
                severity=target_severity,
                detected_items=["error"],
                is_celebration=False,
                provider_name="error_handler",
            )

        # 6. Update mascot emotion and speech dialog
        self.mascot.set_emotion(result.emotion, dialog=result.roast, dialog_duration_seconds=12.0)

        # 7. Update mascot mood
        if result.is_celebration:
            self.mascot.update_mood(+20)
        elif result.score < 25:
            self.mascot.update_mood(-10)

        # 8. Queue speech synthesis out loud
        if self.config.speech_enabled and self.speech.is_available() and not self.speech.muted:
            self.speech.speak(result.roast)

        # 9. Update stats and history
        self._record_result(result)

        # 10. Notify external listeners (UI / Web / WebSocket)
        for listener in self._listeners:
            try:
                listener(result)
            except Exception as e:
                logger.debug(f"Roast listener error: {e}")

        return result

    def _record_result(self, result: VisionAnalysisResult) -> None:
        """Update metrics and history buffer."""
        self.history.append(result)
        if len(self.history) > 100:
            self.history.pop(0)

        self.stats["total_roasts"] += 1
        if result.is_celebration:
            self.stats["total_celebrations"] += 1

        # Running average score
        scores = [r.score for r in self.history]
        self.stats["average_score"] = round(sum(scores) / len(scores), 1)

        # Category counter
        cat_key = result.category.value
        self.stats["category_counts"][cat_key] = self.stats["category_counts"].get(cat_key, 0) + 1

    def capture_preview(self) -> bytes:
        """Capture a single frame with privacy redaction applied and return JPEG bytes."""
        frame = self.camera.capture_frame()
        if frame is None:
            frame = np.zeros((self.config.frame_height, self.config.frame_width, 3), dtype=np.uint8)
        redacted = self.privacy.process_frame(frame)
        return PrivacyEngine.encode_to_jpeg(redacted, quality=80)

    def add_listener(self, callback: Callable[[VisionAnalysisResult], None]) -> None:
        """Add result notification subscriber."""
        self._listeners.append(callback)

    def start_auto_roast(self) -> None:
        """Start the background periodic auto-roast worker."""
        if self._running:
            return
        self._running = True
        self._auto_task = asyncio.create_task(self._auto_roast_loop())
        logger.info(f"Auto-roast loop started (interval: {self.config.auto_roast_interval_seconds}s)")

    def stop_auto_roast(self) -> None:
        """Halt the background periodic auto-roast worker."""
        self._running = False
        if self._auto_task and not self._auto_task.done():
            self._auto_task.cancel()
        self._auto_task = None

    async def _auto_roast_loop(self) -> None:
        """Background coroutine periodically running roasts."""
        while self._running:
            try:
                await asyncio.sleep(self.config.auto_roast_interval_seconds)
                if not self._running:
                    break
                await self.roast_now()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in auto roast loop: {e}")
                await asyncio.sleep(5.0)

    def get_stats(self) -> Dict[str, Any]:
        """Retrieve aggregated metrics."""
        uptime = round(time.time() - self.stats["start_time"], 1)
        return {
            **self.stats,
            "uptime_seconds": uptime,
            "mascot_emotion": self.mascot.emotion.value,
            "mascot_mood": self.mascot.mood_score,
            "speech_muted": self.speech.muted,
            "severity": self.config.severity.value,
            "category": self.config.category.value,
            "privacy_mode": self.privacy.mode.value,
            "provider": self.provider.name,
        }

    def close(self) -> None:
        """Release camera handles and shutdown speech engine."""
        self.stop_auto_roast()
        if self.camera:
            self.camera.release()
        if self.speech:
            self.speech.shutdown()
