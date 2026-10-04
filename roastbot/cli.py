"""Rich Command-Line Interface for RoastBot-Vision."""

from __future__ import annotations

import asyncio
import logging
import sys
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from roastbot.config import AppConfig, RoastCategory, RoastSeverity, PrivacyMode, MascotEmotion
from roastbot.engine.roaster import RoastEngine
from roastbot.mascot.sprites import PixelSpriteRenderer

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="roastbot")
def main() -> None:
    """RoastBot-Vision: Real-Time Multimodal Vision Sidekick & Desk Critic."""
    pass


@main.command(name="roast")
@click.option("--category", "-c", type=click.Choice([c.value for c in RoastCategory]), default=RoastCategory.GENERAL_ROAST.value, help="Roast evaluation category.")
@click.option("--severity", "-s", type=click.Choice([s.value for s in RoastSeverity]), default=RoastSeverity.SNARKY.value, help="Roast severity intensity.")
@click.option("--privacy", "-p", type=click.Choice([p.value for p in PrivacyMode]), default=PrivacyMode.BLUR_FACES.value, help="Camera privacy redaction mode.")
@click.option("--mute", is_flag=True, default=False, help="Mute speech synthesis audio output.")
@click.option("--mock-cam", is_flag=True, default=False, help="Use synthetic test camera.")
def roast_command(category: str, severity: str, privacy: str, mute: bool, mock_cam: bool) -> None:
    """Capture a webcam frame and roast the workspace immediately."""
    config = AppConfig(
        category=RoastCategory(category),
        severity=RoastSeverity(severity),
        privacy_mode=PrivacyMode(privacy),
        speech_enabled=not mute,
        use_mock_camera=mock_cam,
    )

    console.print("\n[bold cyan]🤖 Bytey the Sentry Bot is initializing optics...[/bold cyan]")
    engine = RoastEngine(config=config)

    async def _execute():
        result = await engine.roast_now()
        ascii_art = PixelSpriteRenderer.render_ascii(result.emotion)

        # Build terminal display
        grid_table = Table.grid(padding=2)
        grid_table.add_column()
        grid_table.add_column()

        tag_color = "green" if result.is_celebration else ("red" if result.severity == RoastSeverity.GORDON_RAMSAY else "yellow")
        badge = f"[{tag_color} bold]{result.category.value.upper()}[/{tag_color} bold] | Score: [bold]{result.score}/100[/bold] | Severity: [bold]{result.severity.value}[/bold]"

        content = f"{badge}\n\n[bold white]\"{result.roast}\"[/bold white]\n\n"
        if result.detected_items:
            content += f"[dim]Observed:[/dim] [cyan]{', '.join(result.detected_items)}[/cyan]\n"
        content += f"[dim]Provider:[/dim] [magenta]{result.provider_name}[/magenta]"

        panel = Panel(
            content,
            title=f"Bytey ({result.emotion.value.upper()})",
            border_style=tag_color,
            expand=False,
        )

        grid_table.add_row(f"[cyan]{ascii_art}[/cyan]", panel)
        console.print(grid_table)

    try:
        asyncio.run(_execute())
    finally:
        engine.close()


@main.command(name="serve")
@click.option("--host", default="127.0.0.1", help="FastAPI companion server host.")
@click.option("--port", default=8420, help="FastAPI companion server port.")
@click.option("--mock-cam", is_flag=True, default=False, help="Force mock camera.")
def serve_command(host: str, port: int, mock_cam: bool) -> None:
    """Launch the companion web server and dashboard."""
    import uvicorn
    from roastbot.server.app import create_app

    config = AppConfig(server_host=host, server_port=port, use_mock_camera=mock_cam)
    engine = RoastEngine(config=config)
    app = create_app(engine)

    console.print(f"[bold green]🚀 RoastBot-Vision Web Companion running at http://{host}:{port}[/bold green]")
    try:
        uvicorn.run(app, host=host, port=port, log_level="info")
    finally:
        engine.close()


@main.command(name="overlay")
@click.option("--tk", is_flag=True, default=False, help="Force Tkinter fallback overlay instead of PyQt6.")
@click.option("--mock-cam", is_flag=True, default=False, help="Force mock camera.")
def overlay_command(tk: bool, mock_cam: bool) -> None:
    """Launch the floating transparent desktop mascot widget."""
    from roastbot.gui import PYQT_AVAILABLE, launch_overlay_app, TK_AVAILABLE, TkRoastBotOverlay

    config = AppConfig(use_mock_camera=mock_cam)
    engine = RoastEngine(config=config)

    if not tk and PYQT_AVAILABLE:
        console.print("[bold cyan]Launching PyQt6 transparent desktop mascot...[/bold cyan]")
        try:
            launch_overlay_app(engine)
        finally:
            engine.close()
    elif TK_AVAILABLE:
        console.print("[bold yellow]Launching Tkinter transparent desktop mascot...[/bold yellow]")
        tk_app = TkRoastBotOverlay(engine)
        try:
            tk_app.run()
        finally:
            engine.close()
    else:
        console.print("[bold red]Neither PyQt6 nor Tkinter is available on this system.[/bold red]")


@main.command(name="mascot")
def mascot_command() -> None:
    """Preview Bytey's expressive pixel sprite gallery in the terminal."""
    console.print("\n[bold cyan]=== BYTEY THE SENTRY MASCOT EXPRESSION GALLERY ===[/bold cyan]\n")
    for emo in MascotEmotion:
        ascii_art = PixelSpriteRenderer.render_ascii(emo)
        p = Panel(f"[cyan]{ascii_art}[/cyan]", title=f"[bold yellow]{emo.value.upper()}[/bold yellow]", width=34)
        console.print(p)


@main.command(name="demo")
def demo_command() -> None:
    """Run an automated comedic desk critic demonstration."""
    console.print("\n[bold magenta]🎬 Welcome to the RoastBot-Vision Showcase Demo![/bold magenta]\n")
    config = AppConfig(use_mock_camera=True, speech_enabled=False)
    engine = RoastEngine(config=config)

    scenarios = [
        ("Drinking water celebration!", RoastCategory.HYDRATION_HERO, RoastSeverity.GENTLE),
        ("Cable spaghetti inspection!", RoastCategory.DESK_CLUTTER, RoastSeverity.SAVAGE),
        ("Spine curvature check!", RoastCategory.POSTURE_CHECK, RoastSeverity.SNARKY),
        ("Gordon Ramsay enters the chat!", RoastCategory.DESK_CLUTTER, RoastSeverity.GORDON_RAMSAY),
    ]

    async def run_demo():
        for desc, cat, sev in scenarios:
            console.print(f"[bold cyan]▶ Testing scenario: {desc}[/bold cyan]")
            res = await engine.roast_now(category=cat, severity=sev)
            console.print(f"[bold white]Bytey ({res.emotion.value}):[/bold white] \"{res.roast}\"")
            console.print(f"[dim]Score: {res.score}/100 | Items: {res.detected_items}[/dim]\n")
            await asyncio.sleep(0.5)

    try:
        asyncio.run(run_demo())
        console.print("[bold green]✔ Demo completed successfully![/bold green]\n")
    finally:
        engine.close()


if __name__ == "__main__":
    main()
