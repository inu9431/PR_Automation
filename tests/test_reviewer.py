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