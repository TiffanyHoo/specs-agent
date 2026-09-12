"""Markdown 分块器：按标题层级切分，保留标题路径作为引用定位 anchor。

设计要点：
- 分块粒度 = 最深标题小节，天然对齐"规范条款"这一引用单元；
- 超长小节按段落二次切分，anchor 追加序号保证 ID 稳定；
- 正文前缀拼接「文档标题 > 标题路径」，提升 embedding 的语义可分性。
"""
import re

from corpus.schema import Chunk, RawDocument

MAX_CHARS = 600  # 单块正文上限，超出按段落二次切分

HEADING_RE = re.compile(r"^(#{1,4})\s+(.+?)\s*$")


def _slug(text: str) -> str:
    s = re.sub(r"\s+", "-", text.strip())
    s = re.sub(r"[^\w\u4e00-\u9fff-]", "", s)
    return s or "section"


def split_sections(text: str) -> list[tuple[list[str], str]]:
    """切分为 [(标题路径, 小节正文)]；首个 H1 之前的游离内容忽略。"""
    sections: list[tuple[list[str], str]] = []
    stack: list[tuple[int, str]] = []  # (标题级别, 标题文本)
    buf: list[str] = []

    def flush() -> None:
        sections.append(([t for _, t in stack], "\n".join(buf).strip()))

    for line in text.splitlines():
        m = HEADING_RE.match(line)
        if m:
            flush()
            buf = []
            level, title = len(m.group(1)), m.group(2).strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
        else:
            buf.append(line)
    flush()
    return sections


def _split_long(body: str) -> list[str]:
    """超过 MAX_CHARS 的正文按空行分段累积切分。"""
    if len(body) <= MAX_CHARS:
        return [body]
    parts, cur = [], ""
    for para in re.split(r"\n\s*\n", body):
        candidate = f"{cur}\n\n{para}" if cur else para
        if len(candidate) > MAX_CHARS and cur:
            parts.append(cur)
            cur = para
        else:
            cur = candidate
    if cur:
        parts.append(cur)
    return parts


def chunk_document(doc: RawDocument) -> list[Chunk]:
    doc_slug = _slug(doc.title)
    chunks: list[Chunk] = []
    for path, body in split_sections(doc.text):
        if not body or not path:
            continue
        section = " > ".join(path)
        anchor = "-".join(_slug(p) for p in path[1:]) or doc_slug
        prefix = f"{doc.title}｜{section}"
        for seq, part in enumerate(_split_long(body)):
            chunk_id = f"{doc.source_id}/{doc_slug}#{anchor}" + (f"-{seq + 1}" if seq else "")
            chunks.append(
                Chunk(
                    id=chunk_id,
                    source_id=doc.source_id,
                    doc_title=doc.title,
                    section=section,
                    anchor=anchor,
                    content=f"{prefix}\n{part}",
                )
            )
    return chunks


def chunk_all(docs: list[RawDocument]) -> list[Chunk]:
    """全量分块 + 按 ID 去重（重复 ID 追加序号，保证稳定可引用）。"""
    chunks: list[Chunk] = []
    seen: dict[str, int] = {}
    for doc in docs:
        for chunk in chunk_document(doc):
            n = seen.get(chunk.id, 0)
            seen[chunk.id] = n + 1
            if n:
                chunk = chunk.model_copy(update={"id": f"{chunk.id}-{n + 1}"})
            chunks.append(chunk)
    return chunks
