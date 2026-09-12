"""LLM / Embedding 客户端封装（OpenAI 兼容协议）。

配置来自仓库根目录 .env（参考 .env.example）。
"""
import os
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1024"))


def _embedding_client() -> OpenAI:
    api_key = os.getenv("EMBEDDING_API_KEY")
    if not api_key:
        raise RuntimeError(
            "缺少 EMBEDDING_API_KEY：请复制 .env.example 为 .env 并填入密钥"
        )
    return OpenAI(
        api_key=api_key,
        base_url=os.getenv(
            "EMBEDDING_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
        ),
    )


def embed_texts(texts: list[str], batch_size: int = 10) -> np.ndarray:
    """批量文本 → 归一化向量矩阵（L2 归一化后内积即余弦相似度）。

    batch_size 上限 10：DashScope embedding 接口的批量限制。
    """
    client = _embedding_client()
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-v3")
    vecs: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        resp = client.embeddings.create(
            model=model,
            input=texts[i : i + batch_size],
            dimensions=EMBEDDING_DIM,
            encoding_format="float",
        )
        vecs.extend(d.embedding for d in resp.data)
    arr = np.asarray(vecs, dtype="float32")
    arr /= np.linalg.norm(arr, axis=1, keepdims=True)
    return arr


CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen-plus")
# 思考过程模型：qwen3 系列开启 enable_thinking 后会流式返回 reasoning_content
CHAT_REASONING_MODEL = os.getenv("CHAT_REASONING_MODEL", CHAT_MODEL)


def chat_client() -> OpenAI:
    """问答/审查用的 LLM 客户端（OpenAI 兼容协议，默认复用百炼配置）。"""
    # 未单独配置 CHAT_* 时复用 EMBEDDING_*（同一平台，如百炼）
    api_key = os.getenv("CHAT_API_KEY") or os.getenv("EMBEDDING_API_KEY")
    if not api_key:
        raise RuntimeError("缺少 CHAT_API_KEY / EMBEDDING_API_KEY：请参考 .env.example 配置 .env")
    return OpenAI(
        api_key=api_key,
        base_url=os.getenv("CHAT_BASE_URL")
        or os.getenv(
            "EMBEDDING_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
        ),
    )
