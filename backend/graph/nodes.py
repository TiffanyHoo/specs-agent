"""LangGraph 节点：retrieve → grade →（generate | review）。

流式约定：节点内通过 get_stream_writer() 发射事件，
API 层以 graph.stream(state, stream_mode="custom") 消费：
    {"type": "token", "content": str}       回答增量
    {"type": "reasoning", "content": str}   思考过程增量
    {"type": "sources", "sources": [...]}   编号条款（角标 hover 卡片数据源）
    {"type": "review_item", "item": {...}}  审查违规项（逐条）
"""
import json

from langgraph.config import get_stream_writer

from graph.prompts import (
    REVIEW_OUTPUT_SCHEMA,
    SYSTEM_GRADE,
    SYSTEM_QA,
    SYSTEM_RERANK,
    SYSTEM_REVIEW,
    SYSTEM_REWRITE,
)
from graph.state import AgentState, SourceChunk
from llm import CHAT_MODEL, CHAT_REASONING_MODEL, chat_client


def _parse_json(text: str) -> dict:
    """容错解析 LLM 输出的 JSON（剥离代码围栏等）。"""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"LLM 输出中未找到 JSON: {text[:200]}")
    return json.loads(text[start : end + 1])


def _format_sources(sources: list[SourceChunk]) -> str:
    return "\n\n".join(
        f"[{s['n']}]《{s['doc_title']}》{s['section']}\n{s['content']}"
        for s in sources
    )


def _lexical_boost(terms: set[str], content: str, chunk_id: str = "") -> float:
    """词面信号加权：条款内容/ID 命中的查询标识符越多加分越多（封顶 3 个）。"""
    hay = (content + chunk_id).lower()
    return min(sum(1 for t in terms if t in hay), 3) * 0.1


def _rerank(question: str, candidates: list[SourceChunk], top_n: int | None = None) -> list[SourceChunk]:
    """LLM 重排：按与问题的相关性对候选条款排序；失败时保持原序。

    top_n 非 None 时裁剪到前 top_n 条（问答模式），None 时只排序不裁剪（审查模式，
    后续 grade 节点负责过滤，裁剪会丢掉词面补充进来的有效条款）。
    """
    if len(candidates) <= 1:
        return candidates[:top_n] if top_n else candidates
    lines = "\n\n".join(
        f"[{i}]《{c['doc_title']}》{c['section']}\n{c['content'][:200]}"
        for i, c in enumerate(candidates, 1)
    )
    try:
        resp = chat_client().chat.completions.create(
            model=CHAT_MODEL,
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_RERANK},
                {"role": "user", "content": f"问题：{question[:500]}\n\n条款：\n{lines}"},
            ],
        )
        order = _parse_json(resp.choices[0].message.content).get("order", [])
        ranked = [candidates[i - 1] for i in order if isinstance(i, int) and 1 <= i <= len(candidates)]
        seen = {c["id"] for c in ranked}
        ranked += [c for c in candidates if c["id"] not in seen]  # 漏排的候选拼回尾部，只增不减
    except Exception:  # noqa: BLE001 —— 重排失败不阻断检索
        ranked = list(candidates)
    return ranked[:top_n] if top_n else ranked


def _rewrite_review_query(question: str) -> str | None:
    """把待审查代码改写成规范概念查询（如"组件体积 拆分 单一职责"）。

    弥补无拉丁标识符可词面匹配的场景（如"900 行单文件组件"），失败时返回 None。
    """
    try:
        resp = chat_client().chat.completions.create(
            model=CHAT_MODEL,
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_REWRITE},
                {"role": "user", "content": question[:800]},
            ],
        )
        query = str(_parse_json(resp.choices[0].message.content).get("query", "")).strip()
        return query or None
    except Exception:  # noqa: BLE001 —— 改写失败不阻断检索
        return None


def retrieve(state: AgentState) -> dict:
    """向量检索召回候选条款，并做 LLM 重排。

    审查模式下做两件事弥补 dense embedding 对代码的弱势：
    1. 查询构造：剥掉代码围栏，加审查意图前缀，头部 400 + 尾部 200（尾部含关键 token）；
    2. 词面增强 + 查询改写：提取代码中的拉丁标识符（any / v-html / localStorage 等），
       从 dense 池 9-20 名中补充词面命中最多的 5 条；再用 LLM 把代码改写成规范概念
       查询补召回（覆盖无词面信号的违规，如"900 行单文件组件"）。
    多路并集（前缀查询 + 原始问题 + 词面补充 + 改写查询）只增不减，最终统一 rerank。
    """
    import re

    from retrieval.search import retriever

    if state["mode"] == "review":
        cleaned = state["question"].replace("```", "").strip()
        prefixed = (
            "审查以下前端代码，找出违反前端工程规范的点（安全、类型、命名、组件体积等）：\n"
            f"{cleaned[:400]} ... {cleaned[-200:]}"
        )
        top_k = max(state.get("top_k", 5), 8)
        terms = {t.lower() for t in re.findall(r"[A-Za-z_][A-Za-z0-9_-]+", cleaned) if len(t) >= 2}

        pool = retriever.search(prefixed, top_k=20)
        merged: dict[str, object] = {r.chunk.id: r for r in pool[:top_k]}
        for r in retriever.search(state["question"][:300], top_k=8):
            merged.setdefault(r.chunk.id, r)
        extras = sorted(
            pool[top_k:],
            key=lambda r: _lexical_boost(terms, r.chunk.content, r.chunk.id),
            reverse=True,
        )[:5]
        for e in extras:
            if _lexical_boost(terms, e.chunk.content, e.chunk.id) > 0:
                merged.setdefault(e.chunk.id, e)
        rewritten = _rewrite_review_query(cleaned)
        if rewritten:
            for r in retriever.search(rewritten, top_k=8):
                merged.setdefault(r.chunk.id, r)
        results = list(merged.values())
    else:
        top_k = state.get("top_k", 5)
        results = retriever.search(state["question"], top_k=top_k * 2)

    candidates: list[SourceChunk] = []
    seen: set[str] = set()
    for r in results:
        if r.chunk.id in seen:
            continue
        seen.add(r.chunk.id)
        candidates.append(
            {
                "n": 0,
                "id": r.chunk.id,
                "doc_title": r.chunk.doc_title,
                "section": r.chunk.section,
                "content": r.chunk.content,
                "score": r.score,
            }
        )

    if state["mode"] == "review":
        candidates = _rerank(state["question"], candidates)
    else:
        candidates = _rerank(state["question"], candidates, top_n=top_k)
    return {"candidates": candidates}


def grade(state: AgentState) -> dict:
    """LLM 相关性过滤：保留真正支撑回答的条款，并重新编号为 1..k。"""
    if not state["candidates"]:
        return {"sources": [], "covered": False}

    lines = "\n\n".join(
        f"[{i}]《{c['doc_title']}》{c['section']}\n{c['content'][:300]}"
        for i, c in enumerate(state["candidates"], 1)
    )
    resp = chat_client().chat.completions.create(
        model=CHAT_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_GRADE},
            {"role": "user", "content": f"问题：{state['question'][:500]}\n\n条款：\n{lines}"},
        ],
    )
    relevant = set(_parse_json(resp.choices[0].message.content).get("relevant", []))

    sources: list[SourceChunk] = []
    for n, c in enumerate(state["candidates"], 1):
        if n in relevant:
            sources.append({**c, "n": len(sources) + 1})
    get_stream_writer()({"type": "sources", "sources": sources})
    return {"sources": sources, "covered": bool(sources)}


def generate(state: AgentState) -> dict:
    """问答生成：流式输出 token / reasoning；规范未覆盖时走诚实兜底。"""
    writer = get_stream_writer()

    if not state["covered"]:
        hint = "、".join(c["section"] for c in state["candidates"]) or "无相近条款"
        answer = (
            "该问题规范未覆盖。知识库中没有足以回答的条款，"
            f"最相近的内容涉及：{hint}。建议补充相应规范后重试。"
        )
        writer({"type": "token", "content": answer})
        return {"answer": answer}

    messages = [
        {"role": "system", "content": SYSTEM_QA.format(sources=_format_sources(state["sources"]))},
        {"role": "user", "content": state["question"]},
    ]
    answer, reasoning = _stream_llm(writer, messages, thinking=True)
    return {"answer": answer, "reasoning": reasoning}


def review(state: AgentState) -> dict:
    """代码审查：结构化输出违规清单，逐条发射 review_item 事件。"""
    writer = get_stream_writer()
    if not state["covered"]:
        items: list[dict] = []
        writer({"type": "review_item", "item": {"uncovered": True}})
        return {"review_items": items}

    resp = chat_client().chat.completions.create(
        model=CHAT_MODEL,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_REVIEW.format(sources=_format_sources(state["sources"]))
                + "\n\n" + REVIEW_OUTPUT_SCHEMA,
            },
            {"role": "user", "content": f"待审查代码：\n{state['question']}"},
        ],
    )
    violations = _parse_json(resp.choices[0].message.content).get("violations", [])
    by_n = {s["n"]: s for s in state["sources"]}
    items = []
    for v in violations:
        clause = by_n.get(v.get("clause"))
        item = {
            "clause_n": v.get("clause"),
            "clause_id": clause["id"] if clause else None,
            "section": clause["section"] if clause else None,
            "severity": v.get("severity", "medium"),
            "issue": v.get("issue", ""),
            "quote": v.get("quote", ""),
            "suggestion": v.get("suggestion", ""),
        }
        items.append(item)
        writer({"type": "review_item", "item": item})
    return {"review_items": items}


def _stream_llm(
    writer, messages: list[dict], thinking: bool
) -> tuple[str, str]:
    """流式调用 LLM：返回 (answer, reasoning)。

    thinking=True 时请求开启思考过程（qwen3 enable_thinking），
    若模型不支持该参数则自动降级为普通调用。
    """
    client = chat_client()
    answer, reasoning = "", ""
    try:
        stream = client.chat.completions.create(
            model=CHAT_REASONING_MODEL,
            messages=messages,
            stream=True,
            extra_body={"enable_thinking": True} if thinking else None,
        )
    except Exception:
        stream = client.chat.completions.create(
            model=CHAT_MODEL, messages=messages, stream=True
        )
    for chunk in stream:
        delta = chunk.choices[0].delta
        rc = getattr(delta, "reasoning_content", None)
        if rc:
            reasoning += rc
            writer({"type": "reasoning", "content": rc})
        if delta.content:
            answer += delta.content
            writer({"type": "token", "content": delta.content})
    return answer, reasoning
