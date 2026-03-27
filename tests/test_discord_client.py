import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.discord_client import send_discord_message
import httpx

@pytest.mark.asyncio
async def test_send_discord_message_success():
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        await send_discord_message("테스트메세지")
        mock_post.assert_called_once()

@pytest.mark.asyncio
async def test_send_discord_message_truncate():
    long_massage = "a" * 2100

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        await send_discord_message(long_massage)

        sent = mock_post.call_args[1]["json"]["content"]
        assert len(sent) > 1990