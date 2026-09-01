from __future__ import annotations


def parse_status(document: str) -> dict[str, object]:
    lines = document.splitlines()
    if not lines or lines[0] != "---":
        return {"work_state": "UNKNOWN", "agent": None, "summary": document.strip()}

    frontmatter: dict[str, str] = {}
    body_start = 1
    for index, line in enumerate(lines[1:], 1):
        if line == "---":
            body_start = index + 1
            break
        if ":" in line:
            key, value = line.split(":", 1)
            frontmatter[key.strip()] = value.strip()

    raw_state = frontmatter.get("work_state", "UNKNOWN").lower()
    work_state = raw_state if raw_state in {"idle", "active", "paused"} else "UNKNOWN"
    agent = frontmatter.get("agent") or None
    body = "\n".join(lines[body_start:]).strip()
    summary = body.splitlines()[0] if body else ""
    return {"work_state": work_state, "agent": agent, "summary": summary}
