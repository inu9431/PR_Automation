# PR 리뷰 자동화 시스템

## 개요

GitHub PR 오픈 → Claude API 1차 리뷰 → 디스코드로 조교에게 전송
조교가 검토 후 GitHub에 최종 코멘트 직접 등록

## 전체 흐름

```
수강생 PR 오픈
      ↓
GitHub Webhook → FastAPI 수신
      ↓
PR diff 코드 fetch
      ↓
Claude API 1차 분석 (요구사항 + ERD 기준)
      ↓
디스코드로 조교에게 초안 전송
      ↓
조교 검토 → GitHub PR에 최종 코멘트 등록
```

## 디렉토리 구조

```
pr-review-agent/
├── main.py
├── reviewer.py
├── github_client.py
├── discord_client.py
├── cost_logger.py
├── prompts/
│   └── review_prompt.py
├── .env
└── requirements.txt
```

## 환경 변수 (.env)

```
ANTHROPIC_API_KEY=sk-ant-xxxxx
GITHUB_TOKEN=ghp_xxxxx
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxxx
```

## 설치

```bash
pip install fastapi uvicorn anthropic httpx python-dotenv
```

## 실행

```bash
uvicorn main:app --reload --port 8000
```

## 비용 확인

```
GET http://localhost:8000/cost
```

응답:

```json
{
  "total_pr_count": 47,
  "total_cost_usd": 0.021340,
  "total_cost_krw": 29.876
}
```

## GitHub Webhook 설정

1. 레포 → Settings → Webhooks → Add webhook
2. Payload URL: `http://your-server:8000/webhook`
3. Content type: `application/json`
4. Events: `Pull requests` 체크

로컬 테스트 시 ngrok 사용:

```bash
ngrok http 8000
```

## 로컬 테스트

```python
# test_review.py
import asyncio
from dotenv import load_dotenv
load_dotenv()

from reviewer import review_pr

asyncio.run(review_pr(
    repo="your-org/your-repo",
    pr_number=1,
    pr_title="테스트 PR",
    pr_url="https://github.com/your-org/your-repo/pull/1",
    author="test-user",
))
```

```bash
python test_review.py
```

디스코드에 리뷰 초안 + 비용 오면 정상. `cost_log.jsonl` 파일 생성 확인.

## 요구사항/ERD 업데이트 방법

`prompts/review_prompt.py`의 `REQUIREMENTS`만 수정.
프로젝트 바뀔 때마다 이 부분만 교체해서 재사용.

```python
REQUIREMENTS = """
[요구사항]
- todo_list: 제목 리스트 표시, a태그로 상세 페이지 이동
- todo_info: h1 제목, hr 구분선, 상세정보 표시

[ERD]
Todo
- id (PK)
- title (CharField)
- description (TextField)
- start_date (DateField)
- end_date (DateField)
- is_completed (BooleanField)
- created_at (DateTimeField)
- modified_at (DateTimeField)

[레이어 분리 기준]
- View: 요청/응답 처리만
- Service: 비즈니스 로직
- Serializer: 데이터 직렬화/검증
- 뷰에 비즈니스 로직 있으면 피드백
- Serializer 안 거치고 직접 응답하면 피드백
"""
```

## 비용 계산 기준

Claude Sonnet 4.5 기준: input $3/1M tokens, output $15/1M tokens
