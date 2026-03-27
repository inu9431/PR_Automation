# 트러블슈팅

## 개발 중 발견한 이슈와 해결

### 1. async 컨텍스트에서 동기 Claude API 호출 (이벤트 루프 블로킹)

**위치**: `app/services/reviewer.py`

**문제**: `anthropic.Anthropic()`의 `messages.create()`는 동기 함수다. FastAPI의 BackgroundTask는 async로 실행되는데, 이 안에서 동기 호출을 하면 이벤트 루프가 블로킹된다. 현재 단일 요청에서는 동작하지만, 동시에 여러 PR이 오픈되면 하나의 Claude API 응답이 완료될 때까지 다른 태스크가 대기하게 된다.

**원인**: `Anthropic` 클라이언트가 내부적으로 `requests`(동기 HTTP)를 사용하기 때문.

**해결**: `AsyncAnthropic` 클라이언트로 교체하면 `await`로 비동기 호출이 가능하다.

```python
# Before: 동기 클라이언트 (이벤트 루프 블로킹)
from anthropic import Anthropic
client = Anthropic()
response = client.messages.create(...)

# After: 비동기 클라이언트
from anthropic import AsyncAnthropic
client = AsyncAnthropic()
response = await client.messages.create(...)
```

**현재 상태**: 리팩토링 시 `AsyncAnthropic`으로 교체 완료.

---

### 2. BackgroundTask에서 DB 세션 수명 불일치

**위치**: `app/api/webhook.py`

**문제**: 요청 핸들러에서 생성된 DB 세션(Depends로 주입)을 BackgroundTask에 넘기면, 요청이 끝난 시점에 세션이 닫힐 수 있다. BackgroundTask는 응답 반환 후 실행되므로, 이미 닫힌 세션으로 DB 작업을 시도하면 `SessionClosedError`가 발생한다.

**원인**: FastAPI의 Depends 세션은 요청 라이프사이클에 바인딩되어 있다. BackgroundTask는 요청 라이프사이클 밖에서 실행된다.

**해결**: BackgroundTask 내부에서 세션을 새로 생성한다.

```python
async def review_pr_background(...):
    async with SessionLocal() as db:
        await review_pr(..., db=db)
```

---

### 3. 비용 집계 시 전체 레코드 메모리 로딩

**위치**: `app/services/cost_logger.py`

**문제**: `get_total_cost()`가 `CostLog` 테이블의 전체 행을 Python 메모리에 올린 뒤 `sum()`으로 집계한다. PR이 수십 건일 때는 문제없지만, 수백~수천 건으로 늘어나면 불필요한 메모리 사용과 쿼리 시간이 발생한다.

**원인**: ORM의 편의성에 의존해 SQL 집계를 사용하지 않은 것.

**해결**: DB 레벨에서 SQL 집계 함수로 처리한다.

```python
from sqlalchemy import func

result = db.query(
    func.count(CostLog.id),
    func.sum(CostLog.cost_usd),
    func.sum(CostLog.cost_krw),
).one()
```

**현재 상태**: 리팩토링 완료.

---

### 4. BackgroundTask 내 예외가 조용히 무시되는 문제

**위치**: `app/services/reviewer.py`

**문제**: `review_pr()` 함수에서 GitHub API, Claude API, DB 저장, Discord 전송 중 어디서든 예외가 발생하면 BackgroundTask 안에서 조용히 죽었다. 로그가 없어서 실패 원인을 파악할 수 없었다.

**원인**: BackgroundTask는 응답 반환 후 실행되므로, 예외가 발생해도 HTTP 응답에 반영되지 않는다. 별도 에러 핸들링이 없으면 실패 사실 자체를 알 수 없다.

**해결**: 각 단계를 try/except로 감싸고 `logging`으로 에러를 기록했다. 단계별 실패 영향이 다르므로 중단 여부를 구분했다.

- GitHub diff 실패 / Claude API 실패 → `return`으로 중단 (이후 단계 실행 불가)
- DB 저장 실패 → 중단하지 않고 Discord 전송 이어서 진행 (리뷰 결과 전달이 더 중요)

**현재 상태**: 리팩토링 완료. 에러 발생 시 `docker compose logs -f web`에서 단계별 실패 원인 확인 가능.

---

### 5. Webhook 진입점에서 입력 검증 부재

**위치**: `app/api/webhook.py`

**문제**: 잘못된 JSON이나 필수 필드(`repo`, `pr_number`)가 누락된 payload가 들어와도 검증 없이 BackgroundTask에 등록됐다. `None` 값으로 GitHub API URL이 생성되어 의미 없는 404 에러가 백그라운드에서 발생했다.

**원인**: Webhook 진입점에서 payload 유효성을 확인하지 않은 것.

**해결**: `request.json()` 파싱 실패 시 예외처리, `repo_full_name`과 `pr_number` 존재 여부 확인 후 없으면 에러 응답 반환하도록 수정.

**현재 상태**: 리팩토링 완료.

---

## 운영 중 자주 발생하는 문제

### Webhook이 수신되지 않을 때

1. ngrok이 실행 중인지 확인: `ngrok http 8000`
2. GitHub Webhook Payload URL이 현재 ngrok URL과 일치하는지 확인 (ngrok은 재시작마다 URL이 바뀐다)
3. GitHub Webhook 설정에서 Events가 `Pull requests`만 체크되어 있는지 확인 (push 이벤트가 체크되어 있으면 불필요한 요청이 들어온다)

---

### Discord에 메시지가 오지 않을 때

1. `.env`의 `DISCORD_WEBHOOK_URL`이 올바른지 확인
2. PR diff가 매우 클 경우 Claude API 응답이 오래 걸릴 수 있음 → 서버 로그에서 진행 상태 확인
3. `discord_client.py`에서 에러가 발생했는지 로그 확인

```bash
docker compose logs -f web
```

---

### DB 연결 오류

```
sqlalchemy.exc.OperationalError: could not connect to server
```

PostgreSQL 컨테이너가 아직 ready 상태가 아닐 때 발생한다. `docker-compose.yml`에서 `depends_on.condition: service_healthy`가 설정되어 있는지 확인. 헬스체크가 통과한 후 웹 서비스가 기동되어야 한다.

---

### Claude API 비용이 예상보다 높을 때

- `app/prompts/review_prompt.py`의 `REQUIREMENTS`가 너무 길면 input 토큰이 증가한다. 요구사항을 간결하게 유지할 것.
- PR diff 크기가 클수록 비용이 증가한다. `get_pr_diff_text()`에서 파일별 diff 크기 상한을 설정하는 것을 고려.

---

## 프롬프트 이터레이션 기록

실제 PR을 테스트하면서 프롬프트를 반복 개선한 과정.

---

### 1차: 초기 프롬프트 — 체크리스트 수준

**문제**: "부트캠프 조교" 페르소나 + 요구사항 충족 O/X 순서로 구성. 리뷰가 단순 지적 수준에 그쳤고, 권한/보안 섹션이 아예 없었다. 레이어 분리 지적도 "섞여있다"에서 끝나고 왜 문제인지, 어떻게 고쳐야 하는지가 없었다.

**개선 방향**: 페르소나를 시니어 개발자로 교체, 리뷰 규칙 순서를 권한/보안 → 레이어 → 요구사항으로 변경, 모든 문제에 "무엇/왜/어떻게" 형식 강제.

---

### 2차: 출력 형식 강제 — 섹션 누락 문제

**문제**: 리뷰 규칙 순서를 바꿨는데도 LLM이 자기 스타일로 출력해서 권한 섹션 자체가 누락됐다. 규칙만 줘서는 LLM이 무시하는 경우가 생긴다.

**개선 방향**: `[출력 형식 - 반드시 이 구조로 작성]` 블록 추가. 각 섹션을 헤더로 강제하고, 문제 없을 때도 "문제 없음" + 이유를 명시하도록 요구.

---

### 3차: Critical 요약 섹션 추가

**문제**: 리뷰 내용이 길어지면서 핵심 파악에 시간이 걸렸다. 조교 입장에서 디코 메시지를 열자마자 위험 여부를 파악해야 한다.

**개선 방향**: 출력 최상단에 `## 🚨 Critical 요약` 섹션 추가. Critical 문제만 한 줄씩 요약, 없으면 "없음" + 근거 명시. 이것만 보면 10초 안에 위험 여부 판단 가능.

---

### 4차: 추론 금지 규칙 추가 — False Positive 발생

**문제**: `TransactionDetailView`에 `get_queryset`이 없는데 "다른 View에서 상속될 것"이라고 추론해서 "문제 없음" 판정을 내렸다. 실제로는 권한이 뚫려 있는 상태.

**개선 방향**: `[추론 금지 규칙]` 블록 추가.
- 다른 클래스의 메서드를 상속되어 있을 것이라고 가정 금지
- 해당 클래스에 명시적으로 정의된 코드 기준으로만 판단
- 코드에 없는 로직은 존재하지 않는 것으로 간주

---

### 5차: Serializer 추론 금지 추가 — False Positive 2차 발생

**문제**: `AccountDetailView.put`에서 "AccountSerializer가 nested transaction 필드를 받을 수도 있으니 위험하다"는 Critical이 나왔다. 코드에 nested serializer가 없는데 존재할 수도 있다고 추론한 False Positive.

**개선 방향**: 추론 금지 규칙에 추가.
- Serializer에 정의되지 않은 필드나 nested 관계를 가정하지 말 것
- 코드에 명시되지 않은 구조는 추측하지 말 것

---

### 최종 상태

- 리뷰 우선순위: 권한/보안 → 레이어 분리 → 요구사항
- Critical 요약이 최상단에 위치 → 조교가 3~5초 안에 위험 여부 파악 가능
- 추론 없이 명시된 코드만 기준으로 판단
- False Positive 거의 없는 수준

---

## 프로젝트 교체 시 체크리스트

매달 프로젝트가 바뀔 때 확인할 항목:

- [ ] `app/prompts/review_prompt.py`의 `REQUIREMENTS` 업데이트 (새 프로젝트의 요구사항 + ERD)
- [ ] 기존 비용 로그 초기화 여부 결정 (`CostLog` 테이블 truncate 또는 유지)
- [ ] GitHub Webhook을 새 레포로 재설정 (Payload URL, Events)
- [ ] 테스트 PR로 Discord 수신 확인
