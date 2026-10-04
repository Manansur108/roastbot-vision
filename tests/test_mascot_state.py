"""Tests for Mascot state machine and animation ticker."""

import time
from roastbot.config import MascotEmotion
from roastbot.mascot.state import MascotStateMachine


def test_mascot_initial_state():
    mascot = MascotStateMachine()
    snapshot = mascot.get_snapshot()
    assert snapshot.emotion == MascotEmotion.IDLE
    assert snapshot.mood_score == 75
    assert snapshot.current_dialog is None
    assert snapshot.is_speaking is False


def test_mascot_set_emotion_and_dialog():
    mascot = MascotStateMachine()
    mascot.set_emotion(MascotEmotion.SHOCKED, dialog="Look at those cables!", dialog_duration_seconds=5.0)

    snap = mascot.get_snapshot()
    assert snap.emotion == MascotEmotion.SHOCKED
    assert snap.current_dialog == "Look at those cables!"
    assert snap.is_speaking is True


def test_mascot_dialog_expiration():
    mascot = MascotStateMachine(idle_timeout_seconds=0.1)
    mascot.set_emotion(MascotEmotion.SNARKY, dialog="Quick roast", dialog_duration_seconds=0.05)

    time.sleep(0.08)
    snap = mascot.tick()
    # Dialog should have expired
    assert snap.current_dialog is None


def test_mascot_mood_clamping():
    mascot = MascotStateMachine()
    mascot.update_mood(50)
    assert mascot.mood_score == 100
    mascot.update_mood(-150)
    assert mascot.mood_score == 0
