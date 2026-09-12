"""LangGraph 图装配：单张 4 节点小图，按 mode 分支到 generate 或 review。"""
from langgraph.graph import END, START, StateGraph

from graph.nodes import generate, grade, retrieve, review
from graph.state import AgentState


def _route_after_grade(state: AgentState) -> str:
    return "review" if state["mode"] == "review" else "generate"


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("retrieve", retrieve)
    g.add_node("grade", grade)
    g.add_node("generate", generate)
    g.add_node("review", review)

    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "grade")
    g.add_conditional_edges("grade", _route_after_grade)
    g.add_edge("generate", END)
    g.add_edge("review", END)
    return g.compile()


# 进程级单例：API 层导入使用
graph = build_graph()
