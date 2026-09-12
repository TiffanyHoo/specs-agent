"""ingest CLI：语料 → 分块 → embedding → backend/index/{index.faiss, meta.json}

用法（backend 目录下）：
    .venv/Scripts/python -m retrieval.ingest            # 全量构建索引
    .venv/Scripts/python -m retrieval.ingest --dry-run  # 仅分块统计，不调 embedding
"""
import argparse
import json
import time
from pathlib import Path

import faiss

from corpus.provider import load_corpus
from llm import EMBEDDING_DIM, embed_texts
from retrieval.chunker import chunk_all

INDEX_DIR = Path(__file__).resolve().parents[1] / "index"


def build_index(dry_run: bool = False) -> None:
    t0 = time.time()
    docs = load_corpus()
    print(f"[1/3] 语料加载: {len(docs)} 篇文档")
    chunks = chunk_all(docs)
    print(f"[2/3] 分块完成: {len(chunks)} 个 chunk（去重后）")
    for source in {c.source_id for c in chunks}:
        n = sum(1 for c in chunks if c.source_id == source)
        print(f"      - {source}: {n} chunks")
    if dry_run:
        return

    vectors = embed_texts([c.content for c in chunks])
    assert vectors.shape[1] == EMBEDDING_DIM, "embedding 维度与 EMBEDDING_DIM 不一致"
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_DIR / "index.faiss"))
    (INDEX_DIR / "meta.json").write_text(
        json.dumps(
            {"dim": EMBEDDING_DIM, "chunks": [c.model_dump() for c in chunks]},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"[3/3] 索引写入 {INDEX_DIR}，耗时 {time.time() - t0:.1f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="构建规范知识库向量索引")
    parser.add_argument("--dry-run", action="store_true", help="仅分块统计，不调用 embedding")
    build_index(parser.parse_args().dry_run)
