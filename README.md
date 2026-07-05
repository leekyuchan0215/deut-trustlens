# TrustLens

GPT, Claude, Gemini의 답변을 비교하고 외부 근거로 검증하여 Trust Score와 최종 검증 답변을 제공하는 AI 답변 신뢰성 검증 플랫폼이다.

## 핵심 흐름

```text
질문 입력
→ 질문 개선
→ 다중 AI 답변 생성
→ Claim 추출 및 통합
→ 계산·공식 검증 또는 웹 검색
→ PostgreSQL FTS + pgvector Hybrid Search
→ Claim Verification
→ Cross Review
→ Risk Analysis
→ Trust Score
→ Final Answer
```

## 주요 특징

- GPT, Claude, Gemini 독립 답변 비교
- Core Claim과 Supporting Claim 분리
- 수학·공식·논리 문제의 결정적 검증
- Tavily 기반 외부 문서 검색
- PostgreSQL Full Text Search와 pgvector 결합
- Claim별 Evidence와 검증 상태 제공
- 의미 기반 AI 합의도 분석
- 추가 설명과 실제 모순 구분
- 설명 가능한 Trust Score
- 검증 기록과 재분석

## 기술 스택

### Frontend

```text
Next.js
React
TypeScript
Tailwind CSS
```

### Backend

```text
FastAPI
Python 3.11+
SQLAlchemy
Pydantic
Alembic
```

### Database

```text
PostgreSQL 16
pgvector
PostgreSQL Full Text Search
```

### External Services

```text
OpenAI
Claude
Gemini
Tavily
OpenAI Embedding
```

## 프로젝트 구조

```text
TrustLens/
├── CLAUDE.md
├── README.md
├── assets/
│   └── UI/
│       ├── 01-home.png
│       ├── 02-prompt_refinement.png
│       ├── 03-loading.png
│       ├── 04-result_summary.png
│       ├── 05-1-detail_analysis.png
│       ├── 05-2-detail_analysis.png
│       ├── 05-3-detail_analysis.png
│       ├── 05-4-detail_analysis.png
│       ├── 05-5-detail_analysis.png
│       └── 06-history.png
├── docs/
│   ├── PRD.md
│   ├── FEATURES.md
│   ├── UI_FLOW.md
│   ├── API_SPEC.md
│   ├── DB_SCHEMA.md
│   ├── PROMPTS.md
│   ├── TRUST_SCORE.md
│   ├── PROJECT_SETUP.md
│   ├── TEAM_TASKS.md
│   └── PROGRESS.md
├── frontend/
└── backend/
```

## UI 기준

Frontend는 `assets/UI`의 10개 이미지를 실제 구현 기준으로 사용한다.

- 레이아웃과 디자인은 UI 이미지 우선
- API 경로와 필드는 `docs/API_SPEC.md` 우선
- 점수 계산은 `docs/TRUST_SCORE.md` 우선
- 이미지 속 숫자와 질문은 예시이므로 하드코딩하지 않음

## Trust Score

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

핵심 원칙:

- 추가 설명의 차이는 논리 불일치가 아님
- 단순 미언급은 반대가 아님
- 수학·계산은 독립 검증 성공 시 100점 가능
- 공식 사실은 공식 출처 하나로도 높은 점수 가능
- 검색 문서 수만으로 근거 지지도를 결정하지 않음
- 낮은 점수의 구체적인 이유를 사용자에게 제공

## Mock Mode

### Frontend 단독 Mock

```env
NEXT_PUBLIC_USE_MOCK=true
```

### Backend Mock 연동

```env
NEXT_PUBLIC_USE_MOCK=false
USE_MOCK=true
```

### Real Mode

```env
NEXT_PUBLIC_USE_MOCK=false
USE_MOCK=false
```

Mock 결과는 반드시 실제 AI 검증 결과와 구분해서 표시한다.

## 핵심 API

| Method | Endpoint | 기능 |
|---|---|---|
| GET | `/api/v1/health` | 서버 상태 |
| POST | `/api/refine-prompt` | 질문 개선 |
| POST | `/api/analyze` | 분석 생성 |
| GET | `/api/progress/{question_id}` | 진행 상태 |
| GET | `/api/result/{question_id}` | 결과 요약 |
| GET | `/api/result/{question_id}/detail` | 상세 결과 |
| GET | `/api/history` | 검증 기록 |
| POST | `/api/reanalyze/{question_id}` | 재분석 |

## 문서 읽는 순서

```text
1. CLAUDE.md
2. docs/PRD.md
3. docs/FEATURES.md
4. docs/UI_FLOW.md
5. docs/API_SPEC.md
6. docs/DB_SCHEMA.md
7. docs/PROMPTS.md
8. docs/TRUST_SCORE.md
9. docs/PROJECT_SETUP.md
10. docs/TEAM_TASKS.md
11. docs/PROGRESS.md
```

현재 구현 상태는 `docs/PROGRESS.md`에서 확인한다.
