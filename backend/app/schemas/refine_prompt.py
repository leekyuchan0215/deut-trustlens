from pydantic import BaseModel, Field, field_validator

from app.utils.enums import ANSWER_PURPOSE_VALUES


class RefinePromptRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    answer_purpose: str

    @field_validator("question")
    @classmethod
    def question_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be blank")
        return value

    @field_validator("answer_purpose")
    @classmethod
    def answer_purpose_valid(cls, value: str) -> str:
        if value not in ANSWER_PURPOSE_VALUES:
            raise ValueError(f"answer_purpose must be one of {ANSWER_PURPOSE_VALUES}")
        return value


class RefinePromptResponse(BaseModel):
    original_question: str
    refined_question: str
    answer_purpose: str
    question_type: str
    verification_basis: str
    suggested_keywords: list[str]
