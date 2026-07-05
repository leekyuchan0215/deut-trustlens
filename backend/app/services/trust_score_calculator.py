"""Backend-only deterministic Trust Score calculation.

LLMs never decide the final numeric score (docs/TRUST_SCORE.md, CLAUDE.md #6).
This module implements the fixed weighted formula from docs/DB_SCHEMA.md #16:

    Base Score = 0.40*Evidence Support + 0.20*Source Quality
               + 0.15*Consensus + 0.15*Logic + 0.10*Freshness
    Final Score = Base Score - Contradiction Penalty - Risk Penalty
"""
from dataclasses import dataclass

CORE_WEIGHT = 1.0
SUPPORTING_WEIGHT = 0.25

_STATUS_SCORE = {
    "verified": 100.0,
    "weak_evidence": 60.0,
    "unsupported": 20.0,
    "contradicted": 0.0,
    "pending": 40.0,
}

FORMULA_VERSION = "1.1"


def grade_for_score(score: float) -> str:
    if score >= 90:
        return "신뢰도 매우 높음"
    if score >= 75:
        return "신뢰도 높음"
    if score >= 55:
        return "신뢰도 보통"
    if score >= 35:
        return "신뢰도 낮음"
    return "신뢰도 매우 낮음"


def _claim_weight(importance: str) -> float:
    return CORE_WEIGHT if importance == "core" else SUPPORTING_WEIGHT


def _weighted_average(pairs: list[tuple[float, float]]) -> float:
    """pairs of (value, weight); returns 100.0 if there is nothing to weigh."""
    total_weight = sum(weight for _, weight in pairs)
    if total_weight <= 0:
        return 100.0
    return sum(value * weight for value, weight in pairs) / total_weight


@dataclass
class ClaimScoreInput:
    importance: str
    verification_status: str
    consensus_score: float | None
    deterministic_verified: bool
    evidence_source_quality: list[float]


def calculate_evidence_support(claims: list[ClaimScoreInput]) -> tuple[float, list[str], list[str]]:
    pairs = []
    positives: list[str] = []
    negatives: list[str] = []
    core_verified = 0
    core_total = 0
    for claim in claims:
        weight = _claim_weight(claim.importance)
        if claim.importance == "core":
            core_total += 1
        if claim.deterministic_verified:
            score = 100.0
        else:
            score = _STATUS_SCORE.get(claim.verification_status, 40.0)
        if claim.importance == "core" and claim.verification_status == "verified":
            core_verified += 1
        pairs.append((score, weight))
    if core_total:
        positives.append(f"Core Claim {core_verified}/{core_total}개 검증됨")
    weak = [c for c in claims if c.verification_status in ("weak_evidence", "unsupported", "contradicted")]
    if weak:
        negatives.append(f"근거가 부족하거나 미검증인 Claim {len(weak)}개 존재")
    return _weighted_average(pairs), positives, negatives


def calculate_source_quality(claims: list[ClaimScoreInput]) -> tuple[float, list[str], list[str]]:
    pairs = []
    positives: list[str] = []
    negatives: list[str] = []
    official_backed = 0
    for claim in claims:
        weight = _claim_weight(claim.importance)
        if claim.deterministic_verified:
            pairs.append((100.0, weight))
            continue
        if claim.evidence_source_quality:
            avg_quality = sum(claim.evidence_source_quality) / len(claim.evidence_source_quality)
            if avg_quality >= 85:
                official_backed += 1
            pairs.append((avg_quality, weight))
        else:
            pairs.append((50.0, weight))
    if official_backed:
        positives.append(f"공식·학술 출처로 뒷받침된 Claim {official_backed}개")
    low_quality = [c for c in claims if c.evidence_source_quality and sum(c.evidence_source_quality) / len(c.evidence_source_quality) < 60]
    if low_quality:
        negatives.append(f"출처 품질이 낮은 Claim {len(low_quality)}개 존재")
    return _weighted_average(pairs), positives, negatives


def calculate_consensus(claims: list[ClaimScoreInput]) -> tuple[float, list[str], list[str]]:
    pairs = []
    positives: list[str] = []
    negatives: list[str] = []
    for claim in claims:
        weight = _claim_weight(claim.importance)
        score = claim.consensus_score if claim.consensus_score is not None else 70.0
        pairs.append((score, weight))
    high = [c for c in claims if (c.consensus_score or 0) >= 90]
    if high:
        positives.append(f"AI {len(high)}개 Claim에서 핵심 의미 합의")
    low = [c for c in claims if c.importance == "core" and (c.consensus_score or 0) < 60]
    if low:
        negatives.append(f"Core Claim {len(low)}개에서 모델 간 합의도 낮음")
    return _weighted_average(pairs), positives, negatives


def calculate_logic(logic_issue_count: int) -> tuple[float, list[str], list[str]]:
    score = max(0.0, 100.0 - (logic_issue_count * 15.0))
    negatives = [f"실제 논리 오류 {logic_issue_count}건 발견"] if logic_issue_count else []
    positives = ["모델 간 답변 길이·추가 설명 차이는 감점에 반영하지 않음"]
    return score, positives, negatives


def calculate_freshness(question_type: str, outdated_risk_count: int) -> tuple[float, list[str], list[str]]:
    if outdated_risk_count:
        score = max(0.0, 90.0 - outdated_risk_count * 20.0)
        return score, [], [f"최신성 문제 {outdated_risk_count}건 발견"]
    if question_type == "current_information":
        return 90.0, ["최신 정보 확인 완료"], []
    return 100.0, ["시점에 민감하지 않은 질문"], []


def calculate_trust_score(
    claims: list[ClaimScoreInput],
    contradiction_penalty: float,
    risk_penalty: float,
    logic_issue_count: int,
    outdated_risk_count: int,
    question_type: str,
    verification_basis: str,
) -> dict:
    evidence_support, es_pos, es_neg = calculate_evidence_support(claims)
    source_quality, sq_pos, sq_neg = calculate_source_quality(claims)
    consensus, co_pos, co_neg = calculate_consensus(claims)
    logic, lo_pos, lo_neg = calculate_logic(logic_issue_count)
    freshness, fr_pos, fr_neg = calculate_freshness(question_type, outdated_risk_count)

    base_score = (
        0.40 * evidence_support
        + 0.20 * source_quality
        + 0.15 * consensus
        + 0.15 * logic
        + 0.10 * freshness
    )
    total_score = max(0.0, min(100.0, base_score - contradiction_penalty - risk_penalty))

    core_claims = [c for c in claims if c.importance == "core"]
    supporting_claims = [c for c in claims if c.importance == "supporting"]

    def _count(status: str, pool: list[ClaimScoreInput]) -> int:
        return len([c for c in pool if c.verification_status == status])

    score_reasons = {
        "evidence_support": {
            "score": round(evidence_support, 2),
            "reason": "Core Claim 검증 상태와 결정적 검증 결과를 기준으로 산정했습니다.",
            "verification_basis": verification_basis,
            "positive_factors": es_pos,
            "negative_factors": es_neg,
        },
        "source_quality": {
            "score": round(source_quality, 2),
            "reason": "Claim별 채택된 Evidence의 출처 품질 평균을 기준으로 산정했습니다.",
            "verification_basis": verification_basis,
            "positive_factors": sq_pos,
            "negative_factors": sq_neg,
        },
        "consensus": {
            "score": round(consensus, 2),
            "reason": "모델 간 핵심 의미 합의도를 기준으로 산정했습니다.",
            "verification_basis": verification_basis,
            "positive_factors": co_pos,
            "negative_factors": co_neg,
        },
        "logic": {
            "score": round(logic, 2),
            "reason": "실제 논리적 자기모순만 감점했습니다.",
            "verification_basis": verification_basis,
            "positive_factors": lo_pos,
            "negative_factors": lo_neg,
        },
        "freshness": {
            "score": round(freshness, 2),
            "reason": "질문의 최신성 민감도와 발견된 Risk를 기준으로 산정했습니다.",
            "verification_basis": verification_basis,
            "positive_factors": fr_pos,
            "negative_factors": fr_neg,
        },
    }

    strengths = es_pos + sq_pos + co_pos
    deductions = es_neg + sq_neg + co_neg + lo_neg + fr_neg

    calculation_detail = {
        "formula": "0.40×Evidence Support + 0.20×Source Quality + 0.15×Consensus + 0.15×Logic + 0.10×Freshness - Penalties",
        "weighted_scores": {
            "evidence_support": round(0.40 * evidence_support, 2),
            "source_quality": round(0.20 * source_quality, 2),
            "consensus": round(0.15 * consensus, 2),
            "logic": round(0.15 * logic, 2),
            "freshness": round(0.10 * freshness, 2),
        },
        "verification_basis": verification_basis,
        "core_claim_count": len(core_claims),
        "verified_core_claim_count": _count("verified", core_claims),
        "weak_core_claim_count": _count("weak_evidence", core_claims),
        "unsupported_core_claim_count": _count("unsupported", core_claims),
        "contradicted_core_claim_count": _count("contradicted", core_claims),
        "supporting_claim_count": len(supporting_claims),
        "used_evidence_count": sum(len(c.evidence_source_quality) for c in claims),
        "official_source_count": sum(1 for c in claims if c.evidence_source_quality and sum(c.evidence_source_quality) / len(c.evidence_source_quality) >= 85),
        "deterministic_check_count": sum(1 for c in claims if c.deterministic_verified),
    }

    return {
        "evidence_support_score": round(evidence_support, 2),
        "source_quality_score": round(source_quality, 2),
        "consensus_score": round(consensus, 2),
        "logic_score": round(logic, 2),
        "freshness_score": round(freshness, 2),
        "base_score": round(base_score, 2),
        "contradiction_penalty": round(contradiction_penalty, 2),
        "risk_penalty": round(risk_penalty, 2),
        "total_score": round(total_score, 2),
        "grade": grade_for_score(total_score),
        "score_reasons": score_reasons,
        "strengths": strengths,
        "deductions": deductions,
        "calculation_detail": calculation_detail,
        "formula_version": FORMULA_VERSION,
    }


def calculate_model_score(claims_from_model: list[ClaimScoreInput]) -> tuple[float, str, str]:
    if not claims_from_model:
        return 100.0, grade_for_score(100.0), "이 모델이 언급한 Claim이 없습니다."
    pairs = [
        (
            100.0 if c.deterministic_verified else _STATUS_SCORE.get(c.verification_status, 40.0),
            _claim_weight(c.importance),
        )
        for c in claims_from_model
    ]
    score = _weighted_average(pairs)
    contradicted = _count_status(claims_from_model, "contradicted")
    unsupported_core = len(
        [c for c in claims_from_model if c.importance == "core" and c.verification_status == "unsupported"]
    )
    if contradicted:
        reason = f"핵심 주장 중 {contradicted}건이 근거와 모순되어 감점되었습니다."
    elif unsupported_core:
        reason = f"핵심 주장 중 {unsupported_core}건이 근거로 뒷받침되지 않았습니다."
    else:
        reason = "핵심 Claim이 대부분 검증되었습니다."
    return round(score, 2), grade_for_score(score), reason


def _count_status(claims: list[ClaimScoreInput], status: str) -> int:
    return len([c for c in claims if c.verification_status == status])
