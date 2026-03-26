import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from app.main import app

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
