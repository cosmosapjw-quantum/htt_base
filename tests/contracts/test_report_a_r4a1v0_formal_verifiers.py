from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs" / "research_reports" / "verifiers" / "r4a1nf"
CONTRACT = BASE / "CAS_CONTRACT_R4A1NF_DOMAIN.json"
RUN_SPEC = BASE / "CAS_RUN_SPEC_R4A1NF_DOMAIN.json"
SOURCE_BINDER = BASE / "verify_source_bindings.py"
SYMPY_AXIS = BASE / "cas" / "axes" / "sympy" / "axis_program.py"
LEAN_AXIS = BASE / "cas" / "axes" / "lean" / "axis_program"
LEAN_MODULE = ROOT / "formal_mathlib" / "Egs3V8Mathlib" / "ReportAConvention.lean"
LEAN_ROOT = ROOT / "formal_mathlib" / "Egs3V8Mathlib.lean"
FORMAL_WORKFLOW = ROOT / ".github" / "workflows" / "report-a-formal-verifiers.yml"
PLAN = (
    ROOT
    / "docs"
    / "codex_handoff"
    / "htt_tensorized_report_first_20260903"
    / "R4A1NF_MULTI_CAS_VERIFICATION_PLAN.yaml"
)

OBLIGATIONS = {
    "photon_null_decomposition",
    "observer_measured_photon_energy",
    "boosted_observer_unit_timelike",
    "regularized_error_envelope_positive_definite",
}


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_r4a1v0_uses_a_canonical_r2_cas_contract_and_run_spec():
    contract = load_json(CONTRACT)
    run_spec = load_json(RUN_SPEC)

    assert contract["schema_version"] == 2
    assert contract["risk_tier"] == "R2"
    assert contract["required_axes"] == ["sympy", "lean"]
    assert contract["identity"]["contract_id"] == "CAS-R4A1NF-DOMAIN-R2"
    assert contract["identity"]["claim_ceiling"] == "SUPPORTING_DOMAIN_LEMMAS_ONLY"
    assert set(contract["identity"]["claim_ids"]) == OBLIGATIONS
    assert set(contract["target"]["exact_test_obligations"]) == OBLIGATIONS
    assert contract["exceptions_adjudication"]["preregistered_exceptions"] == []

    axes = run_spec["axes"]
    assert run_spec["schema_version"] == 1
    assert set(axes) == {"sympy", "lean"}
    assert axes["sympy"]["cwd"] == "."
    assert axes["lean"]["cwd"] == "."
    assert axes["sympy"]["argv"] != axes["lean"]["argv"]
    assert axes["sympy"]["argv"][-1].endswith("cas/axes/sympy/axis_program.py")
    assert axes["lean"]["argv"][-1].endswith("cas/axes/lean/axis_program")


def test_r4a1v0_axis_programs_match_the_runner_json_and_formal_scope():
    sympy_text = SYMPY_AXIS.read_text(encoding="utf-8")
    lean_axis_text = LEAN_AXIS.read_text(encoding="utf-8")
    lean_text = LEAN_MODULE.read_text(encoding="utf-8")
    lean_root_text = LEAN_ROOT.read_text(encoding="utf-8")

    for obligation in OBLIGATIONS:
        assert obligation in sympy_text
        assert obligation in lean_axis_text
    assert '"checks"' in sympy_text
    assert '"domain_assumption_diff"' in sympy_text
    assert '"counterexample"' in sympy_text
    assert "sp.ask" not in sympy_text

    assert "theorem regularized_error_envelope_posDef" in lean_text
    assert "Matrix.PosSemidef" in lean_text
    assert "Matrix.PosDef" in lean_text
    assert "lambdaReg ^ 2" in lean_text
    assert "sorry" not in lean_text
    assert "native_decide" not in lean_text
    assert "import Egs3V8Mathlib.ReportAConvention" in lean_root_text

    assert "formal_mathlib" in lean_axis_text
    assert "lake env lean" in lean_axis_text
    assert "-DwarningAsError=true" in lean_axis_text
    assert "R4A1NFConvention.lean" not in lean_axis_text


def test_r4a1v0_sympy_axis_proves_the_general_ordered_quadratic_form_step():
    text = SYMPY_AXIS.read_text(encoding="utf-8")
    assert "q_psd" in text
    assert "x_norm_sq" in text
    assert "nonnegative=True" in text
    assert "positive=True" in text
    assert "strict_regularizer" in text
    assert "q_psd.is_nonnegative is True" in text
    assert "x_norm_sq.is_positive is True" in text
    assert "general_ordered_posdef" in text
    assert '"nonzero_vector_assumption"' in text


def test_r4a1v0_contract_binds_inputs_run_spec_adjudicator_and_axis_sources():
    contract = load_json(CONTRACT)
    identity = contract["identity"]

    assert SOURCE_BINDER.is_file()
    assert identity["run_spec_hash"]["path"] == RUN_SPEC.relative_to(ROOT).as_posix()
    assert identity["adjudicator_hash"]["path"] == ".agent-harness/scripts/cas_gate.py"
    assert identity["binding_validator_hash"]["path"] == SOURCE_BINDER.relative_to(ROOT).as_posix()
    for row in (
        *identity["source_input_hashes"],
        identity["run_spec_hash"],
        identity["adjudicator_hash"],
        identity["binding_validator_hash"],
    ):
        assert row["hash_algorithm"] in {"git_blob_sha1", "sha256"}
        assert row["digest"]

    assert set(contract["axes"]) == {"sympy", "lean"}
    for axis in ("sympy", "lean"):
        rows = contract["axes"][axis]["source_hashes"]
        assert rows
        for row in rows:
            assert row["hash_algorithm"] in {"git_blob_sha1", "sha256"}
            assert row["digest"]

    binder_text = SOURCE_BINDER.read_text(encoding="utf-8")
    assert "git_blob_sha1" in binder_text
    assert "source_input_hashes" in binder_text
    assert "run_spec_hash" in binder_text
    assert "adjudicator_hash" in binder_text
    assert "binding_validator_hash" in binder_text
    assert "source_hashes" in binder_text
    assert "is_symlink" in binder_text


def test_r4a1v0_formal_workflow_executes_source_binding_then_parent_cas_gate():
    text = FORMAL_WORKFLOW.read_text(encoding="utf-8")
    binding_call = "verify_source_bindings.py"
    gate_call = ".agent-harness/scripts/cas_gate.py run-adjudicate"
    assert binding_call in text
    assert "CAS_SOURCE_BINDINGS_R4A1NF_DOMAIN.json" in text
    assert gate_call in text
    assert text.index(binding_call) < text.index(gate_call)
    assert "CAS_CONTRACT_R4A1NF_DOMAIN.json" in text
    assert "CAS_RUN_SPEC_R4A1NF_DOMAIN.json" in text
    assert "CAS_ADJUDICATION_R4A1NF_DOMAIN.json" in text
    assert "actions/upload-artifact" in text
    assert "sympy==1.14.0" in text
    assert "mpmath==1.3.0" in text
    assert "auto-config: false" in text
    assert "build: false" in text
    assert "build: true" not in text


def test_r4a1v0_plan_separates_required_and_supplemental_axes():
    text = PLAN.read_text(encoding="utf-8")
    assert "CAS-R4A1NF-DOMAIN-R2" in text
    assert "required_axes" in text
    assert "sympy" in text
    assert "lean" in text
    assert "supplemental" in text
    assert "gnu_octave" in text
    assert "sagemath" in text
    assert "singular" in text
    assert "Wolfram" in text or "wolfram" in text
