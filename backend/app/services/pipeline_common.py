"""Stage bookkeeping shared by app/services/mock_pipeline.py and
app/services/real_pipeline.py, so progress reporting behaves identically in
both modes."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Question

STAGE_LABELS = {
    "question_analysis": "질문 분석",
    "prompt_refinement": "질문 개선",
    "ai_generation": "AI 답변 생성",
    "claim_extraction": "Claim 추출",
    "claim_consolidation": "Claim 통합",
    "verification_strategy": "검증 방식 분류",
    "deterministic_verification": "결정적 검증",
    "search_query_generation": "검색어 생성",
    "evidence_search": "외부 근거 검색",
    "document_storage": "문서 저장",
    "chunking": "문서 분할",
    "embedding": "임베딩 생성",
    "hybrid_search": "Hybrid Search",
    "evidence_selection": "근거 선정",
    "claim_verification": "Claim 검증",
    "cross_review": "교차 검토",
    "risk_analysis": "위험 분석",
    "trust_score": "신뢰도 점수 계산",
    "final_answer": "최종 답변 생성",
    "reflection": "최종 검토",
    "result_storage": "결과 저장",
    "completed": "완료",
}


def advance_stage(
    db: Session, question: Question, stage: str, display_stage: str, percent: int, duration_ms: int
) -> None:
    question.current_stage = stage
    question.display_stage = display_stage
    question.progress_percent = percent
    question.estimated_remaining_seconds = max(0, round((100 - percent) / 100 * 3))
    question.stage_details = [
        *question.stage_details,
        {
            "stage": stage,
            "display_stage": display_stage,
            "label": STAGE_LABELS.get(stage, stage),
            "status": "completed",
            "duration_ms": duration_ms,
        },
    ]
    question.updated_at = datetime.now(timezone.utc)
    db.add(question)
    db.commit()


def mark_failed(db: Session, question_id: str, error_code: str, error_message: str) -> None:
    question = db.get(Question, question_id)
    if question is None:
        return
    question.status = "failed"
    question.error_code = error_code
    question.error_message = error_message
    question.updated_at = datetime.now(timezone.utc)
    db.add(question)
    db.commit()
