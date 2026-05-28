import os

os.environ.setdefault("GITHUB_WEBHOOK_SECRET", "test-secret")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("GITHUB_TOKEN", "test-token")
os.environ.setdefault("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from unittest.mock import MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app

TEST_WEBHOOK_SECRET = os.environ["GITHUB_WEBHOOK_SECRET"]


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def webhook_payload():
    return {
        "action": "opened",
        "pull_request": {
            "number": 1,
            "title": "테스트 PR",
            "html_url": "https://github.com/test/repo/pull/1",
            "user": {"login": "testuser"},
        },
        "repository": {"full_name": "test/repo"},
    }


@pytest.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
