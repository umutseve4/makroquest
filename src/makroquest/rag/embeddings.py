"""Embedding backends.

Baseline: `HashingEmbedder` — a deterministic bag-of-words hashing vector
(char 3-gram TF, L2-normalized). Zero external dependencies, zero API keys,
fully reproducible. It is intentionally simple: M1.5's golden-set eval will
measure it and justify (or reject) a model upgrade with numbers instead of
hype.

The interface is one function: `embed(texts) -> list[list[float]]`.
Any future backend (ONNX model, API) must keep the same signature and
declare its own `dim`.
"""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata

DIM = 512  # small enough for cheap pgvector ops, large enough for 3-gram TF

_WORD = re.compile(r"\w+", re.UNICODE)


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(_WORD.findall(text))


def _ngrams(text: str, n: int = 3) -> list[str]:
    padded = f" {text} "
    if len(padded) < n:
        return [padded]
    return [padded[i : i + n] for i in range(len(padded) - n + 1)]


class HashingEmbedder:
    """Deterministic char-3-gram hashing embedder (no model download)."""

    dim = DIM
    name = "hashing-3gram-v1"

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for gram in _ngrams(_normalize(text)):
            digest = hashlib.md5(gram.encode("utf-8"), usedforsecurity=False).digest()
            idx = int.from_bytes(digest[:4], "big") % self.dim
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0.0:
            return vec
        return [v / norm for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity for pre-normalized or raw vectors."""
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)
