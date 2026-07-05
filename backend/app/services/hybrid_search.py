"""PostgreSQL FTS keyword search + pgvector cosine vector search, combined
into Hybrid Score = 0.6*keyword + 0.4*vector (docs/DB_SCHEMA.md #14,
docs/FEATURES.md F-13). Frontend never recomputes this."""
import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import DocumentChunk, DocumentEmbedding, SearchDocument

KEYWORD_WEIGHT = 0.6
VECTOR_WEIGHT = 0.4


@dataclass
class HybridSearchResult:
    document: SearchDocument
    chunk: DocumentChunk
    keyword_score: float
    vector_score: float
    hybrid_score: float


def _keyword_scores(db: Session, question_id: uuid.UUID, queries: list[str]) -> dict[uuid.UUID, float]:
    scores: dict[uuid.UUID, float] = {}
    for query in queries:
        if not query or not query.strip():
            continue
        rank = func.ts_rank_cd(
            DocumentChunk.search_vector,
            func.plainto_tsquery("simple", query),
            32,
        )
        stmt = (
            select(DocumentChunk.id, rank.label("score"))
            .join(SearchDocument, DocumentChunk.document_id == SearchDocument.id)
            .where(
                SearchDocument.question_id == question_id,
                DocumentChunk.search_vector.op("@@")(func.plainto_tsquery("simple", query)),
            )
        )
        for chunk_id, score in db.execute(stmt).all():
            score = float(score or 0.0)
            if chunk_id not in scores or score > scores[chunk_id]:
                scores[chunk_id] = score
    return scores


def _vector_scores(
    db: Session, question_id: uuid.UUID, query_embeddings: list[list[float]]
) -> dict[uuid.UUID, float]:
    scores: dict[uuid.UUID, float] = {}
    for embedding in query_embeddings:
        distance = DocumentEmbedding.embedding.cosine_distance(embedding)
        stmt = (
            select(DocumentChunk.id, distance.label("distance"))
            .join(DocumentEmbedding, DocumentEmbedding.chunk_id == DocumentChunk.id)
            .join(SearchDocument, DocumentChunk.document_id == SearchDocument.id)
            .where(SearchDocument.question_id == question_id)
            .order_by(distance)
            .limit(50)
        )
        for chunk_id, distance in db.execute(stmt).all():
            similarity = max(0.0, 1.0 - float(distance))
            if chunk_id not in scores or similarity > scores[chunk_id]:
                scores[chunk_id] = similarity
    return scores


def search(
    db: Session,
    question_id: uuid.UUID,
    keyword_queries: list[str],
    query_embeddings: list[list[float]],
    top_k: int = 5,
) -> list[HybridSearchResult]:
    keyword_scores = _keyword_scores(db, question_id, keyword_queries)
    vector_scores = _vector_scores(db, question_id, query_embeddings)

    chunk_ids = set(keyword_scores) | set(vector_scores)
    if not chunk_ids:
        return []

    chunks = {
        c.id: c
        for c in db.execute(select(DocumentChunk).where(DocumentChunk.id.in_(chunk_ids))).scalars()
    }
    document_ids = {c.document_id for c in chunks.values()}
    documents = {
        d.id: d
        for d in db.execute(select(SearchDocument).where(SearchDocument.id.in_(document_ids))).scalars()
    }

    ranked: list[HybridSearchResult] = []
    for chunk_id in chunk_ids:
        chunk = chunks.get(chunk_id)
        if chunk is None:
            continue
        document = documents.get(chunk.document_id)
        if document is None:
            continue
        k_score = keyword_scores.get(chunk_id, 0.0)
        v_score = vector_scores.get(chunk_id, 0.0)
        hybrid = round(KEYWORD_WEIGHT * k_score + VECTOR_WEIGHT * v_score, 5)
        ranked.append(
            HybridSearchResult(
                document=document,
                chunk=chunk,
                keyword_score=round(k_score, 5),
                vector_score=round(v_score, 5),
                hybrid_score=hybrid,
            )
        )

    ranked.sort(key=lambda r: r.hybrid_score, reverse=True)

    deduped: list[HybridSearchResult] = []
    seen_documents: set[uuid.UUID] = set()
    for result in ranked:
        if result.document.id in seen_documents:
            continue
        seen_documents.add(result.document.id)
        deduped.append(result)
        if len(deduped) >= top_k:
            break
    return deduped
