"""LangGraph 共享状态：贯穿全图的字段。"""
from typing import TypedDict


class SourceChunk(TypedDict):
    """带编号的规范条款：编号 n 与回答中的角标 [n] 一一对应。"""

    n: int
    id: str
    doc_title: str
    section: str
    content: str
    score: float


class AgentState(TypedDict, total=False):
    mode: str  # "chat" | "review"
    question: str  # chat: 用户问题；review: 代码 + 可选说明
    top_k: int

    candidates: list[SourceChunk]  # 检索召回（未过滤）
    sources: list[SourceChunk]  # grade 过滤后保留并重新编号的条款
    covered: bool  # 规范是否覆盖该问题

    answer: str  # chat 模式最终回答（含 [n] 角标）
    reasoning: str  # 思考过程文本
    review_items: list[dict]  # review 模式违规清单
