import pytest

from app import create_app


@pytest.fixture()
def app(tmp_path):
    return create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(tmp_path / "test-monitoring.db"),
            "ALERT_COOLDOWN_SECONDS": 0,
            "REPEATED_FAILURE_THRESHOLD": 2,
            "HIGH_FREQUENCY_THRESHOLD": 3,
            "HIGH_FREQUENCY_WINDOW_SECONDS": 60,
        }
    )


@pytest.fixture()
def client(app):
    return app.test_client()

