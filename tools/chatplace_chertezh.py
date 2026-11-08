#!/usr/bin/env python3
"""Создать воронку ЧЕРТЕЖ в ChatPlace через MCP, если есть ключ.

Ключ только из переменной CHATPLACE_API_KEY. В stdout ключ не пишется.
Без ключа: код 2 и инструкция, как подключить MCP в Cursor.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "funnels" / "chertezh" / "scenario.json"
MCP_URL = "https://mcp.chatplace.io/mcp"


def rpc(key: str, req_id: int, method: str, params: dict | None = None) -> dict:
    payload: dict = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params is not None:
        payload["params"] = params
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        MCP_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "Mozilla/5.0 (compatible; CursorAgent/1.0; ChatPlace MCP client)",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:800]
        raise SystemExit(f"ChatPlace MCP HTTP {exc.code}: {detail}") from exc
    if raw.startswith("event:") or "data:" in raw[:40]:
        chunks = []
        for line in raw.splitlines():
            if line.startswith("data:"):
                chunks.append(line[5:].strip())
        raw = "\n".join(chunks) if chunks else raw
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"ChatPlace MCP: не JSON: {raw[:400]}") from exc


def call_tool(key: str, req_id: int, name: str, arguments: dict) -> dict:
    return rpc(key, req_id, "tools/call", {"name": name, "arguments": arguments})


def tool_names(listed: dict) -> list[str]:
    result = listed.get("result") or {}
    tools = result.get("tools") or []
    return [t.get("name", "") for t in tools if t.get("name")]


def build_prompt(scenario: dict) -> str:
    replies = "\n".join(f"- {line}" for line in scenario["comment_replies"])
    dm1, dm2, dm3 = scenario["flow"]
    aliases = ", ".join(scenario["keyword_aliases"])
    return f"""
Собери и включи автоматизацию в Instagram-аккаунте @xeniia_neuro.

Название: {scenario["name"]}
Триггер: комментарий к публикации (только комментарий, без Direct).
После публикации карусели привязать к этому посту. Пока поста нет — все посты.
Ключевое слово: {scenario["keyword"]}. Совпадение частичное. Синонимы: {aliases}.
Не удалять и не менять существующие воронки ИНСТРУКЦИЯ, КУРС, МОНТАЖ, АГЕНТ, ДЕСКТОП.

Автоответы на комментарий:
{replies}

Сообщение 1 (единственное до клика, БЕЗ ссылок):
{dm1["text"]}
Кнопка действия (не ссылка): {dm1["buttons"][0]["title"]}

Сообщение 2 после клика, тег {dm2["tag"]} — это само наполнение, не голая ссылка:
{dm2["text"]}
Кнопка-ссылка {dm2["buttons"][0]["title"]} → {dm2["buttons"][0]["url"]}

Сообщение 3, тег {dm3["tag"]}:
{dm3["text"]}
Кнопка-ссылка {dm3["buttons"][0]["title"]} → {dm3["buttons"][0]["url"]}

Цель: комментарий ЧЕРТЕЖ → разбор в Direct → промпты в канале @xeniia_neuro → курс/внедрение боту.
""".strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    scenario = json.loads(SCENARIO.read_text(encoding="utf-8"))
    key = os.environ.get("CHATPLACE_API_KEY", "").strip()

    print("Воронка ЧЕРТЕЖ готова к вставке.")
    print(f"Сценарий: {SCENARIO.relative_to(ROOT)}")
    print(f"Ключевое слово: {scenario['keyword']}")
    print("Наполнение: разбор в Direct, промпты в канале, курс боту.")

    if not key:
        print(
            "Ключа CHATPLACE_API_KEY нет — живую автоматизацию "
            "из этой среды создать нельзя. Вставь сценарий в ChatPlace "
            "или подключи MCP в Cursor Settings → Tools & MCP."
        )
        return 0 if args.dry_run else 2

    if not args.apply:
        print("Ключ найден. Для создания: python3 tools/chatplace_chertezh.py --apply")
        return 0

    listed = rpc(key, 1, "tools/list")
    if listed.get("error"):
        print(f"tools/list error: {listed['error']}", file=sys.stderr)
        return 1
    names = tool_names(listed)
    print("MCP tools:", ", ".join(names) or "(пусто)")

    prompt = build_prompt(scenario)
    preferred = [
        name
        for name in names
        if "automation" in name.lower()
        and any(part in name.lower() for part in ("create", "generate", "build", "ai"))
    ]
    fallback = [name for name in names if "automation" in name.lower()]
    target = (preferred or fallback or names)[:3]
    if not target:
        print("В ключе нет методов автоматизаций. Выдай в ChatPlace право на запись.", file=sys.stderr)
        return 1

    for i, name in enumerate(target, start=10):
        arguments = {"prompt": prompt}
        schema_tools = (listed.get("result") or {}).get("tools") or []
        schema = next((t for t in schema_tools if t.get("name") == name), {})
        props = ((schema.get("inputSchema") or {}).get("properties")) or {}
        if "name" in props:
            arguments["name"] = scenario["name"]
        if "account" in props:
            arguments["account"] = "instagram"
        print(f"tools/call {name}")
        last = call_tool(key, i, name, arguments)
        if not last.get("error"):
            result = last.get("result")
            text = json.dumps(result, ensure_ascii=False)[:1200] if result is not None else "ok"
            print(text)
            return 0
        print(f"{name}: {last.get('error')}", file=sys.stderr)

    print("Не удалось создать автоматизацию через MCP. Вставь scenario.json в ChatPlace вручную.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
