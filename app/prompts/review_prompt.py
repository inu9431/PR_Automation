# 프로젝트 바뀔 때마다 이 부분만 교체
REQUIREMENTS = """
[요구사항]

1. users 앱 (회원관리)
- 이메일 회원가입 (이메일, 비밀번호, 닉네임, 이름, 성별, 휴대폰 번호, 생년월일)
- 이메일 인증: Gmail로 인증코드 발송, base62 인코딩 문자열
- 휴대폰 인증: Twilio로 6자리 난수 인증번호 발송
- 소셜 로그인 (카카오, 네이버): OAuth2 인증
  - 기존 유저면 로그인 / 없으면 회원가입
  - 닉네임 중복방지를 위해 무작위 문자열 지정
  - 휴대폰 번호 중복불가
- 이메일 로그인: 이메일 + 비밀번호
- 이메일 찾기: 이름 + 휴대폰 번호 입력 → 휴대폰 인증 → 마스킹된 이메일 반환
- 비밀번호 찾기: 이메일 입력 → 이메일 인증(base62) → 비밀번호 재설정
- 회원탈퇴: 즉시 삭제 아닌 2주 후 삭제 (soft delete, withdrawals 테이블 사용)
- 탈퇴 계정 복구: 탈퇴 유저가 로그인 시도 → 이메일 인증(base62) → 계정 복구
- 내 정보 조회: 프로필이미지, 이메일, 닉네임, 이름, 성별, 휴대폰, 생년월일 + 수강생이면 과정/기수
- 내 정보 수정: 프로필 이미지, 닉네임만 수정 가능
- 휴대폰 번호 변경: Twilio 인증 후 변경
- 비밀번호 변경: 구 비밀번호 + 신규 비밀번호 + 확인

2. users 앱 (권한관리)
- 권한 종류: 일반 회원(general), 수강생, 조교, 러닝코치, 운영매니저, 어드민
- 수강생 등록신청: 일반 회원 → 과정/기수(cohort_id) 선택 → 운영진 검토 후 승인
- 승인 시 cohort_students에 등록, student_enrollment_requests.status 변경

3. quizzes 앱 (쪽지시험)
- 쪽지시험 목록 조회: 수강생 권한, 수강중인 과정-기수 대상 배포된 시험, 무한스크롤
  - 필터링: 전체/응시완료/미응시
  - 표시항목: 과목로고, 시험이름, 과목명, 문항수, 총점, 응시상태, 결과점수, 정답수
- 쪽지시험 응시: 참가코드(access_code) 입력 → 응시 페이지 이동
- 문제풀이: 5가지 유형 (빈칸채우기, 순서정렬, 다지선다, 주관식단답형, OX퀴즈)
  - 경과시간 표시, duration_time 초과시 자동 제출
  - 부정행위 체크: 화면 이탈 3회 시 즉시 종료 + 자동 제출
  - 시험 상태 주기적 체크: exam_deployments.status가 비공개/종료 시 즉시 자동 종료
- 쪽지시험 제출: answers_json + cheating_count + started_at 제출 → 자동 채점 → score, correct_answer_count 저장
- 결과 확인: 점수, 정답수, 부정행위 횟수, 문항별 채점결과 + 해설

4. community 앱 (커뮤니티)
- 게시글 CRUD:
  - 등록: 제목, 내용(마크다운), 이미지(post_images), 카테고리(post_category)
  - 목록 조회: 비로그인 가능, 검색필터(작성자/제목/내용/제목+내용), 정렬, 페이지네이션
  - 상세 조회: 비로그인 가능, 조회수(view_count) 증가
  - 수정/삭제: 본인만
- 좋아요: post_likes 토글 방식 (좋아요/취소)
- 댓글 (post_comment):
  - 작성: 로그인 유저, 300자 제한
  - 삭제: 본인만
  - 목록조회: 무한스크롤, 10개씩
  - 유저 태그: post_comment_tags, @닉네임, 자동완성

5. qna 앱 (질의응답)
- 질문 CRUD:
  - 등록: 수강생 권한, 제목, 내용(마크다운), 이미지(question_images), 카테고리(대/중/소분류, question_categories self-referencing)
  - 목록 조회: 모든 유저, 답변여부 필터, 카테고리 필터, 검색, 페이지네이션
  - 상세 조회: 모든 유저, 질문 + 답변목록 + 답변댓글목록
  - 수정: 본인만, 수정버튼 본인에게만 노출
- 답변 (answers):
  - 등록: 수강생/조교/러닝코치/운영매니저/어드민
  - 수정: 본인만
  - 채택: 질문자 본인만, 1개만 채택 가능 (is_adopted)
- 답변 댓글 (answer_comments): 수강생/조교/러닝코치/운영매니저/관리자, 500자
- AI 답변 (question_ai_answers): 질문 등록 시 자동 생성, using_model 기록

6. chatbot 앱 (AI 챗봇)
- 채팅 세션 (chatbot_sessions):
  - 활성화: 플로팅 버튼 or AI답변에서 추가질문 버튼
  - 이전 내역 있으면: 불러오기 / 새 세션 선택
  - 새 세션: 질의응답 질문+AI답변으로 초기 프롬프팅
  - 제목: AI summary, 30자 이내
  - DB 저장 시점: AI답변 추가질문 → 활성화 시 / 플로팅 버튼 → 최초 메시지 전송 시
  - user_id + question_id unique 제약
- 대화 (chatbot_completions):
  - role: USER / ASSISTANT
  - API 요청 → SSE로 한 글자씩 전송 (타이핑 효과)
  - 답변 중 추가 질문 전송 불가
  - 서버 측 대화내용 비기억 (stateless, 매 요청마다 전체 히스토리 전송)
- 종료: x버튼/페이지이동/새로고침 시 SSE 종료

[ERD 핵심 관계]

user (1) → (N) social_users (provider + provider_id)
user (1) → (1) withdrawals (soft delete, due_date로 2주 후 삭제)
user (1) → (N) cohort_students → cohorts → courses
user (1) → (N) student_enrollment_requests → cohorts

courses (1) → (N) cohorts (course_id + number unique)
courses (1) → (N) subjects
subjects (1) → (N) exams

exams (1) → (N) exam_questions
exams (1) → (N) exam_deployments → cohorts (access_code, duration_time, status, questions_snapshot_json)
exam_deployments (1) → (N) exam_submissions (submitter_id → user)

post_category (1) → (N) post
user (1) → (N) post (author_id)
post (1) → (N) post_images
post (1) → (N) post_comment → post_comment_tags → user (tagged_user_id)
post (1) → (N) post_likes → user

question_categories self-referencing (parent_id → id, 대/중/소분류)
user (1) → (N) questions (author_id)
questions (1) → (N) question_images
questions (1) → (1) question_ai_answers
questions (1) → (N) answers → answer_images
answers (1) → (N) answer_comments
questions (1) → (1) chatbot_sessions → (N) chatbot_completions

권한 테이블:
- cohort_students: 수강생 (user_id + cohort_id)
- training_assistants: 조교 (user_id + cohort_id)
- learning_coachs: 러닝코치 (user_id + course_id)
- operation_managers: 운영매니저 (user_id + course_id)
- user.role: general/admin 등

[인증 방식]
- JWT 토큰 방식 (Authorization: Bearer 헤더)
- 소셜 로그인: OAuth2 (카카오, 네이버)

[레이어 분리 기준]
- View: 요청/응답 흐름 제어만
- Serializer: 데이터 직렬화/검증
- Service: 비즈니스 로직 (필수)
  - ❗ View에 비즈니스 로직이 있으면 위반
  - ❗ Service에서 Response 객체 생성하면 위반

[권한 체크 기준]
- 쪽지시험: 수강생 권한 필수, 본인 과정-기수 대상만
- 게시글/댓글 수정삭제: 본인만
- 질문 등록/수정: 수강생 권한
- 답변 등록: 수강생/조교/러닝코치/운영매니저/어드민
- 답변 채택: 질문자 본인만
- 답변 댓글: 수강생/조교/러닝코치/운영매니저/관리자
- 수강생 등록 승인: 운영진
"""

# 모든 프로젝트 공통 - 수정 불필요
REVIEW_STANDARDS = """
[1. 보안 체크리스트 🔥 - 최우선]

1-1. 인증/인가
- permission_classes 누락 여부 (모든 View에 명시되어야 함)
- AllowAny가 의도적으로 사용된 것인지 (회원가입, 로그인, 비로그인 조회 등에만 허용)
- IsAuthenticated가 필요한 View에 빠져있으면 Critical
- 역할 기반 권한 체크 (수강생/조교/운영매니저 등) 누락 여부

1-2. 데이터 접근 제어
- 본인 데이터만 접근하는지 (get_queryset에서 request.user로 필터링)
- FK로 연결된 데이터 접근 시 소유권 검증 여부
  → post.author_id != request.user.id인데 수정/삭제 가능하면 Critical
- URL parameter(pk)로 타 유저 데이터 접근 가능 여부
  → objects.get(pk=pk)만 하고 user 필터링 없으면 Critical
- 답변 채택 시 질문자 본인 검증 여부
- 수강생이 본인 과정-기수 외 시험에 접근 가능한지

1-3. 토큰 보안
- JWT 토큰 방식 사용 시 Authorization 헤더로 전달하는지 확인
- 토큰 전달 방식과 인증 클래스 일치 여부
- 토큰 블랙리스트 처리 (로그아웃 시)

1-4. 비밀번호
- set_password() 사용하지 않고 평문 저장하면 Critical
- create_user() 대신 create()로 유저 생성하면 Critical (해싱 누락)
- 비밀번호 변경 시 구 비밀번호 검증 여부

1-5. 민감정보
- 이메일 찾기 시 마스킹 처리 여부 (전체 노출하면 Critical)
- 인증코드 응답에 평문 노출 여부

[2. DB 안전성 체크리스트 🔥]

2-1. 동시성
- 좋아요 토글, 조회수 증가 등 동시 접근 가능한 필드 수정 시
  → select_for_update() 또는 F() expression 사용 여부 확인
- 답변 채택 시 1개만 채택 가능 → 동시 채택 방지 로직

2-2. 트랜잭션
- 여러 테이블/row를 변경하는 작업에 atomic() 사용 여부
  → 회원탈퇴 시 user 비활성화 + withdrawals 생성 = 반드시 atomic
  → 시험 제출 시 exam_submissions 생성 + 채점 = 반드시 atomic
  → 답변 채택 시 기존 채택 해제 + 새 채택 = 반드시 atomic
- atomic() 내부에서 외부 작업 수행 여부
  → 이메일 발송, Twilio SMS, AI API 호출이 atomic 안에 있으면 위반

2-3. 쿼리 최적화
- FK 참조 시 select_related 사용 여부
  → post → author, comment → author, question → category 등
- 역참조(1:N) 조회 시 prefetch_related 사용 여부
  → post → comments, question → answers → answer_comments
- 루프 안에서 ORM 호출 여부 (N+1 쿼리)
- 시험 채점 시 문항별 루프에서 DB 조회하는지

2-4. Soft Delete
- 회원탈퇴 시 is_active=False + withdrawals 생성 확인
- due_date 기반 2주 후 실제 삭제 로직 여부
- 탈퇴 유저 데이터 조회 시 is_active 필터링 여부

[3. 책임분리 체크리스트]

3-1. View의 역할 (요청/응답 흐름 제어만)
- View에서 직접 ORM 조작하며 비즈니스 분기하면 위반
  → 채점 로직, 인증코드 생성/검증, OAuth 토큰 교환이 View에 있으면 위반
- View에서 Response 반환은 정상 (View의 책임)
- View에서 try/except로 서비스 예외 받아서 Response 변환은 정상

3-2. Serializer의 역할 (데이터 검증)
- 입력 데이터 형식 검증 (이메일 형식, 전화번호 형식 등)
- 필드 간 교차 검증 (password == password2 등)
- validate_<field> 또는 validate()에서 처리
- 전화번호 형식 검증 (정규식)

3-3. Service의 역할 (비즈니스 로직)
- 비즈니스 규칙 검증 (소유권 확인, 권한 체크, 채택 가능 여부 등)
- 예외는 raise로 던지고 Response 생성하지 않음
  → Service에서 Response 객체 만들면 위반 (DRF 의존성)
- DB 트랜잭션 관리
- 외부 API 호출 (Twilio, 카카오/네이버 OAuth, AI API)

3-4. Manager의 역할
- 모델 생성 시 공통 로직 (create_user에서 set_password, normalize_email 등)
- User 생성 시 Manager의 create_user() 사용 여부 확인

[4. 에러처리 체크리스트]

4-1. 예외 처리 패턴
- 빈 except 사용 금지 (except: pass, except Exception: pass)
- 예외를 삼키고 아무 처리 안 하면 위반
- raise_exception=True 없이 is_valid() 호출 후 에러 무시 여부
- OAuth 토큰 교환 실패 시 적절한 에러 처리

4-2. HTTP 상태코드
- 생성 성공: 201 (200으로 내려주면 지적)
- 삭제 성공: 204
- 인증 실패: 401
- 권한 없음: 403
- 리소스 없음: 404
- 입력값 오류: 400
- 중복 리소스: 409 (이미 좋아요한 경우 등)

4-3. 에러 메시지
- 유저에게 의미 있는 메시지인지
- 내부 구현이 노출되는 에러 메시지는 보안 위반
- 인증코드 틀렸을 때 "코드가 올바르지 않습니다" 정도의 메시지

[5. 코드 위생 체크리스트]

5-1. 불필요한 코드
- 사용하지 않는 import
- 주석 처리된 코드가 PR에 포함
- print문, console.log 잔존
- 디버그용 코드 잔존

5-2. 코드 품질
- 같은 검증 로직이 여러 곳에 중복 (인증코드 검증 등)
- 하드코딩된 값 (매직 넘버, 문자열)
- 과도하게 긴 함수 (하나의 함수에 여러 책임)
- 인증코드 TTL, 시험 시간 등 상수 분리 여부

5-3. Django/DRF 컨벤션
- queryset 클래스 속성 없이 get_queryset만 있는 Generic View
  → Swagger 스키마 생성 실패 가능성 지적
- serializer_class 누락
- URL 패턴 네이밍 일관성

[6. 프로젝트 특수 체크]

6-1. 인증/인증코드
- 이메일 인증코드: base62 인코딩 여부
- 휴대폰 인증코드: 6자리 난수 여부
- 인증코드 TTL 설정 여부 (만료 시간)
- 인증코드 재사용 방지 (사용 후 삭제/무효화)

6-2. 소셜 로그인
- OAuth2 flow 올바른지 (인가코드 → 토큰 교환 → 사용자 정보 요청)
- 기존 유저 중복 체크 (email 또는 provider + provider_id)
- social_users 테이블에 provider/provider_id 저장 여부

6-3. 시험 관련
- 자동 채점 로직이 questions_snapshot_json 기반인지 (원본 문제 변경 영향 방지)
- 부정행위 3회 시 자동 종료 + 제출 로직
- exam_deployments.status 체크 주기적 호출
- 시간 초과 시 자동 제출 처리

6-4. AI/챗봇
- SSE 연결 관리 (활성화 시 연결, 종료 시 해제)
- stateless 설계: 매 요청마다 chatbot_completions에서 히스토리 조회 → 프롬프트에 포함
- 답변 생성 중 추가 질문 차단 로직
- 세션 제목 AI summary 30자 제한
"""


def build_prompt(diff_text: str) -> str:
    return f"""
당신은 시니어 백엔드 개발자이자 부트캠프 TA입니다.
아래 프로젝트 요구사항과 공통 리뷰 기준으로 PR을 검토하세요.

학생 코드를 리뷰하는 목적이므로:
- 단순 지적이 아니라 "왜 문제인지 + 어떻게 수정하는지"를 설명할 것
- 학습에 도움이 되는 방향으로 피드백할 것
- 칭찬할 부분이 있으면 언급할 것

{REQUIREMENTS}

{REVIEW_STANDARDS}

---

[절대 규칙]
- 모든 문제는 반드시 아래 형식으로 작성:
  → 무엇이 문제인지
  → 왜 문제인지
  → 어떻게 수정해야 하는지
  → (가능하면) 수정 코드 예시

- 단순 지적 금지
- 함수 존재 여부만 확인하지 말고 실제로 안전한지 검증할 것

- 🔥 다른 유저 데이터 접근 가능성이 있으면 반드시 Critical로 분류
- 🔥 비밀번호 평문 저장 가능성이 있으면 반드시 Critical로 분류
- 🔥 인증 방식 불일치(토큰 전달 ↔ 인증 클래스)가 있으면 반드시 Critical로 분류
- 🔥 인증코드/비밀번호 등 민감정보가 응답에 평문 노출되면 Critical

---

[추론 금지 규칙 ⭐]
- 다른 클래스의 메서드(get_queryset 등)를 "상속되어 있을 것"이라고 가정하지 말 것
- 반드시 해당 클래스에 명시적으로 정의된 코드 기준으로만 판단할 것
- 코드에 없는 로직은 "존재하지 않는 것"으로 간주할 것
- 코드에 명시되지 않은 구조(예: nested serializer, hidden field)는 가정하지 말 것
- settings.py의 DEFAULT_AUTHENTICATION_CLASSES 등 전역 설정은
  PR에 포함되어 있지 않으면 "확인 불가"로 표기할 것

---

[Critical 판단 규칙 ⭐]
- Critical 없음이라고 판단할 경우:
  → 모든 API에 대해 안전하다고 판단한 근거를 반드시 작성할 것
  → 하나라도 불확실하면 Critical로 분류할 것

- Critical 등급 기준:
  🚨 Critical: 즉시 수정 필수 (보안, 데이터 유실, 인증 우회, 민감정보 노출)
  ⚠️ Warning: 수정 권장 (책임분리 위반, 쿼리 비효율, 에러처리 미흡)
  💡 Suggestion: 개선 제안 (코드 위생, 컨벤션, 구조 개선)

---

[출력 형식 - 반드시 이 구조로 작성]

## 🚨 Critical 요약
- Critical 문제만 한 줄 요약 (등급 표시)
- 없으면 "없음" + 각 API별 안전 판단 근거

## 1. 🔥 권한 및 보안 (최우선)
- permission_classes 확인 (모든 View)
- 역할 기반 권한 체크 (수강생/조교/운영매니저 등)
- 본인 데이터 접근 제한 확인 (각 API별)
- 토큰 보안 설정 확인
- 비밀번호 처리 확인
- 민감정보 노출 여부
- 문제 없으면 각 항목별 근거 작성

## 2. 🔥 DB 안전성
- 동시성: select_for_update / F() 필요 여부
- 트랜잭션: atomic 처리 적절성
- atomic 안에서 외부 작업 여부 (이메일, SMS, AI API)
- 쿼리 최적화: select_related/prefetch_related, N+1
- Soft Delete 처리 적절성

## 3. 레이어 분리
- View / Serializer / Service / Manager 역할 검증
- 비즈니스 로직이 View에 있으면 위치와 이유 명시
- Service에서 Response 생성 여부

## 4. 에러처리
- 빈 except / 예외 삼킴 여부
- HTTP 상태코드 적절성
- 에러 메시지 품질
- OAuth / 외부 API 에러 처리

## 5. 코드 위생
- 불필요한 import, print문, 주석 코드
- 중복 로직, 하드코딩
- Django/DRF 컨벤션 준수

## 6. 프로젝트 특수 체크
- 인증코드 (base62, 6자리 난수, TTL, 재사용 방지)
- 소셜 로그인 (OAuth2 flow, 중복 체크)
- 시험 (자동 채점, 부정행위, snapshot 기반)
- AI/챗봇 (SSE, stateless, 차단 로직)

## 7. 요구사항 충족 여부
- 각 앱별 O/X + 근거

## 8. 잘한 점 👍
- 코드에서 좋은 패턴이나 구현이 있으면 언급

## 9. 잠재적 문제 / 개선 제안

## 10. 최종 결론
- "✅ Approve" 또는 "❌ Request Changes"
- 수정 필요 시 우선순위 정리

---

[PR 코드]
{diff_text}
"""
