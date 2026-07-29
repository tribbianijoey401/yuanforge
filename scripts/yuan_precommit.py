"""Fail-closed pre-commit checks for the Core authority boundary."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys
from typing import Any

from yuan_authority import verify_authority


M7_SHA256 = "4e8d974409bf0ad2bd66df17039c8dee12b6fca03a0e2860ed5ac865615823d4"
LEGACY_PREFIXES = (
    "docs/",
    "contracts/",
    "protocols/",
    "templates/",
    ".yuan/docs/",
    ".yuan/platforms/",
    ".yuan/rules/",
    ".yuan/skills/",
    ".yuan/specs/",
)
EPHEMERAL_PREFIXES = (
    ".yuan-shadow/",
    ".yuan-m8-projection/",
)
ACTIVE_RUNTIME_PATH = re.compile(
    r"^\.yuan-run/runs/[A-Za-z0-9._-]+/"
    r"(?:run-memory\.json|runtime-manifest\.json|"
    r"(?:contracts|attempts|evidence)/[A-Za-z0-9._-]+\.json)$"
)


class GateError(RuntimeError):
    """A trust-boundary check failed closed."""


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def staged_paths(repo: pathlib.Path) -> list[str]:
    process = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "-z"],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        raise GateError("cannot enumerate staged paths")
    try:
        return [
            item.decode("utf-8").replace("\\", "/")
            for item in process.stdout.split(b"\0")
            if item
        ]
    except UnicodeDecodeError as error:
        raise GateError("staged path is not UTF-8") from error


def check_staged_paths(authority: str, paths: list[str]) -> None:
    normalized = []
    for path in paths:
        value = path.replace("\\", "/")
        normalized.append(value[2:] if value.startswith("./") else value)
    for path in normalized:
        if path.startswith(EPHEMERAL_PREFIXES):
            raise GateError(f"ephemeral projection must not be staged: {path}")
        if authority == "core" and path.startswith(LEGACY_PREFIXES):
            raise GateError(f"legacy state/specification is read-only: {path}")
        if path.startswith(".yuan-run/") and not (
            path == ".yuan-run/active-run.json"
            or ACTIVE_RUNTIME_PATH.fullmatch(path)
        ):
            raise GateError(f"undeclared runtime path: {path}")


def _verify_distribution(repo: pathlib.Path) -> str:
    version_path = repo / ".yuan/VERSION"
    try:
        version = version_path.read_text(encoding="utf-8").strip()
        initializer = (repo / "bin/yuanforge-init").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise GateError("distribution version/initializer is unreadable") from error
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise GateError(".yuan/VERSION is not a semantic version")
    if '".yuan/VERSION"' not in initializer or re.search(
        r"FRAMEWORK_VERSION\s*=", initializer
    ):
        raise GateError("initializer does not use .yuan/VERSION as sole source")
    return version


def _verify_agent_binding(repo: pathlib.Path) -> None:
    binding_path = repo / ".yuan/authority/legacy-bindings/AGENTS.json"
    registry_path = repo / ".yuan/extensions/provenance/semantic-registry.json"
    try:
        binding = json.loads(binding_path.read_text(encoding="utf-8"))
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        bootstrap = (repo / "AGENTS.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise GateError("AGENTS legacy binding is missing or invalid") from error
    records = [
        item["record_key"]
        for item in registry.get("records", [])
        if item.get("source") == "AGENTS.md"
    ]
    if (
        binding.get("source_sha256")
        != "d282f61862b19ab42fe4933584fa4dd5b893650c38776ba2e9a3c97fb8d45d7a"
        or binding.get("semantic_registry_sha256") != M7_SHA256
        or binding.get("semantic_record_keys") != records
        or _sha256(registry_path) != M7_SHA256
        or ".yuan/authority/legacy-bindings/AGENTS.json" not in bootstrap
    ):
        raise GateError("AGENTS M0/M7 semantic binding mismatch")


def _verify_provenance(repo: pathlib.Path) -> None:
    process = subprocess.run(
        [
            sys.executable,
            "-B",
            str(repo / "scripts/yuan_provenance_history.py"),
            "--repo",
            str(repo),
        ],
        cwd=repo,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        raise GateError("pinned semantic provenance verifier failed")
    try:
        receipt = json.loads(process.stdout)
    except json.JSONDecodeError as error:
        raise GateError("pinned provenance receipt is not JSON") from error
    assertions = receipt.get("assertions", receipt.get("semantic_records", 0))
    if (
        receipt.get("status") != "PASS"
        or receipt.get("registry_sha256") != M7_SHA256
        or receipt.get("semantic_records") != 2227
        or receipt.get("mapped") != 2227
        or receipt.get("source_clauses") != 2207
        or receipt.get("included_sources") != 177
        or receipt.get("unmapped") != 0
        or not isinstance(assertions, int)
        or isinstance(assertions, bool)
        or assertions != 2227
        or receipt.get("delta_assertions") != 9
    ):
        raise GateError("pinned provenance receipt did not PASS")


def verify_gate(
    repo_root: pathlib.Path,
    *,
    staged_paths: list[str] | None = None,
) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    authority = verify_authority(repo)
    if authority["authority"] != "core":
        raise GateError("final authority is not Core")
    check_staged_paths(
        authority["authority"],
        globals()["staged_paths"](repo) if staged_paths is None else staged_paths,
    )
    release = _verify_distribution(repo)
    _verify_agent_binding(repo)
    _verify_provenance(repo)
    return {
        "status": "PASS",
        "authority": authority["authority"],
        "revision": authority["revision"],
        "history_length": authority["history_length"],
        "version": release,
        "m7_semantic_registry_sha256": M7_SHA256,
    }


def main() -> int:
    repo = pathlib.Path(__file__).resolve().parents[1]
    try:
        receipt = verify_gate(repo)
    except (GateError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"BLOCKED {error}", file=sys.stderr)
        return 1
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
