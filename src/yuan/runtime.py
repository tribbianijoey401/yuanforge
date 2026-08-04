"""由不可变 Ledger Event 构建的 Yuan Run 生命周期。"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .artifacts import build_manifest, changed_paths, diff_manifests
from .canonical import canonical_bytes, digest, digest_bytes, verify_digest
from .errors import IntegrityError, ValidationError
from .identity import harness_digest, protocol_revision
from .ledger import Ledger, atomic_write, exclusive_lock
from .paths import scope_contains
from .reducer import reduce_projection
from .validate import action_authorized, identifier, validate_evidence, validate_proposal, validate_work
from .workflow import validate_handoff


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"JSON 文件不合法：{path}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"JSON 文档必须是 Object：{path}")
    return value


def load_config(root: Path) -> dict[str, Any]:
    path = root.resolve() / ".yuan" / "config.json"
    value = read_json(path)
    required = {
        "schema_version", "profile", "protocol", "harness", "state_root",
        "artifact_exclude", "environment", "capability", "digest",
    }
    if set(value) != required or value["schema_version"] != "yuan.config/v1":
        raise IntegrityError("Yuan config 不合法")
    if not verify_digest(value):
        raise IntegrityError("Yuan config digest 不匹配")
    protocol_path = root.resolve() / ".yuan" / "protocol.md"
    try:
        protocol_digest = digest_bytes(protocol_path.read_bytes())
    except OSError as exc:
        raise IntegrityError("已选择的 Protocol 不存在") from exc
    if protocol_digest != value["protocol"].get("digest"):
        raise IntegrityError("已选择的 Protocol digest 不匹配")
    if protocol_revision(protocol_path.read_bytes()) != value["protocol"].get("revision"):
        raise IntegrityError("已选择的 Protocol revision 不匹配")
    if harness_digest() != value["harness"].get("digest"):
        raise IntegrityError("当前 Kernel 与固定的 Harness 不匹配")
    capability = value["capability"]
    if capability is not None:
        from .capabilities import read_installed_manifest
        from .validate import binding

        binding(capability, "capability")
        manifest = read_installed_manifest(root)
        expected = {
            "id": manifest["profile_id"],
            "revision": manifest["profile_version"],
            "digest": manifest["digest"],
        }
        if capability != expected:
            raise IntegrityError("Yuan config 与已安装 Capability Profile Binding 不匹配")
    return value


def state_root(root: Path, config: dict[str, Any]) -> Path:
    target = (root.resolve() / config["state_root"]).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise IntegrityError("State Root 越出仓库") from exc
    return target


def current_run_id(root: Path, config: dict[str, Any]) -> str:
    pointer = state_root(root, config) / "current.json"
    value = read_json(pointer)
    if set(value) != {"run_id"} or not isinstance(value["run_id"], str):
        raise IntegrityError("Current Run Pointer 不合法")
    return identifier(value["run_id"], "run_id")


def active_ledger(root: Path) -> tuple[dict[str, Any], Ledger]:
    config = load_config(root)
    return config, Ledger(state_root(root, config), current_run_id(root, config))


def artifact_for(root: Path, work: dict[str, Any]) -> dict[str, Any]:
    # Long-term Memory 是 Work/Evidence 的派生语义记录，不属于被验证 Artifact。
    # 运行时强制排除可让新 Runtime 在旧 Work 尚未声明该路径时仍保持兼容。
    exclude = list(dict.fromkeys([*work["artifact"]["exclude"], "docs/memory/**"]))
    return build_manifest(
        root,
        include=work["artifact"]["include"],
        exclude=exclude,
    )


def _manifest_from_blob(ledger: Ledger, blob: str) -> dict[str, Any]:
    try:
        value = json.loads(ledger.get_blob(blob).decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise IntegrityError("Artifact Manifest Blob 不合法") from exc
    if not isinstance(value, dict) or value.get("digest") != digest(value, ("digest",)):
        raise IntegrityError("Artifact Manifest digest 不匹配")
    return value


def replay(
    ledger: Ledger,
    *,
    current_artifact_digest: str | None = None,
    _events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    projection: dict[str, Any] = {
        "schema_version": "yuan.run-memory/v1",
        "run_id": ledger.run_id,
        "work": None,
        "attempts": {},
        "attempt_order": [],
        "evidence": {},
        "criterion_evidence": {},
        "latest_evidence": None,
        "handoffs": {},
        "agent_handoffs": {},
        "latest_handoff": None,
        "superseded": None,
        "authorization_required": None,
        "budgets_used": {"ticks": 0, "attempts": 0, "tool_calls": 0, "command_seconds": 0},
        "errors": [],
        "legal_next_step": True,
        "expected_artifact": None,
    }
    events = ledger.events() if _events is None else _events
    for event in events:
        kind = event["type"]
        payload = event["payload"]
        try:
            if kind == "WORK_ACCEPTED":
                if projection["work"] is not None:
                    raise IntegrityError("Run 包含多个 Work Record")
                projection["work"] = validate_work(payload, require_confirmation=True)
            elif kind == "ARTIFACT_BASELINED":
                if projection["work"] is None or projection["expected_artifact"] is not None:
                    raise IntegrityError("Artifact Baseline 位置错误或重复")
                manifest = _manifest_from_blob(ledger, payload["manifest_blob"])
                if payload.get("artifact_digest") != manifest["digest"]:
                    raise IntegrityError("Artifact Baseline Payload 与其 Blob 不匹配")
                projection["expected_artifact"] = payload["artifact_digest"]
            elif kind == "AUTHORIZATION_REQUIRED":
                if projection["work"] is None:
                    raise IntegrityError("Authorization Event 早于 Work")
                projection["authorization_required"] = payload
            elif kind == "BUDGET_EXHAUSTED":
                if projection["work"] is None:
                    raise IntegrityError("Budget Event 早于 Work")
                charge = payload.get("budget_charge")
                if not isinstance(charge, dict) or not any(
                    projection["budgets_used"].get(name, 0) + charge.get(name, 0) > maximum
                    for name, maximum in projection["work"]["budgets"].items()
                ):
                    raise IntegrityError("Budget Exhaustion Event 没有耗尽任何 Budget")
                projection["budgets_used"]["_exhausted"] = True
            elif kind == "ATTEMPT_PREPARED":
                work = projection["work"]
                if work is None:
                    raise IntegrityError("Attempt 早于 Work")
                attempt_id = payload.get("attempt_id")
                if attempt_id in projection["attempts"]:
                    raise IntegrityError("Attempt id 重复")
                expected_sequence = len(projection["attempt_order"]) + 1
                if payload.get("sequence") != expected_sequence or payload.get("work_digest") != work["digest"]:
                    raise IntegrityError("Attempt sequence 或 Work Binding 不匹配")
                validate_proposal(payload["proposal"])
                if payload["proposal"]["attempt_id"] != attempt_id:
                    raise IntegrityError("Attempt Proposal Identity 不匹配")
                reconciliation = payload["proposal"].get("reconciliation")
                if reconciliation is None:
                    if payload.get("artifact_before") != projection["expected_artifact"]:
                        raise IntegrityError("Attempt Baseline 与权威 Artifact 不一致")
                else:
                    target = projection["attempts"].get(reconciliation["target_attempt_id"])
                    if not target or target["state"] != "UNKNOWN":
                        raise IntegrityError("Reconciliation Target 不是 UNKNOWN Attempt")
                    if payload["proposal"]["action"]["paths"] != target["proposal"]["action"]["paths"]:
                        raise IntegrityError("Reconciliation Scope 与原 Attempt 不一致")
                if not action_authorized(work, payload["proposal"]["action"]):
                    raise IntegrityError("已准备的 Attempt 未获授权")
                before_manifest = _manifest_from_blob(ledger, payload["manifest_before_blob"])
                if before_manifest["digest"] != payload["artifact_before"]:
                    raise IntegrityError("Attempt Baseline Blob 不匹配")
                initial = "PREPARED" if payload["proposal"]["action"]["mutating"] else "NOT_APPLICABLE"
                projection["attempts"][attempt_id] = {**payload, "state": initial}
                projection["attempt_order"].append(attempt_id)
                for name, charge in payload["proposal"]["budget_charge"].items():
                    projection["budgets_used"][name] += charge
                if any(
                    projection["budgets_used"][name] > maximum
                    for name, maximum in work["budgets"].items()
                ):
                    raise IntegrityError("Attempt Budget Charge 超出 Work Maximum")
            elif kind == "ATTEMPT_DISPATCHED":
                attempt = projection["attempts"].get(payload.get("attempt_id"))
                if not attempt or attempt["state"] != "PREPARED":
                    raise IntegrityError("ATTEMPT_DISPATCHED Transition 不合法")
                attempt["state"] = "DISPATCHED"
            elif kind in {"ATTEMPT_OBSERVED", "ATTEMPT_UNKNOWN", "ATTEMPT_COMMITTED"}:
                attempt = projection["attempts"].get(payload.get("attempt_id"))
                if not attempt:
                    raise IntegrityError("Attempt Transition 指向未知 id")
                expected = {
                    "ATTEMPT_OBSERVED": {"DISPATCHED"},
                    "ATTEMPT_UNKNOWN": {"DISPATCHED", "OBSERVED"},
                    "ATTEMPT_COMMITTED": {"OBSERVED"},
                }[kind]
                if attempt["state"] not in expected:
                    raise IntegrityError(f"{kind} Transition 不合法")
                if kind == "ATTEMPT_OBSERVED":
                    before = _manifest_from_blob(ledger, attempt["manifest_before_blob"])
                    after = _manifest_from_blob(ledger, payload["manifest_after_blob"])
                    if after["digest"] != payload.get("artifact_after"):
                        raise IntegrityError("Observed Artifact Blob 不匹配")
                    expected_diff = diff_manifests(before, after)
                    if payload.get("diff") != expected_diff:
                        raise IntegrityError("Observed Artifact Diff 不匹配")
                    unexpected = [
                        path for path in changed_paths(expected_diff)
                        if not any(scope_contains(scope, path) for scope in attempt["proposal"]["action"]["paths"])
                    ]
                    if unexpected:
                        raise IntegrityError("Observed Attempt 包含未声明修改")
                    receipt = json.loads(ledger.get_blob(payload["receipt_blob"]).decode("utf-8"))
                    if digest(receipt) != payload.get("receipt_digest"):
                        raise IntegrityError("Observed Receipt Blob 不匹配")
                if kind == "ATTEMPT_COMMITTED" and (
                    payload.get("artifact_after") != attempt.get("artifact_after")
                    or payload.get("receipt_digest") != attempt.get("receipt_digest")
                ):
                    raise IntegrityError("Commit 未绑定对应 Observation")
                attempt.update(payload)
                attempt["state"] = {
                    "ATTEMPT_OBSERVED": "OBSERVED",
                    "ATTEMPT_UNKNOWN": "UNKNOWN",
                    "ATTEMPT_COMMITTED": "COMMITTED",
                }[kind]
                if kind == "ATTEMPT_COMMITTED":
                    projection["expected_artifact"] = payload["artifact_after"]
            elif kind == "ATTEMPT_RECONCILED":
                target = projection["attempts"].get(payload.get("target_attempt_id"))
                reconciler = projection["attempts"].get(payload.get("reconciler_attempt_id"))
                if not target or target["state"] != "UNKNOWN":
                    raise IntegrityError("Reconciliation Target 不是 UNKNOWN Attempt")
                if not reconciler or reconciler["state"] != "NOT_APPLICABLE":
                    raise IntegrityError("Reconciler 必须是已完成的只读 Attempt")
                binding = reconciler["proposal"].get("reconciliation")
                if not binding or binding["target_attempt_id"] != target["attempt_id"]:
                    raise IntegrityError("Reconciler 没有绑定目标 Attempt")
                after = _manifest_from_blob(ledger, payload["manifest_after_blob"])
                if after["digest"] != payload.get("artifact_after"):
                    raise IntegrityError("Reconciliation Artifact Blob 不匹配")
                resolution = payload.get("resolution")
                if resolution == "COMMITTED":
                    evidence = projection["evidence"].get(payload.get("evidence_id"))
                    if (
                        not evidence
                        or evidence["attempt_id"] != reconciler["attempt_id"]
                        or evidence["status"] != "PASS"
                        or evidence["artifact"]["digest"] != after["digest"]
                    ):
                        raise IntegrityError("COMMITTED Reconciliation 缺少独立 PASS Evidence")
                    before = _manifest_from_blob(ledger, target["manifest_before_blob"])
                    difference = diff_manifests(before, after)
                    unexpected = [
                        path for path in changed_paths(difference)
                        if not any(scope_contains(scope, path) for scope in target["proposal"]["action"]["paths"])
                    ]
                    if unexpected:
                        raise IntegrityError("Reconciliation 发现原 Action Scope 外修改")
                elif resolution == "NO_EFFECT":
                    if after["digest"] != target["artifact_before"] or payload.get("evidence_id") is not None:
                        raise IntegrityError("NO_EFFECT 必须由 Baseline Manifest 完全相等证明")
                else:
                    raise IntegrityError("Reconciliation Resolution 不合法")
                target.update(
                    state="COMMITTED",
                    outcome=resolution,
                    artifact_after=after["digest"],
                    reconciler_attempt_id=reconciler["attempt_id"],
                    reconciliation_evidence_id=payload.get("evidence_id"),
                )
                projection["expected_artifact"] = after["digest"]
            elif kind == "EVIDENCE_RECORDED":
                work = projection["work"]
                if work is None:
                    raise IntegrityError("Evidence 早于 Work")
                attempt = projection["attempts"].get(payload.get("attempt_id"))
                if not attempt or attempt["state"] not in {"COMMITTED", "NOT_APPLICABLE"}:
                    raise IntegrityError("Evidence 来源 Attempt 尚未解析")
                evidence = validate_evidence(payload, work, payload["artifact"]["digest"])
                source_artifact = attempt.get("artifact_after", attempt.get("artifact_before"))
                if evidence["artifact"]["digest"] != source_artifact:
                    raise IntegrityError("Evidence Artifact 与来源 Attempt 不匹配")
                if evidence["evidence_id"] in projection["evidence"]:
                    raise IntegrityError("Evidence id 重复")
                current = current_artifact_digest is None or evidence["artifact"]["digest"] == current_artifact_digest
                item = {**evidence, "current": current}
                projection["evidence"][evidence["evidence_id"]] = item
                projection["criterion_evidence"][evidence["criterion_id"]] = item
                projection["latest_evidence"] = item
            elif kind == "ROLE_HANDOFF_RECORDED":
                work = projection["work"]
                if work is None:
                    raise IntegrityError("Role Handoff 早于 Work")
                handoff = validate_handoff(payload, work)
                if handoff["handoff_id"] in projection["handoffs"]:
                    raise IntegrityError("Role Handoff id 重复")
                _validate_handoff_order(projection, work, handoff)
                for evidence_id in handoff["evidence_ids"]:
                    evidence = projection["evidence"].get(evidence_id)
                    if not evidence or evidence.get("current") is not True:
                        raise IntegrityError("Role Handoff 引用了不存在或过期的 Evidence")
                current = current_artifact_digest is None or handoff["artifact_digest"] == current_artifact_digest
                item = {**handoff, "current": current}
                projection["handoffs"][handoff["handoff_id"]] = item
                projection["agent_handoffs"][handoff["agent_id"]] = item
                projection["latest_handoff"] = item
            elif kind == "WORK_SUPERSEDED":
                if projection["work"] is None or projection["superseded"] is not None:
                    raise IntegrityError("Work Supersede 位置错误或重复")
                if set(payload) != {"reason", "request", "request_digest"}:
                    raise IntegrityError("Work Supersede Payload 不合法")
                if (
                    not isinstance(payload["reason"], str)
                    or not payload["reason"].strip()
                    or not isinstance(payload["request"], str)
                    or not payload["request"].strip()
                    or payload["request_digest"] != digest_bytes(payload["request"].encode("utf-8"))
                ):
                    raise IntegrityError("Work Supersede Request Binding 不合法")
                unresolved = _unresolved_attempt_ids(projection)
                if unresolved:
                    raise IntegrityError("Work Supersede 时存在未解析副作用")
                projection["superseded"] = payload
            elif kind == "RESULT_REDUCED":
                if payload.get("result") not in {"CONTINUE", "CORRECT", "COMPLETE", "BLOCKED", "WAIT_AUTH", "BUDGET_EXIT"}:
                    raise IntegrityError("已存储的 Result 名称不合法")
            else:
                raise IntegrityError(f"未知 Event type：{kind}")
        except (ValidationError, IntegrityError, KeyError, TypeError, UnicodeError, json.JSONDecodeError) as exc:
            projection["errors"].append(f"Event {event['sequence']}：{exc}")
            break
    projection["source_head"] = None if not events else events[-1]["digest"]
    projection["source_count"] = len(events)
    if projection["work"] is not None and projection["expected_artifact"] is None:
        projection["errors"].append("Work 缺少 ARTIFACT_BASELINED Event")
    in_flight = any(item["state"] in {"DISPATCHED", "UNKNOWN"} for item in projection["attempts"].values())
    if (
        current_artifact_digest is not None
        and projection["expected_artifact"] is not None
        and current_artifact_digest != projection["expected_artifact"]
        and not in_flight
    ):
        projection["errors"].append("检测到 Attempt 之外的 Artifact 修改")
    projection["errors"] = sorted(set(projection["errors"]))
    projection["decision"] = reduce_projection(projection)
    projection["digest"] = digest(projection, ("digest",))
    return projection


def _snapshot(root: Path, *, write: bool) -> tuple[dict[str, Any], dict[str, Any] | None]:
    _, ledger = active_ledger(root)
    events = ledger.events()
    work = None
    for event in events:
        if event["type"] == "WORK_ACCEPTED":
            try:
                work = validate_work(event["payload"], require_confirmation=True)
            except (ValidationError, IntegrityError, KeyError, TypeError):
                pass
            break
    manifest = artifact_for(root, work) if work else None
    projection = replay(
        ledger,
        current_artifact_digest=None if manifest is None else manifest["digest"],
        _events=events,
    )
    if write:
        atomic_write(ledger.run_root / "run-memory.json", canonical_bytes(projection))
    return projection, manifest


def _refresh(ledger: Ledger, artifact_digest: str | None) -> dict[str, Any]:
    projection = replay(ledger, current_artifact_digest=artifact_digest, _events=ledger.events())
    atomic_write(ledger.run_root / "run-memory.json", canonical_bytes(projection))
    return projection


def rebuild(root: Path, *, write: bool = True) -> dict[str, Any]:
    return _snapshot(root, write=write)[0]


def accept_work(root: Path, work: dict[str, Any]) -> dict[str, Any]:
    config, ledger = active_ledger(root)
    validate_work(work, require_confirmation=True)
    if work["profile"] != config["profile"] or work["protocol"] != config["protocol"] or work["harness"] != config["harness"]:
        raise ValidationError("Work 未绑定已选择的 Profile、Protocol 与 Harness")
    if work["artifact"]["environment"] != config["environment"]:
        raise ValidationError("Work Environment 与初始化环境不一致")
    if config["capability"] is not None:
        from .capabilities import routing_plan

        if work["routing"] != routing_plan(
            root,
            risk=work["intake"]["risk"]["level"],
            signals=work["intake"]["signals"],
        ):
            raise ValidationError("Work Routing 与已安装 Capability Workflow 不匹配")
    if work["predecessor"] is not None:
        raise ValidationError("首个 Run 的 Work predecessor 必须为 null")
    verify_work_verifiers(root, work)
    if ledger.events():
        raise IntegrityError("当前 Run 已存在不可变历史")
    accepted = ledger.append("WORK_ACCEPTED", work, expected_head=None)
    manifest = artifact_for(root, work)
    manifest_blob = ledger.put_blob(canonical_bytes(manifest))
    ledger.append(
        "ARTIFACT_BASELINED",
        {"artifact_digest": manifest["digest"], "manifest_blob": manifest_blob},
        expected_head=accepted["digest"],
    )
    return rebuild(root)


def predecessor_binding(ledger: Ledger, projection: dict[str, Any]) -> dict[str, Any]:
    head = ledger.events()[-1] if ledger.events() else None
    work = projection.get("work")
    if head is None or work is None:
        raise IntegrityError("当前 Run 没有可绑定的 Work History")
    return {
        "run_id": ledger.run_id,
        "work_digest": work["digest"],
        "result": projection["decision"]["result"],
        "head_digest": head["digest"],
    }


def start_successor(root: Path, work: dict[str, Any], run_id: str) -> dict[str, Any]:
    """创建绑定当前不可变 Head 的新 Run，并使用 CAS 切换 Current Pointer。"""
    config, current_ledger = active_ledger(root)
    identifier(run_id, "run_id")
    current = rebuild(root, write=False)
    if current["decision"]["result"] not in {"COMPLETE", "BLOCKED", "WAIT_AUTH", "BUDGET_EXIT"}:
        raise ValidationError("只有 Terminal Run 才能创建 Successor")
    if current["decision"]["result"] == "BLOCKED" and current["decision"].get("reason_code") != "WORK_SUPERSEDED":
        raise ValidationError("BLOCKED Run 只有经 WORK_SUPERSEDED 明确关闭后才能创建 Successor")
    validate_work(work, require_confirmation=True)
    old_work = current["work"]
    if old_work is None:
        raise IntegrityError("当前 Run 没有 Work")
    if work["work_id"] != old_work["work_id"] or work["revision"] != old_work["revision"] + 1:
        raise ValidationError("Successor Work 必须保持 work_id 且 Revision 递增一")
    expected_predecessor = predecessor_binding(current_ledger, current)
    if work["predecessor"] != expected_predecessor:
        raise ValidationError("Successor Work predecessor Binding 不匹配")
    if work["profile"] != config["profile"] or work["protocol"] != config["protocol"] or work["harness"] != config["harness"]:
        raise ValidationError("Successor Work 没有绑定当前 Profile、Protocol 与 Harness")
    if work["artifact"]["environment"] != config["environment"]:
        raise ValidationError("Successor Work Environment Binding 不匹配")
    if config["capability"] is not None:
        from .capabilities import routing_plan

        if work["routing"] != routing_plan(
            root,
            risk=work["intake"]["risk"]["level"],
            signals=work["intake"]["signals"],
        ):
            raise ValidationError("Successor Work Routing 与 Capability Workflow 不匹配")
    verify_work_verifiers(root, work)
    successor = Ledger(state_root(root, config), run_id)
    successor.run_root.mkdir(parents=True, exist_ok=False)
    accepted = successor.append("WORK_ACCEPTED", work, expected_head=None)
    manifest = artifact_for(root, work)
    manifest_blob = successor.put_blob(canonical_bytes(manifest))
    successor.append(
        "ARTIFACT_BASELINED",
        {"artifact_digest": manifest["digest"], "manifest_blob": manifest_blob},
        expected_head=accepted["digest"],
    )
    pointer = state_root(root, config) / "current.json"
    lock = state_root(root, config) / ".current.lock"
    with exclusive_lock(lock):
        actual = read_json(pointer)
        if actual != {"run_id": current_ledger.run_id}:
            raise IntegrityError("Current Run Pointer CAS 失败")
        atomic_write(pointer, canonical_bytes({"run_id": run_id}))
    return {
        "status": "SUCCESSOR_ACTIVE",
        "run_id": run_id,
        "predecessor": expected_predecessor,
        "projection": rebuild(root),
    }


def list_runs(root: Path) -> dict[str, Any]:
    config = load_config(root)
    current = current_run_id(root, config)
    runs_root = state_root(root, config) / "runs"
    values = []
    if runs_root.exists():
        for path in sorted(runs_root.iterdir(), key=lambda item: item.name):
            if not path.is_dir():
                continue
            ledger = Ledger(state_root(root, config), path.name)
            try:
                projection = replay(ledger)
                values.append(
                    {
                        "run_id": path.name,
                        "current": path.name == current,
                        "work_revision": None if projection["work"] is None else projection["work"]["revision"],
                        "result": projection["decision"]["result"],
                        "head_digest": projection["source_head"],
                    }
                )
            except IntegrityError as exc:
                values.append({"run_id": path.name, "current": path.name == current, "result": "BLOCKED", "error": str(exc)})
    return {"current_run_id": current, "runs": values}


def verify_work_verifiers(root: Path, work: dict[str, Any]) -> None:
    from .paths import resolve_inside

    for criterion in work["acceptance_criteria"]:
        verifier = criterion["verifier"]
        for file in verifier["files"]:
            target = resolve_inside(root.resolve(), file["path"])
            if target.is_symlink() or not target.is_file() or digest_bytes(target.read_bytes()) != file["digest"]:
                raise ValidationError(f"Verifier File Binding 不匹配：{file['path']}")


def begin_attempt(root: Path, proposal: dict[str, Any]) -> dict[str, Any]:
    validate_proposal(proposal)
    _, ledger = active_ledger(root)
    projection, manifest = _snapshot(root, write=False)
    work = projection["work"]
    if work is None or projection["errors"]:
        raise IntegrityError("没有合法 Work，不能启动 Attempt")
    decision = projection["decision"]["result"]
    reconciliation = proposal.get("reconciliation")
    if decision == "BLOCKED":
        if reconciliation is None:
            raise ValidationError("BLOCKED Run 只能启动 Reconciliation Attempt")
        target = projection["attempts"].get(reconciliation["target_attempt_id"])
        if not target or target["state"] != "UNKNOWN":
            raise ValidationError("Reconciliation Target 不是 UNKNOWN Attempt")
        if proposal["action"]["paths"] != target["proposal"]["action"]["paths"]:
            raise ValidationError("Reconciliation Scope 与原 Attempt 不一致")
    elif reconciliation is not None:
        raise ValidationError("只有存在 UNKNOWN 时才能启动 Reconciliation Attempt")
    if decision in {"COMPLETE", "WAIT_AUTH", "BUDGET_EXIT"}:
        raise ValidationError(f"Run 不能从 {projection['decision']['result']} 继续推进")
    if proposal["attempt_id"] in projection["attempts"]:
        raise ValidationError("Attempt id 已存在")
    fingerprint = digest({"strategy": proposal["strategy"], "inputs": proposal["relevant_inputs"]})
    from .paths import resolve_inside

    for relevant in proposal["relevant_inputs"]:
        target = resolve_inside(root.resolve(), relevant["path"])
        if target.is_symlink() or not target.is_file() or digest_bytes(target.read_bytes()) != relevant["digest"]:
            raise ValidationError(f"Relevant Input digest 不匹配：{relevant['path']}")
    for attempt in projection["attempts"].values():
        if attempt.get("strategy_fingerprint") == fingerprint:
            newer = projection.get("latest_evidence")
            if newer is None or newer.get("attempt_id") == attempt["attempt_id"]:
                raise ValidationError("相同 Strategy 与 Input 没有更新的 Evidence")
    if not action_authorized(work, proposal["action"]):
        event = ledger.append(
            "AUTHORIZATION_REQUIRED",
            {"attempt_id": proposal["attempt_id"], "action": proposal["action"]},
            expected_head=projection["source_head"],
        )
        projection = rebuild(root)
        return {"event": event, "decision": projection["decision"]}
    if any(
        projection["budgets_used"].get(name, 0) + proposal["budget_charge"].get(name, 0) > maximum
        for name, maximum in work["budgets"].items()
    ):
        event = ledger.append(
            "BUDGET_EXHAUSTED",
            {"attempt_id": proposal["attempt_id"], "budget_charge": proposal["budget_charge"]},
            expected_head=projection["source_head"],
        )
        return {"event": event, "decision": rebuild(root)["decision"]}
    if manifest is None:
        raise IntegrityError("没有可审计的 Artifact Manifest")
    manifest_blob = ledger.put_blob(canonical_bytes(manifest))
    event = ledger.append(
        "ATTEMPT_PREPARED",
        {
            "attempt_id": proposal["attempt_id"],
            "sequence": len(projection["attempt_order"]) + 1,
            "work_digest": work["digest"],
            "strategy_fingerprint": fingerprint,
            "artifact_before": manifest["digest"],
            "manifest_before_blob": manifest_blob,
            "proposal": proposal,
        },
        expected_head=projection["source_head"],
    )
    return {"event": event, "decision": _refresh(ledger, manifest["digest"])["decision"]}


def dispatch_attempt(root: Path, attempt_id: str) -> dict[str, Any]:
    _, ledger = active_ledger(root)
    projection, current = _snapshot(root, write=False)
    attempt = projection["attempts"].get(attempt_id)
    if not attempt or attempt["state"] != "PREPARED":
        raise ValidationError("Attempt 不处于 PREPARED 状态")
    work = projection["work"]
    if current is None:
        raise IntegrityError("没有可审计的 Artifact Manifest")
    if current["digest"] != attempt["artifact_before"]:
        event = ledger.append(
            "ATTEMPT_UNKNOWN",
            {"attempt_id": attempt_id, "reason": "Artifact 在 Dispatch 前已改变"},
            expected_head=projection["source_head"],
        )
        return {"event": event, "decision": _refresh(ledger, current["digest"])["decision"]}
    event = ledger.append("ATTEMPT_DISPATCHED", {"attempt_id": attempt_id}, expected_head=projection["source_head"])
    return {"event": event, "decision": _refresh(ledger, current["digest"])["decision"]}


def observe_attempt(root: Path, attempt_id: str, receipt: dict[str, Any]) -> dict[str, Any]:
    _, ledger = active_ledger(root)
    projection, after = _snapshot(root, write=False)
    attempt = projection["attempts"].get(attempt_id)
    if not attempt or attempt["state"] != "DISPATCHED":
        raise ValidationError("Attempt 不处于 DISPATCHED 状态")
    work = projection["work"]
    before = _manifest_from_blob(ledger, attempt["manifest_before_blob"])
    if after is None:
        raise IntegrityError("没有可审计的 Artifact Manifest")
    difference = diff_manifests(before, after)
    changed = changed_paths(difference)
    action_paths = attempt["proposal"]["action"]["paths"]
    unexpected = sorted(path for path in changed if not any(scope_contains(scope, path) for scope in action_paths))
    receipt_blob = ledger.put_blob(canonical_bytes(receipt))
    after_blob = ledger.put_blob(canonical_bytes(after))
    if unexpected:
        event = ledger.append(
            "ATTEMPT_UNKNOWN",
            {"attempt_id": attempt_id, "reason": "存在未声明的 Artifact 修改", "unexpected_paths": unexpected, "receipt_blob": receipt_blob},
            expected_head=projection["source_head"],
        )
        return {"event": event, "decision": _refresh(ledger, after["digest"])["decision"]}
    observed = ledger.append(
        "ATTEMPT_OBSERVED",
        {
            "attempt_id": attempt_id,
            "artifact_after": after["digest"],
            "manifest_after_blob": after_blob,
            "diff": difference,
            "receipt_blob": receipt_blob,
            "receipt_digest": digest(receipt),
        },
        expected_head=projection["source_head"],
    )
    committed = ledger.append(
        "ATTEMPT_COMMITTED",
        {"attempt_id": attempt_id, "artifact_after": after["digest"], "receipt_digest": digest(receipt)},
        expected_head=observed["digest"],
    )
    return {"events": [observed, committed], "decision": _refresh(ledger, after["digest"])["decision"]}


def mark_attempt_unknown(root: Path, attempt_id: str, reason: str) -> dict[str, Any]:
    """在 Adapter 报告 Crash、Timeout 或 Receipt 丢失后关闭执行窗口。"""
    if not isinstance(reason, str) or not reason.strip():
        raise ValidationError("UNKNOWN Reason 不能为空")
    _, ledger = active_ledger(root)
    projection = rebuild(root, write=False)
    attempt = projection["attempts"].get(attempt_id)
    if not attempt or attempt["state"] not in {"DISPATCHED", "OBSERVED"}:
        raise ValidationError("只有 DISPATCHED 或 OBSERVED Attempt 可以转为 UNKNOWN")
    event = ledger.append(
        "ATTEMPT_UNKNOWN",
        {"attempt_id": attempt_id, "reason": reason.strip()},
        expected_head=projection["source_head"],
    )
    return {"event": event, "decision": rebuild(root)["decision"]}


def resolve_attempt(
    root: Path,
    target_attempt_id: str,
    reconciler_attempt_id: str,
    resolution: str,
    evidence_id: str | None = None,
) -> dict[str, Any]:
    """使用独立 Reconciliation Attempt 追加 UNKNOWN 的终态解析。"""
    if resolution not in {"COMMITTED", "NO_EFFECT"}:
        raise ValidationError("Resolution 只能是 COMMITTED 或 NO_EFFECT")
    _, ledger = active_ledger(root)
    projection = rebuild(root, write=False)
    target = projection["attempts"].get(target_attempt_id)
    reconciler = projection["attempts"].get(reconciler_attempt_id)
    if not target or target["state"] != "UNKNOWN":
        raise ValidationError("Target 不是 UNKNOWN Attempt")
    if not reconciler or reconciler["state"] != "NOT_APPLICABLE":
        raise ValidationError("Reconciler 不是已完成的只读 Attempt")
    binding = reconciler["proposal"].get("reconciliation")
    if not binding or binding["target_attempt_id"] != target_attempt_id:
        raise ValidationError("Reconciler 未绑定 Target")
    if resolution == "COMMITTED":
        evidence = projection["evidence"].get(evidence_id or "")
        if (
            not evidence
            or evidence["attempt_id"] != reconciler_attempt_id
            or evidence["status"] != "PASS"
            or evidence.get("current") is not True
        ):
            raise ValidationError("COMMITTED Resolution 需要 Reconciler 的当前 PASS Evidence")
    elif evidence_id is not None:
        raise ValidationError("NO_EFFECT Resolution 不接受 Evidence ID")
    work = projection["work"]
    manifest = artifact_for(root, work)
    before = _manifest_from_blob(ledger, target["manifest_before_blob"])
    if resolution == "COMMITTED":
        difference = diff_manifests(before, manifest)
        unexpected = [
            path for path in changed_paths(difference)
            if not any(scope_contains(scope, path) for scope in target["proposal"]["action"]["paths"])
        ]
        if unexpected:
            raise ValidationError("Reconciliation 发现原 Action Scope 外修改，状态仍为 BLOCKED")
    elif manifest["digest"] != target["artifact_before"]:
        raise ValidationError("NO_EFFECT 无法成立：当前 Artifact 与原 Baseline 不同")
    manifest_blob = ledger.put_blob(canonical_bytes(manifest))
    event = ledger.append(
        "ATTEMPT_RECONCILED",
        {
            "target_attempt_id": target_attempt_id,
            "reconciler_attempt_id": reconciler_attempt_id,
            "resolution": resolution,
            "evidence_id": evidence_id,
            "artifact_after": manifest["digest"],
            "manifest_after_blob": manifest_blob,
        },
        expected_head=projection["source_head"],
    )
    return {"event": event, "decision": rebuild(root)["decision"]}


def add_evidence(root: Path, evidence: dict[str, Any]) -> dict[str, Any]:
    _, ledger = active_ledger(root)
    projection = rebuild(root, write=False)
    work = projection["work"]
    if work is None:
        raise IntegrityError("没有 Work，不能添加 Evidence")
    artifact = artifact_for(root, work)
    validate_evidence(evidence, work, artifact["digest"])
    attempt = projection["attempts"].get(evidence["attempt_id"])
    if not attempt or attempt["state"] not in {"COMMITTED", "NOT_APPLICABLE"}:
        raise ValidationError("Evidence 来源 Attempt 尚未解析")
    source_artifact = attempt.get("artifact_after", attempt.get("artifact_before"))
    if evidence["artifact"]["digest"] != source_artifact:
        raise ValidationError("Evidence Artifact 与来源 Attempt 不匹配")
    event = ledger.append("EVIDENCE_RECORDED", evidence, expected_head=projection["source_head"])
    return {"event": event, "decision": rebuild(root)["decision"]}


def handoff_template(
    root: Path,
    *,
    handoff_id: str,
    agent_id: str,
    to_agent_id: str,
    phase: str,
    status: str,
    summary: str,
    evidence_ids: list[str],
) -> dict[str, Any]:
    projection = rebuild(root, write=False)
    work = projection["work"]
    if work is None or projection["errors"] or projection.get("superseded") is not None:
        raise IntegrityError("没有可交接的 Active Work")
    if unresolved := _unresolved_attempt_ids(projection):
        raise ValidationError("存在未解析 Attempt，不能生成 Role Handoff：" + ", ".join(unresolved))
    artifact = artifact_for(root, work)
    value = {
        "schema_version": "yuan.handoff/v1",
        "handoff_id": handoff_id,
        "work": {"id": work["work_id"], "revision": work["revision"], "digest": work["digest"]},
        "agent_id": agent_id,
        "to_agent_id": to_agent_id,
        "phase": phase,
        "status": status,
        "summary": summary,
        "artifact_digest": artifact["digest"],
        "evidence_ids": evidence_ids,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    value["digest"] = digest(value, ("digest",))
    return validate_handoff(value, work)


def _validate_handoff_order(projection: dict[str, Any], work: dict[str, Any], handoff: dict[str, Any]) -> None:
    order = work["routing"]["handoff_agents"]
    for agent_id in order[:order.index(handoff["agent_id"])]:
        prior = projection["agent_handoffs"].get(agent_id)
        if not prior or prior["status"] != "READY" or (
            agent_id in work["routing"]["artifact_review_agents"] and prior.get("current") is not True
        ):
            raise ValidationError(f"前序 Agent 尚未 READY 或 Handoff 已过期：{agent_id}")


def _unresolved_attempt_ids(projection: dict[str, Any]) -> list[str]:
    return sorted(
        attempt_id for attempt_id, attempt in projection["attempts"].items()
        if attempt["state"] in {"PREPARED", "DISPATCHED", "OBSERVED", "UNKNOWN"}
    )


def record_handoff(root: Path, handoff: dict[str, Any]) -> dict[str, Any]:
    _, ledger = active_ledger(root)
    projection = rebuild(root, write=False)
    work = projection["work"]
    if work is None or projection["errors"] or projection.get("superseded") is not None:
        raise IntegrityError("没有可记录交接的 Active Work")
    if unresolved := _unresolved_attempt_ids(projection):
        raise ValidationError("存在未解析 Attempt，不能记录 Role Handoff：" + ", ".join(unresolved))
    validate_handoff(handoff, work)
    if handoff["handoff_id"] in projection["handoffs"]:
        raise ValidationError("Role Handoff id 已存在")
    _validate_handoff_order(projection, work, handoff)
    artifact = artifact_for(root, work)
    if handoff["artifact_digest"] != artifact["digest"]:
        raise ValidationError("Role Handoff Artifact Binding 已过期")
    for evidence_id in handoff["evidence_ids"]:
        evidence = projection["evidence"].get(evidence_id)
        if not evidence or evidence.get("current") is not True:
            raise ValidationError("Role Handoff 引用了不存在或过期的 Evidence")
    event = ledger.append("ROLE_HANDOFF_RECORDED", handoff, expected_head=projection["source_head"])
    return {"event": event, "decision": rebuild(root)["decision"]}


def supersede_work(root: Path, *, reason: str, request: str) -> dict[str, Any]:
    """由显式用户变更关闭非终态 Work；历史保留并可创建 Successor。"""

    if not isinstance(reason, str) or not reason.strip() or not isinstance(request, str) or not request.strip():
        raise ValidationError("Supersede reason 与新 request 不能为空")
    _, ledger = active_ledger(root)
    projection = rebuild(root, write=False)
    if projection["work"] is None or projection["errors"] or projection.get("superseded") is not None:
        raise IntegrityError("当前没有可 Supersede 的合法 Work")
    if projection["decision"]["result"] not in {"CONTINUE", "CORRECT"}:
        raise ValidationError("只有 CONTINUE 或 CORRECT Work 需要显式 Supersede")
    unresolved = _unresolved_attempt_ids(projection)
    if unresolved:
        raise ValidationError("存在未解析 Attempt，不能 Supersede：" + ", ".join(sorted(unresolved)))
    payload = {
        "reason": reason.strip(),
        "request": request.strip(),
        "request_digest": digest_bytes(request.strip().encode("utf-8")),
    }
    event = ledger.append("WORK_SUPERSEDED", payload, expected_head=projection["source_head"])
    return {"event": event, "decision": rebuild(root)["decision"], "successor_required": True}


_VERIFIER_WRAPPER = r'''
import os
import runpy
import sys

def deny(event, args):
    denied = (
        "subprocess.", "socket.", "ctypes.", "winreg.",
        "os.remove", "os.rename", "os.replace", "os.rmdir", "os.mkdir",
        "os.system", "os.spawn", "shutil.",
    )
    if event == "open":
        mode = args[1] if len(args) > 1 else "r"
        flags = args[2] if len(args) > 2 else 0
        if isinstance(mode, str) and any(flag in mode for flag in "wax+"):
            raise PermissionError("Verifier 写入被拒绝")
        write_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
        if isinstance(flags, int) and flags & write_flags:
            raise PermissionError("Verifier 写入被拒绝")
    if event.startswith(denied):
        raise PermissionError("Verifier 副作用被拒绝：" + event)

sys.addaudithook(deny)
script, artifact = sys.argv[1], sys.argv[2]
sys.argv = [script, artifact]
runpy.run_path(script, run_name="__main__")
'''


def run_verifier(root: Path, criterion_id: str, attempt_id: str) -> dict[str, Any]:
    config, _ = active_ledger(root)
    projection = rebuild(root, write=False)
    work = projection["work"]
    if work is None or projection["errors"]:
        raise IntegrityError("不能验证不合法的 Run")
    criteria = [item for item in work["acceptance_criteria"] if item["id"] == criterion_id]
    if len(criteria) != 1:
        raise ValidationError("Criterion 未被 Work 绑定")
    attempt = projection["attempts"].get(attempt_id)
    if not attempt or attempt["state"] not in {"COMMITTED", "NOT_APPLICABLE"}:
        raise ValidationError("Verifier 来源 Attempt 尚未解析")
    verifier = criteria[0]["verifier"]
    if verifier.get("kind") != "python-script":
        raise ValidationError("Reference Kernel 仅支持 python-script Verifier")
    entrypoint = verifier.get("entrypoint")
    timeout = verifier.get("timeout_seconds")
    if not isinstance(entrypoint, str) or not isinstance(timeout, int) or timeout <= 0 or timeout > 600:
        raise ValidationError("Verifier Invocation Profile 不合法")
    from .paths import resolve_inside

    for file in verifier["files"]:
        target = resolve_inside(root.resolve(), file["path"])
        if target.is_symlink() or not target.is_file() or digest_bytes(target.read_bytes()) != file["digest"]:
            raise IntegrityError("Verifier Closure 与 Work Binding 不匹配")
    closure = {"kind": verifier["kind"], "entrypoint": entrypoint, "files": verifier["files"]}
    if digest(closure) != verifier["digest"]:
        raise IntegrityError("Verifier Closure digest 不匹配")
    script = resolve_inside(root.resolve(), entrypoint)
    before = artifact_for(root, work)
    source_artifact = attempt.get("artifact_after", attempt.get("artifact_before"))
    if before["digest"] != source_artifact:
        raise IntegrityError("当前 Artifact 与 Verifier 来源 Attempt 不一致")
    argv = [sys.executable, "-I", "-B", "-c", _VERIFIER_WRAPPER, str(script), str(root.resolve())]
    try:
        completed = subprocess.run(
            argv,
            cwd=root.resolve(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise IntegrityError("Verifier 执行超时") from exc
    after = artifact_for(root, work)
    if after["digest"] != before["digest"]:
        raise IntegrityError("Verifier 修改了 Artifact")
    try:
        report = json.loads(completed.stdout.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError("Verifier stdout 不是单个 JSON Object") from exc
    if not isinstance(report, dict) or set(report) != {"status", "assertions"}:
        raise ValidationError("Verifier Report 结构不合法")
    if report["status"] == "PASS" and completed.returncode != 0:
        raise ValidationError("Verifier PASS 与其 Exit Code 矛盾")
    receipt = {
        "kind": "python-script",
        "argv_profile": ["pinned-python", "-I", "-B", "audit-read-only", entrypoint],
        "exit_code": completed.returncode,
        "stdout": digest_bytes(completed.stdout),
        "stderr": digest_bytes(completed.stderr),
        "tool": digest({"wrapper": _VERIFIER_WRAPPER, "python": config["environment"]}),
    }
    evidence = {
        "schema_version": "yuan.evidence/v1",
        "evidence_id": f"EVD-{criterion_id}-{attempt_id}-{receipt['stdout'][:12]}",
        "work": {"id": work["work_id"], "revision": work["revision"], "digest": work["digest"]},
        "attempt_id": attempt_id,
        "criterion_id": criterion_id,
        "artifact": {"scope": work["artifact"]["root"], "digest": before["digest"]},
        "environment": config["environment"],
        "harness": work["harness"],
        "verifier": verifier,
        "status": report["status"],
        "assertions": report["assertions"],
        "receipt": {key: receipt[key] for key in ("tool", "stdout", "stderr")},
        "independence": criteria[0]["independence"],
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    from .validate import with_digest

    evidence = with_digest(evidence)
    result = add_evidence(root, evidence)
    result["verifier_receipt"] = receipt
    return result


def record_reduction(root: Path) -> dict[str, Any]:
    _, ledger = active_ledger(root)
    projection = rebuild(root)
    event = ledger.append(
        "RESULT_REDUCED",
        {"result": projection["decision"]["result"], "projection_digest": projection["digest"]},
        expected_head=projection["source_head"],
    )
    final = rebuild(root)
    return {"event": event, "decision": final["decision"], "projection_digest": final["digest"]}
