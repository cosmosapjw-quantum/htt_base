#!/usr/bin/env python3
"""Independent invariant oracle for the frozen PR-286 claim/provenance review."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np
import yaml


ROOT = Path(__file__).resolve().parents[5]
EXPECTED_HEAD = "0b1a8ef76df47b0b42e972bb47c9bc294e80aa7c"
EXPECTED_BASE = "16bc6db511b8b7228e5c4dcb95c65074fe519f24"
EXPECTED_INPUT_HASHES = {
    ".prguard/runtime/PR286_R3_MIO_CANDIDATE_SEAL.json": "d95f5a26bab5be25afb550e64d75ce4f8419fca8b61b232682c960e9e5e1fc95",
    "docs/research_program/post_pr275/pr286_spec.yaml": "6fca230213eea5c914842c63513a9047cb3221d0646564692464a82d7a03fc05",
    "htt/src/common/vector_tensor_statistical_inference.py": "61278f7d29831215dac2abd38f00c1f96a68e6f6462683778f3635a01fc9c254",
    "htt/mio/formalism/vector_tensor_validation.py": "e08b58382250ae70c8afabaaf771e6579e5244812f2a59706f8f3b681888da8b",
    "scripts/codex_harness/run_pr286_pillar_s_adjudication.py": "a4a5243e13bc46503a16904c5f26a670a077d575220f16ebdae0c5d206493732",
    "tests/contracts/test_pillar_s_inference.py": "f1daf4bf081a0eadf9cb6443b5580282cffae6a03937506d9ec1350f8b8999a3",
    "tests/contracts/test_pillar_s_complete_adjudication.py": "5e544fdbbe564765092a8c4f60b4f39a6bd3a32d42467f7dc6c9ac34f6754bef",
    "docs/research_program/post_pr275/pillar_s_adjudication/PILLAR_S_COMPLETE_ADJUDICATION_V1.json": "b5ea12647f1d7818da3702b3da8d127f490a15cdef8e37fa8958cfe803b3ee5a",
    "docs/research_program/post_pr275/pr286_publication_policy.json": "768b5263096154770e48762704e363d127ea1c1ef89a8c973f94a14173ec086d",
    "docs/PR_DELTAS/pr-286.md": "39ce89dc0b149540221e1cbdb9331322f31a734851762f5a93b9f5744a221047",
    "docs/codex_handoff/pr_status.yaml": "d27e79de2c61e0db1ff22852cd1cc9a27af74f57aa282b8714acd621663b8eef",
    "machine_readable/pr_status.yaml": "d27e79de2c61e0db1ff22852cd1cc9a27af74f57aa282b8714acd621663b8eef",
    "docs/codex_handoff/pr_backlog.yaml": "73553b6056e5111c1047b80f79c35cdb8e898e0a7b8a7e7e28f97731b5cc699e",
}


def _bytes(relative: str) -> bytes:
    return (ROOT / relative).read_bytes()


def _json(relative: str) -> dict:
    return json.loads(_bytes(relative))


def _yaml(relative: str) -> dict:
    return yaml.safe_load(_bytes(relative))


def _canonical_sha(payload: dict, omitted: str) -> str:
    body = {key: value for key, value in payload.items() if key != omitted}
    encoded = json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def main() -> None:
    for relative, expected in EXPECTED_INPUT_HASHES.items():
        assert hashlib.sha256(_bytes(relative)).hexdigest() == expected, relative

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert head == EXPECTED_HEAD

    seal = _json(".prguard/runtime/PR286_R3_MIO_CANDIDATE_SEAL.json")
    assert seal["candidate_sha"] == EXPECTED_HEAD
    assert seal["base_sha"] == EXPECTED_BASE
    assert seal["merge_base_sha"] == EXPECTED_BASE
    assert seal["target_branch"] == (
        "changeset/pr285-pillar-t-adjudication-recovery-20260810"
    )
    assert seal["dirty"] is False
    assert seal["production_hash"] == (
        "99ad99e15ff863b63945663c112767d1f6dc90e8f697a407798c281cb39c2b30"
    )
    assert _canonical_sha(seal, "seal_sha256") == seal["seal_sha256"]

    spec = _yaml("docs/research_program/post_pr275/pr286_spec.yaml")
    assert spec["owner"] == "HTT"
    assert set(spec["contributors"]) == {"COMMON", "OBSSTAT"}
    assert spec["claim_tier"] == "diagnostic_only"
    assert spec["claim_level"] == {"scheme": "roadmap_rescue_v1", "level": "C2"}
    assert spec["transfer_source"] == "none"
    assert spec["observed_data_executed"] is False
    assert spec["public_use"] is False
    assert spec["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    admitted = spec["vector_tensor_evidence"]["admitted_data_gate"]
    assert admitted["row"] == "VT-S14"
    assert admitted["verdict"] == "BLOCKED_WITH_RECEIPT"
    assert "admitted-data requirement" in admitted["reason"]
    assert any(
        text.startswith("PR-273 is a held-out synthetic integration diagnostic")
        for text in spec["assumptions"]
    )
    assert any("VT-S14 remains blocked before admitted data" in text for text in spec["caveats"])

    receipt = _json(
        "docs/research_program/post_pr275/pillar_s_adjudication/"
        "PILLAR_S_COMPLETE_ADJUDICATION_V1.json"
    )
    assert receipt["receipt_content_sha256"] == _canonical_sha(
        receipt, "receipt_content_sha256"
    )
    assert len(receipt["rows"]) == 72
    terminal_counts = Counter(row["verdict"] for row in receipt["rows"])
    assert terminal_counts["PASS"] == 21
    assert terminal_counts["FAIL"] == 0
    assert terminal_counts["INCONCLUSIVE_WITH_RECEIPT"] == 50
    assert terminal_counts["BLOCKED_WITH_RECEIPT"] == 1
    assert set(terminal_counts) == {
        "PASS",
        "INCONCLUSIVE_WITH_RECEIPT",
        "BLOCKED_WITH_RECEIPT",
    }
    assert all(row["claim_ceiling"] == "diagnostic_only" for row in receipt["rows"])
    rows = {row["row_id"]: row for row in receipt["rows"]}
    assert rows["VT-S14"]["verdict"] == "BLOCKED_WITH_RECEIPT"
    assert rows["VT-S14"]["source_status_effect"] == "RETAIN_PROGRAM_OBLIGATION"
    assert "admitted data are absent" in rows["VT-S14"]["verdict_reason"]
    assert receipt["metadata"]["claim_tier"] == "diagnostic_only"
    assert receipt["metadata"]["claim_level"] == {
        "scheme": "roadmap_rescue_v1",
        "level": "C2",
    }
    assert receipt["metadata"]["transfer_source"] == "none"
    assert receipt["metadata"]["observed_data_executed"] is False
    assert receipt["metadata"]["public_use"] is False
    assert receipt["metadata"]["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    assert receipt["ownership"] == {
        "COMMON": "exact contracts and proof identities",
        "OBSSTAT": "observable estimands features nulls and covariance inputs",
        "HTT": "model-dependent calibration coverage and inference diagnostics",
        "MIO": "diagnostic residual and coherence consumers only",
    }
    assert receipt["mio_forbidden_outputs"] == [
        "likelihood",
        "posterior",
        "Bayes_factor",
        "evidence",
    ]
    consumer = receipt["future_consumer_contract"]
    assert consumer["consumer"] == "PR-287"
    assert consumer["upstream_success_semantics"] == "PROCESS_COMPLETION_ONLY"
    assert consumer["preserve_inconclusive_and_blocked"] is True
    assert consumer["synthetic_validation_effect"] == (
        "NO_OBSERVED_OR_SOURCE_PROOF_PROMOTION"
    )
    assert len(receipt["mutation_registry"]) == 20
    assert len(receipt["mutation_results"]) == 20
    assert all(
        item["executed"]
        and item["activated"]
        and item["killed"]
        and item["survivor"] is False
        for item in receipt["mutation_results"]
    )
    json.dumps(receipt, allow_nan=False)

    policy = _json("docs/research_program/post_pr275/pr286_publication_policy.json")
    assert policy["claim_ceiling"] == "diagnostic_only"
    assert policy["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    assert policy["ordinary_agent_push_forbidden"] is True
    assert policy["ordinary_agent_pr_mutation_forbidden"] is True
    assert "merge" in policy["attended_publication"]["forbidden_actions"]
    assert "MIO likelihood posterior or evidence" in policy["forbidden_inputs"]
    assert "Bianchi family identification" in policy["forbidden_inputs"]

    status_bytes = _bytes("docs/codex_handoff/pr_status.yaml")
    assert status_bytes == _bytes("machine_readable/pr_status.yaml")
    status = yaml.safe_load(status_bytes)
    stack = status["stacked_pr_execution"]
    assert stack["merge_policy"] == "HUMAN_ONLY"
    pr285 = stack["prs"]["PR-285"]
    pr286 = stack["prs"]["PR-286"]
    pr287 = stack["prs"]["PR-287"]
    assert pr285["lifecycle"] == "PR_OPEN"
    assert pr285["sealed_head"] == EXPECTED_BASE
    assert pr286["lifecycle"] == "VALIDATED"
    assert pr286["assurance_budget"] == {"consumed": 7, "maximum": 16}
    assert pr286["base_sha"] == EXPECTED_BASE
    assert pr286["predecessor_pr"] == "PR-285"
    assert pr286["predecessor_sealed_sha"] == EXPECTED_BASE
    assert pr286["production_hash"] == seal["production_hash"]
    assert pr286["gate_dispositions"]["seal"] == "INELIGIBLE"
    assert pr286["gate_dispositions"]["push"] == "INELIGIBLE"
    assert pr286["gate_dispositions"]["publication"] == "INELIGIBLE"
    assert pr287["lifecycle"] == "PLANNED"
    assert pr287["gate_dispositions"] == {"eligibility": "INELIGIBLE"}
    assert pr287["assurance_budget"] == {"consumed": 0, "maximum": 16}
    assert pr287["predecessor_pr"] == "PR-286"

    backlog = _yaml("docs/codex_handoff/pr_backlog.yaml")
    cards = {item["id"]: item for item in backlog["prs"]}
    assert cards["PR-286"]["owner"] == "HTT"
    assert cards["PR-286"]["claim_tier_ceiling"] == "diagnostic_only"
    assert cards["PR-286"]["public_use"] is False
    edge = next(
        item
        for item in cards["PR-287"]["dependency_contracts"]
        if item["upstream_id"] == "PR-286"
    )
    assert edge["required_terminal"] == "PASS_COMPLETE_PILLAR_S_ADJUDICATION"
    assert edge["success_semantics"] == "PROCESS_COMPLETION_ONLY"
    assert edge["downstream_row_contract"] == {
        "preserve_inconclusive_and_blocked": True,
        "preserve_row_verdicts": True,
        "synthetic_validation_effect": "NO_OBSERVED_OR_SOURCE_PROOF_PROMOTION",
    }

    delta = " ".join(_bytes("docs/PR_DELTAS/pr-286.md").decode("utf-8").split())
    assert "The human granted standing approval on 2026-08-11 for any further bounded repair required inside the current Phase-2 scope." in delta
    assert "That approval does not extend the 16-unit assurance budget, activate PR-287, authorize merge" in delta
    assert "Assurance consumption remains 7 of 16" in delta
    assert "merge remains human-only" in delta

    sys.path[:0] = [str(ROOT / "htt/src"), str(ROOT / "htt")]
    from common.vector_tensor_statistical_inference import (  # noqa: PLC0415
        CLAIM_CEILING,
        HttDepthDiscriminationReport,
        MioDepthDiagnosticCrossCheck,
        PillarSInferenceError,
    )
    import mio.formalism.vector_tensor_validation as mio_surface  # noqa: PLC0415

    assert CLAIM_CEILING == "diagnostic_only"
    assert HttDepthDiscriminationReport.__dataclass_fields__["likelihood_owner"].default == "HTT"
    mio_fields = MioDepthDiagnosticCrossCheck.__dataclass_fields__
    assert mio_fields["owner"].default == "MIO"
    assert mio_fields["likelihood_present"].default is False
    assert mio_fields["posterior_present"].default is False
    assert mio_fields["evidence_present"].default is False
    assert set(mio_surface.__all__) == {
        "MioDepthDiagnosticCrossCheck",
        "PillarSInferenceError",
        "ValidationStatus",
        "build_mio_depth_cross_check",
    }
    assert not hasattr(mio_surface, "HttDepthDiscriminationReport")
    assert not hasattr(mio_surface, "PosteriorExceedance")
    normal = mio_surface.build_mio_depth_cross_check(
        (1.0, 2.0),
        local_design=(1.0, 0.0),
        global_design=(0.0, 1.0),
        mask_path_id="oracle-mask",
    )
    assert normal.owner == "MIO"
    assert normal.claim_ceiling == "diagnostic_only"
    assert not normal.likelihood_present
    assert not normal.posterior_present
    assert not normal.evidence_present
    assert all(
        math.isfinite(value)
        for value in (
            normal.local_residual_norm,
            normal.global_residual_norm,
            normal.residual_norm_difference_global_minus_local,
        )
    )
    try:
        mio_surface.build_mio_depth_cross_check(
            np.asarray((1.0e200, 1.0e200)),
            local_design=np.asarray((1.0e200, 1.0e200)),
            global_design=np.asarray((1.0e200, 1.0e200 + 2.0e185)),
            mask_path_id="oracle-mask",
        )
    except PillarSInferenceError as exc:
        assert "finite MIO diagnostic" in str(exc)
    else:
        raise AssertionError("public MIO non-finite counterexample was accepted")

    print(
        json.dumps(
            {
                "oracle": "A-PR286-R3-CLAIM-REPLACEMENT",
                "status": "PASS",
                "candidate_sha": head,
                "claims": {
                    "C-PR273-BLIND-INTEGRATION": "synthetic_diagnostic_only",
                    "C-PR274-DATA-ADMISSION": "no_admitted_data_vts14_blocked",
                },
                "terminal_counts": dict(sorted(terminal_counts.items())),
                "assurance_before_wave": "7/16",
                "pr287": "PLANNED_INELIGIBLE_0_OF_16",
                "merge_authority": "HUMAN_ONLY",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
