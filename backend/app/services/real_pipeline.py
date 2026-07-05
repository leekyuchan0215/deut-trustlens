"""Real-mode (USE_MOCK=false) analysis pipeline. Mirrors the stage-by-stage
progress reporting of app/services/mock_pipeline.py but every artifact is
produced by real provider calls, Tavily search, OpenAI embeddings and
Postgres hybrid search instead of templated mock data.

Every LLM step follows docs/PROMPTS.md #19: parse -> validate -> repair once
-> explicit fallback (never a silently-faked mock success, per CLAUDE.md #8).
"""
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from statistics import mean

from sqlalchemy.orm import Session

from app.agents import answer_agent, claim_agent, cross_review_agent, final_answer_agent, reflection_agent, risk_agent
from app.agents import verification_agent
from app.agents.question_agent import analyze_question
from app.agents.schemas import FinalAnswerOutput
from app.db.session import SessionLocal
from app.models import (
    AIResponse,
    Claim,
    DeterministicCheck,
    DocumentChunk,
    DocumentEmbedding,
    Evidence,
    FinalResult,
    Question,
    Risk,
    SearchDocument,
    TrustScore,
)
from app.services import deterministic_verification as detcheck
from app.services import hybrid_search
from app.services import tavily_service
from app.services.chunking import chunk_text
from app.services.embedding_service import EmbeddingService
from app.services.llm.base import LLMClient, ProviderError
from app.services.llm.router import get_judge_client
from app.services.pipeline_common import advance_stage as _advance
from app.services.pipeline_common import mark_failed as _mark_failed
from app.services.trust_score_calculator import ClaimScoreInput, calculate_model_score, calculate_trust_score
from app.utils.enums import PIPELINE_STEPS
from app.utils.source_quality import quality_for_source_type

logger = logging.getLogger("trustlens.real_pipeline")

CORE_CONSENSUS_BY_PROVIDER_COUNT = {3: 100.0, 2: 85.0, 1: 40.0}
MAX_PARALLEL_CLAIM_WORKERS = 5


def _parallel_for_each(items: list, fn) -> None:
    """Run fn(item) for each item concurrently (pure-LLM calls only — no
    shared DB session may be touched inside fn)."""
    if not items:
        return
    with ThreadPoolExecutor(max_workers=min(MAX_PARALLEL_CLAIM_WORKERS, len(items))) as pool:
        list(pool.map(fn, items))


def run_pipeline(question_id: str) -> None:
    db = SessionLocal()
    try:
        _run(db, question_id)
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("real pipeline failed for question_id=%s", question_id)
        db.rollback()
        _mark_failed(db, question_id, "REAL_PIPELINE_ERROR", "실제 분석 처리 중 예상치 못한 오류가 발생했습니다.")
    finally:
        db.close()


class ClaimContext:
    def __init__(self, claim: Claim):
        self.claim = claim
        self.requires_web_search = False
        self.requires_deterministic_check = False
        self.deterministic_result: detcheck.DeterministicResult | None = None
        self.evidences: list[Evidence] = []
        self.verification_mode: str = "pending"


def _run(db: Session, question_id: str) -> None:
    question = db.get(Question, question_id)
    if question is None:
        return

    try:
        judge_client, judge_resolution = get_judge_client()
    except ProviderError as exc:
        _mark_failed(db, question_id, "NO_JUDGE_PROVIDER_AVAILABLE", f"사용 가능한 AI Provider가 없습니다: {exc.message}")
        return

    question.status = "processing"
    question.started_at = datetime.now(timezone.utc)
    db.add(question)
    db.commit()

    fallback_notes: list[str] = []
    judge_attempts = 0

    ai_responses: list[AIResponse] = []
    claims: list[Claim] = []
    claim_ctx_by_id: dict[uuid.UUID, ClaimContext] = {}
    deterministic_checks: list[DeterministicCheck] = []
    documents: list[SearchDocument] = []
    all_evidences: list[Evidence] = []
    risks: list[Risk] = []
    cross_review: dict = {}
    cross_review_mode = "llm_judge"

    for stage, display_stage, percent in PIPELINE_STEPS:
        started = time.monotonic()

        if stage == "ai_generation":
            ai_responses = _run_ai_generation(db, question)
            if not any(r.status == "success" for r in ai_responses):
                _mark_failed(
                    db, question_id, "ALL_PROVIDERS_FAILED",
                    "GPT, Claude, Gemini 모두 응답에 실패하여 분석을 진행할 수 없습니다.",
                )
                return

        elif stage == "claim_extraction":
            claims_by_provider = _run_claim_extraction(judge_client, question, ai_responses, fallback_notes)

        elif stage == "claim_consolidation":
            claims = _run_claim_consolidation(db, judge_client, question, claims_by_provider, fallback_notes)
            claim_ctx_by_id = {c.id: ClaimContext(c) for c in claims}
            if not claims:
                _mark_failed(
                    db, question_id, "NO_CLAIMS_EXTRACTED",
                    "AI 답변에서 검증 가능한 Claim을 추출하지 못했습니다.",
                )
                return

        elif stage == "verification_strategy":
            _run_verification_strategy(judge_client, claim_ctx_by_id, fallback_notes)

        elif stage == "deterministic_verification":
            deterministic_checks = _run_deterministic_verification(db, judge_client, claim_ctx_by_id, fallback_notes)

        elif stage == "search_query_generation":
            _run_search_query_generation(judge_client, claim_ctx_by_id, question, fallback_notes)

        elif stage == "evidence_search" or stage == "document_storage":
            if stage == "evidence_search":
                documents = _run_evidence_search(db, question, claim_ctx_by_id, fallback_notes)

        elif stage == "chunking":
            _run_chunking(db, documents)

        elif stage == "embedding":
            _run_embedding(db, documents, fallback_notes)

        elif stage == "hybrid_search" or stage == "evidence_selection":
            if stage == "evidence_selection":
                all_evidences = _run_evidence_selection(db, judge_client, claim_ctx_by_id, question, fallback_notes)

        elif stage == "claim_verification":
            _run_claim_verification(judge_client, claim_ctx_by_id, fallback_notes)

        elif stage == "cross_review":
            cross_review, cross_review_mode = _run_cross_review(judge_client, question, ai_responses, claims, fallback_notes)

        elif stage == "risk_analysis":
            risks = _run_risk_analysis(db, judge_client, question, claims, all_evidences, cross_review, fallback_notes)

        elif stage == "final_answer" or stage == "reflection":
            if stage == "final_answer":
                final_answer_output, final_answer_mode, judge_attempts = _run_final_answer_and_reflection(
                    judge_client, question, claims, deterministic_checks, all_evidences, cross_review, risks, fallback_notes
                )

        elif stage == "result_storage":
            _finalize(
                db, question, judge_client, judge_resolution, ai_responses, claims, deterministic_checks,
                documents, all_evidences, risks, cross_review, cross_review_mode,
                final_answer_output, final_answer_mode, judge_attempts, fallback_notes,
            )

        duration_ms = round((time.monotonic() - started) * 1000)
        _advance(db, question, stage, display_stage, percent, duration_ms)

    question.status = "completed"
    question.completed_at = datetime.now(timezone.utc)
    db.add(question)
    db.commit()


def _run_ai_generation(db: Session, question: Question) -> list[AIResponse]:
    results = answer_agent.generate_answers(
        question.selected_question, question.question_type or "general",
        question.verification_basis or "mixed", question.answer_purpose,
    )
    rows = []
    for r in results:
        row = AIResponse(
            question_id=question.id,
            provider=r.provider,
            model_name=r.model_name,
            status=r.status,
            response_text=r.response_text,
            latency_ms=r.latency_ms,
            input_tokens=r.input_tokens,
            output_tokens=r.output_tokens,
            total_tokens=r.total_tokens,
            estimated_cost=r.estimated_cost,
            error_code=r.error_code,
            error_message=r.error_message,
        )
        rows.append(row)
        if r.status != "success":
            logger.warning("provider_failed provider=%s error=%s", r.provider, r.error_message)
    db.add_all(rows)
    db.flush()
    return rows


def _run_claim_extraction(
    judge_client: LLMClient, question: Question, ai_responses: list[AIResponse], fallback_notes: list[str]
) -> dict[str, list]:
    claims_by_provider: dict[str, list] = {}
    successful = [r for r in ai_responses if r.status == "success" and r.response_text]

    def _extract(response: AIResponse) -> None:
        parsed, meta = claim_agent.extract_claims(judge_client, question.selected_question, response.provider, response.response_text)
        if parsed is None:
            fallback_notes.append(f"claim_extraction_failed:{response.provider}:{meta.get('error')}")
            claims_by_provider[response.provider] = []
            return
        claims_by_provider[response.provider] = parsed.claims

    _parallel_for_each(successful, _extract)
    return claims_by_provider


def _run_claim_consolidation(
    db: Session, judge_client: LLMClient, question: Question, claims_by_provider: dict[str, list], fallback_notes: list[str]
) -> list[Claim]:
    parsed, meta = claim_agent.consolidate_claims(judge_client, claims_by_provider)
    rows: list[Claim] = []

    if parsed is not None and parsed.claims:
        for idx, item in enumerate(parsed.claims, start=1):
            rows.append(
                Claim(
                    question_id=question.id,
                    display_id=f"C{idx}",
                    claim_text=item.claim_text,
                    normalized_claim=item.normalized_claim,
                    claim_type=item.claim_type,
                    importance=item.importance,
                    verification_basis=item.verification_basis,
                    source_models=item.source_models or [],
                    verification_status="pending",
                )
            )
    else:
        fallback_notes.append(f"claim_consolidation_failed:{meta.get('error')}")
        idx = 0
        seen_texts: set[str] = set()
        for provider, extracted in claims_by_provider.items():
            for item in extracted:
                key = item.normalized_claim.strip().lower()
                if key in seen_texts:
                    continue
                seen_texts.add(key)
                idx += 1
                rows.append(
                    Claim(
                        question_id=question.id,
                        display_id=f"C{idx}",
                        claim_text=item.claim_text,
                        normalized_claim=item.normalized_claim,
                        claim_type=item.claim_type,
                        importance=item.importance,
                        verification_basis=item.verification_basis,
                        source_models=[provider],
                        verification_status="pending",
                    )
                )
                if idx >= 12:
                    break
            if idx >= 12:
                break

    db.add_all(rows)
    db.flush()

    provider_count = len([p for p in claims_by_provider if claims_by_provider[p]])
    consensus_ceiling = CORE_CONSENSUS_BY_PROVIDER_COUNT.get(min(3, max(1, provider_count)), 40.0)
    for row in rows:
        agree_count = len(row.source_models) if row.source_models else 1
        base = 100.0 if agree_count >= max(1, provider_count) else 60.0 + 20.0 * agree_count
        row.consensus_score = round(min(consensus_ceiling, base), 2)
        row.consensus_level = "high" if row.consensus_score >= 85 else ("medium" if row.consensus_score >= 60 else "low")
    db.flush()
    return rows


def _run_verification_strategy(judge_client: LLMClient, claim_ctx_by_id: dict, fallback_notes: list[str]) -> None:
    def _classify(ctx: ClaimContext) -> None:
        parsed, meta = verification_agent.classify_verification_basis(judge_client, ctx.claim.claim_text)
        if parsed is not None:
            ctx.claim.verification_basis = parsed.verification_basis
            ctx.requires_web_search = parsed.requires_web_search
            ctx.requires_deterministic_check = parsed.requires_deterministic_check
        else:
            fallback_notes.append(f"verification_strategy_failed:{ctx.claim.display_id}")
            ctx.requires_deterministic_check = ctx.claim.verification_basis == "deterministic"
            ctx.requires_web_search = ctx.claim.verification_basis in ("authoritative_fact", "web_evidence", "mixed")

    _parallel_for_each(list(claim_ctx_by_id.values()), _classify)


def _run_deterministic_verification(
    db: Session, judge_client: LLMClient, claim_ctx_by_id: dict, fallback_notes: list[str]
) -> list[DeterministicCheck]:
    target_ctxs = [
        ctx for ctx in claim_ctx_by_id.values()
        if ctx.requires_deterministic_check or ctx.claim.verification_basis == "deterministic"
    ]
    extraction_by_claim_id: dict = {}

    def _extract(ctx: ClaimContext) -> None:
        parsed, _meta = verification_agent.extract_deterministic(judge_client, ctx.claim.claim_text)
        extraction_by_claim_id[ctx.claim.id] = parsed

    _parallel_for_each(target_ctxs, _extract)

    rows: list[DeterministicCheck] = []
    for ctx in target_ctxs:
        parsed = extraction_by_claim_id.get(ctx.claim.id)
        if parsed is None:
            fallback_notes.append(f"deterministic_extraction_failed:{ctx.claim.display_id}")
            ctx.claim.verification_status = "weak_evidence"
            ctx.claim.verification_confidence = 40.0
            ctx.claim.verification_reason = "결정적 검증 입력을 추출하지 못했습니다."
            ctx.claim.verification_mode = "score_fallback"
            ctx.claim.limitations = ["결정적 검증 입력 추출 실패"]
            ctx.verification_mode = "resolved"
            continue

        result = detcheck.run_check(
            check_type=parsed.check_type,
            input_expression=parsed.input_expression,
            ai_claimed_result=parsed.ai_claimed_result,
            variables=parsed.variables,
            from_unit=parsed.from_unit,
            to_unit=parsed.to_unit,
            value=parsed.value,
            from_base=parsed.from_base,
            to_base=parsed.to_base,
        )
        ctx.deterministic_result = result
        ctx.verification_mode = "resolved"

        check_row = DeterministicCheck(
            question_id=ctx.claim.question_id,
            claim_id=ctx.claim.id,
            check_type=result.check_type,
            input_expression=result.input_expression,
            expected_result=result.expected_result,
            ai_claimed_result=result.ai_claimed_result,
            check_passed=result.check_passed,
            verification_status=result.verification_status,
            verification_confidence=result.verification_confidence,
            verification_reason=result.verification_reason,
            execution_detail=result.execution_detail,
            limitations=result.limitations,
        )
        rows.append(check_row)

        ctx.claim.verification_status = result.verification_status
        ctx.claim.verification_confidence = result.verification_confidence
        ctx.claim.verification_reason = result.verification_reason
        ctx.claim.verification_mode = "deterministic"
        ctx.claim.direct_evidence_strength = 100.0 if result.check_passed else 0.0
        ctx.claim.cross_source_agreement = 100.0 if result.check_passed else 0.0
        ctx.claim.positive_factors = ["독립 계산/변환 결과와 AI 응답이 일치함"] if result.check_passed else []
        ctx.claim.deductions = [] if result.check_passed else ["독립 계산/변환 결과와 AI 응답이 불일치함"]
        ctx.claim.limitations = result.limitations

    db.add_all(rows)
    db.flush()

    evidence_rows = []
    for ctx in claim_ctx_by_id.values():
        check_row = next((r for r in rows if r.claim_id == ctx.claim.id), None)
        if check_row is None:
            continue
        evidence_rows.append(
            Evidence(
                question_id=ctx.claim.question_id,
                claim_id=ctx.claim.id,
                deterministic_check_id=check_row.id,
                title="결정적 계산/변환 검증",
                url=None,
                domain=None,
                snippet=check_row.verification_reason,
                source_name="Deterministic Verifier",
                source_type="deterministic_verifier",
                relation="support" if check_row.check_passed else "contradict",
                source_quality_score=100.0,
                directness_score=100.0,
                support_score=100.0 if check_row.check_passed else 0.0,
                rank=1,
                selection_reason="결정적 검증 결과가 Claim을 직접 뒷받침합니다.",
            )
        )
    db.add_all(evidence_rows)
    for ctx in claim_ctx_by_id.values():
        ctx.evidences.extend(e for e in evidence_rows if e.claim_id == ctx.claim.id)
    db.flush()
    return rows


def _run_search_query_generation(
    judge_client: LLMClient, claim_ctx_by_id: dict, question: Question, fallback_notes: list[str]
) -> None:
    target_ctxs = [
        ctx for ctx in claim_ctx_by_id.values()
        if ctx.verification_mode != "resolved"
        and (ctx.requires_web_search or ctx.claim.verification_basis in ("authoritative_fact", "web_evidence", "mixed"))
    ]

    def _generate(ctx: ClaimContext) -> None:
        parsed, meta = verification_agent.generate_search_queries(judge_client, ctx.claim.claim_text, ctx.claim.verification_basis)
        if parsed is not None:
            ctx.keyword_queries = parsed.keyword_queries or [ctx.claim.normalized_claim[:80]]
            ctx.semantic_queries = parsed.semantic_queries or [ctx.claim.normalized_claim]
            ctx.recency_required = parsed.recency_required
        else:
            fallback_notes.append(f"search_query_generation_failed:{ctx.claim.display_id}")
            ctx.keyword_queries = [ctx.claim.normalized_claim[:80]]
            ctx.semantic_queries = [ctx.claim.normalized_claim]
            ctx.recency_required = question.question_type == "current_information"
        ctx.requires_web_search = True

    _parallel_for_each(target_ctxs, _generate)


def _run_evidence_search(
    db: Session, question: Question, claim_ctx_by_id: dict, fallback_notes: list[str]
) -> list[SearchDocument]:
    all_queries: set[str] = set()
    any_recency = False
    for ctx in claim_ctx_by_id.values():
        if not getattr(ctx, "requires_web_search", False) or ctx.verification_mode == "resolved":
            continue
        all_queries.update(getattr(ctx, "keyword_queries", []))
        all_queries.update(getattr(ctx, "semantic_queries", []))
        any_recency = any_recency or getattr(ctx, "recency_required", False)

    if not all_queries:
        return []

    try:
        results = tavily_service.search_many(list(all_queries), recency_required=any_recency)
    except ProviderError as exc:
        fallback_notes.append(f"tavily_search_failed:{exc.message}")
        logger.warning("tavily_search_unavailable error=%s", exc)
        return []

    rows = []
    for result in results:
        rows.append(
            SearchDocument(
                question_id=question.id,
                title=result.title,
                url=result.url,
                domain=result.domain,
                content=result.content,
                summary=result.content[:300] if result.content else None,
                source_name=result.domain,
                source_type=result.source_type,
                published_at=result.published_at,
                searched_at=datetime.now(timezone.utc),
                search_query=result.search_query[:2000],
                content_hash=result.content_hash,
            )
        )
    db.add_all(rows)
    db.flush()
    return rows


def _run_chunking(db: Session, documents: list[SearchDocument]) -> None:
    for document in documents:
        for chunk in chunk_text(document.content or ""):
            db.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    token_count=chunk.token_count,
                    chunk_hash=chunk.chunk_hash,
                )
            )
    db.flush()


def _run_embedding(db: Session, documents: list[SearchDocument], fallback_notes: list[str]) -> None:
    if not documents:
        return
    document_ids = [d.id for d in documents]
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id.in_(document_ids)).all()
    if not chunks:
        return
    try:
        service = EmbeddingService()
        vectors = service.embed([c.content for c in chunks])
    except ProviderError as exc:
        fallback_notes.append(f"embedding_failed:{exc.message}")
        logger.warning("embedding_unavailable error=%s", exc)
        return

    rows = []
    for chunk, vector in zip(chunks, vectors):
        rows.append(
            DocumentEmbedding(
                chunk_id=chunk.id,
                embedding_provider="openai",
                embedding_model=service.model_name,
                dimension=len(vector),
                embedding=vector,
                is_mock=False,
            )
        )
    db.add_all(rows)
    db.flush()


def _run_evidence_selection(
    db: Session, judge_client: LLMClient, claim_ctx_by_id: dict, question: Question, fallback_notes: list[str]
) -> list[Evidence]:
    embedding_service = None
    try:
        embedding_service = EmbeddingService()
    except ProviderError:
        pass

    target_ctxs = [
        ctx for ctx in claim_ctx_by_id.values()
        if ctx.verification_mode != "resolved" and getattr(ctx, "requires_web_search", False)
    ]

    # Phase 1 (parallel): each worker opens its own short-lived read session
    # for hybrid_search — the shared `db` session is never touched off-thread.
    prepared: dict = {}

    def _prepare(ctx: ClaimContext) -> None:
        query_embeddings = []
        semantic_queries = getattr(ctx, "semantic_queries", [])
        if embedding_service is not None and semantic_queries:
            try:
                query_embeddings = embedding_service.embed(semantic_queries)
            except ProviderError:
                query_embeddings = []

        local_db = SessionLocal()
        try:
            candidates = hybrid_search.search(
                local_db, question.id, getattr(ctx, "keyword_queries", []), query_embeddings, top_k=5
            )
            resolved = [
                {
                    "document_id": c.document.id,
                    "chunk_id": c.chunk.id,
                    "title": c.document.title,
                    "url": c.document.url,
                    "domain": c.document.domain,
                    "snippet": (c.chunk.content or "")[:500],
                    "source_type": c.document.source_type,
                    "published_at": c.document.published_at,
                    "searched_at": c.document.searched_at,
                    "keyword_score": c.keyword_score,
                    "vector_score": c.vector_score,
                    "hybrid_score": c.hybrid_score,
                }
                for c in candidates
            ]
        finally:
            local_db.close()

        if not resolved:
            prepared[ctx.claim.id] = None
            return

        candidate_dicts = [
            {"evidence_id": str(r["chunk_id"]), "title": r["title"], "url": r["url"], "domain": r["domain"],
             "snippet": r["snippet"][:300], "source_type": r["source_type"], "keyword_score": r["keyword_score"],
             "vector_score": r["vector_score"], "hybrid_score": r["hybrid_score"]}
            for r in resolved
        ]
        parsed, meta = verification_agent.evaluate_evidence(judge_client, ctx.claim.claim_text, candidate_dicts)
        prepared[ctx.claim.id] = (resolved, parsed)

    _parallel_for_each(target_ctxs, _prepare)

    # Phase 2 (sequential, main thread): build ORM rows on the shared session.
    all_evidences: list[Evidence] = []
    for ctx in target_ctxs:
        outcome = prepared.get(ctx.claim.id)
        if outcome is None:
            continue
        resolved, parsed = outcome
        resolved_by_chunk_id = {str(r["chunk_id"]): r for r in resolved}

        rows: list[Evidence] = []
        if parsed is not None and parsed.selected_evidences:
            for rank, sel in enumerate(parsed.selected_evidences, start=1):
                r = resolved_by_chunk_id.get(sel.evidence_id)
                if r is None:
                    continue  # never persist an evidence_id the candidate list didn't offer
                rows.append(
                    Evidence(
                        question_id=question.id,
                        claim_id=ctx.claim.id,
                        document_id=r["document_id"],
                        chunk_id=r["chunk_id"],
                        title=r["title"],
                        url=r["url"],
                        domain=r["domain"],
                        snippet=r["snippet"],
                        source_name=r["domain"],
                        source_type=sel.source_type or r["source_type"],
                        published_at=r["published_at"],
                        searched_at=r["searched_at"],
                        relation=sel.relation,
                        keyword_score=r["keyword_score"],
                        vector_score=r["vector_score"],
                        hybrid_score=r["hybrid_score"],
                        source_quality_score=sel.source_quality_score,
                        directness_score=sel.directness_score,
                        support_score=sel.support_score,
                        rank=rank,
                        selection_reason=sel.selection_reason,
                    )
                )
        else:
            fallback_notes.append(f"evidence_evaluation_failed:{ctx.claim.display_id}")
            for rank, r in enumerate(resolved[:3], start=1):
                quality = quality_for_source_type(r["source_type"])
                support = round(min(100.0, quality * r["hybrid_score"]), 2)
                rows.append(
                    Evidence(
                        question_id=question.id,
                        claim_id=ctx.claim.id,
                        document_id=r["document_id"],
                        chunk_id=r["chunk_id"],
                        title=r["title"],
                        url=r["url"],
                        domain=r["domain"],
                        snippet=r["snippet"],
                        source_name=r["domain"],
                        source_type=r["source_type"],
                        published_at=r["published_at"],
                        searched_at=r["searched_at"],
                        relation="support",
                        keyword_score=r["keyword_score"],
                        vector_score=r["vector_score"],
                        hybrid_score=r["hybrid_score"],
                        source_quality_score=quality,
                        directness_score=round(quality * r["hybrid_score"], 2),
                        support_score=support,
                        rank=rank,
                        selection_reason="Hybrid Search 상위 순위 자동 채택 (score_fallback).",
                    )
                )

        db.add_all(rows)
        ctx.evidences.extend(rows)
        all_evidences.extend(rows)

    db.flush()
    return all_evidences


def _run_claim_verification(judge_client: LLMClient, claim_ctx_by_id: dict, fallback_notes: list[str]) -> None:
    target_ctxs = [ctx for ctx in claim_ctx_by_id.values() if ctx.verification_mode != "resolved"]

    def _verify(ctx: ClaimContext) -> None:
        evidence_dicts = [
            {
                "evidence_id": str(e.id),
                "title": e.title,
                "source_type": e.source_type,
                "relation": e.relation,
                "source_quality_score": float(e.source_quality_score),
                "directness_score": float(e.directness_score),
                "support_score": float(e.support_score),
            }
            for e in ctx.evidences
        ]

        parsed, meta = verification_agent.verify_claim(
            judge_client, ctx.claim.claim_text, ctx.claim.verification_basis, None, evidence_dicts
        )
        if parsed is not None:
            ctx.claim.verification_status = parsed.verification_status
            ctx.claim.verification_confidence = parsed.verification_confidence
            ctx.claim.verification_reason = parsed.verification_reason
            ctx.claim.verification_mode = "llm_judge"
            ctx.claim.direct_evidence_strength = parsed.direct_evidence_strength
            ctx.claim.cross_source_agreement = parsed.cross_source_agreement
            ctx.claim.positive_factors = parsed.positive_factors
            ctx.claim.deductions = parsed.deductions
            ctx.claim.limitations = parsed.limitations
            return

        fallback_notes.append(f"claim_verification_failed:{ctx.claim.display_id}")
        if not evidence_dicts:
            ctx.claim.verification_status = "unsupported"
            ctx.claim.verification_confidence = 20.0
            ctx.claim.verification_reason = "채택된 근거가 없어 검증하지 못했습니다."
            ctx.claim.direct_evidence_strength = 0.0
            ctx.claim.cross_source_agreement = 0.0
            ctx.claim.deductions = ["채택 가능한 Evidence 없음"]
        else:
            avg_support = mean(d["support_score"] for d in evidence_dicts)
            avg_quality = mean(d["source_quality_score"] for d in evidence_dicts)
            if avg_support >= 70:
                status, confidence = "verified", round(min(99.0, avg_support), 2)
            elif avg_support >= 50:
                status, confidence = "weak_evidence", round(avg_support * 0.8, 2)
            else:
                status, confidence = "unsupported", round(avg_support * 0.5, 2)
            ctx.claim.verification_status = status
            ctx.claim.verification_confidence = confidence
            ctx.claim.verification_reason = f"채택된 Evidence {len(evidence_dicts)}건의 평균 지지도({avg_support:.1f})를 기준으로 판정했습니다. (score_fallback)"
            ctx.claim.direct_evidence_strength = round(avg_support, 2)
            ctx.claim.cross_source_agreement = round(avg_quality, 2)
            ctx.claim.deductions = [] if status == "verified" else ["근거 평가에 score_fallback 적용됨"]
        ctx.claim.verification_mode = "score_fallback"
        ctx.claim.limitations = ["Claim Verification Judge 실패로 score_fallback 적용"]

    _parallel_for_each(target_ctxs, _verify)


def _claim_dict(claim: Claim) -> dict:
    return {
        "claim_id": str(claim.id),
        "display_id": claim.display_id,
        "claim_text": claim.claim_text,
        "importance": claim.importance,
        "verification_basis": claim.verification_basis,
        "source_models": claim.source_models,
        "verification_status": claim.verification_status,
    }


def _run_cross_review(
    judge_client: LLMClient, question: Question, ai_responses: list[AIResponse], claims: list[Claim], fallback_notes: list[str]
) -> tuple[dict, str]:
    response_by_provider = {r.provider: r.response_text for r in ai_responses if r.status == "success"}
    claim_dicts = [_claim_dict(c) for c in claims]
    verification_dicts = [
        {"claim_id": str(c.id), "verification_status": c.verification_status, "verification_confidence": float(c.verification_confidence or 0)}
        for c in claims
    ]

    parsed, meta = cross_review_agent.cross_review(
        judge_client, question.selected_question,
        response_by_provider.get("gpt"), response_by_provider.get("claude"), response_by_provider.get("gemini"),
        claim_dicts, verification_dicts,
    )
    if parsed is not None:
        review = parsed.model_dump()
        review["cross_review_mode"] = "llm_judge"
        return review, "llm_judge"

    fallback_notes.append(f"cross_review_failed:{meta.get('error')}")
    providers_present = set(response_by_provider)
    semantic_consensus = []
    missing_points = []
    for claim in claims:
        if claim.importance == "core":
            semantic_consensus.append(
                {
                    "claim_id": str(claim.id),
                    "meaning": claim.normalized_claim,
                    "agreeing_models": claim.source_models,
                    "consensus_level": claim.consensus_level or "medium",
                }
            )
        missing = [p for p in providers_present if p not in (claim.source_models or [])]
        if missing:
            missing_points.append({
                "description": f"{', '.join(missing)}는 {claim.display_id}를 언급하지 않았습니다 (모순 아님).",
                "affects_core_answer": False,
            })

    fallback_review = {
        "semantic_consensus": semantic_consensus,
        "consensus": ["모델 간 핵심 의미가 대체로 일치합니다. (rule_fallback)"],
        "contradictions": [],
        "model_additions": {p: [] for p in ("gpt", "claude", "gemini")},
        "missing_points": missing_points,
        "overclaims": [],
        "logic_issues": [],
        "model_strengths": {p: [] for p in ("gpt", "claude", "gemini")},
        "model_weaknesses": {p: [] for p in ("gpt", "claude", "gemini")},
        "cross_review_mode": "rule_fallback",
    }
    return fallback_review, "rule_fallback"


_RISK_PENALTY_BY_LEVEL = {"low": 0.0, "medium": 5.0, "high": 15.0}
_CONTRADICTION_PENALTY_BY_LEVEL = {"low": 3.0, "medium": 15.0, "high": 25.0}


def _run_risk_analysis(
    db: Session, judge_client: LLMClient, question: Question, claims: list[Claim],
    evidences: list[Evidence], cross_review: dict, fallback_notes: list[str],
) -> list[Risk]:
    claim_dicts = [_claim_dict(c) for c in claims]
    verification_dicts = [
        {"claim_id": str(c.id), "verification_status": c.verification_status} for c in claims
    ]
    evidence_dicts = [
        {"evidence_id": str(e.id), "claim_id": str(e.claim_id), "source_type": e.source_type, "relation": e.relation}
        for e in evidences
    ]

    parsed, meta = risk_agent.analyze_risks(judge_client, claim_dicts, verification_dicts, evidence_dicts, cross_review)

    known_claim_ids = {str(c.id) for c in claims}
    claims_by_id = {str(c.id): c for c in claims}
    risk_items: list[dict] = []
    if parsed is not None:
        for item in parsed.risks:
            risk_items.append(item.model_dump())
    else:
        fallback_notes.append(f"risk_analysis_failed:{meta.get('error')}")
        contradicted = [c for c in claims if c.verification_status == "contradicted"]
        for c in contradicted:
            risk_items.append({
                "risk_type": "contradiction", "risk_level": "high" if c.importance == "core" else "medium",
                "description": f"{c.display_id}이(가) 채택된 근거와 모순됩니다. (rule_fallback)",
                "affected_claim_ids": [str(c.id)], "affects_core_answer": c.importance == "core",
                "resolved_by_evidence": False,
            })
        low_quality = [e for e in evidences if e.source_type in ("blog", "community")]
        if low_quality:
            risk_items.append({
                "risk_type": "source_credibility", "risk_level": "low",
                "description": "일부 근거가 블로그·커뮤니티 출처에 의존합니다. (rule_fallback)",
                "affected_claim_ids": [], "affects_core_answer": False, "resolved_by_evidence": True,
            })
        if question.question_type == "current_information" and not any(e.source_type in ("official", "government", "news") for e in evidences):
            risk_items.append({
                "risk_type": "outdated_information", "risk_level": "medium",
                "description": "최신 정보 질문에 대한 신선한 공식 출처를 찾지 못했습니다. (rule_fallback)",
                "affected_claim_ids": [], "affects_core_answer": True, "resolved_by_evidence": False,
            })

    rows: list[Risk] = []
    seen_keys: set[str] = set()
    for item in risk_items:
        affected_ids = [cid for cid in item.get("affected_claim_ids", []) if cid in known_claim_ids]
        primary_claim_id = affected_ids[0] if affected_ids else None
        risk_key = f"{item['risk_type']}:{primary_claim_id or 'global'}"
        if risk_key in seen_keys:
            continue
        seen_keys.add(risk_key)

        level = item.get("risk_level", "low")
        if item["risk_type"] == "contradiction":
            penalty = _CONTRADICTION_PENALTY_BY_LEVEL.get(level, 0.0)
            if item.get("affects_core_answer") and level == "high":
                penalty = 30.0
        else:
            penalty = _RISK_PENALTY_BY_LEVEL.get(level, 0.0)
        if item.get("resolved_by_evidence"):
            penalty = 0.0

        rows.append(
            Risk(
                question_id=question.id,
                claim_id=uuid.UUID(primary_claim_id) if primary_claim_id else None,
                risk_key=risk_key[:150],
                risk_type=item["risk_type"],
                risk_level=level,
                description=item.get("description", ""),
                affects_core_answer=bool(item.get("affects_core_answer", False)),
                resolved_by_evidence=bool(item.get("resolved_by_evidence", False)),
                penalty=penalty,
                detected_by="llm_judge" if parsed is not None else "rule_fallback",
            )
        )

    db.add_all(rows)
    db.flush()
    return rows


def _run_final_answer_and_reflection(
    judge_client: LLMClient, question: Question, claims: list[Claim], deterministic_checks: list[DeterministicCheck],
    evidences: list[Evidence], cross_review: dict, risks: list[Risk], fallback_notes: list[str],
) -> tuple[FinalAnswerOutput, str, int]:
    claim_dicts = [_claim_dict(c) for c in claims]
    det_dicts = [
        {"claim_id": str(d.claim_id), "check_type": d.check_type, "check_passed": d.check_passed, "expected_result": d.expected_result}
        for d in deterministic_checks
    ]
    verification_dicts = [
        {"claim_id": str(c.id), "verification_status": c.verification_status, "verification_reason": c.verification_reason}
        for c in claims
    ]
    evidence_dicts = [
        {"evidence_id": str(e.id), "claim_id": str(e.claim_id), "title": e.title, "url": e.url, "relation": e.relation}
        for e in evidences
    ]
    risk_dicts = [{"risk_type": r.risk_type, "risk_level": r.risk_level, "description": r.description} for r in risks]
    known_evidence_by_id = {str(e.id): e for e in evidences}

    def _sanitize(output: FinalAnswerOutput) -> FinalAnswerOutput:
        clean_citations = []
        for c in output.citations:
            ev = known_evidence_by_id.get(c.evidence_id)
            if ev is None:
                continue
            clean_citations.append({"evidence_id": str(ev.id), "title": ev.title, "url": ev.url})
        output.citations = clean_citations
        return output

    parsed, meta = final_answer_agent.generate_final_answer(
        judge_client, question.original_question, question.refined_question, question.selected_question,
        question.answer_purpose, claim_dicts, det_dicts, verification_dicts, evidence_dicts, cross_review, risk_dicts,
    )
    attempts = 1

    if parsed is None:
        fallback_notes.append(f"final_answer_failed:{meta.get('error')}")
        return _assembled_fallback(claims, evidences), "assembled_fallback", attempts

    parsed = _sanitize(parsed)

    reflection_parsed, reflection_meta = reflection_agent.reflect(
        judge_client, question.selected_question, parsed, claim_dicts, verification_dicts, evidence_dicts
    )
    attempts += 1
    if reflection_parsed is not None and not reflection_parsed.passed and reflection_parsed.revised is not None:
        parsed = _sanitize(reflection_parsed.revised)
    elif reflection_parsed is None:
        fallback_notes.append(f"reflection_failed:{reflection_meta.get('error')}")

    return parsed, "llm_judge", attempts


def _assembled_fallback(claims: list[Claim], evidences: list[Evidence]) -> FinalAnswerOutput:
    verified_core = [c for c in claims if c.importance == "core" and c.verification_status == "verified"]
    weak_or_worse = [c for c in claims if c.verification_status in ("weak_evidence", "unsupported", "contradicted")]

    if verified_core:
        body = " ".join(c.claim_text for c in verified_core)
    else:
        body = "핵심 주장에 대한 충분한 근거를 확보하지 못했습니다."

    cautions = [f"{c.display_id}은(는) 근거가 제한적이므로 참고용으로만 사용하세요." for c in weak_or_worse]
    citations = [
        {"evidence_id": str(e.id), "title": e.title, "url": e.url}
        for e in evidences
        if e.relation == "support" and e.claim_id in {c.id for c in verified_core}
    ]
    return FinalAnswerOutput(
        summary=body[:300],
        final_answer=body,
        cautions=cautions,
        citations=[{"evidence_id": c["evidence_id"], "title": c["title"], "url": c["url"]} for c in citations],
    )


def _finalize(
    db: Session, question: Question, judge_client: LLMClient, judge_resolution: str,
    ai_responses: list[AIResponse], claims: list[Claim], deterministic_checks: list[DeterministicCheck],
    documents: list[SearchDocument], evidences: list[Evidence], risks: list[Risk],
    cross_review: dict, cross_review_mode: str, final_answer_output: FinalAnswerOutput,
    final_answer_mode: str, judge_attempts: int, fallback_notes: list[str],
) -> None:
    claim_inputs = []
    evidence_quality_by_claim: dict = {}
    for evidence in evidences:
        evidence_quality_by_claim.setdefault(evidence.claim_id, []).append(float(evidence.source_quality_score))

    for claim in claims:
        claim_inputs.append(
            ClaimScoreInput(
                importance=claim.importance,
                verification_status=claim.verification_status,
                consensus_score=float(claim.consensus_score) if claim.consensus_score is not None else None,
                deterministic_verified=(
                    claim.verification_basis == "deterministic" and claim.verification_status == "verified"
                ),
                evidence_source_quality=evidence_quality_by_claim.get(claim.id, []),
            )
        )

    logic_issue_count = len(cross_review.get("logic_issues", []))
    outdated_risk_count = len([r for r in risks if r.risk_type == "outdated_information" and r.penalty > 0])
    contradiction_penalty = min(30.0, sum(float(r.penalty) for r in risks if r.risk_type == "contradiction"))
    risk_penalty = min(40.0, sum(float(r.penalty) for r in risks if r.risk_type != "contradiction"))

    score = calculate_trust_score(
        claims=claim_inputs,
        contradiction_penalty=contradiction_penalty,
        risk_penalty=risk_penalty,
        logic_issue_count=logic_issue_count,
        outdated_risk_count=outdated_risk_count,
        question_type=question.question_type or "general",
        verification_basis=question.verification_basis or "mixed",
    )

    claims_by_provider: dict[str, list[ClaimScoreInput]] = {}
    for claim, claim_input in zip(claims, claim_inputs):
        for provider in claim.source_models or []:
            claims_by_provider.setdefault(provider, []).append(claim_input)

    for response in ai_responses:
        if response.status != "success":
            continue
        model_score, model_grade, reason = calculate_model_score(claims_by_provider.get(response.provider, []))
        response.model_score = model_score
        response.model_grade = model_grade
        response.model_score_reason = reason
        response.model_score_detail = {"claim_count": len(claims_by_provider.get(response.provider, []))}
        db.add(response)

    db.add(
        TrustScore(
            question_id=question.id,
            evidence_support_score=score["evidence_support_score"],
            source_quality_score=score["source_quality_score"],
            consensus_score=score["consensus_score"],
            logic_score=score["logic_score"],
            freshness_score=score["freshness_score"],
            base_score=score["base_score"],
            contradiction_penalty=score["contradiction_penalty"],
            risk_penalty=score["risk_penalty"],
            total_score=score["total_score"],
            grade=score["grade"],
            score_reasons=score["score_reasons"],
            strengths=score["strengths"],
            deductions=score["deductions"],
            calculation_detail=score["calculation_detail"],
        )
    )

    claim_distribution = {
        "verified": len([c for c in claims if c.verification_status == "verified"]),
        "weak_evidence": len([c for c in claims if c.verification_status == "weak_evidence"]),
        "unsupported": len([c for c in claims if c.verification_status == "unsupported"]),
        "contradicted": len([c for c in claims if c.verification_status == "contradicted"]),
    }
    claim_evidence_relations = [
        {"claim_id": str(e.claim_id), "evidence_id": str(e.id), "relation": e.relation} for e in evidences
    ]
    source_summary = {
        "total_documents": len(documents),
        "used_evidences": len(evidences),
        "web_documents": len([d for d in documents if d.source_type not in ("official", "government")]),
        "academic_papers": len([d for d in documents if d.source_type in ("academic", "paper")]),
        "technical_blogs": len([d for d in documents if d.source_type == "blog"]),
        "official_documents": len([d for d in documents if d.source_type == "official"]),
        "government_sources": len([d for d in documents if d.source_type == "government"]),
        "deterministic_checks": len(deterministic_checks),
    }

    fallback_reason = "; ".join(fallback_notes)[:2000] if fallback_notes else None

    db.add(
        FinalResult(
            question_id=question.id,
            summary=final_answer_output.summary,
            final_answer=final_answer_output.final_answer,
            cautions=final_answer_output.cautions,
            citations=[c if isinstance(c, dict) else c.model_dump() for c in final_answer_output.citations],
            key_issues=[mp.get("description", "") if isinstance(mp, dict) else mp for mp in cross_review.get("missing_points", [])][:3],
            cross_review=cross_review,
            source_summary=source_summary,
            claim_distribution=claim_distribution,
            claim_evidence_relations=claim_evidence_relations,
            final_answer_mode=final_answer_mode,
            cross_review_mode=cross_review_mode,
            judge_provider=judge_client.provider,
            judge_model=judge_client.model_name,
            judge_attempts=judge_attempts,
            fallback_reason=fallback_reason,
        )
    )
    db.flush()
