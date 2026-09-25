import sys
import subprocess
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import app as flask_app


@pytest.fixture
def client():
    flask_app.app.config.update(TESTING=True)

    flask_app.scrape_running = False

    if flask_app.scrape_lock.locked():
        flask_app.scrape_lock.release()

    with flask_app.app.test_client() as client:
        yield client

    flask_app.scrape_running = False

    if flask_app.scrape_lock.locked():
        flask_app.scrape_lock.release()


@pytest.mark.buttons
def test_update_analysis_success(client, monkeypatch):
    """Update Analysis should return 200 when the app is not busy."""

    called = {"value": False}

    def fake_get_analysis():
        called["value"] = True
        return {}

    monkeypatch.setattr(
        flask_app,
        "get_analysis",
        fake_get_analysis,
    )

    response = client.post("/update-analysis")

    assert response.status_code == 200
    assert response.get_json()["ok"] is True
    assert called["value"] is True


@pytest.mark.buttons
def test_update_analysis_busy(client, monkeypatch):
    """Update Analysis should return 409 while data is being pulled."""

    flask_app.scrape_running = True

    called = {"value": False}

    def fake_get_analysis():
        called["value"] = True
        return {}

    monkeypatch.setattr(
        flask_app,
        "get_analysis",
        fake_get_analysis,
    )

    response = client.post("/update-analysis")

    assert response.status_code == 409
    assert response.get_json()["busy"] is True
    assert called["value"] is False


@pytest.mark.buttons
def test_pull_data_success(client, monkeypatch):
    """Pull Data should start the refresh process and return 202."""

    started = {"value": False}

    class FakeThread:
        def __init__(self, target, daemon):
            self.target = target
            self.daemon = daemon

        def start(self):
            started["value"] = True

    monkeypatch.setattr(
        flask_app.threading,
        "Thread",
        FakeThread,
    )

    response = client.post("/pull-data")

    assert response.status_code == 202
    assert response.get_json()["ok"] is True
    assert started["value"] is True


@pytest.mark.buttons
def test_pull_data_busy(client):
    """A second Pull Data request should return 409 when busy."""

    flask_app.scrape_lock.acquire()
    flask_app.scrape_running = True

    response = client.post("/pull-data")

    assert response.status_code == 409
    assert response.get_json()["busy"] is True


@pytest.mark.buttons
def test_run_data_refresh_success(monkeypatch):
    """The refresh process should run all three data scripts."""

    calls = []

    def fake_run(command, check, cwd):
        calls.append(command)

    monkeypatch.setattr(
        flask_app.subprocess,
        "run",
        fake_run,
    )

    flask_app.scrape_running = True

    if not flask_app.scrape_lock.locked():
        flask_app.scrape_lock.acquire()

    flask_app.run_data_refresh()

    assert len(calls) == 3
    assert calls[0][1].endswith("refresh_data.py")
    assert calls[1][1].endswith("clean.py")
    assert calls[2][1].endswith("load_data.py")

    assert flask_app.scrape_running is False
    assert flask_app.scrape_lock.locked() is False


@pytest.mark.buttons
def test_run_data_refresh_failure(monkeypatch):
    """The refresh process should clean up after a subprocess failure."""

    def fake_run(command, check, cwd):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=command,
        )

    monkeypatch.setattr(
        flask_app.subprocess,
        "run",
        fake_run,
    )

    flask_app.scrape_running = True

    if not flask_app.scrape_lock.locked():
        flask_app.scrape_lock.acquire()

    flask_app.run_data_refresh()

    assert flask_app.scrape_running is False
    assert flask_app.scrape_lock.locked() is False