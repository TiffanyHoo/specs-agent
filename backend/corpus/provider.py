"""语料提供者协议与装配。

检索层只面向 CorpusProvider 协议与 Chunk 结构，与语料来源完全解耦；
更换语料 = 修改 corpus.yaml + 重跑 ingest，业务代码零改动。
"""
import os
from pathlib import Path
from typing import Protocol

import yaml

from corpus.adapters import company, fs_md
from corpus.schema import RawDocument

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS_CONFIG = Path(__file__).parent / "corpus.yaml"


class CorpusProvider(Protocol):
    """语料适配器协议：任何新语料源实现 load() 即可接入。"""

    source_id: str

    def load(self) -> list[RawDocument]: ...


def _resolve_path(p: str) -> Path:
    path = Path(os.path.expandvars(p))
    return path if path.is_absolute() else (REPO_ROOT / path)


def _build_provider(cfg: dict) -> CorpusProvider:
    match cfg["type"]:
        case "fs_md":
            return fs_md.FsMdProvider(
                source_id=cfg["source_id"], path=_resolve_path(cfg["path"])
            )
        case "company":
            return company.CompanyProvider(
                source_id=cfg["source_id"],
                path_env=cfg.get("path_env", "COMPANY_CORPUS_PATH"),
            )
        case _:
            raise ValueError(f"未知语料适配器类型: {cfg['type']}")


def load_providers() -> list[CorpusProvider]:
    cfg = yaml.safe_load(CORPUS_CONFIG.read_text(encoding="utf-8")) or {}
    return [
        _build_provider(sc)
        for sc in cfg.get("sources", [])
        if sc.get("enabled", True)
    ]


def load_corpus() -> list[RawDocument]:
    """装配所有已启用的语料源。"""
    docs: list[RawDocument] = []
    for provider in load_providers():
        docs.extend(provider.load())
    return docs
