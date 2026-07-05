# TrustLens Team Tasks

## 1. 목적

네 명이 동시에 개발하면서 파일 충돌을 줄이고 Frontend·Backend 계약을 유지하기 위한 역할 문서다.

---

## 2. 역할

| 역할 | 담당 |
|---|---|
| Frontend A | 공통 Layout, Home, Prompt Modal, Loading |
| Frontend B | Result, History, API Client와 Types |
| Backend A | FastAPI, DB, Models, Schemas, Mock API |
| Backend B | AI, 검색, 검증, Trust Score, 전체 통합 |

Backend B 또는 지정된 팀원이 통합 담당자가 된다.

---

## 3. 공통 규칙

- 작업 전 Pull
- `CLAUDE.md`와 담당 문서 확인
- 담당 폴더 중심으로 수정
- API 필드와 Enum 임의 변경 금지
- `.env` Commit 금지
- 작업 후 직접 실행
- 테스트하지 않은 기능을 완료로 보고 금지
- 사용자 요청 없이 Claude Code Commit·Push 금지
- 공용 문서 수정은 통합 담당자만 수행

---

## 4. Frontend A

### UI 이미지

```text
assets/UI/01-home.png
assets/UI/02-prompt_refinement.png
assets/UI/03-loading.png
```

### 담당

```text
frontend/app/layout.tsx
frontend/app/page.tsx
frontend/app/analyze/
frontend/components/layout/
frontend/components/home/
frontend/components/analysis/
frontend/hooks/useAnalysisPolling.ts
```

### 기능

- Sidebar
- Top Header
- Page Shell
- Home 질문 입력
- 답변 목적 선택
- 최근 질문
- Prompt Refinement Modal
- Analyze Page
- 7단계 진행 UI
- 모델 상태 Card
- Polling

### API

```text
POST /api/refine-prompt
POST /api/analyze
GET /api/progress/{question_id}
POST /api/reanalyze/{question_id}
```

### 완료 기준

```text
[ ] 01~03 이미지와 주요 배치 일치
[ ] 질문 Validation
[ ] Modal 동작
[ ] 분석 ID URL 전달
[ ] Polling 종료 처리
[ ] npm run build 성공
```

---

## 5. Frontend B

### UI 이미지

```text
assets/UI/04-result_summary.png
assets/UI/05-1-detail_analysis.png
assets/UI/05-2-detail_analysis.png
assets/UI/05-3-detail_analysis.png
assets/UI/05-4-detail_analysis.png
assets/UI/05-5-detail_analysis.png
assets/UI/06-history.png
```

### 담당

```text
frontend/app/result/
frontend/app/history/
frontend/components/result/
frontend/components/history/
frontend/lib/api.ts
frontend/lib/types.ts
frontend/lib/constants.ts
frontend/lib/formatters.ts
frontend/data/mockData.ts
```

### 기능

- Result Header와 Tab
- Trust Score Summary
- 모델별 신뢰도
- AI 답변 비교
- Claim Table
- Evidence Card
- Risk Accordion
- 신뢰성 그래프
- History Filter와 Card
- API Client와 Types
- Mock Data

### API

```text
GET /api/result/{question_id}
GET /api/result/{question_id}/detail
GET /api/history
POST /api/reanalyze/{question_id}
```

### 완료 기준

```text
[ ] 04~06 이미지와 주요 배치 일치
[ ] Result Tab 6개
[ ] C1·C2 Claim 표시
[ ] 점수 이유 표시 가능
[ ] History 필터
[ ] Mock·API Data 렌더링
[ ] npm run build 성공
```

---

## 6. Backend A

### 담당

```text
backend/app/main.py
backend/app/core/
backend/app/db/
backend/app/models/
backend/app/schemas/
backend/app/routers/
backend/app/services/mock_service.py
backend/app/services/result_service.py
backend/app/services/history_service.py
backend/alembic/
backend/tests/
```

### 기능

- FastAPI App
- CORS
- 환경 변수
- Health API
- PostgreSQL·pgvector
- 11개 테이블 Model
- Pydantic Schema
- Mock API
- 결과·History 조회
- Alembic

### Endpoint

```text
GET /api/v1/health
POST /api/refine-prompt
POST /api/analyze
GET /api/progress/{question_id}
GET /api/result/{question_id}
GET /api/result/{question_id}/detail
GET /api/history
POST /api/reanalyze/{question_id}
```

### 완료 기준

```text
[ ] FastAPI 실행
[ ] Swagger 접속
[ ] PostgreSQL 연결
[ ] pgvector 활성화
[ ] 11개 Model
[ ] Migration 적용
[ ] Mock API 정상
[ ] 404·409·422 처리
[ ] compileall·pytest 성공
```

---

## 7. Backend B 및 통합

### 담당

```text
backend/app/services/provider_service.py
backend/app/services/prompt_service.py
backend/app/services/claim_service.py
backend/app/services/deterministic_service.py
backend/app/services/search_service.py
backend/app/services/chunk_service.py
backend/app/services/embedding_service.py
backend/app/services/hybrid_search.py
backend/app/services/verification_service.py
backend/app/services/judge_service.py
backend/app/services/risk_service.py
backend/app/services/trust_score_service.py
backend/app/services/final_answer_service.py
backend/app/services/pipeline.py
backend/app/agents/
backend/app/utils/
```

### 기능

- GPT·Claude·Gemini
- Claim Extraction과 Consolidation
- Verification Basis
- Deterministic Check
- Tavily
- Chunking·Embedding
- FTS·pgvector
- Hybrid Ranking
- Evidence Pack
- Claim Verification
- Cross Review
- Risk Analysis
- 모델별 점수
- Trust Score
- Final Answer와 Reflection
- 전체 Pipeline

### 필수 점수 규칙

- 추가 설명 감점 금지
- 미언급을 모순 처리 금지
- Core Claim 우선
- 계산 검증 성공 시 100점 가능
- 공식 출처 하나로 안정적 사실 고득점 가능
- 점수 이유 반환
- Risk·모순 중복 감점 금지

### 통합 업무

- Frontend·Backend 필드 확인
- Mock E2E
- Real E2E
- 공용 문서 업데이트
- 충돌 해결
- 배포
- 발표 테스트

### 완료 기준

```text
[ ] Provider 3개 실제 호출
[ ] Claim Extraction·Consolidation
[ ] Deterministic Check
[ ] Tavily와 문서 저장
[ ] Embedding 1536 저장
[ ] FTS·pgvector 검색
[ ] Claim Verification
[ ] Cross Review
[ ] Risk
[ ] Trust Score 테스트
[ ] Final Answer
[ ] Real E2E
```

---

## 8. 공용 파일 담당

| 파일 | 우선 담당 |
|---|---|
| `frontend/app/layout.tsx` | Frontend A |
| `frontend/lib/types.ts` | Frontend B |
| `frontend/lib/api.ts` | Frontend B |
| `backend/app/main.py` | Backend A |
| `backend/app/models/` | Backend A |
| `backend/app/schemas/` | Backend A |
| `backend/app/services/` | Backend B |
| `docs/` | 통합 담당자 |

같은 파일을 동시에 수정하지 않는다.

---

## 9. 작업 순서

### 1단계

```text
Frontend Skeleton
FastAPI Skeleton
PostgreSQL
Types와 Mock Data
```

### 2단계

```text
Backend Mock API
Frontend ↔ Backend Mock E2E
```

### 3단계

```text
GPT
Claude
Gemini
Tavily
Embedding
```

### 4단계

```text
Claim
Deterministic Check
Hybrid Search
Verification
```

### 5단계

```text
Cross Review
Risk
Trust Score
Final Answer
```

### 6단계

```text
History
Real E2E
배포
발표 테스트
```

---

## 10. 작업 전달 형식

```text
담당 역할:
구현한 기능:
생성한 파일:
수정한 파일:
실행한 명령:
테스트 결과:
남은 오류:
다른 팀원이 알아야 할 사항:
권장 Commit 메시지:
```

---

## 11. Git 규칙

작업 전:

```bash
git status
git pull
```

Commit 전:

```bash
git status
```

확인:

- 담당 파일만 포함
- `.env` 제외
- Build 또는 Test 실행

금지:

```text
git push --force
다른 팀원 작업 덮어쓰기
API Key Commit
테스트하지 않은 대규모 변경 Push
```

---

## 12. 발표 테스트 질문

### 계산

```text
25 × 4는?
```

### 안정적 사실

```text
산소와 철의 원소기호는 무엇인가?
```

### 기술 비교

```text
RAG와 Fine-tuning 중 어떤 방식이 더 적합한가?
```

### 최신 정보

발표 당일 공식 출처로 검증 가능한 질문을 사용한다.

---

## 13. 최종 체크

```text
[ ] UI 10장 구현
[ ] Mock E2E
[ ] Real E2E
[ ] Frontend Build
[ ] Backend Test
[ ] DB 저장
[ ] Provider 3개
[ ] Deterministic Check
[ ] Hybrid Search
[ ] Claim Verification
[ ] Cross Review
[ ] Trust Score
[ ] History
[ ] 배포
```
