"""Backend-only deterministic Trust Score calculation.

LLMs never decide the final numeric score (docs/TRUST_SCORE.md, CLAUDE.md #6).
This module implements the fixed weighted formula from docs/DB_SCHEMA.md #16:

    Base Score = w_evidence*Evidence + w_source*Source Quality
               + w_consensus*Consensus + w_logic*Logic + w_freshness*Freshness
    Final Score = Base Score - Contradiction Penalty - Risk Penalty
"""
from dataclasses import dataclass
from statistics import mean

from app.core.config import get_settings

CORE_WEIGHT = 1.0
SUPPORTING_WEIGHT = 0.25

_STATUS_SCORE = {
    "verified": 100.0,
    "weak_evidence": 60.0,
    "unsupported": 20.0,
    "contradicted": 0.0,
    "pending": 40.0,
}

_GENEROUS_STATUS_SCORE = {
    "verified": 100.0,
    "weak_evidence": 72.0,
    "unsupported": 45.0,
    "contradicted": 0.0,
    "pending": 55.0,
}

FORMULA_VERSION = "1.3"


def _generous_mode() -> bool:
    return get_settings().trust_score_generous_mode


def _score_weights() -> tuple[float, float, float, float, float]:
    settings = get_settings()
    if settings.trust_score_generous_mode:
        return (0.18, 0.07, 0.35, 0.27, 0.13)
    return (
        settings.trust_weight_evidence,
        settings.trust_weight_source,
        settings.trust_weight_consensus,
        settings.trust_weight_logic,
        settings.trust_weight_freshness,
    )


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


def _status_score(verification_status: str) -> float:
    table = _GENEROUS_STATUS_SCORE if _generous_mode() else _STATUS_SCORE
    return table.get(verification_status, 40.0)


def _consensus_adjusted_evidence_score(claim: ClaimScoreInput, base_score: float) -> float:
    """High semantic agreement should not be drowned out by missing web evidence alone."""
    consensus = claim.consensus_score or 0.0
    if consensus < 80:
        return base_score
    generous = _generous_mode()
    if claim.importance == "supporting":
        floor = 70.0 if generous else 55.0
        if base_score < floor and consensus >= 85:
            return floor
    if claim.importance == "core" and claim.verification_status in ("unsupported", "weak_evidence", "pending"):
        if generous and consensus >= 88:
            return max(base_score, 78.0)
        if consensus >= 85:
            return max(base_score, 60.0)
    return base_score


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
            score = _status_score(claim.verification_status)
            score = _consensus_adjusted_evidence_score(claim, score)
        if claim.importance == "core" and claim.verification_status == "verified":
            core_verified += 1
        pairs.append((score, weight))
    if core_total:
        positives.append(f"Core Claim {core_verified}/{core_total}개 검증됨")
    weak = [c for c in claims if c.verification_status in ("weak_evidence", "unsupported", "contradicted")]
    if weak and not _generous_mode():
        negatives.append(f"근거가 부족하거나 미검증인 Claim {len(weak)}개 존재")
    elif weak and _generous_mode():
        positives.append("AI 모델 간 핵심 의미 일치로 개념 설명 신뢰도를 보정했습니다.")
    return _weighted_average(pairs), positives, negatives


def calculate_source_quality(claims: list[ClaimScoreInput]) -> tuple[float, list[str], list[str]]:
    pairs = []
    positives: list[str] = []
    negatives: list[str] = []
    official_backed = 0
    generous = _generous_mode()
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
            consensus = claim.consensus_score or 0.0
            if generous and consensus >= 88:
                fallback = 78.0
            elif consensus >= 85:
                fallback = 70.0
            else:
                fallback = 50.0
            pairs.append((fallback, weight))
    if official_backed:
        positives.append(f"공식·학술 출처로 뒷받침된 Claim {official_backed}개")
    low_quality = [c for c in claims if c.evidence_source_quality and sum(c.evidence_source_quality) / len(c.evidence_source_quality) < 60]
    if low_quality and not generous:
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
    if logic_issue_count <= 0:
        return 100.0, ["핵심 의미가 일치하고 실제 논리적 자기모순이 없습니다."], []
    per_issue = 6.0 if _generous_mode() else 8.0
    score = max(0.0, 100.0 - (logic_issue_count * per_issue))
    negatives = [f"실제 논리 오류 {logic_issue_count}건 발견"]
    return score, [], negatives


def calculate_freshness(question_type: str, outdated_risk_count: int) -> tuple[float, list[str], list[str]]:
    if outdated_risk_count:
        penalty = 12.0 if _generous_mode() else 20.0
        score = max(0.0, 90.0 - outdated_risk_count * penalty)
        return score, [], [f"최신성 문제 {outdated_risk_count}건 발견"]
    if question_type == "current_information":
        return 90.0, ["최신 정보 확인 완료"], []
    return 100.0, ["시점에 민감하지 않은 질문"], []


def _apply_generous_total_adjustment(
    total_score: float,
    consensus: float,
    logic: float,
    contradiction_penalty: float,
    answer_purpose: str,
) -> float:
    if not _generous_mode():
        return total_score
    adjusted = total_score
    if consensus >= 88 and logic >= 95 and contradiction_penalty <= 0:
        adjusted += 8.0
    if answer_purpose in ("concept_understanding", "fact_check") and consensus >= 90 and logic >= 95:
        adjusted = max(adjusted, 86.0)
    if consensus >= 92 and logic == 100.0 and contradiction_penalty <= 0:
        adjusted = max(adjusted, 88.0)
    return min(100.0, adjusted)


def calculate_trust_score(
    claims: list[ClaimScoreInput],
    contradiction_penalty: float,
    risk_penalty: float,
    logic_issue_count: int,
    outdated_risk_count: int,
    question_type: str,
    verification_basis: str,
    answer_purpose: str = "concept_understanding",
) -> dict:
    evidence_support, es_pos, es_neg = calculate_evidence_support(claims)
    source_quality, sq_pos, sq_neg = calculate_source_quality(claims)
    consensus, co_pos, co_neg = calculate_consensus(claims)
    logic, lo_pos, lo_neg = calculate_logic(logic_issue_count)
    freshness, fr_pos, fr_neg = calculate_freshness(question_type, outdated_risk_count)

    w_evidence, w_source, w_consensus, w_logic, w_freshness = _score_weights()
    base_score = (
        w_evidence * evidence_support
        + w_source * source_quality
        + w_consensus * consensus
        + w_logic * logic
        + w_freshness * freshness
    )
    total_score = max(0.0, min(100.0, base_score - contradiction_penalty - risk_penalty))
    total_score = _apply_generous_total_adjustment(
        total_score, consensus, logic, contradiction_penalty, answer_purpose
    )

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
        "formula": (
            f"{w_evidence}×Evidence Support + {w_source}×Source Quality + "
            f"{w_consensus}×Consensus + {w_logic}×Logic + {w_freshness}×Freshness - Penalties"
        ),
        "weighted_scores": {
            "evidence_support": round(w_evidence * evidence_support, 2),
            "source_quality": round(w_source * source_quality, 2),
            "consensus": round(w_consensus * consensus, 2),
            "logic": round(w_logic * logic, 2),
            "freshness": round(w_freshness * freshness, 2),
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
        "generous_mode": _generous_mode(),
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

    pairs = []
    for claim in claims_from_model:
        if claim.deterministic_verified:
            score = 100.0
        else:
            score = _status_score(claim.verification_status)
            score = _consensus_adjusted_evidence_score(claim, score)
        pairs.append((score, _claim_weight(claim.importance)))

    score = _weighted_average(pairs)
    avg_consensus = mean(c.consensus_score or 70.0 for c in claims_from_model)
    contradicted = _count_status(claims_from_model, "contradicted")
    unsupported_core = len(
        [c for c in claims_from_model if c.importance == "core" and c.verification_status == "unsupported"]
    )

    if _generous_mode() and not contradicted:
        score = max(score, min(90.0, avg_consensus * 0.92))
        if avg_consensus >= 90:
            score = max(score, 82.0)

    if contradicted:
        reason = f"핵심 주장 중 {contradicted}건이 근거와 모순되어 감점되었습니다."
    elif unsupported_core and not _generous_mode():
        reason = f"핵심 주장 중 {unsupported_core}건이 근거로 뒷받침되지 않았습니다."
    elif unsupported_core and _generous_mode():
        reason = "핵심 의미는 다른 모델과 일치하나, 일부 주장의 외부 근거가 제한적입니다."
    else:
        reason = "핵심 Claim이 대부분 검증되었습니다."

    return round(score, 2), grade_for_score(score), reason


def _count_status(claims: list[ClaimScoreInput], status: str) -> int:
    return len([c for c in claims if c.verification_status == status])
