from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    use_mock: bool
    database_connected: bool
    pgvector_enabled: bool
