# 아키텍처 개요

## 프로젝트 목적

부트캠프 조교로서 매달 2개 메인 프로젝트의 PR을 리뷰해야 한다. 전체 흐름 파악, 레이어 분리 여부 같은 기계적 검토를 LLM에 위임하고, 조교는 LLM 초안을 검증한 뒤 최종 코멘트만 직접 작성하는 **리뷰 업무 자동화 시스템**.

---

## 시스템 구성

```
수강생 PR 오픈
      ↓
GitHub Webhook ──→ FastAPI (app/)
                        │
                   BackgroundTask
                   ┌────┴─────┐
                   │          │
              Claude API   PostgreSQL
              (1차 리뷰)   (비용 로그)
                   │
              Discord Webhook
              (조교에게 초안 전송)
                   ↓
            조교 검토 → GitHub에 최종 코멘트
```

**핵심 설계 원칙**: LLM은 초안만 생성하고, GitHub에 직접 코멘트를 달지 않는다. 코드 품질이나 설계에 대한 최종 판단은 반드시 조교가 한다.

---

## 레이어 구조

```
app/
├── api/
│   └── webhook.py              # Router: HTTP 수신, 즉시 응답
├── services/
│   ├── reviewer.py             # Service: Claude API 리뷰 로직
│   ├── github_client.py        # Service: PR diff fetch
│   ├── discord_client.py       # Service: Discord 전송
│   └── cost_logger.py          # Service: 비용 DB 저장/조회
├── models/
│   └── cost_log.py             # Model: SQLAlchemy ORM
├── schemas/
│   └── github.py               # Schema: Pydantic 직렬화
├── prompts/
│   └── review_prompt.py        # Prompt: Claude 프롬프트 템플릿
├── config.py                   # pydantic-settings 환경변수
├── database.py                 # SQLAlchemy engine, session
└── main.py                     # FastAPI app 진입점
```

| 레이어 | 역할 | 분리 이유 |
|--------|------|-----------|
| Router | HTTP 요청 수신, BackgroundTask 등록, 즉시 응답 반환 | GitHub 타임아웃 방지를 위해 처리 로직과 분리 |
| Service | 외부 API 연동(GitHub, Claude, Discord) 및 비즈니스 로직 | 외부 의존성별 모듈화로 교체·테스트 용이 |
| Model | DB ORM 정의 | 비용 로그 스키마 변경 시 영향 범위 최소화 |
| Schema | 요청/응답 직렬화 | API 계약과 내부 모델 분리 |
| Prompt | Claude 프롬프트 템플릿 (요구사항 + ERD) | 프로젝트 교체 시 이 파일만 수정하면 재사용 가능 |

---

## 요청 흐름

### 1. Webhook → 리뷰 초안 생성

```
POST /webhook
  │
  ├─ action == "opened" 확인
  ├─ review_pr() → BackgroundTask 등록
  └─ {"status": "ok"} 즉시 반환          ← GitHub 10초 타임아웃 방지

  [BackgroundTask]
  │
  ├─ get_pr_diff_text()                   ← GitHub API: /pulls/{pr}/files
  ├─ build_prompt(diff_text)              ← REQUIREMENTS(요구사항+ERD) + diff 조합
  ├─ client.messages.create()             ← Claude API (모델/토큰 config.py에서 참조)
  ├─ calculate_cost()                     ← 비용 계산 (단가 config.py에서 참조)
  ├─ log_cost()                           ← CostLog DB insert
  └─ send_discord_message()               ← Discord Webhook → 조교에게 전송
```

### 2. 비용 조회

```
GET /cost
  │
  ├─ func.count(), func.sum() SQL 집계
  └─ CostSummaryResponse 반환 (총 PR 수, USD, KRW)
```

---

## 외부 의존성

| 서비스 | 용도 | 인증 방식 |
|--------|------|-----------|
| GitHub API v3 | PR diff 조회 | `GITHUB_TOKEN` (Bearer) |
| Anthropic API | 코드 리뷰 초안 생성 | `ANTHROPIC_API_KEY` |
| Discord Webhook | 리뷰 초안을 조교에게 전송 | URL에 토큰 포함 |
| PostgreSQL | API 호출 비용 로그 저장 | `DATABASE_URL` |

---

## Docker 구성

### 개발 환경 (`docker-compose.yml`)

- PostgreSQL 16-Alpine → 포트 5434
- 소스 볼륨 마운트 (`.:/app`) → uvicorn `--reload` 핫 리로드
- 웹 서비스 포트 8003

### 프로덕션 환경 (`docker-compose.prod.yml`)

- Docker Hub 이미지 (`${DOCKER_USERNAME}/app:latest`)
- uvicorn 워커 4개
- 웹 서비스 포트 8002
- `/cost` 엔드포인트 헬스체크
- `depends_on.condition: service_healthy`로 DB ready 후 앱 기동
