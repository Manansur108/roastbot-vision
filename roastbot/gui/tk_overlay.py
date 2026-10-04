"""Tkinter lightweight transparent overlay fallback widget."""

from __future__ import annotations

import asyncio
import logging
import threading
from typing import Optional
from roastbot.engine.roaster import RoastEngine
from roastbot.mascot.sprites import PixelSpriteRenderer

logger = logging.getLogger(__name__)

try:
    import tkinter as tk
    from PIL import ImageTk
    TK_AVAILABLE = True
except ImportError:
    TK_AVAILABLE = False


class TkRoastBotOverlay:
    """Tkinter-based floating companion widget for environments without PyQt6."""

    def __init__(self, engine: RoastEngine):
        if not TK_AVAILABLE:
            raise RuntimeError("Tkinter and PIL ImageTk are required for TkRoastBotOverlay.")

        self.engine = engine
        self.root = tk.Tk()
        self.root.title("RoastBot")
        self.root.geometry("340x280+100+100")
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)  # Frameless window
        self.root.config(bg="#161b22")

        self._drag_data = {"x": 0, "y": 0}
        self._init_ui()
        self._schedule_tick()

    def _init_ui(self) -> None:
        # Header / close bar
        top_bar = tk.Frame(self.root, bg="#161b22")
        top_bar.pack(fill="x", padx=6, pady=4)

        title_lbl = tk.Label(top_bar, text="🤖 Bytey Desk Critic", bg="#161b22", fg="#38bdf8", font=("Helvetica", 9, "bold"))
        title_lbl.pack(side="left")

        close_btn = tk.Button(top_bar, text="✕", bg="#161b22", fg="#8b949e", bd=0, command=self.root.destroy)
        close_btn.pack(side="right")

        # Speech dialog label
        self.dialog_lbl = tk.Label(
            self.root,
            text="Point webcam at your desk for inspection.",
            bg="#21262d",
            fg="#f0f6fc",
            wraplength=300,
            font=("Helvetica", 10),
            padx=8,
            pady=8,
            relief="groove",
        )
        self.dialog_lbl.pack(fill="x", padx=12, pady=6)

        # Mascot sprite canvas
        self.canvas = tk.Canvas(self.root, width=128, height=128, bg="#161b22", highlightthickness=0)
        self.canvas.pack(pady=4)

        # Drag handlers
        self.canvas.bind("<ButtonPress-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._on_drag)

        # Action button bar
        btn_bar = tk.Frame(self.root, bg="#161b22")
        btn_bar.pack(fill="x", padx=12, pady=6)

        self.roast_btn = tk.Button(
            btn_bar,
            text="🔥 Roast Now",
            bg="#f85149",
            fg="white",
            font=("Helvetica", 9, "bold"),
            command=self._on_roast_clicked,
            relief="flat",
        )
        self.roast_btn.pack(side="left", fill="x", expand=True, padx=2)

        self.mute_btn = tk.Button(
            btn_bar,
            text="🔊",
            bg="#21262d",
            fg="white",
            command=self._on_mute_clicked,
            relief="flat",
        )
        self.mute_btn.pack(side="right", padx=2)

    def _start_drag(self, event) -> None:
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _on_drag(self, event) -> None:
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    def _schedule_tick(self) -> None:
        snapshot = self.engine.mascot.tick()

        if snapshot.current_dialog:
            self.dialog_lbl.config(text=snapshot.current_dialog)
        else:
            self.dialog_lbl.config(text="Listening & observing your desk...")

        # Render sprite
        img = PixelSpriteRenderer.render_image(snapshot.emotion, frame_idx=snapshot.animation_frame, scale=5)
        self._tk_img = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.create_image(64, 64, image=self._tk_img)

        self.root.after(60, self._schedule_tick)

    def _on_roast_clicked(self) -> None:
        self.roast_btn.config(state="disabled", text="Scanning...")

        def runner():
            asyncio.run(self.engine.roast_now())
            self.root.after(0, lambda: self.roast_btn.config(state="normal", text="🔥 Roast Now"))

        threading.Thread(target=runner, daemon=True).start()

    def _on_mute_clicked(self) -> None:
        new_muted = self.engine.speech.toggle_mute()
        self.mute_btn.config(text="🔇" if new_muted else "🔊")

    def run(self) -> None:
        self.root.mainloop()
