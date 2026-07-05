# TrustLens Database Schema

## 1. 문서 목적

이 문서는 TrustLens에서 사용하는 PostgreSQL 데이터베이스 구조, 테이블 관계, 제약조건과 인덱스를 정의한다.

다음 데이터를 저장한다.

- 사용자 질문
- 질문 개선 결과
- 답변 목적
- 질문 유형과 검증 방식
- 분석 진행 상태
- GPT·Claude·Gemini 원본 답변
- 모델별 신뢰도
- Claim
- 결정적 계산·규칙 검증 결과
- 검색 문서
- 문서 Chunk
- Embedding
- Evidence
- Risk
- Trust Score와 상세 산정 이유
- Cross Review
- Final Answer
- History 조회용 데이터

---

## 2. 사용 기술

```text
PostgreSQL 16
pgvector
SQLAlchemy
Alembic
```

필수 Extension:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

- `vector`: Embedding 저장과 유사도 검색
- `pgcrypto`: `gen_random_uuid()` 사용

---

## 3. 핵심 설계 원칙

- 모든 주요 PK는 UUID를 사용한다.
- 시간은 `TIMESTAMPTZ`로 저장한다.
- 시간 기준은 UTC다.
- Embedding 차원은 `1536`이다.
- 질문 삭제 시 관련 분석 데이터도 삭제할 수 있도록 FK를 구성한다.
- API Key와 비밀번호를 DB에 저장하지 않는다.
- 로그인 기능이 없으므로 `users` 테이블을 만들지 않는다.
- 별도의 `history` 테이블을 만들지 않는다.
- History는 기존 분석 테이블을 조합해 조회한다.
- 별도의 진행 상태 테이블을 만들지 않는다.
- 진행 상태는 `questions`에 저장한다.
- Trust Score는 LLM이 아니라 Backend 계산 결과를 저장한다.
- 검색 문서 개수는 점수 자체가 아니라 UI 요약용 통계다.
- 한 모델의 추가 설명과 다른 모델의 미언급은 모순으로 저장하지 않는다.
- 수학·계산 검증은 웹 Evidence와 별도로 저장한다.
- Core Claim과 Supporting Claim을 구분한다.
- 동일 Risk가 중복 감점되지 않게 한다.
- 기존 분석을 재실행할 때 원본 결과를 덮어쓰지 않는다.

---

## 4. 전체 테이블

```text
1. questions
2. ai_responses
3. claims
4. deterministic_checks
5. search_documents
6. document_chunks
7. document_embeddings
8. evidences
9. risks
10. trust_scores
11. final_results
```

기존 10개 테이블에서 다음 테이블이 추가되었다.

```text
deterministic_checks
```

추가 이유:

- 수학 계산
- 진법 변환
- 단위 변환
- 논리 연산
- 공식 적용
- 안전한 코드 실행
- 규칙 기반 검증

결과를 웹 검색과 구분해서 저장하기 위함이다.

---

## 5. 전체 관계

```text
questions
├── ai_responses
├── claims
│   ├── deterministic_checks
│   ├── evidences
│   └── risks
├── search_documents
│   └── document_chunks
│       └── document_embeddings
├── risks
├── trust_scores
└── final_results
```

Evidence는 다음 둘 중 하나를 근거로 사용할 수 있다.

```text
Web Evidence:
search_documents
→ document_chunks
→ evidences
```

```text
Deterministic Evidence:
deterministic_checks
→ evidences
```

결정적 검증 결과를 Evidence Card로 표시하지 않는 구현에서는 `deterministic_checks`만 저장하고 `evidences` 행을 만들지 않아도 된다.

---

## 6. 공통 Enum

PostgreSQL ENUM 또는 `TEXT + CHECK` 방식 중 하나를 사용할 수 있다.

해커톤 MVP에서는 Migration 충돌을 줄이기 위해 `TEXT + CHECK` 사용을 권장한다.

### 6.1 Answer Purpose

```text
fact_check
concept_understanding
decision_support
evidence_focused
risk_analysis
```

### 6.2 Question Type

```text
calculation
simple_fact
comparison
current_information
medical
legal
recommendation
opinion
general
```

### 6.3 Verification Basis

```text
deterministic
authoritative_fact
web_evidence
mixed
subjective
```

### 6.4 Analysis Status

```text
queued
processing
completed
failed
```

### 6.5 AI Provider

```text
gpt
claude
gemini
```

### 6.6 AI Response Status

```text
pending
success
failed
timeout
```

### 6.7 Claim Type

```text
fact
numeric
calculation
definition
comparison
cause_effect
latest_info
recommendation
opinion
```

### 6.8 Claim Importance

```text
core
supporting
```

### 6.9 Verification Status

```text
pending
verified
weak_evidence
unsupported
contradicted
```

### 6.10 Evidence Relation

```text
support
contradict
neutral
```

### 6.11 Source Type

```text
deterministic_verifier
official
government
academic
paper
documentation
news
blog
community
unknown
```

### 6.12 Risk Type

```text
hallucination
source_credibility
outdated_information
contradiction
```

### 6.13 Risk Level

```text
low
medium
high
```

---

## 7. questions

### 목적

사용자 질문, 질문 개선 결과, 답변 목적과 전체 분석 진행 상태를 저장한다.

### 컬럼

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| `id` | UUID | PK | 질문 ID |
| `original_question` | TEXT | NOT NULL | 사용자가 최초 입력한 질문 |
| `refined_question` | TEXT | NULL | AI가 개선한 질문 |
| `selected_question` | TEXT | NOT NULL | 실제 분석에 사용한 질문 |
| `answer_purpose` | VARCHAR(40) | NOT NULL | 답변 목적 |
| `question_type` | VARCHAR(40) | NULL | 질문 유형 |
| `verification_basis` | VARCHAR(40) | NULL | 질문 전체의 기본 검증 방식 |
| `suggested_keywords` | JSONB | NOT NULL DEFAULT `[]` | 질문 분석 키워드 |
| `tags` | JSONB | NOT NULL DEFAULT `[]` | History 화면 Category Tag |
| `status` | VARCHAR(20) | NOT NULL | 분석 상태 |
| `current_stage` | VARCHAR(60) | NOT NULL | Backend 상세 단계 |
| `display_stage` | VARCHAR(60) | NOT NULL | Loading UI용 7단계 |
| `progress_percent` | SMALLINT | NOT NULL DEFAULT 0 | 진행률 |
| `stage_details` | JSONB | NOT NULL DEFAULT `[]` | 단계별 상태와 처리 시간 |
| `estimated_remaining_seconds` | INTEGER | NULL | 예상 남은 시간 |
| `execution_mode` | VARCHAR(20) | NOT NULL | `mock` 또는 `real` |
| `reanalysis_of_question_id` | UUID | FK, NULL | 재분석 이전 질문 |
| `error_code` | VARCHAR(100) | NULL | 실패 코드 |
| `error_message` | TEXT | NULL | 사용자용 실패 설명 |
| `started_at` | TIMESTAMPTZ | NULL | 분석 시작 |
| `completed_at` | TIMESTAMPTZ | NULL | 분석 완료 |
| `created_at` | TIMESTAMPTZ | NOT NULL | 생성 시간 |
| `updated_at` | TIMESTAMPTZ | NOT NULL | 수정 시간 |

### SQL 예시

```sql
CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_question TEXT NOT NULL,
    refined_question TEXT,
    selected_question TEXT NOT NULL,
    answer_purpose VARCHAR(40) NOT NULL,
    question_type VARCHAR(40),
    verification_basis VARCHAR(40),
    suggested_keywords JSONB NOT NULL DEFAULT '[]'::jsonb,
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    status VARCHAR(20) NOT NULL DEFAULT 'queued',
    current_stage VARCHAR(60) NOT NULL DEFAULT 'question_analysis',
    display_stage VARCHAR(60) NOT NULL DEFAULT 'question_analysis',
    progress_percent SMALLINT NOT NULL DEFAULT 0,
    stage_details JSONB NOT NULL DEFAULT '[]'::jsonb,
    estimated_remaining_seconds INTEGER,
    execution_mode VARCHAR(20) NOT NULL DEFAULT 'mock',
    reanalysis_of_question_id UUID REFERENCES questions(id) ON DELETE SET NULL,
    error_code VARCHAR(100),
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_questions_answer_purpose CHECK (
        answer_purpose IN (
            'fact_check',
            'concept_understanding',
            'decision_support',
            'evidence_focused',
            'risk_analysis'
        )
    ),
    CONSTRAINT ck_questions_status CHECK (
        status IN ('queued', 'processing', 'completed', 'failed')
    ),
    CONSTRAINT ck_questions_progress CHECK (
        progress_percent BETWEEN 0 AND 100
    ),
    CONSTRAINT ck_questions_execution_mode CHECK (
        execution_mode IN ('mock', 'real')
    )
);
```

---

## 8. ai_responses

### 목적

GPT, Claude, Gemini가 생성한 원본 답변과 각 모델의 처리 상태 및 모델별 신뢰도 점수를 저장한다.

모델별 점수는 답변 길이나 추가 설명의 양으로 계산하지 않는다.

### 컬럼

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| `id` | UUID | PK | 응답 ID |
| `question_id` | UUID | FK | 질문 ID |
| `provider` | VARCHAR(20) | NOT NULL | GPT·Claude·Gemini |
| `model_name` | VARCHAR(150) | NOT NULL | 실제 모델명 |
| `status` | VARCHAR(20) | NOT NULL | 호출 상태 |
| `response_text` | TEXT | NULL | 원본 답변 |
| `latency_ms` | INTEGER | NULL | 응답 시간 |
| `input_tokens` | INTEGER | NULL | 입력 Token |
| `output_tokens` | INTEGER | NULL | 출력 Token |
| `total_tokens` | INTEGER | NULL | 전체 Token |
| `estimated_cost` | NUMERIC(12,6) | NULL | 예상 비용 |
| `model_score` | NUMERIC(5,2) | NULL | 모델별 신뢰도 |
| `model_grade` | VARCHAR(50) | NULL | 모델별 등급 |
| `model_score_reason` | TEXT | NULL | 모델 점수 이유 |
| `model_score_detail` | JSONB | NOT NULL DEFAULT `{}` | 모델 점수 상세 |
| `error_code` | VARCHAR(100) | NULL | 오류 코드 |
| `error_message` | TEXT | NULL | 오류 설명 |
| `created_at` | TIMESTAMPTZ | NOT NULL | 생성 시간 |
| `updated_at` | TIMESTAMPTZ | NOT NULL | 수정 시간 |

### SQL 예시

```sql
CREATE TABLE ai_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    provider VARCHAR(20) NOT NULL,
    model_name VARCHAR(150) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    response_text TEXT,
    latency_ms INTEGER,
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    estimated_cost NUMERIC(12, 6),
    model_score NUMERIC(5, 2),
    model_grade VARCHAR(50),
    model_score_reason TEXT,
    model_score_detail JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_code VARCHAR(100),
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_ai_responses_question_provider UNIQUE (question_id, provider),
    CONSTRAINT ck_ai_responses_provider CHECK (
        provider IN ('gpt', 'claude', 'gemini')
    ),
    CONSTRAINT ck_ai_responses_status CHECK (
        status IN ('pending', 'success', 'failed', 'timeout')
    ),
    CONSTRAINT ck_ai_responses_model_score CHECK (
        model_score IS NULL OR model_score BETWEEN 0 AND 100
    )
);
```

---

## 9. claims

### 목적

AI 답변에서 추출하고 통합한 검증 가능한 Claim과 검증 결과를 저장한다.

### 핵심 변경

- Core와 Supporting 구분
- Claim별 검증 방식 저장
- 의미 기반 AI 합의도 저장
- 추가 설명과 미언급을 모순으로 처리하지 않음
- 근거 지지도가 낮은 이유 저장
- 사용자 화면용 `C1`, `C2` ID 저장

### 컬럼

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| `id` | UUID | PK | Claim ID |
| `question_id` | UUID | FK | 질문 ID |
| `display_id` | VARCHAR(20) | NOT NULL | `C1`, `C2` |
| `claim_text` | TEXT | NOT NULL | 대표 Claim |
| `normalized_claim` | TEXT | NOT NULL | 정규화 Claim |
| `claim_type` | VARCHAR(40) | NOT NULL | Claim 유형 |
| `importance` | VARCHAR(20) | NOT NULL | Core·Supporting |
| `verification_basis` | VARCHAR(40) | NOT NULL | 검증 방식 |
| `source_models` | JSONB | NOT NULL | Claim을 언급한 모델 |
| `consensus_score` | NUMERIC(5,2) | NULL | 의미 기반 합의도 |
| `consensus_level` | VARCHAR(20) | NULL | high·medium·low |
| `verification_status` | VARCHAR(30) | NOT NULL | 검증 상태 |
| `verification_confidence` | NUMERIC(5,2) | NULL | 검증 Confidence |
| `verification_reason` | TEXT | NULL | 검증 이유 |
| `verification_mode` | VARCHAR(30) | NULL | 검증 방식 |
| `direct_evidence_strength` | NUMERIC(5,2) | NULL | 근거 직접성 |
| `cross_source_agreement` | NUMERIC(5,2) | NULL | 출처 간 일치도 |
| `positive_factors` | JSONB | NOT NULL DEFAULT `[]` | 점수를 높인 이유 |
| `deductions` | JSONB | NOT NULL DEFAULT `[]` | 점수가 낮아진 이유 |
| `limitations` | JSONB | NOT NULL DEFAULT `[]` | 검증 한계 |
| `created_at` | TIMESTAMPTZ | NOT NULL | 생성 시간 |
| `updated_at` | TIMESTAMPTZ | NOT NULL | 수정 시간 |

### SQL 예시

```sql
CREATE TABLE claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    display_id VARCHAR(20) NOT NULL,
    claim_text TEXT NOT NULL,
    normalized_claim TEXT NOT NULL,
    claim_type VARCHAR(40) NOT NULL,
    importance VARCHAR(20) NOT NULL,
    verification_basis VARCHAR(40) NOT NULL,
    source_models JSONB NOT NULL DEFAULT '[]'::jsonb,
    consensus_score NUMERIC(5, 2),
    consensus_level VARCHAR(20),
    verification_status VARCHAR(30) NOT NULL DEFAULT 'pending',
    verification_confidence NUMERIC(5, 2),
    verification_reason TEXT,
    verification_mode VARCHAR(30),
    direct_evidence_strength NUMERIC(5, 2),
    cross_source_agreement NUMERIC(5, 2),
    positive_factors JSONB NOT NULL DEFAULT '[]'::jsonb,
    deductions JSONB NOT NULL DEFAULT '[]'::jsonb,
    limitations JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_claims_question_display_id UNIQUE (question_id, display_id),
    CONSTRAINT ck_claims_importance CHECK (importance IN ('core', 'supporting')),
    CONSTRAINT ck_claims_verification_status CHECK (
        verification_status IN (
            'pending', 'verified', 'weak_evidence', 'unsupported', 'contradicted'
        )
    ),
    CONSTRAINT ck_claims_consensus_score CHECK (
        consensus_score IS NULL OR consensus_score BETWEEN 0 AND 100
    ),
    CONSTRAINT ck_claims_verification_confidence CHECK (
        verification_confidence IS NULL OR verification_confidence BETWEEN 0 AND 100
    ),
    CONSTRAINT ck_claims_direct_evidence_strength CHECK (
        direct_evidence_strength IS NULL OR direct_evidence_strength BETWEEN 0 AND 100
    ),
    CONSTRAINT ck_claims_cross_source_agreement CHECK (
        cross_source_agreement IS NULL OR cross_source_agreement BETWEEN 0 AND 100
    )
);
```

---

## 10. deterministic_checks

### 목적

웹 검색이 아닌 계산, 공식, 코드 실행 또는 규칙으로 Claim을 독립 검증한 결과를 저장한다.

### 지원 유형

```text
calculator
unit_conversion
base_conversion
logic_evaluation
formula
safe_code_execution
rule_based
```

### 컬럼

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| `id` | UUID | PK | 검증 ID |
| `question_id` | UUID | FK | 질문 ID |
| `claim_id` | UUID | FK | 대상 Claim |
| `check_type` | VARCHAR(40) | NOT NULL | 검증 유형 |
| `input_expression` | TEXT | NULL | 검증 입력 |
| `expected_result` | TEXT | NULL | 독립 검증 결과 |
| `ai_claimed_result` | TEXT | NULL | AI가 제시한 결과 |
| `check_passed` | BOOLEAN | NOT NULL | 통과 여부 |
| `verification_status` | VARCHAR(30) | NOT NULL | Claim 검증 상태 |
| `verification_confidence` | NUMERIC(5,2) | NOT NULL | Confidence |
| `verification_reason` | TEXT | NOT NULL | 판정 이유 |
| `execution_detail` | JSONB | NOT NULL DEFAULT `{}` | 공식·단위·실행 정보 |
| `limitations` | JSONB | NOT NULL DEFAULT `[]` | 한계 |
| `created_at` | TIMESTAMPTZ | NOT NULL | 생성 시간 |

### SQL 예시

```sql
CREATE TABLE deterministic_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    check_type VARCHAR(40) NOT NULL,
    input_expression TEXT,
    expected_result TEXT,
    ai_claimed_result TEXT,
    check_passed BOOLEAN NOT NULL,
    verification_status VARCHAR(30) NOT NULL,
    verification_confidence NUMERIC(5, 2) NOT NULL,
    verification_reason TEXT NOT NULL,
    execution_detail JSONB NOT NULL DEFAULT '{}'::jsonb,
    limitations JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_deterministic_checks_type CHECK (
        check_type IN (
            'calculator', 'unit_conversion', 'base_conversion',
            'logic_evaluation', 'formula', 'safe_code_execution', 'rule_based'
        )
    ),
    CONSTRAINT ck_deterministic_checks_status CHECK (
        verification_status IN (
            'verified', 'weak_evidence', 'unsupported', 'contradicted'
        )
    ),
    CONSTRAINT ck_deterministic_confidence CHECK (
        verification_confidence BETWEEN 0 AND 100
    )
);
```

---

## 11. search_documents

### 목적

Tavily 등 외부 검색으로 수집한 원본 문서를 저장한다.

검색 문서 수는 UI 통계에 사용할 수 있지만 Trust Score를 문서 개수만으로 계산하지 않는다.

### 컬럼

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| `id` | UUID | PK | 문서 ID |
| `question_id` | UUID | FK | 질문 ID |
| `title` | TEXT | NOT NULL | 문서 제목 |
| `url` | TEXT | NOT NULL | 문서 URL |
| `domain` | VARCHAR(255) | NULL | Domain |
| `content` | TEXT | NULL | 정리된 원문 |
| `summary` | TEXT | NULL | 문서 요약 |
| `source_name` | VARCHAR(255) | NULL | 출처 이름 |
| `source_type` | VARCHAR(40) | NOT NULL | 출처 유형 |
| `published_at` | TIMESTAMPTZ | NULL | 게시일 |
| `searched_at` | TIMESTAMPTZ | NOT NULL | 검색일 |
| `search_query` | TEXT | NOT NULL | 사용한 Query |
| `content_hash` | VARCHAR(64) | NULL | 중복 검사 Hash |
| `created_at` | TIMESTAMPTZ | NOT NULL | 생성 시간 |

### SQL 예시

```sql
CREATE TABLE search_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    domain VARCHAR(255),
    content TEXT,
    summary TEXT,
    source_name VARCHAR(255),
    source_type VARCHAR(40) NOT NULL DEFAULT 'unknown',
    published_at TIMESTAMPTZ,
    searched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    search_query TEXT NOT NULL,
    content_hash VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_search_documents_question_url UNIQUE (question_id, url),
    CONSTRAINT ck_search_documents_source_type CHECK (
        source_type IN (
            'official', 'government', 'academic', 'paper',
            'documentation', 'news', 'blog', 'community', 'unknown'
        )
    )
);
```

`deterministic_verifier`는 웹 문서가 아니므로 `search_documents`에는 저장하지 않는다.

---

## 12. document_chunks

### 목적

검색 문서를 Keyword Search와 Vector Search에 적합한 크기로 분할하여 저장한다.

### 컬럼

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| `id` | UUID | PK | Chunk ID |
| `document_id` | UUID | FK | 원본 문서 |
| `chunk_index` | INTEGER | NOT NULL | 문서 내 순서 |
| `content` | TEXT | NOT NULL | Chunk 본문 |
| `token_count` | INTEGER | NULL | Token 수 |
| `chunk_hash` | VARCHAR(64) | NOT NULL | 중복 검사 |
| `search_vector` | TSVECTOR | NULL | PostgreSQL FTS |
| `created_at` | TIMESTAMPTZ | NOT NULL | 생성 시간 |

### SQL 예시

```sql
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES search_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER,
    chunk_hash VARCHAR(64) NOT NULL,
    search_vector TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('simple', COALESCE(content, ''))
    ) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_document_chunks_document_index UNIQUE (document_id, chunk_index),
    CONSTRAINT uq_document_chunks_document_hash UNIQUE (document_id, chunk_hash)
);
```

---

## 13. document_embeddings

### 목적

각 Document Chunk의 Embedding Vector를 저장한다.

### 기본 설정

```text
Provider: OpenAI
Model: text-embedding-3-small
Dimension: 1536
```

### 컬럼

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| `id` | UUID | PK | Embedding ID |
| `chunk_id` | UUID | FK, UNIQUE | Chunk ID |
| `embedding_provider` | VARCHAR(50) | NOT NULL | OpenAI 또는 Mock |
| `embedding_model` | VARCHAR(150) | NOT NULL | 모델명 |
| `dimension` | INTEGER | NOT NULL | Vector 차원 |
| `embedding` | VECTOR(1536) | NOT NULL | Vector |
| `is_mock` | BOOLEAN | NOT NULL | Mock 여부 |
| `created_at` | TIMESTAMPTZ | NOT NULL | 생성 시간 |

### SQL 예시

```sql
CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id UUID NOT NULL UNIQUE REFERENCES document_chunks(id) ON DELETE CASCADE,
    embedding_provider VARCHAR(50) NOT NULL,
    embedding_model VARCHAR(150) NOT NULL,
    dimension INTEGER NOT NULL DEFAULT 1536,
    embedding VECTOR(1536) NOT NULL,
    is_mock BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_document_embeddings_dimension CHECK (dimension = 1536)
);
```

---

## 14. evidences

### 목적

Claim 검증에 실제로 선택된 Evidence를 저장한다.

```text
search_documents
→ 검색된 원본 문서 전체

evidences
→ Claim 검증에 실제 사용한 근거
```

### Evidence 원본 유형

```text
Web Evidence:
document_id: 값 존재
chunk_id: 값 존재 가능
deterministic_check_id: null
```

```text
Deterministic Evidence:
document_id: null
chunk_id: null
deterministic_check_id: 값 존재
```

### 컬럼

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| `id` | UUID | PK | Evidence ID |
| `question_id` | UUID | FK | 질문 ID |
| `claim_id` | UUID | FK | Claim ID |
| `document_id` | UUID | FK, NULL | 검색 문서 |
| `chunk_id` | UUID | FK, NULL | 문서 Chunk |
| `deterministic_check_id` | UUID | FK, NULL | 결정적 검증 |
| `title` | TEXT | NOT NULL | Evidence 제목 |
| `url` | TEXT | NULL | 원문 URL |
| `domain` | VARCHAR(255) | NULL | Domain |
| `snippet` | TEXT | NOT NULL | 검증에 사용한 내용 |
| `source_name` | VARCHAR(255) | NULL | 출처명 |
| `source_type` | VARCHAR(40) | NOT NULL | 출처 유형 |
| `published_at` | TIMESTAMPTZ | NULL | 게시일 |
| `searched_at` | TIMESTAMPTZ | NULL | 검색일 |
| `relation` | VARCHAR(20) | NOT NULL | 지지·반박·중립 |
| `keyword_score` | NUMERIC(6,5) | NULL | Keyword Score |
| `vector_score` | NUMERIC(6,5) | NULL | Vector Score |
| `hybrid_score` | NUMERIC(6,5) | NULL | Hybrid Score |
| `source_quality_score` | NUMERIC(5,2) | NOT NULL | 출처 품질 |
| `directness_score` | NUMERIC(5,2) | NOT NULL | Claim 직접성 |
| `support_score` | NUMERIC(5,2) | NOT NULL | 지지 정도 |
| `rank` | INTEGER | NOT NULL | Claim 내 순위 |
| `selection_reason` | TEXT | NULL | 선택 이유 |
| `created_at` | TIMESTAMPTZ | NOT NULL | 생성 시간 |

### Hybrid Score

```text
Hybrid Score =
0.6 × Keyword Score
+ 0.4 × Vector Score
```

### SQL 예시

```sql
CREATE TABLE evidences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    document_id UUID REFERENCES search_documents(id) ON DELETE CASCADE,
    chunk_id UUID REFERENCES document_chunks(id) ON DELETE CASCADE,
    deterministic_check_id UUID REFERENCES deterministic_checks(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    url TEXT,
    domain VARCHAR(255),
    snippet TEXT NOT NULL,
    source_name VARCHAR(255),
    source_type VARCHAR(40) NOT NULL,
    published_at TIMESTAMPTZ,
    searched_at TIMESTAMPTZ,
    relation VARCHAR(20) NOT NULL,
    keyword_score NUMERIC(6, 5),
    vector_score NUMERIC(6, 5),
    hybrid_score NUMERIC(6, 5),
    source_quality_score NUMERIC(5, 2) NOT NULL,
    directness_score NUMERIC(5, 2) NOT NULL,
    support_score NUMERIC(5, 2) NOT NULL,
    rank INTEGER NOT NULL,
    selection_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_evidences_source CHECK (
        document_id IS NOT NULL OR deterministic_check_id IS NOT NULL
    ),
    CONSTRAINT ck_evidences_relation CHECK (
        relation IN ('support', 'contradict', 'neutral')
    ),
    CONSTRAINT ck_evidences_search_scores CHECK (
        (keyword_score IS NULL OR keyword_score BETWEEN 0 AND 1)
        AND (vector_score IS NULL OR vector_score BETWEEN 0 AND 1)
        AND (hybrid_score IS NULL OR hybrid_score BETWEEN 0 AND 1)
    ),
    CONSTRAINT ck_evidences_quality_scores CHECK (
        source_quality_score BETWEEN 0 AND 100
        AND directness_score BETWEEN 0 AND 100
        AND support_score BETWEEN 0 AND 100
    )
);
```

---

## 15. risks

### 목적

Claim 또는 전체 답변에서 발견한 위험 요소와 실제 적용 Penalty를 저장한다.

같은 Claim에 같은 Risk가 여러 번 탐지되더라도 한 번만 저장하거나 가장 높은 심각도로 갱신한다.

### 컬럼

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| `id` | UUID | PK | Risk ID |
| `question_id` | UUID | FK | 질문 ID |
| `claim_id` | UUID | FK, NULL | 관련 Claim |
| `risk_key` | VARCHAR(150) | NOT NULL | 중복 방지 Key |
| `risk_type` | VARCHAR(40) | NOT NULL | 위험 유형 |
| `risk_level` | VARCHAR(20) | NOT NULL | 위험 수준 |
| `description` | TEXT | NOT NULL | 위험 설명 |
| `affects_core_answer` | BOOLEAN | NOT NULL | 핵심 답변 영향 여부 |
| `resolved_by_evidence` | BOOLEAN | NOT NULL | Evidence로 해결됐는지 |
| `penalty` | NUMERIC(5,2) | NOT NULL | 실제 적용 감점 |
| `detected_by` | VARCHAR(50) | NOT NULL | 탐지 방식 |
| `created_at` | TIMESTAMPTZ | NOT NULL | 생성 시간 |

### SQL 예시

```sql
CREATE TABLE risks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    claim_id UUID REFERENCES claims(id) ON DELETE CASCADE,
    risk_key VARCHAR(150) NOT NULL,
    risk_type VARCHAR(40) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    affects_core_answer BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_by_evidence BOOLEAN NOT NULL DEFAULT FALSE,
    penalty NUMERIC(5, 2) NOT NULL DEFAULT 0,
    detected_by VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_risks_question_key UNIQUE (question_id, risk_key),
    CONSTRAINT ck_risks_type CHECK (
        risk_type IN (
            'hallucination', 'source_credibility',
            'outdated_information', 'contradiction'
        )
    ),
    CONSTRAINT ck_risks_level CHECK (risk_level IN ('low', 'medium', 'high')),
    CONSTRAINT ck_risks_penalty CHECK (penalty BETWEEN 0 AND 40)
);
```

---

## 16. trust_scores

### 목적

Backend가 계산한 최종 Trust Score와 각 구성 점수, 산정 이유 및 계산 내역을 저장한다.

### 공식

```text
Base Score =
0.40 × Evidence Support
+ 0.20 × Source Quality
+ 0.15 × Consensus
+ 0.15 × Logic
+ 0.10 × Freshness
```

```text
Final Score =
Base Score
- Contradiction Penalty
- Risk Penalty
```

### 컬럼

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| `id` | UUID | PK | 점수 ID |
| `question_id` | UUID | FK, UNIQUE | 질문 ID |
| `evidence_support_score` | NUMERIC(5,2) | NOT NULL | 근거 지지도 |
| `source_quality_score` | NUMERIC(5,2) | NOT NULL | 출처 품질 |
| `consensus_score` | NUMERIC(5,2) | NOT NULL | AI 합의도 |
| `logic_score` | NUMERIC(5,2) | NOT NULL | 논리적 일관성 |
| `freshness_score` | NUMERIC(5,2) | NOT NULL | 최신성 |
| `base_score` | NUMERIC(5,2) | NOT NULL | 기본 점수 |
| `contradiction_penalty` | NUMERIC(5,2) | NOT NULL | 모순 감점 |
| `risk_penalty` | NUMERIC(5,2) | NOT NULL | 위험 감점 |
| `total_score` | NUMERIC(5,2) | NOT NULL | 최종 점수 |
| `grade` | VARCHAR(50) | NOT NULL | 신뢰도 등급 |
| `score_reasons` | JSONB | NOT NULL | 구성 점수별 상세 이유 |
| `strengths` | JSONB | NOT NULL DEFAULT `[]` | 점수를 높인 요인 |
| `deductions` | JSONB | NOT NULL DEFAULT `[]` | 감점 요인 |
| `calculation_detail` | JSONB | NOT NULL | 계산 상세 |
| `formula_version` | VARCHAR(20) | NOT NULL | 공식 버전 |
| `created_at` | TIMESTAMPTZ | NOT NULL | 생성 시간 |
| `updated_at` | TIMESTAMPTZ | NOT NULL | 수정 시간 |

### SQL 예시

```sql
CREATE TABLE trust_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL UNIQUE REFERENCES questions(id) ON DELETE CASCADE,
    evidence_support_score NUMERIC(5, 2) NOT NULL,
    source_quality_score NUMERIC(5, 2) NOT NULL,
    consensus_score NUMERIC(5, 2) NOT NULL,
    logic_score NUMERIC(5, 2) NOT NULL,
    freshness_score NUMERIC(5, 2) NOT NULL,
    base_score NUMERIC(5, 2) NOT NULL,
    contradiction_penalty NUMERIC(5, 2) NOT NULL DEFAULT 0,
    risk_penalty NUMERIC(5, 2) NOT NULL DEFAULT 0,
    total_score NUMERIC(5, 2) NOT NULL,
    grade VARCHAR(50) NOT NULL,
    score_reasons JSONB NOT NULL DEFAULT '{}'::jsonb,
    strengths JSONB NOT NULL DEFAULT '[]'::jsonb,
    deductions JSONB NOT NULL DEFAULT '[]'::jsonb,
    calculation_detail JSONB NOT NULL DEFAULT '{}'::jsonb,
    formula_version VARCHAR(20) NOT NULL DEFAULT '1.1',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_trust_scores_components CHECK (
        evidence_support_score BETWEEN 0 AND 100
        AND source_quality_score BETWEEN 0 AND 100
        AND consensus_score BETWEEN 0 AND 100
        AND logic_score BETWEEN 0 AND 100
        AND freshness_score BETWEEN 0 AND 100
        AND base_score BETWEEN 0 AND 100
        AND total_score BETWEEN 0 AND 100
    ),
    CONSTRAINT ck_trust_scores_penalties CHECK (
        contradiction_penalty >= 0 AND risk_penalty >= 0
    )
);
```

---

## 17. final_results

### 목적

최종 답변, Citation, Cross Review와 결과 화면용 요약 Snapshot을 저장한다.

### 컬럼

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| `id` | UUID | PK | 결과 ID |
| `question_id` | UUID | FK, UNIQUE | 질문 ID |
| `summary` | TEXT | NOT NULL | 핵심 요약 |
| `final_answer` | TEXT | NOT NULL | 최종 검증 답변 |
| `cautions` | JSONB | NOT NULL DEFAULT `[]` | 주의사항 |
| `citations` | JSONB | NOT NULL DEFAULT `[]` | Citation |
| `key_issues` | JSONB | NOT NULL DEFAULT `[]` | 주요 쟁점 |
| `cross_review` | JSONB | NOT NULL | 교차 검토 |
| `source_summary` | JSONB | NOT NULL DEFAULT `{}` | 출처 개수 요약 |
| `claim_distribution` | JSONB | NOT NULL DEFAULT `{}` | Claim 상태 분포 |
| `claim_evidence_relations` | JSONB | NOT NULL DEFAULT `[]` | 그래프용 관계 |
| `final_answer_mode` | VARCHAR(40) | NOT NULL | 최종 답변 방식 |
| `cross_review_mode` | VARCHAR(40) | NOT NULL | 교차 검토 방식 |
| `judge_provider` | VARCHAR(50) | NULL | Judge Provider |
| `judge_model` | VARCHAR(150) | NULL | Judge 모델 |
| `judge_attempts` | SMALLINT | NOT NULL | 시도 횟수 |
| `fallback_reason` | TEXT | NULL | Fallback 이유 |
| `result_version` | VARCHAR(20) | NOT NULL | 결과 구조 버전 |
| `created_at` | TIMESTAMPTZ | NOT NULL | 생성 시간 |
| `updated_at` | TIMESTAMPTZ | NOT NULL | 수정 시간 |

### SQL 예시

```sql
CREATE TABLE final_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL UNIQUE REFERENCES questions(id) ON DELETE CASCADE,
    summary TEXT NOT NULL,
    final_answer TEXT NOT NULL,
    cautions JSONB NOT NULL DEFAULT '[]'::jsonb,
    citations JSONB NOT NULL DEFAULT '[]'::jsonb,
    key_issues JSONB NOT NULL DEFAULT '[]'::jsonb,
    cross_review JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    claim_distribution JSONB NOT NULL DEFAULT '{}'::jsonb,
    claim_evidence_relations JSONB NOT NULL DEFAULT '[]'::jsonb,
    final_answer_mode VARCHAR(40) NOT NULL,
    cross_review_mode VARCHAR(40) NOT NULL,
    judge_provider VARCHAR(50),
    judge_model VARCHAR(150),
    judge_attempts SMALLINT NOT NULL DEFAULT 1,
    fallback_reason TEXT,
    result_version VARCHAR(20) NOT NULL DEFAULT '1.1',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_final_results_judge_attempts CHECK (judge_attempts >= 0)
);
```

---

## 18. History 조회

별도 `history` 테이블을 만들지 않는다.

```text
questions
+ ai_responses
+ trust_scores
+ final_results
```

| API 필드 | DB 출처 |
|---|---|
| `question_id` | `questions.id` |
| `question` | `questions.selected_question` |
| `answer_purpose` | `questions.answer_purpose` |
| `question_type` | `questions.question_type` |
| `verification_basis` | `questions.verification_basis` |
| `status` | `questions.status` |
| `providers` | 성공한 `ai_responses.provider` |
| `model_names` | 성공한 `ai_responses.model_name` |
| `trust_score` | `trust_scores.total_score` |
| `grade` | `trust_scores.grade` |
| `summary` | `final_results.summary` |
| `tags` | `questions.tags` |
| `created_at` | `questions.created_at` |
| `completed_at` | `questions.completed_at` |

---

## 19. 인덱스

```sql
CREATE INDEX idx_questions_status ON questions(status);
CREATE INDEX idx_questions_created_at ON questions(created_at DESC);
CREATE INDEX idx_questions_answer_purpose ON questions(answer_purpose);
CREATE INDEX idx_questions_question_type ON questions(question_type);
CREATE INDEX idx_questions_verification_basis ON questions(verification_basis);
CREATE INDEX idx_questions_reanalysis ON questions(reanalysis_of_question_id);
CREATE INDEX idx_questions_tags_gin ON questions USING GIN(tags);

CREATE INDEX idx_ai_responses_question ON ai_responses(question_id);
CREATE INDEX idx_ai_responses_provider_status ON ai_responses(provider, status);
CREATE INDEX idx_ai_responses_model_score ON ai_responses(model_score DESC);

CREATE INDEX idx_claims_question ON claims(question_id);
CREATE INDEX idx_claims_importance ON claims(question_id, importance);
CREATE INDEX idx_claims_verification_status ON claims(question_id, verification_status);
CREATE INDEX idx_claims_verification_basis ON claims(question_id, verification_basis);
CREATE INDEX idx_claims_source_models_gin ON claims USING GIN(source_models);

CREATE INDEX idx_deterministic_checks_question ON deterministic_checks(question_id);
CREATE INDEX idx_deterministic_checks_claim ON deterministic_checks(claim_id);
CREATE INDEX idx_deterministic_checks_passed ON deterministic_checks(check_passed);

CREATE INDEX idx_search_documents_question ON search_documents(question_id);
CREATE INDEX idx_search_documents_source_type ON search_documents(source_type);
CREATE INDEX idx_search_documents_published_at ON search_documents(published_at DESC);
CREATE INDEX idx_search_documents_content_hash ON search_documents(content_hash);

CREATE INDEX idx_document_chunks_document ON document_chunks(document_id);
CREATE INDEX idx_document_chunks_search_vector ON document_chunks USING GIN(search_vector);
CREATE INDEX idx_document_chunks_hash ON document_chunks(chunk_hash);

CREATE INDEX idx_document_embeddings_chunk ON document_embeddings(chunk_id);

CREATE INDEX idx_evidences_question ON evidences(question_id);
CREATE INDEX idx_evidences_claim ON evidences(claim_id);
CREATE INDEX idx_evidences_hybrid_score ON evidences(claim_id, hybrid_score DESC);
CREATE INDEX idx_evidences_relation ON evidences(claim_id, relation);
CREATE INDEX idx_evidences_source_type ON evidences(source_type);

CREATE INDEX idx_risks_question ON risks(question_id);
CREATE INDEX idx_risks_claim ON risks(claim_id);
CREATE INDEX idx_risks_level ON risks(risk_level);

CREATE INDEX idx_trust_scores_total_score ON trust_scores(total_score DESC);
```

Vector 인덱스는 HNSW 또는 IVFFlat 중 하나를 선택한다.

```sql
CREATE INDEX idx_document_embeddings_hnsw
ON document_embeddings
USING hnsw (embedding vector_cosine_ops);
```

또는:

```sql
CREATE INDEX idx_document_embeddings_ivfflat
ON document_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

---

## 20. 데이터 저장 순서

```text
1. questions 생성
2. 질문 분석 결과 저장
3. ai_responses 저장
4. claims 저장
5. deterministic_checks 저장
6. search_documents 저장
7. document_chunks 저장
8. document_embeddings 저장
9. evidences 저장
10. claims 검증 결과 갱신
11. risks 저장
12. ai_responses 모델별 점수 갱신
13. trust_scores 저장
14. final_results 저장
15. questions.status = completed
```

`trust_scores`와 `final_results` 저장이 모두 성공하기 전에는 분석 상태를 `completed`로 변경하지 않는다.

---

## 21. Transaction 원칙

- 외부 API 호출 중 긴 DB Transaction을 유지하지 않는다.
- 단계별로 짧게 Commit한다.
- 최종 Trust Score 저장, Final Result 저장, Question 완료 전환은 하나의 Transaction으로 처리하는 것을 권장한다.
- 하나라도 실패하면 `completed`로 변경하지 않는다.

---

## 22. 재분석

재분석 시 기존 결과를 갱신하지 않는다.

```text
기존 질문:
questions.id = A

재분석:
questions.id = B
questions.reanalysis_of_question_id = A
```

---

## 23. Mock Mode

```env
USE_MOCK=true
```

Mock Mode에서도 실제 API와 같은 테이블 구조를 사용한다.

```text
questions.execution_mode = mock
document_embeddings.is_mock = true
```

Real Mode:

```env
USE_MOCK=false
```

```text
questions.execution_mode = real
```

Provider 실패를 Mock 결과로 몰래 대체하지 않는다.

---

## 24. 데이터 삭제

MVP에는 사용자용 삭제 API가 없다.

개발용 초기화는 명시적인 Script로만 수행한다.

```bash
python scripts/reset_db.py
```

서버 시작 시 자동으로 테이블을 삭제하지 않는다.

---

## 25. 보안

DB에 저장하지 않는 데이터:

- OpenAI API Key
- Anthropic API Key
- OpenRouter API Key
- Gemini API Key
- Tavily API Key
- PostgreSQL 비밀번호 원문
- 전체 환경 변수
- 시스템 프롬프트 전체

오류 메시지에 다음 내용을 포함하지 않는다.

- 전체 `DATABASE_URL`
- DB 비밀번호
- API Key
- Stack Trace
- 서버 내부 절대 경로

---

## 26. SQLAlchemy 권장 구조

```text
backend/app/models/
├── __init__.py
├── question.py
├── ai_response.py
├── claim.py
├── deterministic_check.py
├── search_document.py
├── document_chunk.py
├── document_embedding.py
├── evidence.py
├── risk.py
├── trust_score.py
└── final_result.py
```

```text
backend/app/db/
├── base.py
├── session.py
└── init_db.py
```

---

## 27. JSONB 사용 기준

```text
suggested_keywords
tags
stage_details
model_score_detail
source_models
positive_factors
deductions
limitations
execution_detail
score_reasons
strengths
calculation_detail
cautions
citations
key_issues
cross_review
source_summary
claim_distribution
claim_evidence_relations
```

JSONB를 사용하더라도 Pydantic Model로 내부 구조를 검증한 뒤 저장한다.

---

## 28. 주요 점수 관련 DB 규칙

### Logic

다음을 Logic 문제로 저장하지 않는다.

- 모델별 답변 길이 차이
- 한 모델의 추가 설명
- 다른 모델의 단순 미언급
- 예시 차이
- 표현 차이
- 일반적인 Missing Point

실제 자기모순이나 잘못된 추론만 `cross_review.logic_issues`에 저장한다.

### Consensus

`claims.consensus_score`는 문장 일치율이 아니라 핵심 의미의 합의도를 저장한다.

```text
GPT: 핵심 의미 A
Claude: 핵심 의미 A + 추가 설명 B
Gemini: 핵심 의미 A
```

위 경우 Core Claim의 Consensus는 높은 값이어야 한다.

### Evidence Support

근거 지지도는 다음 개수만으로 계산하지 않는다.

```text
검색 문서 수
블로그 수
Evidence 수
```

다음을 사용한다.

- Verification Basis
- Deterministic Check
- Core Claim 검증 상태
- Evidence 직접성
- 출처 품질
- 출처 간 일치도
- 반박 Evidence

---

## 29. 완료 기준

```text
[ ] PostgreSQL 16 연결 성공
[ ] pgvector Extension 활성화
[ ] 총 11개 테이블 생성
[ ] questions에 answer_purpose 저장
[ ] questions에 verification_basis 저장
[ ] questions에 display_stage 저장
[ ] ai_responses에 모델별 신뢰도 저장
[ ] claims에 C1·C2 표시 ID 저장
[ ] claims에 의미 기반 Consensus 저장
[ ] claims에 Verification Basis 저장
[ ] claims에 근거 직접성과 출처 합의도 저장
[ ] deterministic_checks 테이블 생성
[ ] 수학·진법·논리 검증 결과 저장
[ ] 검색 문서와 Evidence 구분
[ ] PostgreSQL FTS 동작
[ ] VECTOR(1536) 저장
[ ] pgvector 검색 동작
[ ] Evidence Hybrid Score 저장
[ ] Risk 중복 방지
[ ] Trust Score 상세 이유 저장
[ ] 추가 설명을 Logic Issue로 저장하지 않음
[ ] 단순 미언급을 Contradiction으로 저장하지 않음
[ ] Final Result에 Cross Review 저장
[ ] Final Result에 Source Summary 저장
[ ] Final Result에 Claim Distribution 저장
[ ] History 점수·모델 필터 가능
[ ] 재분석 시 기존 결과 유지
[ ] Mock과 Real 결과 구분
[ ] 실제 API Key를 저장하지 않음
[ ] DB 초기화가 명시적인 Script로만 수행됨
```
