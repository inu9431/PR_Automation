# PR Review Automation

GitHub PR이 열리면 Claude API로 1차 리뷰 초안을 생성하고, Discord로 조교에게 전송하는 자동화 시스템.
조교는 초안을 검토한 뒤 GitHub에 최종 코멘트를 직접 등록한다.

> LLM은 초안만 생성하고 GitHub에 직접 코멘트를 달지 않는다. 최종 판단은 반드시 조교가 한다.

## 흐름

```
수강생 PR 오픈
      ↓
GitHub Webhook → FastAPI 수신 (HMAC 서명 검증)
      ↓
PR diff fetch (GitHub API)
      ↓
Claude API 1차 분석
  - system prompt: 보안/DB/레이어 분리 등 공통 리뷰 기준
  - user message: 프로젝트 요구사항 + ERD + PR diff
      ↓
Discord로 조교에게 초안 전송
      ↓
조교 검토 → GitHub PR에 최종 코멘트 등록
```

## 기술 스택

| 영역 | 사용 기술 |
|------|-----------|
| API 서버 | FastAPI, uvicorn |
| AI | Anthropic Claude API (claude-sonnet) |
| DB | PostgreSQL, SQLAlchemy |
| 설정 관리 | pydantic-settings |
| HTTP 클라이언트 | httpx (async) |
| 컨테이너 | Docker, Docker Compose |
| CI/CD | GitHub Actions → Docker Hub → EC2 |

## 주요 설계 포인트

**보안**
- GitHub Webhook HMAC 서명 검증 (`hmac.compare_digest` 타이밍 어택 방지)
- 환경변수 기반 시크릿 관리 (pydantic-settings)

**비동기 처리**
- Webhook 수신 즉시 200 응답 후 BackgroundTask로 리뷰 처리
- httpx AsyncClient로 GitHub/Discord API 비동기 호출

**프롬프트 설계**
- system prompt: 보안·DB·레이어 분리 체크리스트 (모든 프로젝트 공통)
- user message: 프로젝트별 요구사항/ERD + PR diff
- `REQUIREMENTS`만 교체하면 다른 프로젝트에 재사용 가능

**비용 추적**
- 리뷰마다 input/output 토큰 및 비용(USD/KRW) DB 저장
- `/cost` 엔드포인트로 누적 비용 조회

## 디렉토리 구조

```
app/
├── api/webhook.py           # Webhook 수신, HMAC 서명 검증, BackgroundTask 등록
├── services/
│   ├── reviewer.py          # Claude API 리뷰 로직
│   ├── github_client.py     # PR diff fetch
│   ├── discord_client.py    # Discord 전송
│   └── cost_logger.py       # 비용 DB 저장/조회
├── models/cost_log.py       # SQLAlchemy ORM
├── schemas/github.py        # Pydantic 스키마
├── prompts/review_prompt.py # 리뷰 프롬프트 (요구사항/ERD/리뷰 기준)
├── config.py                # 환경변수
├── database.py              # DB 엔진/세션
└── main.py                  # FastAPI 앱
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
