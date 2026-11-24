#!/usr/bin/env python3
"""Render the current task's token.json into its 00-overview.md.

Run the matching entrypoint once from the project root during SOP Commit
preparation, before boundary A / git add:

    # CodeBuddy / Cursor
    python3 .codebuddy/scripts/token_report.py
    # Codex
    python3 .codex/scripts/token_report.py

Both entrypoints use this same source and report all clients' records from the
task's ``token.json``. The committed table is one row per user turn: Codex and
CodeBuddy model calls inside a turn are summed, while a Cursor generation is
already one turn and is not summed again. When the Codex collector is installed,
refresh its logs already bound to this task before rendering; otherwise skip
that refresh.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

START = "<!-- TOKEN_USAGE_START -->"
END = "<!-- TOKEN_USAGE_END -->"
TOKEN_FILE_NAME = "token.json"

# Kept inline (not imported from _token_common) because this script is copied
# standalone into .codebuddy/scripts/ and .codex/scripts/ without a hooks-dir import.
CLIENT_CODEBUDDY = "codebuddy"
CLIENT_CURSOR = "cursor"
CLIENT_CODEX = "codex"
CLIENT_CLAUDE = "claude"
CODEBUDDY_SOURCES = ("ide_index", "cli_jsonl")


def as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def as_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def token_work_disabled(branch: str) -> bool:
    name = (branch or "").strip()
    if name in ("master", "main"):
        return True
    return name == "release" or name.startswith("release/")


def git_branch(repo: Path) -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "branch", "--show-current"],
                cwd=str(repo),
                stderr=subprocess.DEVNULL,
                timeout=3,
            )
            .decode("utf-8", errors="replace")
            .strip()
        )
    except Exception:
        return ""


def find_repo(start: Path) -> Path | None:
    cur = start.resolve()
    while True:
        if (cur / ".wally").is_dir():
            return cur
        if cur.parent == cur:
            return None
        cur = cur.parent


def find_overview(repo: Path, branch: str) -> Path | None:
    candidates = []
    for path in (repo / ".wally" / "plans").glob("*/00-overview.md"):
        if path.parent.name.startswith(("_", ".")):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        match = re.search(r"\|\s*(?:Branch|\u5206\u652f)\s*\|\s*`?([^`\n\r|]+)`?\s*\|", text)
        if match and match.group(1).strip() == branch:
            candidates.append(path)
    if not candidates:
        return None
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0]


def load_requests(path: Path) -> list[dict]:
    try:
        store = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    requests = store.get("requests") if isinstance(store, dict) else None
    if not isinstance(requests, list):
        return []
    selected = [item for item in requests if isinstance(item, dict)]
    selected.sort(
        key=lambda item: (as_int(item.get("started_at")), item.get("request_id", ""))
    )
    return selected


def format_time(value: Any) -> str:
    number = as_int(value)
    if not number:
        return "—"
    # IDE/CLI timestamps are milliseconds since epoch.
    if number > 10_000_000_000:
        number /= 1000
    try:
        return datetime.fromtimestamp(number).strftime("%Y-%m-%d %H:%M:%S")
    except (OSError, OverflowError, ValueError):
        return str(value)


def markdown_prompt(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return "_未提取到 prompt_"
    return (
        text.replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "<br>")
    )


def format_credit(value: float) -> str:
    return f"{value:.2f}" if value else "—"


def client_label(item: dict) -> str:
    """Resolve the client for a record, tolerating pre-`client` CodeBuddy rows."""
    client = str(item.get("client") or "").strip()
    if client == CLIENT_CURSOR:
        return "Cursor"
    if client == CLIENT_CLAUDE:
        return "Claude"
    if client == CLIENT_CODEX:
        if item.get("agent_type") == "guardian":
            return "Codex / guardian 审批代理"
        return "Codex / 子代理" if item.get("agent_kind") == "subagent" else "Codex / 主会话"
    if client == CLIENT_CODEBUDDY or item.get("source") in CODEBUDDY_SOURCES:
        return "CodeBuddy"
    return "—"


def _usage(item: dict) -> dict:
    usage = item.get("usage")
    return usage if isinstance(usage, dict) else {}


def record_client(item: dict) -> str:
    """Client identity. CodeBuddy rows written before ``client`` existed keep only ``source``."""
    client = str(item.get("client") or "").strip()
    if client in (CLIENT_CURSOR, CLIENT_CODEX, CLIENT_CODEBUDDY, CLIENT_CLAUDE):
        return client
    if item.get("source") in CODEBUDDY_SOURCES:
        return CLIENT_CODEBUDDY
    return client or str(item.get("source") or "")


def _same_codebuddy_run(previous: dict, item: dict) -> bool:
    """True when two ledger rows are consecutive steps of one user prompt."""
    if record_client(previous) != record_client(item) or record_client(item) == CLIENT_CURSOR:
        return False
    prompt = str(item.get("prompt") or "").strip()
    if not prompt or prompt != str(previous.get("prompt") or "").strip():
        return False
    return str(item.get("session_id") or "") == str(previous.get("session_id") or "")


def rollup_turns(requests: list[dict]) -> list[dict]:
    """Collapse the per-request ledger into one row per user turn.

    Cursor is already one ``generation_id`` and must not be summed. Codex model
    calls that share a thread and ``root_turn_id`` are one turn. CodeBuddy has
    no turn id, so a contiguous run with the same session and prompt is one turn.
    Each of those calls reports its own final usage, so the turn total is a sum.
    """
    groups: list[list[dict]] = []
    codex_groups: dict[tuple, list[dict]] = {}
    for item in requests:
        if item.get("client") == CLIENT_CURSOR:
            groups.append([item])
            continue
        root_turn = str(item.get("root_turn_id") or "")
        if item.get("client") == CLIENT_CODEX and root_turn:
            key = (
                str(item.get("session_id") or ""),
                str(item.get("thread_id") or ""),
                str(item.get("agent_kind") or ""),
                str(item.get("agent_type") or ""),
                root_turn,
            )
            bucket = codex_groups.get(key)
            if bucket is None:
                bucket = []
                codex_groups[key] = bucket
                groups.append(bucket)
            bucket.append(item)
            continue
        previous = groups[-1][-1] if groups else None
        if previous is not None and _same_codebuddy_run(previous, item):
            groups[-1].append(item)
            continue
        groups.append([item])
    return [_merge_turn(group) for group in groups]


def _merge_turn(group: list[dict]) -> dict:
    if len(group) == 1:
        return group[0]
    usage = {
        "input_tokens": 0,
        "uncached_input_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "credit": 0.0,
    }
    reasoning = None
    models: list[str] = []
    prompt = ""
    started = None
    for item in group:
        raw = _usage(item)
        for key in usage:
            if key == "credit":
                usage[key] += as_float(raw.get(key))
            else:
                usage[key] += as_int(raw.get(key))
        if "reasoning_output_tokens" in raw:
            reasoning = as_int(reasoning) + as_int(raw.get("reasoning_output_tokens"))
        model = str(item.get("model") or "").strip()
        if model and model not in models:
            models.append(model)
        if not prompt and str(item.get("prompt") or "").strip():
            prompt = str(item.get("prompt") or "")
        stamp = as_int(item.get("started_at"))
        if stamp and (started is None or stamp < started):
            started = stamp
    if reasoning is not None:
        usage["reasoning_output_tokens"] = reasoning
    merged = dict(group[0])
    merged["prompt"] = prompt or group[0].get("prompt") or ""
    merged["model"] = " / ".join(models) if models else group[0].get("model")
    if started is not None:
        merged["started_at"] = started
    merged["usage"] = usage
    merged["_calls"] = len(group)
    return merged


def render(requests: list[dict], token_rel: str, collection: dict | None = None,
           warning: str = "") -> str:
    rows = []
    totals: dict[str, float] = {
        "input_tokens": 0,
        "uncached_input_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
        "total_tokens": 0,
        "credit": 0.0,
    }
    turns = rollup_turns(requests)
    for index, item in enumerate(turns, 1):
        usage = _usage(item)
        for key in totals:
            if key == "credit":
                if item.get("client") not in (CLIENT_CODEX, CLIENT_CLAUDE):
                    totals[key] += as_float(usage.get(key))
            else:
                totals[key] += as_int(usage.get(key))
        prompt = markdown_prompt(item.get("prompt"))
        calls = as_int(item.get("_calls"))
        if calls > 1:
            prompt += f"<br>_本轮 {calls} 次模型调用已汇总_"
        rows.append(
            "| {idx} | {client} | {time} | {prompt} | `{model}` | {inp:,} | "
            "{miss:,} | {read:,} | {write:,} | {out:,} | {reasoning} | {total:,} | {credit} |\n".format(
                idx=index,
                client=client_label(item),
                time=format_time(item.get("started_at")),
                prompt=prompt,
                model=str(item.get("model") or "unknown").replace("|", "\\|"),
                inp=as_int(usage.get("input_tokens")),
                miss=as_int(usage.get("uncached_input_tokens")),
                read=as_int(usage.get("cache_read_tokens")),
                write=as_int(usage.get("cache_write_tokens")),
                out=as_int(usage.get("output_tokens")),
                reasoning=(f'{as_int(usage["reasoning_output_tokens"]):,}'
                           if "reasoning_output_tokens" in usage else "—"),
                total=as_int(usage.get("total_tokens")),
                credit=("—" if item.get("client") in (CLIENT_CODEX, CLIENT_CLAUDE)
                        else format_credit(as_float(usage.get("credit")))),
            )
        )

    if not rows:
        rows.append("| _未采集到记录_ | — | — | — | — | — | — | — | — | — | — | — | — |\n")
    else:
        summary = f"记录数：{len(turns)} 轮"
        if len(turns) != len(requests):
            summary += f"（模型请求 {len(requests)}）"
        rows.append(
            "| **累计** | — | — | **{}** | — | {:,} | {:,} | {:,} | {:,} | "
            "{:,} | {:,} | **{:,}** | **{}** |\n".format(
                summary,
                int(totals["input_tokens"]),
                int(totals["uncached_input_tokens"]),
                int(totals["cache_read_tokens"]),
                int(totals["cache_write_tokens"]),
                int(totals["output_tokens"]),
                int(totals["reasoning_output_tokens"]),
                int(totals["total_tokens"]),
                format_credit(totals["credit"]),
            )
        )

    return (
        "{start}\n"
        "| # | 客户端 | 时间 | Prompt | 模型 | 输入合计 | 非缓存输入 | 缓存读 | "
        "缓存写 | 输出 | 其中 reasoning | Tokens | Credit |\n"
        "|---|--------|------|--------|------|----------|------------|--------|"
        "--------|------|----------------|--------|--------|\n"
        "{rows}"
        "\n{health}\n"
        "> 口径：`输入合计 = 非缓存输入 + 缓存读 + 缓存写`；"
        "`Tokens = 输入合计 + 输出`；reasoning 是输出子项，不再次累加。"
        "逐请求明细在本任务 `{token}`，该文件不提交。\n"
        "> 粒度：本表一行 = 一轮用户对话，与 Cursor 的一个 `generation_id` 相同。"
        "Cursor 上报的是整轮累计值，采集时已按最大值去重，这里不再相加。"
        "Codex 按同一线程的 `root_turn_id`、CodeBuddy 按同一会话里 prompt 相同的连续请求，"
        "把该轮多次模型调用的 token **相加**为一行（含每次调用自己的缓存读）。"
        "Codex、Cursor 的 Credit 显示 `—`，不估算费用。\n"
        "> 快照：仅包含生成报告时已落盘且已采集的用量，不包含之后发生的请求。\n"
        "{end}\n"
    ).format(start=START, rows="".join(rows), end=END, token=token_rel,
             health=render_health(requests, collection or {}, warning))


def render_health(requests: list[dict], collection: dict, warning: str) -> str:
    lines = []
    codex = [r for r in requests if r.get("client") == CLIENT_CODEX]
    if codex:
        main = [r for r in codex if r.get("agent_kind") != "subagent" and r.get("agent_type") != "guardian"]
        sub = [r for r in codex if r.get("agent_kind") == "subagent" and r.get("agent_type") != "guardian"]
        guardian = [r for r in codex if r.get("agent_type") == "guardian"]
        count = lambda rows: sum(as_int((r.get("usage") or {}).get("total_tokens")) for r in rows)
        approvals = f"guardian 审批 {len(guardian)} 次模型请求 / {count(guardian):,} tokens；" if guardian else ""
        lines.append(f"> Codex 已观测用量：主会话 {len(main)} 次模型请求 / {count(main):,} tokens；"
                     f"子代理 {len(sub)} 次模型请求 / {count(sub):,} tokens；{approvals}合计 {len(codex)} 次模型请求 / {count(codex):,} tokens。")
    status_labels = {"ok": "已采集快照", "partial": "数据不完整", "missing": "日志缺失",
                     "unsupported": "暂不支持旧版累计日志", "pending": "等待用量落盘"}
    sessions = (collection.get("codex") or {}).get("sessions", {})
    for session, health in sessions.items():
        label = status_labels.get(health.get("status"), "采集状态未知")
        sources = "、".join(f'{x.get("thread_id", "?")}: {status_labels.get(x.get("status"), "未知")}'
                           for x in health.get("sources", []))
        lines.append(f"> Codex 采集状态：{label}（根会话 {session}，截至 {health.get('as_of', '未知')}）。")
        if sources:
            lines.append("> 线程状态：" + sources + "。")
        discovery = health.get("guardian_discovery", {})
        if discovery.get("status") != "ok":
            lines.append("> guardian 发现未完成或尚未核验，当前快照可能遗漏内部审批用量。")
    if not sessions:
        lines.append("> Codex 采集状态：未登记采集状态，不能据此认定用量完整或为零。")
    if warning:
        lines.append("> 采集提示：" + warning)
    if not requests:
        lines.append("> 尚未采集到用量记录；这不表示完整的零消耗。")
    return "\n".join(lines) + "\n"


def refresh_codex(repo: Path, overview: Path) -> str:
    collector = repo / ".codex/hooks/codex_token_collect.py"
    if not collector.is_file():
        return ""
    try:
        result = subprocess.run([sys.executable, str(collector), "--refresh-task", str(overview.parent)],
                                capture_output=True, timeout=10)
        if result.returncode:
            return "Codex 补采未完成，当前数值仅为已保存用量。"
    except (OSError, subprocess.TimeoutExpired):
        return "Codex 补采未完成或超时，当前数值仅为已保存用量。"
    return ""


def patch_overview(path: Path, block: str) -> None:
    text = path.read_text(encoding="utf-8")
    # Older reports left their generated footnotes outside the markers.
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END) +
                         r"\n?(?:\n?> (?:\u53e3\u5f84|\u7c92\u5ea6)\uff1a[^\n]*\n?)*", re.DOTALL)
    if not pattern.search(text):
        raise RuntimeError(f"{path} 缺少 Token marker")
    updated, count = pattern.subn(lambda _: block.rstrip("\n") + "\n", text, count=1)
    if count != 1:
        raise RuntimeError(f"{path} Token marker 不唯一")
    path.write_text(updated, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", nargs="?", default=None)
    parser.add_argument("--branch")
    parser.add_argument("--overview")
    args = parser.parse_args()

    start = Path(
        args.repo
        or os.environ.get("CODEBUDDY_PROJECT_DIR")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.environ.get("CURSOR_PROJECT_DIR")
        or os.getcwd()
    )
    repo = find_repo(start)
    if repo is None:
        print("[ERROR] 找不到 .wally 目录", file=sys.stderr)
        return 1
    branch = args.branch or git_branch(repo)
    if token_work_disabled(branch):
        print(f"[SKIP] 当前分支 {branch!r} 不做 Token 汇总", file=sys.stderr)
        return 0
    overview = Path(args.overview) if args.overview else find_overview(repo, branch)
    if overview is None:
        print(f"[ERROR] 找不到分支 {branch!r} 对应的 00-overview.md", file=sys.stderr)
        return 1

    token_file = overview.parent / TOKEN_FILE_NAME
    warning = refresh_codex(repo, overview)
    collection = {}
    try:
        store = json.loads(token_file.read_text(encoding="utf-8"))
        if not isinstance(store, dict) or not isinstance(store.get("requests"), list):
            raise ValueError("invalid token store")
        collection = store.get("collection") or {}
        if not isinstance(collection, dict):
            collection = {}
            raise ValueError("invalid collection status")
    except (OSError, ValueError):
        warning += " 用量文件缺失或无法读取，不能认定为零消耗。"
    requests = load_requests(token_file)
    token_rel = "token.json"
    patch_overview(overview, render(requests, token_rel, collection, warning.strip()))
    total = sum(
        as_int((item.get("usage") or {}).get("total_tokens")) for item in requests
    )
    credit = sum(
        as_float((item.get("usage") or {}).get("credit")) for item in requests
    )
    print(
        f"[OK] Token 汇总：对话 {len(rollup_turns(requests))} 轮，"
        f"模型请求 {len(requests)}，已观测 {total:,} tokens，"
        f"{format_credit(credit)} credit → {overview}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
