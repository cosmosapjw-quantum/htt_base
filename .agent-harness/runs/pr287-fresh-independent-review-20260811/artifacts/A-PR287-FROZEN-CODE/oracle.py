#!/usr/bin/env python3
"""Independent hostile oracle for the frozen PR-287 code review."""

from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[5]
for relative in ("htt/src", "htt/htt", "htt"):
    candidate = str(ROOT / relative)
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from common import post275_blind_replay as common  # noqa: E402
from htt.infer.post275_blind_replay import analyze_fresh_challenge  # noqa: E402
from obsstat.exact_parity_readiness import (  # noqa: E402
    PASS_TOKEN,
    build_parity_readiness_receipt,
    validate_parity_readiness_receipt,
)


def expect_contract_error(label: str, call) -> str:
    try:
        call()
    except common.BlindReplayContractError as exc:
        return f"{label}: {exc}"
    raise AssertionError(f"{label}: hostile mutation survived")


def main() -> None:
    checks: list[str] = []

    required_outputs = (
        "docs/research_program/post_pr275/blind_replay/FRESH_CHALLENGE_V1.json",
        "docs/research_program/post_pr275/blind_replay/FRESH_TRUTH_VAULT_V1.json",
        "docs/research_program/post_pr275/blind_replay/FROZEN_SUBMISSION_V1.json",
        "docs/research_program/post_pr275/blind_replay/REGISTERED_ADJUDICATION_V1.json",
        "docs/research_program/post_pr275/blind_replay/PACK_A_V1.json",
        "docs/research_program/post_pr275/blind_replay/PACK_B_V1.json",
        "docs/research_program/post_pr275/blind_replay/PACK_C_V1.json",
        "docs/generated/pr287_fresh_blind_typed_replay_receipt.json",
    )
    before = {path: (ROOT / path).exists() for path in required_outputs}
    assert not any(before.values()), before
    activation = common.build_dependency_activation_receipt(
        spec_path=ROOT / "docs/research_program/post_pr275/pr287_spec.yaml",
        status_path=ROOT / "docs/codex_handoff/pr_status.yaml",
        repository_root=ROOT,
    )
    common.require_dependency_activation(activation)
    after = {path: (ROOT / path).exists() for path in required_outputs}
    assert after == before
    checks.append("activation_rebuilt_and_side_effect_free")

    modules, provenance = common._canonical_harness_validation_modules()
    assert set(modules) == set(common._HARNESS_MODULE_PROVENANCE)
    for module_name, source_path, source_sha256 in provenance:
        source = ROOT / source_path
        assert Path(modules[module_name].__file__).resolve() == source.resolve()
        assert hashlib.sha256(source.read_bytes()).hexdigest() == source_sha256
    checks.append("transitive_harness_origin_and_bytes_bound")

    for kind in common.BlindReplayPackKind:
        module_name = common._PACK_FACTORY_MODULE[kind]
        _, provenance_row = common._owner_factory_provenance(
            kind=kind, factory_module=module_name
        )
        source = ROOT / provenance_row["source_path"]
        assert hashlib.sha256(source.read_bytes()).hexdigest() == provenance_row[
            "source_sha256"
        ]
    checks.append("owner_factory_origin_and_bytes_bound")

    checks.append(
        expect_contract_error(
            "owner_factory_callsite_substitution",
            lambda: common._issue_diagnostic_pack(
                kind=common.BlindReplayPackKind.PACK_A,
                factory_module="common.post275_blind_replay",
                metadata={},
                surfaces={},
            ),
        )
    )
    checks.append(
        expect_contract_error(
            "recursive_forbidden_alias",
            lambda: common._scan_surface_forbidden(
                {"nested": [{"posterior_odds": 2.0}]}, "oracle"
            ),
        )
    )
    checks.append(
        expect_contract_error(
            "runtime_claim_variant",
            lambda: common._scan_runtime_claim_values(
                {"nested": ["Bianchi geometry was detected"]}, "oracle"
            ),
        )
    )

    parameters = inspect.signature(analyze_fresh_challenge).parameters
    assert tuple(parameters) == ("challenge", "analyzer")
    assert parameters["analyzer"].default is None
    checks.append(
        expect_contract_error(
            "isolated_executor_typed_blocker",
            lambda: analyze_fresh_challenge(object()),
        )
    )
    source = inspect.getsource(analyze_fresh_challenge)
    assert "capability-isolated analyst executor is not installed" in source
    assert "in-process analyzer callbacks are forbidden" in source
    checks.append("isolated_executor_contains_ambient_callback_authority")

    parity_spec = yaml.safe_load(
        (ROOT / "docs/research_program/post_pr275/pr282_spec.yaml").read_text(
            encoding="utf-8"
        )
    )
    parity = build_parity_readiness_receipt(parity_spec)
    assert parity["terminal"]["g3_outcome"] == PASS_TOKEN
    assert parity["clean_execution"]["baseline"] == {
        "numerator": -115,
        "denominator": 3,
    }
    assert parity["clean_execution"]["transformed"] == {
        "numerator": 115,
        "denominator": 3,
    }
    assert parity["clean_execution"]["relation_residual"] == {
        "numerator": 0,
        "denominator": 1,
    }
    assert validate_parity_readiness_receipt(parity, parity_spec) == ()
    checks.append("exact_rational_anti_equivariance_preserved")

    print(json.dumps({"status": "PASS", "checks": checks}, indent=2))


if __name__ == "__main__":
    main()
