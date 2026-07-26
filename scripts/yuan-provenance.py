#!/usr/bin/env python3
"""Generate provenance only from a frozen inventory and explicit clause map."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROV = ROOT / ".yuan/extensions/provenance"
MD_HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
FENCE = re.compile(r"^[ \t]*(```+|~~~+)")
SHELL_FUNCTION = re.compile(r"^[ \t]*(?:function[ \t]+)?([A-Za-z_][A-Za-z0-9_]*)[ \t]*(?:\(\))?[ \t]*\{[ \t]*$")
SHELL_SECTION = re.compile(r"^[ \t]*#[ \t]*(?:[-=]{2,}[ \t]*)?([^#].*?)(?:[ \t]*[-=]{2,})?[ \t]*$")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def line_data(data: bytes) -> tuple[list[bytes], list[int]]:
    lines = [line.encode("utf-8") for line in data.decode("utf-8").splitlines(keepends=True)]
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    return lines, offsets


def item(data: bytes, start: int, end: int, first: int, last: int, anchor: str, heading: str | None, granularity: str) -> dict[str, Any]:
    return {
        "anchor": anchor,
        "heading": heading,
        "line_start": first,
        "line_end": last,
        "byte_start": start,
        "byte_end": end,
        "clause_sha256": sha(data[start:end]),
        "granularity": granularity,
    }


def partition(data: bytes, lines: list[bytes], boundaries: list[tuple[int, int, str, str | None]], granularity: str) -> list[dict[str, Any]]:
    if not boundaries:
        return [item(data, 0, len(data), 1, max(1, len(lines)), "whole:file", None, "content-addressed-whole-file")]
    result: list[dict[str, Any]] = []
    if boundaries[0][0] > 0:
        result.append(item(data, 0, boundaries[0][0], 1, boundaries[0][1] - 1, f"{granularity}:preamble", None, f"{granularity}-preamble"))
    for index, (start, first, anchor, heading) in enumerate(boundaries):
        end = boundaries[index + 1][0] if index + 1 < len(boundaries) else len(data)
        last = boundaries[index + 1][1] - 1 if index + 1 < len(boundaries) else max(first, len(lines))
        result.append(item(data, start, end, first, last, anchor, heading, granularity))
    return result


def markdown_clauses(data: bytes) -> list[dict[str, Any]]:
    lines, offsets = line_data(data)
    boundaries: list[tuple[int, int, str, str | None]] = []
    counts: Counter[str] = Counter()
    in_fence = False
    fence_char = ""
    for index, raw in enumerate(lines):
        text = raw.decode("utf-8").rstrip("\r\n")
        fence = FENCE.match(text)
        if fence:
            marker = fence.group(1)
            if not in_fence:
                in_fence, fence_char = True, marker[0]
            elif marker[0] == fence_char:
                in_fence, fence_char = False, ""
            continue
        if in_fence:
            continue
        match = MD_HEADING.match(text)
        if not match:
            continue
        heading = match.group(2).strip()
        slug = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "-", heading.lower()).strip("-") or "heading"
        counts[slug] += 1
        boundaries.append((offsets[index], index + 1, f"md:{slug}:{counts[slug]}", heading))
    return partition(data, lines, boundaries, "markdown-heading")


def python_clauses(data: bytes) -> list[dict[str, Any]]:
    tree = ast.parse(data.decode("utf-8"))
    lines, offsets = line_data(data)
    boundaries: list[tuple[int, int, str, str | None]] = []
    counts: Counter[str] = Counter()
    for node in tree.body:
        first = getattr(node, "lineno", 1)
        decorators = getattr(node, "decorator_list", [])
        if decorators:
            first = min([first] + [decorator.lineno for decorator in decorators])
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
        counts[base] += 1
        boundaries.append((offsets[first - 1], first, f"{base}:{counts[base]}", f"{kind} {name}"))
    return partition(data, lines, boundaries, "python-ast")


def shell_clauses(data: bytes) -> list[dict[str, Any]]:
    lines, offsets = line_data(data)
    boundaries: list[tuple[int, int, str, str | None]] = []
    counts: Counter[str] = Counter()
    for index, raw in enumerate(lines):
        text = raw.decode("utf-8").rstrip("\r\n")
        function = SHELL_FUNCTION.match(text)
        section = SHELL_SECTION.match(text)
        if function:
            base, heading = f"sh:function:{function.group(1)}", f"function {function.group(1)}"
        elif section and len(section.group(1).strip()) >= 4 and index > 0:
            heading = section.group(1).strip()
            slug = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "-", heading.lower()).strip("-") or f"line-{index + 1}"
            base = f"sh:section:{slug}"
        else:
            continue
        counts[base] += 1
        boundaries.append((offsets[index], index + 1, f"{base}:{counts[base]}", heading))
    return partition(data, lines, boundaries, "shell-unit")


def split_clauses(data: bytes, path: str) -> list[dict[str, Any]]:
    suffix = Path(path).suffix.lower()
    first = data.splitlines()[0].decode("utf-8", "ignore") if data.splitlines() else ""
    if suffix == ".md":
        return markdown_clauses(data)
    if suffix == ".py" or "python" in first:
        return python_clauses(data)
    if suffix in {".sh", ".bash"} or "bash" in first or first.endswith("/sh"):
        return shell_clauses(data)
    lines = data.decode("utf-8", "replace").splitlines()
    return [item(data, 0, len(data), 1, max(1, len(lines)), "whole:file", None, "content-addressed-whole-file")]


@lru_cache(maxsize=None)
def git_source(revision: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{revision}:{path}"],
        cwd=ROOT, check=True, capture_output=True,
    ).stdout


def source_bytes(entry: dict[str, Any]) -> bytes:
    source = entry["source"]
    if source["kind"] == "git":
        return git_source(source["revision"], source["path"])
    if source["kind"] == "content-addressed-snapshot":
        return (ROOT / source["path"]).read_bytes()
    raise ValueError(f"unsupported source kind: {source.get('kind')}")


def mapping_key(path: str, anchor: str, clause_hash: str) -> str:
    return sha(f"{path}\n{anchor}\n{clause_hash}".encode("utf-8"))


def build(prov: Path) -> tuple[dict[str, Any], dict[str, Any], str, dict[str, bytes]]:
    inventory_bytes = (prov / "inventory.lock.json").read_bytes()
    inventory = json.loads(inventory_bytes)
    registry_bytes = (prov / "semantic-registry.json").read_bytes()
    registry = json.loads(registry_bytes)
    target_registry_bytes = (prov / "target-family-registry.json").read_bytes()
    included = [entry for entry in inventory["entries"] if entry["decision"] == "include"]
    file_records: list[dict[str, Any]] = []
    source_clauses: dict[str, dict[str, Any]] = {}
    source_payloads: dict[str, bytes] = {}
    retained: dict[str, bytes] = {}

    for entry in included:
        data = source_bytes(entry)
        source_payloads[entry["path"]] = data
        if sha(data) != entry["source_sha256"]:
            raise ValueError(f"source hash drift: {entry['path']}")
        clauses = split_clauses(data, entry["path"])
        file_records.append({
            "path": entry["path"],
            "source_sha256": entry["source_sha256"],
            "source_kind": entry["source"]["kind"],
            "bytes": len(data),
            "clause_count": len(clauses),
        })
        for clause in clauses:
            key = mapping_key(entry["path"], clause["anchor"], clause["clause_sha256"])
            source_clauses[key] = {
                "mapping_key": key,
                "source": entry["path"],
                "source_sha256": entry["source_sha256"],
                **clause,
            }

    scope = {
        "schema_version": "yuan.provenance-scope/v2",
        "inventory_lock_sha256": sha(inventory_bytes),
        "source_revision": inventory["source_revision"],
        "tracked_inventory_count": inventory["source_revision_tracked_count"],
        "out_of_band_count": inventory["out_of_band_count"],
        "included_source_count": len(included),
        "included_source_bytes": sum(record["bytes"] for record in file_records),
        "source_clause_count": len(source_clauses),
        "files": sorted(file_records, key=lambda record: record["path"]),
        "excluded_entries": [
            {"path": entry["path"], "reason": entry["reason"]}
            for entry in inventory["entries"] if entry["decision"] == "exclude"
        ],
        "filesystem_exclusions": inventory["filesystem_exclusions"],
    }
    if registry["inventory_lock_sha256"] != sha(inventory_bytes):
        raise ValueError("semantic registry inventory binding mismatch")
    if registry["scope_sha256"] != sha(canonical(scope)):
        raise ValueError("semantic registry scope binding mismatch")
    if registry["target_family_registry_sha256"] != sha(target_registry_bytes):
        raise ValueError("semantic registry target-family binding mismatch")
    pinned = (prov / "semantic-registry.sha256").read_text(
        encoding="ascii"
    ).strip()
    if pinned != sha(registry_bytes):
        raise ValueError("semantic registry hash pin mismatch")
    if registry["source_clause_count"] != len(source_clauses):
        raise ValueError("semantic registry source clause count mismatch")
    if registry["semantic_record_count"] != len(registry["records"]):
        raise ValueError("semantic registry record count mismatch")

    reviewed_groups: dict[str, list[dict[str, Any]]] = {}
    record_keys: set[str] = set()
    for record in registry["records"]:
        key = record["source_mapping_key"]
        reviewed_groups.setdefault(key, []).append(record)
        if record["record_key"] in record_keys:
            raise ValueError(f"duplicate semantic record key: {record['record_key']}")
        record_keys.add(record["record_key"])

    missing = sorted(set(source_clauses) - set(reviewed_groups))
    extra = sorted(set(reviewed_groups) - set(source_clauses))
    if missing:
        raise ValueError(f"UNMAPPED source clauses: {len(missing)}")
    if extra:
        raise ValueError(f"semantic registry has stale/extra source clauses: {len(extra)}")

    identity_fields = (
        "source", "source_sha256", "anchor", "heading", "line_start",
        "line_end", "byte_start", "byte_end", "clause_sha256",
        "granularity",
    )
    for key, records in reviewed_groups.items():
        parent = source_clauses[key]
        data = source_payloads[parent["source"]]
        if len(records) == 1 and "parent_mapping_key" not in records[0]:
            record = records[0]
            if any(record[field] != parent[field] for field in identity_fields):
                raise ValueError(f"semantic registry source identity mismatch: {key}")
        else:
            ordered = sorted(records, key=lambda item: item["byte_start"])
            if any(record.get("parent_mapping_key") != key for record in ordered):
                raise ValueError(f"compound semantic parent mismatch: {key}")
            if ordered[0]["byte_start"] != parent["byte_start"]:
                raise ValueError(f"compound semantic range start mismatch: {key}")
            if ordered[-1]["byte_end"] != parent["byte_end"]:
                raise ValueError(f"compound semantic range end mismatch: {key}")
            for left, right in zip(ordered, ordered[1:]):
                if left["byte_end"] != right["byte_start"]:
                    raise ValueError(f"compound semantic range gap/overlap: {key}")
            parent_destination = ordered[0]["parent_destination"]
            parent_bytes = data[parent["byte_start"]:parent["byte_end"]]
            if (
                parent_destination["sha256"] != sha(parent_bytes)
                or any(
                    record["parent_destination"] != parent_destination
                    for record in ordered
                )
            ):
                raise ValueError(f"compound parent retained binding mismatch: {key}")
            retained[parent_destination["path"]] = parent_bytes

        for record in records:
            clause_bytes = data[record["byte_start"]:record["byte_end"]]
            if sha(clause_bytes) != record["clause_sha256"]:
                raise ValueError(f"semantic record byte hash mismatch: {record['record_key']}")
            destination = record["destination"]
            if (
                destination["kind"] != "content-addressed-retained-clause"
                or destination["sha256"] != record["clause_sha256"]
            ):
                raise ValueError(f"semantic retained destination mismatch: {record['record_key']}")
            retained[destination["path"]] = clause_bytes

    report = render_report(scope, registry, sha(registry_bytes))
    return scope, registry, report, retained


def render_report(
    scope: dict[str, Any],
    registry: dict[str, Any],
    registry_hash: str,
) -> str:
    counts = Counter(record["disposition"] for record in registry["records"])
    families = Counter(record["target_family"] for record in registry["records"])
    relations = Counter(record["relation"] for record in registry["records"])
    lines = [
        "# M7 Semantic Clause Provenance Report",
        "",
        "> Generated only from frozen source bytes and the reviewed semantic registry.",
        "",
        "## Coverage",
        "",
        f"- frozen tracked inventory: {scope['tracked_inventory_count']}",
        f"- out-of-band M0 sources: {scope['out_of_band_count']}",
        f"- included source files: {scope['included_source_count']}",
        f"- included source bytes: {scope['included_source_bytes']}",
        f"- source clauses: {scope['source_clause_count']}",
        f"- semantic records: {registry['semantic_record_count']}",
        "- unmapped source clauses: 0",
        "- coverage: 100.00%",
        f"- semantic registry SHA-256: `{registry_hash}`",
        "",
        "## Dispositions",
        "",
        "| Disposition | Clauses |",
        "|-------------|--------:|",
    ]
    for name in registry["allowed_dispositions"] + ["UNMAPPED"]:
        lines.append(f"| `{name}` | {counts[name]} |")
    lines.extend(["", "## Target families", ""])
    for name, count in sorted(families.items()):
        lines.append(f"- `{name}`: {count}")
    lines.extend(["", "## Relations", ""])
    for name, count in sorted(relations.items()):
        lines.append(f"- `{name}`: {count}")
    lines.extend([
        "",
        "## Trust boundary",
        "",
        "- The generator never infers, classifies, or rewrites semantic review decisions.",
        "- Unknown source+anchor+hash tuples fail as `UNMAPPED`.",
        "- `clause-manifest.json` is byte-identical to `semantic-registry.json`.",
        "- Every record binds a disposition, target family, exact target, source claim, target claim, and relation.",
        "- Every mapped clause points to an exact content-addressed retained blob.",
        "- Independent verification is performed by `scripts/verify-yuan-provenance.py`.",
        "- Legacy sources and protected dirty paths remain untouched.",
        "",
    ])
    return "\n".join(lines)


def generate(prov: Path) -> int:
    scope, registry, report, retained = build(prov)
    retained_root = prov / "retained"
    retained_root.mkdir(parents=True, exist_ok=True)
    expected_names = {Path(path).name for path in retained}
    for existing in retained_root.glob("*.blob"):
        if existing.name not in expected_names:
            existing.unlink()
    for path, data in retained.items():
        destination = ROOT / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    (prov / "scope-manifest.json").write_bytes(canonical(scope))
    registry_bytes = (prov / "semantic-registry.json").read_bytes()
    (prov / "clause-manifest.json").write_bytes(registry_bytes)
    (prov / "REPORT.md").write_text(report, encoding="utf-8", newline="\n")
    print(
        "PASS "
        f"files={scope['included_source_count']} clauses={scope['source_clause_count']} "
        f"semantic_records={registry['semantic_record_count']} unmapped=0 "
        f"registry_sha256={sha(registry_bytes)}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("generate",))
    parser.add_argument("--provenance-dir", type=Path, default=DEFAULT_PROV)
    args = parser.parse_args()
    try:
        return generate(args.provenance_dir.resolve())
    except (OSError, ValueError, KeyError, UnicodeError, json.JSONDecodeError, subprocess.CalledProcessError, SyntaxError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
