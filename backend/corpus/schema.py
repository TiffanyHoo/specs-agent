"""统一语料数据结构：语料库与检索层之间的唯一契约。

所有引用溯源（角标、hover 卡片）都依赖 Chunk 的 metadata，
语料来源可替换，但该结构不可变。
"""
from pydantic import BaseModel


class RawDocument(BaseModel):
    """适配器产出的原始文档，尚未分块。"""

    source_id: str
    path: str  # 展示用相对路径
    title: str  # 文档标题（取 H1，缺省用文件名）
    text: str  # 原始 Markdown 全文


class Chunk(BaseModel):
    """检索与引用的最小单元。"""

    id: str  # 稳定 ID：{source_id}/{doc_slug}#{anchor}[-seq]
    source_id: str
    doc_title: str
    section: str  # 完整标题路径，如 "CSS 规范 > BEM 命名"
    anchor: str  # 标题路径 slug，用于引用定位
    content: str  # 已含标题路径前缀的正文，直接用于 embedding 与展示
