"""FastAPI 入口：两个 NDJSON 流式端点（fetch + ReadableStream 消费）。

事件格式（每事件一行 JSON + 空行）：
    {"type": "token", "content": "..."}       回答增量
    {"type": "reasoning", "content": "..."}   思考过程增量
    {"type": "sources", "sources": [...]}     编号条款（角标 hover 卡片）
    {"type": "review_item", "item": {...}}    审查违规项
    {"type": "error", "message": "..."}       错误兜底（流式链路异常时不静默断流）

运行：backend 目录下 .venv/Scripts/python -m uvicorn main:app --port 8000
"""
import json
from collections.abc import Iterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from graph.build import graph

app = FastAPI(title="前端工程规范问答 Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskBody(BaseModel):
    question: str = Field(min_length=1, max_length=8000)
    top_k: int = Field(default=5, ge=1, le=10)


def stream_events(mode: str, body: AskBody) -> Iterator[str]:
    """消费 LangGraph custom 事件流 → NDJSON。异常转 error 事件，避免静默断流。"""
    try:
        for ev in graph.stream(
            {"mode": mode, "question": body.question, "top_k": body.top_k},
            stream_mode="custom",
        ):
            yield json.dumps(ev, ensure_ascii=False) + "\n\n"
    except Exception as exc:  # noqa: BLE001 —— 流式链路的最后兜底
        yield json.dumps({"type": "error", "message": str(exc)}, ensure_ascii=False) + "\n\n"


@app.post("/api/chat/stream")
def chat_stream(body: AskBody):
    from fastapi.responses import StreamingResponse

    return StreamingResponse(
        stream_events("chat", body), media_type="text/event-stream"
    )


@app.post("/api/review/stream")
def review_stream(body: AskBody):
    from fastapi.responses import StreamingResponse

    return StreamingResponse(
        stream_events("review", body), media_type="text/event-stream"
    )


@app.get("/api/health")
def health():
    return {"status": "ok"}
