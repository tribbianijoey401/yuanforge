"""Independent M7 provenance verifier.

This module intentionally does not import the author generator or its mapping
logic. It recomputes inventory, clause boundaries, hashes, and destinations.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

FROZEN_SOURCE_REVISION = "c1fd815a85395351e7ebc23e3ff72507326977f2"
EXPECTED_OUT_OF_BAND = {
    ".yuan/rules/test-integrity.md": "include",
    "docs/decisions/OPEN-DECISIONS.md": "exclude",
}
REQUIRED_EXCLUSIONS = {
    ".workbuddy/**", ".yuan-shadow/**", ".yuan-run/**",
    "**/__pycache__/**", "docs/graph/index.json", ".git/**",
}
KEY_SCRIPTS = {
    "scripts/bootstrap-core-verifier.py", "scripts/bootstrap_verifier.py",
    "scripts/bootstrap_verifier_support.py", "scripts/build-graph.py",
    "scripts/distill-pitfall.sh", "scripts/pre-commit",
    "scripts/ptg-cal-gen.py", "scripts/query-graph.py",
    "scripts/run-ptg-cal-check.py", "scripts/yuan-shadow-migrate.py",
    "scripts/yuan_shadow_migrate.py", "scripts/yuan_shadow_support.py",
}
MD_HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
FENCE = re.compile(r"^[ \t]*(```+|~~~+)")
SH_FUNCTION = re.compile(r"^[ \t]*(?:function[ \t]+)?([A-Za-z_][A-Za-z0-9_]*)[ \t]*(?:\(\))?[ \t]*\{[ \t]*$")
SH_SECTION = re.compile(r"^[ \t]*#[ \t]*(?:[-=]{2,}[ \t]*)?([^#].*?)(?:[ \t]*[-=]{2,})?[ \t]*$")

NORMATIVE_DOCS = {
    "docs/ARCHITECTURE.md", "docs/CONVENTIONS.md", "docs/INDEX.md",
    "docs/SETUP.md", "docs/anti-patterns.md", "docs/glossary.md",
    "docs/object-model.yaml", "docs/pitfalls.md", "docs/ptg-critical.md",
    "docs/MVP专家团对标与YuanForge优化.md",
}

EXTENSION_PATHS = {
    "testing": ".yuan/extensions/testing.md",
    "docsos": ".yuan/extensions/docsos.md",
    "knowledge": ".yuan/extensions/knowledge.md",
    "ui": ".yuan/extensions/ui.md",
    "software-delivery": ".yuan/extensions/software-delivery.md",
    "platform-adapters": ".yuan/extensions/platform-adapters.md",
}
DISPOSITION_FAMILIES = {
    "core": {"core"},
    "extension": set(EXTENSION_PATHS),
    "knowledge": {"knowledge"},
    "fixture": {"fixture"},
    "obsolete-with-proof": {"obsolete"},
}
RELATIONS = {
    "core": {"preserved", "refined", "superseded"},
    "extension": {"preserved", "refined", "superseded"},
    "knowledge": {"preserved", "superseded"},
    "fixture": {"fixture"},
    "obsolete-with-proof": {"obsolete"},
}
REQUIRED_SEMANTIC_BINDINGS = {
    (".yuan/rules/iron-rules.md", 90): (
        "extension", "testing", ".yuan/extensions/testing.md", "md:verifier-recipe:1",
    ),
    (".yuan/rules/iron-rules.md", 160): (
        "extension", "docsos", ".yuan/extensions/docsos.md", "md:document-verification:1",
    ),
    (".yuan/rules/iron-rules.md", 374): (
        "extension", "testing", ".yuan/extensions/testing.md", "md:actor-checker-separation:1",
    ),
    (".yuan/specs/object-protocol.md", 36): (
        "extension", "knowledge", ".yuan/extensions/knowledge.md", "md:record-shape:1",
    ),
    (".yuan/specs/object-protocol.md", 61): (
        "extension", "knowledge", ".yuan/extensions/knowledge.md", "md:promotion-advice:1",
    ),
    ("contracts/frontend-dev.md", 24): (
        "extension", "testing", ".yuan/extensions/testing.md", "md:verifier-recipe:1",
    ),
    ("contracts/quality-auditor.md", 57): (
        "extension", "software-delivery", ".yuan/extensions/software-delivery.md", "md:review-recipe:1",
    ),
}
COMPOUND_EXPECTED = {
    259: "testing", 279: "knowledge", 303: "software-delivery",
    305: "software-delivery", 315: "software-delivery",
    342: "software-delivery", 373: "testing", 383: "software-delivery",
    406: "software-delivery", 422: "software-delivery",
    434: "software-delivery", 444: "knowledge",
    456: "software-delivery", 478: "docsos",
    490: "software-delivery", 504: "docsos",
    529: "software-delivery", 538: "software-delivery",
    549: "software-delivery", 554: "software-delivery",
    572: "software-delivery",
}
COMPOUND_PATH = ".yuan/specs/workflow-protocol.md"
COMPOUND_ANCHOR = "md:phase-4b-tester-测试验证:1"


class ProvenanceFailure(RuntimeError):
    pass


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


@lru_cache(maxsize=None)
def git_blob(repo: Path, revision: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{revision}:{path}"],
        cwd=repo, capture_output=True, check=True,
    )
    return result.stdout


@lru_cache(maxsize=None)
def frozen_tree(repo: Path) -> tuple[str, ...]:
    result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", "-z", FROZEN_SOURCE_REVISION],
        cwd=repo, capture_output=True, check=True,
    )
    return tuple(sorted(part.decode("utf-8") for part in result.stdout.split(b"\0") if part))


def expected_decision(path: str) -> str:
    if path in {".gitignore", "AGENTS.md", "README.md", ".yuan/VERSION", "bin/yuanforge-init"}:
        return "include"
    include_prefixes = (
        ".yuan/core/0.1/", ".yuan/adapters/", ".yuan/migration/",
        ".yuan/platforms/", "contracts/", ".yuan/specs/", ".yuan/rules/",
        ".yuan/docs/", ".yuan/skills/", "protocols/", "templates/",
        "docs/policies/", "docs/knowledge/", "references/",
    )
    if path.startswith(include_prefixes) or path in NORMATIVE_DOCS:
        return "include"
    if path.startswith("scripts/") and path != "scripts/yuan-provenance.py":
        return "include"
    return "exclude"


def byte_lines(data: bytes) -> tuple[list[bytes], list[int]]:
    lines = [line.encode("utf-8") for line in data.decode("utf-8").splitlines(keepends=True)]
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    return lines, offsets


def clause(data: bytes, start: int, end: int, first: int, last: int, anchor: str, heading: str | None, granularity: str) -> dict[str, Any]:
    return {
        "anchor": anchor, "heading": heading,
        "line_start": first, "line_end": last,
        "byte_start": start, "byte_end": end,
        "clause_sha256": hash_bytes(data[start:end]),
        "granularity": granularity,
    }


def assemble(data: bytes, lines: list[bytes], boundaries: list[tuple[int, int, str, str | None]], kind: str) -> list[dict[str, Any]]:
    if not boundaries:
        return [clause(data, 0, len(data), 1, max(1, len(lines)), "whole:file", None, "content-addressed-whole-file")]
    output: list[dict[str, Any]] = []
    if boundaries[0][0] > 0:
        output.append(clause(data, 0, boundaries[0][0], 1, boundaries[0][1] - 1, f"{kind}:preamble", None, f"{kind}-preamble"))
    for index, current in enumerate(boundaries):
        start, first, anchor, heading = current
        if index + 1 < len(boundaries):
            end, last = boundaries[index + 1][0], boundaries[index + 1][1] - 1
        else:
            end, last = len(data), max(first, len(lines))
        output.append(clause(data, start, end, first, last, anchor, heading, kind))
    return output


def split_markdown(data: bytes) -> list[dict[str, Any]]:
    lines, offsets = byte_lines(data)
    boundaries: list[tuple[int, int, str, str | None]] = []
    seen: Counter[str] = Counter()
    fenced = False
    fence_char = ""
    for index, raw in enumerate(lines):
        text = raw.decode("utf-8").rstrip("\r\n")
        marker = FENCE.match(text)
        if marker:
            token = marker.group(1)
            if not fenced:
                fenced, fence_char = True, token[0]
            elif token[0] == fence_char:
                fenced, fence_char = False, ""
            continue
        if fenced:
            continue
        heading = MD_HEADING.match(text)
        if not heading:
            continue
        title = heading.group(2).strip()
        slug = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "-", title.lower()).strip("-") or "heading"
        seen[slug] += 1
        boundaries.append((offsets[index], index + 1, f"md:{slug}:{seen[slug]}", title))
    return assemble(data, lines, boundaries, "markdown-heading")


def split_python(data: bytes) -> list[dict[str, Any]]:
    tree = ast.parse(data.decode("utf-8"))
    lines, offsets = byte_lines(data)
    boundaries: list[tuple[int, int, str, str | None]] = []
    seen: Counter[str] = Counter()
    for node in tree.body:
        first = getattr(node, "lineno", 1)
        decorators = getattr(node, "decorator_list", [])
        if decorators:
            first = min([first] + [part.lineno for part in decorators])
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            kind, name = "function", node.name
        elif isinstance(node, ast.ClassDef):
            kind, name = "class", node.name
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            kind, name = "import", getattr(node, "module", None) or "names"
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            kind, name = "assignment", f"line-{first}"
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            kind, name = "module-docstring", "docstring"
        else:
            kind, name = type(node).__name__.lower(), f"line-{first}"
        base = f"py:{kind}:{name}"
        seen[base] += 1
        boundaries.append((offsets[first - 1], first, f"{base}:{seen[base]}", f"{kind} {name}"))
    return assemble(data, lines, boundaries, "python-ast")


def split_shell(data: bytes) -> list[dict[str, Any]]:
    lines, offsets = byte_lines(data)
    boundaries: list[tuple[int, int, str, str | None]] = []
    seen: Counter[str] = Counter()
    for index, raw in enumerate(lines):
        text = raw.decode("utf-8").rstrip("\r\n")
        function = SH_FUNCTION.match(text)
        section = SH_SECTION.match(text)
        if function:
            base, title = f"sh:function:{function.group(1)}", f"function {function.group(1)}"
        elif section and len(section.group(1).strip()) >= 4 and index > 0:
            title = section.group(1).strip()
            slug = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "-", title.lower()).strip("-") or f"line-{index + 1}"
            base = f"sh:section:{slug}"
        else:
            continue
        seen[base] += 1
        boundaries.append((offsets[index], index + 1, f"{base}:{seen[base]}", title))
    return assemble(data, lines, boundaries, "shell-unit")


def independent_split(data: bytes, path: str) -> list[dict[str, Any]]:
    suffix = Path(path).suffix.lower()
    first = data.splitlines()[0].decode("utf-8", "ignore") if data.splitlines() else ""
    if suffix == ".md":
        return split_markdown(data)
    if suffix == ".py" or "python" in first:
        return split_python(data)
    if suffix in {".sh", ".bash"} or "bash" in first or first.endswith("/sh"):
        return split_shell(data)
    lines = data.decode("utf-8", "replace").splitlines()
    return [clause(data, 0, len(data), 1, max(1, len(lines)), "whole:file", None, "content-addressed-whole-file")]


def key_for(path: str, anchor: str, content_hash: str) -> str:
    return hash_bytes(f"{path}\n{anchor}\n{content_hash}".encode("utf-8"))


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def resolve_source(repo: Path, entry: dict[str, Any]) -> bytes:
    source = entry["source"]
    if source["kind"] == "git":
        if source["revision"] != FROZEN_SOURCE_REVISION or source["path"] != entry["path"]:
            raise ProvenanceFailure(f"invalid git source binding: {entry['path']}")
        return git_blob(repo, source["revision"], source["path"])
    if source["kind"] == "content-addressed-snapshot":
        path = repo / source["path"]
        if not path.is_file():
            raise ProvenanceFailure(f"dirty source snapshot missing: {entry['path']}")
        return path.read_bytes()
    raise ProvenanceFailure(f"unknown source kind: {entry['path']}")


def validate_markdown_target(repo: Path, target: dict[str, str]) -> None:
    path = repo / target["path"]
    if not path.is_file():
        raise ProvenanceFailure(f"target missing: {target['path']}")
    matches = [part for part in split_markdown(path.read_bytes()) if part["anchor"] == target["anchor"]]
    if len(matches) != 1 or matches[0]["clause_sha256"] != target["clause_sha256"]:
        raise ProvenanceFailure(f"target anchor/hash mismatch: {target['path']}#{target['anchor']}")


def validate_fixture_target(repo: Path, target: dict[str, str]) -> None:
    path = repo / target["path"]
    if not path.is_file() or not target["anchor"].startswith("case:"):
        raise ProvenanceFailure(f"fixture target missing/invalid: {target}")
    case_id = target["anchor"].split(":", 1)[1]
    payload = json.loads(path.read_text(encoding="utf-8"))
    matches = [case for case in payload["cases"] if case["id"] == case_id]
    if len(matches) != 1:
        raise ProvenanceFailure(f"fixture case missing/duplicate: {case_id}")
    encoded = json.dumps(matches[0], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if hash_bytes(encoded) != target["clause_sha256"]:
        raise ProvenanceFailure(f"fixture case hash mismatch: {case_id}")


def verify(
    repo: Path,
    prov: Path,
    expected_registry_sha256: str | None = None,
) -> dict[str, Any]:
    inventory_raw = (prov / "inventory.lock.json").read_bytes()
    registry_raw = (prov / "semantic-registry.json").read_bytes()
    manifest_raw = (prov / "clause-manifest.json").read_bytes()
    family_raw = (prov / "target-family-registry.json").read_bytes()
    inventory = json.loads(inventory_raw)
    registry = json.loads(registry_raw)
    family_registry = json.loads(family_raw)
    registry_sha256 = hash_bytes(registry_raw)
    pinned = (prov / "semantic-registry.sha256").read_text(encoding="utf-8").strip()
    if pinned != registry_sha256:
        raise ProvenanceFailure("semantic registry hash pin mismatch")
    if expected_registry_sha256 is not None and registry_sha256 != expected_registry_sha256:
        raise ProvenanceFailure("semantic registry hash differs from reviewed value")
    if manifest_raw != registry_raw:
        raise ProvenanceFailure("registry/manifest byte drift")
    if registry["target_family_registry_sha256"] != hash_bytes(family_raw):
        raise ProvenanceFailure("target family registry hash mismatch")
    if inventory["source_revision"] != FROZEN_SOURCE_REVISION:
        raise ProvenanceFailure("inventory source revision is not frozen")
    if registry["source_revision"] != FROZEN_SOURCE_REVISION:
        raise ProvenanceFailure("semantic registry source revision is not frozen")
    if registry["inventory_lock_sha256"] != hash_bytes(inventory_raw):
        raise ProvenanceFailure("semantic registry inventory binding mismatch")

    allowed_targets: dict[str, set[tuple[str, str, str, str]]] = {}
    seen_targets: set[tuple[str, str, str, str]] = set()
    for family, descriptor in family_registry["families"].items():
        targets: set[tuple[str, str, str, str]] = set()
        for target in descriptor.get("targets", []):
            token = (target["kind"], target["path"], target["anchor"], target["sha256"])
            if token in seen_targets:
                raise ProvenanceFailure(f"duplicate target registry entry: {token}")
            seen_targets.add(token)
            targets.add(token)
            path = repo / target["path"]
            if not path.is_file():
                raise ProvenanceFailure(f"target missing: {target['path']}")
            clauses = independent_split(path.read_bytes(), target["path"])
            matches = [part for part in clauses if part["anchor"] == target["anchor"]]
            if len(matches) != 1 or matches[0]["clause_sha256"] != target["sha256"]:
                raise ProvenanceFailure(
                    f"target anchor/hash mismatch: {target['path']}#{target['anchor']}"
                )
            if family == "core" and not target["path"].startswith(".yuan/core/0.1/"):
                raise ProvenanceFailure("core family target escapes Core 0.1")
            if family in EXTENSION_PATHS and target["path"] != EXTENSION_PATHS[family]:
                raise ProvenanceFailure(f"target family/path mismatch: {family}")
        allowed_targets[family] = targets

    tree = frozen_tree(repo)
    entries = inventory["entries"]
    if len({entry["path"] for entry in entries}) != len(entries):
        raise ProvenanceFailure("duplicate inventory path")
    tracked_entries = {entry["path"]: entry for entry in entries if entry["tracked_at_source"]}
    if set(tracked_entries) != set(tree):
        raise ProvenanceFailure("inventory does not exhaustively match frozen tracked tree")
    out_of_band = {entry["path"]: entry for entry in entries if not entry["tracked_at_source"]}
    if {path: entry["decision"] for path, entry in out_of_band.items()} != EXPECTED_OUT_OF_BAND:
        raise ProvenanceFailure("out-of-band inventory is not the frozen M0 set")

    for path in tree:
        entry = tracked_entries[path]
        tracked = git_blob(repo, FROZEN_SOURCE_REVISION, path)
        if hash_bytes(tracked) != entry["tracked_sha256"]:
            raise ProvenanceFailure(f"tracked hash mismatch: {path}")
        if entry["decision"] != expected_decision(path):
            raise ProvenanceFailure(f"independent include/exclude mismatch: {path}")
        if not entry.get("reason"):
            raise ProvenanceFailure(f"inventory reason missing: {path}")
    if any(path not in tree for path in KEY_SCRIPTS):
        raise ProvenanceFailure("key script absent from frozen tree")
    if any(tracked_entries[path]["decision"] != "include" for path in KEY_SCRIPTS):
        raise ProvenanceFailure("key script excluded from scope")

    required_paths = {
        "AGENTS.md", "README.md", ".gitignore", ".yuan/rules/test-integrity.md",
    }
    if any(next(entry for entry in entries if entry["path"] == path)["decision"] != "include" for path in required_paths):
        raise ProvenanceFailure("required singleton family excluded")
    required_prefixes = (
        "contracts/", ".yuan/specs/", ".yuan/rules/", ".yuan/docs/",
        ".yuan/skills/", ".yuan/platforms/", ".yuan/adapters/",
        ".yuan/migration/", "protocols/", "templates/", "docs/policies/",
        "docs/knowledge/", "references/",
    )
    for prefix in required_prefixes:
        if not any(entry["decision"] == "include" and entry["path"].startswith(prefix) for entry in entries):
            raise ProvenanceFailure(f"required family empty: {prefix}")
    exclusions = {entry["path"] for entry in inventory["filesystem_exclusions"]}
    if not REQUIRED_EXCLUSIONS.issubset(exclusions):
        raise ProvenanceFailure("required filesystem exclusion missing")

    receipt = json.loads((prov / "dirty-source-receipt.json").read_text(encoding="utf-8"))
    tracked_m0 = read_tsv(repo / "docs/20260726-yuan-core-01-upgrade/evidence/m0a/tracked-dirty.tsv")
    untracked_m0 = read_tsv(repo / "docs/20260726-yuan-core-01-upgrade/evidence/m0a/untracked-files.tsv")
    expected_dirty = {row["path"]: row["sha256"] for row in tracked_m0 + untracked_m0}
    receipt_sources = {row["logical_path"]: row for row in receipt["sources"]}
    if set(receipt_sources) != set(expected_dirty):
        raise ProvenanceFailure("dirty receipt does not reproduce all M0 sources")
    for path, expected_hash in expected_dirty.items():
        record = receipt_sources[path]
        snapshot = repo / record["snapshot_path"]
        if not snapshot.is_file() or hash_bytes(snapshot.read_bytes()) != expected_hash:
            raise ProvenanceFailure(f"dirty snapshot missing/hash mismatch: {path}")

    records = registry["records"]
    if registry["semantic_record_count"] != len(records):
        raise ProvenanceFailure("semantic record count mismatch")
    if len({record["record_key"] for record in records}) != len(records):
        raise ProvenanceFailure("duplicate semantic record key")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        grouped.setdefault(record["source_mapping_key"], []).append(record)
    expected_keys: set[str] = set()
    expected_files: list[dict[str, Any]] = []
    expected_clauses: list[dict[str, Any]] = []
    retained_names: set[str] = set()
    legacy_core = 0
    ap_ids: set[str] = set()
    ptg_obsolete: list[str] = []

    for entry in sorted((item for item in entries if item["decision"] == "include"), key=lambda item: item["path"]):
        data = resolve_source(repo, entry)
        if hash_bytes(data) != entry["source_sha256"]:
            raise ProvenanceFailure(f"included source hash mismatch: {entry['path']}")
        parts = independent_split(data, entry["path"])
        line_count = max(1, len(data.decode("utf-8", "replace").splitlines()))
        if not parts or parts[0]["byte_start"] != 0 or parts[-1]["byte_end"] != len(data):
            raise ProvenanceFailure(f"source byte coverage incomplete: {entry['path']}")
        for left, right in zip(parts, parts[1:]):
            if left["byte_end"] != right["byte_start"]:
                raise ProvenanceFailure(f"source byte gap/overlap: {entry['path']}")
        expected_files.append({
            "path": entry["path"], "source_sha256": entry["source_sha256"],
            "source_kind": entry["source"]["kind"], "bytes": len(data),
            "clause_count": len(parts),
        })
        for part in parts:
            if not (1 <= part["line_start"] <= part["line_end"] <= line_count):
                raise ProvenanceFailure(f"invalid inclusive range: {entry['path']}#{part['anchor']}")
            key = key_for(entry["path"], part["anchor"], part["clause_sha256"])
            expected_keys.add(key)
            clause_records = grouped.get(key)
            if not clause_records:
                raise ProvenanceFailure(f"UNMAPPED clause: {entry['path']}#{part['anchor']}")
            is_compound = len(clause_records) > 1 or "parent_source_anchor" in clause_records[0]
            if is_compound:
                if entry["path"] != COMPOUND_PATH or part["anchor"] != COMPOUND_ANCHOR:
                    raise ProvenanceFailure("unexpected compound clause")
                starts = {record["line_start"]: record["target_family"] for record in clause_records}
                if starts != COMPOUND_EXPECTED:
                    raise ProvenanceFailure("compound clause family coverage mismatch")
                ordered = sorted(clause_records, key=lambda record: record["byte_start"])
                if (
                    ordered[0]["byte_start"] != part["byte_start"]
                    or ordered[-1]["byte_end"] != part["byte_end"]
                    or any(left["byte_end"] != right["byte_start"] for left, right in zip(ordered, ordered[1:]))
                ):
                    raise ProvenanceFailure("compound clause byte coverage mismatch")
                parent_destinations = {
                    json.dumps(record.get("parent_destination"), sort_keys=True)
                    for record in clause_records
                }
                if len(parent_destinations) != 1:
                    raise ProvenanceFailure("compound clause parent destination mismatch")
                parent_destination = clause_records[0]["parent_destination"]
                parent_blob = repo / parent_destination["path"]
                parent_bytes = data[part["byte_start"]:part["byte_end"]]
                if (
                    parent_destination["sha256"] != part["clause_sha256"]
                    or not parent_blob.is_file()
                    or parent_blob.read_bytes() != parent_bytes
                ):
                    raise ProvenanceFailure("compound clause retained parent mismatch")
                retained_names.add(parent_blob.name)
            else:
                record = clause_records[0]
                for field, value in (
                    ("source", entry["path"]), ("anchor", part["anchor"]),
                    ("clause_sha256", part["clause_sha256"]),
                    ("byte_start", part["byte_start"]), ("byte_end", part["byte_end"]),
                    ("line_start", part["line_start"]), ("line_end", part["line_end"]),
                ):
                    if record[field] != value:
                        raise ProvenanceFailure(f"semantic source identity mismatch: {key}")

            for record in clause_records:
                if any(token in record for token in ("mapping_rule", "default", "keyword", "review_rationale")):
                    raise ProvenanceFailure(f"heuristic semantic metadata forbidden: {record['record_key']}")
                disposition = record["disposition"]
                family = record["target_family"]
                if family not in DISPOSITION_FAMILIES.get(disposition, set()):
                    raise ProvenanceFailure("disposition/target family mismatch")
                if record["relation"] not in RELATIONS[disposition]:
                    raise ProvenanceFailure("invalid semantic relation")
                if not record.get("source_claim", "").strip() or not record.get("target_claim", "").strip():
                    raise ProvenanceFailure("source_claim/target_claim missing")
                record_bytes = data[record["byte_start"]:record["byte_end"]]
                if hash_bytes(record_bytes) != record["clause_sha256"]:
                    raise ProvenanceFailure(f"semantic record byte hash mismatch: {record['record_key']}")
                destination = record["destination"]
                blob = repo / destination["path"]
                if (
                    destination["kind"] != "content-addressed-retained-clause"
                    or destination["sha256"] != record["clause_sha256"]
                    or not blob.is_file()
                    or blob.read_bytes() != record_bytes
                ):
                    raise ProvenanceFailure(f"retained destination mismatch: {record['record_key']}")
                retained_names.add(blob.name)
                target = record["target"]
                token = (target["kind"], target["path"], target["anchor"], target["sha256"])
                if target["kind"] in {"semantic-anchor", "core-registry-anchor"}:
                    if token not in allowed_targets.get(family, set()):
                        raise ProvenanceFailure("target family/path mismatch")
                elif target["kind"] == "retained-clause":
                    if family in {"core", "fixture"} or target["path"] != destination["path"] or target["sha256"] != destination["sha256"]:
                        raise ProvenanceFailure("target family/path mismatch")
                elif target["kind"] == "fixture-case":
                    if family != "fixture":
                        raise ProvenanceFailure("target family/path mismatch")
                    validate_fixture_target(repo, {
                        "path": target["path"], "anchor": target["anchor"],
                        "clause_sha256": target["sha256"],
                    })
                else:
                    raise ProvenanceFailure(f"unknown semantic target kind: {target['kind']}")

            mapping = clause_records[0]
            disposition = mapping["disposition"]
            if disposition == "obsolete-with-proof":
                proof = mapping.get("obsolete") or {}
                if proof.get("source_sha256") != part["clause_sha256"] or not proof.get("reason"):
                    raise ProvenanceFailure(f"obsolete proof source/reason invalid: {key}")
                validate_markdown_target(repo, proof["replacement"])
                validate_fixture_target(repo, proof["fixture"])
            if disposition == "core" and not entry["path"].startswith(".yuan/core/0.1/"):
                legacy_core += 1
            if entry["path"] == "docs/anti-patterns.md" and part["heading"] and part["heading"].startswith("AP-"):
                ap_id = part["heading"].split(":", 1)[0]
                ap_ids.add(ap_id)
                if disposition not in {"fixture", "knowledge"}:
                    raise ProvenanceFailure(f"anti-pattern not retained as fixture/knowledge: {ap_id}")
                if mapping.get("fixture_target", {}).get("anchor") != f"case:{ap_id}":
                    raise ProvenanceFailure(f"anti-pattern fixture target missing: {ap_id}")
            if entry["path"] == "scripts/run-ptg-cal-check.py":
                if "generate_report" in part["anchor"]:
                    if disposition != "obsolete-with-proof":
                        raise ProvenanceFailure("false-green PTG gate is not obsolete-with-proof")
                    ptg_obsolete.append(part["anchor"])
                elif disposition == "obsolete-with-proof":
                    raise ProvenanceFailure("only the false-green PTG gate may be obsolete")

            expected_clauses.append({"mapping_key": key, "source": entry["path"], **part})

    if set(grouped) != expected_keys:
        raise ProvenanceFailure("semantic registry has stale/extra clauses")
    if legacy_core != 12:
        raise ProvenanceFailure("reviewed legacy-to-Core count is not 12")
    if len(ptg_obsolete) != 1:
        raise ProvenanceFailure("PTG runner obsolete function count is not exactly one")
    fixture_payload = json.loads((repo / ".yuan/extensions/fixtures/legacy-anti-patterns.json").read_text(encoding="utf-8"))
    fixture_ids = {case["id"] for case in fixture_payload["cases"]}
    if not ap_ids.issubset(fixture_ids):
        raise ProvenanceFailure("not every AP entry is preserved in fixture catalog")

    retained_actual = {path.name for path in (prov / "retained").glob("*.blob")}
    if retained_actual != retained_names:
        raise ProvenanceFailure("retained clause pack has missing or unreferenced blobs")

    bindings = {(record["source"], record["line_start"]): record for record in records}
    for identity, expected in REQUIRED_SEMANTIC_BINDINGS.items():
        record = bindings.get(identity)
        if record is None:
            raise ProvenanceFailure(f"required semantic binding missing: {identity}")
        actual = (
            record["disposition"], record["target_family"],
            record["target"]["path"], record["target"]["anchor"],
        )
        if actual != expected:
            raise ProvenanceFailure(f"required semantic binding mismatch: {identity}")
    claim_pairs = {(record["source_claim"], record["target_claim"]) for record in records}
    if len(claim_pairs) != len(records):
        raise ProvenanceFailure("source_claim/target_claim pair is not record-specific")

    scope_expected = {
        "schema_version": "yuan.provenance-scope/v2",
        "inventory_lock_sha256": hash_bytes(inventory_raw),
        "source_revision": FROZEN_SOURCE_REVISION,
        "tracked_inventory_count": inventory["source_revision_tracked_count"],
        "out_of_band_count": inventory["out_of_band_count"],
        "included_source_count": len(expected_files),
        "included_source_bytes": sum(record["bytes"] for record in expected_files),
        "source_clause_count": len(expected_clauses),
        "files": expected_files,
        "excluded_entries": [
            {"path": entry["path"], "reason": entry["reason"]}
            for entry in entries if entry["decision"] == "exclude"
        ],
        "filesystem_exclusions": inventory["filesystem_exclusions"],
    }
    scope_actual = json.loads((prov / "scope-manifest.json").read_text(encoding="utf-8"))
    if scope_actual != scope_expected:
        raise ProvenanceFailure("scope manifest is stale or independently inconsistent")
    if registry["scope_sha256"] != hash_bytes(json_bytes(scope_expected)):
        raise ProvenanceFailure("semantic registry scope binding mismatch")
    if registry["source_clause_count"] != len(expected_clauses):
        raise ProvenanceFailure("semantic registry source clause count mismatch")

    return {
        "status": "PASS",
        "tracked_inventory": len(tree),
        "out_of_band": len(out_of_band),
        "included_sources": len(expected_files),
        "source_clauses": len(expected_clauses),
        "semantic_records": len(records),
        "mapped": len(records),
        "unmapped": 0,
        "registry_sha256": registry_sha256,
        "families": dict(sorted(Counter(record["target_family"] for record in records).items())),
        "legacy_to_core": legacy_core,
        "anti_patterns": len(ap_ids),
        "ptg_obsolete_functions": len(ptg_obsolete),
        "dirty_snapshots": len(expected_dirty),
    }
