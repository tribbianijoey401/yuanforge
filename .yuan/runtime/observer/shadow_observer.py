#!/usr/bin/env python3
"""
YuanCore Shadow Runtime Observer

This script runs in "shadow mode" - it observes the existing YuanForge workflow
without interfering with it. It reads the same inputs as the Conductor but feeds
them through the Core's deterministic reduction logic, producing observations
for validation and comparison.

Key principle: Shadow writes ONLY to its own observation logs, never to the
authoritative work/STATE.md or any other state file that the legacy system uses.
"""

import os
import sys
import json
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Optional

# Add scripts path
sys.path.insert(0, '/home/admin/yuanforge/scripts/validation')

from core_validator import ProposalValidator, RoleExtensionValidator, ValidationError

# Paths
LEGACY_STATE_DIR = "/home/admin/yuanforge/docs"  # Legacy PROGRESS.md, TASK_BOARD location
WORK_DIR = "/home/admin/yuanforge/work"          # New Core work directory
SHADOW_LOG_DIR = "/home/admin/yuanforge/.yuan/runtime/shadow/logs"
CORE_SCHEMA_PATH = "/home/admin/yuanforge/.yuan/core/schemas/PROPOSAL.md"

os.makedirs(SHADOW_LOG_DIR, exist_ok=True)


class ShadowObserver:
    """Observes legacy system and computes what Core would do."""
    
    def __init__(self):
        self.observation_count = 0
        self.mismatches = []
    
    def load_legacy_state(self) -> Dict:
        """Load state from legacy sources (TASK_BOARD, PROGRESS, SESSION)."""
        # In legacy YuanForge, state is distributed across multiple files
        # For shadow observation, we need to reconstruct a unified view
        
        state = {"timestamp": datetime.utcnow().isoformat()}
        
        # Read TASK_BOARD if exists
        tb_path = os.path.join(LEGACY_STATE_DIR, "TASK_BOARD.md")
        if os.path.exists(tb_path):
            state["task_board"] = self._read_file(tb_path)
        
        # Read PROGRESS if exists
        pg_path = os.path.join(LEGACY_STATE_DIR, "PROGRESS.md")
        if os.path.exists(pg_path):
            state["progress"] = self._read_file(pg_path)
        
        return state
    
    def _read_file(self, path: str) -> str:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()[:10000]  # Limit size to avoid memory issues
        except Exception:
            return "[ERROR: Could not read file]"
    
    def scan_proposals(self) -> List[Dict]:
        """Scan for proposals in the proposals directory."""
        proposals_dir = os.path.join(WORK_DIR, "proposals")
        if not os.path.exists(proposals_dir):
            return []
        
        proposals = []
        for fname in os.listdir(proposals_dir):
            if fname.endswith(".md"):
                prop_path = os.path.join(proposals_dir, fname)
                try:
                    pv = ProposalValidator(prop_path)
                    proposals.append({
                        "id": fname,
                        "valid": len(pv.validate()) == 0,
                        "fingerprint": pv.get_strategy_fingerprint() if pv.proposal else None
                    })
                except Exception:
                    proposals.append({"id": fname, "valid": False, "fingerprint": None})
        
        return proposals
    
    def compute_reducer_decision(self, state: Dict, proposals: List[Dict]) -> Dict:
        """Compute what the Reducer would decide given current state and proposals.
        
        This is a simplified shadow reducer - in production, the full REDUCER.md
        decision table would be implemented.
        """
        # Check for unhandled conditions (simplified for shadow mode)
        result = {
            "type": "CONTINUE",  # Default fallback
            "reason": "Need more evidence",
            "confidence": 0.5,
            "observations": []
        }
        
        # Count valid proposals
        valid_p = [p for p in proposals if p["valid"]]
        result["observations"].append(f"Found {len(valid_p)} valid proposals")
        
        # Check if all acceptance criteria might be met (very rough estimate)
        if len(valid_p) >= 2:  # Heuristic: multiple proposals suggest progress
            result["type"] = "CONTINUE"
            result["reason"] = "Multiple candidate proposals available"
        elif not proposals:
            result["type"] = "WAIT_AUTH"
            result["reason"] = "No proposals submitted"
        
        return result
    
    def log_observation(self, tick_id: int, state: Dict, proposals: Dict, reducer_result: Dict):
        """Log a shadow observation entry."""
        log_entry = {
            "tick": tick_id,
            "timestamp": datetime.utcnow().isoformat(),
            "legacy_state_snapshot": {
                "task_board_present": "task_board" in state,
                "progress_present": "progress" in state,
                "state_summary": str(state)[:200]
            },
            "proposal_scan": {
                "total": len(proposals),
                "valid": sum(1 for p in proposals if p["valid"])
            },
            "reducer_prediction": reducer_result,
            "observation_id": f"O-{tick_id:06d}"
        }
        
        log_path = os.path.join(SHADOW_LOG_DIR, f"shadow_tick_{tick_id:06d}.json")
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)
        
        self.observation_count += 1
        print(f"  [Shadow] Logged observation O-{tick_id:06d} -> {reducer_result['type']}")
    
    def run_single_tick(self, tick_id: int) -> Dict:
        """Run one iteration of shadow observation."""
        print(f"[Shadow] Running tick #{tick_id}...")
        
        # Step 1: Load legacy state
        state = self.load_legacy_state()
        
        # Step 2: Scan proposals
        proposals = self.scan_proposals()
        
        # Step 3: Compute reducer decision
        reducer_result = self.compute_reducer_decision(state, proposals)
        
        # Step 4: Log observation
        self.log_observation(tick_id, state, proposals, reducer_result)
        
        # Step 5: Return summary for comparison
        return {
            "tick": tick_id,
            "reducer_result": reducer_result,
            "proposal_count": len(proposals),
            "valid_proposal_count": sum(1 for p in proposals if p["valid"]),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def run_continuous(self, duration_seconds: int = 60):
        """Run shadow observer continuously for specified duration."""
        start_time = time.time()
        tick_id = 0
        
        print(f"[Shadow] Starting continuous observation for {duration_seconds}s...")
        print(f"Observing at: {WORK_DIR}")
        print(f"Logging to: {SHADOW_LOG_DIR}\n")
        
        while time.time() - start_time < duration_seconds:
            tick_id += 1
            try:
                self.run_single_tick(tick_id)
            except Exception as e:
                print(f"[Shadow] Error at tick {tick_id}: {e}")
            
            # Wait a bit before next tick (adjustable)
            time.sleep(2)
        
        print(f"\n[Shadow] Completed {self.observation_count} observations.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="YuanCore Shadow Runtime Observer")
    parser.add_argument("--duration", type=int, default=60, 
                       help="Observation duration in seconds (continuous mode)")
    parser.add_argument("--once", action="store_true",
                       help="Run single observation tick only")
    
    args = parser.parse_args()
    
    observer = ShadowObserver()
    
    if args.once:
        result = observer.run_single_tick(1)
        print(f"\nResult: {json.dumps(result, indent=2, ensure_ascii=False)}")
    else:
        observer.run_continuous(args.duration)
    
    print(f"\nShadow observer finished. Total observations: {observer.observation_count}")
