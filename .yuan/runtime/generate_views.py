#!/usr/bin/env python3
"""
YuanCore View Generator — Phase 6

Generates human-readable views (TASK_BOARD, PROGRESS, SESSION) FROM
the authoritative STATE + Attempts + Evidence. Views are read-only
derivations; they never modify Core state.

Usage:
    python3 generate_views.py [--work-dir /path/to/work]
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional

# Add scripts path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "validation"))
from core_validator import read_state, write_state

BASE_DIR = os.environ.get("YUANFORGE_BASE_DIR", "/home/admin/yuanforge")
WORK_DIR = os.path.join(BASE_DIR, "work")
STATE_PATH = os.path.join(WORK_DIR, "STATE.md")
ATTEMPT_DIR = os.path.join(WORK_DIR, "attempts")
EVIDENCE_DIR = os.path.join(WORK_DIR, "evidence")
JOURNAL_DIR = os.path.join(WORK_DIR, "journal")
VIEWS_DIR = os.path.join(WORK_DIR, "views")


def load_yaml(path: str) -> dict:
    """Load a YAML file, return empty dict on failure."""
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def load_attempts() -> List[Dict]:
    """Load all attempt files."""
    attempts = []
    if not os.path.exists(ATTEMPT_DIR):
        return attempts
    for fname in sorted(os.listdir(ATTEMPT_DIR)):
        if not fname.endswith((".md", ".yaml", ".yml")):
            continue
        data = load_yaml(os.path.join(ATTEMPT_DIR, fname))
        if data:
            data["_file"] = fname
            attempts.append(data)
    return attempts


def load_evidence() -> List[Dict]:
    """Load all evidence files."""
    evidence = []
    if not os.path.exists(EVIDENCE_DIR):
        return evidence
    for fname in sorted(os.listdir(EVIDENCE_DIR)):
        if not fname.endswith((".md", ".yaml", ".yml")):
            continue
        data = load_yaml(os.path.join(EVIDENCE_DIR, fname))
        if data:
            data["_file"] = fname
            evidence.append(data)
    return evidence


def load_journals() -> List[Dict]:
    """Load all journal entries."""
    journals = []
    if not os.path.exists(JOURNAL_DIR):
        return journals
    for fname in sorted(os.listdir(JOURNAL_DIR)):
        if not fname.endswith((".md", ".yaml", ".yml")):
            continue
        data = load_yaml(os.path.join(JOURNAL_DIR, fname))
        if data:
            data["_file"] = fname
            journals.append(data)
    return journals


def generate_task_board(state: Dict, attempts: List[Dict], evidence: List[Dict]) -> str:
    """Generate TASK_BOARD.md view from Core data."""
    lines = [
        "# Task Board (Generated View)",
        "",
        f"> Auto-generated from STATE + Attempts + Evidence on {datetime.utcnow().isoformat()}",
        f"> Schema: yuan.view.taskboard/v1",
        "",
        "## Current State",
        "",
        f"- **Status:** {state.get('status', 'UNKNOWN')}",
        f"- **Revision:** {state.get('current_revision', 0)}",
        f"- **Artifact Hash:** `{state.get('current_artifact_hash', '')[:16]}...`",
        f"- **Current Attempt:** {state.get('attempt_id', 'none')}",
        "",
        "---",
        "",
        "## Attempts",
        "",
    ]

    if not attempts:
        lines.append("*No attempts recorded.*")
    else:
        for a in attempts:
            aid = a.get("attempt_id", a.get("_file", "?"))
            status = a.get("status", {})
            phase = status.get("phase", "unknown") if isinstance(status, dict) else str(status)
            result = status.get("result", "pending") if isinstance(status, dict) else "pending"
            src = a.get("source_proposal", "?")
            lines.append(f"### {aid}")
            lines.append(f"- **Phase:** {phase}")
            lines.append(f"- **Result:** {result}")
            lines.append(f"- **Source Proposal:** {src}")
            lines.append("")

    lines.extend([
        "---",
        "",
        "## Evidence Summary",
        "",
    ])

    valid_count = sum(1 for e in evidence if e.get("result") == "pass" and e.get("status") == "valid")
    fail_count = sum(1 for e in evidence if e.get("result") == "fail")
    lines.append(f"- **Total:** {len(evidence)}")
    lines.append(f"- **Pass:** {valid_count}")
    lines.append(f"- **Fail:** {fail_count}")
    lines.append("")

    if evidence:
        lines.extend(["### Evidence List", ""])
        for e in evidence:
            eid = e.get("evidence_id", e.get("_file", "?"))
            result = e.get("result", "unknown")
            claim = e.get("claim", "")[:60]
            lines.append(f"- `{eid}`: {result} — {claim}")
        lines.append("")

    lines.extend([
        "---",
        "",
        "> This view is generated from Core state. Do not edit directly.",
    ])
    return "\n".join(lines)


def generate_progress(state: Dict, attempts: List[Dict], evidence: List[Dict]) -> str:
    """Generate PROGRESS.md view from Core data."""
    lines = [
        "# Progress Report (Generated View)",
        "",
        f"> Auto-generated from STATE + Attempts + Evidence on {datetime.utcnow().isoformat()}",
        f"> Schema: yuan.view.progress/v1",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| **Status** | {state.get('status', 'UNKNOWN')} |",
        f"| **Revision** | {state.get('current_revision', 0)} |",
        f"| **Attempts** | {len(attempts)} |",
        f"| **Evidence** | {len(evidence)} |",
        f"| **Valid Evidence** | {sum(1 for e in evidence if e.get('result') == 'pass')} |",
        f"| **Failed Evidence** | {sum(1 for e in evidence if e.get('result') == 'fail')} |",
        "",
    ]

    if attempts:
        lines.extend([
            "---",
            "",
            "## Attempt Timeline",
            "",
        ])
        for a in attempts:
            aid = a.get("attempt_id", a.get("_file", "?"))
            status = a.get("status", {})
            phase = status.get("phase", "?") if isinstance(status, dict) else "?"
            result = status.get("result", "pending") if isinstance(status, dict) else "pending"
            lines.append(f"- [{phase}] {aid} → {result}")
        lines.append("")

    lines.extend([
        "---",
        "",
        "> This view is generated from Core state. Do not edit directly.",
    ])
    return "\n".join(lines)


def generate_session(state: Dict, attempts: List[Dict], journals: List[Dict]) -> str:
    """Generate SESSION.md view from Core data."""
    lines = [
        "# Session Log (Generated View)",
        "",
        f"> Auto-generated from STATE + Attempts + Journals on {datetime.utcnow().isoformat()}",
        f"> Schema: yuan.view.session/v1",
        "",
        "## Current Session",
        "",
        f"- **Status:** {state.get('status', 'UNKNOWN')}",
        f"- **Revision:** {state.get('current_revision', 0)}",
        f"- **Active Attempt:** {state.get('attempt_id', 'none')}",
        "",
    ]

    if journals:
        lines.extend([
            "---",
            "",
            "## Journal Entries",
            "",
        ])
        for j in journals[-20:]:  # Last 20 entries
            jid = j.get("journal_id", j.get("_file", "?"))
            entry_type = j.get("entry_type", "unknown")
            content = str(j.get("content", ""))[:100]
            lines.append(f"- [{entry_type}] {jid}: {content}")
        lines.append("")

    lines.extend([
        "---",
        "",
        "> This view is generated from Core state. Do not edit directly.",
    ])
    return "\n".join(lines)


def generate_all_views() -> Dict[str, str]:
    """Generate all views and return {filename: content}."""
    state = read_state(STATE_PATH)
    attempts = load_attempts()
    evidence = load_evidence()
    journals = load_journals()

    return {
        "TASK_BOARD.md": generate_task_board(state, attempts, evidence),
        "PROGRESS.md": generate_progress(state, attempts, evidence),
        "SESSION.md": generate_session(state, attempts, journals),
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="YuanCore View Generator")
    parser.add_argument("--work-dir", type=str, default=WORK_DIR, help="Work directory")
    parser.add_argument("--output", type=str, default=None, help="Output directory (default: work/views/)")
    parser.add_argument("--dry-run", action="store_true", help="Print views without writing")
    args = parser.parse_args()

    work_dir = args.work_dir
    state_path = os.path.join(work_dir, "STATE.md")
    views_dir = args.output or os.path.join(work_dir, "views")

    # Override module-level globals for this run
    import __main__ as main_module
    main_module.WORK_DIR = work_dir
    main_module.STATE_PATH = state_path
    main_module.VIEWS_DIR = views_dir

    os.makedirs(views_dir, exist_ok=True)

    views = generate_all_views()
    written = 0
    for name, content in views.items():
        path = os.path.join(views_dir, name)
        if args.dry_run:
            print(f"=== {name} ===")
            print(content)
            print()
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            written += 1
            print(f"  Generated: {path}")

    print(f"\nGenerated {written} views to {views_dir}")
    return written


if __name__ == "__main__":
    main()
