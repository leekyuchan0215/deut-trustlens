# TrustLens Project Setup

## 1. 목적

이 문서는 TrustLens의 개발 환경, 프로젝트 구조, 실행 방법과 Mock·Real Mode 설정을 정의한다.

---

## 2. 필수 도구

```text
Node.js 20+
npm
Python 3.11+
PostgreSQL 16
Docker Desktop
Git
VS Code
```

선택:

```text
GitHub Desktop
Postman
pgAdmin
```

---

## 3. 최종 프로젝트 구조

```text
TrustLens/
├── CLAUDE.md
├── README.md
├── .gitignore
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

Frontend 작업 전 `assets/UI` 이미지를 반드시 확인한다.

---

## 4. Frontend 생성

프로젝트 루트에서:

```bash
npx create-next-app@latest frontend
```

권장 선택:

```text
TypeScript: Yes
ESLint: Yes
Tailwind CSS: Yes
src directory: 선택 가능
App Router: Yes
Turbopack: 선택 가능
Import alias: @/*
```

실행:

```bash
cd frontend
npm install
npm run dev
```

기본 주소:

```text
http://localhost:3000
```

Build:

```bash
npm run build
```

---

## 5. Frontend 환경 변수

`frontend/.env.local.example`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_USE_MOCK=true
```

Frontend Mock:

```env
NEXT_PUBLIC_USE_MOCK=true
```

Backend API 사용:

```env
NEXT_PUBLIC_USE_MOCK=false
```

비밀 API Key를 `NEXT_PUBLIC_` 변수에 넣지 않는다.

---

## 6. Backend 생성

```bash
mkdir backend
cd backend
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Windows CMD:

```cmd
.venv\Scripts\activate.bat
```

Linux·WSL·macOS:

```bash
source .venv/bin/activate
```

권장 패키지:

```bash
pip install fastapi uvicorn[standard] sqlalchemy psycopg[binary] alembic pydantic-settings pgvector httpx openai anthropic google-generativeai tavily-python pytest pytest-asyncio
```

의존성 저장:

```bash
pip freeze > requirements.txt
```

실행:

```bash
python -m uvicorn app.main:app --reload
```

기본 주소:

```text
http://localhost:8000
http://localhost:8000/docs
```

---

## 7. Backend 권장 구조

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   └── errors.py
│   ├── db/
│   │   ├── base.py
│   │   ├── session.py
│   │   └── init_db.py
│   ├── models/
│   ├── schemas/
│   ├── routers/
│   ├── services/
│   ├── agents/
│   └── utils/
├── scripts/
├── tests/
├── alembic/
├── alembic.ini
├── requirements.txt
└── .env.example
```

---

## 8. Backend 환경 변수

`backend/.env.example`:

```env
APP_ENV=development
USE_MOCK=true

DATABASE_URL=postgresql+psycopg://trustlens:trustlens@localhost:5432/trustlens

OPENAI_API_KEY=
OPENAI_CHAT_MODEL=
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

ANTHROPIC_API_KEY=
CLAUDE_MODEL=

OPENROUTER_API_KEY=
OPENROUTER_CLAUDE_MODEL=

GEMINI_API_KEY=
GEMINI_MODEL=

TAVILY_API_KEY=

JUDGE_PROVIDER=
JUDGE_MODEL=

FRONTEND_ORIGIN=http://localhost:3000
```

Claude는 Anthropic 또는 OpenRouter 중 프로젝트 설정에 맞는 Provider를 선택한다.

실제 `.env`는 Commit하지 않는다.

---

## 9. PostgreSQL과 pgvector

### Docker Compose 예시

`docker-compose.yml`:

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: trustlens-postgres
    environment:
      POSTGRES_DB: trustlens
      POSTGRES_USER: trustlens
      POSTGRES_PASSWORD: trustlens
    ports:
      - "5432:5432"
    volumes:
      - trustlens-postgres-data:/var/lib/postgresql/data

volumes:
  trustlens-postgres-data:
```

실행:

```bash
docker compose up -d
```

확인:

```bash
docker compose ps
```

Extension:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

---

## 10. Alembic

초기화:

```bash
cd backend
alembic init alembic
```

Migration 생성:

```bash
alembic revision --autogenerate -m "create trustlens tables"
```

적용:

```bash
alembic upgrade head
```

DB Schema는 `docs/DB_SCHEMA.md`를 기준으로 한다.

---

## 11. 실행 모드

### Frontend 단독 Mock

```env
NEXT_PUBLIC_USE_MOCK=true
```

```text
Frontend
→ frontend/data/mockData.ts
```

### Backend Mock E2E

Frontend:

```env
NEXT_PUBLIC_USE_MOCK=false
```

Backend:

```env
USE_MOCK=true
```

```text
Frontend
→ FastAPI
→ Backend Mock Service
→ PostgreSQL
→ Result
```

### Real Mode

Frontend:

```env
NEXT_PUBLIC_USE_MOCK=false
```

Backend:

```env
USE_MOCK=false
```

```text
Frontend
→ FastAPI
→ GPT / Claude / Gemini
→ Deterministic Check
→ Tavily
→ Embedding
→ Hybrid Search
→ Judge
→ Trust Score
→ PostgreSQL
```

Mock 실패를 실제 결과로 위장하지 않는다.

---

## 12. 권장 개발 순서

```text
1. 문서와 UI 이미지 배치
2. Frontend Skeleton
3. FastAPI Skeleton
4. PostgreSQL 연결
5. Backend Mock API
6. Frontend ↔ Backend Mock E2E
7. GPT·Claude·Gemini 개별 연결
8. Claim Extraction
9. Deterministic Check
10. Tavily 검색
11. Chunking·Embedding
12. FTS·pgvector Hybrid Search
13. Claim Verification
14. Cross Review·Risk
15. Trust Score
16. Final Answer
17. History
18. Real E2E
19. 배포
```

---

## 13. CORS

Backend는 Frontend Origin만 허용한다.

개발 예시:

```text
http://localhost:3000
```

모든 Origin을 무조건 허용하는 설정은 Production에서 사용하지 않는다.

---

## 14. 테스트

Frontend:

```bash
npm run build
```

Backend Syntax:

```bash
python -m compileall app
```

Backend Test:

```bash
pytest
```

Health:

```text
GET http://localhost:8000/api/v1/health
```

필수 테스트:

- 질문 Validation
- Progress Polling 종료
- API Schema
- Trust Score 계산
- Deterministic Check
- 추가 설명과 모순 구분
- Provider Timeout
- DB 저장

---

## 15. Git Ignore

권장:

```gitignore
# Frontend
frontend/node_modules/
frontend/.next/
frontend/.env.local

# Backend
backend/.venv/
backend/__pycache__/
backend/.pytest_cache/
backend/.env
*.pyc

# General
.env
.DS_Store
Thumbs.db
```

UI 이미지는 프로젝트에 포함해야 하므로 `assets/UI`를 Ignore하지 않는다.

---

## 16. 배포

### Frontend

- Vercel
- `NEXT_PUBLIC_API_BASE_URL`을 배포 Backend 주소로 설정

### Backend

필수:

- Python 3.11+
- PostgreSQL 접근
- 환경 변수
- CORS 배포 Origin

### Database

- PostgreSQL 16
- pgvector Extension
- Migration 실행

---

## 17. 완료 기준

```text
[ ] UI 이미지 10장 배치
[ ] Frontend dev 실행
[ ] Frontend build 성공
[ ] Backend 실행
[ ] Swagger 접속
[ ] PostgreSQL 연결
[ ] pgvector 활성화
[ ] Alembic 적용
[ ] Backend Mock E2E
[ ] Real Provider 연결
[ ] pytest 통과
[ ] .env가 Git에 포함되지 않음
```
