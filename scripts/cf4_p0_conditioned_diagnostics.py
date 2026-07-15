#!/usr/bin/env python3
"""Method-only PR-120 records for secondary CF4 P0 consumers.

The historical numerical producers and their exact outputs live below
``legacy/cf4_p0``.  Active paths intentionally expose only treatment or
reconstruction mechanics plus the canonical OPEN-finding block.  They never
load the CF4 catalogue and never calculate a replacement value.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[1]
for root in (REPO, REPO / "htt", REPO / "htt" / "src"):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from common.cf4_p0_quarantine import (  # noqa: E402
    CF4P0PolicyError,
    atomic_write_text,
    quarantine_block_payload,
    read_regular_text,
)


@dataclass(frozen=True)
class ConditionedDiagnosticSpec:
    artifact_id: str
    active_script: str
    active_json: str
    active_markdown: str | None
    legacy_script: str
    legacy_artifacts: tuple[str, ...]
    method_definition: tuple[str, ...]
    allowed_use: str
    forbidden_uses: tuple[str, ...]


RECONSTRUCTION_SPEC = ConditionedDiagnosticSpec(
    artifact_id="cf4_reconstruction_dependence_card",
    active_script="scripts/cf4_reconstruction_dependence.py",
    active_json="docs/generated/cf4_reconstruction_dependence_card.json",
    active_markdown=None,
    legacy_script="legacy/cf4_p0/scripts/cf4_reconstruction_dependence.py",
    legacy_artifacts=(
        "legacy/cf4_p0/cards/cf4_reconstruction_dependence_card.json",
    ),
    method_definition=(
        "Compare peculiar-velocity reconstruction treatments on identical catalogue support.",
        "Keep estimator, object support, and weighting fixed when isolating reconstruction dependence.",
        "Treat Zone-of-Avoidance cuts and external reconstruction grids as sensitivity axes, not independent detections.",
    ),
    allowed_use="reconstruction_conditioned_method_and_systematics_design_only",
    forbidden_uses=(
        "bulk_flow_amplitude_measurement",
        "apex_measurement",
        "global_tilt_pushforward",
        "cosmological_tension",
        "family_identification",
    ),
)


PAIR_SPEC = ConditionedDiagnosticSpec(
    artifact_id="cf4_velocity_correlation_card",
    active_script="scripts/cf4_velocity_correlation.py",
    active_json="docs/generated/cf4_velocity_correlation_card.json",
    active_markdown=None,
    legacy_script="legacy/cf4_p0/scripts/cf4_velocity_correlation.py",
    legacy_artifacts=(
        "legacy/cf4_p0/cards/cf4_velocity_correlation_card.json",
    ),
    method_definition=(
        "Define line-of-sight pair-correlation bins and angular projection weights before fitting any amplitude.",
        "Keep direct and reconstructed peculiar-velocity treatments separate throughout the pair statistic.",
        "Use mock-bound covariance and an independently authorized likelihood before any growth-amplitude interpretation.",
    ),
    allowed_use="treatment_conditioned_pair_statistic_and_systematics_design_only",
    forbidden_uses=(
        "growth_amplitude_measurement",
        "f_sigma8_constraint",
        "global_tilt_pushforward",
        "cosmological_tension",
        "family_identification",
    ),
)


LIKELIHOOD_SPEC = ConditionedDiagnosticSpec(
    artifact_id="cf4_bulkflow_likelihood_report",
    active_script="scripts/make_cf4_bulkflow_likelihood.py",
    active_json="docs/generated/cf4_bulkflow_likelihood_report.json",
    active_markdown="docs/generated/cf4_bulkflow_likelihood_report.md",
    legacy_script="legacy/cf4_p0/scripts/make_cf4_bulkflow_likelihood.py",
    legacy_artifacts=(
        "legacy/cf4_p0/cards/cf4_bulkflow_likelihood_report.json",
        "legacy/cf4_p0/cards/cf4_bulkflow_likelihood_report.md",
        "legacy/cf4_p0/figures/observed_current/fig_observed_cf4_bulkflow_likelihood.png",
        "legacy/cf4_p0/figures/observed_current/fig_observed_cf4_bulkflow_likelihood.manifest.json",
    ),
    method_definition=(
        "Retain the forward-likelihood schema, nuisance decomposition, and coverage-test design.",
        "Require authenticated catalogue support, full covariance, matched nulls, and response-rank audit before observational evaluation.",
        "Keep local-flow and global-vector terms distinct; no data-derived global component is available on this active path.",
    ),
    allowed_use="likelihood_schema_and_coverage_test_design_only",
    forbidden_uses=(
        "bulk_flow_amplitude_measurement",
        "observed_likelihood_ratio",
        "global_tilt_measurement",
        "posterior_or_evidence",
        "family_identification",
    ),
)


def conditioned_payload(spec: ConditionedDiagnosticSpec) -> dict:
    payload = quarantine_block_payload(REPO)
    payload["artifact"] = {
        "artifact_id": spec.artifact_id,
        "artifact_kind": "conditioned_method_diagnostic_block_record",
        "producer": spec.active_script,
        "active_json": spec.active_json,
        "active_markdown": spec.active_markdown,
        "legacy_script": spec.legacy_script,
        "legacy_reproduction_only": list(spec.legacy_artifacts),
        "legacy_public_use": False,
        "owner": "OBSSTAT",
        "implementation_scope": "obsstat_method_and_systematics_only",
        "claim_tier": "blocked",
        "transfer_source": "none",
        "allowed_use": spec.allowed_use,
        "method_definition": list(spec.method_definition),
        "observational_numeric_instantiation": {
            "status": "QUARANTINED_OPEN_P0",
            "values": None,
            "replacement_value": None,
        },
        "forbidden_uses": list(spec.forbidden_uses),
        "sky_support_status": "not_evaluated_on_active_path",
        "covariance_status": "not_bound_on_active_path",
        "null_mock_status": "not_bound_on_active_path",
        "caveats": [
            "Method mechanics survive only as treatment-conditioned design substrate.",
            "Quarantine is propagation control and does not remediate the OPEN findings.",
            "No observed numerical value or alternative audit sensitivity is a replacement result.",
        ],
        "generating_command": f"python {spec.active_script}",
        "git_commit_or_worktree_state": "content-addressed_by_canonical_block",
    }
    return payload


def _render_markdown(spec: ConditionedDiagnosticSpec, payload: dict) -> str:
    artifact = payload["artifact"]
    findings = ", ".join(row["finding_id"] for row in payload["findings"])
    lines = [
        f"# {spec.artifact_id} - PR-120 conditioned method record",
        "",
        "owner: OBSSTAT",
        "implementation_scope: obsstat_method_and_systematics_only",
        "claim_tier: blocked",
        "transfer_source: none",
        "sky_support_status: not_evaluated_on_active_path",
        "covariance_status: not_bound_on_active_path",
        "null_mock_status: not_bound_on_active_path",
        f"status: {payload['status']}",
        f"findings: {findings}",
        f"allowed_use: {artifact['allowed_use']}",
        "replacement_value: none",
        "",
        "## Retained method substrate",
        "",
    ]
    lines.extend(f"- {row}" for row in artifact["method_definition"])
    lines.extend(
        [
            "",
            "## Claim boundary",
            "",
            "No observational numerical instantiation is active. Historical bytes are legacy reproduction only and public use is false.",
            "Quarantine is propagation control, not scientific remediation.",
            "",
        ]
    )
    return "\n".join(lines)


def expected_texts(spec: ConditionedDiagnosticSpec) -> dict[Path, str]:
    payload = conditioned_payload(spec)
    outputs = {
        REPO / spec.active_json: json.dumps(payload, indent=2, sort_keys=True) + "\n",
    }
    if spec.active_markdown is not None:
        outputs[REPO / spec.active_markdown] = _render_markdown(spec, payload)
    return outputs


def conditioned_main(
    spec: ConditionedDiagnosticSpec, argv: list[str] | None = None
) -> int:
    parser = argparse.ArgumentParser(
        description="Emit a method-only PR-120 record with no CF4 numerical evaluation."
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    expected = expected_texts(spec)
    if args.check:
        stale = []
        for path, text in expected.items():
            relative = path.relative_to(REPO).as_posix()
            try:
                current = read_regular_text(REPO, relative)
            except CF4P0PolicyError:
                current = None
            if current != text:
                stale.append(relative)
        missing_legacy = [
            path for path in spec.legacy_artifacts if not (REPO / path).is_file()
        ]
        if stale or missing_legacy:
            if stale:
                print("stale conditioned CF4 records: " + ", ".join(stale), file=sys.stderr)
            if missing_legacy:
                print("missing legacy CF4 artifacts: " + ", ".join(missing_legacy), file=sys.stderr)
            return 1
        print(f"conditioned CF4 record current: {spec.artifact_id}")
        return 0
    for path, text in expected.items():
        atomic_write_text(REPO, path.relative_to(REPO).as_posix(), text)
    print(f"wrote method-only block record: {spec.artifact_id}")
    return 0
