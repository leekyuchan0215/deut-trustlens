"""Source quality reference table (docs/TRUST_SCORE.md #7)."""

SOURCE_QUALITY_BY_TYPE: dict[str, float] = {
    "deterministic_verifier": 100.0,
    "official": 100.0,
    "government": 100.0,
    "academic": 95.0,
    "paper": 95.0,
    "documentation": 90.0,
    "news": 80.0,
    "blog": 60.0,
    "community": 40.0,
    "unknown": 20.0,
}


def quality_for_source_type(source_type: str) -> float:
    return SOURCE_QUALITY_BY_TYPE.get(source_type, 20.0)
