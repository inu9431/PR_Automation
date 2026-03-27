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
PR_Automation/
├── app/
│   ├── api/
│   │   └── webhook.py          # /webhook, /cost 라우터
│   ├── models/
│   │   └── cost_log.py         # SQLAlchemy ORM 모델
│   ├── schemas/
│   │   └── github.py           # Pydantic 응답 스키마
│   ├── services/
│   │   ├── reviewer.py         # Claude API 리뷰 로직
│   │   ├── github_client.py    # PR diff fetch
│   │   ├── discord_client.py   # Discord 전송
│   │   └── cost_logger.py      # 비용 DB 저장/조회
│   ├── prompts/
│   │   └── review_prompt.py    # 리뷰 프롬프트 (요구사항/ERD)
│   ├── config.py               # pydantic-settings 환경변수
│   ├── database.py             # SQLAlchemy engine, session
│   └── main.py                 # FastAPI app
├── tests/
│   ├── conftest.py             # 공통 fixtures
│   ├── test_webhook.py
│   ├── test_reviewer.py
│   └── test_cost_logger.py
├── docker-compose.yml
├── docker-compose.prod.yml
├── Dockerfile
└── pyproject.toml
```

## 환경 변수 (.env)

```
ANTHROPIC_API_KEY=sk-ant-xxxxx
GITHUB_TOKEN=ghp_xxxxx
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxxx
DATABASE_URL=postgresql://postgres:postgres@db:5432/dev_db
DEBUG=False

# DB (docker-compose용)
DB_NAME=dev_db
DB_USER=postgres
DB_PASSWORD=postgres

# Docker Hub
DOCKER_USERNAME=your-username
```

## 설치

```bash
uv add anthropic httpx pydantic-settings sqlalchemy psycopg2-binary
```

## 실행

```bash
# 도커
docker compose up -d --build

# 로컬
uv run uvicorn app.main:app --reload --port 8000
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

1. 테스트용 레포 → Settings → Webhooks → Add webhook
2. Payload URL: `https://xxxx.ngrok-free.dev/webhook`
3. Content type: `application/json`
4. Events: `Pull requests`만 체크 (push 제외)

로컬 테스트 시 ngrok 사용:

```bash
ngrok http 8000
```

## 테스트

```bash
# 단위 테스트
uv run pytest -v

# E2E 테스트
# 테스트용 레포에서 PR 오픈 → 디스코드에 리뷰 초안 수신 확인
```

디스코드에 리뷰 초안 + 비용 오면 정상.

## GitHub Secrets 설정 (CI/CD)

레포 → Settings → Secrets and variables → Actions:
- `ANTHROPIC_API_KEY`
- `GH_TOKEN`
- `DISCORD_WEBHOOK_URL`
- `DOCKER_USERNAME` / `DOCKER_PASSWORD`
- `EC2_HOST` / `EC2_KEY`

## 요구사항/ERD 업데이트 방법

`app/prompts/review_prompt.py`의 `REQUIREMENTS`만 수정.
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
