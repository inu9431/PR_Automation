import anthropic
from sqlalchemy.orm import Session
from app.config import settings
from app.services.github_client import get_pr_diff_text
from app.services.discord_client import send_discord_message
from app.services.cost_logger import log_cost
from app.prompts.review_prompt import build_prompt

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

async def review_pr(
        repo: str, pr_number: int, pr_title: str, pr_url: str, author: str, db: Session
):
    diff_text = await get_pr_diff_text(repo, pr_number)

    prompt = build_prompt(diff_text)
    response = client.messages.create(
        model = "claude-sonnet-4-5",
        max_tokens = 1500,
        messages = [{"role": "user", "content": prompt}],
    )

    review_text = response.content[0].text
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    cost = calculate_cost(input_tokens, output_tokens)

    log_cost(db, pr_number, input_tokens, output_tokens, cost)

    message = build_discord_message(
        pr_title, pr_url, author, pr_number,
        input_tokens, output_tokens, cost, review_text
    )
    await send_discord_message(message)

def calculate_cost(input_tokens: int, output_tokens: int) -> float:
    input_cost = (input_tokens / 1_000_000) * 3
    output_cost = (output_tokens / 1_000_000) * 15
    return input_cost + output_cost

def build_discord_message(
        pr_title: str, pr_url: str, author: str, pr_number: int,
        input_tokens: int, output_tokens: int, cost: float, review_text: str
)-> str:
    return f"""**[PR #{pr_number} 리뷰 초안]**                                                                                                                       
  - 제목: [{pr_title}]({pr_url})
  - 작성자: {author}                                                                                                                                                   
  - 토큰: input {input_tokens} / output {output_tokens}
  - 이번 비용: ${cost:.6f} (약 {cost * 1400:.1f}원)                                                                                                                    
                                                                                                                                                                       
  **Claude 1차 리뷰:**
  {review_text[:1500]}                                                                                                                                                 
                  
  > 검토 후 GitHub에서 최종 코멘트 달아주세요 👆   
"""
