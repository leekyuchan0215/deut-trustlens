# TrustLens API Specification

## 1. 공통 원칙

- Base URL: `http://localhost:8000`
- JSON 기본
- 필드명은 `snake_case`
- 시간은 ISO 8601 UTC
- UUID는 문자열
- Mock과 Real 응답 구조 동일
- Trust Score와 모델별 점수는 Backend가 계산
- Frontend는 점수를 재계산하지 않음

---

## 2. Enum

### Answer Purpose

```text
fact_check
concept_understanding
decision_support
evidence_focused
risk_analysis
```

### Question Type

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

### Verification Basis

```text
deterministic
authoritative_fact
web_evidence
mixed
subjective
```

### Analysis Status

```text
queued
processing
completed
failed
```

### Pipeline Stage

```text
question_analysis
prompt_refinement
ai_generation
claim_extraction
claim_consolidation
verification_strategy
deterministic_verification
search_query_generation
evidence_search
document_storage
chunking
embedding
hybrid_search
evidence_selection
claim_verification
cross_review
risk_analysis
trust_score
final_answer
reflection
result_storage
completed
failed
```

### Display Stage

```text
question_analysis
ai_generation
claim_extraction
evidence_search
hybrid_search
claim_verification
final_answer
```

### Provider

```text
gpt
claude
gemini
```

### Verification Status

```text
pending
verified
weak_evidence
unsupported
contradicted
```

### Source Type

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

---

## 3. Health Check

```http
GET /api/v1/health
```

```json
{
  "status": "ok",
  "service": "TrustLens API",
  "environment": "development",
  "use_mock": true,
  "database_connected": true,
  "pgvector_enabled": true
}
```

---

## 4. 질문 개선

```http
POST /api/refine-prompt
```

Request:

```json
{
  "question": "RAG랑 Fine-tuning 뭐가 좋아?",
  "answer_purpose": "decision_support"
}
```

Response:

```json
{
  "original_question": "RAG랑 Fine-tuning 뭐가 좋아?",
  "refined_question": "RAG와 Fine-tuning을 최신 정보 반영, 비용, 유지보수성, 출력 일관성 측면에서 비교해 주세요.",
  "answer_purpose": "decision_support",
  "question_type": "comparison",
  "verification_basis": "mixed",
  "suggested_keywords": [
    "RAG",
    "Fine-tuning",
    "비용",
    "유지보수성"
  ]
}
```

Validation:

```text
question 2~2000자
answer_purpose Enum 필수
```

---

## 5. 분석 생성

```http
POST /api/analyze
```

Request:

```json
{
  "question": "실제 분석 질문",
  "original_question": "최초 질문",
  "refined_question": "개선 질문",
  "answer_purpose": "decision_support"
}
```

Response:

```http
202 Accepted
```

```json
{
  "question_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "current_stage": "question_analysis",
  "display_stage": "question_analysis",
  "progress_percent": 0,
  "message": "검증 작업이 생성되었습니다.",
  "created_at": "2026-07-05T03:30:00Z"
}
```

---

## 6. 진행 상태

```http
GET /api/progress/{question_id}
```

```json
{
  "question_id": "uuid",
  "status": "processing",
  "current_stage": "hybrid_search",
  "display_stage": "hybrid_search",
  "progress_percent": 58,
  "message": "Hybrid Search를 수행하고 있습니다.",
  "estimated_remaining_seconds": 24,
  "display_steps": [
    {
      "stage": "question_analysis",
      "label": "질문 분석",
      "status": "completed",
      "duration_ms": 1200
    },
    {
      "stage": "hybrid_search",
      "label": "Hybrid Search",
      "status": "processing",
      "duration_ms": null
    }
  ],
  "model_statuses": [
    {
      "provider": "gpt",
      "model_name": "configured-gpt-model",
      "status": "success",
      "latency_ms": 1520
    }
  ],
  "metrics": {
    "total_claims": 8,
    "verified_claims": 0,
    "deterministic_checks": 0,
    "search_documents": 18,
    "selected_evidences": 0
  },
  "error_message": null,
  "updated_at": "2026-07-05T03:31:20Z"
}
```

Display Step Status:

```text
pending
processing
completed
failed
```

---

## 7. 결과 요약

```http
GET /api/result/{question_id}
```

```json
{
  "question_id": "uuid",
  "status": "completed",
  "original_question": "원본 질문",
  "refined_question": "개선 질문",
  "selected_question": "실제 질문",
  "answer_purpose": "decision_support",
  "question_type": "comparison",
  "verification_basis": "mixed",
  "trust_score": 87.45,
  "grade": "신뢰도 높음",
  "summary": "핵심 요약",
  "final_answer": "최종 검증 답변",
  "cautions": [
    "주의사항"
  ],
  "trust_score_breakdown": {},
  "model_scores": [],
  "claim_summary": {
    "total": 8,
    "core": 5,
    "supporting": 3,
    "verified": 5,
    "weak_evidence": 2,
    "unsupported": 1,
    "contradicted": 0
  },
  "source_summary": {
    "total_documents": 153,
    "used_evidences": 24,
    "web_documents": 128,
    "academic_papers": 12,
    "technical_blogs": 8,
    "official_documents": 5,
    "government_sources": 0,
    "deterministic_checks": 0
  },
  "key_issues": [
    "최신성 vs 출력 일관성"
  ],
  "created_at": "2026-07-05T03:30:00Z",
  "completed_at": "2026-07-05T03:32:00Z"
}
```

완료 전:

```http
409 Conflict
```

---

## 8. 모델별 점수 Object

```json
{
  "provider": "gpt",
  "model_name": "configured-gpt-model",
  "score": 88,
  "grade": "신뢰도 높음",
  "reason": "핵심 Claim이 대부분 검증되었습니다."
}
```

답변 길이나 추가 설명의 양을 감점 사유로 사용하지 않는다.

---

## 9. 상세 결과

```http
GET /api/result/{question_id}/detail
```

```json
{
  "question_id": "uuid",
  "status": "completed",
  "original_question": "원본 질문",
  "refined_question": "개선 질문",
  "selected_question": "실제 질문",
  "answer_purpose": "decision_support",
  "question_type": "comparison",
  "verification_basis": "mixed",
  "ai_responses": [],
  "model_scores": [],
  "claims": [],
  "deterministic_checks": [],
  "evidences": [],
  "cross_review": {},
  "risk_analysis": [],
  "trust_score_breakdown": {},
  "source_summary": {},
  "claim_distribution": {},
  "claim_evidence_relations": [],
  "final_result": {},
  "created_at": "2026-07-05T03:30:00Z",
  "completed_at": "2026-07-05T03:32:00Z"
}
```

---

## 10. AI Response Object

```json
{
  "id": "uuid",
  "provider": "gpt",
  "model_name": "configured-gpt-model",
  "status": "success",
  "response_text": "원본 답변",
  "latency_ms": 1250,
  "input_tokens": 250,
  "output_tokens": 620,
  "total_tokens": 870,
  "estimated_cost": 0.0023,
  "error_message": null
}
```

---

## 11. Claim Object

```json
{
  "id": "uuid",
  "display_id": "C1",
  "claim_text": "RAG는 외부 문서를 검색하여 최신 정보를 반영할 수 있다.",
  "normalized_claim": "RAG는 외부 검색을 통해 최신 정보를 반영할 수 있다.",
  "claim_type": "fact",
  "importance": "core",
  "verification_basis": "authoritative_fact",
  "source_models": [
    "gpt",
    "claude",
    "gemini"
  ],
  "consensus_score": 100,
  "consensus_level": "high",
  "verification_status": "verified",
  "verification_confidence": 96,
  "verification_reason": "공식 문서가 직접 지지합니다.",
  "verification_mode": "llm_judge",
  "direct_evidence_strength": 95,
  "cross_source_agreement": 92,
  "risk_level": "low",
  "evidence_count": 3,
  "evidence_ids": [
    "uuid"
  ],
  "positive_factors": [],
  "deductions": [],
  "limitations": []
}
```

`display_id`는 질문 내부에서 `C1`, `C2` 형태로 고유하다.

---

## 12. Deterministic Check Object

```json
{
  "id": "uuid",
  "claim_id": "uuid",
  "check_type": "calculator",
  "input_expression": "25 * 4",
  "expected_result": "100",
  "ai_claimed_result": "100",
  "check_passed": true,
  "verification_status": "verified",
  "verification_confidence": 100,
  "verification_reason": "독립 계산 결과와 일치합니다.",
  "limitations": []
}
```

Check Type:

```text
calculator
unit_conversion
base_conversion
logic_evaluation
formula
safe_code_execution
rule_based
```

---

## 13. Evidence Object

```json
{
  "id": "uuid",
  "claim_id": "uuid",
  "title": "문서 제목",
  "url": "https://example.com",
  "domain": "example.com",
  "snippet": "Claim 검증에 사용한 문장",
  "source_name": "출처 이름",
  "source_type": "documentation",
  "published_at": "2026-06-01T00:00:00Z",
  "searched_at": "2026-07-05T03:31:00Z",
  "relation": "support",
  "keyword_score": 0.91,
  "vector_score": 0.88,
  "hybrid_score": 0.898,
  "source_quality_score": 95,
  "directness_score": 96,
  "support_score": 94,
  "rank": 1
}
```

검색 점수는 0~1, 검증 점수는 0~100이다.

---

## 14. Cross Review Object

```json
{
  "semantic_consensus": [
    {
      "claim_id": "uuid",
      "meaning": "RAG는 외부 정보를 검색해 활용한다.",
      "agreeing_models": [
        "gpt",
        "claude",
        "gemini"
      ],
      "consensus_level": "high"
    }
  ],
  "consensus": [
    "세 모델의 핵심 의미가 일치합니다."
  ],
  "contradictions": [],
  "model_additions": {
    "gpt": [],
    "claude": [
      "유지보수 설명을 추가했습니다."
    ],
    "gemini": []
  },
  "missing_points": [
    {
      "description": "보안 설명이 부족합니다.",
      "affects_core_answer": false
    }
  ],
  "overclaims": [],
  "logic_issues": [],
  "model_strengths": {
    "gpt": [],
    "claude": [],
    "gemini": []
  },
  "model_weaknesses": {
    "gpt": [],
    "claude": [],
    "gemini": []
  },
  "cross_review_mode": "llm_judge"
}
```

추가 설명과 미언급은 `contradictions` 또는 `logic_issues`가 아니다.

---

## 15. Risk Object

```json
{
  "id": "uuid",
  "claim_id": null,
  "risk_type": "source_credibility",
  "risk_level": "low",
  "description": "보조 Claim 일부가 블로그에 의존합니다.",
  "affects_core_answer": false,
  "resolved_by_evidence": true,
  "penalty": 0,
  "detected_by": "llm_judge"
}
```

---

## 16. Trust Score Breakdown

```json
{
  "evidence_support_score": 96,
  "source_quality_score": 100,
  "consensus_score": 98,
  "logic_score": 99,
  "freshness_score": 100,
  "base_score": 98.5,
  "contradiction_penalty": 0,
  "risk_penalty": 0,
  "total_score": 98.5,
  "grade": "신뢰도 매우 높음",
  "score_reasons": {
    "evidence_support": {
      "score": 96,
      "reason": "핵심 Claim이 공식 출처에서 검증되었습니다.",
      "verification_basis": "authoritative_fact",
      "positive_factors": [
        "Core Claim 2개 모두 검증됨"
      ],
      "negative_factors": [
        "Supporting Claim 1개의 근거가 제한적임"
      ]
    }
  },
  "strengths": [],
  "deductions": [],
  "calculation_detail": {
    "formula": "0.40×Evidence Support + 0.20×Source Quality + 0.15×Consensus + 0.15×Logic + 0.10×Freshness - Penalties",
    "weighted_scores": {},
    "verification_basis": "authoritative_fact",
    "core_claim_count": 2,
    "verified_core_claim_count": 2,
    "weak_core_claim_count": 0,
    "unsupported_core_claim_count": 0,
    "contradicted_core_claim_count": 0,
    "supporting_claim_count": 1,
    "used_evidence_count": 2,
    "official_source_count": 1,
    "deterministic_check_count": 0
  },
  "formula_version": "1.1"
}
```

---

## 17. Final Result Object

```json
{
  "summary": "핵심 결론",
  "final_answer": "검증된 최종 답변",
  "cautions": [],
  "citations": [
    {
      "evidence_id": "uuid",
      "title": "출처 제목",
      "url": "https://example.com"
    }
  ],
  "final_answer_mode": "llm_judge",
  "cross_review_mode": "llm_judge",
  "judge_provider": "configured-provider",
  "judge_model": "configured-model",
  "judge_attempts": 1,
  "fallback_reason": null
}
```

Deterministic 문제는 Citation이 비어 있을 수 있다.

---

## 18. History

```http
GET /api/history
```

Query:

| 이름 | 설명 |
|---|---|
| `search` | 질문·키워드 |
| `status` | 상태 |
| `min_score` | 최소 점수 |
| `max_score` | 최대 점수 |
| `provider` | GPT·Claude·Gemini |
| `sort` | 정렬 |
| `limit` | 개수 |
| `offset` | 시작 위치 |

Sort:

```text
newest
oldest
score_high
score_low
```

Response:

```json
{
  "items": [
    {
      "question_id": "uuid",
      "question": "질문",
      "answer_purpose": "decision_support",
      "question_type": "comparison",
      "verification_basis": "mixed",
      "status": "completed",
      "providers": [
        "gpt",
        "claude",
        "gemini"
      ],
      "model_names": [],
      "trust_score": 87.45,
      "grade": "신뢰도 높음",
      "summary": "요약",
      "tags": [
        "AI",
        "비교 분석"
      ],
      "created_at": "2026-07-05T03:30:00Z",
      "completed_at": "2026-07-05T03:32:00Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

---

## 19. 재분석

```http
POST /api/reanalyze/{question_id}
```

Optional Request:

```json
{
  "answer_purpose": "evidence_focused"
}
```

Response:

```json
{
  "original_question_id": "uuid",
  "question_id": "new-uuid",
  "status": "queued",
  "current_stage": "question_analysis",
  "display_stage": "question_analysis",
  "progress_percent": 0,
  "message": "재검증 작업이 생성되었습니다.",
  "created_at": "2026-07-05T04:00:00Z"
}
```

기존 결과를 덮어쓰지 않는다.

---

## 20. 오류 형식

```json
{
  "error": {
    "code": "QUESTION_NOT_FOUND",
    "message": "요청한 분석 기록을 찾을 수 없습니다.",
    "details": null
  }
}
```

주요 Status:

| HTTP | 상황 |
|---|---|
| 200 | 성공 |
| 202 | 분석 생성 |
| 400 | 잘못된 요청 |
| 404 | 기록 없음 |
| 409 | 결과 준비 전 |
| 422 | Validation 실패 |
| 500 | 내부 오류 |
| 502 | 외부 Provider 오류 |
| 503 | DB 또는 필수 서비스 오류 |
| 504 | Timeout |

비밀값과 Stack Trace를 포함하지 않는다.

---

## 21. Endpoint 목록

| Method | Endpoint | 기능 |
|---|---|---|
| GET | `/api/v1/health` | 상태 |
| POST | `/api/refine-prompt` | 질문 개선 |
| POST | `/api/analyze` | 분석 생성 |
| GET | `/api/progress/{question_id}` | 진행 상태 |
| GET | `/api/result/{question_id}` | 결과 요약 |
| GET | `/api/result/{question_id}/detail` | 상세 결과 |
| GET | `/api/history` | 기록 |
| POST | `/api/reanalyze/{question_id}` | 재분석 |

---

## 22. 완료 기준

```text
[ ] UI 답변 목적 5개 일치
[ ] Verification Basis 제공
[ ] Loading Display Stage 제공
[ ] 모델별 신뢰도 제공
[ ] Source Summary 제공
[ ] Claim C1·C2 제공
[ ] 의미 기반 Consensus 제공
[ ] Deterministic Check 제공
[ ] Score Reason 제공
[ ] Claim Distribution 제공
[ ] Claim–Evidence 관계 제공
[ ] History 필터 제공
[ ] Mock·Real 구조 일치
[ ] Swagger 검증
```
