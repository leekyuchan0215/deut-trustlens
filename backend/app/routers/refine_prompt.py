from fastapi import APIRouter

from app.schemas.refine_prompt import RefinePromptRequest, RefinePromptResponse
from app.services.question_analysis import classify_question, extract_keywords, refine_question

router = APIRouter(tags=["refine-prompt"])


@router.post("/api/refine-prompt", response_model=RefinePromptResponse)
def refine_prompt(payload: RefinePromptRequest) -> RefinePromptResponse:
    question_type, verification_basis = classify_question(payload.question)
    refined = refine_question(payload.question, payload.answer_purpose, question_type)
    keywords = extract_keywords(payload.question)

    return RefinePromptResponse(
        original_question=payload.question,
        refined_question=refined,
        answer_purpose=payload.answer_purpose,
        question_type=question_type,
        verification_basis=verification_basis,
        suggested_keywords=keywords,
    )
