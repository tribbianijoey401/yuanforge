#!/usr/bin/env python3
"""
YuanCore Shadow Runtime — Phase 5

Runs the Core validator in shadow mode alongside the legacy system.
Reads proposals from work/, validates them through Core + Role Extension,
computes reducer decisions, and logs observations WITHOUT modifying STATE.

Dual-track invariant:
  - Legacy continues controlling execution
  - Shadow only observes and reduces
  - Mismatches are logged, never enforced
"""

import os
import sys
import json
import hashlib
import time
import glob
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add scripts path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "validation"))

from core_validator import (
    CoreSchemaValidator,
    RoleExtensionValidator,
    select_proposal,
    run_reducer,
    is_evidence_stale,
    compute_artifact_hash,
    read_state,
)

# ── paths ────────────────────────────────────────────────────────────────────
BASE_DIR = os.environ.get("YUANFORGE_BASE_DIR", "/home/admin/yuanforge")
WORK_DIR = os.path.join(BASE_DIR, "work")
STATE_PATH = os.path.join(WORK_DIR, "STATE.md")
EVIDENCE_DIR = os.path.join(WORK_DIR, "evidence")
ATTEMPT_DIR = os.path.join(WORK_DIR, "attempts")
JOURNAL_DIR = os.path.join(WORK_DIR, "journal")
SHADOW_LOG_DIR = os.path.join(BASE_DIR, ".yuan", "runtime", "shadow", "logs")
PROPOSAL_SCAN_DIRS = [
    os.path.join(WORK_DIR, "proposals"),
    os.path.join(WORK_DIR, "outbox"),
]

os.makedirs(SHADOW_LOG_DIR, exist_ok=True)
os.makedirs(EVIDENCE_DIR, exist_ok=True)
os.makedirs(ATTEMPT_DIR, exist_ok=True)
os.makedirs(JOURNAL_DIR, exist_ok=True)


# ── data classes ─────────────────────────────────────────────────────────────
class ShadowTick:
    """One observation tick of the shadow runtime."""

    def __init__(self, tick_id: int):
        self.tick_id = tick_id
        self.timestamp = datetime.utcnow().isoformat()
        self.state_snapshot: Dict[str, Any] = {}
        self.proposals: List[Dict] = []
        self.evidence_items: List[Dict] = []
        self.reducer_result: Optional[Dict] = None
        self.mismatches: List[Dict] = []
        self.duplicate_fingerprints: List[str] = []
        self.observation_id = f"O-{tick_id:06d}"

    def to_dict(self) -> Dict:
        return {
            "observation_id": self.observation_id,
            "tick": self.tick_id,
            "timestamp": self.timestamp,
            "state_snapshot": self.state_snapshot,
            "proposal_scan": {
                "total": len(self.proposals),
                "valid": sum(1 for p in self.proposals if p.get("valid")),
                "rejected": sum(1 for p in self.proposals if not p.get("valid")),
                "selected": self.proposals[0].get("proposal_id") if self.proposals and self.proposals[0].get("valid") else None,
            },
            "evidence_summary": {
                "total": len(self.evidence_items),
                "stale": sum(1 for e in self.evidence_items if e.get("stale")),
                "valid": sum(1 for e in self.evidence_items if e.get("valid")),
                "invalid": sum(1 for e in self.evidence_items if e.get("invalid")),
            },
            "reducer_prediction": self.reducer_result,
            "mismatches": self.mismatches,
            "duplicate_fingerprints": self.duplicate_fingerprints,
        }


# ── shadow observer ──────────────────────────────────────────────────────────
class ShadowRuntime:
    """Observes legacy system, runs Core validation in parallel."""

    def __init__(self):
        self.tick_count = 0
        self.mismatch_log: List[Dict] = []

    def load_state(self) -> Dict:
        """Read current STATE.md (read-only, never writes)."""
        try:
            state = read_state(STATE_PATH)
            return {
                "current_revision": state.get("current_revision", 0),
                "current_artifact_hash": state.get("current_artifact_hash", ""),
                "status": state.get("status", "UNKNOWN"),
                "attempt_id": state.get("attempt_id"),
                "pending_changes": len(state.get("pending_changes", [])),
            }
        except Exception as e:
            return {"error": str(e), "status": "STATE_UNREADABLE"}

    def scan_proposals(self) -> List[Dict]:
        """Find and validate all proposals in known directories."""
        proposals = []
        for scan_dir in PROPOSAL_SCAN_DIRS:
            if not os.path.exists(scan_dir):
                continue
            for fname in sorted(os.listdir(scan_dir)):
                if not fname.endswith(".md") and not fname.endswith(".yaml") and not fname.endswith(".yml"):
                    continue
                fpath = os.path.join(scan_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        import yaml
                        data = yaml.safe_load(f) or {}
                except Exception:
                    proposals.append({
                        "file": fname, "path": fpath,
                        "valid": False, "error": "parse_failed",
                    })
                    continue

                # Core validation
                try:
                    cv = CoreSchemaValidator(proposal_data=data)
                    core_errors = cv.validate()
                    core_ok = len(core_errors) == 0
                except Exception as e:
                    core_errors = [type("E", (), {"message": str(e), "field": "exception"})()]
                    core_ok = False

                # Role extension validation
                role = data.get("producer", {}).get("role", "unknown")
                role_errors = []
                role_ok = False
                if core_ok:
                    try:
                        rv = RoleExtensionValidator(proposal_data=data, role=role)
                        role_errors = rv.validate()
                        role_ok = len(role_errors) == 0
                    except Exception as e:
                        role_errors = [type("E", (), {"message": str(e), "field": "exception"})()]
                        role_ok = False

                valid = core_ok and role_ok
                fingerprint = None
                if core_ok:
                    try:
                        fingerprint = cv.compute_strategy_fingerprint()
                    except Exception:
                        pass

                proposals.append({
                    "file": fname,
                    "path": fpath,
                    "valid": valid,
                    "core_ok": core_ok,
                    "role_ok": role_ok,
                    "proposal_id": data.get("proposal_id"),
                    "selection_rank": data.get("selection_rank"),
                    "fingerprint": fingerprint,
                    "core_errors": [e.message for e in core_errors],
                    "role_errors": [e.message for e in role_errors],
                    "work_revision": data.get("work", {}).get("revision"),
                })

        return proposals

    def scan_evidence(self, work_revision: int) -> List[Dict]:
        """Scan evidence files and check staleness."""
        items = []
        if not os.path.exists(EVIDENCE_DIR):
            return items
        for fname in sorted(os.listdir(EVIDENCE_DIR)):
            if not fname.endswith(".md") and not fname.endswith(".yaml"):
                continue
            fpath = os.path.join(EVIDENCE_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    import yaml
                    data = yaml.safe_load(f) or {}
            except Exception:
                items.append({"file": fname, "valid": False, "error": "parse_failed"})
                continue

            bound_rev = data.get("bound_work_revision")
            stale = bound_rev is not None and bound_rev != work_revision
            items.append({
                "file": fname,
                "evidence_id": data.get("evidence_id"),
                "result": data.get("result"),
                "status": data.get("status"),
                "bound_work_revision": bound_rev,
                "current_work_revision": work_revision,
                "stale": stale,
                "valid": not stale and data.get("result") == "pass",
                "invalid": stale or (data.get("result") == "fail"),
            })
        return items

    def compute_reducer_decision(
        self,
        state: Dict,
        proposals: List[Dict],
        evidence: List[Dict],
    ) -> Dict:
        """Run the deterministic reducer on current evidence."""
        # Build evidence list for reducer
        evidence_list = []
        for ev in evidence:
            if not ev.get("stale") and ev.get("result"):
                evidence_list.append({
                    "evidence_id": ev.get("evidence_id"),
                    "result": ev.get("result"),
                    "status": ev.get("status", "valid"),
                    "bound_work_revision": ev.get("bound_work_revision"),
                })

        # Build invariants from state (simplified — real invariants from INVARIANTS.md)
        invariants = {}
        status = state.get("status", "UNKNOWN")
        if status == "BLOCKED":
            invariants["I-STATE-BLOCKED"] = "FAIL"

        # Budget: assume infinite for shadow (no real budget tracking yet)
        budget_remaining = 9999
        budget_max = 10000

        reducer = run_reducer(state, evidence_list, invariants, budget_remaining, budget_max)
        return {
            "result": reducer.result,
            "details": reducer.details,
        }

    def detect_duplicates(self, proposals: List[Dict]) -> List[str]:
        """Find proposals with identical strategy fingerprints."""
        fp_map: Dict[str, List[str]] = {}
        for p in proposals:
            fp = p.get("fingerprint")
            if fp:
                fp_map.setdefault(fp, []).append(p.get("proposal_id", "?"))
        return [fp for fp, ids in fp_map.items() if len(ids) > 1]

    def run_tick(self, tick_id: int) -> ShadowTick:
        """Execute one shadow observation tick."""
        tick = ShadowTick(tick_id)

        # 1. Read state (read-only)
        tick.state_snapshot = self.load_state()
        work_rev = tick.state_snapshot.get("current_revision", 0)

        # 2. Scan proposals
        tick.proposals = self.scan_proposals()

        # 3. Scan evidence
        tick.evidence_items = self.scan_evidence(work_rev)

        # 4. Detect duplicate fingerprints
        tick.duplicate_fingerprints = self.detect_duplicates(tick.proposals)

        # 5. Compute reducer decision
        tick.reducer_result = self.compute_reducer_decision(
            tick.state_snapshot, tick.proposals, tick.evidence_items
        )

        # 6. Log mismatches
        if tick.reducer_result["result"] == "COMPLETE":
            # Check: are there really enough evidence?
            valid_evidence = [e for e in tick.evidence_items if e.get("valid")]
            if len(valid_evidence) < 1:
                tick.mismatches.append({
                    "type": "false_complete",
                    "detail": "Reducer says COMPLETE but no valid evidence",
                })

        if tick.duplicate_fingerprints:
            tick.mismatches.append({
                "type": "duplicate_strategy",
                "fingerprints": tick.duplicate_fingerprints,
            })

        # 7. Write observation log (shadow-only, never touches STATE)
        self._write_tick_log(tick)

        return tick

    def _write_tick_log(self, tick: ShadowTick):
        """Write observation to shadow log directory."""
        log_path = os.path.join(SHADOW_LOG_DIR, f"shadow_tick_{tick.tick_id:06d}.json")
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(tick.to_dict(), f, indent=2, ensure_ascii=False)
        self.tick_count += 1

    def run_once(self) -> ShadowTick:
        """Run a single tick and return result."""
        tick_id = self.tick_count + 1
        return self.run_tick(tick_id)

    def run_continuous(self, duration_seconds: int = 60, interval: float = 5.0):
        """Run shadow observer continuously."""
        start = time.time()
        print(f"[Shadow] Starting continuous observation ({duration_seconds}s, {interval}s interval)")
        print(f"[Shadow] State source: {STATE_PATH}")
        print(f"[Shadow] Log dir: {SHADOW_LOG_DIR}\n")

        while time.time() - start < duration_seconds:
            tick = self.run_once()
            r = tick.reducer_result
            print(f"  Tick #{tick.tick_id}: state={tick.state_snapshot.get('status')} "
                  f"proposals={tick.proposal_scan['total']}/{tick.proposal_scan['valid']} "
                  f"evidence={tick.evidence_summary['total']}/{tick.evidence_summary['valid']} "
                  f"reducer={r['result']} "
                  f"duplicates={len(tick.duplicate_fingerprints)} "
                  f"mismatches={len(tick.mismatches)}")

            elapsed = time.time() - start
            if elapsed >= duration_seconds:
                break
            time.sleep(interval)

        print(f"\n[Shadow] Completed {self.tick_count} observations.")


# ── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="YuanCore Shadow Runtime Observer")
    parser.add_argument("--once", action="store_true", help="Run single tick only")
    parser.add_argument("--duration", type=int, default=60, help="Observation duration (seconds)")
    parser.add_argument("--interval", type=float, default=5.0, help="Tick interval (seconds)")
    parser.add_argument("--report", action="store_true", help="Generate evaluation report after run")
    args = parser.parse_args()

    runtime = ShadowRuntime()

    if args.once:
        tick = runtime.run_once()
        print(json.dumps(tick.to_dict(), indent=2, ensure_ascii=False))
    else:
        runtime.run_continuous(args.duration, args.interval)

        if args.report:
            from shadow_evaluator import load_shadow_observations, generate_report, print_report
            obs = load_shadow_observations()
            report = generate_report(obs)
            print_report(report)

    print(f"\nShadow runtime finished. Total ticks: {runtime.tick_count}")
