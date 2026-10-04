"""Tests for FastAPI companion REST endpoints."""

import pytest
from fastapi.testclient import TestClient
from roastbot.server.app import create_app


@pytest.fixture
def api_client(test_engine):
    app = create_app(engine=test_engine)
    return TestClient(app)


def test_api_mascot_state(api_client):
    res = api_client.get("/api/mascot/state")
    assert res.status_code == 200
    data = res.json()
    assert "emotion" in data
    assert "mood_score" in data


def test_api_sprite_endpoint(api_client):
    res = api_client.get("/api/mascot/sprite?emotion=snarky&scale=4")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/png"
    assert len(res.content) > 100


def test_api_camera_preview(api_client):
    res = api_client.get("/api/camera/preview")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/jpeg"
    assert len(res.content) > 100


def test_api_roast_endpoint(api_client):
    payload = {"category": "desk_clutter", "severity": "savage"}
    res = api_client.post("/api/roast", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "roast" in data
    assert data["category"] == "desk_clutter"
    assert data["severity"] == "savage"


def test_api_stats_and_history(api_client):
    res = api_client.get("/api/stats")
    assert res.status_code == 200
    data = res.json()
    assert "total_roasts" in data

    hist_res = api_client.get("/api/history")
    assert hist_res.status_code == 200
    assert isinstance(hist_res.json(), list)


def test_api_config_update(api_client):
    res = api_client.post("/api/config", json={"severity": "gordon_ramsay", "category": "posture_check"})
    assert res.status_code == 200
    data = res.json()
    assert data["severity"] == "gordon_ramsay"
    assert data["category"] == "posture_check"
