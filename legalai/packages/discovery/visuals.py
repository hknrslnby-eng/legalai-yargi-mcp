"""Conditional visual specifications with text fallbacks for MCP hosts."""
from __future__ import annotations

from typing import Any


def visual_spec(kind: str, data: Any) -> dict[str, Any]:
    if kind == "strategy_paths" and isinstance(data, list):
        rows = []
        nodes = []
        for index, item in enumerate(data, 1):
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or item.get("route") or f"Seçenek {index}")
            benefit = str(item.get("benefit") or item.get("benefits") or "Belirtilmedi")
            rows.append({"option": title, "benefit": benefit, "risk": item.get("risk", item.get("risks", "Belirtilmedi"))})
            nodes.append(f"N{index}[{_escape(title)}]")
        mermaid = "flowchart TD\nS[Strateji seçimi] --> " + " & ".join(f"N{index}" for index in range(1, len(nodes) + 1)) + "\n" + "\n".join(nodes)
        return {"kind": kind, "mermaid": mermaid if rows else "", "fallback": {"type": "table", "columns": ["option", "benefit", "risk"], "rows": rows}}
    return {
        "kind": kind,
        "mermaid": "",
        "fallback": {"type": "text", "content": str(data) if data is not None else "Görsel veri yok."},
    }


def _escape(value: str) -> str:
    return value.replace("[", "(").replace("]", ")").replace('"', "'")
