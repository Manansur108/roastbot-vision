"""FastAPI companion server providing REST & WebSocket endpoints and Web UI for RoastBot-Vision."""

from __future__ import annotations

import io
import json
import logging
from typing import Optional, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

from roastbot.config import AppConfig, RoastCategory, RoastSeverity, PrivacyMode, MascotEmotion
from roastbot.engine.roaster import RoastEngine
from roastbot.mascot.sprites import PixelSpriteRenderer
from roastbot.providers.base import VisionAnalysisResult

logger = logging.getLogger(__name__)


class RoastRequest(BaseModel):
    category: Optional[str] = None
    severity: Optional[str] = None


class ConfigUpdateRequest(BaseModel):
    severity: Optional[str] = None
    category: Optional[str] = None
    privacy_mode: Optional[str] = None
    speech_enabled: Optional[bool] = None


class ConnectionManager:
    """Manages connected WebSocket clients for real-time telemetry."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        payload = json.dumps(message)
        for conn in list(self.active_connections):
            try:
                await conn.send_text(payload)
            except Exception:
                self.disconnect(conn)


def create_app(engine: Optional[RoastEngine] = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="RoastBot-Vision Companion API",
        description="Multimodal Vision Sidekick & Desk Critic companion service",
        version="0.1.0",
    )

    # Attach or create roast engine instance
    roast_engine = engine or RoastEngine()
    ws_manager = ConnectionManager()

    # Wire engine event listener to WebSocket broadcaster
    def on_new_roast(result: VisionAnalysisResult):
        import asyncio
        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
        if loop and loop.is_running():
            asyncio.create_task(ws_manager.broadcast({
                "type": "new_roast",
                "data": result.to_dict()
            }))

    roast_engine.add_listener(on_new_roast)

    @app.get("/api/mascot/state")
    def get_mascot_state():
        """Retrieve current mascot emotional state and active dialog."""
        snapshot = roast_engine.mascot.get_snapshot()
        return {
            "emotion": snapshot.emotion.value,
            "dialog": snapshot.current_dialog,
            "mood_score": snapshot.mood_score,
            "is_speaking": snapshot.is_speaking,
            "animation_frame": snapshot.animation_frame,
            "idle_seconds": round(snapshot.idle_seconds, 1),
        }

    @app.get("/api/mascot/sprite")
    def get_mascot_sprite(emotion: Optional[str] = None, scale: int = 8, frame: int = 0):
        """Render and return high-fidelity pixel sprite PNG for requested emotion."""
        target_emotion = MascotEmotion.IDLE
        if emotion:
            try:
                target_emotion = MascotEmotion(emotion.lower())
            except ValueError:
                pass
        else:
            target_emotion = roast_engine.mascot.emotion

        img = PixelSpriteRenderer.render_image(target_emotion, frame_idx=frame, scale=min(max(scale, 1), 16))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return Response(content=buf.getvalue(), media_type="image/png")

    @app.get("/api/camera/preview")
    def get_camera_preview():
        """Capture single frame with privacy filters applied and return JPEG preview."""
        jpeg_bytes = roast_engine.capture_preview()
        return Response(content=jpeg_bytes, media_type="image/jpeg")

    @app.get("/api/stats")
    def get_stats():
        """Get running performance metrics and roast counts."""
        return roast_engine.get_stats()

    @app.get("/api/history")
    def get_history():
        """Get recent roast history."""
        return [r.to_dict() for r in reversed(roast_engine.history[-25:])]

    @app.post("/api/roast")
    async def trigger_roast(req: Optional[RoastRequest] = None):
        """Trigger an immediate camera snapshot and vision roast evaluation."""
        cat: Optional[RoastCategory] = None
        sev: Optional[RoastSeverity] = None

        if req and req.category:
            try:
                cat = RoastCategory(req.category)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid category '{req.category}'")

        if req and req.severity:
            try:
                sev = RoastSeverity(req.severity)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid severity '{req.severity}'")

        result = await roast_engine.roast_now(category=cat, severity=sev)
        return result.to_dict()

    @app.post("/api/speech/toggle")
    def toggle_speech():
        """Toggle text-to-speech mute status."""
        new_mute = roast_engine.speech.toggle_mute()
        return {"muted": new_mute, "speech_enabled": not new_mute}

    @app.post("/api/config")
    def update_config(req: ConfigUpdateRequest):
        """Update runtime roasting options."""
        if req.severity:
            try:
                roast_engine.config.severity = RoastSeverity(req.severity)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid severity '{req.severity}'")

        if req.category:
            try:
                roast_engine.config.category = RoastCategory(req.category)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid category '{req.category}'")

        if req.privacy_mode:
            try:
                new_pm = PrivacyMode(req.privacy_mode)
                roast_engine.config.privacy_mode = new_pm
                roast_engine.privacy.mode = new_pm
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid privacy mode '{req.privacy_mode}'")

        if req.speech_enabled is not None:
            roast_engine.config.speech_enabled = req.speech_enabled
            roast_engine.speech.set_muted(not req.speech_enabled)

        return roast_engine.get_stats()

    @app.websocket("/ws/mascot")
    async def websocket_mascot_feed(websocket: WebSocket):
        """Live telemetry WebSocket for real-time client UI synchronization."""
        await ws_manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                # Handle client ping or manual roast trigger over websocket
                try:
                    payload = json.loads(data)
                    if payload.get("action") == "roast":
                        await roast_engine.roast_now()
                except Exception:
                    pass
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)

    @app.get("/", response_class=HTMLResponse)
    def index():
        """Serve the companion web dashboard."""
        return HTML_DASHBOARD_TEMPLATE

    return app


HTML_DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RoastBot-Vision | Real-Time Multimodal Desk Critic</title>
  <style>
    :root {
      --bg: #0d1117;
      --card-bg: #161b22;
      --border: #30363d;
      --accent: #58a6ff;
      --accent-hover: #1f6feb;
      --roast-red: #f85149;
      --gold: #f1e05a;
      --cyan: #38bdf8;
      --text: #c9d1d9;
      --text-bright: #f0f6fc;
      --font: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg);
      color: var(--text);
      font-family: var(--font);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    header {
      background: var(--card-bg);
      border-bottom: 1px solid var(--border);
      padding: 1rem 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 1.4rem;
      font-weight: 700;
      color: var(--text-bright);
    }
    .badge {
      background: rgba(88, 166, 255, 0.15);
      color: var(--accent);
      padding: 4px 10px;
      border-radius: 12px;
      font-size: 0.75rem;
      border: 1px solid rgba(88, 166, 255, 0.3);
    }
    main {
      flex: 1;
      padding: 2rem;
      max-width: 1300px;
      margin: 0 auto;
      width: 100%;
      display: grid;
      grid-template-columns: 420px 1fr;
      gap: 2rem;
    }
    .panel {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.5rem;
      box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }
    .mascot-stage {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      position: relative;
    }
    .mascot-avatar {
      width: 192px;
      height: 192px;
      image-rendering: pixelated;
      margin-bottom: 1rem;
      filter: drop-shadow(0 10px 15px rgba(0,0,0,0.5));
      animation: hover-bob 2.5s ease-in-out infinite alternate;
    }
    @keyframes hover-bob {
      0% { transform: translateY(0px); }
      100% { transform: translateY(-8px); }
    }
    .speech-bubble {
      background: #21262d;
      border: 2px solid var(--border);
      border-radius: 16px;
      padding: 1.2rem;
      position: relative;
      margin-top: 0.5rem;
      width: 100%;
      min-height: 80px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.05rem;
      font-weight: 500;
      color: var(--text-bright);
      line-height: 1.4;
    }
    .speech-bubble::before {
      content: '';
      position: absolute;
      top: -12px;
      left: 50%;
      transform: translateX(-50%);
      border-width: 0 12px 12px 12px;
      border-style: solid;
      border-color: transparent transparent #21262d transparent;
    }
    .controls {
      display: flex;
      flex-direction: column;
      gap: 1rem;
      margin-top: 1.5rem;
      width: 100%;
    }
    .btn {
      background: var(--accent);
      color: white;
      border: none;
      padding: 12px 20px;
      border-radius: 8px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: all 0.2s ease;
    }
    .btn:hover { background: var(--accent-hover); transform: translateY(-1px); }
    .btn-roast {
      background: linear-gradient(135deg, #f85149, #da3633);
      font-size: 1.1rem;
      padding: 14px;
      box-shadow: 0 4px 14px rgba(248, 81, 73, 0.4);
    }
    .btn-roast:hover { background: linear-gradient(135deg, #ff6e67, #e03e3a); }
    .btn-secondary {
      background: #21262d;
      border: 1px solid var(--border);
      color: var(--text);
    }
    .btn-secondary:hover { background: #30363d; color: var(--text-bright); }
    .form-group {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    label { font-size: 0.85rem; font-weight: 600; color: #8b949e; text-transform: uppercase; }
    select {
      background: #0d1117;
      border: 1px solid var(--border);
      color: var(--text-bright);
      padding: 10px;
      border-radius: 6px;
      font-size: 0.95rem;
      outline: none;
    }
    .camera-panel {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }
    .preview-box {
      width: 100%;
      height: 280px;
      background: #0d1117;
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
    }
    .preview-img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1rem;
    }
    .stat-card {
      background: #0d1117;
      border: 1px solid var(--border);
      padding: 1rem;
      border-radius: 8px;
      text-align: center;
    }
    .stat-value {
      font-size: 1.8rem;
      font-weight: 700;
      color: var(--text-bright);
    }
    .stat-label {
      font-size: 0.75rem;
      color: #8b949e;
      text-transform: uppercase;
      margin-top: 4px;
    }
    .history-feed {
      margin-top: 1rem;
      max-height: 220px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .history-item {
      background: #0d1117;
      border: 1px solid var(--border);
      padding: 10px 14px;
      border-radius: 6px;
      font-size: 0.9rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .history-text { color: var(--text-bright); flex: 1; margin-right: 12px; }
    .history-tag { font-size: 0.75rem; color: #8b949e; }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <span>🤖 RoastBot-Vision</span>
      <span class="badge">Edge Vision AI</span>
    </div>
    <div style="display:flex; gap: 12px; align-items:center;">
      <button id="muteBtn" class="btn btn-secondary" onclick="toggleMute()">🔊 Audio On</button>
      <span id="mascotMoodBadge" class="badge" style="color:var(--gold); border-color:var(--gold);">Mood: 75%</span>
    </div>
  </header>

  <main>
    <!-- Mascot & Immediate Action Column -->
    <div class="panel mascot-stage">
      <img id="mascotImg" class="mascot-avatar" src="/api/mascot/sprite?scale=8" alt="Bytey the Sentry Mascot">
      <div id="speechBubble" class="speech-bubble">
        "Point your camera at your desk. I dare you."
      </div>

      <div class="controls">
        <button id="roastBtn" class="btn btn-roast" onclick="triggerRoast()">
          🔥 ROAST MY DESK NOW!
        </button>

        <div class="form-group">
          <label>Roast Severity Level</label>
          <select id="severitySelect" onchange="updateSettings()">
            <option value="gentle">Gentle Ribbing (Friendly Teasing)</option>
            <option value="snarky" selected>Snarky Dev (Sarcastic Senior Eng)</option>
            <option value="savage">Savage Mode (Brutal Comedy Burns)</option>
            <option value="gordon_ramsay">Gordon Ramsay (FULL RAGE)</option>
          </select>
        </div>

        <div class="form-group">
          <label>Evaluation Target</label>
          <select id="categorySelect" onchange="updateSettings()">
            <option value="general_roast" selected>General Workspace Critic</option>
            <option value="desk_clutter">Desk Clutter & Cable Spaghetti</option>
            <option value="posture_check">Posture & Ergonomics Inspector</option>
            <option value="drip_check">Outfit & Drip Check</option>
            <option value="hydration_hero">Hydration Hero (Water Celebration)</option>
            <option value="code_roast">Code & Terminal Chaos</option>
            <option value="caffeine_radar">Caffeine & Mug Graveyard</option>
          </select>
        </div>

        <div class="form-group">
          <label>Privacy Masking</label>
          <select id="privacySelect" onchange="updateSettings()">
            <option value="blur_faces" selected>Blur Faces (Edge Privacy)</option>
            <option value="redact_screens">Redact Screens (Blackout Displays)</option>
            <option value="normal">Unredacted (Full Frame)</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Feed, Preview & Telemetry Column -->
    <div class="panel camera-panel">
      <div>
        <h3 style="color:var(--text-bright); margin-bottom: 0.75rem;">📷 Live Frame with Privacy Redaction</h3>
        <div class="preview-box">
          <img id="camPreview" class="preview-img" src="/api/camera/preview" alt="Privacy-Filtered Camera Preview">
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div id="totalRoasts" class="stat-value">0</div>
          <div class="stat-label">Total Roasts</div>
        </div>
        <div class="stat-card">
          <div id="totalCelebs" class="stat-value" style="color: var(--cyan);">0</div>
          <div class="stat-label">Hydration Sips</div>
        </div>
        <div class="stat-card">
          <div id="avgScore" class="stat-value" style="color: var(--gold);">50</div>
          <div class="stat-label">Avg Desk Score</div>
        </div>
      </div>

      <div>
        <h3 style="color:var(--text-bright); margin-bottom: 0.5rem;">📜 Recent Commentary Log</h3>
        <div id="historyFeed" class="history-feed">
          <div class="history-item">
            <span class="history-text">Ready for inspection. Click Roast to begin.</span>
            <span class="history-tag">READY</span>
          </div>
        </div>
      </div>
    </div>
  </main>

  <script>
    let isMuted = false;

    async function triggerRoast() {
      const roastBtn = document.getElementById('roastBtn');
      const speech = document.getElementById('speechBubble');
      const mascot = document.getElementById('mascotImg');

      roastBtn.disabled = true;
      roastBtn.innerText = "🔍 SCANNING DESK...";
      speech.innerText = "Analyzing pixels with multimodal models...";
      mascot.src = "/api/mascot/sprite?emotion=thinking&scale=8";

      try {
        const cat = document.getElementById('categorySelect').value;
        const sev = document.getElementById('severitySelect').value;
        const res = await fetch('/api/roast', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ category: cat, severity: sev })
        });
        const data = await res.json();

        speech.innerText = `"${data.roast}"`;
        mascot.src = `/api/mascot/sprite?emotion=${data.emotion}&scale=8`;
        refreshData();
      } catch (err) {
        speech.innerText = "Roast failed: " + err;
      } finally {
        roastBtn.disabled = false;
        roastBtn.innerText = "🔥 ROAST MY DESK NOW!";
      }
    }

    async function updateSettings() {
      const sev = document.getElementById('severitySelect').value;
      const cat = document.getElementById('categorySelect').value;
      const priv = document.getElementById('privacySelect').value;
      await fetch('/api/config', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ severity: sev, category: cat, privacy_mode: priv })
      });
      refreshPreview();
    }

    async function toggleMute() {
      const res = await fetch('/api/speech/toggle', { method: 'POST' });
      const data = await res.json();
      const btn = document.getElementById('muteBtn');
      if (data.muted) {
        btn.innerText = "🔇 Muted";
        btn.style.color = "#f85149";
      } else {
        btn.innerText = "🔊 Audio On";
        btn.style.color = "";
      }
    }

    async function refreshPreview() {
      const cam = document.getElementById('camPreview');
      cam.src = '/api/camera/preview?t=' + Date.now();
    }

    async function refreshData() {
      refreshPreview();
      const statsRes = await fetch('/api/stats');
      const stats = await statsRes.json();
      document.getElementById('totalRoasts').innerText = stats.total_roasts || 0;
      document.getElementById('totalCelebs').innerText = stats.total_celebrations || 0;
      document.getElementById('avgScore').innerText = stats.average_score || 50;
      document.getElementById('mascotMoodBadge').innerText = `Mood: ${stats.mascot_mood}%`;

      const histRes = await fetch('/api/history');
      const hist = await histRes.json();
      const feed = document.getElementById('historyFeed');
      if (hist.length > 0) {
        feed.innerHTML = hist.map(h => `
          <div class="history-item">
            <span class="history-text">"${h.roast}"</span>
            <span class="history-tag">${h.category.toUpperCase()} (${h.score}/100)</span>
          </div>
        `).join('');
      }
    }

    // Refresh telemetry periodically
    setInterval(refreshData, 5000);
    refreshData();
  </script>
</body>
</html>
"""
