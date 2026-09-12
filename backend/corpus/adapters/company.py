"""公司知识库适配器（信息安全约束）。

- 语料路径经环境变量注入，绝不写入仓库；
- 本适配器与 fs_md 共用分块/检索链路，业务代码对其无感知。
"""
import os
from pathlib import Path

from corpus.adapters.fs_md import FsMdProvider
from corpus.schema import RawDocument


class CompanyProvider:
    def __init__(self, source_id: str, path_env: str = "COMPANY_CORPUS_PATH"):
        self.source_id = source_id
        self.path_env = path_env

    def load(self) -> list[RawDocument]:
        raw = os.getenv(self.path_env)
        if not raw:
            raise RuntimeError(
                f"未设置环境变量 {self.path_env}，无法加载公司语料"
                "（该语料按信息安全要求不入仓库，需在本机配置路径）"
            )
        return FsMdProvider(self.source_id, Path(raw)).load()
