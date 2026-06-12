#!/usr/bin/env python3
"""Generate the PR-032 legacy TSC theorem-to-test audit map."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

from common.contracts import BundleKind, ClaimTier, ImplementationScope, Owner
from tsc.validation.theorem_map import (
    CORE_THEOREM_MAP,
    build_tsc_validation_witnesses,
)
from tsc_legacy import (
    TSC_ACTIVE_SCIENCE_OWNER,
    TSC_ALLOWED_BUNDLE_KIND,
    TSC_DEPRECATION_CAVEAT,
    TSC_DEPRECATION_STATUS,
    TSC_IMPLEMENTATION_SCOPE,
    TSC_OWNER,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "generated" / "theorem_to_test_map_legacy_tsc.json"
SCHEMA_VERSION = "pr032.legacy_theorem_to_test_map.v1"
SOURCE_PATHS = (
    REPO_ROOT / "scripts" / "codex_harness" / "generate_theorem_to_test_map.py",
    REPO_ROOT / "htt" / "tsc" / "validation" / "theorem_map.py",
    REPO_ROOT / "docs" / "PR_DELTAS" / "pr-030.md",
    REPO_ROOT / "docs" / "PR_DELTAS" / "pr-031.md",
    REPO_ROOT / "docs" / "deprecation" / "tsc_legacy.md",
)
DOES_NOT_ESTABLISH = (
    "production_observation_claim",
    "observable_adequacy",
    "htt_evidence",
    "mio_certificate",
    "posterior_or_likelihood_support",
    "transfer_validation",
    "native_solver_validation",
    "native_solver_result",
    "null_calibration",
    "mask_or_sky_coverage_support",
    "covariance_support",
    "response_rank_support",
    "equivalence_class_breaking",
    "morphology_atlas_support",
    "morphology_compatibility",
    "geometry_or_family_identification",
)
CAVEATS = (
    "Legacy theorem labels are retained for audit only.",
    "Rows describe validation obligations and historical test witnesses, not production observation claims.",
    "TSC_LEGACY provenance is reproduction context only and is not active science ownership.",
    "The map is not HTT evidence, not a MIO certificate, not transfer validation, not native solver validation, and not family identification.",
)


def build_payload(
    *,
    generated_on: str | None = None,
    generating_command: str | None = None,
    git_state: str | None = None,
) -> dict[str, Any]:
    """Return the canonical PR-032 audit-map payload."""

    input_hashes = [_path_hash(path) for path in SOURCE_PATHS]
    config_hash = _config_hash(
        {
            "schema_version": SCHEMA_VERSION,
            "source_module": "tsc.validation.theorem_map",
            "input_hashes": input_hashes,
            "does_not_establish": DOES_NOT_ESTABLISH,
            "theorem_count": len(CORE_THEOREM_MAP),
            "witness_count": len(build_tsc_validation_witnesses()),
        }
    )
    witnesses_by_theorem: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for witness in build_tsc_validation_witnesses():
        witnesses_by_theorem[witness.theorem].append(
            {
                "test_id": witness.test_id,
                "category": witness.category,
                "path": witness.path,
                "purpose": witness.purpose,
                "artifact_refs": list(witness.artifact_refs),
                "witness_role": "legacy_test_witness_only",
                "production_claim_allowed": False,
            }
        )

    theorems: list[dict[str, Any]] = []
    for link in CORE_THEOREM_MAP:
        theorems.append(
            {
                "theorem_id": link.theorem,
                "artifact_role": "legacy_theorem_validation_obligation",
                "legacy_status": "validation_obligation_only",
                "audit_only": True,
                "validation_obligation_only": True,
                "legacy_source_owner": TSC_OWNER.value,
                "legacy_source_scope": TSC_IMPLEMENTATION_SCOPE.value,
                "legacy_bundle_kind": TSC_ALLOWED_BUNDLE_KIND.value,
                "claim_tier_ceiling": ClaimTier.DIAGNOSTIC_ONLY.value,
                "legacy_tests": list(link.tests),
                "metrics_recorded": list(link.metrics),
                "required_artifacts": list(link.required_artifacts),
                "witnesses": witnesses_by_theorem.get(link.theorem, []),
                "production_claim_allowed": False,
                "observation_claim_allowed": False,
                "observable_adequacy_established": False,
                "native_solver_validation_allowed": False,
                "transfer_validation_allowed": False,
                "consumable_as_htt_evidence": False,
                "consumable_as_mio_certificate": False,
                "consumable_as_family_identification": False,
                "does_not_establish": list(DOES_NOT_ESTABLISH),
                "caveats": list(CAVEATS),
            }
        )

    command = generating_command or (
        f"{Path(sys.executable).as_posix()} "
        "scripts/codex_harness/generate_theorem_to_test_map.py "
        "--write docs/generated/theorem_to_test_map_legacy_tsc.json"
    )
    return {
        "metadata": {
            "schema_version": SCHEMA_VERSION,
            "source": "scripts/codex_harness/generate_theorem_to_test_map.py",
            "source_module": "tsc.validation.theorem_map",
            "owner": Owner.COMMON.value,
            "implementation_scope": ImplementationScope.COMMON.value,
            "bundle_kind": BundleKind.COMMON_CONTRACT.value,
            "legacy_source_owner": TSC_OWNER.value,
            "legacy_source_scope": TSC_IMPLEMENTATION_SCOPE.value,
            "legacy_bundle_kind": TSC_ALLOWED_BUNDLE_KIND.value,
            "legacy_deprecation_status": TSC_DEPRECATION_STATUS,
            "legacy_active_science_owner": TSC_ACTIVE_SCIENCE_OWNER,
            "claim_tier": ClaimTier.DIAGNOSTIC_ONLY.value,
            "production_status": "diagnostic_only",
            "artifact_role": "legacy_theorem_to_test_audit_map",
            "audit_only": True,
            "transfer_source": "none",
            "sky_support_status": "not_directional",
            "null_mock_status": "not_statistical",
            "covariance_status": "not_statistical",
            "source_paths": [_display_path(path) for path in SOURCE_PATHS],
            "config_hash": config_hash,
            "input_hashes": input_hashes,
            "generated_on": generated_on
            or datetime.now(UTC).replace(microsecond=0).isoformat(),
            "generating_command": command,
            "git_commit_or_worktree_state": git_state or _git_state(),
            "caveats": [*CAVEATS, TSC_DEPRECATION_CAVEAT],
            "does_not_establish": list(DOES_NOT_ESTABLISH),
            "consumable_as_production_claim": False,
            "consumable_as_solver_validation": False,
            "consumable_as_htt_evidence": False,
            "consumable_as_mio_certificate": False,
            "consumable_as_family_identification": False,
        },
        "theorems": theorems,
    }


def write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate the PR-032 legacy TSC theorem-to-test audit map."
    )
    parser.add_argument(
        "--write",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output JSON path.",
    )
    parser.add_argument(
        "--generated-on",
        default=None,
        help="Override generated_on timestamp for deterministic tests.",
    )
    parser.add_argument(
        "--git-state",
        default=None,
        help="Override git_commit_or_worktree_state for deterministic tests.",
    )
    args = parser.parse_args(argv)
    command = (
        f"{Path(sys.executable).as_posix()} "
        "scripts/codex_harness/generate_theorem_to_test_map.py "
        + " ".join(sys.argv[1:])
    )
    payload = build_payload(
        generated_on=args.generated_on,
        generating_command=command,
        git_state=args.git_state,
    )
    write_payload(args.write, payload)
    print(f"wrote {args.write}")
    return 0


def _path_hash(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"{_display_path(path)}:{digest}"


def _config_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


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


if __name__ == "__main__":
    raise SystemExit(main())
