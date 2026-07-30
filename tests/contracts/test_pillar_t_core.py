from __future__ import annotations

import copy
import hashlib
import math
import subprocess
import sys
from pathlib import Path
from typing import Callable

import numpy as np
import pytest
import yaml

from common.joint_anisotropy_state import (
    AccelerationNormalization,
    UnitsConvention,
)
from common.orbit_nonlinearity import matrix_to_stf5, stf5_to_matrix
from common.pillar_t_core_proofs import (
    REGISTRY_SHA256,
    REFERENCE_RESOLVED_LEGACY,
    SOURCE_HASHES,
    TF_ANALYTIC_IDS,
    VT_ANALYTIC_IDS,
    PillarTCoreProofError,
    ProofVerdict,
    convert_kinematic_normalizations,
    directional_polar_stress,
    euler_slaving_shape,
    evaluate_polar_axial_parity,
    factor_weighted_box_amplitude,
    factorized_budget_directional_derivative,
    linear_image_gauge,
    load_pillar_t_core_registry,
    polar_box_support,
    product_ball_gauge,
    weighted_box_gauge,
)
from common.tensor_foundations_oracle import (
    krylov_determinant,
    tf02_catalogue_completion,
)


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = (
    ROOT
    / "docs/research_program/vector_tensor/proofs/"
    "PILLAR_T_CORE_PROOFS_V1.yaml"
)
DERIVATION_PATH = (
    ROOT
    / "docs/research_program/vector_tensor/proofs/"
    "PR269_PILLAR_T_CORE.md"
)
V3_PATH = (
    ROOT
    / "docs/research_program/vector_tensor/THEOREM_SIGNATURES_V3.yaml"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _payload() -> dict:
    value = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _write_mutation(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "PILLAR_T_CORE_PROOFS_V1.yaml"
    path.write_text(
        yaml.safe_dump(
            payload,
            sort_keys=False,
            allow_unicode=True,
            width=96,
        ),
        encoding="utf-8",
    )
    return path


@pytest.fixture(scope="session")
def registry():
    return load_pillar_t_core_registry(ROOT)


def test_generated_registry_is_current() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/codex_harness/build_pr269_pillar_t_core.py",
            "--check",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert _sha256(REGISTRY_PATH) == REGISTRY_SHA256


def test_frozen_inputs_and_pr268_registry_remain_exact() -> None:
    for relative, expected in SOURCE_HASHES.items():
        assert _sha256(ROOT / relative) == expected
    v3 = yaml.safe_load(V3_PATH.read_text(encoding="utf-8"))
    assert v3["authority"] == "PR-268"
    assert v3["proof_adjudication_status"] == "NOT_ADJUDICATED"
    assert all(
        row["proof_adjudication_status"] == "NOT_ADJUDICATED"
        for group in v3["source_groups"].values()
        for row in group["entries"]
    )


def test_exact_analytic_core_selection_and_inventory(registry) -> None:
    assert len(registry.records) == 42
    assert {
        row.obligation_id
        for row in registry.records
        if row.obligation_id.startswith("VT-")
    } == VT_ANALYTIC_IDS
    assert {
        row.obligation_id
        for row in registry.records
        if row.obligation_id.startswith("TF-")
    } == TF_ANALYTIC_IDS
    assert all(row.claim_ceiling == "diagnostic_only" for row in registry.records)
    assert all(not row.counts_without_review for row in registry.records)


def test_legacy_t_inventory_is_exact(registry) -> None:
    legacy = tuple(
        row
        for row in registry.records
        if row.source_identity.kind == "legacy_signature_inventory"
    )
    assert len(legacy) == 31
    resolved = {
        row.obligation_id
        for row in legacy
        if row.verdict
        is ProofVerdict.REFERENCE_RESOLVED_NOT_READJUDICATED
    }
    assert resolved == REFERENCE_RESOLVED_LEGACY
    missing = tuple(
        row
        for row in legacy
        if row.verdict is ProofVerdict.INCONCLUSIVE_MISSING_SIGNATURE
    )
    assert len(missing) == 24
    assert all(not row.assumptions and not row.domain for row in missing)
    assert all(
        row.frame_convention == "SOURCE_NOT_TYPED"
        and row.branch_convention == "SOURCE_NOT_TYPED"
        for row in missing
    )


def test_proof_artifact_references_resolve(registry) -> None:
    derivation = DERIVATION_PATH.read_text(encoding="utf-8").lower()
    for row in registry.records:
        path, anchor = row.proof_artifact.split("#", 1)
        assert ROOT / path == DERIVATION_PATH
        assert f'id="{anchor}"' in derivation or f"## {anchor}" in derivation


def test_review_gate_and_raw_count_refusal(registry) -> None:
    assert registry.review_required
    assert not registry.accepted_for_rendering()
    with pytest.raises(TypeError):
        registry.accepted_for_rendering(  # type: ignore[call-arg]
            canonical_pr_status="completed",
            frozen_review_receipt_valid=True,
        )
    with pytest.raises(
        PillarTCoreProofError, match="not an accepted proof count"
    ):
        registry.reject_raw_proof_count(len(registry.records))


def test_statement_identity_mutation_is_refused(
    tmp_path: Path,
) -> None:
    payload = _payload()
    payload["records"][-1]["statement_identity_sha256"] = "0" * 64
    path = _write_mutation(tmp_path, payload)
    with pytest.raises(
        PillarTCoreProofError, match="typed statement identity drifted"
    ):
        load_pillar_t_core_registry(ROOT, path)


def test_missing_signature_premise_invention_is_refused(
    tmp_path: Path,
) -> None:
    payload = _payload()
    row = next(
        item
        for item in payload["records"]
        if item["verdict"] == "INCONCLUSIVE_MISSING_SIGNATURE"
    )
    row["assumptions"] = ["inferred from a source title"]
    path = _write_mutation(tmp_path, payload)
    with pytest.raises(
        PillarTCoreProofError, match="missing signature acquired"
    ):
        load_pillar_t_core_registry(ROOT, path)


def test_source_status_cannot_be_promoted_by_registry_mutation(
    tmp_path: Path,
) -> None:
    payload = _payload()
    row = next(
        item
        for item in payload["records"]
        if item["obligation_id"] == "SIG-P4"
    )
    row["verdict"] = "PROVED_ANALYTIC"
    path = _write_mutation(tmp_path, payload)
    with pytest.raises(PillarTCoreProofError):
        load_pillar_t_core_registry(ROOT, path)


def test_hostile_self_consistent_registry_mutations_are_refused(
    tmp_path: Path,
) -> None:
    attacks: list[tuple[str, Callable[[dict], None]]] = []

    def row(payload: dict, obligation_id: str) -> dict:
        return next(
            item
            for item in payload["records"]
            if item["obligation_id"] == obligation_id
        )

    # Use the exact canonical JSON identity algorithm after altering the
    # statement so these attacks exercise semantic/byte guards, not a stale
    # statement digest.
    def refresh_statement_digest(target: dict) -> None:
        import json

        target["statement_identity_sha256"] = hashlib.sha256(
            json.dumps(
                target["statement"],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

    def tf02_promotion(payload: dict) -> None:
        row(payload, "TF-02-CATALOGUE-COMPLETION")[
            "verdict"
        ] = "PROVED_ANALYTIC"

    def deferred_insertion(payload: dict) -> None:
        added = copy.deepcopy(row(payload, "VT-T4"))
        added["proof_id"] = "PR269-VT-T5"
        added["obligation_id"] = "VT-T5"
        payload["records"].append(added)

    def overread(obligation_id: str, text: str):
        def mutate(payload: dict) -> None:
            target = row(payload, obligation_id)
            target["statement"] += text
            refresh_statement_digest(target)

        return mutate

    attacks.extend(
        [
            ("tf02_verdict_promotion", tf02_promotion),
            ("deferred_vt_insertion", deferred_insertion),
            (
                "tf02_generic_overread",
                overread(
                    "TF-02-CATALOGUE-COMPLETION",
                    " Therefore all generic orbits are separated.",
                ),
            ),
            (
                "tf07_degree_overread",
                overread(
                    "TF-07-BUDGET-MORPHOLOGY-SPLIT",
                    " This proves degree-wide invariant completeness.",
                ),
            ),
            (
                "tf12_ceiling_overread",
                overread(
                    "TF-12-ACCELERATION-EULER-SLAVING",
                    " Hence the numerical MES ceiling is established.",
                ),
            ),
        ]
    )

    field_attacks = (
        (
            "source_identity_forgery",
            "TF-01-PARITY-TYPING",
            lambda target: target["source_identity"].__setitem__(
                "id", "FORGED-SOURCE"
            ),
        ),
        (
            "unrecorded_premise",
            "TF-08-PRODUCT-GAUGE-MAX",
            lambda target: target["assumptions"].append(
                "an unrecorded narrowing premise"
            ),
        ),
        (
            "frame_drift",
            "TF-12-ACCELERATION-EULER-SLAVING",
            lambda target: target.__setitem__(
                "frame_convention", "SILENT_DIFFERENT_FRAME"
            ),
        ),
        (
            "branch_drift",
            "TF-12-ACCELERATION-EULER-SLAVING",
            lambda target: target.__setitem__(
                "branch_convention", "SILENT_NATURAL_UNITS"
            ),
        ),
        (
            "domain_drift",
            "TF-12-ACCELERATION-EULER-SLAVING",
            lambda target: target.__setitem__(
                "domain", ["all finite fluid variables"]
            ),
        ),
        (
            "counterexample_erasure",
            "TF-12-ACCELERATION-EULER-SLAVING",
            lambda target: target.__setitem__(
                "counterexample_boundary", ["none"]
            ),
        ),
        (
            "proof_artifact_forgery",
            "VT-T1",
            lambda target: target.__setitem__(
                "proof_artifact", "docs/DOES_NOT_EXIST.md#forged"
            ),
        ),
        (
            "executable_evidence_forgery",
            "VT-T1",
            lambda target: target.__setitem__(
                "executable_evidence",
                ["tests/contracts/test_pillar_t_core.py::does_not_exist"],
            ),
        ),
        (
            "unnecessary_cas_insertion",
            "VT-T1",
            lambda target: target.__setitem__(
                "proof_method", "CAS self-report"
            ),
        ),
    )
    for name, obligation_id, mutation in field_attacks:
        def mutate(
            payload: dict,
            *,
            obligation_id: str = obligation_id,
            mutation=mutation,
        ) -> None:
            mutation(row(payload, obligation_id))

        attacks.append((name, mutate))

    def forbidden_claim(payload: dict) -> None:
        target = row(payload, "VT-T1")
        target["statement"] += " Bianchi family identified."
        refresh_statement_digest(target)

    def review_bypass(payload: dict) -> None:
        payload["registry_status"] = "ACCEPTED"
        payload["review_gate"]["rendering_rule"] = (
            "Caller boolean authorizes rendering."
        )

    attacks.extend(
        [
            ("forbidden_claim_language", forbidden_claim),
            ("review_gate_bypass", review_bypass),
        ]
    )

    for attack_name, mutate in attacks:
        payload = _payload()
        mutate(payload)
        path = _write_mutation(tmp_path, payload)
        with pytest.raises(PillarTCoreProofError) as refusal:
            load_pillar_t_core_registry(ROOT, path)
        assert str(refusal.value), attack_name


def test_vt_analytic_core_exact_vectors() -> None:
    sigma_hat = (1.0, 2.0, 0.5, -0.25, 0.75)
    omega_hat = (0.2, -0.4, 0.6)
    converted = convert_kinematic_normalizations(sigma_hat, omega_hat)
    sigma = stf5_to_matrix(sigma_hat)
    assert converted.sigma2 == pytest.approx(
        1.5 * float(np.einsum("ab,ab->", sigma, sigma))
    )
    assert converted.w2 == pytest.approx(
        3.0 * float(np.dot(omega_hat, omega_hat))
    )

    value = np.array([2.0, -3.0, 1.0])
    radii = np.array([1.0, 2.0, 4.0])
    gauge = weighted_box_gauge(value, radii)
    assert gauge == pytest.approx(2.0)
    assert polar_box_support(value, radii) == pytest.approx(gauge)
    phi = np.array([1.0, 0.0, 0.0])
    assert directional_polar_stress(value, phi, radii) <= gauge

    action = np.array(
        [[2.0, 1.0, 0.0], [0.0, 1.5, -0.5], [0.0, 0.0, 0.75]]
    )
    transformed = action @ value
    assert linear_image_gauge(
        transformed,
        action,
        lambda item: weighted_box_gauge(item, radii),
    ) == pytest.approx(gauge)

    reflection = np.diag([-1.0, 1.0, 1.0])
    parity = evaluate_polar_axial_parity(value, (0.5, 1.0, -2.0), reflection)
    assert parity.determinant == -1
    assert parity.polar_polar_after == pytest.approx(
        parity.polar_polar_before
    )
    assert parity.axial_axial_after == pytest.approx(
        parity.axial_axial_before
    )
    assert parity.polar_axial_after == pytest.approx(
        -parity.polar_axial_before
    )

    factorization = factor_weighted_box_amplitude(value, radii)
    assert factorization.amplitude == pytest.approx(gauge)
    assert factorization.normalized_gauge == pytest.approx(1.0)
    assert (
        factorization.amplitude
        * np.asarray(factorization.normalized_shape)
    ) == pytest.approx(value)


def test_vt_t1_rotation_covariance_and_scalar_convention() -> None:
    rng = np.random.default_rng(269)
    for _ in range(50):
        raw = rng.normal(size=(3, 3))
        q, _ = np.linalg.qr(raw)
        if np.linalg.det(q) < 0.0:
            q[:, 0] *= -1.0
        sigma_hat = tuple(rng.normal(size=5))
        omega_hat = rng.normal(size=3)
        before = convert_kinematic_normalizations(
            sigma_hat, tuple(omega_hat)
        )
        sigma_rotated = q @ stf5_to_matrix(sigma_hat) @ q.T
        after = convert_kinematic_normalizations(
            matrix_to_stf5(sigma_rotated), tuple(q @ omega_hat)
        )
        assert after.sigma2 == pytest.approx(before.sigma2, abs=1.0e-12)
        assert after.w2 == pytest.approx(before.w2, abs=1.0e-12)

    h = 2.0
    theta = 3.0 * h
    sigma = np.array(
        [[1.0, 0.2, 0.0], [0.2, -0.4, 0.1], [0.0, 0.1, -0.6]]
    )
    omega = np.array([0.4, -0.2, 0.3])
    converted = convert_kinematic_normalizations(
        matrix_to_stf5(sigma / theta), tuple(omega / theta)
    )
    assert converted.sigma2 == pytest.approx(
        float(np.einsum("ab,ab->", sigma, sigma)) / (6.0 * h * h)
    )
    assert converted.w2 == pytest.approx(
        float(omega @ omega) / (3.0 * h * h)
    )


def test_vt_gauge_metamorphic_cases() -> None:
    rng = np.random.default_rng(26902)
    for _ in range(100):
        value = rng.normal(size=4)
        radii = np.exp(rng.normal(size=4))
        matrix = rng.normal(size=(4, 4))
        matrix += 3.0 * np.eye(4)
        expected = weighted_box_gauge(value, radii)
        assert linear_image_gauge(
            matrix @ value,
            matrix,
            lambda item: weighted_box_gauge(item, radii),
        ) == pytest.approx(expected, abs=1.0e-11)
        assert polar_box_support(value, radii) == pytest.approx(expected)
        factorized = factor_weighted_box_amplitude(value, radii)
        assert factorized.normalized_gauge == pytest.approx(1.0)

    base = np.array([2.0, -3.0])
    for scale in (1.0e-8, 1.0e-4, 1.0, 1.0e4, 1.0e8):
        action = scale * np.eye(2)
        assert linear_image_gauge(
            action @ base,
            action,
            lambda item: float(np.linalg.norm(item)),
        ) == pytest.approx(float(np.linalg.norm(base)))


def test_vt_analytic_core_mutations_refuse() -> None:
    with pytest.raises(PillarTCoreProofError, match="invertible"):
        linear_image_gauge(
            (1.0, 2.0),
            ((1.0, 0.0), (0.0, 0.0)),
            lambda item: float(np.linalg.norm(item)),
        )
    with pytest.raises(PillarTCoreProofError, match="strictly positive"):
        weighted_box_gauge((1.0, 2.0), (1.0, 0.0))
    with pytest.raises(PillarTCoreProofError, match="outside"):
        directional_polar_stress((1.0, 2.0), (2.0, 0.0), (1.0, 1.0))
    with pytest.raises(PillarTCoreProofError, match="orthogonal"):
        evaluate_polar_axial_parity(
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            np.diag([2.0, 1.0, 1.0]),
        )
    with pytest.raises(PillarTCoreProofError, match="nonzero"):
        factor_weighted_box_amplitude((0.0, 0.0), (1.0, 1.0))


def test_tf_analytic_core_boundaries() -> None:
    sigma = np.diag([1.0, 2.0, -3.0])
    omega = np.array([1.0, 2.0, 3.0])
    reflection = np.diag([-1.0, 1.0, 1.0])
    sigma_reflected = reflection @ sigma @ reflection.T
    omega_reflected = -reflection @ omega
    assert krylov_determinant(
        sigma_reflected, omega_reflected
    ) == pytest.approx(krylov_determinant(sigma, omega))

    witness = tf02_catalogue_completion(seed=20260730)
    assert witness["ok"]
    assert witness["distinct_orbits"]
    assert witness["generic_orbit_separation_status"].startswith("UNPROVEN")
    assert witness["degree_completeness_status"].startswith("UNPROVEN")

    jacobian = np.array(
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [1.0, 1.0, 0.0]]
    )
    derivative = factorized_budget_directional_derivative(
        jacobian, (2.0, -1.0, 0.5), (0.0, 0.0, 7.0)
    )
    assert derivative == pytest.approx(0.0)

    sectors = ((3.0, 4.0), (0.0, 0.0, 6.0), (2.0,))
    radii = (10.0, 2.0, 4.0)
    assert product_ball_gauge(sectors, radii) == pytest.approx(3.0)

    shape = euler_slaving_shape(
        mu=1.0,
        w=0.25,
        sound_speed_squared=0.1,
        eps_g=0.03,
        theta=2.0,
        units_convention=UnitsConvention.C_EQUALS_ONE_THETA_NORMALIZED,
        acceleration_normalization=(
            AccelerationNormalization.A_OVER_THETA_C_EQUALS_ONE
        ),
    )
    expected = 1.5 * (0.1 / 1.25) ** 2 * 0.03**2
    assert shape.conditional_a2_shape_value == pytest.approx(expected)
    assert shape.normalized_acceleration_coefficient == pytest.approx(
        -0.1 / 1.25
    )
    assert (
        shape.acceleration_normalization
        is AccelerationNormalization.A_OVER_THETA_C_EQUALS_ONE
    )
    assert not shape.numerical_ceiling_authorized

    explicit_c = euler_slaving_shape(
        mu=1.0,
        w=0.25,
        sound_speed_squared=0.1,
        eps_g=0.03,
        theta=2.0,
        units_convention=UnitsConvention.EXPLICIT_C_THETA_NORMALIZED,
        acceleration_normalization=(
            AccelerationNormalization.A_OVER_C_THETA
        ),
        c_numeric_in_source_velocity_units=2.0,
    )
    assert explicit_c.normalized_acceleration_coefficient == pytest.approx(
        -0.1 / (2.0 * 1.25)
    )
    assert explicit_c.conditional_a2_shape_value == pytest.approx(
        expected / 4.0
    )


def test_tf_conditional_mutations_refuse() -> None:
    with pytest.raises(PillarTCoreProofError, match="strictly positive"):
        product_ball_gauge(((1.0,), (2.0,)), (1.0, 0.0))
    with pytest.raises(PillarTCoreProofError, match="mu"):
        euler_slaving_shape(
            mu=0.0,
            w=0.0,
            sound_speed_squared=0.1,
            eps_g=0.2,
            theta=1.0,
            units_convention=UnitsConvention.C_EQUALS_ONE_THETA_NORMALIZED,
            acceleration_normalization=(
                AccelerationNormalization.A_OVER_THETA_C_EQUALS_ONE
            ),
        )
    with pytest.raises(PillarTCoreProofError, match=r"1 \+ w"):
        euler_slaving_shape(
            mu=1.0,
            w=-1.0,
            sound_speed_squared=0.1,
            eps_g=0.2,
            theta=1.0,
            units_convention=UnitsConvention.C_EQUALS_ONE_THETA_NORMALIZED,
            acceleration_normalization=(
                AccelerationNormalization.A_OVER_THETA_C_EQUALS_ONE
            ),
        )
    with pytest.raises(PillarTCoreProofError, match="nonnegative"):
        euler_slaving_shape(
            mu=1.0,
            w=0.0,
            sound_speed_squared=0.1,
            eps_g=-0.2,
            theta=1.0,
            units_convention=UnitsConvention.C_EQUALS_ONE_THETA_NORMALIZED,
            acceleration_normalization=(
                AccelerationNormalization.A_OVER_THETA_C_EQUALS_ONE
            ),
        )
    with pytest.raises(PillarTCoreProofError, match="theta"):
        euler_slaving_shape(
            mu=1.0,
            w=0.0,
            sound_speed_squared=0.1,
            eps_g=0.2,
            theta=0.0,
            units_convention=UnitsConvention.C_EQUALS_ONE_THETA_NORMALIZED,
            acceleration_normalization=(
                AccelerationNormalization.A_OVER_THETA_C_EQUALS_ONE
            ),
        )
    with pytest.raises(PillarTCoreProofError, match="does not match"):
        euler_slaving_shape(
            mu=1.0,
            w=0.0,
            sound_speed_squared=0.1,
            eps_g=0.2,
            theta=1.0,
            units_convention=UnitsConvention.EXPLICIT_C_THETA_NORMALIZED,
            acceleration_normalization=(
                AccelerationNormalization.A_OVER_THETA_C_EQUALS_ONE
            ),
            c_numeric_in_source_velocity_units=2.0,
        )
    with pytest.raises(PillarTCoreProofError, match="requires a real"):
        euler_slaving_shape(
            mu=1.0,
            w=0.0,
            sound_speed_squared=0.1,
            eps_g=0.2,
            theta=1.0,
            units_convention=UnitsConvention.EXPLICIT_C_THETA_NORMALIZED,
            acceleration_normalization=(
                AccelerationNormalization.A_OVER_C_THETA
            ),
        )
    with pytest.raises(PillarTCoreProofError, match="strictly positive c"):
        euler_slaving_shape(
            mu=1.0,
            w=0.0,
            sound_speed_squared=0.1,
            eps_g=0.2,
            theta=1.0,
            units_convention=UnitsConvention.EXPLICIT_C_THETA_NORMALIZED,
            acceleration_normalization=(
                AccelerationNormalization.A_OVER_C_THETA
            ),
            c_numeric_in_source_velocity_units=0.0,
        )
    with pytest.raises(PillarTCoreProofError, match="exact numerical 1"):
        euler_slaving_shape(
            mu=1.0,
            w=0.0,
            sound_speed_squared=0.1,
            eps_g=0.2,
            theta=1.0,
            units_convention=UnitsConvention.C_EQUALS_ONE_THETA_NORMALIZED,
            acceleration_normalization=(
                AccelerationNormalization.A_OVER_THETA_C_EQUALS_ONE
            ),
            c_numeric_in_source_velocity_units=2.0,
        )


def test_no_deferred_or_cas_obligation_is_promoted(registry) -> None:
    forbidden = {
        "VT-T5",
        "VT-T6",
        "VT-T7",
        "VT-T8",
        "VT-T11",
        "VT-T12",
        "VT-T13",
        "VT-T14",
        "TF-03-KRYLOV-SYZYGY",
        "TF-04-CAYLEY-HAMILTON-REDUCTION",
        "TF-05-SHAPE-DISCRIMINANT",
        "TF-06-INVARIANT-DIMENSION",
        "TF-09-PARITY-SIGN-EXACTNESS",
        "TF-10-LOCAL-GLOBAL-SEPARATION",
        "TF-11-MASK-PATH-MARTINGALE",
    }
    assert forbidden.isdisjoint(
        {row.obligation_id for row in registry.records}
    )
    assert all("CAS" not in row.proof_method.upper() for row in registry.records)


def test_statement_boundaries_are_machine_visible(registry) -> None:
    vt3 = registry.record("VT-T3")
    assert any("balanced" in premise for premise in vt3.assumptions)
    vt4 = registry.record("VT-T4")
    assert "abs(phi(k))" in " ".join(vt4.assumptions)
    tf02 = registry.record("TF-02-CATALOGUE-COMPLETION")
    assert tf02.verdict is ProofVerdict.RESTRICTED_WITNESS_CONFIRMED
    assert "witness" in " ".join(tf02.domain).lower()
    tf08 = registry.record("TF-08-PRODUCT-GAUGE-MAX")
    assert any("strictly positive" in item for item in tf08.assumptions)
    tf12 = registry.record("TF-12-ACCELERATION-EULER-SLAVING")
    joined = " ".join(tf12.assumptions)
    assert "strictly positive" in joined
    assert "nonzero" in joined
    assert "Theta" in joined
    assert "EXPLICIT_C_OR_C_EQUALS_ONE" in tf12.branch_convention
    assert tf12.verdict is ProofVerdict.PROVED_CONDITIONAL_ANALYTIC


def test_finite_real_domain_refuses_nonfinite_vectors() -> None:
    with pytest.raises(PillarTCoreProofError, match="finite"):
        weighted_box_gauge((math.inf, 1.0), (1.0, 1.0))
    with pytest.raises(PillarTCoreProofError, match="finite"):
        product_ball_gauge(((1.0, math.nan),), (1.0,))
    with pytest.raises(PillarTCoreProofError, match="boolean"):
        weighted_box_gauge((True, 1.0), (1.0, 1.0))
    with pytest.raises(PillarTCoreProofError, match="non-empty"):
        weighted_box_gauge((), ())
