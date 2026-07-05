from datetime import datetime

from pydantic import BaseModel


class DisplayStep(BaseModel):
    stage: str
    label: str
    status: str
    duration_ms: int | None = None


class ModelStatus(BaseModel):
    provider: str
    model_name: str
    status: str
    latency_ms: int | None = None


class ProgressMetrics(BaseModel):
    total_claims: int = 0
    verified_claims: int = 0
    deterministic_checks: int = 0
    search_documents: int = 0
    selected_evidences: int = 0


class ProgressResponse(BaseModel):
    question_id: str
    status: str
    current_stage: str
    display_stage: str
    progress_percent: int
    message: str
    estimated_remaining_seconds: int | None = None
    display_steps: list[DisplayStep]
    model_statuses: list[ModelStatus]
    metrics: ProgressMetrics
    error_message: str | None = None
    updated_at: datetime
