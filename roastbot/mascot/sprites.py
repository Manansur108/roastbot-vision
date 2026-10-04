"""Procedural pixel art sprite generator and multi-format renderer for Bytey the Sentry Mascot."""

from __future__ import annotations

from typing import List, Tuple
from PIL import Image
from roastbot.config import MascotEmotion

RGBA = Tuple[int, int, int, int]

# Palette constants
TRANSPARENT: RGBA = (0, 0, 0, 0)
CHASSIS_DARK: RGBA = (38, 43, 62, 255)
CHASSIS_BASE: RGBA = (55, 62, 88, 255)
CHASSIS_LIGHT: RGBA = (82, 92, 126, 255)
BEZEL: RGBA = (24, 26, 38, 255)
SCREEN_BG: RGBA = (18, 22, 33, 255)
GLOW_CYAN: RGBA = (72, 226, 251, 255)
GLOW_AMBER: RGBA = (255, 179, 71, 255)
GLOW_RED: RGBA = (255, 75, 75, 255)
GLOW_GOLD: RGBA = (255, 223, 80, 255)
GLOW_PURPLE: RGBA = (210, 110, 255, 255)
WHITE: RGBA = (255, 255, 255, 255)
THRUSTER_ORANGE: RGBA = (255, 120, 30, 255)
THRUSTER_YELLOW: RGBA = (255, 230, 80, 255)


class PixelSpriteRenderer:
    """Generates procedural 24x24 retro pixel art frames for Bytey the Sentry Mascot."""

    WIDTH = 24
    HEIGHT = 24

    @classmethod
    def generate_frame(cls, emotion: MascotEmotion, frame_idx: int = 0) -> List[List[RGBA]]:
        """Construct the 24x24 RGBA pixel grid for the designated emotion and animation tick."""
        grid: List[List[RGBA]] = [[TRANSPARENT for _ in range(cls.WIDTH)] for _ in range(cls.HEIGHT)]

        # Bobbing hover offset (0 or 1 pixel vertical bounce)
        bob = 1 if (frame_idx % 4 >= 2) else 0

        # Antenna light color based on emotion
        if emotion == MascotEmotion.ROASTING:
            antenna_color = GLOW_RED
        elif emotion == MascotEmotion.CELEBRATING:
            antenna_color = GLOW_GOLD if (frame_idx % 2 == 0) else GLOW_PURPLE
        elif emotion == MascotEmotion.THINKING:
            antenna_color = GLOW_AMBER if (frame_idx % 2 == 0) else GLOW_CYAN
        elif emotion == MascotEmotion.SHOCKED:
            antenna_color = WHITE if (frame_idx % 2 == 0) else GLOW_RED
        elif emotion == MascotEmotion.SLEEPING:
            antenna_color = (60, 60, 80, 255)
        else:
            antenna_color = GLOW_CYAN

        # Draw antenna (rows 1 to 4 + bob)
        ant_x = 11
        ant_y = 1 + bob
        # Antenna bulb
        grid[ant_y][ant_x] = antenna_color
        grid[ant_y][ant_x + 1] = antenna_color
        # Stem
        grid[ant_y + 1][ant_x] = CHASSIS_DARK
        grid[ant_y + 2][ant_x] = CHASSIS_DARK

        # Draw Monitor Chassis (rows 4+bob to 16+bob, cols 4 to 19)
        top_y = 4 + bob
        bot_y = 16 + bob
        for y in range(top_y, bot_y + 1):
            for x in range(4, 20):
                # Rounded corners
                if (y == top_y or y == bot_y) and (x in (4, 19)):
                    continue
                # Highlight top and left edges
                if y == top_y or x == 4:
                    grid[y][x] = CHASSIS_LIGHT
                elif y == bot_y or x == 19:
                    grid[y][x] = CHASSIS_DARK
                else:
                    grid[y][x] = CHASSIS_BASE

        # Bezel border (rows 6+bob to 14+bob, cols 6 to 17)
        for y in range(6 + bob, 15 + bob):
            for x in range(6, 18):
                grid[y][x] = BEZEL

        # CRT Screen background (rows 7+bob to 13+bob, cols 7 to 16)
        screen_y_start = 7 + bob
        screen_y_end = 13 + bob
        screen_x_start = 7
        screen_x_end = 16

        screen_bg = SCREEN_BG
        if emotion == MascotEmotion.ROASTING:
            screen_bg = (40, 15, 20, 255)
        elif emotion == MascotEmotion.CELEBRATING:
            screen_bg = (20, 30, 45, 255)

        for y in range(screen_y_start, screen_y_end + 1):
            for x in range(screen_x_start, screen_x_end + 1):
                grid[y][x] = screen_bg

        # Render Emotion Eyes and Facial Features
        cls._render_face_features(grid, emotion, screen_y_start, screen_x_start, frame_idx)

        # Neck and hover thruster (rows 17+bob to 21+bob)
        neck_y = 17 + bob
        for x in range(10, 14):
            grid[neck_y][x] = CHASSIS_DARK
            grid[neck_y + 1][x] = CHASSIS_LIGHT

        # Thruster jet flames (flickering rows 19+bob to 22+bob)
        thrust_y = neck_y + 2
        flicker = (frame_idx % 3)
        if emotion != MascotEmotion.SLEEPING:
            for x in range(10, 14):
                grid[thrust_y][x] = THRUSTER_ORANGE
            if flicker == 0:
                grid[thrust_y + 1][11] = THRUSTER_YELLOW
                grid[thrust_y + 1][12] = THRUSTER_YELLOW
            elif flicker == 1:
                grid[thrust_y + 1][10] = THRUSTER_YELLOW
                grid[thrust_y + 1][13] = THRUSTER_YELLOW
                grid[thrust_y + 2][11] = THRUSTER_ORANGE
            else:
                grid[thrust_y + 1][11] = THRUSTER_ORANGE
                grid[thrust_y + 1][12] = THRUSTER_ORANGE

        # Particle effects / FX around the mascot
        cls._render_fx(grid, emotion, bob, frame_idx)

        return grid

    @classmethod
    def _render_face_features(cls, grid: List[List[RGBA]], emotion: MascotEmotion, sy: int, sx: int, frame_idx: int) -> None:
        """Render distinct expressive eyes, eyebrows, and mouths on the CRT screen."""
        if emotion == MascotEmotion.IDLE:
            # Friendly cyan eyes: blink on frame_idx % 20 == 0
            eye_color = GLOW_CYAN
            blinking = (frame_idx % 16 == 0)
            if blinking:
                # Closed line
                grid[sy + 3][sx + 2] = eye_color
                grid[sy + 3][sx + 3] = eye_color
                grid[sy + 3][sx + 6] = eye_color
                grid[sy + 3][sx + 7] = eye_color
            else:
                # Open 2x2 eyes
                for dy in (2, 3):
                    for dx in (2, 3):
                        grid[sy + dy][sx + dx] = eye_color
                    for dx in (6, 7):
                        grid[sy + dy][sx + dx] = eye_color
                # Tiny smile
                grid[sy + 5][sx + 4] = eye_color
                grid[sy + 5][sx + 5] = eye_color

        elif emotion == MascotEmotion.SNARKY:
            # Smug arched eyebrows and side smirk
            eye_color = GLOW_AMBER
            # Left eyebrow raised high
            grid[sy + 1][sx + 2] = eye_color
            grid[sy + 1][sx + 3] = eye_color
            # Left eye
            grid[sy + 3][sx + 2] = eye_color
            grid[sy + 3][sx + 3] = eye_color
            # Right eye squinting / flat
            grid[sy + 3][sx + 6] = eye_color
            grid[sy + 3][sx + 7] = eye_color
            # Asymmetrical smirk mouth
            grid[sy + 5][sx + 5] = eye_color
            grid[sy + 5][sx + 6] = eye_color
            grid[sy + 4][sx + 7] = eye_color

        elif emotion == MascotEmotion.SHOCKED:
            # Massive wide glowing white/red eyes, dropped jaw
            eye_color = WHITE
            # Left eye ring
            for dx in (1, 2, 3):
                grid[sy + 1][sx + dx] = eye_color
                grid[sy + 4][sx + dx] = eye_color
            grid[sy + 2][sx + 1] = eye_color
            grid[sy + 3][sx + 1] = eye_color
            grid[sy + 2][sx + 3] = eye_color
            grid[sy + 3][sx + 3] = eye_color
            # Right eye ring
            for dx in (6, 7, 8):
                grid[sy + 1][sx + dx] = eye_color
                grid[sy + 4][sx + dx] = eye_color
            grid[sy + 2][sx + 6] = eye_color
            grid[sy + 3][sx + 6] = eye_color
            grid[sy + 2][sx + 8] = eye_color
            grid[sy + 3][sx + 8] = eye_color
            # Open O mouth
            grid[sy + 5][sx + 4] = GLOW_RED
            grid[sy + 5][sx + 5] = GLOW_RED

        elif emotion == MascotEmotion.CELEBRATING:
            # Star eyes, wide happy open smile
            gold = GLOW_GOLD
            # Star eye left
            grid[sy + 2][sx + 2] = gold
            grid[sy + 3][sx + 1] = gold
            grid[sy + 3][sx + 2] = WHITE
            grid[sy + 3][sx + 3] = gold
            grid[sy + 4][sx + 2] = gold
            # Star eye right
            grid[sy + 2][sx + 7] = gold
            grid[sy + 3][sx + 6] = gold
            grid[sy + 3][sx + 7] = WHITE
            grid[sy + 3][sx + 8] = gold
            grid[sy + 4][sx + 7] = gold
            # Big open grin
            for dx in (3, 4, 5, 6):
                grid[sy + 5][sx + dx] = GLOW_PURPLE

        elif emotion == MascotEmotion.ROASTING:
            # Angry glowing red angled eyes, open shouting fangs
            red = GLOW_RED
            # Angled brows
            grid[sy + 1][sx + 1] = red
            grid[sy + 2][sx + 2] = red
            grid[sy + 2][sx + 7] = red
            grid[sy + 1][sx + 8] = red
            # Red eyes
            grid[sy + 3][sx + 2] = red
            grid[sy + 3][sx + 3] = WHITE
            grid[sy + 3][sx + 6] = WHITE
            grid[sy + 3][sx + 7] = red
            # Open shouting mouth
            for dx in (3, 4, 5, 6):
                grid[sy + 5][sx + dx] = red
            grid[sy + 4][sx + 4] = red
            grid[sy + 4][sx + 5] = red

        elif emotion == MascotEmotion.THINKING:
            # Scanning radar eye beam moving left-right
            scan_pos = (frame_idx % 6) + 2
            grid[sy + 3][sx + scan_pos] = GLOW_AMBER
            grid[sy + 3][sx + scan_pos + 1] = WHITE
            # Thinking wavy mouth
            grid[sy + 5][sx + 4] = GLOW_AMBER
            grid[sy + 5][sx + 5] = GLOW_AMBER

        elif emotion == MascotEmotion.SLEEPING:
            # Dimmed sleep eyes (-- --)
            dim = (80, 90, 110, 255)
            grid[sy + 3][sx + 2] = dim
            grid[sy + 3][sx + 3] = dim
            grid[sy + 3][sx + 6] = dim
            grid[sy + 3][sx + 7] = dim

    @classmethod
    def _render_fx(cls, grid: List[List[RGBA]], emotion: MascotEmotion, bob: int, frame_idx: int) -> None:
        """Render external particle sparkles, flames, or Z's."""
        if emotion == MascotEmotion.CELEBRATING:
            # Confetti sparkles around bot
            confetti_colors = [GLOW_GOLD, GLOW_PURPLE, GLOW_CYAN, WHITE]
            pos_list = [(2, 3), (21, 4), (1, 15), (22, 16), (3, 21), (20, 20)]
            for i, (px, py) in enumerate(pos_list):
                c = confetti_colors[(i + frame_idx) % len(confetti_colors)]
                grid[py][px] = c

        elif emotion == MascotEmotion.ROASTING:
            # Fire embers above monitor
            ember_y = max(0, bob)
            if frame_idx % 2 == 0:
                grid[ember_y][8] = GLOW_RED
                grid[ember_y][15] = THRUSTER_ORANGE
            else:
                grid[ember_y][9] = THRUSTER_YELLOW
                grid[ember_y][14] = GLOW_RED

        elif emotion == MascotEmotion.SLEEPING:
            # Drifting Z's above top right
            grid[1][18] = WHITE
            grid[1][19] = WHITE
            grid[2][19] = WHITE
            grid[3][18] = WHITE
            grid[3][19] = WHITE

    @classmethod
    def render_image(cls, emotion: MascotEmotion, frame_idx: int = 0, scale: int = 8) -> Image.Image:
        """Produce an upscaled RGBA PIL.Image of the mascot frame with sharp pixel fidelity."""
        grid = cls.generate_frame(emotion, frame_idx)
        raw_img = Image.new("RGBA", (cls.WIDTH, cls.HEIGHT), (0, 0, 0, 0))
        for y in range(cls.HEIGHT):
            for x in range(cls.WIDTH):
                raw_img.putpixel((x, y), grid[y][x])

        if scale > 1:
            return raw_img.resize((cls.WIDTH * scale, cls.HEIGHT * scale), Image.Resampling.NEAREST)
        return raw_img

    @classmethod
    def render_ascii(cls, emotion: MascotEmotion, frame_idx: int = 0) -> str:
        """Produce an ANSI-colored or plain ASCII art string for terminal display."""
        grid = cls.generate_frame(emotion, frame_idx)
        lines: List[str] = []
        for y in range(cls.HEIGHT):
            line_chars = []
            for x in range(cls.WIDTH):
                r, g, b, a = grid[y][x]
                if a < 30:
                    line_chars.append(" ")
                elif r > 200 and g > 200 and b > 200:
                    line_chars.append("@")
                elif r > 180 and g < 100:
                    line_chars.append("#")
                elif g > 180 and b > 180:
                    line_chars.append("*")
                elif r > 180 and g > 150:
                    line_chars.append("+")
                else:
                    line_chars.append(".")
            lines.append("".join(line_chars))
        return "\n".join(lines)

    @classmethod
    def render_svg(cls, emotion: MascotEmotion, frame_idx: int = 0, scale: int = 8) -> str:
        """Export the pixel sprite as a scalable vector SVG string."""
        grid = cls.generate_frame(emotion, frame_idx)
        w = cls.WIDTH * scale
        h = cls.HEIGHT * scale
        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" shape-rendering="crispEdges">',
            f'<rect width="{w}" height="{h}" fill="none"/>',
        ]
        for y in range(cls.HEIGHT):
            for x in range(cls.WIDTH):
                r, g, b, a = grid[y][x]
                if a > 0:
                    alpha = round(a / 255.0, 2)
                    fill = f"rgba({r},{g},{b},{alpha})"
                    svg_parts.append(
                        f'<rect x="{x * scale}" y="{y * scale}" width="{scale}" height="{scale}" fill="{fill}"/>'
                    )
        svg_parts.append("</svg>")
        return "".join(svg_parts)
