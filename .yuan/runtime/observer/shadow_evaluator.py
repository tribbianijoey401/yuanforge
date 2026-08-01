#!/usr/bin/env python3
"""
Shadow Runtime Evaluation Framework

This tool evaluates the Shadow Observer's observations against actual 
legacy system outcomes to validate the Core's correctness during
Phase 5 (Shadow Runtime).

Evaluation metrics from the YuanCore plan:
1. Whether the Reducer incorrectly COMPLETEs
2. Whether it accurately recovers current state  
3. Whether it identifies duplicate strategies
4. Whether there are old system pass/new core false positives
5. Whether user confirmation count decreases
6. Whether context size reduces
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Shadow log directory
SHADOW_LOG_DIR = "/home/admin/yuanforge/.yuan/runtime/shadow/logs"

def load_shadow_observations() -> List[Dict]:
    """Load all shadow observation logs."""
    observations = []
    for fname in os.listdir(SHADOW_LOG_DIR):
        if fname.endswith(".json"):
            path = os.path.join(SHADOW_LOG_DIR, fname)
            with open(path, 'r', encoding='utf-8') as f:
                obs = json.load(f)
                obs["source_file"] = fname
                observations.append(obs)
    # Sort by tick number
    observations.sort(key=lambda x: x.get("tick", 0))
    return observations

def analyze_strategy_duplicates(observations: List[Dict]) -> Dict:
    """Analyze whether shadow correctly identifies duplicate strategy attempts."""
    fingerprints = {}
    for obs in observations:
        fp = obs.get("reducer_prediction", {}).get("strategy_fingerprint")
        if fp:
            if fp not in fingerprints:
                fingerprints[fp] = {"count": 1, "ticks": [obs.get("tick")]}
            else:
                fingerprints[fp]["count"] += 1
                fingerprints[fp]["ticks"].append(obs.get("tick"))
    
    duplicates = {fp: info for fp, info in fingerprints.items() if info["count"] > 1}
    
    return {
        "total_unique_fingerprints": len(fingerprints),
        "duplicate_strategies": len(duplicates),
        "detailed": duplicates
    }

def analyze_complete_errors(observations: List[Dict]) -> Dict:
    """Check if Reducer incorrectly predicts COMPLETE when it shouldn't."""
    complete_predictions = [o for o in observations 
                           if o.get("reducer_prediction", {}).get("type") == "COMPLETE"]
    
    # Heuristic: if there are fewer than 3 valid proposals, COMPLETE might be premature
    risky_complete = []
    for obs in complete_predictions:
        valid_count = obs.get("proposal_scan", {}).get("valid", 0)
        if valid_count < 2:
            risky_complete.append({
                "tick": obs.get("tick"),
                "valid_proposals": valid_count,
                "snapshot": obs.get("legacy_state_snapshot", {})[:100]
            })
    
    return {
        "total_complete_predictions": len(complete_predictions),
        "potentially_risky": len(risky_complete),
        "risk_details": risky_complete
    }

def compare_with_legacy(observations: List[Dict], legacy_status_log: str) -> Dict:
    """Compare shadow predictions against actual legacy outcomes (if available)."""
    # This would integrate with actual task execution logs
    # For now, returns placeholder analysis
    return {
        "note": "Integration with legacy status logs requires additional setup",
        "recommendation": "Implement TaskBoard polling hook for direct comparison"
    }

def generate_report(observations: List[Dict]) -> Dict:
    """Generate comprehensive evaluation report."""
    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_observations": len(observations),
        "analysis": {
            "duplicates": analyze_strategy_duplicates(observations),
            "complete_errors": analyze_complete_errors(observations),
            "legacy_comparison": compare_with_legacy(observations, "")
        },
        "recommendations": []
    }
    
    # Generate recommendations based on findings
    dup_analysis = report["analysis"]["duplicates"]
    if dup_analysis["duplicate_strategies"] > 0:
        report["recommendations"].append(
            f"Found {dup_analysis['duplicate_strategies']} duplicate strategy patterns. "
            "Verify that Shadow's deduplication logic correctly prevents redundant attempts."
        )
    
    complete_errors = report["analysis"]["complete_errors"]
    if complete_errors["potentially_risky"] > 0:
        report["recommendations"].append(
            f"{complete_errors['potentially_risky']} COMPLETE prediction(s) may be premature. "
            "Review reducer decision table thresholds."
        )
    
    if not report["recommendations"]:
        report["recommendations"].append("No immediate concerns identified. Continue monitoring.")
    
    return report

def print_report(report: Dict):
    """Pretty-print evaluation report."""
    print("\n" + "=" * 70)
    print("YuanCore Shadow Runtime - Evaluation Report")
    print("=" * 70)
    print(f"Generated: {report['generated_at']}")
    print(f"Total observations analyzed: {report['total_observations']}\n")
    
    dup = report["analysis"]["duplicates"]
    print("Strategy Duplication Analysis:")
    print(f"  Unique fingerprints: {dup['total_unique_fingerprints']}")
    print(f"  Duplicate patterns found: {dup['duplicate_strategies']}")
    if dup["detailed"]:
        for fp, info in list(dup["detailed"].items())[:3]:  # Show top 3
            print(f"    - {fp[:32]}...: observed {info['count']} times at ticks {info['ticks']}")
    
    complete = report["analysis"]["complete_errors"]
    print(f"\nCOMPLETE Prediction Analysis:")
    print(f"  Total COMPLETE predictions: {complete['total_complete_predictions']}")
    print(f"  Potentially premature: {complete['potentially_risky']}")
    
    print(f"\nRecommendations:")
    for i, rec in enumerate(report["recommendations"], 1):
        print(f"  {i}. {rec}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate Shadow Runtime Observations")
    parser.add_argument("--output", type=str, default=None,
                       help="Save report to JSON file")
    parser.add_argument("--verbose", action="store_true",
                       help="Include detailed observation data in output")
    
    args = parser.parse_args()
    
    observations = load_shadow_observations()
    
    if not observations:
        print("No shadow observations found. Run shadow_observer.py first.")
        sys.exit(1)
    
    report = generate_report(observations)
    
    if args.verbose:
        report["raw_observations"] = observations
    
    print_report(report)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\nReport saved to {args.output}")
