#!/usr/bin/env python3
"""
YuanCore Shadow Runtime — Evaluation Module

Analyzes shadow observation logs to validate Phase 5 correctness.
Metrics per shishi.plan Phase 5 acceptance criteria:
  1. Reducer false COMPLETE detection
  2. State recovery accuracy
  3. Duplicate strategy detection
  4. Old-pass / new-reject mismatches
  5. Evidence staleness tracking
  6. Context size reduction (via STATE vs legacy file count)
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional

SHADOW_LOG_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", ".yuan", "runtime", "shadow", "logs"
)


def load_observations(log_dir: str = None) -> List[Dict]:
    """Load all shadow observation logs, sorted by tick."""
    directory = log_dir or SHADOW_LOG_DIR
    observations = []
    if not os.path.exists(directory):
        return observations
    for fname in sorted(os.listdir(directory)):
        if not fname.startswith("shadow_tick_") or not fname.endswith(".json"):
            continue
        path = os.path.join(directory, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                obs = json.load(f)
                obs["source_file"] = fname
                observations.append(obs)
        except Exception:
            continue
    observations.sort(key=lambda x: x.get("tick", 0))
    return observations


def analyze_false_complete(observations: List[Dict]) -> Dict:
    """Check for Reducer predictions that say COMPLETE with insufficient evidence."""
    results = {"total_complete": 0, "risky_complete": 0, "details": []}
    for obs in observations:
        reducer = obs.get("reducer_prediction", {})
        if reducer.get("result") == "COMPLETE":
            results["total_complete"] += 1
            valid_ev = obs.get("evidence_summary", {}).get("valid", 0)
            total_ev = obs.get("evidence_summary", {}).get("total", 0)
            if valid_ev == 0 and total_ev == 0:
                results["risky_complete"] += 1
                results["details"].append({
                    "tick": obs.get("tick"),
                    "observation_id": obs.get("observation_id"),
                    "evidence_valid": valid_ev,
                    "evidence_total": total_ev,
                })
    return results


def analyze_duplicate_strategies(observations: List[Dict]) -> Dict:
    """Check for duplicate strategy fingerprints across ticks."""
    # Track fingerprints per tick
    fp_by_tick: Dict[int, List[str]] = {}
    for obs in observations:
        tick = obs.get("tick", 0)
        fps = obs.get("duplicate_fingerprints", [])
        if fps:
            fp_by_tick[tick] = fps

    return {
        "ticks_with_duplicates": len(fp_by_tick),
        "total_duplicate_groups": sum(len(v) for v in fp_by_tick.values()),
        "details": fp_by_tick,
    }


def analyze_state_recovery(observations: List[Dict]) -> Dict:
    """Check if shadow can accurately recover current state."""
    latest = observations[-1] if observations else None
    if not latest:
        return {"status": "no_observations"}

    state = latest.get("state_snapshot", {})
    return {
        "status": state.get("status", "UNKNOWN"),
        "current_revision": state.get("current_revision", 0),
        "has_attempt": state.get("attempt_id") is not None,
        "pending_changes": state.get("pending_changes", 0),
        "state_readable": "error" not in state,
    }


def analyze_mismatches(observations: List[Dict]) -> Dict:
    """Count and categorize shadow vs legacy mismatches."""
    mismatch_counts = {}
    total_mismatches = 0
    for obs in observations:
        for m in obs.get("mismatches", []):
            mtype = m.get("type", "unknown")
            mismatch_counts[mtype] = mismatch_counts.get(mtype, 0) + 1
            total_mismatches += 1

    return {
        "total_mismatches": total_mismatches,
        "by_type": mismatch_counts,
    }


def analyze_evidence_quality(observations: List[Dict]) -> Dict:
    """Track evidence staleness and validity over time."""
    staleness_over_time = []
    for obs in observations:
        ev = obs.get("evidence_summary", {})
        staleness_over_time.append({
            "tick": obs.get("tick"),
            "total": ev.get("total", 0),
            "stale": ev.get("stale", 0),
            "valid": ev.get("valid", 0),
            "invalid": ev.get("invalid", 0),
        })
    return {"timeline": staleness_over_time}


def generate_report(observations: List[Dict]) -> Dict:
    """Generate comprehensive Phase 5 evaluation report."""
    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_observations": len(observations),
        "metrics": {
            "false_complete": analyze_false_complete(observations),
            "duplicate_strategies": analyze_duplicate_strategies(observations),
            "state_recovery": analyze_state_recovery(observations),
            "mismatches": analyze_mismatches(observations),
            "evidence_quality": analyze_evidence_quality(observations),
        },
        "recommendations": [],
    }

    fc = report["metrics"]["false_complete"]
    if fc["risky_complete"] > 0:
        report["recommendations"].append(
            f"{fc['risky_complete']} COMPLETE prediction(s) with zero evidence — "
            "review reducer threshold logic."
        )

    dup = report["metrics"]["duplicate_strategies"]
    if dup["total_duplicate_groups"] > 0:
        report["recommendations"].append(
            f"Found {dup['total_duplicate_groups']} duplicate strategy groups — "
            "selection deduplication is working."
        )

    mm = report["metrics"]["mismatches"]
    if mm["total_mismatches"] > 0:
        report["recommendations"].append(
            f"{mm['total_mismatches']} shadow/legacy mismatches detected — "
            "review mismatch types."
        )

    sr = report["metrics"]["state_recovery"]
    if sr.get("status") == "no_observations":
        report["recommendations"].append(
            "No observations yet — run shadow observer for at least one tick."
        )

    if not report["recommendations"]:
        report["recommendations"].append("Shadow runtime operating within expected parameters.")

    return report


def print_report(report: Dict):
    """Pretty-print evaluation report."""
    print("\n" + "=" * 70)
    print("YuanCore Phase 5 Shadow Runtime — Evaluation Report")
    print("=" * 70)
    print(f"Generated: {report['generated_at']}")
    print(f"Total observations: {report['total_observations']}")

    fc = report["metrics"]["false_complete"]
    print(f"\n--- False COMPLETE Detection ---")
    print(f"  Total COMPLETE predictions: {fc['total_complete']}")
    print(f"  Risky (zero evidence): {fc['risky_complete']}")
    for d in fc["details"][:3]:
        print(f"    Tick #{d['tick']}: {d['evidence_valid']}/{d['evidence_total']} valid evidence")

    dup = report["metrics"]["duplicate_strategies"]
    print(f"\n--- Duplicate Strategy Detection ---")
    print(f"  Ticks with duplicates: {dup['ticks_with_duplicates']}")
    print(f"  Total duplicate groups: {dup['total_duplicate_groups']}")

    sr = report["metrics"]["state_recovery"]
    print(f"\n--- State Recovery ---")
    if sr.get("status") == "no_observations":
        print("  No observations available")
    else:
        print(f"  Status: {sr['status']}")
        print(f"  Revision: {sr['current_revision']}")
        print(f"  Has attempt: {sr['has_attempt']}")
        print(f"  State readable: {sr['state_readable']}")

    mm = report["metrics"]["mismatches"]
    print(f"\n--- Shadow/Legacy Mismatches ---")
    print(f"  Total: {mm['total_mismatches']}")
    for mtype, count in mm["by_type"].items():
        print(f"  {mtype}: {count}")

    print(f"\n--- Recommendations ---")
    for i, rec in enumerate(report["recommendations"], 1):
        print(f"  {i}. {rec}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate Shadow Runtime Observations")
    parser.add_argument("--log-dir", type=str, default=None, help="Override shadow log directory")
    parser.add_argument("--output", type=str, default=None, help="Save report to JSON file")
    args = parser.parse_args()

    observations = load_observations(args.log_dir)
    if not observations:
        print("No shadow observations found. Run runner.py first.")
        sys.exit(1)

    report = generate_report(observations)
    print_report(report)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\nReport saved to {args.output}")
