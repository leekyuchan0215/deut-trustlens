from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.utils.enums import ANSWER_PURPOSE_VALUES


class AnalyzeRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    original_question: str
    refined_question: str | None = None
    answer_purpose: str

    @field_validator("question", "original_question")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value

    @field_validator("answer_purpose")
    @classmethod
    def answer_purpose_valid(cls, value: str) -> str:
        if value not in ANSWER_PURPOSE_VALUES:
            raise ValueError(f"answer_purpose must be one of {ANSWER_PURPOSE_VALUES}")
        return value


class AnalyzeResponse(BaseModel):
    question_id: str
    status: str
    current_stage: str
    display_stage: str
    progress_percent: int
    message: str
    created_at: datetime


class ReanalyzeRequest(BaseModel):
    answer_purpose: str | None = None

    @field_validator("answer_purpose")
    @classmethod
    def answer_purpose_valid(cls, value: str | None) -> str | None:
        if value is not None and value not in ANSWER_PURPOSE_VALUES:
            raise ValueError(f"answer_purpose must be one of {ANSWER_PURPOSE_VALUES}")
        return value


class ReanalyzeResponse(BaseModel):
    original_question_id: str
    question_id: str
    status: str
    current_stage: str
    display_stage: str
    progress_percent: int
    message: str
    created_at: datetime
