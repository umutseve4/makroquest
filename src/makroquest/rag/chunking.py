"""Corpus chunking for RAG.

Markdown docs are split on headings, then long sections are split on
paragraph boundaries so every chunk stays under `max_chars`. Each chunk
keeps its source path + heading so the hint agent can cite it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Chunk:
    source: str  # relative file path, e.g. "data/corpus/enflasyon.md"
    heading: str  # nearest markdown heading ("" if none)
    text: str

    @property
    def citation(self) -> str:
        return f"{self.source}#{self.heading}" if self.heading else self.source


_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")


def split_markdown(source: str, content: str, max_chars: int = 800) -> list[Chunk]:
    """Split markdown into heading-scoped chunks of at most `max_chars`."""
    sections: list[tuple[str, list[str]]] = [("", [])]
    for line in content.splitlines():
        m = _HEADING.match(line)
        if m:
            sections.append((m.group(2).strip(), []))
        else:
            sections[-1][1].append(line)

    chunks: list[Chunk] = []
    for heading, lines in sections:
        body = "\n".join(lines).strip()
        if not body:
            continue
        for piece in _split_paragraphs(body, max_chars):
            chunks.append(Chunk(source=source, heading=heading, text=piece))
    return chunks


def _split_paragraphs(body: str, max_chars: int) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    pieces: list[str] = []
    buf = ""
    for para in paragraphs:
        candidate = f"{buf}\n\n{para}".strip() if buf else para
        if len(candidate) <= max_chars:
            buf = candidate
        else:
            if buf:
                pieces.append(buf)
            # a single oversized paragraph is hard-wrapped
            while len(para) > max_chars:
                pieces.append(para[:max_chars])
                para = para[max_chars:]
            buf = para
    if buf:
        pieces.append(buf)
    return pieces


def load_corpus(corpus_dir: str | Path, max_chars: int = 800) -> list[Chunk]:
    """Chunk every .md file under `corpus_dir` (sorted, deterministic)."""
    corpus_dir = Path(corpus_dir)
    chunks: list[Chunk] = []
    for path in sorted(corpus_dir.rglob("*.md")):
        rel = path.relative_to(corpus_dir).as_posix()
        chunks.extend(split_markdown(rel, path.read_text(encoding="utf-8"), max_chars))
    return chunks
