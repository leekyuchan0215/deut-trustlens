"""Builds mock (but structurally real) analysis artifacts for USE_MOCK=true.

Every object created here is persisted with the same shape Real Mode will
use later; only the content is templated and clearly labelled `[MOCK]`.
"""
import hashlib
import random
from datetime import datetime, timedelta, timezone

from app.models import (
    AIResponse,
    Claim,
    DeterministicCheck,
    DocumentChunk,
    DocumentEmbedding,
    Evidence,
    Question,
    Risk,
    SearchDocument,
)

MOCK_PROVIDERS = [
    ("gpt", "mock-gpt-4o"),
    ("claude", "mock-claude-sonnet"),
    ("gemini", "mock-gemini-pro"),
]

EMBEDDING_DIMENSION = 1536

_SOURCE_TYPES_BY_QUALITY = [
    ("official", 95.0),
    ("government", 93.0),
    ("academic", 90.0),
    ("paper", 88.0),
    ("documentation", 82.0),
    ("news", 65.0),
    ("blog", 45.0),
    ("community", 35.0),
]

_CLAIM_TYPE_BY_QUESTION_TYPE = {
    "calculation": ["calculation", "numeric", "fact", "definition"],
    "comparison": ["comparison", "fact", "cause_effect", "recommendation"],
    "current_information": ["latest_info", "fact", "numeric", "fact"],
    "simple_fact": ["fact", "definition", "fact", "definition"],
    "recommendation": ["recommendation", "fact", "comparison", "opinion"],
    "opinion": ["opinion", "fact", "opinion", "fact"],
    "medical": ["fact", "cause_effect", "definition", "fact"],
    "legal": ["fact", "definition", "cause_effect", "fact"],
    "general": ["fact", "definition", "fact", "comparison"],
}


def _seeded_random(*parts: str) -> random.Random:
    seed = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return random.Random(seed)


def build_ai_responses(question: Question) -> list[AIResponse]:
    responses = []
    rng = _seeded_random(str(question.id), "ai_responses")
    for provider, model_name in MOCK_PROVIDERS:
        text = (
            f"[MOCK] {model_name}의 답변입니다. '{question.selected_question}' 질문에 대해 "
            f"핵심 사실을 중심으로 정리하면 다음과 같습니다. 이 답변은 실제 {provider.upper()} 호출 없이 "
            "생성된 목업 데이터입니다."
        )
        responses.append(
            AIResponse(
                question_id=question.id,
                provider=provider,
                model_name=model_name,
                status="success",
                response_text=text,
                latency_ms=rng.randint(600, 2200),
                input_tokens=rng.randint(120, 400),
                output_tokens=rng.randint(300, 900),
                total_tokens=0,
                estimated_cost=round(rng.uniform(0.001, 0.02), 6),
            )
        )
    for response in responses:
        response.total_tokens = (response.input_tokens or 0) + (response.output_tokens or 0)
    return responses


def build_claims(question: Question) -> list[Claim]:
    claim_types = _CLAIM_TYPE_BY_QUESTION_TYPE.get(
        question.question_type or "general", _CLAIM_TYPE_BY_QUESTION_TYPE["general"]
    )
    rng = _seeded_random(str(question.id), "claims")
    all_providers = [p for p, _ in MOCK_PROVIDERS]

    definitions = [
        ("core", True),
        ("core", True),
        ("supporting", False),
        ("supporting", False),
    ]

    claims: list[Claim] = []
    for idx, (importance, full_consensus) in enumerate(definitions, start=1):
        display_id = f"C{idx}"
        claim_type = claim_types[(idx - 1) % len(claim_types)]

        if idx == 1 and question.question_type == "calculation":
            verification_basis = "deterministic"
        elif question.verification_basis == "mixed":
            verification_basis = "authoritative_fact" if idx % 2 == 1 else "web_evidence"
        else:
            verification_basis = question.verification_basis or "web_evidence"

        if full_consensus:
            source_models = all_providers
            consensus_score = rng.uniform(92, 100)
            consensus_level = "high"
        else:
            source_models = all_providers[: rng.randint(2, 3)]
            consensus_score = rng.uniform(65, 85) if len(source_models) == 2 else rng.uniform(85, 95)
            consensus_level = "medium" if len(source_models) == 2 else "high"

        claim_text = (
            f"[MOCK] {question.selected_question}와 관련된 {'핵심' if importance == 'core' else '부가'} "
            f"주장 {display_id}입니다."
        )

        claims.append(
            Claim(
                question_id=question.id,
                display_id=display_id,
                claim_text=claim_text,
                normalized_claim=claim_text,
                claim_type=claim_type,
                importance=importance,
                verification_basis=verification_basis,
                source_models=source_models,
                consensus_score=round(consensus_score, 2),
                consensus_level=consensus_level,
                verification_status="pending",
            )
        )
    return claims


def build_deterministic_checks(claims: list[Claim]) -> list[DeterministicCheck]:
    checks = []
    for claim in claims:
        if claim.verification_basis != "deterministic":
            continue
        input_expression = "25 * 4"
        expected_result = str(eval(input_expression, {"__builtins__": {}}))  # noqa: S307 - fixed safe literal
        checks.append(
            DeterministicCheck(
                claim_id=claim.id,
                question_id=claim.question_id,
                check_type="calculator",
                input_expression=input_expression,
                expected_result=expected_result,
                ai_claimed_result=expected_result,
                check_passed=True,
                verification_status="verified",
                verification_confidence=100.0,
                verification_reason="독립 계산 결과와 AI 응답이 일치합니다. (Mock 계산 검증)",
                execution_detail={"engine": "mock_calculator", "expression": input_expression},
                limitations=[],
            )
        )
    return checks


def build_search_documents(question: Question, count: int = 6) -> list[SearchDocument]:
    if question.verification_basis == "deterministic":
        count = 2
    rng = _seeded_random(str(question.id), "documents")
    documents = []
    now = datetime.now(timezone.utc)
    for i in range(count):
        source_type, quality = rng.choice(_SOURCE_TYPES_BY_QUALITY)
        url = f"https://mock-source-{i + 1}.example.com/{question.id}"
        title = f"[MOCK] {question.selected_question} 관련 참고 문서 {i + 1}"
        content = (
            f"[MOCK] 이 문서는 '{question.selected_question}' 검증을 위해 생성된 목업 검색 결과입니다. "
            f"문서 유형은 {source_type}이며 실제 Tavily 호출 없이 생성되었습니다."
        )
        documents.append(
            SearchDocument(
                question_id=question.id,
                title=title,
                url=url,
                domain=f"mock-source-{i + 1}.example.com",
                content=content,
                summary=content[:80],
                source_name=f"Mock Source {i + 1}",
                source_type=source_type,
                published_at=now - timedelta(days=rng.randint(1, 400)),
                searched_at=now,
                search_query=question.selected_question[:200],
                content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
            )
        )
    return documents


def _mock_embedding_vector(seed_text: str) -> list[float]:
    rng = _seeded_random(seed_text, "embedding")
    raw = [rng.uniform(-1.0, 1.0) for _ in range(EMBEDDING_DIMENSION)]
    norm = sum(v * v for v in raw) ** 0.5 or 1.0
    return [v / norm for v in raw]


def build_chunks(documents: list[SearchDocument]) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for document in documents:
        content = document.content or ""
        chunks.append(
            DocumentChunk(
                document_id=document.id,
                chunk_index=0,
                content=content,
                token_count=max(1, len(content) // 4),
                chunk_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
            )
        )
    return chunks


def build_embeddings(
    chunks: list[DocumentChunk], documents: list[SearchDocument]
) -> list[DocumentEmbedding]:
    embeddings: list[DocumentEmbedding] = []
    for chunk, document in zip(chunks, documents):
        embeddings.append(
            DocumentEmbedding(
                chunk_id=chunk.id,
                embedding_provider="mock",
                embedding_model="mock-embedding-1536",
                dimension=EMBEDDING_DIMENSION,
                embedding=_mock_embedding_vector(document.url),
                is_mock=True,
            )
        )
    return embeddings


def build_evidences_and_verify_claims(
    claims: list[Claim],
    documents: list[SearchDocument],
    chunks: list[DocumentChunk],
    deterministic_checks: list[DeterministicCheck],
) -> list[Evidence]:
    evidences: list[Evidence] = []
    checks_by_claim = {c.claim_id: c for c in deterministic_checks}
    doc_by_id = {d.id: d for d in documents}
    rng_base = _seeded_random(str(claims[0].question_id) if claims else "none", "evidence")

    non_deterministic_chunks = list(zip(chunks, documents))

    for idx, claim in enumerate(claims):
        det_check = checks_by_claim.get(claim.id)
        if det_check is not None:
            evidences.append(
                Evidence(
                    question_id=claim.question_id,
                    claim_id=claim.id,
                    deterministic_check_id=det_check.id,
                    title="결정적 계산 검증",
                    url=None,
                    domain=None,
                    snippet=det_check.verification_reason,
                    source_name="Deterministic Verifier",
                    source_type="deterministic_verifier",
                    relation="support",
                    source_quality_score=100.0,
                    directness_score=100.0,
                    support_score=100.0,
                    rank=1,
                    selection_reason="결정적 계산 결과가 AI 주장과 일치합니다.",
                )
            )
            claim.verification_status = "verified"
            claim.verification_confidence = 100.0
            claim.verification_reason = "결정적 계산 검증을 통과했습니다."
            claim.verification_mode = "deterministic"
            claim.direct_evidence_strength = 100.0
            claim.cross_source_agreement = 100.0
            claim.positive_factors = ["결정적 계산 검증 통과"]
            claim.deductions = []
            claim.limitations = []
            continue

        if not non_deterministic_chunks:
            claim.verification_status = "unsupported"
            claim.verification_confidence = 30.0
            claim.verification_reason = "검증에 사용할 근거 문서를 찾지 못했습니다."
            claim.verification_mode = "hybrid_search"
            claim.direct_evidence_strength = 0.0
            claim.cross_source_agreement = 0.0
            claim.positive_factors = []
            claim.deductions = ["채택 가능한 Evidence 없음"]
            claim.limitations = ["웹 검색 결과 부족"]
            continue

        rng = _seeded_random(str(claim.id), "evidence")
        pick_count = min(len(non_deterministic_chunks), rng.randint(1, 3))
        picks = rng.sample(non_deterministic_chunks, pick_count)

        claim_evidences = []
        for rank, (chunk, document) in enumerate(picks, start=1):
            quality = next(
                (q for st, q in _SOURCE_TYPES_BY_QUALITY if st == document.source_type), 50.0
            )
            keyword_score = round(rng.uniform(0.55, 0.95), 5)
            vector_score = round(rng.uniform(0.55, 0.95), 5)
            hybrid_score = round(0.6 * keyword_score + 0.4 * vector_score, 5)
            directness = round(min(100.0, quality * rng.uniform(0.9, 1.05)), 2)
            support = round(min(100.0, directness * rng.uniform(0.9, 1.0)), 2)
            evidence = Evidence(
                question_id=claim.question_id,
                claim_id=claim.id,
                document_id=document.id,
                chunk_id=chunk.id,
                title=document.title,
                url=document.url,
                domain=document.domain,
                snippet=(document.content or "")[:200],
                source_name=document.source_name,
                source_type=document.source_type,
                published_at=document.published_at,
                searched_at=document.searched_at,
                relation="support",
                keyword_score=keyword_score,
                vector_score=vector_score,
                hybrid_score=hybrid_score,
                source_quality_score=round(quality, 2),
                directness_score=directness,
                support_score=support,
                rank=rank,
                selection_reason="Hybrid Search 상위 순위로 채택되었습니다. (Mock)",
            )
            evidences.append(evidence)
            claim_evidences.append(evidence)

        avg_hybrid = sum(e.hybrid_score for e in claim_evidences) / len(claim_evidences)
        avg_support = sum(e.support_score for e in claim_evidences) / len(claim_evidences)
        avg_quality = sum(e.source_quality_score for e in claim_evidences) / len(claim_evidences)

        if avg_hybrid >= 0.75 and avg_support >= 70:
            claim.verification_status = "verified"
            claim.verification_confidence = round(min(99.0, avg_support), 2)
        elif avg_hybrid >= 0.55:
            claim.verification_status = "weak_evidence"
            claim.verification_confidence = round(avg_support * 0.7, 2)
        else:
            claim.verification_status = "unsupported"
            claim.verification_confidence = round(avg_support * 0.4, 2)

        claim.verification_reason = (
            f"채택된 Evidence {len(claim_evidences)}건의 평균 Hybrid Score는 {avg_hybrid:.2f}입니다."
        )
        claim.verification_mode = "hybrid_search"
        claim.direct_evidence_strength = round(avg_support, 2)
        claim.cross_source_agreement = round(avg_quality, 2)
        claim.positive_factors = (
            ["채택된 Evidence가 Claim을 직접 지지함"] if claim.verification_status == "verified" else []
        )
        claim.deductions = (
            [] if claim.verification_status == "verified" else ["근거의 직접성 또는 출처 품질이 제한적임"]
        )
        claim.limitations = [] if claim.verification_status == "verified" else ["추가 출처 확인 권장"]

    return evidences


def build_risks(question: Question, claims: list[Claim], evidences: list[Evidence]) -> list[Risk]:
    risks: list[Risk] = []

    low_quality_claims = [
        c
        for c in claims
        if any(
            e.claim_id == c.id and e.source_type in ("blog", "community")
            for e in evidences
        )
    ]
    if low_quality_claims:
        risks.append(
            Risk(
                question_id=question.id,
                claim_id=low_quality_claims[0].id,
                risk_key="source_credibility_low_quality",
                risk_type="source_credibility",
                risk_level="low",
                description="일부 Supporting Claim이 블로그·커뮤니티 출처에 의존합니다. (Mock)",
                affects_core_answer=False,
                resolved_by_evidence=True,
                penalty=0.0,
                detected_by="mock_rule",
            )
        )

    if question.question_type == "current_information":
        risks.append(
            Risk(
                question_id=question.id,
                claim_id=None,
                risk_key="outdated_information_current_topic",
                risk_level="medium",
                risk_type="outdated_information",
                description="현재 시점 정보는 이후 변경될 수 있습니다. (Mock)",
                affects_core_answer=True,
                resolved_by_evidence=False,
                penalty=5.0,
                detected_by="mock_rule",
            )
        )

    contradicted = [c for c in claims if c.verification_status == "contradicted"]
    for c in contradicted:
        risks.append(
            Risk(
                question_id=question.id,
                claim_id=c.id,
                risk_key=f"contradiction_{c.display_id}",
                risk_type="contradiction",
                risk_level="high",
                description=f"{c.display_id}이(가) 채택된 근거와 모순됩니다. (Mock)",
                affects_core_answer=c.importance == "core",
                resolved_by_evidence=False,
                penalty=15.0 if c.importance == "core" else 5.0,
                detected_by="mock_rule",
            )
        )

    return risks


def build_cross_review(claims: list[Claim]) -> dict:
    semantic_consensus = []
    for claim in claims:
        if claim.importance != "core":
            continue
        semantic_consensus.append(
            {
                "claim_id": str(claim.id),
                "meaning": claim.normalized_claim,
                "agreeing_models": claim.source_models,
                "consensus_level": claim.consensus_level or "medium",
            }
        )

    model_additions = {provider: [] for provider, _ in MOCK_PROVIDERS}
    for claim in claims:
        missing = [p for p, _ in MOCK_PROVIDERS if p not in claim.source_models]
        for provider, _ in MOCK_PROVIDERS:
            if provider in claim.source_models and provider not in missing:
                continue
        if len(claim.source_models) < len(MOCK_PROVIDERS):
            extra_model = claim.source_models[0] if claim.source_models else None
            if extra_model:
                model_additions[extra_model].append(
                    f"{claim.display_id}에 대한 보충 설명을 추가했습니다."
                )

    missing_points = []
    for claim in claims:
        missing_models = [p for p, _ in MOCK_PROVIDERS if p not in claim.source_models]
        if missing_models:
            missing_points.append(
                {
                    "description": f"{', '.join(missing_models)}는 {claim.display_id}를 언급하지 않았습니다 (모순 아님).",
                    "affects_core_answer": False,
                }
            )

    return {
        "semantic_consensus": semantic_consensus,
        "consensus": ["모델 간 핵심 의미가 대체로 일치합니다. (Mock)"],
        "contradictions": [],
        "model_additions": model_additions,
        "missing_points": missing_points,
        "overclaims": [],
        "logic_issues": [],
        "model_strengths": {provider: [] for provider, _ in MOCK_PROVIDERS},
        "model_weaknesses": {provider: [] for provider, _ in MOCK_PROVIDERS},
        "cross_review_mode": "mock",
    }
