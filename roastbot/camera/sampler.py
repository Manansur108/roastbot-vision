"""Camera frame samplers including physical webcam and simulated test cameras."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

try:
    import cv2
except ImportError:
    cv2 = None  # type: ignore


class BaseCameraSampler(ABC):
    """Abstract interface for video frame sampling."""

    @abstractmethod
    def capture_frame(self) -> Optional[np.ndarray]:
        """Capture and return a single BGR frame as a numpy array, or None if unavailable."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if camera device or frame source is actively available."""
        pass

    @abstractmethod
    def release(self) -> None:
        """Release any hardware camera handles or allocated resources."""
        pass


class WebcamSampler(BaseCameraSampler):
    """Hardware webcam sampler powered by OpenCV VideoCapture."""

    def __init__(self, camera_index: int = 0, width: int = 640, height: int = 480):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self._cap: Optional[cv2.VideoCapture] = None
        self._initialized = False

    def _ensure_capture(self) -> bool:
        if cv2 is None:
            logger.warning("OpenCV (cv2) is not installed; WebcamSampler unavailable.")
            return False

        if self._cap is None or not self._cap.isOpened():
            try:
                self._cap = cv2.VideoCapture(self.camera_index)
                if self._cap.isOpened():
                    self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                    self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                    self._initialized = True
                    return True
                else:
                    logger.warning(f"Failed to open hardware webcam at index {self.camera_index}.")
                    self._cap = None
                    return False
            except Exception as e:
                logger.error(f"Error initializing camera index {self.camera_index}: {e}")
                self._cap = None
                return False
        return True

    def capture_frame(self) -> Optional[np.ndarray]:
        """Capture one frame from the physical camera."""
        if not self._ensure_capture():
            return None
        assert self._cap is not None
        ret, frame = self._cap.read()
        if not ret or frame is None:
            logger.warning("Webcam read returned empty frame.")
            return None
        return frame

    def is_available(self) -> bool:
        return self._ensure_capture()

    def release(self) -> None:
        if self._cap is not None and self._cap.isOpened():
            self._cap.release()
            self._cap = None
        self._initialized = False


class MockCameraSampler(BaseCameraSampler):
    """Simulated camera generating synthetic realistic desk & posture frames.
    
    Supports selectable test scenarios (messy_desk, drinking_water, slouching,
    sharp_outfit, code_chaos, clean_desk).
    """

    SCENARIOS = [
        "messy_desk",
        "drinking_water",
        "slouching",
        "sharp_outfit",
        "code_chaos",
        "clean_desk",
    ]

    def __init__(self, width: int = 640, height: int = 480, initial_scenario: str = "messy_desk"):
        self.width = width
        self.height = height
        self.scenario = initial_scenario if initial_scenario in self.SCENARIOS else "messy_desk"
        self._frame_count = 0
        self._closed = False

    def set_scenario(self, scenario: str) -> None:
        """Switch current synthetic scenario."""
        if scenario in self.SCENARIOS:
            self.scenario = scenario
        else:
            raise ValueError(f"Unknown scenario '{scenario}'. Supported: {self.SCENARIOS}")

    def capture_frame(self) -> Optional[np.ndarray]:
        """Generate a synthetic test frame for the active scenario."""
        if self._closed:
            return None

        self._frame_count += 1
        # Create solid canvas with a subtle room gradient
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Background room color (slate / office wall)
        frame[:, :] = (45, 38, 35)

        # Draw desk surface (bottom 35%)
        desk_y = int(self.height * 0.65)
        frame[desk_y:, :] = (60, 80, 110)  # Wood / dark laminate desk

        # Draw computer monitor in background
        mon_w, mon_h = int(self.width * 0.4), int(self.height * 0.35)
        mon_x = int(self.width * 0.3)
        mon_y = int(desk_y - mon_h - 20)
        # Bezel
        frame[mon_y:mon_y + mon_h, mon_x:mon_x + mon_w] = (30, 30, 30)
        # Screen glow
        screen_inner = frame[mon_y + 10:mon_y + mon_h - 10, mon_x + 10:mon_x + mon_w - 10]
        screen_inner[:] = (120, 95, 60)  # Blue-ish IDE screen glow

        # Add scenario-specific procedural visual elements
        if self.scenario == "messy_desk":
            self._render_messy_desk(frame, desk_y)
        elif self.scenario == "drinking_water":
            self._render_drinking_water(frame, desk_y)
        elif self.scenario == "slouching":
            self._render_slouching(frame, desk_y)
        elif self.scenario == "sharp_outfit":
            self._render_sharp_outfit(frame, desk_y)
        elif self.scenario == "code_chaos":
            self._render_code_chaos(frame, desk_y)
        elif self.scenario == "clean_desk":
            self._render_clean_desk(frame, desk_y)

        # Draw face / head placeholder (simulating user in front of webcam)
        self._render_person_silhouette(frame)

        return frame

    def _render_person_silhouette(self, frame: np.ndarray) -> None:
        """Draw an approximate human silhouette with head and shoulders for face detection."""
        head_cx = int(self.width * 0.5)
        head_cy = int(self.height * 0.45)
        head_r = int(self.height * 0.14)

        if cv2 is not None:
            # Head (skin-tone / silhouette)
            cv2.circle(frame, (head_cx, head_cy), head_r, (160, 180, 210), -1)
            # Eyes
            cv2.circle(frame, (head_cx - 20, head_cy - 10), 6, (40, 40, 40), -1)
            cv2.circle(frame, (head_cx + 20, head_cy - 10), 6, (40, 40, 40), -1)
            # Shoulders
            pts = np.array([
                [head_cx - 100, self.height],
                [head_cx - 60, head_cy + head_r + 20],
                [head_cx + 60, head_cy + head_r + 20],
                [head_cx + 100, self.height]
            ], np.int32)
            cv2.fillPoly(frame, [pts], (80, 50, 40))
        else:
            # Fallback simple rectangle without cv2
            y1, y2 = max(0, head_cy - head_r), min(self.height, head_cy + head_r)
            x1, x2 = max(0, head_cx - head_r), min(self.width, head_cx + head_r)
            frame[y1:y2, x1:x2] = (160, 180, 210)

    def _render_messy_desk(self, frame: np.ndarray, desk_y: int) -> None:
        if cv2 is not None:
            # Coffee mugs scattered
            cv2.rectangle(frame, (100, desk_y + 20), (140, desk_y + 70), (200, 200, 200), -1)
            cv2.rectangle(frame, (160, desk_y + 30), (200, desk_y + 80), (100, 120, 150), -1)
            cv2.rectangle(frame, (480, desk_y + 15), (520, desk_y + 65), (50, 80, 200), -1)
            # Tangled cable lines
            cv2.polylines(frame, [np.array([[50, desk_y + 40], [120, desk_y + 85], [240, desk_y + 50], [350, desk_y + 90]])], False, (20, 20, 20), 3)
            cv2.polylines(frame, [np.array([[400, desk_y + 30], [450, desk_y + 70], [530, desk_y + 45], [600, desk_y + 80]])], False, (10, 10, 10), 3)
            # Crushed snack wrappers
            cv2.rectangle(frame, (230, desk_y + 40), (270, desk_y + 65), (40, 180, 240), -1)

    def _render_drinking_water(self, frame: np.ndarray, desk_y: int) -> None:
        if cv2 is not None:
            # Blue water bottle being raised near face
            bottle_x = int(self.width * 0.55)
            bottle_y = int(self.height * 0.38)
            cv2.rectangle(frame, (bottle_x, bottle_y), (bottle_x + 35, bottle_y + 80), (235, 170, 50), -1)  # Clear cyan bottle
            cv2.rectangle(frame, (bottle_x + 8, bottle_y - 12), (bottle_x + 27, bottle_y), (180, 180, 180), -1)  # Cap
            # Text label watermark for vision prompt clues
            cv2.putText(frame, "WATER BOTTLE (HYDRATING)", (bottle_x - 40, bottle_y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)

    def _render_slouching(self, frame: np.ndarray, desk_y: int) -> None:
        if cv2 is not None:
            cv2.putText(frame, "SPINE ANGLE: 42 DEG SLOUCH", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 50, 255), 2)

    def _render_sharp_outfit(self, frame: np.ndarray, desk_y: int) -> None:
        if cv2 is not None:
            cv2.putText(frame, "OUTFIT: CRISP BLAZER", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50, 200, 50), 2)

    def _render_code_chaos(self, frame: np.ndarray, desk_y: int) -> None:
        if cv2 is not None:
            cv2.putText(frame, "SYNTAX ERROR x99 / STACKOVERFLOW", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    def _render_clean_desk(self, frame: np.ndarray, desk_y: int) -> None:
        if cv2 is not None:
            # Single succulent plant
            cv2.circle(frame, (120, desk_y + 35), 18, (70, 160, 60), -1)
            cv2.rectangle(frame, (110, desk_y + 35), (130, desk_y + 60), (50, 90, 180), -1)

    def is_available(self) -> bool:
        return not self._closed

    def release(self) -> None:
        self._closed = True
