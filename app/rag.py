from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .config import CHROMA_DIR, KB_DIR


@dataclass(frozen=True)
class Evidence:
    source: str
    section: str
    text: str
    score: float
    backend: str

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "section": self.section,
            "text": self.text,
            "score": round(float(self.score), 4),
            "backend": self.backend,
        }


def _chunks_from_markdown(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    chunks: list[dict] = []
    section = path.stem.replace("_", " ").title()
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("#"):
            if current:
                body = " ".join(s.strip() for s in current if s.strip()).strip()
                if body:
                    chunks.append({"source": path.name, "section": section, "text": body})
                current = []
            section = line.lstrip("#").strip()
        else:
            if line.strip():
                current.append(line)
    if current:
        body = " ".join(s.strip() for s in current if s.strip()).strip()
        if body:
            chunks.append({"source": path.name, "section": section, "text": body})
    return chunks


def load_chunks(kb_dir: Path = KB_DIR) -> list[dict]:
    chunks: list[dict] = []
    for path in sorted(kb_dir.glob("*.md")):
        chunks.extend(_chunks_from_markdown(path))
    return chunks


class LocalTfidfRetriever:
    """Offline retrieval backend for demos and tests; no API key required."""
    def __init__(self, kb_dir: Path = KB_DIR):
        self.chunks = load_chunks(kb_dir)
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.matrix = self.vectorizer.fit_transform([c["text"] for c in self.chunks]) if self.chunks else None

    def query(self, query: str, k: int = 3) -> list[Evidence]:
        if not self.chunks or self.matrix is None:
            return []
        q = self.vectorizer.transform([query])
        scores = cosine_similarity(q, self.matrix)[0]
        order = scores.argsort()[::-1][:k]
        return [
            Evidence(self.chunks[i]["source"], self.chunks[i]["section"], self.chunks[i]["text"], float(scores[i]), "tfidf")
            for i in order
        ]


class ChromaOpenAIRetriever:
    """Persistent ChromaDB retrieval using OpenAI embeddings.

    This is the full project RAG path. The app automatically falls back to LocalTfidfRetriever
    when ChromaDB or an API key is unavailable.
    """
    def __init__(self, kb_dir: Path = KB_DIR):
        try:
            import chromadb
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install chromadb and openai to use the Chroma backend") from exc
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is required for Chroma/OpenAI embeddings")
        self.client_api = OpenAI()
        self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection = self.client.get_or_create_collection(
            name="supplier_security_guidance",
            metadata={"hnsw:space": "cosine"},
        )
        self.kb_dir = kb_dir
        self._sync()

    def _embed(self, texts: list[str]) -> list[list[float]]:
        result = self.client_api.embeddings.create(model=self.embedding_model, input=texts)
        return [item.embedding for item in result.data]

    def _sync(self) -> None:
        chunks = load_chunks(self.kb_dir)
        if not chunks:
            return
        ids = [hashlib.sha256(f'{c["source"]}:{c["section"]}:{c["text"]}'.encode()).hexdigest()[:24] for c in chunks]
        embeddings = self._embed([c["text"] for c in chunks])
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=[c["text"] for c in chunks],
            metadatas=[{"source": c["source"], "section": c["section"]} for c in chunks],
        )

    def query(self, query: str, k: int = 3) -> list[Evidence]:
        q_emb = self._embed([query])[0]
        result = self.collection.query(query_embeddings=[q_emb], n_results=k)
        docs = (result.get("documents") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        evidence = []
        for doc, meta, distance in zip(docs, metas, distances):
            similarity = 1.0 - float(distance)
            evidence.append(Evidence(meta.get("source","unknown"), meta.get("section",""), doc, similarity, "chroma-openai"))
        return evidence


def get_retriever(prefer_chroma: bool = True):
    if prefer_chroma:
        try:
            return ChromaOpenAIRetriever()
        except Exception:
            pass
    return LocalTfidfRetriever()


def query_from_drivers(drivers: Iterable[dict], max_chars: int = 1200) -> str:
    terms = []
    for d in drivers:
        terms.append(f"{d.get('label','')} {d.get('rationale','')} {d.get('recommendation','')}")
    return ("supplier cybersecurity requirements " + " ".join(terms))[:max_chars]
