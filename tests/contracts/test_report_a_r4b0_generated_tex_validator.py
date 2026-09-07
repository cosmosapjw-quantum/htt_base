from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate_report_a_generated_tex.py"


def load_module():
    spec = importlib.util.spec_from_file_location("report_a_tex_validator", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def good_tex(claim_ids: list[str]) -> str:
    return "\n".join(
        [
            r"\title{Tensorized Low-Multipole CMB Inference}",
            r"\section*{Abstract}",
            r"\section{Scope, authority, and supersession}",
            *claim_ids,
            "CURRENT_CORRECTED_TENSORIZED_PLANCK_RANK = NONE",
            "PLANCK_OR_FFP10_EXECUTION = DEFERRED_BY_OWNER",
            "FINITE_HEALPIX_CONTAINMENT = RANK_UNRESOLVED",
            r"\appendix",
            r"\section{Canonical claim map}",
            r"\section*{References}",
        ]
    )


def test_generated_tex_validator_accepts_a_clean_30_claim_artifact():
    module = load_module()
    ids = [f"RA-TEST-{index:03d}" for index in range(30)]
    result = module.validate_generated_tex(good_tex(ids), ids)
    assert result["claim_count"] == 30
    assert result["missing_claim_count"] == 0
    assert result["control_plane_prologue_removed"] is True
    assert result["scientific_boundary_statements_preserved"] is True


@pytest.mark.parametrize(
    "mutation, expected",
    [
        ("CURRENT_OBSERVATIONAL_RESULT = NONE", "forbidden fragment"),
        ("R3 flattened draft", "forbidden fragment"),
        ("[@MES_1995_LIMITS]", "forbidden fragment"),
        (r"\section{1. Scope}", "manual numeric section prefix"),
        (r"\appendix", "appendix mode exactly once"),
    ],
)
def test_generated_tex_validator_rejects_control_and_structure_mutations(
    mutation: str, expected: str
):
    module = load_module()
    ids = ["RA-TEST-001"]
    text = good_tex(ids) + "\n" + mutation
    with pytest.raises(module.GeneratedTexValidationError, match=expected):
        module.validate_generated_tex(text, ids)


def test_generated_tex_validator_rejects_a_missing_canonical_claim():
    module = load_module()
    ids = ["RA-TEST-001", "RA-TEST-002"]
    text = good_tex(ids).replace("RA-TEST-002", "")
    with pytest.raises(module.GeneratedTexValidationError, match="omits canonical claims"):
        module.validate_generated_tex(text, ids)
