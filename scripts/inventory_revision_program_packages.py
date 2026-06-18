#!/usr/bin/env python3
"""Inventory external revision-program package inputs."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs/audits/revision_program_2026-06-18"
JSON_OUT = OUT_DIR / "package_inventory.json"
MD_OUT = OUT_DIR / "package_inventory.md"
PACKAGES = (
    "HTT_Bianchi_revision_program.zip",
    "htt_revision_upgrade_package_2026-06-17.zip",
)
SMOKE_COMMAND_REVISION_PROGRAM = (
    'REPO_ROOT=$(pwd); '
    'rm -rf /tmp/htt_revision_program_analysis && '
    'mkdir -p /tmp/htt_revision_program_analysis && '
    'unzip -q "$REPO_ROOT/HTT_Bianchi_revision_program.zip" '
    '-d /tmp/htt_revision_program_analysis && '
    'cd /tmp/htt_revision_program_analysis/revision_program/code && '
    '"$REPO_ROOT/venv/bin/python" run_all.py'
)
SMOKE_COMMAND_UPGRADE_PACKAGE = (
    'REPO_ROOT=$(pwd); '
    'rm -rf /tmp/htt_revision_upgrade_package_analysis && '
    'mkdir -p /tmp/htt_revision_upgrade_package_analysis && '
    'unzip -q "$REPO_ROOT/htt_revision_upgrade_package_2026-06-17.zip" '
    '-d /tmp/htt_revision_upgrade_package_analysis && '
    'PYTHONPATH=/tmp/htt_revision_upgrade_package_analysis/'
    'htt_revision_upgrade_package_2026-06-17/src '
    '"$REPO_ROOT/venv/bin/python" -m pytest '
    '/tmp/htt_revision_upgrade_package_analysis/'
    'htt_revision_upgrade_package_2026-06-17/tests/test_framework.py -q'
)
VERIFIED_SMOKE_EVIDENCE = {
    "revision_program_run_all": {
        "package_name": "HTT_Bianchi_revision_program.zip",
        "command": SMOKE_COMMAND_REVISION_PROGRAM,
        "verified_package_sha256": "56a4e517946f4e1ca1eccf819953c7e7bee68a88f12d210e76622d04c585b7c3",
        "verified_at_utc": "2026-06-18T00:00:00Z",
        "exit_code": 0,
        "evidence_mode": "recorded_prior_smoke_result_hash_bound",
    },
    "upgrade_package_pytest": {
        "package_name": "htt_revision_upgrade_package_2026-06-17.zip",
        "command": SMOKE_COMMAND_UPGRADE_PACKAGE,
        "verified_package_sha256": "407892716cdecacc120559921fee6b07c165aef5d3533e0bba53c0c5f7f1b496",
        "verified_at_utc": "2026-06-18T00:00:00Z",
        "exit_code": 0,
        "evidence_mode": "recorded_prior_smoke_result_hash_bound",
    },
}
CAVEATS = (
    "synthetic/analytic scaffold",
    "not publication evidence",
    "adapt concepts into repo-local generators before manuscript promotion",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def zip_entries(path: Path) -> list[str]:
    with ZipFile(path) as archive:
        return sorted(archive.namelist())


def smoke_record(evidence: dict[str, object], packages: dict[str, dict[str, object]]) -> dict[str, object]:
    package_name = evidence["package_name"]
    assert isinstance(package_name, str)
    current_package_sha256 = packages[package_name]["sha256"]
    status = "passed"
    if evidence["exit_code"] != 0:
        status = "failed"
    elif current_package_sha256 != evidence["verified_package_sha256"]:
        status = "stale_package_hash"

    return {
        **evidence,
        "current_package_sha256": current_package_sha256,
        "status": status,
    }


def build_payload() -> dict[str, object]:
    packages: dict[str, dict[str, object]] = {}
    for name in PACKAGES:
        path = ROOT / name
        if not path.exists():
            raise FileNotFoundError(path)
        packages[name] = {
            "path": name,
            "sha256": sha256(path),
            "entries": zip_entries(path),
            "source_role": "external_revision_input",
        }

    return {
        "schema_version": "htt.revision_program_inventory.v1",
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "transfer_source": "none",
        "sky_support_status": "not_directional",
        "null_mock_status": "not_statistical",
        "generating_command": "venv/bin/python scripts/inventory_revision_program_packages.py --write",
        "packages": packages,
        "smoke_tests": {
            name: smoke_record(evidence, packages)
            for name, evidence in VERIFIED_SMOKE_EVIDENCE.items()
        },
        "caveats": list(CAVEATS),
    }


def json_text(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def render_markdown(payload: dict[str, object]) -> str:
    packages = payload["packages"]
    smoke_tests = payload["smoke_tests"]
    caveats = payload["caveats"]
    assert isinstance(packages, dict)
    assert isinstance(smoke_tests, dict)
    assert isinstance(caveats, list)

    lines = [
        "# Revision Program Package Inventory",
        "",
        f"owner: {payload['owner']}",
        f"implementation_scope: {payload['implementation_scope']}",
        f"claim_tier: {payload['claim_tier']}",
        f"transfer_source: {payload['transfer_source']}",
        f"sky_support_status: {payload['sky_support_status']}",
        f"null_mock_status: {payload['null_mock_status']}",
        f"generating_command: `{payload['generating_command']}`",
        "",
        "## Packages",
        "",
        "| Package | SHA256 | Entries | Role |",
        "| --- | --- | ---: | --- |",
    ]
    for name in sorted(packages):
        package = packages[name]
        assert isinstance(package, dict)
        entries = package["entries"]
        assert isinstance(entries, list)
        lines.append(
            f"| `{name}` | `{package['sha256']}` | {len(entries)} | {package['source_role']} |"
        )

    lines.extend(
        [
            "",
            "## Smoke Tests",
            "",
            "| Check | Status | Package | Verified SHA256 | Current SHA256 | Exit Code | Evidence Mode | Command |",
            "| --- | --- | --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for name in sorted(smoke_tests):
        check = smoke_tests[name]
        assert isinstance(check, dict)
        lines.append(
            f"| `{name}` | `{check['status']}` | `{check['package_name']}` | "
            f"`{check['verified_package_sha256']}` | `{check['current_package_sha256']}` | "
            f"{check['exit_code']} | `{check['evidence_mode']}` | "
            f"`{check['command']}` |"
        )

    lines.extend(["", "## Caveats", ""])
    for caveat in caveats:
        lines.append(f"- {caveat}")
    lines.append("")
    return "\n".join(lines)


def write_outputs(payload: dict[str, object]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json_text(payload), encoding="utf-8")
    MD_OUT.write_text(render_markdown(payload), encoding="utf-8")


def check_outputs(payload: dict[str, object]) -> int:
    missing = [str(path.relative_to(ROOT)) for path in (JSON_OUT, MD_OUT) if not path.exists()]
    if missing:
        print("missing generated inventory: " + ", ".join(missing), file=sys.stderr)
        return 1

    expected_json = json_text(payload)
    expected_markdown = render_markdown(payload)
    stale: list[str] = []
    if JSON_OUT.read_text(encoding="utf-8") != expected_json:
        stale.append(str(JSON_OUT.relative_to(ROOT)))
    if MD_OUT.read_text(encoding="utf-8") != expected_markdown:
        stale.append(str(MD_OUT.relative_to(ROOT)))
    if stale:
        print("stale generated inventory: " + ", ".join(stale), file=sys.stderr)
        print("run: venv/bin/python scripts/inventory_revision_program_packages.py --write", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="write deterministic JSON and Markdown outputs")
    mode.add_argument("--check", action="store_true", help="verify generated outputs are current")
    args = parser.parse_args(argv)

    try:
        payload = build_payload()
    except (FileNotFoundError, OSError) as exc:
        print(f"inventory failed: {exc}", file=sys.stderr)
        return 1

    if args.write:
        write_outputs(payload)
        return 0
    if args.check:
        return check_outputs(payload)

    print(json_text(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
