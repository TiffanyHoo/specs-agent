"""文件系统 Markdown 语料适配器：递归读取目录下所有 .md 文件。"""
from pathlib import Path

from corpus.schema import RawDocument


class FsMdProvider:
    def __init__(self, source_id: str, path: Path):
        self.source_id = source_id
        self.path = path

    def load(self) -> list[RawDocument]:
        if not self.path.exists():
            raise FileNotFoundError(f"语料目录不存在: {self.path}")
        docs: list[RawDocument] = []
        for md in sorted(self.path.rglob("*.md")):
            text = md.read_text(encoding="utf-8")
            title = next(
                (
                    line.lstrip("# ").strip()
                    for line in text.splitlines()
                    if line.startswith("# ")
                ),
                md.stem,
            )
            docs.append(
                RawDocument(
                    source_id=self.source_id,
                    path=str(md.relative_to(self.path)),
                    title=title,
                    text=text,
                )
            )
        return docs
