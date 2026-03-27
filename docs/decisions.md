# 의사결정 기록

## 프로젝트 배경

부트캠프 조교로서 한 달 단위 메인 프로젝트 2개를 병행하며 수강생 PR을 리뷰한다. PR이 쌓일수록 전부 직접 읽는 건 시간적으로 한계가 있었다.

**문제 정의**: 전체 흐름 파악, 레이어 분리 여부, 요구사항 충족 확인 같은 기계적 검토에 시간이 과도하게 소요된다.

**해결 방향**: 기계적 검토를 LLM에 위임하고, 조교는 LLM 초안을 검증한 뒤 코드 품질·설계에 대한 최종 판단만 직접 한다. GitHub Webhook → LLM 리뷰 → Discord 전송까지의 파이프라인을 자동화한다.

---

## 기술 스택 선택 근거

### 웹 프레임워크: FastAPI (vs Django, Flask)

| 기준 | FastAPI | Django | Flask |
|------|---------|--------|-------|
| async 네이티브 지원 | O | 부분적 (ASGI 전환 필요) | X (별도 라이브러리) |
| 이 프로젝트에서 필요한 기능 | Webhook 수신 + 외부 API 호출 | 과잉 (admin, ORM, template 등) | 가능하나 async 약함 |
| BackgroundTasks 내장 | O | X (Celery 등 별도 구성) | X |

이 프로젝트는 Webhook 수신 → 외부 API 3곳 호출(GitHub, Claude, Discord) → DB 저장이 전부다. Django의 admin, template engine, built-in ORM은 사용하지 않으므로 과잉이고, Flask는 async 처리에 추가 설정이 필요하다.

FastAPI는 async 네이티브이면서 `BackgroundTasks`가 내장되어 있어 GitHub의 10초 타임아웃 제약을 별도 태스크 큐(Celery 등) 없이 해결할 수 있다. 외부 API 호출이 핵심인 이 프로젝트 특성에 가장 적합하다.

---

### HTTP 클라이언트: httpx (vs requests, aiohttp)

| 기준 | httpx | requests | aiohttp |
|------|-------|----------|---------|
| async 지원 | O (AsyncClient) | X | O |
| sync/async 모두 가능 | O | sync만 | async만 |
| requests 호환 API | O | - | X (API 다름) |

이 프로젝트는 GitHub API, Discord Webhook을 모두 async 컨텍스트에서 호출한다. `requests`를 async 함수 안에서 쓰면 이벤트 루프를 블로킹해서 동시 요청 처리가 불가능하다.

`aiohttp`도 가능하지만 API가 `requests`와 다르고, httpx는 `requests` 호환 인터페이스를 제공하면서 `AsyncClient`로 async 처리가 가능하다. 학습 비용 대비 효용이 가장 높다.

---

### 데이터베이스: PostgreSQL + SQLAlchemy (vs SQLite, 파일 저장)

| 기준 | PostgreSQL | SQLite | JSON 파일 |
|------|-----------|--------|-----------|
| ACID 보장 | O | 부분적 | X |
| 동시 쓰기 | O | 제한적 (write lock) | X |
| 프로덕션 운영 | 적합 | 개발/테스트용 | 부적합 |
| 집계 쿼리 | SQL 집계 함수 사용 가능 | 가능하나 성능 제한 | 직접 구현 필요 |

비용 로그는 **누락되면 안 되는 데이터**다. Claude API 호출 비용이 얼마나 발생하는지 추적하는 것이 이 시스템의 부가 목적이고, BackgroundTask에서 비동기로 INSERT가 발생하므로 동시 쓰기가 안전해야 한다.

SQLite는 동시 쓰기 시 write lock 경합이 발생할 수 있고, JSON 파일은 ACID 보장이 없다. PostgreSQL은 Docker Compose로 원커맨드 구성이 가능하고, 나중에 프로젝트별 비용 집계 등 확장 시 SQL 집계 함수를 바로 사용할 수 있다.

ORM은 SQLAlchemy를 선택했다. FastAPI 생태계에서 가장 넓게 쓰이고, 세션 관리와 마이그레이션(Alembic) 지원이 성숙하다.

---

### 패키지 매니저: uv (vs pip, Poetry)

| 기준 | uv | pip | Poetry |
|------|-----|-----|--------|
| 설치 속도 | 매우 빠름 (Rust 기반) | 느림 | 보통 |
| lock 파일 | O (`uv.lock`) | X (수동 freeze) | O |
| Docker 빌드 시간 | 짧음 | 김 | 보통 |

pip은 lock 파일이 없어 `pip freeze > requirements.txt`를 수동으로 관리해야 하고, 재현 가능한 빌드가 보장되지 않는다. Poetry는 가능하지만 설치 속도가 uv 대비 느리고, Docker 이미지 빌드 시간에 직접적으로 영향을 준다.

uv는 Rust 기반으로 설치 속도가 빠르고, `uv.lock`으로 재현 가능한 빌드를 보장한다. CI/CD에서 Docker 이미지 빌드 시간 단축 효과가 크다.

---

### LLM: Claude Sonnet 4.5 (vs GPT-4o, Claude Opus 등)

| 기준 | Claude Sonnet 4.5 | GPT-4o | Claude Opus |
|------|-------------|--------|-------------|
| 코드 리뷰 품질 | 충분 | 충분 | 과잉 (비용 대비) |
| 가격 (input/output) | $3/$15 per 1M tokens | $2.5/$10 | $15/$75 |
| 응답 속도 | 빠름 | 빠름 | 느림 |

코드 리뷰의 목적이 "요구사항 충족 여부"와 "레이어 분리 확인"이라는 기계적 검토이므로, 최상위 모델이 필요하지 않다. Sonnet 4.5는 이 수준의 검토에 충분한 성능을 제공하면서 비용이 합리적이다.

---

## 설계 결정

### LLM이 GitHub에 직접 코멘트 달지 않는 이유

Claude의 리뷰 기준은 `REQUIREMENTS`에 정의된 요구사항과 ERD다. 요구사항 충족 여부는 기계적으로 판단 가능하지만, **코드 품질이나 설계 판단은 조교가 직접 해야 한다**.

LLM 코멘트가 자동으로 GitHub에 올라가면 수강생이 이를 최종 피드백으로 오인할 수 있다. 따라서 LLM 초안을 Discord로 먼저 받아 조교가 검토한 뒤, 필요한 부분만 GitHub에 직접 등록하는 워크플로우를 선택했다.

---

### 프롬프트를 별도 파일로 분리한 이유

프로젝트가 2개이고 각각 요구사항과 ERD가 다르다. 리뷰 로직(`reviewer.py`)은 건드리지 않고 `REQUIREMENTS` 상수만 교체하면 다음 프로젝트에 바로 재사용할 수 있도록 `prompts/review_prompt.py`로 분리했다.

실제 교체 시 변경 파일이 1개(`review_prompt.py`)뿐이므로, 실수로 로직을 건드릴 위험이 없다.

---

### max_tokens=1500 제한 이유

Discord 메시지 상한이 2000자다. 어차피 2000자를 넘기면 잘라서 보내야 하는데, 잘릴 응답을 길게 생성하는 건 토큰 비용 낭비다. 생성 자체를 1500으로 제한해서 불필요한 output 토큰 소비를 방지했다.

---

### KRW 환율 하드코딩 (1:1400) 이유

정확한 금액 정산이 목적이 아니라 "지금까지 API 비용을 얼마나 쓰고 있는지" 대략적으로 파악하는 것이 목적이다. 환율 API 연동은 별도 에러 핸들링, API 키 관리, 요청 실패 시 폴백 처리 등 복잡도가 추가되는데, 이 프로젝트에서 그 정도의 정확성이 필요하지 않다고 판단했다.

---

### BackgroundTasks 사용 이유 (vs Celery)

GitHub Webhook은 응답을 약 10초 이내에 받지 못하면 재전송한다. Claude API 호출에 수 초가 걸리므로, 즉시 `{"status": "ok"}`를 반환하고 리뷰는 백그라운드에서 처리해야 한다.

Celery를 쓰면 Redis/RabbitMQ 같은 메시지 브로커가 추가로 필요하다. 이 프로젝트는 단일 워커에서 PR당 1개 태스크만 실행하면 되는 수준이므로, FastAPI 내장 `BackgroundTasks`로 충분하다. 인프라 복잡도를 늘릴 이유가 없다.

---

## 리팩토링 기록

AI가 생성한 초기 코드를 코드 리딩 후 아래 항목을 리팩토링했다. 각 항목은 문제 → 원인 → 수정 내용 → 판단 근거 순서로 기록한다.

### webhook.py: 입력 검증 추가

**문제**: GitHub 외의 요청이나 잘못된 payload가 들어와도 검증 없이 BackgroundTask에 등록됐다. `repo`나 `pr_number`가 `None`인 채로 백그라운드 작업이 돌아가면, GitHub API 호출 시 잘못된 URL이 생성되어 의미 없는 에러가 발생한다.

**수정 내용**:
- `request.json()` 파싱 실패 시 예외처리 추가
- `repo_full_name`과 `pr_number`가 없으면 BackgroundTask 등록하지 않고 에러 응답 반환

**판단 근거**: BackgroundTask는 응답 반환 후 실행되므로, 잘못된 데이터가 들어가면 디버깅이 어렵다. 진입점에서 필수 데이터를 검증해야 불필요한 백그라운드 실행을 방지할 수 있다.

---

### reviewer.py: 단계별 예외처리 + 로깅 추가

**문제**: `review_pr()` 함수 안에서 GitHub diff 조회, Claude API 호출, DB 저장, Discord 전송 중 어디서든 실패하면 BackgroundTask 안에서 조용히 죽었다. 로그가 없어서 어디서 실패했는지 알 수 없었다.

**수정 내용**:
- 각 단계를 try/except로 감싸고 `logging`으로 에러 기록
- GitHub diff 실패, Claude API 실패 시 `return`으로 중단 (이후 단계 실행 불가)
- DB 저장 실패 시에는 중단하지 않고 Discord 전송은 이어서 진행 (리뷰 자체는 성공했으므로)

**판단 근거**: 단계별로 실패 영향이 다르다. diff가 없으면 리뷰 자체가 불가능하므로 중단해야 하지만, DB 저장 실패는 리뷰 결과 전달과 무관하므로 Discord 전송까지는 이어가는 것이 사용자(조교) 입장에서 합리적이다.

---

### reviewer.py + config.py: 하드코딩 값 설정 분리

**문제**: 모델명(`"claude-sonnet-4-5"`), `max_tokens=1500`, 토큰 단가(`3`, `15`)가 서비스 코드에 직접 박혀 있었다. 모델 변경이나 단가 업데이트 시 서비스 로직 파일을 수정해야 했다.

**수정 내용**:
- `config.py`의 `Settings`에 `claude_model`, `claude_max_tokens`, `claude_input_price`, `claude_output_price` 추가
- `reviewer.py`에서 `settings`로 참조하도록 변경
- `.env`에 값을 넣으면 기본값을 덮어쓰고, 안 넣으면 기본값으로 동작

**판단 근거**: 설정값은 환경에 따라 바뀔 수 있는 값이다. 서비스 로직과 설정을 분리하면 코드 수정 없이 `.env`만 바꿔서 모델 교체나 단가 변경에 대응할 수 있다. 프롬프트를 별도 파일로 분리한 것과 같은 원칙(변경 가능한 것을 로직에서 분리)이다.
