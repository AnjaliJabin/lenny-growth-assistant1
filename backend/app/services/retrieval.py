"""
RAG service: loads transcripts, builds FAISS index, retrieves relevant chunks.
"""
import os
import json
import pickle
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

CHUNK_SIZE = 600   # words per chunk
CHUNK_OVERLAP = 80
TOP_K = 5


@dataclass
class Chunk:
    text: str
    source: str
    episode: str
    chunk_id: int


class RetrievalService:
    def __init__(self):
        self._index = None
        self._chunks: list[Chunk] = []
        self._embedder = None
        self._ready = False

    def _get_embedder(self):
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer(settings.EMBEDDING_MODEL)
        return self._embedder

    def _chunk_text(self, text: str, source: str, episode: str) -> list[Chunk]:
        words = text.split()
        chunks = []
        i = 0
        cid = 0
        while i < len(words):
            chunk_words = words[i:i + CHUNK_SIZE]
            chunks.append(Chunk(
                text=" ".join(chunk_words),
                source=source,
                episode=episode,
                chunk_id=cid,
            ))
            i += CHUNK_SIZE - CHUNK_OVERLAP
            cid += 1
        return chunks

    def build_index(self):
        import faiss
        transcripts_path = Path(settings.TRANSCRIPTS_PATH)
        if not transcripts_path.exists():
            logger.warning(f'"Transcripts path not found: {transcripts_path}"')
            return

        all_chunks: list[Chunk] = []
        for f in sorted(transcripts_path.glob("*.txt")):
            text = f.read_text(encoding="utf-8", errors="ignore")
            episode = f.stem
            chunks = self._chunk_text(text, str(f.name), episode)
            all_chunks.extend(chunks)
            logger.info(f'"Loaded {len(chunks)} chunks from {f.name}"')

        if not all_chunks:
            logger.warning('"No transcript chunks found"')
            return

        embedder = self._get_embedder()
        texts = [c.text for c in all_chunks]
        logger.info(f'"Embedding {len(texts)} chunks..."')
        embeddings = embedder.encode(texts, batch_size=64, show_progress_bar=False)
        embeddings = np.array(embeddings, dtype="float32")
        faiss.normalize_L2(embeddings)

        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)

        index_path = Path(settings.VECTOR_INDEX_PATH)
        index_path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(index_path / "index.faiss"))
        with open(index_path / "chunks.pkl", "wb") as fh:
            pickle.dump(all_chunks, fh)

        self._index = index
        self._chunks = all_chunks
        self._ready = True
        logger.info(f'"Index built with {len(all_chunks)} chunks"')

    def load_index(self):
        import faiss
        index_path = Path(settings.VECTOR_INDEX_PATH)
        faiss_file = index_path / "index.faiss"
        chunks_file = index_path / "chunks.pkl"
        if faiss_file.exists() and chunks_file.exists():
            self._index = faiss.read_index(str(faiss_file))
            with open(chunks_file, "rb") as fh:
                self._chunks = pickle.load(fh)
            self._ready = True
            logger.info(f'"Loaded index with {len(self._chunks)} chunks"')
        else:
            logger.info('"No cached index found, building..."')
            self.build_index()

    def retrieve(self, query: str, top_k: int = TOP_K) -> list[dict]:
        if not self._ready or self._index is None:
            return []
        import faiss
        embedder = self._get_embedder()
        q_emb = embedder.encode([query], show_progress_bar=False)
        q_emb = np.array(q_emb, dtype="float32")
        faiss.normalize_L2(q_emb)
        scores, indices = self._index.search(q_emb, top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            chunk = self._chunks[idx]
            results.append({
                "text": chunk.text,
                "source": chunk.source,
                "episode": chunk.episode,
                "score": float(score),
            })
        return results

    @property
    def is_ready(self) -> bool:
        return self._ready


retrieval_service = RetrievalService()
