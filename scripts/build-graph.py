#!/usr/bin/env python3
"""build-graph.py — Build knowledge graph from docs/knowledge/ frontmatter.

Reads all .md files in docs/knowledge/**, parses YAML frontmatter,
and produces docs/graph/index.json.

Usage:
    python scripts/build-graph.py              # repo root
    python scripts/build-graph.py --check      # validate only, no output
    python scripts/build-graph.py --stats      # print stats only
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Constants ──────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = REPO_ROOT / "docs" / "knowledge"
GRAPH_DIR = REPO_ROOT / "docs" / "graph"
GRAPH_FILE = GRAPH_DIR / "index.json"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


# ── YAML frontmatter parsing (minimal, no dependencies) ────────

def parse_frontmatter(text: str) -> dict | None:
    """Extract YAML frontmatter from markdown text. Returns dict or None."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None

    raw = m.group(1)
    result = {}
    for line in raw.strip().split("\n"):
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        # Handle simple key: value and key: [list] and key: "string"
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()

            # Quoted string
            if val.startswith('"') and val.endswith('"'):
                result[key] = val[1:-1]
            # Inline list [a, b, c]
            elif val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                result[key] = [x.strip().strip('"').strip("'") for x in inner.split(",")] if inner else []
            # Nested list (next lines are "- item") — handled by indentation state
            elif val == "":
                result[key] = []
            # Scalar
            else:
                result[key] = val
        # List item continuation
        elif line.strip().startswith("- ") and isinstance(result.get(list(result.keys())[-1] if result.keys() else None), list):
            last_key = list(result.keys())[-1]
            item = line.strip()[2:].strip().strip('"').strip("'")
            result[last_key].append(item)

    return result


# ── Build ──────────────────────────────────────────────────────

def build_graph() -> dict:
    """Scan knowledge/ files and build graph."""
    nodes = []
    edges = []
    node_ids = set()
    warnings = []

    for md_file in sorted(KNOWLEDGE_DIR.rglob("*.md")):
        rel_path = md_file.relative_to(REPO_ROOT / "docs")
        text = md_file.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)

        if not fm or "id" not in fm or "object_type" not in fm:
            if md_file.name != ".gitkeep":
                warnings.append(f"⚠️  Skipped (no valid frontmatter): {rel_path}")
            continue

        obj_id = str(fm.get("id", ""))
        if not obj_id:
            continue

        if obj_id in node_ids:
            warnings.append(f"❌ Duplicate ID: {obj_id} in {rel_path}")
            continue

        node_ids.add(obj_id)

        node = {
            "id": obj_id,
            "type": str(fm.get("object_type", "unknown")),
            "status": str(fm.get("status", "unknown")),
            "confidence": str(fm.get("confidence", "draft")),
            "summary": str(fm.get("summary", "")),
            "owner": str(fm.get("owner", "")),
            "file": str(rel_path),
            "depends": fm.get("depends") if isinstance(fm.get("depends"), list) else [],
            "verified_commit": str(fm.get("verified_commit", "")),
            "updated_at": str(fm.get("updated_at", "")),
        }
        nodes.append(node)

        # ── Edges ──────────────────────────────────────────
        # depends → DEPENDS_ON
        for dep in node["depends"]:
            edges.append({"from": obj_id, "to": dep, "type": "DEPENDS_ON"})

        # parent → PARENT_OF
        parent = fm.get("parent")
        if parent and isinstance(parent, str):
            edges.append({"from": parent, "to": obj_id, "type": "PARENT_OF"})

        # children → PARENT_OF (reverse)
        children = fm.get("children")
        if isinstance(children, list):
            for child in children:
                edges.append({"from": obj_id, "to": child, "type": "PARENT_OF"})

        # supersedes → SUPERSEDES
        supersedes = fm.get("supersedes")
        if supersedes and isinstance(supersedes, str):
            edges.append({"from": obj_id, "to": supersedes, "type": "SUPERSEDES"})

        # Module.features → CONTAINS
        if node["type"] == "module" and isinstance(fm.get("features"), list):
            for feat in fm["features"]:
                edges.append({"from": obj_id, "to": feat, "type": "CONTAINS"})

    # ── Integrity checks ──────────────────────────────────
    for edge in edges:
        if edge["to"] not in node_ids:
            warnings.append(f"⚠️  Missing target: {edge['from']} → {edge['to']} ({edge['type']})")

    # ── Stats ─────────────────────────────────────────────
    by_type = {}
    for n in nodes:
        t = n["type"]
        by_type[t] = by_type.get(t, 0) + 1

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_by": "build-graph.py",
        "source": "docs/knowledge/",
        "stats": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "by_type": by_type,
        },
        "nodes": nodes,
        "edges": edges,
        "warnings": warnings,
    }


# ── CLI ────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Build knowledge graph from docs/knowledge/")
    parser.add_argument("--check", action="store_true", help="Validate only, don't write output")
    parser.add_argument("--stats", action="store_true", help="Print stats only")
    args = parser.parse_args()

    graph = build_graph()

    if args.stats:
        print(json.dumps(graph["stats"], indent=2))
        return

    if args.check:
        if graph["warnings"]:
            for w in graph["warnings"]:
                print(w)
            sys.exit(1)
        print("✅ Graph integrity check passed.")
        return

    # Write
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    GRAPH_FILE.write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"✅ Graph built: {graph['stats']['total_nodes']} nodes, {graph['stats']['total_edges']} edges")
    if graph["warnings"]:
        for w in graph["warnings"]:
            print(w)


if __name__ == "__main__":
    main()
