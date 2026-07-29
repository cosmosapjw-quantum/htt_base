#!/usr/bin/env python3
"""Independent numerical oracle for PR-257 orbit and counterpair contracts.

The public catalogue converts a ``DepartureState`` into twelve registered
polynomials.  This oracle independently evaluates those polynomials from
Cartesian matrices, checks the axial/polar O(3) action on random improper and
proper transformations, and verifies the three harmonic interventions from
their closed-form coefficient actions.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
for entry in (ROOT / "htt" / "src", ROOT / "htt"):
    text = str(entry)
    if text not in sys.path:
        sys.path.insert(0, text)

from common.orbit_catalogue_v2 import (  # noqa: E402
    OrbitCatalogueV2Spec,
    PR257_POLYNOMIAL_NAMES,
    PolynomialParity,
    orbit_catalogue_v2,
)
from common.orbit_nonlinearity import (  # noqa: E402
    DEPARTURE_O3_PARITY,
    O3Transform,
    STF5_CARTESIAN_BASIS,
    matrix_to_stf5,
    stf5_to_matrix,
    transform_departure_state,
)
from common.statistical_foundations import DepartureState  # noqa: E402
from obsstat.lowell_counterpairs import (  # noqa: E402
    CounterpairFactor,
    FeatureAvailability,
    InterventionOperator,
    LowEllInterventionSpec,
    MorphologyFeatureKind,
    apply_lowell_counterpair_intervention,
    build_lowell_morphology_feature_packet,
    register_morphology_feature,
)
from obsstat.lowell_poles import IMPLEMENTED_HARMONIC_CONVENTION  # noqa: E402


SEED = 20260729
CASES = 300
ATOL = 2.0e-10


def _receipt(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _catalogue() -> OrbitCatalogueV2Spec:
    return OrbitCatalogueV2Spec(
        catalog_id="PR257-ORACLE-CATALOGUE-V2",
        polynomial_names=PR257_POLYNOMIAL_NAMES,
        multiplicity_method="MAX_ABS_Z_FIXED_CATALOGUE_V1",
        alignment_null_id=_receipt("pr257-oracle-alignment-null"),
        preregistration_id=_receipt("pr257-oracle-preregistration"),
        cas_contract_id=_receipt("pr257-oracle-cas-contract"),
        syzygy_relative_tolerance=1.0e-10,
    )


def _state(
    sigma: np.ndarray,
    omega: np.ndarray,
    beta: np.ndarray,
) -> DepartureState:
    return DepartureState(
        sigma_ab=matrix_to_stf5(sigma),
        omega_a=tuple(float(value) for value in omega),
        beta_a=tuple(float(value) for value in beta),
        delta_omega_k=0.0,
        frame="PR257 oracle Cartesian frame",
        congruence="PR257 oracle synthetic congruence",
        epoch_window="PR257 oracle ell 2-3 window",
        averaging_scale="PR257 oracle unit scale",
        basis=STF5_CARTESIAN_BASIS,
        units="dimensionless",
        parity=DEPARTURE_O3_PARITY,
        perturbative_order="diagnostic finite polynomial state",
    )


def _direct_polynomials(
    sigma: np.ndarray,
    omega: np.ndarray,
    beta: np.ndarray,
) -> np.ndarray:
    sigma2 = sigma @ sigma
    columns = np.column_stack((beta, sigma @ beta, sigma2 @ beta))
    return np.asarray(
        (
            np.trace(sigma2),
            np.trace(sigma2 @ sigma),
            beta @ beta,
            beta @ sigma @ beta,
            beta @ sigma2 @ beta,
            np.linalg.det(columns),
            omega @ omega,
            omega @ sigma @ omega,
            omega @ sigma2 @ omega,
            beta @ omega,
            beta @ sigma @ omega,
            beta @ sigma2 @ omega,
        ),
        dtype=float,
    )


def _orthogonal(rng: np.random.Generator, *, improper: bool) -> np.ndarray:
    raw = rng.normal(size=(3, 3))
    q, _ = np.linalg.qr(raw)
    if (np.linalg.det(q) < 0.0) != improper:
        q[:, 0] *= -1.0
    return q


def _random_stf(rng: np.random.Generator) -> np.ndarray:
    raw = rng.normal(scale=0.5, size=(3, 3))
    symmetric = 0.5 * (raw + raw.T)
    return symmetric - np.trace(symmetric) * np.eye(3) / 3.0


def _oracle_extras():
    return (
        register_morphology_feature(
            kind=MorphologyFeatureKind.DIRECTIONAL_WAVELET,
            availability=FeatureAvailability.MISSING_FEATURE_PROVIDER,
            provider_id=_receipt("pr257-oracle-wavelet-missing"),
            units="not_available",
            missing_reason="oracle has no directional-wavelet provider",
        ),
        register_morphology_feature(
            kind=MorphologyFeatureKind.TEB_CROSS_MORPHOLOGY,
            availability=FeatureAvailability.MISSING_FEATURE_PROVIDER,
            provider_id=_receipt("pr257-oracle-teb-missing"),
            units="not_available",
            missing_reason="oracle has no spin-2 convention",
        ),
    )


def _alm_fixture() -> dict[tuple[int, int], complex]:
    result: dict[tuple[int, int], complex] = {}
    for ell in (2, 3):
        result[(ell, 0)] = complex(0.9 + 0.1 * ell, 0.0)
        for m in range(1, ell + 1):
            value = complex(0.3 * (ell + m), 0.11 * (ell - m + 1))
            result[(ell, m)] = value
            result[(ell, -m)] = ((-1) ** m) * value.conjugate()
    return result


def _direct_intervention(
    alm: dict[tuple[int, int], complex],
    *,
    factor: CounterpairFactor,
    angle: float | None,
) -> dict[tuple[int, int], complex]:
    output: dict[tuple[int, int], complex] = {}
    for (ell, m), value in alm.items():
        if factor is CounterpairFactor.PHASE:
            phase = np.exp(1j * math.copysign(m * m, m) * float(angle))
        elif factor is CounterpairFactor.ORIENTATION:
            phase = np.exp(-1j * m * float(angle))
        else:
            phase = complex((-1) ** ell, 0.0)
        output[(ell, m)] = complex(value * phase)
    return output


def _packet_alm(packet: object) -> dict[tuple[int, int], complex]:
    return {
        (int(ell), int(m)): complex(real, imag)
        for ell, m, real, imag in packet.alm_entries
    }


def _harmonic_oracle() -> float:
    reference = build_lowell_morphology_feature_packet(
        sample_id="PR257-ORACLE-REFERENCE",
        alm_by_lm=_alm_fixture(),
        ell_values=(2, 3),
        additional_features=_oracle_extras(),
        coordinate_frame="PR257 oracle Cartesian frame",
        harmonic_convention=IMPLEMENTED_HARMONIC_CONVENTION,
        anchor_id=_receipt("pr257-oracle-typed-anchor"),
        anchor_stress_interval=(0.6, 0.7),
        mask_id=_receipt("pr257-oracle-mask"),
        beam_id=_receipt("pr257-oracle-beam"),
        foreground_model_id=_receipt("pr257-oracle-foreground"),
    )
    maximum_error = 0.0
    for factor, operator, angle in (
        (
            CounterpairFactor.PHASE,
            InterventionOperator.NONLINEAR_M_PHASE_V1,
            0.37,
        ),
        (
            CounterpairFactor.ORIENTATION,
            InterventionOperator.COMMON_PROPER_Z_ROTATION_V1,
            0.41,
        ),
        (
            CounterpairFactor.PARITY,
            InterventionOperator.SCALAR_PARITY_V1,
            None,
        ),
    ):
        intervention = LowEllInterventionSpec(
            factor=factor,
            operator=operator,
            angle_radians=angle,
        )
        public = apply_lowell_counterpair_intervention(
            reference=reference,
            intervention=intervention,
            sample_id=f"PR257-ORACLE-{factor.value}",
            additional_features=_oracle_extras(),
        )
        direct = _direct_intervention(
            _packet_alm(reference),
            factor=factor,
            angle=angle,
        )
        public_alm = _packet_alm(public)
        for key, expected in direct.items():
            error = abs(public_alm[key] - expected)
            maximum_error = max(maximum_error, error)
            if error > ATOL:
                raise AssertionError(
                    f"{factor.value} {key} coefficient mismatch {error}"
                )
        for ell in (2, 3):
            before = sum(
                abs(value) ** 2
                for (shell, _), value in _packet_alm(reference).items()
                if shell == ell
            )
            after = sum(
                abs(value) ** 2
                for (shell, _), value in public_alm.items()
                if shell == ell
            )
            if not math.isclose(before, after, rel_tol=2.0e-13, abs_tol=0.0):
                raise AssertionError(
                    f"{factor.value} ell={ell} changed scalar power"
                )
        for (ell, m), value in public_alm.items():
            partner = public_alm[(ell, -m)]
            expected_partner = ((-1) ** m) * value.conjugate()
            if abs(partner - expected_partner) > ATOL:
                raise AssertionError(
                    f"{factor.value} violates real-field relation at {(ell, m)}"
                )
    return maximum_error


def _check_frozen_artifact() -> None:
    path = (
        ROOT
        / "docs/generated/pr257_lowell_morphology/"
        "morphology_benchmark.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload["status"] != "PASS":
        raise AssertionError("frozen benchmark status is not PASS")
    for flag in (
        "pr151_data_used",
        "old_rust_science_output_used",
        "native_solver_used",
        "observational_validation",
    ):
        if payload[flag] is not False:
            raise AssertionError(f"frozen benchmark provenance flag {flag} changed")
    if payload["transfer_source"] != "none":
        raise AssertionError("frozen benchmark imported a transfer provider")


def main() -> int:
    rng = np.random.default_rng(SEED)
    catalogue = _catalogue()
    maximum_value_error = 0.0
    maximum_transform_error = 0.0
    maximum_ch_error = 0.0
    for case in range(CASES):
        sigma = _random_stf(rng)
        omega = rng.normal(size=3)
        beta = rng.normal(size=3)
        state = _state(sigma, omega, beta)
        report = orbit_catalogue_v2(state, catalogue)
        direct = _direct_polynomials(sigma, omega, beta)
        value_error = float(
            np.max(np.abs(np.asarray(report.polynomial_values) - direct))
        )
        maximum_value_error = max(maximum_value_error, value_error)
        if not np.allclose(
            report.polynomial_values,
            direct,
            rtol=2.0e-11,
            atol=2.0e-11,
        ):
            raise AssertionError(f"case {case}: polynomial mismatch")

        improper = bool(case % 2)
        matrix = _orthogonal(rng, improper=improper)
        transform = O3Transform(
            matrix=tuple(tuple(float(value) for value in row) for row in matrix),
            transform_id=f"PR257-ORACLE-O3-{case}",
            coordinate_frame=state.frame,
        )
        transformed_state = transform_departure_state(state, transform)
        transformed_sigma = matrix @ sigma @ matrix.T
        transformed_beta = matrix @ beta
        transformed_omega = np.linalg.det(matrix) * matrix @ omega
        transform_error = max(
            float(
                np.max(
                    np.abs(
                        stf5_to_matrix(transformed_state.sigma_ab)
                        - transformed_sigma
                    )
                )
            ),
            float(
                np.max(
                    np.abs(
                        np.asarray(transformed_state.beta_a)
                        - transformed_beta
                    )
                )
            ),
            float(
                np.max(
                    np.abs(
                        np.asarray(transformed_state.omega_a)
                        - transformed_omega
                    )
                )
            ),
        )
        maximum_transform_error = max(
            maximum_transform_error,
            transform_error,
        )
        if transform_error > ATOL:
            raise AssertionError(f"case {case}: O(3) state action mismatch")
        transformed_report = orbit_catalogue_v2(
            transformed_state,
            catalogue,
        )
        parity_sign = -1.0 if improper else 1.0
        expected_values = np.asarray(
            [
                value
                if parity is PolynomialParity.EVEN
                else parity_sign * value
                for value, parity in zip(
                    report.polynomial_values,
                    report.parity,
                    strict=True,
                )
            ]
        )
        if not np.allclose(
            transformed_report.polynomial_values,
            expected_values,
            rtol=2.0e-10,
            atol=2.0e-10,
        ):
            raise AssertionError(f"case {case}: scalar/pseudoscalar parity mismatch")

        sigma2 = sigma @ sigma
        sigma3 = sigma2 @ sigma
        ch = (
            sigma3
            - 0.5 * np.trace(sigma2) * sigma
            - np.trace(sigma3) * np.eye(3) / 3.0
        )
        ch_error = float(np.linalg.norm(ch, ord="fro"))
        maximum_ch_error = max(maximum_ch_error, ch_error)
        if ch_error > ATOL:
            raise AssertionError(f"case {case}: Cayley-Hamilton residual")

    sigma = np.diag((1.0, 2.0, -3.0))
    beta = np.asarray((1.0, 1.0, 1.0))
    omega = np.asarray((1.0, 2.0, 3.0))
    fixed = _direct_polynomials(sigma, omega, beta)
    expected = {
        "det_beta_sigma_beta_sigma2_beta": 20.0,
        "beta_dot_omega": 6.0,
        "beta_sigma_omega": -4.0,
        "beta_sigma2_omega": 36.0,
    }
    by_name = dict(zip(PR257_POLYNOMIAL_NAMES, fixed, strict=True))
    for name, value in expected.items():
        if not math.isclose(by_name[name], value, abs_tol=ATOL, rel_tol=0.0):
            raise AssertionError(f"fixed exact witness {name} drifted")

    positive = _direct_polynomials(
        sigma,
        np.asarray((1.0, 2.0, 3.0)),
        np.zeros(3),
    )
    negative = _direct_polynomials(
        sigma,
        np.asarray((-1.0, -2.0, -3.0)),
        np.zeros(3),
    )
    if not np.array_equal(positive, negative):
        raise AssertionError("registered nongeneric non-separation witness drifted")

    harmonic_error = _harmonic_oracle()
    _check_frozen_artifact()
    print(
        "PASS PR-257 independent morphology oracle "
        f"cases={CASES} "
        f"max_value_error={maximum_value_error:.3e} "
        f"max_transform_error={maximum_transform_error:.3e} "
        f"max_ch_error={maximum_ch_error:.3e} "
        f"max_harmonic_error={harmonic_error:.3e}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
