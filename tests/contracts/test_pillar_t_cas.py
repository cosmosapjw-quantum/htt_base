"""PR-270 four-axis CAS, conditional response, and refusal regressions."""

from __future__ import annotations

import copy
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / ".agent-harness/scripts"
if str(HARNESS) not in sys.path:
    sys.path.insert(0, str(HARNESS))

from cas_gate import _classify_wolfram_probe_failure  # noqa: E402
from publication_integrity import load_publication_policy  # noqa: E402
from common.pillar_t_cas import (  # noqa: E402
    AggregateCASVerdict,
    CAS_ADJUDICATION_PATH,
    CAS_CONTRACT_PATH,
    CAS_REGISTRY_PATH,
    EXACT_OBLIGATIONS,
    GeometryEscalationStatus,
    PROOF_IDS,
    REGISTERED_TF_ALIASES,
    PillarTCasError,
    PillarTStatementVerdict,
    REQUIRED_AXES,
    load_cas_adjudication,
    load_cas_contract,
    load_pillar_t_cas_registry,
    native_geometry_gate,
    principal_angle_separation,
    shape_chain_rule_core,
    supported_response_quotient,
)


CONTRACT_PATH = ROOT / CAS_CONTRACT_PATH
ADJUDICATION_PATH = ROOT / CAS_ADJUDICATION_PATH
REGISTRY_PATH = ROOT / CAS_REGISTRY_PATH
POLICY_PATH = (
    "docs/research_program/vector_tensor/pr270_publication_policy.json"
)
RUN_SPEC_PATH = (
    ROOT / "docs/research_program/vector_tensor/cas/CAS_RUN_SPEC.json"
)
AXIS_ROOT = (
    ROOT / "docs/research_program/vector_tensor/cas/axes"
)
CONTRACT_SHA256 = (
    "2d2ceb84603b24ab0b34db8b69715483061428ee36d6b2f5952494a9bb8108b4"
)
ADJUDICATION_SHA256 = (
    "a30a5597f0cc16786c4fcd4e689a6e5d0009387089f717205043152a439cf275"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _write_json(tmp_path: Path, name: str, payload: object) -> Path:
    path = tmp_path / name
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _write_yaml(tmp_path: Path, payload: object) -> Path:
    path = tmp_path / "PILLAR_T_CAS_PROOFS_V1.yaml"
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, width=100),
        encoding="utf-8",
    )
    return path


def test_contract_is_one_r3_four_axis_identity() -> None:
    contract = load_cas_contract(ROOT)
    assert contract.contract_id == "CAS-PR270-VECTOR-TENSOR-ORBIT-001"
    assert contract.sha256 == CONTRACT_SHA256
    assert contract.required_axes == REQUIRED_AXES
    assert contract.obligations == EXACT_OBLIGATIONS
    assert contract.claim_ceiling == "diagnostic_only"
    assert contract.exception_count == 0
    assert _sha256(CONTRACT_PATH) == CONTRACT_SHA256


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        (
            lambda value: value.update(risk_tier="R2"),
            "must remain R3",
        ),
        (
            lambda value: value["required_axes"].pop(),
            "required axes",
        ),
        (
            lambda value: value["target"]["exact_test_obligations"].reverse(),
            "obligations drifted",
        ),
        (
            lambda value: value["exceptions_adjudication"][
                "preregistered_exceptions"
            ].append({"axis": "wolfram_xact"}),
            "did not preregister",
        ),
    ],
)
def test_contract_mutations_fail_closed(
    tmp_path: Path,
    mutation,
    match: str,
) -> None:
    payload = copy.deepcopy(_json(CONTRACT_PATH))
    mutation(payload)
    with pytest.raises(PillarTCasError, match=match):
        load_cas_contract(
            ROOT,
            _write_json(tmp_path, "CAS_CONTRACT.json", payload),
        )


def test_adjudication_binds_four_runner_observed_passes() -> None:
    result = load_cas_adjudication(ROOT)
    assert result.aggregate_status is AggregateCASVerdict.CAS_4AXIS_PASS
    assert result.axis_statuses == {
        "wolfram_xact": "PASS",
        "sympy": "PASS",
        "sage_singular": "PASS",
        "lean": "PASS",
    }
    assert result.verification_state == "RUNNER_OBSERVED_EXECUTION"
    assert result.claim_promotion_cas_eligible is True
    assert result.claim_promotion_cas_requirement == "SATISFIED"
    assert result.success_dependency_satisfied is True
    assert _sha256(ADJUDICATION_PATH) == ADJUDICATION_SHA256


def test_majority_vote_and_false_execution_are_rejected(
    tmp_path: Path,
) -> None:
    payload = copy.deepcopy(_json(ADJUDICATION_PATH))
    payload["axis_statuses"]["wolfram_xact"] = (
        "BLOCKED_PLATFORM_OR_LICENSE"
    )
    payload["execution_evidence"]["wolfram_xact"]["derived_status"] = (
        "BLOCKED_PLATFORM_OR_LICENSE"
    )
    payload["execution_evidence"]["wolfram_xact"]["solver_executed"] = False
    with pytest.raises(PillarTCasError, match="blocked required axis"):
        load_cas_adjudication(
            ROOT,
            _write_json(tmp_path, "majority.json", payload),
        )

    payload = copy.deepcopy(_json(ADJUDICATION_PATH))
    payload["execution_evidence"]["wolfram_xact"]["solver_executed"] = False
    with pytest.raises(PillarTCasError, match="PASS requires solver execution"):
        load_cas_adjudication(
            ROOT,
            _write_json(tmp_path, "false-execution.json", payload),
        )


def test_missing_axis_or_posthoc_exception_is_rejected(
    tmp_path: Path,
) -> None:
    payload = copy.deepcopy(_json(ADJUDICATION_PATH))
    del payload["axis_statuses"]["lean"]
    with pytest.raises(PillarTCasError, match="cover each required axis"):
        load_cas_adjudication(
            ROOT,
            _write_json(tmp_path, "missing-axis.json", payload),
        )

    payload = copy.deepcopy(_json(ADJUDICATION_PATH))
    payload["exceptions_applied"] = [{"axis": "wolfram_xact"}]
    with pytest.raises(PillarTCasError, match="post-hoc"):
        load_cas_adjudication(
            ROOT,
            _write_json(tmp_path, "posthoc.json", payload),
        )


def test_unregistered_pass_with_exception_state_is_rejected(
    tmp_path: Path,
) -> None:
    payload = copy.deepcopy(_json(ADJUDICATION_PATH))
    payload["axis_statuses"]["wolfram_xact"] = (
        "NOT_APPLICABLE_COMPUTATION_CLASS"
    )
    payload["execution_evidence"]["wolfram_xact"]["derived_status"] = (
        "NOT_APPLICABLE_COMPUTATION_CLASS"
    )
    payload["aggregate_status"] = "CAS_PASS_WITH_REGISTERED_EXCEPTION"
    payload["claim_promotion_cas_eligible"] = False
    payload["claim_promotion_cas_requirement"] = "NOT_SATISFIED"
    with pytest.raises(PillarTCasError, match="preregistered no"):
        load_cas_adjudication(
            ROOT,
            _write_json(tmp_path, "unregistered-exception.json", payload),
        )


def _replace_stdout_payload(row: dict) -> None:
    row["stdout_tail"] = json.dumps(
        row["payload"], separators=(",", ":")
    ) + "\n"


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        (
            lambda row: row["payload"]["checks"].update(
                vt_t5_discriminant_identity=False
            ),
            "stored payload drifted",
        ),
        (
            lambda row: (
                row["payload"]["checks"].update(
                    vt_t5_discriminant_identity=False
                ),
                _replace_stdout_payload(row),
            ),
            "failed exact obligation",
        ),
        (
            lambda row: (
                row["payload"]["checks"].pop(
                    "vt_t5_discriminant_identity"
                ),
                _replace_stdout_payload(row),
            ),
            "exactly cover",
        ),
        (
            lambda row: (
                row["payload"]["computed"].update(principal_I2="9"),
                _replace_stdout_payload(row),
            ),
            "expected exact values",
        ),
        (
            lambda row: (
                row["payload"].update(
                    domain_assumption_diff=["complex branch"]
                ),
                _replace_stdout_payload(row),
            ),
            "assumption/domain difference",
        ),
        (
            lambda row: (
                row["payload"].update(
                    counterexample={"kind": "exact witness"}
                ),
                _replace_stdout_payload(row),
            ),
            "counterexample",
        ),
        (
            lambda row: row.update(exit_code=1),
            "exit_code zero",
        ),
        (
            lambda row: row.update(timed_out=True),
            "timed out",
        ),
        (
            lambda row: row["preflight_probe"].update(
                status="BLOCKED_PACKAGE_UNAVAILABLE"
            ),
            "PASS preflight",
        ),
        (
            lambda row: row.update(errors=["derived payload mismatch"]),
            "validation errors",
        ),
    ],
)
def test_pass_execution_payload_is_rederived_fail_closed(
    tmp_path: Path,
    mutation,
    match: str,
) -> None:
    payload = copy.deepcopy(_json(ADJUDICATION_PATH))
    mutation(payload["execution_evidence"]["wolfram_xact"])
    with pytest.raises(PillarTCasError, match=match):
        load_cas_adjudication(
            ROOT,
            _write_json(tmp_path, "contradictory-pass.json", payload),
        )


def test_wolfram_exit_255_activation_transcript_is_platform_blocker() -> None:
    transcript = (
        "Your Wolfram Engine installation is not activated or is "
        "experiencing a license-related problem. Please run wolframscript "
        "with the -activate option."
    )
    assert (
        _classify_wolfram_probe_failure(255, transcript)
        == "BLOCKED_PLATFORM_OR_LICENSE"
    )
    assert (
        _classify_wolfram_probe_failure(1, "Get::noopen: xAct not found")
        == "BLOCKED_PACKAGE_UNAVAILABLE"
    )


def test_repaired_axis_sources_preserve_declared_domains_and_coverage() -> None:
    sympy_source = (
        AXIS_ROOT / "sympy/axis_program.py"
    ).read_text(encoding="utf-8")
    assert 'q2 = sp.symbols("q2", nonzero=True)' in sympy_source
    assert (
        'q3, dq2, dq3 = sp.symbols("q3 dq2 dq3", real=True)'
        in sympy_source
    )

    lean_source = (
        AXIS_ROOT / "lean/PR270PillarTAxis.lean"
    ).read_text(encoding="utf-8")
    for token in (
        "import Mathlib",
        "0 < shearI2 l1 l2",
        "theorem cayleyHamiltonAllPowers",
        "theorem krylovCyclicIff",
        "def localChartJacobian",
        "theorem localChartJacobianFactor",
        "structure AxisProofBundle",
        "def axisProofBundle",
    ):
        assert token in lean_source
    assert "native_decide" not in lean_source
    assert "\naxiom " not in lean_source


def test_registry_is_additive_and_source_status_is_unchanged() -> None:
    records = load_pillar_t_cas_registry(ROOT)
    assert tuple(record.obligation_id for record in records) == PROOF_IDS
    by_id = {record.obligation_id: record for record in records}
    for theorem_id in ("VT-T5", "VT-T6", "VT-T7"):
        assert (
            by_id[theorem_id].verdict
            is PillarTStatementVerdict.PROVED_CAS4_EXACT
        )
    assert (
        by_id["VT-T8"].verdict
        is PillarTStatementVerdict.PROVED_CAS4_RESTRICTED_LOCAL_CHART
    )
    assert (
        by_id["VT-T11"].verdict
        is PillarTStatementVerdict.PROVED_CONDITIONAL_LINEAR_ALGEBRA
    )
    assert (
        by_id["VT-T12"].verdict
        is PillarTStatementVerdict.PROVED_CONDITIONAL_LINEAR_ALGEBRA
    )
    assert (
        by_id["VT-T13"].verdict
        is PillarTStatementVerdict.PARTIAL_CHAIN_RULE_CAS4
    )
    assert (
        by_id["VT-T14"].verdict
        is PillarTStatementVerdict.INCONCLUSIVE_NATIVE_GEOMETRY_GATE
    )
    assert all(record.claim_ceiling == "diagnostic_only" for record in records)
    source = _yaml(
        ROOT / "docs/research_program/vector_tensor/THEOREM_SIGNATURES_V3.yaml"
    )
    assert source["proof_adjudication_status"] == "NOT_ADJUDICATED"
    assert {
        record.obligation_id: record.tf_aliases for record in records
    } == REGISTERED_TF_ALIASES


def test_registry_binds_governing_spec_aliases_fail_closed(
    tmp_path: Path,
) -> None:
    spec = _yaml(ROOT / "docs/research_program/vector_tensor/pr270_spec.yaml")
    spec["selection"]["registered_tf_aliases"]["VT-T5"] = [
        "TF-06-INVARIANT-DIMENSION"
    ]
    spec_path = tmp_path / "pr270_spec.yaml"
    spec_path.write_text(
        yaml.safe_dump(spec, sort_keys=False, width=100),
        encoding="utf-8",
    )
    with pytest.raises(PillarTCasError, match="alias mapping drifted"):
        load_pillar_t_cas_registry(ROOT, spec_relative=spec_path)

    with pytest.raises(PillarTCasError, match="required file is missing"):
        load_pillar_t_cas_registry(
            ROOT, spec_relative=tmp_path / "missing-spec.yaml"
        )

    registry = copy.deepcopy(_yaml(REGISTRY_PATH))
    registry["records"][0]["tf_aliases"] = [
        "TF-06-INVARIANT-DIMENSION"
    ]
    with pytest.raises(PillarTCasError, match="registered TF aliases"):
        load_pillar_t_cas_registry(ROOT, _write_yaml(tmp_path, registry))


def test_registry_cannot_promote_blocked_or_native_statements(
    tmp_path: Path,
) -> None:
    payload = copy.deepcopy(_yaml(REGISTRY_PATH))
    payload["records"][0]["verdict"] = "PROVED_CONDITIONAL_LINEAR_ALGEBRA"
    with pytest.raises(
        PillarTCasError, match="violates the registered boundary"
    ):
        load_pillar_t_cas_registry(ROOT, _write_yaml(tmp_path, payload))

    payload = copy.deepcopy(_yaml(REGISTRY_PATH))
    payload["source_proof_adjudication_status"] = "PROVEN_CAS4"
    with pytest.raises(PillarTCasError, match="must not rewrite"):
        load_pillar_t_cas_registry(ROOT, _write_yaml(tmp_path, payload))


def test_supported_response_quotient_verifies_vt_t11() -> None:
    response = np.array(
        [
            [2.0, 1.0],
            [3.0, 0.0],
            [0.0, 4.0],
        ]
    )
    nuisance = np.array([[1.0], [0.0], [0.0]])
    report = supported_response_quotient(response, nuisance)
    assert np.allclose(
        report.nuisance_projector,
        np.diag([1.0, 0.0, 0.0]),
        rtol=0.0,
        atol=0.0,
    )
    assert np.allclose(
        report.quotient_response,
        [[0.0, 0.0], [3.0, 0.0], [0.0, 4.0]],
        rtol=0.0,
        atol=0.0,
    )
    assert report.nuisance_rank == 1
    assert report.response_rank == 2
    assert report.claim_ceiling == "diagnostic_only"


def test_supported_response_quotient_refuses_rank_and_shape_mutations() -> None:
    response = np.eye(3)
    with pytest.raises(PillarTCasError, match="full declared column rank"):
        supported_response_quotient(
            response,
            [[1.0, 2.0], [0.0, 0.0], [0.0, 0.0]],
        )
    with pytest.raises(PillarTCasError, match="row count"):
        supported_response_quotient(response, np.ones((2, 1)))
    with pytest.raises(PillarTCasError, match="finite"):
        supported_response_quotient(response, [[math.nan], [0.0], [0.0]])
    with pytest.raises(PillarTCasError, match="must not be boolean"):
        supported_response_quotient(response, [[1.0], [0.0], [0.0]], rtol=True)


def test_principal_angle_schur_identity_and_overlap_boundary() -> None:
    local = np.array([[1.0], [0.0], [0.0]])
    orthogonal = np.array([[0.0], [1.0], [0.0]])
    separated = principal_angle_separation(local, orthogonal)
    assert separated.principal_angles_radians == pytest.approx((math.pi / 2,))
    assert separated.schur_eigenvalues == pytest.approx((1.0,))
    assert separated.positive_definite is True
    assert separated.weak_identification is False

    overlap = principal_angle_separation(local, local)
    assert overlap.principal_angles_radians == pytest.approx((0.0,))
    assert overlap.schur_eigenvalues == pytest.approx((0.0,))
    assert overlap.positive_definite is False


def test_small_positive_angle_is_weak_not_rank_deficient() -> None:
    angle = 1.0e-3
    local = np.array([[1.0], [0.0]])
    global_ = np.array([[math.cos(angle)], [math.sin(angle)]])
    report = principal_angle_separation(
        local,
        global_,
        rtol=1.0e-14,
        weak_angle_threshold=1.0e-2,
    )
    assert report.positive_definite is True
    assert report.weak_identification is True
    assert report.schur_eigenvalues[0] == pytest.approx(math.sin(angle) ** 2)


def test_principal_angle_contract_refuses_nonorthonormal_inputs() -> None:
    with pytest.raises(PillarTCasError, match="orthonormal"):
        principal_angle_separation([[2.0], [0.0]], [[0.0], [1.0]])
    with pytest.raises(PillarTCasError, match="row count"):
        principal_angle_separation([[1.0], [0.0]], [[1.0], [0.0], [0.0]])
    with pytest.raises(PillarTCasError, match="finite real"):
        principal_angle_separation([[1.0], [0.0]], [[1j], [0.0]])


def test_shape_chain_rule_is_exact_and_zero_shear_refuses() -> None:
    assert shape_chain_rule_core(2, 3, 5, 7) == Fraction(-153, 8)
    assert shape_chain_rule_core(
        Fraction(2, 3),
        Fraction(1, 5),
        Fraction(7, 11),
        Fraction(-2, 13),
    ) == (
        12 * Fraction(2, 3) * Fraction(1, 5) * Fraction(-2, 13)
        - 18 * Fraction(1, 5) ** 2 * Fraction(7, 11)
    ) / Fraction(2, 3) ** 4
    with pytest.raises(PillarTCasError, match="I2=0"):
        shape_chain_rule_core(0, 1, 2, 3)


def test_native_geometry_gate_never_promotes_current_inputs() -> None:
    missing = native_geometry_gate(
        geometry_payload_admitted=False,
        native_morphology_atlas_admitted=False,
    )
    assert (
        missing.status
        is GeometryEscalationStatus.INCONCLUSIVE_NATIVE_GEOMETRY_GATE
    )
    assert len(missing.missing_requirements) == 2
    asserted = native_geometry_gate(
        geometry_payload_admitted=True,
        native_morphology_atlas_admitted=True,
    )
    assert (
        asserted.status
        is GeometryEscalationStatus.INCONCLUSIVE_NATIVE_GEOMETRY_GATE
    )
    assert asserted.missing_requirements == ()
    assert asserted.permitted_output == "partial kinematic diagnostic report"
    with pytest.raises(PillarTCasError, match="must be boolean"):
        native_geometry_gate(
            geometry_payload_admitted=1,
            native_morphology_atlas_admitted=False,
        )


@pytest.mark.parametrize(
    ("axis", "argv"),
    [
        (
            "wolfram_xact",
            (
                "wolframscript",
                "-file",
                str(AXIS_ROOT / "wolfram_xact/axis_program.wls"),
            ),
        ),
        (
            "sympy",
            (
                sys.executable,
                "-B",
                str(AXIS_ROOT / "sympy/axis_program.py"),
            ),
        ),
        (
            "sage_singular",
            (
                "sage",
                "-python",
                str(AXIS_ROOT / "sage_singular/axis_program.sage"),
            ),
        ),
        (
            "lean",
            (
                "sh",
                str(AXIS_ROOT / "lean/axis_program"),
            ),
        ),
    ],
)
def test_executable_axis_payloads_match_one_contract(
    axis: str,
    argv: tuple[str, ...],
) -> None:
    completed = subprocess.run(
        argv,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=360,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(completed.stdout)
    contract = load_cas_contract(ROOT)
    assert set(payload["checks"]) == set(contract.obligations)
    assert all(payload["checks"].values())
    assert payload["domain_assumption_diff"] == []
    assert payload["computed"] == contract.expected_exact_values
    assert payload["counterexample"] is None
    assert axis in load_cas_adjudication(ROOT).axis_statuses


def test_run_spec_is_portable_and_covers_exact_axes() -> None:
    payload = _json(RUN_SPEC_PATH)
    assert tuple(payload["axes"]) == REQUIRED_AXES
    assert payload["axes"]["sympy"]["argv"][0] == "python3"
    assert payload["axes"]["sage_singular"]["argv"][:2] == [
        "sage",
        "-python",
    ]
    assert payload["axes"]["lean"]["argv"][0] == "sh"
    assert payload["axes"]["wolfram_xact"]["argv"][0] == "wolframscript"
    assert all(
        Path(row["cwd"]) == Path(".") for row in payload["axes"].values()
    )


def test_publication_policy_wraps_expected_nonzero_cas_state() -> None:
    _, policy = load_publication_policy(ROOT, POLICY_PATH)
    commands = {
        row["id"]: row["argv"] for row in policy["required_commands"]
    }
    assert set(commands) == {
        "pr270-focused",
        "pr270-adjacent",
        "pr270-preflight",
        "pr270-adjudication-replay",
        "pr270-dag-strict",
        "pr270-claim-language",
        "pr270-research-surface-claim-lint",
        "pr270-smoke",
    }
    assert commands["pr270-preflight"] == [
        "{python}",
        "-B",
        "scripts/codex_harness/run_pr270_pillar_t_cas.py",
        "preflight",
    ]
    assert commands["pr270-adjudication-replay"][-1] == "adjudication"
    assert all(
        "allowed_exit_codes" not in row
        for row in policy["required_commands"]
    )


def test_proof_doc_marks_local_global_and_external_boundaries() -> None:
    text = (
        ROOT
        / "docs/research_program/vector_tensor/proofs/PR270_PILLAR_T_CAS.md"
    ).read_text(encoding="utf-8")
    assert "Status: `CAS_4AXIS_PASS`" in text
    assert "principal/cyclic chart result only" in text
    assert "global separation" in text
    assert "INCONCLUSIVE_MISSING_TYPED_EVOLUTION_LAW" in text
    assert "INCONCLUSIVE_NATIVE_GEOMETRY_GATE" in text
    assert "success dependency is true" in text
