import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.github_client import get_pr_diff_text
import httpx

@pytest.mark.asyncio
async def test_get_pr_diff_text_success():
    mock_files = [
        {"filename": "views.py", "patch": "@@ -1,3 +1,5 @@\n+def index(request):"},
        {"filename": "image.png"},  # patch 없는 바이너리 파일
    ]
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_files
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = await get_pr_diff_text("test/repo", 1)

        assert "views.py" in result
        assert "image.png" in result
        assert "(binary or no diff" in result

@pytest.mark.asyncio
async def test_get_pr_diff_text_api_fail():
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.HTTPStatusError(
            "401", request=MagicMock(), response=MagicMock()
        )
        with pytest.raises(Exception):
            await get_pr_diff_text("test/repo", 1)
