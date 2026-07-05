from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import ApiError, api_error_handler, unhandled_error_handler, validation_error_handler
from app.routers import analyze, health, history, progress, reanalyze, refine_prompt, result

settings = get_settings()

app = FastAPI(title="TrustLens API", version="1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(ApiError, api_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)

app.include_router(health.router)
app.include_router(refine_prompt.router)
app.include_router(analyze.router)
app.include_router(progress.router)
app.include_router(result.router)
app.include_router(history.router)
app.include_router(reanalyze.router)
