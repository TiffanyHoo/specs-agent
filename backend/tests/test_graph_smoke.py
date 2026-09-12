"""Agent 管道冒烟测试（依赖真实 embedding + LLM API）。

运行：backend 目录下 .venv/Scripts/python -m pytest tests/test_graph_smoke.py -s
"""
from graph.build import graph


def run(state: dict) -> list[dict]:
    return list(graph.stream(state, stream_mode="custom"))


def test_chat_mode_streams_tokens_and_sources():
    events = run({"mode": "chat", "question": "组件的 props 有什么设计要求？", "top_k": 5})
    types = [e["type"] for e in events]
    assert "sources" in types, "缺少 sources 事件"
    assert "token" in types, "缺少 token 流式事件"
    sources = next(e["sources"] for e in events if e["type"] == "sources")
    assert sources and sources[0]["n"] == 1
    answer = "".join(e["content"] for e in events if e["type"] == "token")
    print("\n回答:", answer)
    assert "[1]" in answer, "回答中未发现引用角标"


def test_review_mode_outputs_violations():
    code = """```ts
// 保存登录态
const token = localStorage.setItem('token', rawToken)
// 用户列表渲染
{list.map((item, idx) => <div v-for={(item, idx) in list} key={idx}>{item.name}</div>)}
```"""
    events = run({"mode": "review", "question": code, "top_k": 5})
    types = [e["type"] for e in events]
    assert "review_item" in types, "缺少 review_item 事件"
    items = [e["item"] for e in events if e["type"] == "review_item"]
    assert not any(i.get("uncovered") for i in items), "审查模式误判为规范未覆盖"
    for i in items:
        print(f"\n[{i['severity']}] {i['section']}: {i['issue']} -> {i['suggestion']}")
    assert len(items) >= 1
