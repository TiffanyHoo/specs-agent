# Specs Agent — 前端工程规范问答 Agent

基于 LangGraph + FAISS + Vue3 的规范知识库 Agent：对规范文档做 RAG 问答（流式输出 + 引用溯源角标），支持贴代码做规范审查（违规清单 + 条款引用），并附 20 题量化评测。

## 功能特性

- **规范问答**：流式 Markdown 回答，每个结论带 `[n]` 角标，hover 弹出条款原文卡片；LLM 思考过程独立折叠面板
- **代码审查**：贴一段代码 → 结构化违规清单（severity / 问题 / 代码片段 / 修复建议），每条附规范条款出处
- **诚实兜底**：grade 节点过滤无关条款，规范未覆盖时明确说"未覆盖"，不编造规范
- **可插拔语料**：语料来源与 Agent 能力解耦，公司语料不入仓库
- **量化评测**：20 题评测脚本输出检索命中率、引用准确率、LLM-as-judge 报告

## 整体架构

```
┌─ frontend/ (Vue3 + Vite + Pinia + TS)
│   ├─ composables/useSSE.ts     POST 流式读取（NDJSON 事件流，含半包缓冲）
│   ├─ Markdown 流式渲染 + 引用角标 [1] hover 卡片（Popover 显示条款原文）
│   ├─ 思考过程折叠面板（qwen enable_thinking → reasoning_content 透传）
│   └─ 代码审查结果卡片（severity 着色 + 条款出处 + 修复建议）
│          │  事件类型: token / reasoning / sources / review_item / error
┌─ backend/ (FastAPI + LangGraph)
│   ├─ main.py          POST /api/chat/stream、/api/review/stream（NDJSON 流式）
│   ├─ graph/           单张 4 节点小图
│   │   ├─ retrieve     向量召回 + 查询改写 + 词面补充 + LLM 重排
│   │   ├─ grade        LLM 相关性过滤（拿不准算相关），无条款走"规范未覆盖"兜底
│   │   └─ generate / review   问答（流式+角标） / 审查（结构化 JSON）
│   ├─ retrieval/       ingest CLI（分块→embedding→index.faiss）+ FAISS 查询
│   └─ corpus/          可插拔语料适配层（fs_md / company 适配器 + corpus.yaml）
├─ corpus-data/         示例语料（15 篇前端工程规范，69 chunks）+ 演示备用语料
└─ eval/                questions.yaml（20 题）+ run.py（评测）→ report.md
```

检索细节（为什么 not 裸向量检索）：dense embedding 对代码查询偏弱，审查模式下做四路并集——
审查意图前缀查询 + 原始问题 + 拉丁标识符词面补充（any / v-html / localStorage 等）+ LLM 把代码改写成规范概念查询，统一 LLM 重排后交 grade 过滤。

## 快速启动

要求：Python ≥ 3.11（推荐 uv）、Node ≥ 18、一个 OpenAI 兼容的 LLM/Embedding API（默认阿里云百炼）。

```bash
# 1. 配置环境变量
cp .env.example .env        # 填入 EMBEDDING_API_KEY（chat 未配置时复用同一平台）

# 2. 后端
cd backend
uv sync                     # 或 python -m venv .venv && pip install -e .
.venv/Scripts/python -m retrieval.ingest   # 语料 → 69 chunks → index.faiss（Windows）
# macOS/Linux: uv run python -m retrieval.ingest
.venv/Scripts/python -m uvicorn main:app --port 8000

# 3. 前端（新终端）
cd frontend
npm install
npm run dev                 # http://localhost:5173
```

冒烟测试：`cd backend && uv run pytest tests/ -s`

## 可插拔语料

检索层与 LangGraph 图只面向统一的 `Chunk` 接口（id / doc_title / section / anchor / content），不知道语料来源。**换语料 = 改 `backend/corpus/corpus.yaml` + 重跑 ingest，业务代码零改动。**

```yaml
# backend/corpus/corpus.yaml
sources:
  - type: fs_md          # 文件夹 Markdown 适配器（按标题层级分块，保留 anchor）
    source_id: public-specs
    path: corpus-data/specs
    enabled: true
  # 公司语料：路径经环境变量注入，不写入本文件、不入 git
  # - type: company
  #   source_id: company-specs
  #   path_env: COMPANY_CORPUS_PATH
  #   enabled: true
```

新增适配器只需实现 `CorpusProvider` Protocol（`load() -> list[Chunk]`），见 `backend/corpus/provider.py`。

## 评测

```bash
cd backend
.venv/Scripts/python ../eval/run.py                  # 全量评测（含 LLM 生成与 judge）
.venv/Scripts/python ../eval/run.py --retrieval-only # 只测检索命中率
```

20 题 = 10 事实型 + 5 多跳型 + 5 代码审查型。最新结果（`eval/report.md`）：

| 指标 | 结果 |
|------|------|
| 检索 hit@1 | **95%**（19/20） |
| 检索 hit@3 | **100%**（20/20） |
| 多跳 full-recall | **100%** |
| 引用准确率 | **15/15**（角标全部指向真实条款） |
| LLM-as-judge | **4.9 / 5** |
| 审查条款命中 / 关键词覆盖 | **5/5 / 5/5** |

评测驱动的关键调优：review 检索四路并集修复 `as any` 被截断、纯中文条款被挤出的问题；LLM 重排修复 hit@1 排序差 1-3 名的边界案例；judge 喂实际引用条款并禁止外部知识，均分 4.2 → 4.9。

## 演示脚本（5 分钟）

1. **规范问答**：提问"组件的 props 应该怎么设计？"→ 流式回答带 `[1]` 角标，hover 弹出条款原文；展开思考过程面板
2. **代码审查**：切审查模式，贴含 `v-html` + `as any` 的 Vue 片段 → 返回分级违规清单，每条附条款引用
3. **诚实兜底**：问一个规范外的问题（如"周末加班有调休吗"）→ 回答"该问题规范未覆盖"并列出最相近条款
4. **评测报告**：打开 `eval/report.md`，出示 hit@1 95% / judge 4.9 等数字
5. **换语料现场演示**（能力与语料解耦的证明）：
   ```bash
   # ① 把 corpus.yaml 的 path 改为 corpus-data/demo-alt-specs（2 篇团队规范）
   # ② 重跑索引
   cd backend && .venv/Scripts/python -m retrieval.ingest   # 2 篇 → 4 chunks
   # ③ 重启服务后提问"分支怎么命名？"→ 立即按新语料回答
   # ④ 演示完把 path 改回 corpus-data/specs 重跑 ingest 还原
   ```
   全程不改任何业务代码；已演练验证（2 篇备用语料 → 4 chunks，检索/问答链路复用不变）。
