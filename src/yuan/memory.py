"""项目长期记忆：不可变事实记录、连续性检查点与确定性检索。"""

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
from .memory_views import CATEGORIES, MEMORY_ROOT, index_value, record_relative, write_views
from .paths import normalize_relative, resolve_inside
from .runtime import rebuild
from .validate import identifier, with_digest


KINDS = tuple(CATEGORIES)
STATUSES = ("active", "resolved", "superseded", "deprecated")
CONFIDENCE = ("verified", "decided", "observed", "hypothesis", "stale", "superseded", "deprecated")
KNOWLEDGE_KINDS = {"feature", "module", "architecture", "convention"}
DECISION_KINDS = {"project", "decision"}
EXPERIENCE_KINDS = {"pitfall", "incident"}
CONTINUITY_KINDS = {"checkpoint", "handoff"}
CHECKPOINT_FIELDS = ("completed", "blockers", "next_steps", "open_questions", "resume_commands")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _text(value: Any, label: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"{label} 必须是非空字符串")
    return value.strip()


def _git_revision(root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root.resolve()), "rev-parse", "HEAD"], stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False, shell=False,
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


def _validate_common(value: dict[str, Any]) -> None:
    identifier(value["memory_id"], "memory_id")
    _require(isinstance(value["revision"], int) and value["revision"] > 0, "Memory revision 必须是正整数")
    _require(value["kind"] in KINDS, "Memory kind 不合法")
    for field in ("title", "summary", "details", "created_at"):
        _text(value[field], f"Memory {field}")
    _require(value["status"] in STATUSES, "Memory status 不合法")
    _require(value["confidence"] in CONFIDENCE, "Memory confidence 不合法")
    for field in ("tags", "relations"):
        items = value[field]
        _require(isinstance(items, list) and all(isinstance(item, str) and item.strip() for item in items), f"Memory {field} 不合法")
        _require(items == sorted(set(items)), f"Memory {field} 必须唯一且排序")
    _require(isinstance(value["bindings"], list), "Memory bindings 必须是 Array")
    paths = []
    for binding in value["bindings"]:
        _require(isinstance(binding, dict) and set(binding) == {"path", "bytes", "digest"}, "Memory Binding 结构不合法")
        paths.append(normalize_relative(binding["path"]))
        _require(isinstance(binding["bytes"], int) and binding["bytes"] >= 0, "Memory Binding bytes 不合法")
        _require(isinstance(binding["digest"], str) and re.fullmatch(r"[0-9a-f]{64}", binding["digest"]) is not None, "Memory Binding digest 不合法")
    _require(paths == sorted(set(paths)), "Memory Binding 必须唯一且排序")
    _require(value["supersedes"] is None or (isinstance(value["supersedes"], str) and re.fullmatch(r"[0-9a-f]{64}", value["supersedes"]) is not None), "Memory supersedes 不合法")
    _require(verify_digest(value), "Memory Record Digest 不匹配")


def _validate_source(source: Any, *, version: str) -> None:
    base = {"work_id", "work_revision", "work_digest", "evidence_ids", "artifact_digest", "ledger_head", "git_commit"}
    keys = base if version == "yuan.memory/v1" else base | {"attempt_ids"}
    _require(isinstance(source, dict) and set(source) == keys, "Memory Source 结构不合法")
    identifier(source["work_id"], "Memory source work_id")
    _require(isinstance(source["work_revision"], int) and source["work_revision"] > 0, "Memory Source work_revision 不合法")
    for field in ("work_digest", "artifact_digest", "ledger_head"):
        _require(isinstance(source[field], str) and re.fullmatch(r"[0-9a-f]{64}", source[field]) is not None, f"Memory Source {field} 不合法")
    for field in (("evidence_ids",) if version == "yuan.memory/v1" else ("evidence_ids", "attempt_ids")):
        items = source[field]
        _require(isinstance(items, list) and all(isinstance(item, str) and item.strip() for item in items), f"Memory Source {field} 不合法")
        _require(items == sorted(set(items)), f"Memory Source {field} 必须唯一且排序")
    if version == "yuan.memory/v1":
        _require(bool(source["evidence_ids"]), "Memory Source 至少绑定一个 Evidence")
    _require(source["git_commit"] is None or (isinstance(source["git_commit"], str) and bool(source["git_commit"])), "Memory Source git_commit 不合法")


def validate_memory(value: Any) -> dict[str, Any]:
    _require(isinstance(value, dict), "Memory Record 必须是 JSON Object")
    common = {"schema_version", "memory_id", "revision", "kind", "title", "summary", "details", "status", "confidence", "tags", "relations", "bindings", "source", "supersedes", "created_at", "digest"}
    version = value.get("schema_version")
    _require(version in {"yuan.memory/v1", "yuan.memory/v2"}, "Memory Schema Version 不受支持")
    _require(set(value) == (common if version == "yuan.memory/v1" else common | {"data"}), "Memory Record 字段集合不合法")
    _validate_common(value)
    _validate_source(value["source"], version=version)
    if version == "yuan.memory/v1":
        _require(value["kind"] in {"feature", "decision", "pitfall", "module", "convention"}, "v1 Memory kind 不合法")
        _require(value["confidence"] in {"verified", "stale", "deprecated"}, "v1 Memory confidence 不合法")
    else:
        _require(isinstance(value["data"], dict), "Memory data 必须是 Object")
        allowed_confidence = (
            {"verified", "stale", "superseded", "deprecated"} if value["kind"] in KNOWLEDGE_KINDS
            else {"decided", "stale", "superseded", "deprecated"} if value["kind"] in DECISION_KINDS
            else {"observed", "hypothesis", "stale", "superseded", "deprecated"}
        )
        _require(value["confidence"] in allowed_confidence, "Memory confidence 与 kind 不匹配")
        if value["kind"] in CONTINUITY_KINDS:
            _require(set(value["data"]) == set(CHECKPOINT_FIELDS), "连续性 Memory data 字段不完整")
            for field in CHECKPOINT_FIELDS:
                items = value["data"][field]
                _require(isinstance(items, list) and all(isinstance(item, str) and item.strip() for item in items), f"Memory data.{field} 不合法")
        else:
            _require(value["data"] == {}, "非连续性 Memory data 当前必须为空")
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
        if path.resolve() != (root / record_relative(value)).resolve():
            raise IntegrityError(f"Memory Record 路径与 Identity 不匹配：{path.relative_to(root)}")
        values.setdefault(value["memory_id"], []).append(value)
    for memory_id, revisions in values.items():
        revisions.sort(key=lambda item: item["revision"])
        for index, record in enumerate(revisions, start=1):
            if record["revision"] != index:
                raise IntegrityError(f"Memory Revision 不连续：{memory_id}")
            expected = None if index == 1 else revisions[index - 2]["digest"]
            if record["supersedes"] != expected or record["kind"] != revisions[0]["kind"]:
                raise IntegrityError(f"Memory Revision Chain 不合法：{memory_id}")
    return values


def rebuild_memory(root: Path, *, write: bool = True) -> dict[str, Any]:
    root = root.resolve()
    heads = [values[-1] for _, values in sorted(_records(root).items())]
    return write_views(root, heads) if write else index_value(heads)


def _source(projection: dict[str, Any], root: Path) -> dict[str, Any]:
    work = projection.get("work")
    _require(isinstance(work, dict), "当前 Run 没有可绑定的 Work")
    _require(isinstance(projection.get("expected_artifact"), str), "当前 Work 缺少 Artifact Baseline")
    _require(isinstance(projection.get("source_head"), str), "当前 Work 缺少 Ledger Head")
    evidence = sorted(item["evidence_id"] for item in projection["evidence"].values() if item.get("current") is True)
    attempts = sorted(projection["attempts"])
    return {
        "work_id": work["work_id"], "work_revision": work["revision"], "work_digest": work["digest"],
        "evidence_ids": evidence, "attempt_ids": attempts, "artifact_digest": projection["expected_artifact"],
        "ledger_head": projection["source_head"], "git_commit": _git_revision(root),
    }


def _confidence(kind: str, projection: dict[str, Any]) -> str:
    if kind in KNOWLEDGE_KINDS:
        passed = any(item.get("status") == "PASS" and item.get("current") is True for item in projection["evidence"].values())
        _require(passed, "知识 Memory 必须绑定当前 Artifact 的 PASS Evidence")
        return "verified"
    if kind in DECISION_KINDS:
        _require(bool(projection["work"].get("confirmation")), "决策 Memory 必须绑定用户已确认的 Work")
        return "decided"
    if kind in EXPERIENCE_KINDS:
        failed = any(item.get("status") == "FAIL" for item in projection["evidence"].values())
        _require(failed or bool(projection["attempts"]), "经验 Memory 必须绑定 FAIL Evidence 或 Attempt 历史")
        return "observed"
    return "observed"


def memory_template(
    root: Path, *, memory_id: str, kind: str, title: str, summary: str, details: str,
    status: str = "active", tags: list[str] | None = None, relations: list[str] | None = None,
    bind_paths: list[str] | None = None, data: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    identifier(memory_id, "memory_id")
    _require(kind in KINDS, "Memory kind 不合法")
    projection = rebuild(root, write=False)
    records = _records(root).get(memory_id, [])
    if records:
        _require(records[-1]["kind"] == kind, "Memory kind 不能跨 Revision 改变")
    structured: dict[str, Any] = data or {}
    if kind in CONTINUITY_KINDS:
        structured = {field: list(structured.get(field, [])) for field in CHECKPOINT_FIELDS}
    source = _source(projection, root)
    if kind in KNOWLEDGE_KINDS:
        source["evidence_ids"] = sorted(
            item["evidence_id"] for item in projection["evidence"].values()
            if item.get("status") == "PASS" and item.get("current") is True
        )
    elif kind in DECISION_KINDS:
        source["evidence_ids"] = []
        source["attempt_ids"] = []
    elif kind in EXPERIENCE_KINDS:
        source["evidence_ids"] = sorted(
            item["evidence_id"] for item in projection["evidence"].values()
            if item.get("status") == "FAIL" and item.get("current") is True
        )
    value = {
        "schema_version": "yuan.memory/v2", "memory_id": memory_id, "revision": len(records) + 1,
        "kind": kind, "title": _text(title, "Memory title"), "summary": _text(summary, "Memory summary"),
        "details": _text(details, "Memory details"), "status": status,
        "confidence": _confidence(kind, projection), "tags": sorted(set(tags or [])),
        "relations": sorted(set(relations or [])), "bindings": _bindings(root, bind_paths or []),
        "data": structured, "source": source,
        "supersedes": None if not records else records[-1]["digest"],
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    return validate_memory(with_digest(value))


def _check_policy(projection: dict[str, Any], value: dict[str, Any]) -> None:
    source = value["source"]
    if value["schema_version"] == "yuan.memory/v1" or value["kind"] in KNOWLEDGE_KINDS:
        _require(bool(source["evidence_ids"]), "知识 Memory 必须绑定 Evidence")
        for evidence_id in source["evidence_ids"]:
            evidence = projection["evidence"].get(evidence_id)
            _require(bool(evidence) and evidence.get("status") == "PASS" and evidence.get("current") is True, f"Memory Source PASS Evidence 不存在或已过期：{evidence_id}")
    elif value["kind"] in DECISION_KINDS:
        _require(bool(projection["work"].get("confirmation")), "决策 Memory 的 Work 尚未由用户确认")
    elif value["kind"] in EXPERIENCE_KINDS:
        failed = any(projection["evidence"].get(item, {}).get("status") == "FAIL" for item in source["evidence_ids"])
        attempts = source.get("attempt_ids", [])
        _require(failed or bool(attempts), "经验 Memory 缺少 FAIL Evidence 或 Attempt 来源")
        _require(all(item in projection["attempts"] for item in attempts), "经验 Memory 引用了不存在的 Attempt")


def check_memory_source(root: Path, value: dict[str, Any]) -> dict[str, Any]:
    validate_memory(value)
    projection = rebuild(root.resolve(), write=False)
    work = projection.get("work")
    _require(isinstance(work, dict), "当前 Run 没有 Work")
    source = value["source"]
    _require((source["work_id"], source["work_revision"], source["work_digest"]) == (work["work_id"], work["revision"], work["digest"]), "Memory Source Work Binding 已过期")
    _require(source["artifact_digest"] == projection["expected_artifact"], "Memory Source Artifact Binding 已过期")
    _require(source["ledger_head"] == projection["source_head"], "Memory Source Ledger Head 已过期")
    _check_policy(projection, value)
    return value


def record_memory(root: Path, value: dict[str, Any]) -> dict[str, Any]:
    root = root.resolve()
    check_memory_source(root, value)
    records = _records(root).get(value["memory_id"], [])
    _require(value["revision"] == len(records) + 1, "Memory Revision 不是下一版本")
    _require(value["supersedes"] == (None if not records else records[-1]["digest"]), "Memory Supersedes 不是当前 Head")
    path = root / record_relative(value)
    if path.exists():
        raise IntegrityError("Memory Record 已存在")
    atomic_write(path, canonical_bytes(value))
    index = rebuild_memory(root)
    return {"status": "MEMORY_RECORDED", "record": path.relative_to(root).as_posix(), "memory_id": value["memory_id"], "revision": value["revision"], "digest": value["digest"], "index_digest": index["digest"]}


def checkpoint_memory(
    root: Path, *, summary: str, details: str, completed: list[str] | None = None,
    blockers: list[str] | None = None, next_steps: list[str] | None = None,
    open_questions: list[str] | None = None, resume_commands: list[str] | None = None,
) -> dict[str, Any]:
    data = {
        "completed": completed or [], "blockers": blockers or [], "next_steps": next_steps or [],
        "open_questions": open_questions or [], "resume_commands": resume_commands or [],
    }
    value = memory_template(root, memory_id="CURRENT", kind="checkpoint", title="当前工作检查点", summary=summary, details=details, tags=["continuity"], data=data)
    return record_memory(root, value)


def memory_status(root: Path) -> dict[str, Any]:
    root = root.resolve()
    items = []
    for memory_id, revisions in sorted(_records(root).items()):
        head = revisions[-1]
        stale = []
        for binding in head["bindings"]:
            path = resolve_inside(root, binding["path"])
            if path.is_symlink() or not path.is_file():
                stale.append({"path": binding["path"], "reason": "MISSING"})
            else:
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
    documents = {}
    for memory_id, revisions in _records(root.resolve()).items():
        head = revisions[-1]
        fields = {
            "title": _search_terms(head["title"]), "tags": _search_terms(" ".join(head["tags"])),
            "summary": _search_terms(head["summary"]),
            "details": _search_terms(head["details"] + " " + json.dumps(head.get("data", {}), ensure_ascii=False)),
        }
        documents[memory_id] = (head, fields)
    terms = _search_terms(request)
    frequencies = {term: sum(term in set().union(*fields.values()) for _, fields in documents.values()) for term in terms}
    matches = []
    weights = {"title": 5, "tags": 4, "summary": 3, "details": 1}
    for memory_id, (head, fields) in documents.items():
        matched = sorted(term for term in terms if any(term in values for values in fields.values()))
        score = sum(round(100 * (1 + math.log((len(documents) + 1) / (frequencies[term] + 1)))) * max(weights[name] for name, values in fields.items() if term in values) for term in matched)
        haystack = " ".join([head["title"], head["summary"], head["details"], *head["tags"]]).casefold()
        if request.casefold() in haystack:
            score += 1000
        if score:
            matches.append((score, memory_id, head, matched))
    matches.sort(key=lambda item: (-item[0], item[1]))
    return {"status": "PASS", "request": request, "memories": [{"score": score, "matched_terms": matched, "record": record} for score, _, record, matched in matches[:limit]]}


def memory_resume(root: Path, request: str | None = None, *, limit: int = 10) -> dict[str, Any]:
    records = _records(root.resolve())
    continuity = [values[-1] for values in records.values() if values[-1]["kind"] in CONTINUITY_KINDS and values[-1]["status"] == "active"]
    current = max(continuity, key=lambda item: (item["created_at"], item["memory_id"]), default=None)
    context = memory_context(root, request, limit=limit) if request else {"status": "PASS", "request": None, "memories": []}
    return {"status": "PASS", "current": current, "context": context["memories"], "memory_status": memory_status(root)}
