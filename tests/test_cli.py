"""Tests for CLI commands."""

from click.testing import CliRunner
from roastbot.cli import main


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "RoastBot-Vision" in result.output
    assert "roast" in result.output
    assert "serve" in result.output
    assert "mascot" in result.output


def test_cli_mascot_gallery():
    runner = CliRunner()
    result = runner.invoke(main, ["mascot"])
    assert result.exit_code == 0
    assert "BYTEY THE SENTRY" in result.output
    assert "SNARKY" in result.output


def test_cli_roast_mock():
    runner = CliRunner()
    result = runner.invoke(main, ["roast", "--mock-cam", "--mute", "--category", "desk_clutter", "--severity", "snarky"])
    assert result.exit_code == 0
    assert "Bytey" in result.output


def test_cli_demo():
    runner = CliRunner()
    result = runner.invoke(main, ["demo"])
    assert result.exit_code == 0
    assert "RoastBot-Vision Showcase Demo" in result.output
    assert "Demo completed successfully!" in result.output
