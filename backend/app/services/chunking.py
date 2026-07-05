"""Document chunking (docs/FEATURES.md F-12). Splits cleaned document text
into token-bounded chunks for FTS + embedding, each with a content hash for
de-duplication."""
import hashlib
import re
from dataclasses import dataclass

_WHITESPACE_RE = re.compile(r"\s+")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?。？！])\s+")


@dataclass
class Chunk:
    chunk_index: int
    content: str
    token_count: int
    chunk_hash: str


def clean_text(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text or "").strip()


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def chunk_text(text: str, max_chars: int = 1200) -> list[Chunk]:
    cleaned = clean_text(text)
    if not cleaned:
        return []

    sentences = _SENTENCE_SPLIT_RE.split(cleaned)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) > max_chars and current:
            chunks.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        chunks.append(current)

    if not chunks:
        chunks = [cleaned[i : i + max_chars] for i in range(0, len(cleaned), max_chars)]

    result = []
    seen_hashes: set[str] = set()
    for idx, content in enumerate(chunks):
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if content_hash in seen_hashes:
            continue
        seen_hashes.add(content_hash)
        result.append(
            Chunk(
                chunk_index=idx,
                content=content,
                token_count=_estimate_tokens(content),
                chunk_hash=content_hash,
            )
        )
    return result
