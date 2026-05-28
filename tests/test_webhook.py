import hashlib
import hmac
import json
from unittest.mock import AsyncMock, patch

import pytest


def make_signature(body: bytes, secret: str = "test-secret") -> str:
    return (
        "sha256="
        + hmac.new(
            key=secret.encode(),
            msg=body,
            digestmod=hashlib.sha256,
        ).hexdigest()
    )


def signed_headers(body: bytes, secret: str = "test-secret") -> dict:
    return {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": make_signature(body, secret),
    }


@pytest.mark.asyncio
async def test_webhook_opened(async_client, webhook_payload):
    body = json.dumps(webhook_payload).encode()
    with patch("app.api.webhook.review_pr", new_callable=AsyncMock):
        res = await async_client.post("/webhook", content=body, headers=signed_headers(body))
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}


@pytest.mark.asyncio
@pytest.mark.parametrize("action", ["closed", "synchronize", "edited"])
async def test_webhook_skipped(async_client, webhook_payload, action):
    webhook_payload["action"] = action
    body = json.dumps(webhook_payload).encode()
    res = await async_client.post("/webhook", content=body, headers=signed_headers(body))
    assert res.json() == {"status": "skipped"}


@pytest.mark.asyncio
async def test_webhook_no_signature(async_client, webhook_payload):
    res = await async_client.post("/webhook", json=webhook_payload)
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_webhook_invalid_signature(async_client, webhook_payload):
    body = json.dumps(webhook_payload).encode()
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": make_signature(body, secret="wrong-secret"),
    }
    res = await async_client.post("/webhook", content=body, headers=headers)
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_webhook_invalid_json(async_client):
    body = b"not json"
    res = await async_client.post("/webhook", content=body, headers=signed_headers(body))
    assert res.status_code == 200
    assert res.json()["status"] == "error"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"action": "opened", "pull_request": {"number": 1}, "repository": {}},
        {"action": "opened", "pull_request": {}, "repository": {"full_name": "test/repo"}},
    ],
)
async def test_webhook_missing_fields(async_client, payload):
    body = json.dumps(payload).encode()
    res = await async_client.post("/webhook", content=body, headers=signed_headers(body))
    assert res.json()["status"] == "error"
