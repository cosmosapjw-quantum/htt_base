#!/usr/bin/env python3
"""Produce or verify the rootless PR-289/PR-300 integration receipt.

This runner reads only repository contracts.  It does not accept candidate data
roots, invoke a network client, or construct an authorization successor.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs/generated/pr303_integrated_data_identity_receipt.json"
PR289_SOURCE_HEAD = "45da1bf54149864fb9d87be3a828df202ee1df7f"
PR300302_BASE = "4c371d1101f5e0eb19d3dea80ca40eabea5f7987"
TERMINAL = "PASS_PR289_PR300_INTEGRATION_ONLY"
CORE_HASHES = {
    "docs/PR_DELTAS/pr-289.md": "bf490fc07bbc0145f123272ba21f838465cdc4dee42f56662654dca76951b77c",
    "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json": "e72eee5fd720318367bd38b90412aa0286f521be7cb47b7a988df4e579ab167f",
    "docs/research_program/post_pr275/pr289_spec.yaml": "f4a8e89e603a1f6e4fe9cb99c422ef83407fd264328b3adaf927aafdcfb6636f",
    "docs/research_program/post_pr275/pr289_publication_policy.json": "4c282e04fb154a92861ff28cc67c0bb1dab881486b8ee3c87892053318e019a9",
    "htt/src/common/data_identity.py": "145fa42267348098522cd90929c052f21629e0314086e24aad216ce0de112da2",
    "scripts/codex_harness/run_pr289_data_identity_v2.py": "14ed58a68f4a628644219f6df0b966d5e2cedddef0a7c32f10ce1c94a85e6ad5",
    "tests/contracts/test_data_identity_registry_v2.py": "1ee3fb1541a911abfd686d5cd78f75380b8847dfe5d1fd076cd48153a4f1c3c3",
}
PR151_WITHDRAWN = (
    "docs/generated/desi_dipole_card.json",
    "docs/generated/desi_dipole_mock_card.json",
    "docs/generated/desi_exact_selection_card.json",
    "figures/obsdata_current/fig_obs_desi_dipole_mock.png",
    "figures/obsdata_current/fig_obs_desi_dipole_mock.source.json",
    "figures/obsdata_current/fig_obs_desi_dipole_mock.manifest.json",
)
STALE_RECEIPT = "docs/generated/pr289_data_identity_v2_receipt.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_core_identity(root: Path) -> dict[str, str]:
    actual = {relative: _sha256(root / relative) for relative in CORE_HASHES}
    mismatches = [
        relative
        for relative, digest in CORE_HASHES.items()
        if actual[relative] != digest
    ]
    if mismatches:
        raise RuntimeError(f"PR289_SOURCE_DRIFT {sorted(mismatches)}")
    return actual


def _require_pr151_quarantine(root: Path) -> None:
    spec = root / "docs/research_program/long_horizon_rescue/pr151_spec.yaml"
    if "scientific_status: INVALIDATED_PENDING_FORMALISM_REVALIDATION" not in spec.read_text(encoding="utf-8"):
        raise RuntimeError("PR151_INVALIDATION_STATE_DRIFT")
    if (root / STALE_RECEIPT).exists():
        raise RuntimeError("STALE_PR289_CANDIDATE_RECEIPT_PRESENT")
    present = [relative for relative in PR151_WITHDRAWN if (root / relative).exists()]
    if present:
        raise RuntimeError(f"PR151_INVALIDATION_REGRESSION {present}")


def _load_exact_pr289_runner(root: Path):
    path = root / "scripts/codex_harness/run_pr289_data_identity_v2.py"
    spec = importlib.util.spec_from_file_location("_pr303_exact_pr289_runner", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("PR289_RUNNER_IMPORT_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if Path(module.__file__).resolve() != path.resolve():
        raise RuntimeError("PR289_RUNNER_ORIGIN_DRIFT")
    return module


def build_payload(root: Path = ROOT) -> dict[str, Any]:
    source_hashes = _require_core_identity(root)
    _require_pr151_quarantine(root)
    runner = _load_exact_pr289_runner(root)
    preflight = runner._build(root)
    decisions = preflight["lane_decisions"]
    authorizations = preflight["authorization_receipts"]
    if len(decisions) != 6 or len(authorizations) != 6:
        raise RuntimeError("PR289_LANE_CARDINALITY_DRIFT")
    if any(row["status"] == "ADMITTED_IDENTITY_ONLY" for row in decisions):
        raise RuntimeError("PR303_UNEXPECTED_ADMITTED_LANE")
    if any(row["status"] != "NOT_AUTHORIZED" for row in authorizations):
        raise RuntimeError("PR303_UNEXPECTED_AUTHORIZATION")
    if preflight["aggregate_status"] != "NO_ADMITTED_IDENTITIES":
        raise RuntimeError("PR303_UNEXPECTED_PREFLIGHT_AGGREGATE")
    return {
        "schema": "htt.pr303.integrated_data_identity_receipt.v1",
        "terminal": TERMINAL,
        "base_commit": PR300302_BASE,
        "pr289_source_head": PR289_SOURCE_HEAD,
        "exact_pr289_source_hashes": source_hashes,
        "registry_content_id": preflight["registry_content_id"],
        "pr289_preflight_terminal": preflight["terminal"],
        "pr289_aggregate_status": preflight["aggregate_status"],
        "refused_lane_count": len(decisions),
        "admitted_lane_count": 0,
        "authorized_lane_count": 0,
        "executed_lane_count": 0,
        "observed_data_executed": False,
        "scientific_effect": "none",
        "authorization_successor_present": False,
        "stale_pr289_candidate_receipt_present": False,
        "pr151_withdrawn_artifacts_absent": True,
        "network_or_download_side_effect": False,
        "write_scope": "atomic_receipt_only",
    }


def _encoded(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _validate_output(output: Path) -> None:
    parent = output.parent
    if parent.is_symlink() or not parent.is_dir():
        raise RuntimeError("receipt parent must be a regular directory")
    if output.is_symlink() or (output.exists() and not output.is_file()):
        raise RuntimeError("receipt output must be a regular non-symlink file")


def _atomic_write(output: Path, payload: dict[str, Any]) -> None:
    _validate_output(output)
    parent = output.parent
    parent_stat = parent.stat(follow_symlinks=False)
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(parent, flags)
    temporary_name = ""
    try:
        opened_parent = os.fstat(descriptor)
        if (opened_parent.st_dev, opened_parent.st_ino) != (
            parent_stat.st_dev,
            parent_stat.st_ino,
        ):
            raise RuntimeError("receipt parent identity drifted")
        temporary_name = f".pr303-{secrets.token_hex(16)}"
        temporary_fd = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0),
            0o600,
            dir_fd=descriptor,
        )
        with os.fdopen(temporary_fd, "wb") as handle:
            handle.write(_encoded(payload))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(
            temporary_name,
            output.name,
            src_dir_fd=descriptor,
            dst_dir_fd=descriptor,
        )
        temporary_name = ""
        os.fsync(descriptor)
    finally:
        if temporary_name:
            os.unlink(temporary_name, dir_fd=descriptor)
        os.close(descriptor)


def _load_receipt(output: Path) -> dict[str, Any]:
    _validate_output(output)
    if not output.is_file():
        raise RuntimeError("integration receipt is missing")
    payload = json.loads(output.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("integration receipt must be a JSON object")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args(argv)
    payload = build_payload()
    if args.write:
        _atomic_write(args.output, payload)
    else:
        if _load_receipt(args.output) != payload:
            raise RuntimeError("integration receipt drifted")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
