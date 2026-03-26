import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_webhook_opened(async_client, webhook_payload):
    with patch("app.api.webhook.review_pr", new_callable=AsyncMock) as mock_pr:
        res = await async_client.post("/webhook", json=webhook_payload)
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_webhook_skipped(async_client, webhook_payload):
    webhook_payload["action"] = "closed"
    res = await async_client.post("/webhook", json=webhook_payload)
    assert res.json() == {"status": "skipped"}

