"""Yuan Capability Profile 的发现、打包、安装与运行时路由。"""

from __future__ import annotations

import json
import re
from importlib import resources
from pathlib import Path, PurePosixPath
from typing import Any

from .canonical import digest, digest_bytes, verify_digest
from .errors import IntegrityError, ValidationError
from .paths import resolve_inside
from .workflow import RISK_LEVELS, validate_routing


DEFAULT_PROFILE = "vibe-coding"
PROFILES_ROOT = "profiles"
MANIFEST_PATH = ".yuan/extensions/manifest.json"
CUSTOM_ROOT = ".yuan/extensions/custom"
PROFILE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CATALOG_KINDS = ("rules", "agents", "skills")


def _profiles_root() -> Any:
    return resources.files("yuan").joinpath(PROFILES_ROOT)


def available_profiles() -> tuple[str, ...]:
    values = []
    for child in sorted(_profiles_root().iterdir(), key=lambda item: item.name):
        if child.is_dir() and PROFILE_ID.fullmatch(child.name) and child.joinpath("profile.json").is_file():
            values.append(child.name)
    if not values:
        raise IntegrityError("发行包没有 Capability Profile")
    return tuple(values)


def _validate_catalog_entry(value: Any, kind: str) -> dict[str, Any]:
    required = {"id", "path", "description", "use_when"}
    if not isinstance(value, dict) or set(value) != required:
        raise IntegrityError(f"Capability {kind} Catalog Entry 字段不合法")
    if not isinstance(value["id"], str) or not PROFILE_ID.fullmatch(value["id"]):
        raise IntegrityError(f"Capability {kind} id 不合法")
    path = PurePosixPath(value["path"])
    if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != kind:
        raise IntegrityError(f"Capability {kind} path 不合法：{value['path']}")
    if not isinstance(value["description"], str) or not value["description"].strip():
        raise IntegrityError(f"Capability {kind} description 不能为空")
    if not isinstance(value["use_when"], list) or not value["use_when"] or any(
        not isinstance(item, str) or not item.strip() for item in value["use_when"]
    ):
        raise IntegrityError(f"Capability {kind} use_when 不合法")
    return value


def _validate_workflow(value: Any, agent_ids: set[str], skill_ids: set[str]) -> dict[str, Any]:
    required = {
        "schema_version", "base", "risk_routes", "signal_routes",
        "agent_skill_routes", "artifact_review_agents",
    }
    if not isinstance(value, dict) or set(value) != required or value["schema_version"] != "yuan.workflow/v1":
        raise IntegrityError("Capability Workflow 字段或版本不合法")

    def route(item: Any, label: str) -> dict[str, Any]:
        if not isinstance(item, dict) or set(item) != {"agents", "skills"}:
            raise IntegrityError(f"{label} Route 字段不合法")
        agents = item["agents"]
        skills = item["skills"]
        if (
            not isinstance(agents, list)
            or not isinstance(skills, list)
            or len(agents) != len(set(agents))
            or len(skills) != len(set(skills))
            or not set(agents) <= agent_ids
            or not set(skills) <= skill_ids
        ):
            raise IntegrityError(f"{label} Route 引用了未知或重复能力")
        return item

    route(value["base"], "Base")
    risks = value["risk_routes"]
    if not isinstance(risks, dict) or set(risks) != RISK_LEVELS:
        raise IntegrityError("Workflow Risk Route 集合不完整")
    for risk, item in risks.items():
        route(item, risk)
    signals = value["signal_routes"]
    if not isinstance(signals, dict) or not signals:
        raise IntegrityError("Workflow Signal Route 不能为空")
    for signal, item in signals.items():
        if not PROFILE_ID.fullmatch(signal):
            raise IntegrityError(f"Workflow Signal id 不合法：{signal}")
        route(item, f"Signal {signal}")
    assignments = value["agent_skill_routes"]
    if not isinstance(assignments, dict) or set(assignments) != agent_ids:
        raise IntegrityError("Workflow Agent Skill Route 必须覆盖全部 Agent")
    for agent_id, assigned_skills in assignments.items():
        if (
            not isinstance(assigned_skills, list)
            or len(assigned_skills) != len(set(assigned_skills))
            or not set(assigned_skills) <= skill_ids
        ):
            raise IntegrityError(f"Workflow Agent Skill Route 不合法：{agent_id}")
    reviewers = value["artifact_review_agents"]
    if not isinstance(reviewers, list) or len(reviewers) != len(set(reviewers)) or not set(reviewers) <= agent_ids:
        raise IntegrityError("Workflow Artifact Reviewer 不合法")
    return value


def profile_descriptor(profile_id: str = DEFAULT_PROFILE) -> dict[str, Any]:
    if not PROFILE_ID.fullmatch(profile_id) or profile_id not in available_profiles():
        raise ValidationError(f"未知 Capability Profile：{profile_id}")
    root = _profiles_root().joinpath(profile_id)
    try:
        value = json.loads(root.joinpath("profile.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise IntegrityError(f"Capability Profile Descriptor 不合法：{profile_id}") from exc
    required = {
        "schema_version", "profile_id", "profile_version", "description",
        "required_rules", "agents", "skills", "workflow",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise IntegrityError("Capability Profile Descriptor 字段不合法")
    if value["schema_version"] != "yuan.capability-source/v1" or value["profile_id"] != profile_id:
        raise IntegrityError("Capability Profile Descriptor Identity 不匹配")
    if not isinstance(value["profile_version"], str) or not value["profile_version"].strip():
        raise IntegrityError("Capability Profile Version 不能为空")
    if not isinstance(value["description"], str) or not value["description"].strip():
        raise IntegrityError("Capability Profile Description 不能为空")
    agents = [_validate_catalog_entry(item, "agents") for item in value["agents"]]
    skills = [_validate_catalog_entry(item, "skills") for item in value["skills"]]
    if len({item["id"] for item in agents}) != len(agents) or len({item["id"] for item in skills}) != len(skills):
        raise IntegrityError("Capability Catalog id 重复")
    _validate_workflow(value["workflow"], {item["id"] for item in agents}, {item["id"] for item in skills})
    required_rules = value["required_rules"]
    if not isinstance(required_rules, list) or not required_rules:
        raise IntegrityError("Capability Profile 必须声明 Required Rules")
    for relative in required_rules:
        if not isinstance(relative, str):
            raise IntegrityError("Required Rule path 不合法")
        path = PurePosixPath(relative)
        if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "rules":
            raise IntegrityError(f"Required Rule path 不合法：{relative}")
    referenced = set(required_rules) | {item["path"] for item in agents + skills}
    for relative in referenced:
        if not root.joinpath(*PurePosixPath(relative).parts).is_file():
            raise IntegrityError(f"Capability Catalog 引用不存在：{relative}")
    resource_map = {path: payload for path, payload in _resource_files(profile_id)}
    actual_rules = {path for path in resource_map if path.startswith("rules/") and path.endswith(".md")}
    actual_agents = {path for path in resource_map if path.startswith("agents/") and path.endswith(".md")}
    actual_skills = {path for path in resource_map if path.startswith("skills/") and path.endswith("/SKILL.md")}
    if actual_rules != set(required_rules):
        raise IntegrityError("Capability Rules 必须全部进入 Required Rules Catalog")
    if actual_agents != {item["path"] for item in agents}:
        raise IntegrityError("Capability Agents Catalog 与文件集合不一致")
    if actual_skills != {item["path"] for item in skills}:
        raise IntegrityError("Capability Skills Catalog 与文件集合不一致")
    for item in skills:
        text = resource_map[item["path"]].decode("utf-8")
        frontmatter = text.split("---", 2)
        if len(frontmatter) != 3 or f"name: {item['id']}" not in frontmatter[1] or "description:" not in frontmatter[1]:
            raise IntegrityError(f"Skill Frontmatter 与 Catalog 不匹配：{item['id']}")
    return value


def _resource_files(profile_id: str) -> list[tuple[str, bytes]]:
    root = _profiles_root().joinpath(profile_id)
    files: list[tuple[str, bytes]] = []

    def visit(node: Any, relative: PurePosixPath) -> None:
        for child in sorted(node.iterdir(), key=lambda item: item.name):
            child_relative = relative / child.name
            if child.is_dir():
                visit(child, child_relative)
            elif not child.name.endswith(".pyc"):
                files.append((child_relative.as_posix(), child.read_bytes()))

    visit(root, PurePosixPath())
    if not files:
        raise IntegrityError(f"Capability Profile 为空：{profile_id}")
    return files


def capability_payloads(profile_id: str = DEFAULT_PROFILE) -> list[tuple[str, bytes]]:
    """返回选定 Profile 的项目相对路径与固定内容。"""

    profile_descriptor(profile_id)
    install_root = PurePosixPath(".yuan/extensions") / profile_id
    return [((install_root / relative).as_posix(), payload) for relative, payload in _resource_files(profile_id)]


def capability_manifest(profile_id: str = DEFAULT_PROFILE) -> dict[str, Any]:
    descriptor = profile_descriptor(profile_id)
    prefix_parts = len(PurePosixPath(".yuan/extensions").parts) + 1
    files = []
    for path, payload in capability_payloads(profile_id):
        relative = PurePosixPath(path).parts[prefix_parts:]
        kind = relative[0] if relative and relative[0] in CATALOG_KINDS else "profile"
        files.append({"path": path, "digest": digest_bytes(payload), "bytes": len(payload), "kind": kind})
    value = {
        "schema_version": "yuan.capability-profile/v2",
        "profile_id": profile_id,
        "profile_version": descriptor["profile_version"],
        "description": descriptor["description"],
        "boundary": "advisory-and-evidence-only",
        "required_rules": [f".yuan/extensions/{profile_id}/{path}" for path in descriptor["required_rules"]],
        "agents": [
            {**item, "path": f".yuan/extensions/{profile_id}/{item['path']}"}
            for item in descriptor["agents"]
        ],
        "skills": [
            {**item, "path": f".yuan/extensions/{profile_id}/{item['path']}"}
            for item in descriptor["skills"]
        ],
        "workflow": descriptor["workflow"],
        "files": files,
        "custom_root": CUSTOM_ROOT,
    }
    value["digest"] = digest(value, ("digest",))
    return value


def capability_paths(profile_id: str = DEFAULT_PROFILE) -> tuple[str, ...]:
    return tuple(path for path, _ in capability_payloads(profile_id)) + (MANIFEST_PATH,)


def read_installed_manifest(root: Path) -> dict[str, Any]:
    path = root.resolve() / MANIFEST_PATH
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise IntegrityError("Capability Manifest 不存在或不是合法 JSON") from exc
    if (
        not isinstance(value, dict)
        or value.get("schema_version") not in {"yuan.capability-profile/v1", "yuan.capability-profile/v2"}
        or not verify_digest(value)
    ):
        raise IntegrityError("Capability Manifest Digest 或版本不合法")
    for item in value.get("files", []):
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise IntegrityError("Capability Manifest File Entry 不合法")
        target = resolve_inside(root.resolve(), item["path"])
        if not target.is_file() or target.is_symlink():
            raise IntegrityError(f"Capability 文件不存在或不安全：{item['path']}")
        payload = target.read_bytes()
        if digest_bytes(payload) != item.get("digest") or len(payload) != item.get("bytes"):
            raise IntegrityError(f"Capability 文件 Digest 或 Size 不匹配：{item['path']}")
    return value


def installed_catalog(root: Path) -> dict[str, Any]:
    manifest = read_installed_manifest(root)
    if manifest["schema_version"] == "yuan.capability-profile/v1":
        base = {
            "status": "PASS",
            "profile_id": manifest["profile_id"],
            "profile_version": manifest["profile_version"],
            "required_rules": [],
            "agents": [],
            "skills": [],
            "workflow": None,
            "legacy_catalog": True,
        }
    else:
        base = {
            "status": "PASS",
            "profile_id": manifest["profile_id"],
            "profile_version": manifest["profile_version"],
            "description": manifest["description"],
            "required_rules": manifest["required_rules"],
            "agents": manifest["agents"],
            "skills": manifest["skills"],
            "workflow": manifest.get("workflow"),
            "legacy_catalog": False,
        }
    custom, errors = _custom_catalog(root)
    base["custom_rules"] = custom["rules"]
    base["agents"] = base["agents"] + custom["agents"]
    base["skills"] = base["skills"] + custom["skills"]
    base["custom_errors"] = errors
    return base


def _custom_catalog(root: Path) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, str]]]:
    custom_root = root.resolve() / CUSTOM_ROOT
    catalog: dict[str, list[dict[str, Any]]] = {kind: [] for kind in CATALOG_KINDS}
    errors: list[dict[str, str]] = []
    if not custom_root.is_dir():
        return catalog, errors
    for directory in sorted(custom_root.iterdir(), key=lambda item: item.name):
        if not directory.is_dir() or not PROFILE_ID.fullmatch(directory.name):
            continue
        try:
            descriptor = _read_custom_descriptor(directory)
            for kind in CATALOG_KINDS:
                for item in descriptor[kind]:
                    catalog[kind].append({
                        **item,
                        "id": f"{descriptor['extension_id']}:{item['id']}",
                        "path": (Path(CUSTOM_ROOT) / directory.name / item["path"]).as_posix(),
                        "source": "custom",
                    })
        except (IntegrityError, ValidationError) as exc:
            errors.append({"extension_id": directory.name, "error": str(exc)})
    return catalog, errors


def _read_custom_descriptor(directory: Path) -> dict[str, Any]:
    try:
        value = json.loads((directory / "extension.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise IntegrityError("Custom Extension Descriptor 不存在或不合法") from exc
    required = {"schema_version", "extension_id", "description", "rules", "agents", "skills", "digest"}
    if not isinstance(value, dict) or set(value) != required or not verify_digest(value):
        raise IntegrityError("Custom Extension Descriptor 字段或 Digest 不合法")
    if value["schema_version"] != "yuan.custom-extension/v1" or value["extension_id"] != directory.name:
        raise IntegrityError("Custom Extension Identity 不匹配")
    if not isinstance(value["description"], str) or not value["description"].strip():
        raise IntegrityError("Custom Extension Description 不能为空")
    for kind in CATALOG_KINDS:
        entries = value[kind]
        if not isinstance(entries, list):
            raise IntegrityError(f"Custom Extension {kind} 必须是 List")
        seen = set()
        for item in entries:
            expected = {"id", "path", "description", "use_when", "digest"}
            if not isinstance(item, dict) or set(item) != expected:
                raise IntegrityError(f"Custom Extension {kind} Entry 不合法")
            plain = {key: item[key] for key in ("id", "path", "description", "use_when")}
            _validate_catalog_entry(plain, kind)
            if item["id"] in seen:
                raise IntegrityError(f"Custom Extension {kind} id 重复")
            seen.add(item["id"])
            target = resolve_inside(directory.resolve(), item["path"])
            if target.is_symlink() or not target.is_file() or digest_bytes(target.read_bytes()) != item["digest"]:
                raise IntegrityError(f"Custom Extension 文件 Binding 不匹配：{item['path']}")
    return value


def bind_custom_descriptor(directory: Path) -> dict[str, Any]:
    """为 Custom Extension 草稿计算逐文件与 Descriptor Digest。"""

    directory = directory.resolve()
    try:
        value = json.loads((directory / "extension.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError("Custom Extension 草稿 extension.json 不合法") from exc
    expected = {"schema_version", "extension_id", "description", "rules", "agents", "skills"}
    if not isinstance(value, dict) or set(value) - {"digest"} != expected:
        raise ValidationError("Custom Extension 草稿字段不合法")
    value.pop("digest", None)
    if (
        value["schema_version"] != "yuan.custom-extension/v1"
        or value["extension_id"] != directory.name
        or not PROFILE_ID.fullmatch(value["extension_id"])
    ):
        raise ValidationError("Custom Extension 草稿 Identity 不匹配")
    if not isinstance(value["description"], str) or not value["description"].strip():
        raise ValidationError("Custom Extension Description 不能为空")
    for kind in CATALOG_KINDS:
        if not isinstance(value[kind], list):
            raise ValidationError(f"Custom Extension {kind} 必须是 List")
        seen = set()
        for item in value[kind]:
            if not isinstance(item, dict) or set(item) - {"digest"} != {"id", "path", "description", "use_when"}:
                raise ValidationError(f"Custom Extension {kind} Entry 字段不合法")
            plain = {key: item[key] for key in ("id", "path", "description", "use_when")}
            _validate_catalog_entry(plain, kind)
            if item["id"] in seen:
                raise ValidationError(f"Custom Extension {kind} id 重复")
            seen.add(item["id"])
            target = resolve_inside(directory, item["path"])
            if target.is_symlink() or not target.is_file():
                raise ValidationError(f"Custom Extension 文件不存在或不安全：{item['path']}")
            item["digest"] = digest_bytes(target.read_bytes())
    value["digest"] = digest(value, ("digest",))
    return value


def resolve_capabilities(
    root: Path,
    *,
    rules: list[str],
    agents: list[str],
    skills: list[str],
) -> dict[str, Any]:
    catalog = installed_catalog(root)
    manifest = read_installed_manifest(root)
    digests = {item["path"]: item["digest"] for item in manifest["files"]}
    agent_by_id = {item["id"]: item for item in catalog["agents"]}
    skill_by_id = {item["id"]: item for item in catalog["skills"]}
    required_rules = catalog["required_rules"]
    custom_rule_by_id = {item["id"]: item for item in catalog["custom_rules"]}
    missing_rules = sorted(set(rules) - set(custom_rule_by_id))
    if missing_rules:
        raise ValidationError("Custom Rule id 不存在：" + ", ".join(missing_rules))
    missing_agents = sorted(set(agents) - set(agent_by_id))
    missing_skills = sorted(set(skills) - set(skill_by_id))
    if missing_agents or missing_skills:
        raise ValidationError("Capability id 不存在：" + ", ".join(missing_agents + missing_skills))

    def bind(item: dict[str, Any]) -> dict[str, Any]:
        if item.get("source") == "custom":
            target = resolve_inside(root.resolve(), item["path"])
            return {**item, "digest": digest_bytes(target.read_bytes())}
        return {**item, "digest": digests[item["path"]]}

    return {
        "status": "RESOLVED",
        "profile_id": catalog["profile_id"],
        "rules": [
            *[{"path": path, "digest": digests[path], "source": "managed"} for path in required_rules],
            *[bind(custom_rule_by_id[item]) for item in rules],
        ],
        "agents": [bind(agent_by_id[item]) for item in agents],
        "skills": [bind(skill_by_id[item]) for item in skills],
    }


def routing_plan(root: Path, *, risk: str, signals: list[str]) -> dict[str, Any]:
    """根据已安装 Profile、风险和显式 Signal 生成唯一 Routing Contract。"""

    if risk not in RISK_LEVELS:
        raise ValidationError(f"未知 Risk Level：{risk}")
    catalog = installed_catalog(root)
    manifest = read_installed_manifest(root)
    workflow = catalog.get("workflow")
    if not isinstance(workflow, dict):
        raise ValidationError("已安装 Capability Profile 没有可执行 Workflow")
    if len(signals) != len(set(signals)):
        raise ValidationError("Routing Signal 重复")
    unknown = sorted(set(signals) - set(workflow["signal_routes"]))
    if unknown:
        raise ValidationError("未知 Routing Signal：" + ", ".join(unknown))
    selected_agents = set(workflow["base"]["agents"] + workflow["risk_routes"][risk]["agents"])
    selected_skills = set(workflow["base"]["skills"] + workflow["risk_routes"][risk]["skills"])
    for signal in signals:
        selected_agents.update(workflow["signal_routes"][signal]["agents"])
        selected_skills.update(workflow["signal_routes"][signal]["skills"])
    agents = [item["id"] for item in catalog["agents"] if item["id"] in selected_agents]
    skills = [item["id"] for item in catalog["skills"] if item["id"] in selected_skills]
    handoff_agents = [item for item in agents if item != "conductor"]
    artifact_review_agents = [
        item for item in workflow["artifact_review_agents"] if item in handoff_agents
    ]
    value = {
        "schema_version": "yuan.routing/v1",
        "profile_id": catalog["profile_id"],
        "profile_digest": manifest["digest"],
        "risk": risk,
        "signals": list(signals),
        "agents": agents,
        "skills": skills,
        "handoff_agents": handoff_agents,
        "artifact_review_agents": artifact_review_agents,
    }
    value["digest"] = digest(value, ("digest",))
    return validate_routing(value)


def route_capabilities(root: Path, *, risk: str, signals: list[str]) -> dict[str, Any]:
    route = routing_plan(root, risk=risk, signals=signals)
    resolved = resolve_capabilities(root, rules=[], agents=route["agents"], skills=route["skills"])
    workflow = installed_catalog(root)["workflow"]
    selected_skills = set(route["skills"])
    assignments = [
        {
            "agent_id": agent_id,
            "skills": [skill_id for skill_id in workflow["agent_skill_routes"][agent_id] if skill_id in selected_skills],
        }
        for agent_id in route["agents"]
    ]
    assigned = {skill_id for item in assignments for skill_id in item["skills"]}
    unassigned = sorted(selected_skills - assigned)
    if unassigned:
        raise IntegrityError("Routing Skill 没有承接 Agent：" + ", ".join(unassigned))
    return {**resolved, "status": "ROUTED", "routing": route, "assignments": assignments}
