# TrustLens PRD

## 1. 제품 개요

TrustLens는 GPT, Claude, Gemini가 생성한 답변을 Claim 단위로 분해하고, 계산·공식 검증 또는 외부 Evidence 검색을 통해 신뢰성을 평가하는 웹 서비스다.

한 줄 정의:

```text
여러 AI의 답변을 비교하고 근거를 검증해 Trust Score와 최종 검증 답변을 제공하는 플랫폼
```

---

## 2. 문제 정의

사용자는 생성형 AI 답변을 그대로 믿기 어렵다.

주요 문제:

- AI가 사실과 다른 내용을 자연스럽게 생성할 수 있음
- 답변의 근거와 출처가 불분명할 수 있음
- 최신 정보와 오래된 정보가 섞일 수 있음
- 모델마다 답변이 다를 수 있음
- 추가 설명의 양이 다르다는 이유만으로 실제 모순처럼 보일 수 있음
- 사용자가 직접 여러 AI와 웹 검색을 비교해야 함

---

## 3. 해결 방식

```text
사용자 질문
→ 질문 개선
→ GPT / Claude / Gemini 독립 답변
→ Core / Supporting Claim 추출
→ Claim 통합
→ Verification Basis 분류
→ Deterministic Check 또는 Web Search
→ Hybrid Retrieval
→ Claim Verification
→ Cross Review
→ Risk Analysis
→ Trust Score
→ Final Answer
```

사용자는 다음 정보를 확인한다.

- AI별 원본 답변
- Claim별 검증 상태
- 실제 Evidence
- 의미 기반 AI 합의도
- 직접적인 모순
- 추가 설명과 누락 사항
- 위험 요소
- Trust Score와 산정 이유
- 최종 검증 답변

---

## 4. 대상 사용자

- AI 답변의 사실 여부를 확인하고 싶은 일반 사용자
- 근거가 필요한 학생과 개발자
- 여러 AI 답변을 반복 비교하는 사용자
- 최신 정보와 공식 출처를 빠르게 확인하고 싶은 사용자

---

## 5. 답변 목적

UI에서 다음 중 하나를 선택한다.

| API 값 | 화면 표시 |
|---|---|
| `fact_check` | 사실 확인 |
| `concept_understanding` | 개념 이해 |
| `decision_support` | 의사 결정 |
| `evidence_focused` | 근거 중심 |
| `risk_analysis` | 위험 요소 분석 |

답변 목적은 최종 답변의 표현 방식을 조정하지만 Trust Score 공식을 직접 변경하지 않는다.

---

## 6. 핵심 사용자 흐름

```text
1. 질문 입력
2. 답변 목적 선택
3. 질문 개선 Modal 확인
4. 원본·개선·직접 수정 질문 중 선택
5. 분석 시작
6. Loading 화면에서 진행 상태 확인
7. 종합 요약 확인
8. AI 답변·Claim·Evidence·Risk·그래프 확인
9. 검증 기록에서 이전 결과 조회
10. 필요 시 재분석
```

---

## 7. MVP 필수 기능

### 질문 처리

- 자유 텍스트 입력
- 최대 2000자 Validation
- 질문 개선
- 질문 유형 분류
- Verification Basis 분류
- 답변 목적 선택

### 다중 AI

- GPT 답변
- Claude 답변
- Gemini 답변
- 독립 호출
- Provider별 상태·모델명·응답 시간 저장

### Claim 처리

- Atomic Claim 추출
- Core / Supporting 구분
- 의미 기반 Claim 통합
- 화면용 `C1`, `C2` ID
- Claim별 의미 합의도

### 검증

- 계산·진법·논리·공식 기반 Deterministic Check
- Tavily 검색
- 검색 문서 저장 및 Chunking
- OpenAI Embedding
- PostgreSQL FTS
- pgvector 검색
- Hybrid Ranking
- Claim Verification

### 교차 검토

- Consensus
- Contradictions
- Model Additions
- Missing Points
- Overclaims
- Logic Issues

### 결과

- Trust Score
- 구성 점수와 산정 이유
- 모델별 신뢰도
- 최종 검증 답변
- Citation
- 결과 저장
- History
- 재분석

---

## 8. Trust Score 목표

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

제품 원칙:

- 추가 설명 차이는 Logic 또는 Consensus 감점이 아님
- 단순 미언급은 모순이 아님
- Core Claim을 Supporting Claim보다 크게 반영
- 계산 가능한 정답은 독립 검증 성공 시 100점 가능
- 안정적인 사실은 공식 출처 하나로도 높은 점수 가능
- 최신·논쟁적 정보는 출처 충돌과 불확실성을 반영
- 점수만 보여주지 않고 구체적인 이유를 제공

---

## 9. 페이지

```text
/                                 질문 입력
/analyze?question_id={uuid}       분석 진행
/result?question_id={uuid}        검증 결과
/history                          검증 기록
```

Result Tab:

```text
summary
ai-responses
claims
evidence
risks
graph
```

---

## 10. UI 기준

Frontend는 `assets/UI`의 10개 이미지를 기준으로 구현한다.

```text
01-home.png
02-prompt_refinement.png
03-loading.png
04-result_summary.png
05-1-detail_analysis.png
05-2-detail_analysis.png
05-3-detail_analysis.png
05-4-detail_analysis.png
05-5-detail_analysis.png
06-history.png
```

- 시각적 구조는 이미지 우선
- API 데이터는 문서 우선
- 이미지의 예시 데이터는 하드코딩하지 않음

---

## 11. 성공 기준

```text
[ ] 질문 입력부터 결과 화면까지 Mock E2E 성공
[ ] GPT, Claude, Gemini 실제 호출 성공
[ ] Claim 추출과 통합 성공
[ ] Deterministic Check 성공
[ ] Tavily 검색과 DB 저장 성공
[ ] FTS와 pgvector Hybrid Search 성공
[ ] Claim Verification 성공
[ ] Cross Review에서 추가 설명과 모순 구분
[ ] Trust Score 공식 테스트 통과
[ ] 점수 산정 이유 표시
[ ] History와 재분석 동작
[ ] UI 이미지와 주요 레이아웃 일치
[ ] Frontend Build와 Backend Test 성공
```

---

## 12. MVP 제외 범위

- 회원가입과 로그인
- 결제와 실제 Pro 요금제
- 관리자 화면
- 즐겨찾기 API
- 리포트 다운로드 API
- Multi-round Debate
- 모바일 네이티브 앱
- 자체 LLM 학습과 Fine-tuning
- 완전한 실시간 Streaming
- 대규모 분산 Queue

이미지에 존재하지만 구현하지 않는 메뉴는 `준비 중인 기능입니다`로 처리한다.

---

## 13. 주요 위험과 대응

### 외부 API 실패

- Timeout
- 제한된 재시도
- Provider별 실패 기록
- 명시적 Fallback

### 점수 왜곡

- Core / Supporting 가중치 분리
- 의미 기반 Consensus
- 실제 Logic Issue만 감점
- 문서 개수가 아닌 검증 품질 평가
- 중복 Risk 제거

### LLM JSON 오류

- Pydantic Validation
- JSON Repair 최대 1회
- 재실패 시 Fallback

### 개발 시간 부족

- Mock E2E 우선
- 실제 Provider를 하나씩 연결
- 복잡한 그래프보다 핵심 데이터 표시 우선

---

## 14. 완료 정의

```text
코드 작성
+ 실행 성공
+ 오류 처리 확인
+ API 또는 UI 확인
+ 필요한 테스트 통과
```

실제 진행 상태는 `docs/PROGRESS.md`에 기록한다.
