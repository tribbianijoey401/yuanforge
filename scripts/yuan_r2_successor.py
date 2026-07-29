"""Install the trust-bound task-011-r2 successor Work and authority revision."""

from __future__ import annotations

import copy
import json
import pathlib
import shutil
from typing import Any

from yuan_activation import verify_activation_descriptor
from yuan_authority import load_current, verify_authority
from yuan_runtime_state import (
    RUNS_ROOT,
    atomic_write,
    canonical,
    file_sha256,
    rebuild_runtime_memory,
    resolve_runtime_root,
    seal_runtime,
    verify_runtime_at,
    write_immutable,
)
from yuan_runtime_transaction import (
    canonical_digest,
    replace_runtime_generation,
)


def _documents(repo: pathlib.Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    runtime, _, _ = resolve_runtime_root(repo)
    work = json.loads(next((runtime / "contracts").glob("*.json")).read_text())
    attempt = json.loads(next((runtime / "attempts").glob("*.json")).read_text())
    evidence = json.loads(next((runtime / "evidence").glob("*.json")).read_text())
    activation = verify_activation_descriptor(repo)
    work = copy.deepcopy(work)
    work["harness_binding"]["sha256"] = file_sha256(
        repo / "scripts/yuan_runtime_transaction.py"
    )
    work["revision"]["revision"] = "2"
    work["revision"]["sha256"] = canonical_digest(
        work, omitted_paths=(("revision", "sha256"),)
    )
    descriptor_sha = activation["descriptor_sha256"]
    receipt_sha = activation["independent_evidence_sha256"]
    attempt = copy.deepcopy(attempt)
    attempt.update(
        {
            "attempt_id": "ATT-M8-R2-ACTIVATION-0001",
            "sequence": 1,
            "work_binding": work["revision"],
            "harness_binding": work["harness_binding"],
            "evidence_ids": ["EVD-M8-R2-ACTIVATION-0001"],
        }
    )
    attempt["relevant_inputs"] = [
        {
            "scope": ".yuan/authority/activation/yuan-core-0.1.json",
            "sha256": descriptor_sha,
        }
    ]
    attempt["tool_receipt"]["stdout_sha256"] = receipt_sha
    attempt["strategy_fingerprint"] = canonical_digest(
        {
            "strategy": "r2-old-root-activation",
            "descriptor": descriptor_sha,
            "harness": work["harness_binding"]["sha256"],
        }
    )
    evidence = copy.deepcopy(evidence)
    evidence.update(
        {
            "evidence_id": "EVD-M8-R2-ACTIVATION-0001",
            "sequence": 1,
            "source_attempt_id": attempt["attempt_id"],
            "work_binding": work["revision"],
            "harness_binding": work["harness_binding"],
            "artifact_binding": {
                "scope": ".yuan/authority",
                "sha256": descriptor_sha,
            },
        }
    )
    evidence["freshness"]["observed_artifact_sha256"] = descriptor_sha
    evidence["logs"]["receipt_sha256"] = receipt_sha
    evidence["immutable_digest"] = canonical_digest(
        evidence, omitted_paths=(("immutable_digest",),)
    )
    return work, attempt, evidence


def install(
    repo_root: pathlib.Path,
    *,
    failure_after: str | None = None,
) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    current = load_current(repo)
    runtime_before, active, active_sha = resolve_runtime_root(repo)
    if active is None or active_sha is None:
        raise RuntimeError("task-011-r2 requires the r1 active successor")
    work, attempt, evidence = _documents(repo)
    run_id = f"{work['work_id']}-r2-{work['revision']['sha256'][:12]}"
    final = repo / RUNS_ROOT / run_id
    pending = repo / RUNS_ROOT / f".pending-r2-{work['revision']['sha256'][:12]}"
    if final.exists() or pending.exists():
        raise RuntimeError("task-011-r2 successor already exists")
    for area in ("contracts", "attempts", "evidence"):
        (pending / area).mkdir(parents=True, exist_ok=True)
    write_immutable(
        pending / "contracts" / f"{work['work_id']}.json", canonical(work)
    )
    write_immutable(pending / "attempts/0001.json", canonical(attempt))
    write_immutable(pending / "evidence/0001.json", canonical(evidence))
    atomic_write(
        pending / "run-memory.json",
        canonical(rebuild_runtime_memory(repo, pending)),
        None,
    )
    previous = verify_runtime_at(repo, runtime_before)
    seal_runtime(
        repo,
        pending,
        legacy_snapshot_sha256=previous["legacy_snapshot_sha256"],
        source_projection_sha256=file_sha256(
            runtime_before / "runtime-manifest.json"
        ),
    )
    verify_runtime_at(repo, pending)
    pending.rename(final)
    transaction = replace_runtime_generation(
        repo,
        final,
        expected_authority_pointer_sha256=current["pointer_sha256"],
        expected_active_run_pointer_sha256=active_sha,
        protocol_activation=verify_activation_descriptor(repo),
        failure_after=failure_after,
    )
    return {
        "status": "PASS",
        "runtime_root": final.relative_to(repo).as_posix(),
        "transaction": transaction,
        "authority": verify_authority(repo),
    }


def main() -> int:
    repo = pathlib.Path(__file__).resolve().parents[1]
    try:
        result = install(repo)
    except Exception as error:
        print(f"FAIL {error}")
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
