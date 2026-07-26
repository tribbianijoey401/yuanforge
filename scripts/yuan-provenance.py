#!/usr/bin/env python3
"""Generate and verify deterministic clause-level YuanForge provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / ".yuan" / "extensions" / "provenance"
POLICY_PATH = BASE / "scope-policy.json"
SCOPE_PATH = BASE / "scope-manifest.json"
CLAUSE_PATH = BASE / "clause-manifest.json"
REPORT_PATH = BASE / "REPORT.md"
FIXTURE_PATH = ROOT / ".yuan" / "extensions" / "fixtures" / "legacy-anti-patterns.json"

HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
FENCE_RE = re.compile(r"^[ \t]*(```+|~~~+)")
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_policy() -> dict[str, Any]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def ignored(path: Path, policy: dict[str, Any]) -> bool:
    relative = path.relative_to(ROOT)
    if any(part in policy["ignore_segments"] for part in relative.parts):
        return True
    return any(path.name.endswith(suffix) for suffix in policy["ignore_suffixes"])


def discover(policy: dict[str, Any]) -> list[Path]:
    found: set[Path] = set()
    for name in policy["include_files"]:
        path = ROOT / name
        if not path.is_file():
            raise ValueError(f"required source missing: {name}")
        found.add(path)
    for name in policy["include_roots"]:
        root = ROOT / name
        if not root.is_dir():
            raise ValueError(f"required source root missing: {name}")
        for path in root.rglob("*"):
            if path.is_file() and not ignored(path, policy):
                found.add(path)
    paths = sorted(found, key=lambda item: rel(item))
    names = [rel(path) for path in paths]
    for family in policy["required_families"]:
        if family.endswith("/"):
            if not any(name.startswith(family) for name in names):
                raise ValueError(f"required family empty: {family}")
        elif family not in names:
            raise ValueError(f"required family file missing: {family}")
    return paths


def markdown_clauses(data: bytes) -> list[dict[str, Any]]:
    text = data.decode("utf-8")
    lines = text.splitlines(keepends=True)
    starts: list[tuple[int, int, str]] = []
    in_fence = False
    fence_char = ""
    offset = 0
    for number, line in enumerate(lines, start=1):
        plain = line.rstrip("\r\n")
        fence = FENCE_RE.match(plain)
        if fence:
            marker = fence.group(1)
            if not in_fence:
                in_fence = True
                fence_char = marker[0]
            elif marker[0] == fence_char:
                in_fence = False
                fence_char = ""
        elif not in_fence:
            heading = HEADING_RE.match(plain)
            if heading:
                starts.append((offset, number, heading.group(2).strip()))
        offset += len(line.encode("utf-8"))

    if not starts:
        return [{
            "anchor": "@file",
            "heading": None,
            "line_start": 1,
            "line_end": max(1, len(lines)),
            "byte_start": 0,
            "byte_end": len(data),
            "clause_sha256": digest(data),
        }]

    boundaries: list[tuple[int, int, str | None, str]] = []
    first_offset, first_line, _ = starts[0]
    if first_offset:
        boundaries.append((0, first_line, None, "@preamble"))
    for index, (byte_start, line_start, heading) in enumerate(starts):
        anchor = f"h{index + 1:04d}"
        boundaries.append((byte_start, line_start, heading, anchor))

    clauses: list[dict[str, Any]] = []
    for index, (byte_start, line_start, heading, anchor) in enumerate(boundaries):
        byte_end = boundaries[index + 1][0] if index + 1 < len(boundaries) else len(data)
        if index + 1 < len(boundaries):
            line_end = boundaries[index + 1][1] - 1
        else:
            line_end = max(line_start, len(lines))
        clauses.append({
            "anchor": anchor,
            "heading": heading,
            "line_start": line_start,
            "line_end": line_end,
            "byte_start": byte_start,
            "byte_end": byte_end,
            "clause_sha256": digest(data[byte_start:byte_end]),
        })
    return clauses


def clauses_for(path: Path, data: bytes) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".md":
        return markdown_clauses(data)
    return [{
        "anchor": "@file",
        "heading": None,
        "line_start": 1,
        "line_end": data.count(b"\n") + 1,
        "byte_start": 0,
        "byte_end": len(data),
        "clause_sha256": digest(data),
    }]


def mapping(path: str, heading: str | None, source_hash: str) -> dict[str, Any]:
    probe = f"{path} {heading or ''}".lower()
    extension = "software-delivery"
    rule = "legacy-default-software-delivery"

    if path.startswith(".yuan/core/0.1/"):
        return {
            "disposition": "core",
            "target": ".yuan/core/0.1/protocol.md",
            "mapping_rule": "core-candidate",
            "rationale": "M3-approved Core candidate implementation, schema, fixture, or conformance clause.",
        }
    if path == "scripts/run-ptg-cal-check.py":
        return {
            "disposition": "obsolete-with-proof",
            "target": ".yuan/extensions/testing.md",
            "mapping_rule": "obsolete-simulated-ptg-runner",
            "rationale": "Genesis Design §8 excludes this simulated/zero-selection-capable runner from the trust root.",
            "obsolete": {
                "source_sha256": source_hash,
                "reason": "It simulates assertion names and can accept an empty effective test selection, so it cannot prove typed ACs.",
                "replacement": ".yuan/core/0.1/conformance.py",
                "fixture": ".yuan/extensions/fixtures/legacy-anti-patterns.json#legacy-zero-check-pass",
            },
        }
    if path.startswith("scripts/bootstrap") or path in {
        "scripts/bootstrap-core-verifier.py",
        "scripts/bootstrap_verifier.py",
        "scripts/bootstrap_verifier_support.py",
    }:
        return {
            "disposition": "fixture",
            "target": "tests/bootstrap_verifier/",
            "mapping_rule": "genesis-verifier-fixture",
            "rationale": "Frozen old-trust-root validation material retained as an independent verification fixture.",
        }
    if path in {"docs/anti-patterns.md", "templates/anti-patterns.md"}:
        return {
            "disposition": "fixture",
            "target": ".yuan/extensions/fixtures/legacy-anti-patterns.json",
            "mapping_rule": "legacy-anti-pattern-catalog",
            "rationale": "Negative scenario retained as verifier input; it does not define Core runtime semantics.",
        }
    if path.startswith("references/") or path.startswith("docs/knowledge/"):
        return {
            "disposition": "knowledge",
            "target": path,
            "mapping_rule": "existing-knowledge-source",
            "rationale": "Advisory knowledge remains at its content-addressed source and is not runtime authority.",
        }

    ui_tokens = ("ui", "ux", "visual", "design-system", "视觉", "界面", "无障碍", "颜色", "字体", "交互")
    test_tokens = (
        "tester", "test-integrity", "ptg", "cal", "seam", "verdict", "code-review",
        "debug", "test-driven", "测试", "验证", "审查", "证据", "tdd", "验收",
    )
    docs_tokens = (
        ".yuan/docs/", "docs-framework", "doc-engineer", "project-memory",
        "project-audit", "文档", "memory", "docsos", "归档",
    )
    knowledge_tokens = (
        "distill", "graph-query", "knowledge-injection", "promotion",
        "self-improving-memory", "知识", "promotion",
    )
    platform_tokens = (
        ".yuan/platforms/", ".yuan/adapters/", "adapter-protocol",
        "dispatch-routing", "role-switch", "subagent", "platform", "adapter",
        "平台", "tier", "适配",
    )

    if any(token in probe for token in ui_tokens):
        extension, rule = "ui", "ui-advice-or-verifier"
    elif any(token in probe for token in test_tokens):
        extension, rule = "testing", "testing-advice-or-verifier"
    elif any(token in probe for token in knowledge_tokens):
        extension, rule = "knowledge", "knowledge-advice"
    elif any(token in probe for token in docs_tokens):
        extension, rule = "docsos", "docs-memory-advice-or-verifier"
    elif path == "bin/yuanforge-init" or any(token in probe for token in platform_tokens):
        extension, rule = "platform-adapters", "platform-capability-advice"
    elif path == ".yuan/VERSION" or "version" in probe:
        extension, rule = "platform-adapters", "version-authority-advice"

    return {
        "disposition": "extension",
        "target": f".yuan/extensions/{extension}.md",
        "mapping_rule": rule,
        "rationale": "Optional authoring advice or verifier recipe; Core results, completion, and authority remain unchanged.",
    }


def build() -> tuple[dict[str, Any], dict[str, Any], str]:
    policy = load_policy()
    paths = discover(policy)
    files: list[dict[str, Any]] = []
    clauses: list[dict[str, Any]] = []

    for path in paths:
        name = rel(path)
        data = path.read_bytes()
        source_hash = digest(data)
        source_clauses = clauses_for(path, data)
        if not source_clauses or source_clauses[0]["byte_start"] != 0:
            raise ValueError(f"clause coverage does not start at byte zero: {name}")
        if source_clauses[-1]["byte_end"] != len(data):
            raise ValueError(f"clause coverage does not end at EOF: {name}")
        for left, right in zip(source_clauses, source_clauses[1:]):
            if left["byte_end"] != right["byte_start"]:
                raise ValueError(f"clause byte gap/overlap: {name}")

        files.append({
            "path": name,
            "sha256": source_hash,
            "bytes": len(data),
            "clause_count": len(source_clauses),
        })
        for part in source_clauses:
            record = {
                "clause_id": digest(f"{name}:{part['anchor']}:{part['clause_sha256']}".encode("utf-8"))[:24],
                "source": name,
                "source_sha256": source_hash,
                **part,
                **mapping(name, part["heading"], source_hash),
            }
            clauses.append(record)

    policy_hash = digest(POLICY_PATH.read_bytes())
    scope = {
        "schema_version": "yuan.provenance-scope/v1",
        "policy_sha256": policy_hash,
        "source_file_count": len(files),
        "source_byte_count": sum(item["bytes"] for item in files),
        "source_clause_count": len(clauses),
        "files": files,
        "excluded_inventory": policy["excluded_inventory"],
    }
    clause_manifest = {
        "schema_version": "yuan.clause-provenance/v1",
        "scope_sha256": digest(canonical_json(scope)),
        "allowed_dispositions": ["core", "extension", "knowledge", "fixture", "obsolete-with-proof"],
        "mapped_clause_count": len(clauses),
        "unmapped_clause_count": 0,
        "clauses": clauses,
    }
    report = render_report(scope, clause_manifest)
    return scope, clause_manifest, report


def render_report(scope: dict[str, Any], manifest: dict[str, Any]) -> str:
    dispositions = Counter(item["disposition"] for item in manifest["clauses"])
    targets = Counter(
        item["target"] for item in manifest["clauses"] if item["disposition"] == "extension"
    )
    lines = [
        "# M7 Clause Provenance Report",
        "",
        "> Deterministically generated by `python -B scripts/yuan-provenance.py generate`.",
        "",
        "## Coverage",
        "",
        f"- source files: {scope['source_file_count']}",
        f"- source bytes: {scope['source_byte_count']}",
        f"- source clauses: {scope['source_clause_count']}",
        f"- mapped clauses: {manifest['mapped_clause_count']}",
        f"- unmapped clauses: {manifest['unmapped_clause_count']}",
        f"- coverage: {'100.00%' if not manifest['unmapped_clause_count'] else 'FAIL'}",
        "",
        "## Dispositions",
        "",
        "| Disposition | Clauses |",
        "|-------------|--------:|",
    ]
    for name in manifest["allowed_dispositions"]:
        lines.append(f"| `{name}` | {dispositions[name]} |")
    lines.extend([
        "",
        "## Extension targets",
        "",
        "| Target | Clauses |",
        "|--------|--------:|",
    ])
    for name, count in sorted(targets.items()):
        lines.append(f"| `{name}` | {count} |")
    lines.extend([
        "",
        "## Invariants",
        "",
        "- Every in-scope source byte is covered by one contiguous clause partition.",
        "- Every clause has exactly one allowed disposition and content hash.",
        "- Every obsolete clause carries its source hash, reason, and replacement or fixture.",
        "- Legacy source files remain in place; this report does not authorize tombstoning.",
        "- Runtime/evidence exclusions are enumerated in the scope manifest.",
        "",
    ])
    return "\n".join(lines)


def validate_fixture_bindings() -> None:
    catalog = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    ids: set[str] = set()
    for case in catalog["cases"]:
        if case["id"] in ids:
            raise ValueError(f"duplicate fixture id: {case['id']}")
        ids.add(case["id"])
        source = ROOT / case["source"]
        if not source.is_file():
            raise ValueError(f"fixture source missing: {case['source']}")
        actual = digest(source.read_bytes())
        if actual != case["source_sha256"]:
            raise ValueError(f"fixture source hash drift: {case['id']}")


def validate_links() -> None:
    for path in (ROOT / ".yuan" / "extensions").rglob("*.md"):
        for target in LINK_RE.findall(path.read_text(encoding="utf-8")):
            clean = target.split("#", 1)[0]
            if not clean or "://" in clean or clean.startswith("mailto:"):
                continue
            resolved = (path.parent / clean).resolve()
            if not resolved.exists():
                raise ValueError(f"broken extension link: {rel(path)} -> {target}")


def validate_manifest(scope: dict[str, Any], manifest: dict[str, Any]) -> None:
    allowed = set(manifest["allowed_dispositions"])
    if manifest["unmapped_clause_count"] != 0:
        raise ValueError("unmapped clauses are forbidden")
    if manifest["mapped_clause_count"] != scope["source_clause_count"]:
        raise ValueError("mapped/source clause count mismatch")
    seen: set[str] = set()
    for item in manifest["clauses"]:
        if item["clause_id"] in seen:
            raise ValueError(f"duplicate clause id: {item['clause_id']}")
        seen.add(item["clause_id"])
        if item["disposition"] not in allowed:
            raise ValueError(f"invalid disposition: {item['clause_id']}")
        if not item.get("target") or not item.get("rationale"):
            raise ValueError(f"incomplete mapping: {item['clause_id']}")
        if item["disposition"] == "obsolete-with-proof":
            proof = item.get("obsolete") or {}
            if proof.get("source_sha256") != item["source_sha256"]:
                raise ValueError(f"obsolete source hash mismatch: {item['clause_id']}")
            if not proof.get("reason") or not (proof.get("replacement") or proof.get("fixture")):
                raise ValueError(f"incomplete obsolete proof: {item['clause_id']}")


def generate() -> int:
    scope, manifest, report = build()
    validate_manifest(scope, manifest)
    validate_fixture_bindings()
    SCOPE_PATH.write_bytes(canonical_json(scope))
    CLAUSE_PATH.write_bytes(canonical_json(manifest))
    REPORT_PATH.write_text(report, encoding="utf-8", newline="\n")
    validate_links()
    print(
        f"PASS generated files={scope['source_file_count']} "
        f"clauses={scope['source_clause_count']} unmapped=0"
    )
    return 0


def verify() -> int:
    expected_scope, expected_manifest, expected_report = build()
    validate_manifest(expected_scope, expected_manifest)
    validate_fixture_bindings()
    validate_links()
    expected = {
        SCOPE_PATH: canonical_json(expected_scope),
        CLAUSE_PATH: canonical_json(expected_manifest),
        REPORT_PATH: expected_report.encode("utf-8"),
    }
    for path, content in expected.items():
        if not path.is_file():
            raise ValueError(f"generated artifact missing: {rel(path)}")
        if path.read_bytes() != content:
            raise ValueError(f"generated artifact stale: {rel(path)}")
    print(
        f"PASS coverage=100.00% files={expected_scope['source_file_count']} "
        f"clauses={expected_scope['source_clause_count']} links=PASS hashes=PASS"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("generate", "verify"))
    args = parser.parse_args()
    try:
        return generate() if args.command == "generate" else verify()
    except (OSError, UnicodeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
