# TrustLens Feature Specification

## 1. 문서 목적

이 문서는 TrustLens MVP의 기능 요구사항과 완료 조건을 정의한다.

세부 기준:

- API: `docs/API_SPEC.md`
- DB: `docs/DB_SCHEMA.md`
- Prompt: `docs/PROMPTS.md`
- 점수: `docs/TRUST_SCORE.md`
- UI: `docs/UI_FLOW.md`

---

## 2. 전체 흐름

```text
질문 입력
→ 답변 목적 선택
→ 질문 개선 Modal
→ 분석 생성
→ 다중 AI 답변
→ Claim 추출·통합
→ 검증 방식 분류
→ Deterministic Check 또는 Web Search
→ Chunking·Embedding·Hybrid Search
→ Evidence Pack
→ Claim Verification
→ Cross Review
→ Risk Analysis
→ Trust Score
→ Final Answer
→ 결과 저장
```

---

## 3. F-01 질문 입력

기능:

- 자유 텍스트 입력
- 최소 2자, 최대 2000자
- 공백만 입력 금지
- 글자 수 표시
- 예시 질문 선택
- 입력 수정 시 이전 질문 개선 결과 초기화

완료 조건:

```text
[ ] Validation 동작
[ ] 중복 클릭 방지
[ ] 오류 메시지 표시
```

---

## 4. F-02 답변 목적 선택

지원 값:

```text
fact_check
concept_understanding
decision_support
evidence_focused
risk_analysis
```

- 한 번에 하나만 선택
- 기본값 `fact_check`
- Trust Score 공식에는 직접 영향 없음
- Final Answer 표현 방식에 사용

---

## 5. F-03 질문 개선

API:

```http
POST /api/refine-prompt
```

기능:

- 모호한 표현 보완
- 비교 기준과 현재 시점 보완
- 질문 유형 분류
- Verification Basis 분류
- 검색 키워드 생성
- 질문 개선 Modal 표시

사용자 선택:

```text
개선된 질문 사용
직접 수정
원본 질문 사용
```

질문 개선 실패 시 원본 질문으로 분석할 수 있어야 한다.

---

## 6. F-04 분석 작업 생성

API:

```http
POST /api/analyze
```

기능:

- 새 `question_id` 생성
- 질문과 답변 목적 저장
- 상태 `queued`
- 분석 파이프라인 실행
- Loading Page 이동

실패 시 Loading Page로 이동하지 않는다.

---

## 7. F-05 분석 진행 상태

API:

```http
GET /api/progress/{question_id}
```

화면용 7단계:

```text
1. 질문 분석
2. AI 답변 생성
3. Claim 추출
4. 외부 근거 검색
5. Hybrid Search
6. Claim 검증
7. 최종 답변 생성
```

표시 데이터:

- 전체 진행률
- 현재 단계
- GPT·Claude·Gemini 상태
- 단계별 처리 시간
- Claim 수
- 검색 문서 수
- Evidence 수
- 실패 단계와 이유

Polling은 완료·실패·Unmount 시 중단한다.

---

## 8. F-06 다중 AI 답변 생성

필수 Provider:

```text
gpt
claude
gemini
```

규칙:

- 동일 질문에 독립 응답
- 서로의 답변을 보지 않음
- 가능한 경우 병렬 호출
- 모델명, 상태, 응답 시간, Token, 비용 저장
- Provider 실패를 숨기지 않음

---

## 9. F-07 Claim Extraction

기능:

- Atomic Claim 추출
- `core`와 `supporting` 구분
- Claim Type 지정
- Verification Basis 지정
- 모델별 Claim 출처 저장
- 중복 제거

규칙:

- 하나의 Claim에 하나의 주장
- 원문보다 강한 주장으로 변경 금지
- 부가 설명은 Supporting Claim으로 분리

---

## 10. F-08 Claim Consolidation

기능:

- 표현이 다른 동일 의미 Claim 통합
- `source_models` 저장
- 화면용 `C1`, `C2` 생성
- 직접적인 반대 Claim은 별도 유지

중요:

```text
미언급 ≠ 반대
추가 설명 ≠ 모순
표현 차이 ≠ 불일치
```

---

## 11. F-09 Verification Basis 분류

지원 값:

```text
deterministic
authoritative_fact
web_evidence
mixed
subjective
```

예시:

- `25 × 4` → deterministic
- `산소의 원소기호` → authoritative_fact
- `현재 환율` → web_evidence
- `RAG와 Fine-tuning 비교` → mixed
- `가장 좋은 언어` → subjective

---

## 12. F-10 Deterministic Verification

대상:

- 사칙연산
- 백분율
- 단위 변환
- 진법 변환
- 논리 연산
- 명시된 공식
- 제한된 안전 코드 실행
- 규칙 기반 판정

규칙:

- 가능한 경우 LLM이 아닌 Backend 함수로 검증
- 검증 성공 시 `verified`
- AI 결과와 다르면 `contradicted`
- 성공 시 Evidence Support 100 가능
- 웹 문서가 없다는 이유로 감점하지 않음

---

## 13. F-11 외부 검색

도구:

```text
Tavily
```

기능:

- Claim별 Keyword·Semantic Query 생성
- 공식·정부·학술·문서 우선
- 제목, URL, Domain, 본문, 게시일 저장
- 중복 URL 제거
- 최신성 필요 여부 반영

Tavily 결과를 그대로 최종 답변에 사용하지 않는다.

---

## 14. F-12 문서 처리와 Embedding

기능:

- 본문 정리
- Chunking
- Chunk Hash
- Token 수
- OpenAI `text-embedding-3-small`
- 1536차원 Vector 저장

Mock Vector와 실제 Embedding을 구분한다.

---

## 15. F-13 Hybrid Search

```text
Hybrid Score =
0.6 × Keyword Score
+ 0.4 × Vector Score
```

기능:

- PostgreSQL FTS
- pgvector Cosine Search
- 점수 정규화
- 중복 URL과 유사 Chunk 제거
- Claim별 Top 3~5 Evidence 선정

Frontend는 Hybrid Score를 다시 계산하지 않는다.

---

## 16. F-14 Evidence Pack

포함 항목:

- Evidence ID
- Claim ID
- 제목과 URL
- Domain과 Snippet
- Source Type
- 게시일과 검색일
- Relation
- Keyword·Vector·Hybrid Score
- Source Quality
- Directness
- Support Score

공식 출처 하나가 안정적인 사실을 직접 검증하면 저품질 문서를 억지로 추가하지 않는다.

---

## 17. F-15 Claim Verification

상태:

```text
verified
weak_evidence
unsupported
contradicted
```

반환 데이터:

- Verification Basis
- Confidence
- 검증 이유
- Evidence ID
- Direct Evidence Strength
- Cross Source Agreement
- Positive Factors
- Deductions
- Limitations

검색 실패는 `contradicted`가 아니다.

---

## 18. F-16 Cross Review

단일 Judge가 다음을 분석한다.

- Semantic Consensus
- Contradictions
- Model Additions
- Missing Points
- Overclaims
- Logic Issues
- 모델별 강점과 약점

규칙:

- 답변 길이 차이 감점 금지
- 추가 설명을 모순으로 처리 금지
- 단순 미언급을 반대로 처리 금지
- 동시에 참일 수 없는 Core Claim만 Contradiction
- Missing Point는 기본적으로 Logic Error가 아님

---

## 19. F-17 Risk Analysis

Risk Type:

```text
hallucination
source_credibility
outdated_information
contradiction
```

Risk Level:

```text
low
medium
high
```

기능:

- Core 영향 여부
- Evidence로 해결됐는지 여부
- 실제 Penalty
- 중복 Risk 제거
- 같은 모순 중복 감점 방지

---

## 20. F-18 Trust Score

```text
Base Score =
0.40 × Evidence Support
+ 0.20 × Source Quality
+ 0.15 × Consensus
+ 0.15 × Logic
+ 0.10 × Freshness

Final Score =
Base Score
- Contradiction Penalty
- Risk Penalty
```

핵심 규칙:

- Core Claim Weight 1.0
- Supporting Claim Weight 0.25
- Consensus에서 Supporting 영향은 더 낮게 적용
- Logic은 100에서 실제 오류만 차감
- 추가 설명 차이는 Logic 0점 감점
- Deterministic Check 성공 시 Evidence Support·Source Quality·Freshness 100 가능
- 점수별 이유와 감점 원인 반환

---

## 21. F-19 모델별 신뢰도

각 모델이 생성한 Claim을 기준으로 계산한다.

반영:

- Core Claim 검증 상태
- Contradicted Claim
- Unsupported Core Claim 단정
- Logic Issue
- Overclaim
- Risk

반영하지 않음:

- 답변 길이
- 추가 설명의 양
- 다른 모델보다 설명이 적음

---

## 22. F-20 Final Answer

규칙:

- Verified Core Claim 중심
- Weak Claim은 불확실성 표시 후 제한적으로 사용
- Unsupported Claim 제외
- Contradicted Claim 제외
- 입력에 없는 사실 추가 금지
- 실제 Evidence만 Citation으로 사용
- Deterministic 질문은 Citation이 비어 있을 수 있음
- Reflection 최대 1회

---

## 23. F-21 Result Summary

표시:

- 질문 정보
- Trust Score Gauge
- 구성 점수
- 최종 검증 답변
- 주요 쟁점
- 검증 결과 요약
- 주의사항
- 출처 요약
- GPT·Claude·Gemini 모델별 신뢰도

---

## 24. F-22 상세 결과 Tab

```text
AI 답변 비교
주장 검증
근거
위험 분석
신뢰성 그래프
```

### AI 답변 비교

- AI 원본 답변 3열
- 합의·상충·누락·과도한 주장

### 주장 검증

- Claim Filter
- `C1`, `C2`
- AI 합의도
- 상태
- 근거 수
- 위험도

### 근거

- Evidence Card
- Domain, 제목, Snippet
- 관련도
- 출처 링크

### 위험 분석

- Claim 상태 요약
- Risk Accordion
- Level, 영향 Claim, Penalty

### 신뢰성 그래프

- 구성 점수 Bar
- Claim 상태 분포
- Claim ↔ Evidence 관계
- Cross Review 요약

---

## 25. F-23 History

필터:

- 질문·키워드 검색
- 점수 범위
- Provider
- 최신순·오래된순·점수순

History Card:

- 질문
- Provider
- Summary
- Tag
- Trust Score와 등급
- 날짜
- 결과 보기

별도 History 테이블은 만들지 않는다.

---

## 26. F-24 재분석

API:

```http
POST /api/reanalyze/{question_id}
```

- 새 `question_id` 생성
- 기존 결과 유지
- 답변 목적 변경 가능
- 새 Loading Page로 이동

---

## 27. Mock Mode

### Frontend Mock

```env
NEXT_PUBLIC_USE_MOCK=true
```

### Backend Mock

```env
NEXT_PUBLIC_USE_MOCK=false
USE_MOCK=true
```

### Real

```env
NEXT_PUBLIC_USE_MOCK=false
USE_MOCK=false
```

Mock 데이터도 실제 API와 동일한 구조를 사용한다.

---

## 28. 보안과 오류 처리

- API Key는 Backend 환경 변수에만 저장
- Stack Trace와 비밀값을 사용자에게 노출하지 않음
- LLM JSON을 Pydantic으로 검증
- 검색 문서 내부 명령 무시
- Provider 실패를 성공으로 위장하지 않음
- 존재하지 않는 Citation 생성 금지

---

## 29. MVP 완료 기준

```text
[ ] UI 이미지 10장 기준 화면 구현
[ ] 질문 개선 Modal 동작
[ ] Loading Polling 동작
[ ] Result Tab 6개 동작
[ ] History 필터 동작
[ ] Multi-AI 호출
[ ] Claim 추출·통합
[ ] Deterministic Check
[ ] Tavily·Embedding·Hybrid Search
[ ] Claim Verification
[ ] Cross Review
[ ] Risk Analysis
[ ] Trust Score와 이유
[ ] 결과 저장과 재조회
[ ] Mock E2E
[ ] Real E2E
[ ] Frontend Build
[ ] Backend Test
```
