# State Template (Auto-generated)

**Schema:** `yuan.state/v1`

This file is automatically managed by the Core Harness. Do not edit manually.

## Auto-Generated Fields

```yaml
schema: yuan.state/v1
current_revision: 1
current_artifact_hash: ""   # Set at runtime
status: IDLE                # IDLE | RUNNING | PAUSED | COMPLETE | FAILED
attempt_id: null            # Currently executing Attempt
pending_changes: []         # Approved changes waiting application
side_effect_trackers: []    # Ongoing non-reversible operations
journals_start: ""          # First Journal entry
journals_end: ""            # Most recent Journal entry
```

## Usage Notes

- The Harness reads this file at the start of each tick to determine current state
- All modifications must use Compare-and-Swap (CAS) semantics to prevent races
- On recovery, the Harness restores state from this file
- View files (TASK_BOARD, PROGRESS, SESSION) are generated FROM this state, never written directly
