#!/usr/bin/env python3
"""Synchronize and verify canonical PR-DAG/status/remediation mirrors."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


REPO = Path(__file__).resolve().parents[2]
BACKLOG_YAML = REPO / "docs/codex_handoff/pr_backlog.yaml"
BACKLOG_JSON = REPO / "docs/codex_handoff/pr_backlog.json"
MACHINE_BACKLOG_YAML = REPO / "machine_readable/pr_backlog.yaml"
MACHINE_BACKLOG_JSON = REPO / "machine_readable/pr_backlog.json"
STATUS_YAML = REPO / "docs/codex_handoff/pr_status.yaml"
MACHINE_STATUS_YAML = REPO / "machine_readable/pr_status.yaml"
OPTIONAL_YAML_MIRRORS = (
    (
        REPO / "docs/codex_handoff/authorized_principals.yaml",
        REPO / "machine_readable/authorized_principals.yaml",
    ),
    (
        REPO / "docs/codex_handoff/research_remediation_state.yaml",
        REPO / "machine_readable/research_remediation_state.yaml",
    ),
)


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.relative_to(REPO)} must contain a YAML mapping")
    return payload


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.relative_to(REPO)} must contain a JSON object")
    return payload


def write_mirrors() -> None:
    backlog_text = BACKLOG_YAML.read_text(encoding="utf-8")
    backlog = _load_yaml(BACKLOG_YAML)
    status_text = STATUS_YAML.read_text(encoding="utf-8")
    MACHINE_BACKLOG_YAML.write_text(backlog_text, encoding="utf-8")
    json_text = json.dumps(backlog, indent=2, ensure_ascii=False) + "\n"
    BACKLOG_JSON.write_text(json_text, encoding="utf-8")
    MACHINE_BACKLOG_JSON.write_text(json_text, encoding="utf-8")
    MACHINE_STATUS_YAML.write_text(status_text, encoding="utf-8")
    for canonical, mirror in OPTIONAL_YAML_MIRRORS:
        if canonical.exists():
            mirror.write_text(canonical.read_text(encoding="utf-8"), encoding="utf-8")


def check_mirrors() -> None:
    canonical_backlog = _load_yaml(BACKLOG_YAML)
    if BACKLOG_YAML.read_bytes() != MACHINE_BACKLOG_YAML.read_bytes():
        raise ValueError("backlog YAML mirrors differ byte-for-byte")
    if _load_json(BACKLOG_JSON) != canonical_backlog:
        raise ValueError("docs backlog JSON is not semantically equal to canonical YAML")
    if _load_json(MACHINE_BACKLOG_JSON) != canonical_backlog:
        raise ValueError("machine backlog JSON is not semantically equal to canonical YAML")
    if BACKLOG_JSON.read_bytes() != MACHINE_BACKLOG_JSON.read_bytes():
        raise ValueError("backlog JSON mirrors differ byte-for-byte")
    _load_yaml(STATUS_YAML)
    if STATUS_YAML.read_bytes() != MACHINE_STATUS_YAML.read_bytes():
        raise ValueError("status YAML mirrors differ byte-for-byte")
    for canonical, mirror in OPTIONAL_YAML_MIRRORS:
        if canonical.exists() != mirror.exists():
            raise ValueError(f"optional mirror presence differs: {canonical.name}")
        if canonical.exists():
            _load_yaml(canonical)
            if canonical.read_bytes() != mirror.read_bytes():
                raise ValueError(f"optional YAML mirrors differ: {canonical.name}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.write:
            write_mirrors()
        check_mirrors()
    except (OSError, ValueError, yaml.YAMLError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("OK: PR-DAG, status, and remediation mirrors are synchronized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
