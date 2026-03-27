import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.reviewer import calculate_cost, build_discord_message

def test_calculate_cost():
    assert calculate_cost(1_000_000, 1_000_000) == 18.0

def test_calculate_cost_zero():
    assert calculate_cost(0, 0) == 0.0

def test_build_discord_message():
    msg = build_discord_message(
        pr_title = "테스트 PR",
        pr_url="https://github.com/test/repo/pull/1",
        author="testuser",
        pr_number=1,
        input_tokens=1000,
        output_tokens=500,
        cost=0.0105,
        review_text="리뷰 내용입니다"
    )
    assert "PR #1" in msg
    assert "testuser" in msg
    assert "리뷰 내용입니다" in msg

@pytest.mark.asyncio
async def test_review_pr_github_fail(db):
    with patch("app.services.reviewer.get_pr_diff_text", side_effect=Exception("404 Not Found")):
        # 예외 없이 return 되는지 확인
        from app.services.reviewer import review_pr
        await review_pr("test/repo", 1, "제목", "http://url", "user", db)
        # DB 저장, Discord 전송 모두 호출 안됨
        db.add.assert_not_called()

@pytest.mark.asyncio
async def test_review_pr_claude_fail(db):
    with patch("app.services.reviewer.get_pr_diff_text", return_value="diff text"), \
         patch("app.services.reviewer.client.messages.create", side_effect=Exception("API key expired")):
        from app.services.reviewer import review_pr
        await review_pr("test/repo", 1, "제목", "http://url", "user", db)
        db.add.assert_not_called()

@pytest.mark.asyncio
async def test_review_pr_db_fail_continues_discord(db):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(test="리뷰 내용")]
    mock_response.usage.input_tokens = 100
    mock_response.usage.output_tokens = 50

    with patch("app.services.reviewer.get_pr_diff_text", return_value="diff text"), \
         patch("app.services.reviewer.client.messages.create", new_callable=AsyncMock, return_value=mock_response), \
         patch("app.services.reviewer.log_cost", side_effect=Exception("DB 연결 끊김")), \
         patch("app.services.reviewer.send_discord_message", new_callable=AsyncMock) as mock_discord:
        from app.services.reviewer import review_pr
        await review_pr("test/repo", 1, "제목", "http://url", "user", db)
        mock_discord.assert_called()

@pytest.mark.asyncio
async def test_review_pr_discord_fail(db):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="리뷰 내용")]
    mock_response.usage.input_tokens = 100
    mock_response.usage.output_tokens = 50

    with patch("app.services.reviewer.get_pr_diff_text", return_value="diff text"), \
            patch("app.services.reviewer.client.messages.create", new_callable=AsyncMock, return_value=mock_response), \
            patch("app.services.reviewer.log_cost"), \
            patch("app.services.reviewer.send_discord_message", side_effect=Exception("Webhook URL 잘못됨")):
        from app.services.reviewer import review_pr