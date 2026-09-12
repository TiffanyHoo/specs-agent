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

from graph.prompts import REVIEW_OUTPUT_SCHEMA, SYSTEM_GRADE, SYSTEM_QA, SYSTEM_REVIEW
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


def retrieve(state: AgentState) -> dict:
    """向量检索召回候选条款（审查模式下截断长代码，避免污染查询向量）。"""
    from retrieval.search import retriever

    query = state["question"]
    if state["mode"] == "review":
        query = query[:300]
    results = retriever.search(query, top_k=state.get("top_k", 5))

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
