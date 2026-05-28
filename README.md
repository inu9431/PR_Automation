# PR Review Automation

GitHub PR이 열리면 Claude API로 1차 리뷰 초안을 생성하고, Discord로 조교에게 전송하는 자동화 시스템.
조교는 초안을 검토한 뒤 GitHub에 최종 코멘트를 직접 등록한다.

## 흐름

```
수강생 PR 오픈
      ↓
GitHub Webhook → FastAPI 수신 (HMAC 서명 검증)
      ↓
PR diff fetch (GitHub API)
      ↓
Claude API 1차 분석 (요구사항 + ERD 기준)
      ↓
Discord로 조교에게 초안 전송
      ↓
조교 검토 → GitHub PR에 최종 코멘트 등록
```

> LLM은 초안만 생성하고 GitHub에 직접 코멘트를 달지 않는다. 최종 판단은 반드시 조교가 한다.

## 기술 스택

| 영역 | 사용 기술 |
|------|-----------|
| API 서버 | FastAPI, uvicorn |
| AI | Anthropic Claude API (claude-sonnet) |
| DB | PostgreSQL, SQLAlchemy |
| 설정 관리 | pydantic-settings |
| HTTP 클라이언트 | httpx (async) |
| 컨테이너 | Docker, Docker Compose |
| CI/CD | GitHub Actions |

## 디렉토리 구조

```
app/
├── api/webhook.py          # Webhook 수신, HMAC 서명 검증, BackgroundTask 등록
├── services/
│   ├── reviewer.py         # Claude API 리뷰 로직
│   ├── github_client.py    # PR diff fetch
│   ├── discord_client.py   # Discord 전송
│   └── cost_logger.py      # 비용 DB 저장/조회
├── models/cost_log.py      # SQLAlchemy ORM
├── schemas/github.py       # Pydantic 스키마
├── prompts/review_prompt.py # 리뷰 프롬프트 (요구사항/ERD)
├── config.py               # 환경변수
├── database.py             # DB 엔진/세션
└── main.py                 # FastAPI 앱
```

## 환경 변수

```env
ANTHROPIC_API_KEY=sk-ant-xxxxx
GITHUB_TOKEN=ghp_xxxxx
GITHUB_WEBHOOK_SECRET=your-webhook-secret
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxxx
DATABASE_URL=postgresql://postgres:postgres@db:5432/dev_db

# Docker Compose용
DB_NAME=dev_db
DB_USER=postgres
DB_PASSWORD=postgres

# CI/CD용
DOCKER_USERNAME=your-username
```

## 실행

```bash
# Docker
docker compose up -d --build

# 로컬
uv run uvicorn app.main:app --reload --port 8000
```

## GitHub Webhook 설정

1. 테스트용 레포 → Settings → Webhooks → Add webhook
2. Payload URL: `https://your-domain/webhook`
3. Content type: `application/json`
4. Secret: `GITHUB_WEBHOOK_SECRET`와 동일한 값
5. Events: `Pull requests`만 체크

로컬 테스트 시 ngrok 사용:

```bash
ngrok http 8000
```

## 비용 조회

```
GET /cost
```

```json
{
  "total_pr_count": 47,
  "total_cost_usd": 0.021340,
  "total_cost_krw": 29.876
}
```

## 테스트

```bash
uv run pytest -v
```

## 프로젝트 교체 방법

`app/prompts/review_prompt.py`의 `REQUIREMENTS`만 수정하면 다른 프로젝트에 재사용 가능.
`REVIEW_STANDARDS`(보안/DB/레이어 체크리스트)는 공통 기준이므로 수정 불필요.

```python
REQUIREMENTS = """
[요구사항]
...

[ERD]
...
"""
```
