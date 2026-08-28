"""PMG-WU-006 metamorphic contracts for observer-space orbit morphology."""

from __future__ import annotations

import hashlib
from pathlib import Path
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "htt" / "src"
PACKAGE_ROOT = ROOT / "htt"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from common.observable_irrep_state import ObservableIrrepCarrier  # noqa: E402


def _apis():
    try:
        from obsstat import observable_irrep_orbit as orbit
        from obsstat import planck_lowell_irrep_projection as projection
    except ImportError as exc:
        pytest.fail(f"PMG-WU-006 orbit API is not implemented: {exc}", pytrace=False)
    return orbit, projection


def _sha(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("ascii")).hexdigest()


def _state_from_tensors(q_tensor: np.ndarray, o_tensor: np.ndarray):
    _, projection = _apis()
    carrier = np.zeros(32, dtype=float)
    carrier[:5] = projection.stf2_to_real_harmonic(q_tensor)
    carrier[5:12] = projection.stf3_to_real_harmonic(o_tensor)
    typed = ObservableIrrepCarrier(
        components=tuple(carrier),
        frame="GALACTIC",
        basis="ORTHONORMAL_CONDON_SHORTLEY_REAL_L2_L5_V1",
        units="microK_CMB",
        source_identity=_sha("synthetic-carrier"),
        operator_identity=_sha("synthetic-operator"),
        row_identity="SYNTHETIC-ROW",
    )
    return projection.project_planck_carrier_to_observable_irreps(typed)


def _generic_tensors() -> tuple[np.ndarray, np.ndarray]:
    _, projection = _apis()
    q = projection.stf2_components_to_tensor([1.2, -0.3, 0.4, -0.7, 0.2])
    o = projection.stf3_components_to_tensor(
        [0.7, -0.2, 0.5, -0.1, 0.3, 0.6, -0.4]
    )
    return q, o


def _values(report) -> dict[str, float]:
    return {
        coordinate.feature_id: coordinate.value
        for coordinate in report.coordinates
        if coordinate.status == "AVAILABLE"
    }


def test_registered_orbit_quantities_and_cayley_hamilton_identity() -> None:
    orbit, _ = _apis()
    q, o = _generic_tensors()
    report = orbit.observable_irrep_orbit_report(_state_from_tensors(q, o))
    values = _values(report)

    q2 = float(np.einsum("ij,ij->", q, q))
    q3 = float(np.trace(q @ q @ q))
    o2 = float(np.einsum("ijk,ijk->", o, o))
    assert values["q2"] == pytest.approx(q2)
    assert values["q3"] == pytest.approx(q3)
    assert values["J_Q"] == pytest.approx(np.sqrt(6.0) * q3 / q2**1.5)
    assert values["o2"] == pytest.approx(o2)
    assert -1.0 - 1.0e-13 <= values["J_Q"] <= 1.0 + 1.0e-13

    residual = q @ q @ q - 0.5 * q2 * q - (q3 / 3.0) * np.eye(3)
    assert np.linalg.norm(residual) <= 2.0e-14 * max(1.0, np.linalg.norm(q) ** 3)
    assert report.completeness_status == "GENERIC_GLOBAL_COMPLETENESS_UNPROVEN"
    assert report.claim_ceiling == "OBSERVER_SPACE_METHODS_DIAGNOSTIC"


def test_o3_invariance_and_pseudoscalar_parity() -> None:
    orbit, _ = _apis()
    q, o = _generic_tensors()
    baseline = _values(orbit.observable_irrep_orbit_report(_state_from_tensors(q, o)))
    rng = np.random.default_rng(417006)
    for determinant in (1.0, -1.0):
        raw = rng.normal(size=(3, 3))
        rotation, _ = np.linalg.qr(raw)
        if np.linalg.det(rotation) * determinant < 0.0:
            rotation[:, 0] *= -1.0
        q_rotated = np.einsum("ia,jb,ab->ij", rotation, rotation, q)
        o_rotated = np.einsum("ia,jb,kc,abc->ijk", rotation, rotation, rotation, o)
        transformed = _values(
            orbit.observable_irrep_orbit_report(
                _state_from_tensors(q_rotated, o_rotated)
            )
        )
        for feature_id, expected in baseline.items():
            if feature_id in {
                "Q_galactic_pole_power",
                "O_galactic_pole_power",
            }:
                continue
            if feature_id == "K_v_normalized":
                expected *= determinant
            assert transformed[feature_id] == pytest.approx(
                expected, rel=4.0e-12, abs=4.0e-12
            )


def test_positive_scale_behavior_preserves_normalized_shape() -> None:
    orbit, _ = _apis()
    q, o = _generic_tensors()
    baseline = _values(orbit.observable_irrep_orbit_report(_state_from_tensors(q, o)))
    scaled = _values(
        orbit.observable_irrep_orbit_report(_state_from_tensors(2.5 * q, 0.4 * o))
    )
    assert scaled["q2"] == pytest.approx(2.5**2 * baseline["q2"])
    assert scaled["q3"] == pytest.approx(2.5**3 * baseline["q3"])
    assert scaled["o2"] == pytest.approx(0.4**2 * baseline["o2"])
    for feature_id in orbit.NORMALIZED_SHAPE_FEATURE_IDS:
        assert scaled[feature_id] == pytest.approx(
            baseline[feature_id], rel=2.0e-12, abs=2.0e-12
        )


def test_zero_amplitude_returns_typed_absence_without_zero_fill() -> None:
    orbit, _ = _apis()
    q, o = _generic_tensors()
    q_zero = orbit.observable_irrep_orbit_report(_state_from_tensors(np.zeros((3, 3)), o))
    q_coordinates = {item.feature_id: item for item in q_zero.coordinates}
    assert q_coordinates["q2"].value == 0.0
    assert q_coordinates["J_Q"].status == "ABSENT"
    assert q_coordinates["J_Q"].value is None
    assert q_coordinates["J_Q"].stratum == "ZERO_Q_AMPLITUDE"
    assert q_coordinates["K_v_normalized"].status == "ABSENT"

    o_zero = orbit.observable_irrep_orbit_report(_state_from_tensors(q, np.zeros((3, 3, 3))))
    o_coordinates = {item.feature_id: item for item in o_zero.coordinates}
    assert o_coordinates["o2"].value == 0.0
    assert o_coordinates["R_v0_normalized"].value is None
    assert o_coordinates["R_v0_normalized"].stratum == "ZERO_O_AMPLITUDE"


def test_repeated_and_noncyclic_strata_have_typed_absence() -> None:
    orbit, projection = _apis()
    repeated_q = np.diag([1.0, 1.0, -2.0])
    _, generic_o = _generic_tensors()
    repeated = orbit.observable_irrep_orbit_report(
        _state_from_tensors(repeated_q, generic_o)
    )
    repeated_k = {item.feature_id: item for item in repeated.coordinates}[
        "K_v_normalized"
    ]
    assert repeated_k.status == "ABSENT"
    assert repeated_k.stratum == "REPEATED_Q_SPECTRUM"

    distinct_q = np.diag([1.0, 0.0, -1.0])
    eigenaxis_o = projection.stf3_components_to_tensor(
        [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    )
    noncyclic = orbit.observable_irrep_orbit_report(
        _state_from_tensors(distinct_q, eigenaxis_o)
    )
    dispositions = {item.feature_id: item for item in noncyclic.coordinates}
    assert dispositions["K_v_normalized"].status == "ABSENT"
    assert dispositions["K_v_normalized"].stratum in {
        "COINCIDENT_KRYLOV_DIRECTIONS",
        "NONCYCLIC_KRYLOV",
    }
    assert noncyclic.krylov_plane_status == "ABSENT"


def test_family_registries_are_frozen_and_orientation_is_separate() -> None:
    orbit, _ = _apis()
    assert orbit.FRAME_FREE_FAMILY_ID == "OBSERVABLE_IRREP_ORBIT_V1"
    assert orbit.FRAME_FREE_FEATURE_IDS == (
        "q2",
        "o2",
        "J_Q",
        "R_v0_normalized",
        "R_v1_normalized",
        "R_v2_normalized",
        "R_QS_normalized",
        "K_v_normalized",
    )
    assert orbit.FRAME_FREE_TAILS == (
        "two-sided",
        "two-sided",
        "two-sided",
        "upper",
        "two-sided",
        "upper",
        "two-sided",
        "two-sided",
    )
    assert orbit.GALACTIC_ORIENTATION_FEATURE_IDS[-2:] == (
        "Q_galactic_pole_power",
        "O_galactic_pole_power",
    )


def test_physical_or_family_inputs_are_refused_by_exact_type() -> None:
    orbit, _ = _apis()

    class PhysicalLookingState:
        family = "Bianchi_VIIh"
        shear = 1.0

    with pytest.raises(orbit.ObservableOrbitError, match="exact ObservableIrrepState"):
        orbit.observable_irrep_orbit_report(PhysicalLookingState())
