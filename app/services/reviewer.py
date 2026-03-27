import logging
from anthropic import AsyncAnthropic
from sqlalchemy.orm import Session
from app.config import settings
from app.services.github_client import get_pr_diff_text
from app.services.discord_client import send_discord_message
from app.services.cost_logger import log_cost
from app.prompts.review_prompt import build_prompt

logger = logging.getLogger(__name__)

client = AsyncAnthropic(api_key=settings.anthropic_api_key)

async def review_pr(
        repo: str, pr_number: int, pr_title: str, pr_url: str, author: str, db: Session
):
    try:
        diff_text = await get_pr_diff_text(repo, pr_number) # gitapi에서 diff 가져옴
    except Exception as e:
        logger.error(f"GitHub diff 조회 실패 PR #{pr_number}: {e}")
        return
    try:
        prompt = build_prompt(diff_text) # diff를 요구사항/ERD 기준으로 판단해서 프롬프트 생
        response = await client.messages.create( # claudeAPI 호출해서 llm 리뷰 받음
            model = settings.claude_model,
            max_tokens = settings.claude_max_tokens,
            messages = [{"role": "user", "content": prompt}],
        )
    except Exception as e:
        logger.error(f"Claude API 호출 실패 PR #{pr_number}: {e}")
        return

    review_text = response.content[0].text # 리뷰에서 텍스트 꺼
    input_tokens = response.usage.input_tokens # 토큰수 입력
    output_tokens = response.usage.output_tokens # 토큰수 출력
    cost = calculate_cost(input_tokens, output_tokens) # 토큰수로 비용 계산

    try:
        log_cost(db, pr_number, input_tokens, output_tokens, cost) # 디비저장
    except Exception as e:
        logger.error(f"비용 DB 저장 실패 PR #{pr_number}: {e}")

    message = build_discord_message( # 디스코드 메세지 포매팅
        pr_title, pr_url, author, pr_number,
        input_tokens, output_tokens, cost, review_text
    )
    try:
        await send_discord_message(message) # 디스코드로 전송
    except Exception as e:
        logger.error(f"Discord 전송 실패 PR #{pr_number}: {e}")

def calculate_cost(input_tokens: int, output_tokens: int) -> float:
    input_cost = (input_tokens / 1_000_000) * settings.claude_input_price
    output_cost = (output_tokens / 1_000_000) * settings.claude_output_price
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
