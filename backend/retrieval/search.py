"""FAISS 检索：查询向量 → IndexFlatIP（余弦）→ 元数据回查。"""
import json
from dataclasses import dataclass
from pathlib import Path

import faiss
import numpy as np

from corpus.schema import Chunk
from llm import embed_texts

INDEX_DIR = Path(__file__).resolve().parents[1] / "index"


@dataclass
class SearchResult:
    chunk: Chunk
    score: float


class Retriever:
    """进程级检索器：索引启动时懒加载一次，之后常驻内存。"""

    def __init__(self) -> None:
        self._index: faiss.Index | None = None
        self._chunks: list[Chunk] = []

    @property
    def ready(self) -> bool:
        return self._index is not None

    def load(self) -> int:
        index = faiss.read_index(str(INDEX_DIR / "index.faiss"))
        meta = json.loads((INDEX_DIR / "meta.json").read_text(encoding="utf-8"))
        assert meta["dim"] == index.d, "meta.json 与 index.faiss 维度不一致，请重跑 ingest"
        self._index = index
        self._chunks = [Chunk(**c) for c in meta["chunks"]]
        return len(self._chunks)

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        if self._index is None:
            self.load()
        q = embed_texts([query])
        scores, ids = self._index.search(q, min(top_k, len(self._chunks)))
        return [
            SearchResult(chunk=self._chunks[i], score=float(s))
            for s, i in zip(scores[0], ids[0])
            if i >= 0
        ]


# 进程级单例：FastAPI 启动事件中预热
retriever = Retriever()
