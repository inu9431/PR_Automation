# 프로젝트 바뀔 때마다 이 부분만 교체
REQUIREMENTS = """
[요구사항]
1. users 앱 (APIView 직접 구현)
- 회원가입, 로그인, 로그아웃, 회원정보 수정/삭제
- 로그인: 인증 → 토큰 생성 → 쿠키 세팅
- 로그아웃: 쿠키 삭제 + 블랙리스트 처리

2. accounts 앱 (APIView 직접 구현)
- 계좌 생성/조회/삭제 (CRD)
- 객체 조회, 권한 체크, 시리얼라이저 호출, 에러 처리 직접 구현

3. transactions 앱 (Generic View 사용)
- 거래내역 CRUD + 필터링
- ListCreateAPIView, RetrieveUpdateDestroyAPIView 사용
- get_queryset(): 본인 거래내역만 필터링
- perform_create(): request.user를 거래내역에 자동 연결

[ERD]
account
- id (PK)
- user (FK → User)

Transaction
- id (PK)
- account (FK → Account)
- type
- amount
- date

[레이어 분리 기준]
- View: 요청/응답 처리만
- Serializer: 데이터 직렬화/검증

- ❗ accounts 앱:
  View에 아래 로직이 있으면 위반:
  - 잔액 계산
  - 계좌 소유권 검증
  - 비즈니스 조건 분기

- ❗ transactions 앱:
  - get_queryset / perform_create 반드시 오버라이드
  - Generic View 기본 동작 무시 시 위반

[view 선택 기준]
- accounts: APIView
- transactions: Generic View
"""

def build_prompt(diff_text: str) -> str:
    return f"""
당신은 시니어 백엔드 개발자입니다.
아래 요구사항을 기준으로 PR을 실무 코드 리뷰 수준으로 검토하세요.

{REQUIREMENTS}

---

[절대 규칙]
- 모든 문제는 반드시 아래 형식으로 작성:
  → 무엇이 문제인지
  → 왜 문제인지
  → 어떻게 수정해야 하는지

- 단순 지적 금지
- 함수 존재 여부만 확인하지 말고 실제로 안전한지 검증할 것

- 🔥 다른 유저 데이터 접근 가능성이 있으면 반드시 Critical로 분류

---

[추론 금지 규칙 ⭐]
- 다른 클래스의 메서드(get_queryset 등)를 "상속되어 있을 것"이라고 가정하지 말 것
- 반드시 해당 클래스에 명시적으로 정의된 코드 기준으로만 판단할 것
- 코드에 없는 로직은 "존재하지 않는 것"으로 간주할 것
- 코드에 명시되지 않은 구조(예: nested serializer, hidden field)는 가정하지 말 것

---

[Critical 판단 규칙 ⭐]
- Critical 없음이라고 판단할 경우:
  → 모든 API에 대해 안전하다고 판단한 근거를 반드시 작성할 것
  → 하나라도 불확실하면 Critical로 분류할 것

---

[출력 형식 - 반드시 이 구조로 작성]

## 🚨 Critical 요약
- Critical 문제만 한 줄 요약
- 없으면 "없음" + 근거 작성

## 1. 🔥 권한 및 보안 검증
- 각 API별 접근 제어 검증
- 타 유저 데이터 접근 가능 여부 반드시 판단
- 반드시 "명시된 코드 기준"으로만 판단
- 문제 없으면 "문제 없음" + 근거 작성

## 2. 🔥 레이어 분리 위반
- View / Serializer 역할 검증
- 문제 없으면 "문제 없음"

## 3. 요구사항 충족 여부 (O/X)
- 파일명 + 근거 포함

## 4. 전체 변경 흐름
- 기능 흐름 중심 요약

## 5. 잠재적 문제
- N+1
- 트랜잭션
- 예외 처리
- 성능

## 6. 최종 결론
- "✅ 이상 없음" 또는 "❌ 확인 필요"

---

[추가 강제 규칙]
- 권한/보안 섹션 절대 생략 금지
- get_queryset / perform_create:
  → "존재 여부"가 아니라 "보안적으로 충분한지" 평가할 것
- 클래스 간 상속 추론 금지
- 불확실하면 안전한 쪽이 아니라 "문제 있음"으로 판단

---

[PR 코드]
{diff_text}
"""