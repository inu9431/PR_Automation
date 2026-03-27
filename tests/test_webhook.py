import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_webhook_opened(async_client, webhook_payload):
    with patch("app.api.webhook.review_pr", new_callable=AsyncMock) as mock_pr:
        res = await async_client.post("/webhook", json=webhook_payload)
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}

@pytest.mark.asyncio
@pytest.mark.parametrize("action", ["closed", "synchronize", "edited"])
async def test_webhook_skipped(async_client, webhook_payload, action):
    webhook_payload["action"] = action
    res = await async_client.post("/webhook", json=webhook_payload)
    assert res.json() == {"status": "skipped"}

@pytest.mark.asyncio
async def test_webhook_invalid_json(async_client):
    res = await async_client.post(
        "/webhook",
        content = "not json",
        headers={"Content-Type": "application/json"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "error"

@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [
    {"action": "opened", "pull_request": {"number": 1}, "repository": {}}, # repo_pull_name 없음
    {"action": "opened", "pull_request": {}, "repository": {"full_name": "test/repo"}}, # pr number 없음
])
async def test_webhook_missing_fields(async_client, payload):
    res = await async_client.post("/webhook", json=payload)
    assert res.json()["status"] == "error"