"""Privacy engine for edge frame redaction, face blurring, and screen masking."""

from __future__ import annotations

import base64
import logging
import os
from typing import List, Tuple, Optional
import numpy as np

from roastbot.config import PrivacyMode

logger = logging.getLogger(__name__)

try:
    import cv2
except ImportError:
    cv2 = None  # type: ignore


class PrivacyEngine:
    """Applies edge privacy filters to raw webcam frames before multimodal analysis."""

    def __init__(self, mode: PrivacyMode = PrivacyMode.BLUR_FACES):
        self.mode = mode
        self._face_cascade: Optional[cv2.CascadeClassifier] = None
        self._cascade_loaded = False
        self._init_face_detector()

    def _init_face_detector(self) -> None:
        """Attempt to load OpenCV's default Haar cascade classifier for frontal faces."""
        if cv2 is None:
            return

        try:
            cascade_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
            if os.path.exists(cascade_path):
                self._face_cascade = cv2.CascadeClassifier(cascade_path)
                self._cascade_loaded = not self._face_cascade.empty()
            else:
                logger.warning(f"Haar cascade file not found at {cascade_path}")
        except Exception as e:
            logger.warning(f"Failed to initialize face detector: {e}")
            self._face_cascade = None
            self._cascade_loaded = False

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """Apply active privacy policy to the input image frame."""
        if frame is None or frame.size == 0:
            return frame

        out = frame.copy()

        if self.mode == PrivacyMode.NORMAL or self.mode == PrivacyMode.LOCAL_ONLY:
            return out

        if self.mode == PrivacyMode.BLUR_FACES:
            out = self.blur_faces(out)
        elif self.mode == PrivacyMode.REDACT_SCREENS:
            out = self.redact_screens(out)

        return out

    def blur_faces(self, frame: np.ndarray) -> np.ndarray:
        """Detect and blur human face regions to preserve user privacy."""
        if cv2 is None:
            return frame

        h, w = frame.shape[:2]
        faces: List[Tuple[int, int, int, int]] = []

        if self._cascade_loaded and self._face_cascade is not None:
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                detected = self._face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30)
                )
                if len(detected) > 0:
                    faces = [(int(x), int(y), int(bw), int(bh)) for (x, y, bw, bh) in detected]
            except Exception as e:
                logger.debug(f"Cascade detection error: {e}")

        # If cascade detected nothing (e.g., stylized mock or unusual angle), blur default face zone (center-upper)
        if not faces:
            cx, cy = int(w * 0.5), int(h * 0.45)
            r = int(h * 0.16)
            faces = [(max(0, cx - r), max(0, cy - r), 2 * r, 2 * r)]

        for (x, y, fw, fh) in faces:
            frame = self._apply_gaussian_blur(frame, x, y, fw, fh)

        return frame

    def redact_screens(self, frame: np.ndarray) -> np.ndarray:
        """Blackout likely computer screen region (upper-middle) and mark privacy stamp."""
        h, w = frame.shape[:2]
        # Screen bounding box heuristic (middle 50% width, upper-mid height)
        sx = int(w * 0.25)
        sy = int(h * 0.15)
        sw = int(w * 0.50)
        sh = int(h * 0.45)

        # Blackout rectangle
        frame[sy:sy + sh, sx:sx + sw] = 15

        if cv2 is not None:
            cv2.rectangle(frame, (sx, sy), (sx + sw, sy + sh), (80, 80, 80), 2)
            cv2.putText(
                frame,
                "[SCREEN MASKED - PRIVACY MODE]",
                (sx + 15, sy + int(sh / 2)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 200, 255),
                2
            )
        return frame

    @staticmethod
    def _apply_gaussian_blur(frame: np.ndarray, x: int, y: int, w: int, h: int) -> np.ndarray:
        """Apply heavy blur over the specified subregion."""
        if cv2 is None:
            return frame

        fh, fw = frame.shape[:2]
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(fw, x + w)
        y2 = min(fh, y + h)

        if x2 <= x1 or y2 <= y1:
            return frame

        sub = frame[y1:y2, x1:x2]
        # Heavy kernel for privacy protection
        k = max(25, (min(w, h) // 3) * 2 + 1)
        if k % 2 == 0:
            k += 1
        blurred = cv2.GaussianBlur(sub, (k, k), 30)
        frame[y1:y2, x1:x2] = blurred
        return frame

    @staticmethod
    def encode_to_jpeg(frame: np.ndarray, quality: int = 85) -> bytes:
        """Encode BGR numpy array to JPEG bytes."""
        if cv2 is None:
            raise RuntimeError("OpenCV is required to encode frame to JPEG.")
        success, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        if not success:
            raise RuntimeError("Failed to encode frame to JPEG.")
        return encoded.tobytes()

    @staticmethod
    def encode_to_base64(frame: np.ndarray, quality: int = 85) -> str:
        """Encode frame as base64 string for multimodal payload."""
        jpeg_bytes = PrivacyEngine.encode_to_jpeg(frame, quality)
        return base64.b64encode(jpeg_bytes).decode("ascii")

    @staticmethod
    def decode_from_bytes(data: bytes) -> np.ndarray:
        """Decode JPEG/PNG bytes back into BGR numpy array."""
        if cv2 is None:
            raise RuntimeError("OpenCV is required to decode frame bytes.")
        arr = np.frombuffer(data, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Failed to decode image from provided byte buffer.")
        return frame
