"""Tests for procedural pixel sprite generation and multi-format renderer."""

from PIL import Image
from roastbot.config import MascotEmotion
from roastbot.mascot.sprites import PixelSpriteRenderer


def test_sprite_grid_dimensions():
    grid = PixelSpriteRenderer.generate_frame(MascotEmotion.IDLE, frame_idx=0)
    assert len(grid) == 24
    assert len(grid[0]) == 24
    # Each cell is an RGBA tuple
    assert len(grid[0][0]) == 4


def test_sprite_all_emotions_render_image():
    for emotion in MascotEmotion:
        img = PixelSpriteRenderer.render_image(emotion, frame_idx=0, scale=4)
        assert isinstance(img, Image.Image)
        assert img.size == (24 * 4, 24 * 4)
        assert img.mode == "RGBA"


def test_sprite_ascii_and_svg_export():
    ascii_out = PixelSpriteRenderer.render_ascii(MascotEmotion.SNARKY, frame_idx=0)
    assert isinstance(ascii_out, str)
    assert len(ascii_out) > 50
    assert "\n" in ascii_out

    svg_out = PixelSpriteRenderer.render_svg(MascotEmotion.CELEBRATING, frame_idx=0, scale=8)
    assert isinstance(svg_out, str)
    assert "<svg" in svg_out
    assert "</svg>" in svg_out
