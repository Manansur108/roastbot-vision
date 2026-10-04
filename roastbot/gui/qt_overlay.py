"""PyQt6 transparent always-on-top desktop companion overlay widget."""

from __future__ import annotations

import io
import logging
from typing import Optional
from roastbot.config import MascotEmotion, RoastSeverity, RoastCategory
from roastbot.engine.roaster import RoastEngine
from roastbot.mascot.sprites import PixelSpriteRenderer

logger = logging.getLogger(__name__)

try:
    from PyQt6.QtCore import Qt, QTimer, QPoint
    from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QFont, QCursor
    from PyQt6.QtWidgets import (
        QApplication,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QGraphicsDropShadowEffect,
    )
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


class RoastBotOverlayWidget(QWidget):  # type: ignore[misc]
    """Transparent, frameless, always-on-top mascot widget."""

    def __init__(self, engine: RoastEngine, parent: Optional[QWidget] = None):
        if not PYQT_AVAILABLE:
            raise RuntimeError("PyQt6 is required to instantiate RoastBotOverlayWidget.")

        super().__init__(parent)
        self.engine = engine
        self.drag_position = QPoint()

        # Window flags for transparent, always-on-top floating desk companion
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(360, 320)

        self._init_ui()
        self._init_timer()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(6)

        # Speech bubble label
        self.speech_label = QLabel("Hey there! Point your camera at your desk.")
        self.speech_label.setWordWrap(True)
        self.speech_label.setStyleSheet(
            """
            QLabel {
                background-color: #1e222d;
                color: #f0f6fc;
                border: 2px solid #38bdf8;
                border-radius: 12px;
                padding: 10px 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                font-weight: 600;
            }
            """
        )
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 4)
        self.speech_label.setGraphicsEffect(shadow)
        main_layout.addWidget(self.speech_label)

        # Mascot Sprite display
        mascot_layout = QHBoxLayout()
        mascot_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.mascot_label = QLabel()
        self.mascot_label.setFixedSize(140, 140)
        self.mascot_label.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        mascot_layout.addWidget(self.mascot_label)
        main_layout.addLayout(mascot_layout)

        # Control HUD bar
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(6)

        self.roast_btn = QPushButton("🔥 Roast Now")
        self.roast_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #f85149;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #da3633; }
            QPushButton:disabled { background-color: #555; }
            """
        )
        self.roast_btn.clicked.connect(self._on_roast_clicked)
        controls_layout.addWidget(self.roast_btn)

        self.mute_btn = QPushButton("🔊" if not self.engine.speech.muted else "🔇")
        self.mute_btn.setFixedWidth(36)
        self.mute_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #21262d;
                color: white;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 6px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #30363d; }
            """
        )
        self.mute_btn.clicked.connect(self._on_mute_clicked)
        controls_layout.addWidget(self.mute_btn)

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedWidth(28)
        self.close_btn.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: #8b949e;
                border: none;
                border-radius: 6px;
                padding: 6px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #f85149; color: white; }
            """
        )
        self.close_btn.clicked.connect(self.close)
        controls_layout.addWidget(self.close_btn)

        main_layout.addLayout(controls_layout)

    def _init_timer(self) -> None:
        """Start animation tick timer at ~20fps."""
        self.anim_timer = QTimer(self)
        self.anim_timer.setInterval(50)
        self.anim_timer.timeout.connect(self._on_tick)
        self.anim_timer.start()

    def _on_tick(self) -> None:
        """Update mascot frame and dialog text from state machine."""
        snapshot = self.engine.mascot.tick()

        # Update speech bubble
        if snapshot.current_dialog:
            self.speech_label.setText(snapshot.current_dialog)
            self.speech_label.setVisible(True)
        else:
            self.speech_label.setVisible(False)

        # Render current mascot sprite
        img = PixelSpriteRenderer.render_image(
            snapshot.emotion,
            frame_idx=snapshot.animation_frame,
            scale=5,
        )
        # Convert PIL Image to QPixmap
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qimg = QImage()
        qimg.loadFromData(buf.getvalue(), "PNG")
        self.mascot_label.setPixmap(QPixmap.fromImage(qimg))

    def _on_roast_clicked(self) -> None:
        """Trigger immediate async roast."""
        import asyncio

        self.roast_btn.setEnabled(False)
        self.roast_btn.setText("Scanning...")

        def run_async():
            asyncio.run(self.engine.roast_now())
            self.roast_btn.setEnabled(True)
            self.roast_btn.setText("🔥 Roast Now")

        # Run roast task in background thread
        import threading
        t = threading.Thread(target=run_async, daemon=True)
        t.start()

    def _on_mute_clicked(self) -> None:
        new_muted = self.engine.speech.toggle_mute()
        self.mute_btn.setText("🔇" if new_muted else "🔊")

    # Mouse drag window handlers
    def mousePressEvent(self, event) -> None:  # type: ignore
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.mascot_label.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            event.accept()

    def mouseMoveEvent(self, event) -> None:  # type: ignore
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:  # type: ignore
        self.mascot_label.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        event.accept()


def launch_overlay_app(engine: RoastEngine) -> None:
    """Launch the standalone Qt event loop with the desktop overlay widget."""
    if not PYQT_AVAILABLE:
        raise RuntimeError("PyQt6 is not available.")

    app = QApplication.instance() or QApplication([])
    widget = RoastBotOverlayWidget(engine)
    widget.show()
    app.exec()
