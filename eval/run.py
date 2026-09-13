"""评测脚本：检索命中率 + 引用准确率 + LLM-as-judge + 代码审查覆盖，产出 report.md。

指标定义：
- hit@k：期望 chunk 出现在检索 top-k 中（hit@1 按"top-1 命中任一期望条款"计）
- 检索直测为管道口径：复用图内 retrieve 节点（含 rerank / 词面增强），与线上行为一致
- 引用准确率：回答中 [n] 角标均能对应到 sources，且至少一个角标（"规范未覆盖"兜底另计）
- 审查通过：期望条款进入 sources 且 violation_keywords 全部出现在违规输出中
- LLM-as-judge：qwen-plus 按"覆盖参考要点/引用规范/无编造"打 1-5 分

运行：backend 目录下 .venv/Scripts/python ../eval/run.py [--limit N] [--retrieval-only]
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))  # noqa: E402

from graph.build import graph  # noqa: E402
from graph.nodes import retrieve  # noqa: E402
from llm import CHAT_MODEL, chat_client  # noqa: E402

QUESTIONS = yaml.safe_load((ROOT / "eval" / "questions.yaml").read_text(encoding="utf-8"))["questions"]


def parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text[text.find("{") : text.rfind("}") + 1])


def run_graph(mode: str, question: str) -> dict:
    """跑一遍图，聚合 custom 事件 → sources / answer / review_items。"""
    out = {"sources": [], "tokens": [], "review_items": []}
    for ev in graph.stream({"mode": mode, "question": question, "top_k": 5}, stream_mode="custom"):
        if ev["type"] == "sources":
            out["sources"] = ev["sources"]
        elif ev["type"] == "token":
            out["tokens"].append(ev["content"])
        elif ev["type"] == "review_item":
            out["review_items"].append(ev["item"])
    out["answer"] = "".join(out.pop("tokens"))
    return out


def judge_answer(
    question: str, answer: str, points: str, sources: list[dict]
) -> tuple[int, str]:
    clauses = "\n\n".join(
        f"[{s['n']}]《{s['doc_title']}》{s['section']}\n{s['content'][:300]}"
        for s in sources
    )
    prompt = (
        "你是问答质量评审。依据【参考要点】和【实际引用条款】评估回答，"
        "不得引入条款与要点之外的外部知识（如官方文档）。评分维度："
        "1) 回答是否与要点一致；2) 是否严格依据条款、无编造；3) 角标 [n] 是否指向真实条款。"
        "输出 JSON：{\"score\": 1-5, \"reason\": \"一句话\"}\n\n"
        f"问题：{question}\n参考要点：{points}\n实际引用条款：\n{clauses}\n回答：{answer[:1200]}"
    )
    try:
        resp = chat_client().chat.completions.create(
            model=CHAT_MODEL,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        data = parse_json(resp.choices[0].message.content)
        return int(data.get("score", 0)), str(data.get("reason", ""))
    except Exception as exc:  # noqa: BLE001 —— judge 失败不阻断评测
        return 0, f"judge 失败: {exc}"


def check_citations(answer: str, sources: list[dict]) -> str:
    """返回 ok / fallback / bad。"""
    if "规范未覆盖" in answer and not sources:
        return "fallback"
    nums = [int(n) for n in re.findall(r"\[(\d{1,2})\]", answer)]
    if nums and all(1 <= n <= len(sources) for n in nums):
        return "ok"
    return "bad"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="只跑前 N 题（调试用）")
    ap.add_argument("--retrieval-only", action="store_true", help="只测检索命中率，不跑 LLM")
    args = ap.parse_args()
    questions = QUESTIONS[: args.limit] if args.limit else QUESTIONS

    rows: list[dict] = []
    for i, q in enumerate(questions, 1):
        expected = q["expected_chunks"]
        row: dict = {"id": q["id"], "type": q["type"]}

        # --- 检索命中率（管道口径：复用 retrieve 节点，含 rerank / 词面增强） ---
        mode = "review" if q["type"] == "review" else "chat"
        cands = retrieve({"mode": mode, "question": q["question"], "top_k": 5})["candidates"]
        hits = [c["id"] for c in cands]
        row["hit1"] = bool(hits) and hits[0] in expected
        row["hit3"] = any(h in expected for h in hits[:3])
        row["recall"] = sum(h in expected for h in hits) / len(expected)

        if q["type"] == "review" and not args.retrieval_only:
            res = run_graph("review", q["question"])
            src_ids = [s["id"] for s in res["sources"]]
            row["src_hit"] = any(e in src_ids for e in expected)
            text = json.dumps(res["review_items"], ensure_ascii=False).lower()
            missing = [k for k in q.get("violation_keywords", []) if k.lower() not in text]
            row["kw_ok"] = not missing
            row["note"] = f"{len(res['review_items'])} 项违规" + (f"；缺关键词: {missing}" if missing else "")
        elif q["type"] != "review" and not args.retrieval_only:
            res = run_graph("chat", q["question"])
            row["cite"] = check_citations(res["answer"], res["sources"])
            row["judge"], reason = judge_answer(
                q["question"], res["answer"], q["expected_points"], res["sources"]
            )
            row["note"] = reason

        status = (
            "✓" if (row.get("src_hit") and row.get("kw_ok")) else "✗"
        ) if q["type"] == "review" else ("✓" if (row["hit1"] or row["hit3"]) else "✗")
        print(f"[{i}/{len(questions)}] {row['id']} {status} {row.get('note', '')}")
        rows.append(row)

    write_report(rows, retrieval_only=args.retrieval_only)
    print("报告已写入 eval/report.md")


def write_report(rows: list[dict], retrieval_only: bool) -> None:
    n = len(rows) or 1
    chat_rows = [r for r in rows if r["type"] != "review"]
    review_rows = [r for r in rows if r["type"] == "review"]

    def pct(hit: int) -> str:
        return f"{hit}/{n}（{hit / n * 100:.0f}%）"

    lines = ["# 前端工程规范问答 Agent 评测报告", ""]
    lines.append("## 汇总")
    lines.append(f"- 检索 hit@1：**{pct(sum(r['hit1'] for r in rows))}**")
    lines.append(f"- 检索 hit@3：**{pct(sum(r['hit3'] for r in rows))}**")
    lines.append(f"- 多跳 full-recall 均值：**{sum(r['recall'] for r in rows) / n:.0%}**")
    if not retrieval_only:
        lines.append(f"- 引用准确率（ok/fallback）：**{sum(r.get('cite') in ('ok', 'fallback') for r in chat_rows)}/{len(chat_rows)}**")
        judges = [r["judge"] for r in chat_rows if r.get("judge")]
        if judges:
            lines.append(f"- LLM-as-judge 均分：**{sum(judges) / len(judges):.1f} / 5**")
        if review_rows:
            lines.append(f"- 审查条款命中：**{sum(r.get('src_hit', False) for r in review_rows)}/{len(review_rows)}**")
            lines.append(f"- 审查关键词覆盖：**{sum(r.get('kw_ok', False) for r in review_rows)}/{len(review_rows)}**")
    lines.append("")

    lines.append("## 明细")
    lines.append("| id | 类型 | hit@1 | hit@3 | recall | 引用 | judge | 条款命中 | 关键词 | 说明 |")
    lines.append("|----|------|-------|-------|--------|------|-------|----------|--------|------|")
    for r in rows:
        src = "-" if r["type"] != "review" else ("✓" if r.get("src_hit") else "✗")
        kw = "-" if r["type"] != "review" else ("✓" if r.get("kw_ok") else "✗")
        lines.append(
            f"| {r['id']} | {r['type']} | {'✓' if r['hit1'] else '✗'} "
            f"| {'✓' if r['hit3'] else '✗'} | {r['recall']:.0%} "
            f"| {r.get('cite', '-')} | {r.get('judge', '-')} | {src} | {kw} | {r.get('note', '')} |"
        )
    (ROOT / "eval" / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
