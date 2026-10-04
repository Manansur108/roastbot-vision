"""Desktop overlay companion GUI module."""

from roastbot.gui.qt_overlay import PYQT_AVAILABLE, RoastBotOverlayWidget, launch_overlay_app
from roastbot.gui.tk_overlay import TK_AVAILABLE, TkRoastBotOverlay

__all__ = ["PYQT_AVAILABLE", "RoastBotOverlayWidget", "launch_overlay_app", "TK_AVAILABLE", "TkRoastBotOverlay"]
