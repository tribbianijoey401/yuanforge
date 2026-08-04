"""基于 Work/Evidence 的追加式项目长期记忆。"""

from __future__ import annotations

import json
import math
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .canonical import canonical_bytes, digest_bytes, verify_digest
from .errors import IntegrityError, ValidationError
from .ledger import atomic_write
from .paths import normalize_relative, resolve_inside
from .runtime import rebuild
from .validate import identifier, with_digest


MEMORY_ROOT = Path("docs/memory")
KINDS = ("feature", "decision", "pitfall", "module", "convention")
STATUSES = ("active", "resolved", "superseded", "deprecated")
CONFIDENCE = ("verified", "stale", "deprecated")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _text(value: Any, label: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"{label} 必须是非空字符串")
    return value.strip()


def _git_revision(root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root.resolve()), "rev-parse", "HEAD"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            shell=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    try:
        return completed.stdout.decode("ascii").strip() or None
    except UnicodeError:
        return None


def _bindings(root: Path, paths: list[str]) -> list[dict[str, Any]]:
    values = []
    for relative in paths:
        safe = normalize_relative(relative)
        path = resolve_inside(root, safe)
        if path.is_symlink() or not path.is_file():
            raise ValidationError(f"Memory Binding 必须是普通文件：{safe}")
        payload = path.read_bytes()
        values.append({"path": safe, "bytes": len(payload), "digest": digest_bytes(payload)})
    _require(len(values) == len({item["path"] for item in values}), "Memory Binding Path 重复")
    return sorted(values, key=lambda item: item["path"])


def validate_memory(value: Any) -> dict[str, Any]:
    _require(isinstance(value, dict), "Memory Record 必须是 JSON Object")
    required = {
        "schema_version", "memory_id", "revision", "kind", "title", "summary", "details",
        "status", "confidence", "tags", "relations", "bindings", "source", "supersedes",
        "created_at", "digest",
    }
    _require(set(value) == required, "Memory Record 字段集合不合法")
    _require(value["schema_version"] == "yuan.memory/v1", "Memory Schema Version 不受支持")
    identifier(value["memory_id"], "memory_id")
    _require(isinstance(value["revision"], int) and value["revision"] > 0, "Memory revision 必须是正整数")
    _require(value["kind"] in KINDS, "Memory kind 不合法")
    _text(value["title"], "Memory title")
    _text(value["summary"], "Memory summary")
    _text(value["details"], "Memory details")
    _require(value["status"] in STATUSES, "Memory status 不合法")
    _require(value["confidence"] in CONFIDENCE, "Memory confidence 不合法")
    for field in ("tags", "relations"):
        items = value[field]
        _require(isinstance(items, list) and all(isinstance(item, str) and item.strip() for item in items), f"Memory {field} 不合法")
        _require(len(items) == len(set(items)), f"Memory {field} 重复")
    bindings = value["bindings"]
    _require(isinstance(bindings, list), "Memory bindings 必须是 Array")
    binding_paths = []
    for binding in bindings:
        _require(isinstance(binding, dict) and set(binding) == {"path", "bytes", "digest"}, "Memory Binding 结构不合法")
        binding_paths.append(normalize_relative(binding["path"]))
        _require(isinstance(binding["bytes"], int) and binding["bytes"] >= 0, "Memory Binding bytes 不合法")
        _require(isinstance(binding["digest"], str) and re.fullmatch(r"[0-9a-f]{64}", binding["digest"]) is not None, "Memory Binding digest 不合法")
    _require(binding_paths == sorted(set(binding_paths)), "Memory Binding 必须唯一且排序")
    source = value["source"]
    source_keys = {"work_id", "work_revision", "work_digest", "evidence_ids", "artifact_digest", "ledger_head", "git_commit"}
    _require(isinstance(source, dict) and set(source) == source_keys, "Memory Source 结构不合法")
    identifier(source["work_id"], "Memory source work_id")
    _require(isinstance(source["work_revision"], int) and source["work_revision"] > 0, "Memory Source work_revision 不合法")
    for field in ("work_digest", "artifact_digest", "ledger_head"):
        _require(isinstance(source[field], str) and re.fullmatch(r"[0-9a-f]{64}", source[field]) is not None, f"Memory Source {field} 不合法")
    evidence_ids = source["evidence_ids"]
    _require(isinstance(evidence_ids, list) and bool(evidence_ids), "Memory Source 至少绑定一个 Evidence")
    _require(all(isinstance(item, str) and item.strip() for item in evidence_ids), "Memory Source evidence_ids 不合法")
    _require(evidence_ids == sorted(set(evidence_ids)), "Memory Source evidence_ids 必须唯一且排序")
    _require(source["git_commit"] is None or (isinstance(source["git_commit"], str) and bool(source["git_commit"])), "Memory Source git_commit 不合法")
    _require(value["supersedes"] is None or (isinstance(value["supersedes"], str) and re.fullmatch(r"[0-9a-f]{64}", value["supersedes"]) is not None), "Memory supersedes 不合法")
    _text(value["created_at"], "Memory created_at")
    _require(verify_digest(value), "Memory Record Digest 不匹配")
    return value


def _record_paths(root: Path) -> list[Path]:
    records = root / MEMORY_ROOT / "records"
    return [] if not records.is_dir() else sorted(records.rglob("*.json"))


def _records(root: Path) -> dict[str, list[dict[str, Any]]]:
    values: dict[str, list[dict[str, Any]]] = {}
    for path in _record_paths(root):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise IntegrityError(f"Memory Record 不可读：{path.relative_to(root)}") from exc
        validate_memory(value)
        expected = root / MEMORY_ROOT / "records" / value["kind"] / value["memory_id"] / f"{value['revision']:06d}.json"
        if path.resolve() != expected.resolve():
            raise IntegrityError(f"Memory Record 路径与 Identity 不匹配：{path.relative_to(root)}")
        values.setdefault(value["memory_id"], []).append(value)
    for memory_id, revisions in values.items():
        revisions.sort(key=lambda item: item["revision"])
        for index, record in enumerate(revisions, start=1):
            if record["revision"] != index:
                raise IntegrityError(f"Memory Revision 不连续：{memory_id}")
            expected_supersedes = None if index == 1 else revisions[index - 2]["digest"]
            if record["supersedes"] != expected_supersedes:
                raise IntegrityError(f"Memory Supersedes Chain 不合法：{memory_id}")
            if record["kind"] != revisions[0]["kind"]:
                raise IntegrityError(f"Memory kind 在 Revision 间发生变化：{memory_id}")
    return values


def _index_value(root: Path) -> dict[str, Any]:
    records = _records(root)
    heads = []
    for memory_id in sorted(records):
        head = records[memory_id][-1]
        heads.append({
            "memory_id": memory_id,
            "revision": head["revision"],
            "kind": head["kind"],
            "title": head["title"],
            "summary": head["summary"],
            "status": head["status"],
            "confidence": head["confidence"],
            "tags": head["tags"],
            "digest": head["digest"],
            "record": (MEMORY_ROOT / "records" / head["kind"] / memory_id / f"{head['revision']:06d}.json").as_posix(),
        })
    return with_digest({"schema_version": "yuan.memory-index/v1", "heads": heads})


def _markdown_index(index: dict[str, Any]) -> bytes:
    lines = ["# Yuan 项目长期记忆", "", "此文件由 `yuan memory rebuild` 从追加式 Memory Record 生成。", ""]
    for kind in KINDS:
        items = [item for item in index["heads"] if item["kind"] == kind]
        if not items:
            continue
        lines.extend([f"## {kind}", "", "| ID | Revision | Status | Confidence | Summary |", "|---|---:|---|---|---|"])
        for item in items:
            summary = item["summary"].replace("|", "\\|").replace("\n", " ")
            lines.append(f"| `{item['memory_id']}` | {item['revision']} | {item['status']} | {item['confidence']} | {summary} |")
        lines.append("")
    if not index["heads"]:
        lines.extend(["当前尚无长期记忆记录。", ""])
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8")


def rebuild_memory(root: Path, *, write: bool = True) -> dict[str, Any]:
    root = root.resolve()
    index = _index_value(root)
    if write:
        atomic_write(root / MEMORY_ROOT / "index.json", canonical_bytes(index))
        atomic_write(root / MEMORY_ROOT / "INDEX.md", _markdown_index(index))
    return index


def memory_template(
    root: Path,
    *,
    memory_id: str,
    kind: str,
    title: str,
    summary: str,
    details: str,
    status: str = "active",
    tags: list[str] | None = None,
    relations: list[str] | None = None,
    bind_paths: list[str] | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    identifier(memory_id, "memory_id")
    _require(kind in KINDS, "Memory kind 不合法")
    projection = rebuild(root, write=False)
    work = projection.get("work")
    _require(isinstance(work, dict), "当前 Run 没有可绑定的 Work")
    evidence = sorted(
        item["evidence_id"] for item in projection["evidence"].values()
        if item.get("status") == "PASS" and item.get("current") is True
    )
    _require(bool(evidence), "长期记忆必须绑定当前 Artifact 的 PASS Evidence")
    records = _records(root).get(memory_id, [])
    revision = len(records) + 1
    if records:
        _require(records[-1]["kind"] == kind, "Memory kind 不能跨 Revision 改变")
    value = {
        "schema_version": "yuan.memory/v1",
        "memory_id": memory_id,
        "revision": revision,
        "kind": kind,
        "title": _text(title, "Memory title"),
        "summary": _text(summary, "Memory summary"),
        "details": _text(details, "Memory details"),
        "status": status,
        "confidence": "verified",
        "tags": sorted(set(tags or [])),
        "relations": sorted(set(relations or [])),
        "bindings": _bindings(root, bind_paths or []),
        "source": {
            "work_id": work["work_id"],
            "work_revision": work["revision"],
            "work_digest": work["digest"],
            "evidence_ids": evidence,
            "artifact_digest": projection["expected_artifact"],
            "ledger_head": projection["source_head"],
            "git_commit": _git_revision(root),
        },
        "supersedes": None if not records else records[-1]["digest"],
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    return validate_memory(with_digest(value))


def check_memory_source(root: Path, value: dict[str, Any]) -> dict[str, Any]:
    validate_memory(value)
    projection = rebuild(root.resolve(), write=False)
    work = projection.get("work")
    _require(isinstance(work, dict), "当前 Run 没有 Work")
    source = value["source"]
    _require(source["work_id"] == work["work_id"] and source["work_revision"] == work["revision"] and source["work_digest"] == work["digest"], "Memory Source Work Binding 已过期")
    _require(source["artifact_digest"] == projection["expected_artifact"], "Memory Source Artifact Binding 已过期")
    _require(source["ledger_head"] == projection["source_head"], "Memory Source Ledger Head 已过期")
    for evidence_id in source["evidence_ids"]:
        evidence = projection["evidence"].get(evidence_id)
        _require(bool(evidence) and evidence.get("status") == "PASS" and evidence.get("current") is True, f"Memory Source Evidence 不存在或已过期：{evidence_id}")
    return value


def record_memory(root: Path, value: dict[str, Any]) -> dict[str, Any]:
    root = root.resolve()
    check_memory_source(root, value)
    records = _records(root).get(value["memory_id"], [])
    expected_revision = len(records) + 1
    _require(value["revision"] == expected_revision, "Memory Revision 不是下一版本")
    expected_supersedes = None if not records else records[-1]["digest"]
    _require(value["supersedes"] == expected_supersedes, "Memory Supersedes 不是当前 Head")
    path = root / MEMORY_ROOT / "records" / value["kind"] / value["memory_id"] / f"{value['revision']:06d}.json"
    if path.exists():
        raise IntegrityError("Memory Record 已存在")
    atomic_write(path, canonical_bytes(value))
    index = rebuild_memory(root)
    return {"status": "MEMORY_RECORDED", "record": path.relative_to(root).as_posix(), "memory_id": value["memory_id"], "revision": value["revision"], "digest": value["digest"], "index_digest": index["digest"]}


def memory_status(root: Path) -> dict[str, Any]:
    root = root.resolve()
    records = _records(root)
    items = []
    for memory_id in sorted(records):
        head = records[memory_id][-1]
        stale = []
        for binding in head["bindings"]:
            path = resolve_inside(root, binding["path"])
            if path.is_symlink() or not path.is_file():
                stale.append({"path": binding["path"], "reason": "MISSING"})
                continue
            payload = path.read_bytes()
            if len(payload) != binding["bytes"] or digest_bytes(payload) != binding["digest"]:
                stale.append({"path": binding["path"], "reason": "CHANGED"})
        items.append({"memory_id": memory_id, "revision": head["revision"], "recorded_confidence": head["confidence"], "effective_confidence": "stale" if stale else head["confidence"], "stale_bindings": stale})
    return {"status": "PASS", "items": items, "stale": sum(item["effective_confidence"] == "stale" for item in items)}


def memory_show(root: Path, memory_id: str) -> dict[str, Any]:
    identifier(memory_id, "memory_id")
    records = _records(root.resolve()).get(memory_id)
    if not records:
        raise ValidationError(f"Memory 不存在：{memory_id}")
    return records[-1]


def _search_terms(value: str) -> set[str]:
    terms: set[str] = set()
    for token in re.findall(r"[a-z0-9_]+|[\u4e00-\u9fff]+", value.casefold()):
        terms.add(token)
        if "\u4e00" <= token[0] <= "\u9fff" and len(token) > 2:
            terms.update(token[index:index + 2] for index in range(len(token) - 1))
    return terms


def memory_context(root: Path, request: str, *, limit: int = 10) -> dict[str, Any]:
    request = _text(request, "Memory context request")
    _require(isinstance(limit, int) and 1 <= limit <= 100, "Memory context limit 必须在 1..100")
    records = _records(root.resolve())
    terms = _search_terms(request)
    documents = {}
    for memory_id, revisions in records.items():
        head = revisions[-1]
        fields = {
            "title": _search_terms(head["title"]),
            "tags": _search_terms(" ".join(head["tags"])),
            "summary": _search_terms(head["summary"]),
            "details": _search_terms(head["details"]),
        }
        documents[memory_id] = (head, fields)
    frequencies = {
        term: sum(term in set().union(*fields.values()) for _, fields in documents.values())
        for term in terms
    }
    matches = []
    weights = {"title": 5, "tags": 4, "summary": 3, "details": 1}
    for memory_id, (head, fields) in documents.items():
        matched = sorted(term for term in terms if any(term in values for values in fields.values()))
        score = sum(
            round(100 * (1 + math.log((len(documents) + 1) / (frequencies[term] + 1))))
            * max(weights[name] for name, values in fields.items() if term in values)
            for term in matched
        )
        haystack = " ".join([head["title"], head["summary"], head["details"], *head["tags"]]).casefold()
        if request.casefold() in haystack:
            score += 1000
        if score:
            matches.append((score, memory_id, head, matched))
    matches.sort(key=lambda item: (-item[0], item[1]))
    return {
        "status": "PASS",
        "request": request,
        "memories": [
            {"score": score, "matched_terms": matched, "record": record}
            for score, _, record, matched in matches[:limit]
        ],
    }
