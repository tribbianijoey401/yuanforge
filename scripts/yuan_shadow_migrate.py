"""Yuan M4 one-way shadow migration and lossless rollback drill."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

from scripts.yuan_shadow_support import (
    GuardError,
    LegacyScan,
    MigrationError,
    assert_write_allowed,
    atomic_write,
    authority_pointer,
    build_history,
    build_work_contract,
    canonical_digest,
    canonical_json,
    discover_legacy,
    extract_legacy_records,
    rebuild_projection,
    rollback_shadow,
    safe_shadow_root,
    snapshot_digest,
    source_manifest,
    validate_projection,
    verify_shadow_projection,
    verify_source_manifests,
    write_new_shadow,
)


def _workspace_projection(
    repo_root: pathlib.Path,
    workspace: Any,
    manifest: dict[str, Any],
) -> tuple[dict[str, bytes], dict[str, Any]]:
    unresolved = [dict(item) for item in workspace.unresolved]
    legacy_records = extract_legacy_records(repo_root, workspace)
    work = build_work_contract(
        workspace,
        manifest,
        unresolved,
        replay_record_count=len(legacy_records),
    )
    attempts, evidence_items = build_history(
        workspace, manifest, work, unresolved, legacy_records
    )
    memory, core_result = rebuild_projection(
        work,
        attempts,
        evidence_items,
        unresolved,
        manifest["digest"],
    )
    validation_errors = validate_projection(
        work, attempts, evidence_items, memory
    )
    legacy_acs = []
    feature = workspace.documents.get("FEATURE.md")
    if feature:
        for line in feature.read_text(encoding="utf-8").splitlines():
            cells = [item.strip() for item in line.strip().strip("|").split("|")]
            if len(cells) >= 3 and cells[0].startswith("AC-"):
                legacy_acs.append(
                    {
                        "legacy_ac_id": cells[0],
                        "predicate": cells[1],
                        "required_evidence": cells[2],
                    }
                )
    replay_report = {
        "schema_version": "yuan.shadow-replay-report/v1",
        "workspace_id": workspace.workspace_id,
        "workspace_kind": workspace.kind,
        "covered": [item["path"] for item in manifest["files"]],
        "covered_count": len(manifest["files"]),
        "legacy_acceptance_criteria": legacy_acs,
        "replayed_records": legacy_records,
        "replayed_record_count": len(legacy_records),
        "unresolved": unresolved,
        "unresolved_count": len(unresolved),
        "core_rebuild_result": core_result,
        "projected_result": memory["last_result"],
        "validation_errors": validation_errors,
    }
    files: dict[str, bytes] = {
        "source-manifest.json": canonical_json(manifest),
        "work-contract.json": canonical_json(work),
        "run-memory.json": canonical_json(memory),
        "replay-report.json": canonical_json(replay_report),
    }
    for index, attempt in enumerate(attempts, start=1):
        files[f"attempts/{index:04d}.json"] = canonical_json(attempt)
    for index, evidence in enumerate(evidence_items, start=1):
        files[f"evidence/{index:04d}.json"] = canonical_json(evidence)
    return files, replay_report


def _projection_digest(files: dict[str, bytes]) -> str:
    return canonical_digest(
        [
            {
                "path": relative,
                "sha256": __import__("hashlib").sha256(payload).hexdigest(),
            }
            for relative, payload in sorted(files.items())
            if relative.startswith("workspaces/")
        ]
    )


def migrate(
    repo_root: pathlib.Path,
    shadow_root: pathlib.Path,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    shadow = safe_shadow_root(repo, pathlib.Path(shadow_root))
    scan: LegacyScan = discover_legacy(repo)
    if not scan.workspaces:
        raise MigrationError("no recognizable legacy Workspace found")
    manifests = [
        source_manifest(repo, workspace) for workspace in scan.workspaces
    ]
    verify_source_manifests(repo, manifests)

    output_files: dict[str, bytes] = {}
    workspace_reports: list[dict[str, Any]] = []
    validation_errors: list[str] = []
    for workspace, manifest in zip(scan.workspaces, manifests):
        workspace_files, replay_report = _workspace_projection(
            repo, workspace, manifest
        )
        base = f"workspaces/{workspace.workspace_id}"
        for relative, payload in workspace_files.items():
            output_files[f"{base}/{relative}"] = payload
        workspace_reports.append(replay_report)
        validation_errors.extend(
            f"{workspace.workspace_id}:{item}"
            for item in replay_report["validation_errors"]
        )

    projection_digest = _projection_digest(output_files)
    legacy_digest = snapshot_digest(manifests)
    pointer = authority_pointer(repo, shadow, legacy_digest)
    report = {
        "schema_version": "yuan.shadow-migration-report/v1",
        "operation": "MIGRATED",
        "authority": "legacy",
        "active_workspace_id": scan.active_workspace_id,
        "workspace_count": len(scan.workspaces),
        "covered_sources": sum(
            item["covered_count"] for item in workspace_reports
        ),
        "replayed_records": sum(
            item["replayed_record_count"] for item in workspace_reports
        ),
        "unresolved_count": len(scan.unresolved)
        + sum(item["unresolved_count"] for item in workspace_reports),
        "global_unresolved": scan.unresolved,
        "workspaces": workspace_reports,
        "legacy_snapshot_sha256": legacy_digest,
        "projection_digest": projection_digest,
        "validation_errors": sorted(set(validation_errors)),
        "single_writable_authority": True,
        "dual_write": False,
    }
    output_files["authority.json"] = canonical_json(pointer)
    output_files["report.json"] = canonical_json(report)
    verify_source_manifests(repo, manifests)
    if dry_run:
        return {**report, "operation": "DRY_RUN"}
    write_new_shadow(
        repo,
        shadow,
        output_files,
        manifests,
        projection_digest,
    )
    verify_source_manifests(repo, manifests)
    return report


def rollback(
    repo_root: pathlib.Path,
    shadow_root: pathlib.Path,
    receipt_path: pathlib.Path | None = None,
) -> dict[str, Any]:
    return rollback_shadow(
        pathlib.Path(repo_root),
        pathlib.Path(shadow_root),
        pathlib.Path(receipt_path) if receipt_path is not None else None,
    )


def verify(
    repo_root: pathlib.Path,
    shadow_root: pathlib.Path,
    receipt_path: pathlib.Path | None = None,
) -> dict[str, Any]:
    result = verify_shadow_projection(
        pathlib.Path(repo_root), pathlib.Path(shadow_root)
    )
    if receipt_path is not None:
        repo = pathlib.Path(repo_root).resolve()
        receipt = pathlib.Path(receipt_path).resolve()
        try:
            receipt.relative_to(repo)
        except ValueError as error:
            raise MigrationError("verification receipt must be inside repository") from error
        atomic_write(receipt, canonical_json(result))
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read legacy Yuan docs and build an inert Core shadow projection."
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    migrate_parser = subcommands.add_parser("migrate")
    migrate_parser.add_argument("--repo", type=pathlib.Path, required=True)
    migrate_parser.add_argument("--shadow-root", type=pathlib.Path, required=True)
    migrate_parser.add_argument("--dry-run", action="store_true")
    rollback_parser = subcommands.add_parser("rollback")
    rollback_parser.add_argument("--repo", type=pathlib.Path, required=True)
    rollback_parser.add_argument("--shadow-root", type=pathlib.Path, required=True)
    rollback_parser.add_argument("--receipt", type=pathlib.Path)
    verify_parser = subcommands.add_parser("verify")
    verify_parser.add_argument("--repo", type=pathlib.Path, required=True)
    verify_parser.add_argument("--shadow-root", type=pathlib.Path, required=True)
    verify_parser.add_argument("--receipt", type=pathlib.Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    args = _parser().parse_args(argv)
    try:
        if args.command == "migrate":
            result = migrate(
                args.repo, args.shadow_root, dry_run=args.dry_run
            )
        elif args.command == "rollback":
            result = rollback(args.repo, args.shadow_root, args.receipt)
        else:
            result = verify(args.repo, args.shadow_root, args.receipt)
    except (MigrationError, GuardError, OSError, UnicodeError, json.JSONDecodeError) as error:
        result = {
            "schema_version": "yuan.shadow-operation-error/v1",
            "status": "BLOCKED",
            "error": str(error),
        }
        print(
            json.dumps(result, ensure_ascii=False, sort_keys=True),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("status") != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
