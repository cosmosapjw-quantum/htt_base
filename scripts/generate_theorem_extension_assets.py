#!/usr/bin/env python3
"""Generate the REV-R084 theorem-extension registry assets."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Sequence

from common.theorem_registry import default_theorem_registry


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = REPO_ROOT / "docs" / "generated" / "theorem_extension_registry.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "generated" / "theorem_extension_registry.md"
SCHEMA_VERSION = "rev-r084.theorem_extension_registry.v1"
SOURCE_PATHS = (
    REPO_ROOT / "scripts" / "generate_theorem_extension_assets.py",
    REPO_ROOT / "htt" / "src" / "common" / "theorem_registry.py",
    REPO_ROOT / "htt" / "mio" / "formalism" / "dynamic_budget.py",
    REPO_ROOT / "htt" / "mio" / "formalism" / "bound_pushforward.py",
    REPO_ROOT / "htt" / "bass" / "kinetic" / "boltzmann_memory.py",
    REPO_ROOT / "htt" / "bass" / "kinetic" / "tight_coupling_bounds.py",
    REPO_ROOT / "htt" / "bass" / "kinetic" / "visibility_rigidity.py",
    REPO_ROOT / "htt" / "bass" / "geometry" / "egs_rigidity.py",
    REPO_ROOT / "tests" / "contracts" / "test_theorem_registry.py",
    REPO_ROOT / "tests" / "mio" / "test_dynamic_budget.py",
    REPO_ROOT / "tests" / "bass" / "test_boltzmann_memory_bounds.py",
    REPO_ROOT / "tests" / "bass" / "test_egs_rigidity_theorems.py",
)
GLOBAL_CAVEATS = (
    "synthetic/manufactured verification only",
    "diagnostic-only",
    "not HTT evidence",
    "not a MIO certificate",
    "not native solver validation",
    "not geometry or family identification",
)


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _path_hash(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"{_display_path(path)}:{digest}"


def _config_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _git_state() -> str:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--short"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "git_state_unavailable"
    return f"{commit}+dirty" if status else commit


def build_payload(
    *,
    generated_on: str | None = None,
    generating_command: str | None = None,
    git_state: str | None = None,
) -> dict[str, Any]:
    registry = default_theorem_registry()
    theorem_rows = registry.to_payload()
    input_hashes = [_path_hash(path) for path in SOURCE_PATHS]
    config_hash = _config_hash(
        {
            "schema_version": SCHEMA_VERSION,
            "theorems": theorem_rows,
            "required_kill_switches": registry.required_kill_switches(),
            "source_paths": [_display_path(path) for path in SOURCE_PATHS],
            "input_hashes": input_hashes,
        }
    )
    command = generating_command or (
        f"{Path(sys.executable).as_posix()} scripts/generate_theorem_extension_assets.py --write"
    )
    return {
        "metadata": {
            "schema_version": SCHEMA_VERSION,
            "owner": "COMMON",
            "implementation_scope": "common",
            "claim_tier": "diagnostic_only",
            "transfer_source": "none",
            "sky_support_status": "not_directional",
            "covariance_status": "synthetic_only",
            "null_mock_status": "synthetic_only",
            "production_status": "diagnostic_only",
            "artifact_role": "theorem_extension_registry",
            "production_claim_allowed": False,
            "observation_claim_allowed": False,
            "native_solver_result": False,
            "family_identification": False,
            "consumable_as_htt_evidence": False,
            "consumable_as_mio_certificate": False,
            "consumable_as_family_identification": False,
            "required_kill_switches": list(registry.required_kill_switches()),
            "blocked_observational_uses": registry.blocked_observational_uses(),
            "source_paths": [_display_path(path) for path in SOURCE_PATHS],
            "config_hash": config_hash,
            "input_hashes": input_hashes,
            "generated_on": generated_on
            or datetime.now(UTC).replace(microsecond=0).isoformat(),
            "generating_command": command,
            "git_commit_or_worktree_state": git_state or _git_state(),
            "caveats": list(GLOBAL_CAVEATS),
        },
        "theorems": theorem_rows,
    }


def render_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n"


def render_markdown(payload: dict[str, Any]) -> str:
    metadata = payload["metadata"]
    lines = [
        "# Theorem Extension Registry",
        "",
        f"owner: {metadata['owner']}",
        f"implementation_scope: {metadata['implementation_scope']}",
        f"claim_tier: {metadata['claim_tier']}",
        f"transfer_source: {metadata['transfer_source']}",
        f"sky_support_status: {metadata['sky_support_status']}",
        f"covariance_status: {metadata['covariance_status']}",
        f"null_mock_status: {metadata['null_mock_status']}",
        f"native_solver_result: {str(metadata['native_solver_result']).lower()}",
        f"family_identification: {str(metadata['family_identification']).lower()}",
        f"config_hash: `{metadata['config_hash']}`",
        f"generated_on: `{metadata['generated_on']}`",
        f"generating_command: `{metadata['generating_command']}`",
        f"git_commit_or_worktree_state: `{metadata['git_commit_or_worktree_state']}`",
        "source_paths:",
    ]
    lines.extend(f"- `{path}`" for path in metadata["source_paths"])
    lines.extend(
        [
            "input_hashes:",
        ]
    )
    lines.extend(f"- `{digest}`" for digest in metadata["input_hashes"])
    lines.extend(
        [
            "caveats:",
        ]
    )
    lines.extend(f"- {caveat}" for caveat in metadata["caveats"])
    lines.extend(
        [
            "",
            "This registry is synthetic/manufactured verification only. It is diagnostic-only, not HTT evidence, not a MIO certificate, not native solver validation, and not geometry or family identification.",
            "",
            "| Theorem | Status | Proof Status | Implementation Test Status | Claim Status | Key Kill Switches |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in payload["theorems"]:
        switches = ", ".join(row["kill_switches"])
        lines.append(
            f"| {row['theorem_id']} | {row['status']} | {row['proof_status']} | "
            f"{row['implementation_test_status']} | {row['claim_status']} | {switches} |"
        )
    lines.extend(
        [
            "",
            "## Required Kill Switches",
            "",
        ]
    )
    lines.extend(f"- {switch}" for switch in metadata["required_kill_switches"])
    return "\n".join(lines) + "\n"


def write_assets(json_path: Path, markdown_path: Path, payload: dict[str, Any]) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(render_json(payload), encoding="utf-8")
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")


def check_assets(json_path: Path, markdown_path: Path) -> tuple[bool, list[str]]:
    if not json_path.exists() or not markdown_path.exists():
        return False, ["generated theorem extension assets are missing"]
    current_payload = json.loads(json_path.read_text(encoding="utf-8"))
    current_meta = current_payload.get("metadata", {})
    expected = build_payload(
        generated_on=current_meta.get("generated_on"),
        generating_command=current_meta.get("generating_command"),
        git_state=current_meta.get("git_commit_or_worktree_state"),
    )
    issues: list[str] = []
    if json_path.read_text(encoding="utf-8") != render_json(expected):
        issues.append(f"{_display_path(json_path)} is stale")
    if markdown_path.read_text(encoding="utf-8") != render_markdown(expected):
        issues.append(f"{_display_path(markdown_path)} is stale")
    return not issues, issues


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Write generated JSON and Markdown assets.")
    parser.add_argument("--check", action="store_true", help="Check generated JSON and Markdown assets for drift.")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--generated-on", default=None)
    parser.add_argument("--git-state", default=None)
    args = parser.parse_args(argv)
    command = f"{Path(sys.executable).as_posix()} scripts/generate_theorem_extension_assets.py {' '.join(sys.argv[1:])}".rstrip()
    if args.check:
        ok, issues = check_assets(args.json_output, args.markdown_output)
        if not ok:
            for issue in issues:
                print(issue, file=sys.stderr)
            return 1
        print("theorem extension assets are current")
        return 0
    payload = build_payload(
        generated_on=args.generated_on,
        generating_command=command,
        git_state=args.git_state,
    )
    if args.write:
        write_assets(args.json_output, args.markdown_output, payload)
        print(f"wrote {args.json_output}")
        print(f"wrote {args.markdown_output}")
        return 0
    print(render_json(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
