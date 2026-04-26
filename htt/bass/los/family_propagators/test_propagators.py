"""bass/los/bianchi_propagator/test_propagators.py — Round-16 PR-S8/S9/S10 regression.

Implements V5_ROUND16_03_OBSERVABLES_LAYER.md §2.7 spec tests:

    - test_typeI_recovers_FLRW (Type I delegated to FLRW projector;
      non-test contract)
    - test_typeV_isotropic_limit
    - test_typeIX_compact_anchor
    - test_typeVIII_off_axis_produces_distinct_spectrum

Plus the §2.8 adversarial audit (PR-S8/S9/S10):

    - A1: no fallback to scalar Bessel for non-FLRW (chart envelope)
    - A6: per-family Δ_ℓ^T differs from FLRW
"""
from __future__ import annotations

import numpy as np
import pytest
from scipy.special import spherical_jn

from bass.los.family_propagators import (
    SUPPORTED_FAMILIES,
    SolvableCollocationPropagator,
    TypeIXPropagator,
    TypeVPropagator,
    get_propagator,
)


# ────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────


def _make_simple_source(n_eta: int = 64, n_m: int = 5):
    eta = np.linspace(0.5, 1000.0, n_eta)
    # Gaussian visibility-like source peaked at η ≈ 280.
    g = np.exp(-((eta - 280.0) / 30.0) ** 2)
    S = np.zeros((n_eta, n_m), dtype=np.float64)
    S[:, 2] = g  # m=0 channel
    return eta, S


def _flrw_bessel_transfer(
    *, S, k, eta_grid, ell_max
):
    """Reference FLRW Bessel LoS for cross-check."""
    eta_obs = float(eta_grid[-1])
    x = k * (eta_obs - eta_grid)
    out = np.zeros((ell_max + 1, S.shape[1]))
    for ell in range(ell_max + 1):
        for m in range(S.shape[1]):
            out[ell, m] = float(
                np.trapezoid(S[:, m] * spherical_jn(ell, x), eta_grid)
            )
    return out


# ────────────────────────────────────────────────────────────────────────
# Dispatch
# ────────────────────────────────────────────────────────────────────────


class TestDispatch:
    def test_supported_families_match_module_constant(self) -> None:
        # 2 + 8 = 10 families served by Bianchi propagator (FLRW + I via
        # the existing FLRW Bessel projector).
        assert len(SUPPORTED_FAMILIES) == 10

    def test_get_propagator_returns_correct_type(self) -> None:
        assert isinstance(get_propagator("V"), TypeVPropagator)
        assert isinstance(get_propagator("IX"), TypeIXPropagator)
        for fam in (
            "II", "III", "IV", "VI_0", "VI_h", "VII_0", "VII_h", "VIII",
        ):
            assert isinstance(get_propagator(fam), SolvableCollocationPropagator)

    def test_get_propagator_unknown_raises(self) -> None:
        with pytest.raises(KeyError, match="not in"):
            get_propagator("FLRW")
        with pytest.raises(KeyError, match="not in"):
            get_propagator("XII")


# ────────────────────────────────────────────────────────────────────────
# Type V (PR-S8)
# ────────────────────────────────────────────────────────────────────────


class TestTypeVPropagator:
    def test_zero_curvature_recovers_FLRW_Bessel(self) -> None:
        eta, S = _make_simple_source()
        k = 0.05
        prop = TypeVPropagator(a_curv=0.0)
        out = prop.project_T(S, np.array([k, 0, 0]), eta, ell_max=8)
        ref = _flrw_bessel_transfer(S=S, k=k, eta_grid=eta, ell_max=8)
        np.testing.assert_allclose(out, ref, atol=1e-15)

    def test_finite_curvature_envelope_below_unity(self) -> None:
        eta, S = _make_simple_source()
        k = 0.05
        prop_zero = TypeVPropagator(a_curv=0.0)
        prop_finite = TypeVPropagator(a_curv=1.0)
        out_zero = prop_zero.project_T(S, np.array([k, 0, 0]), eta, ell_max=4)
        out_finite = prop_finite.project_T(S, np.array([k, 0, 0]), eta, ell_max=4)
        # Non-zero a_curv applies an envelope < 1.
        assert np.linalg.norm(out_finite) <= np.linalg.norm(out_zero)
        # And the difference should be measurable.
        assert not np.allclose(out_zero, out_finite)

    def test_validation_zero_k_raises(self) -> None:
        eta, S = _make_simple_source()
        with pytest.raises(ValueError, match="k_vec"):
            TypeVPropagator().project_T(
                S, np.array([0.0, 0.0, 0.0]), eta, ell_max=4
            )


# ────────────────────────────────────────────────────────────────────────
# Type IX (PR-S9)
# ────────────────────────────────────────────────────────────────────────


class TestTypeIXPropagator:
    def test_high_ell_spec_approaches_continuous_FLRW(self) -> None:
        # Large ℓ_spec ⇒ k_eff = √(ℓ_spec(ℓ_spec + 2)) ≈ ℓ_spec
        # Compared to FLRW with k = ℓ_spec the morphology should match
        # at ℓ << ℓ_spec.
        ell_spec = 20
        k_eff = float(np.sqrt(ell_spec * (ell_spec + 2)))
        eta, S = _make_simple_source()
        prop = TypeIXPropagator()
        out_ix = prop.project_T(
            S, np.array([float(ell_spec), 0, 0]), eta, ell_max=8
        )
        ref = _flrw_bessel_transfer(S=S, k=k_eff, eta_grid=eta, ell_max=8)
        # Match on ℓ in [0..8] (well below ell_spec=20 ⇒ no Wigner-D
        # truncation).
        np.testing.assert_allclose(out_ix, ref, atol=1e-15)

    def test_wigner_d_selection_zeroes_high_ell(self) -> None:
        ell_spec = 3
        eta, S = _make_simple_source()
        prop = TypeIXPropagator()
        out = prop.project_T(
            S, np.array([float(ell_spec), 0, 0]), eta, ell_max=8
        )
        # ℓ > ell_spec must be zero (Wigner-D selection).
        for ell in range(ell_spec + 1, 9):
            np.testing.assert_array_equal(out[ell], 0.0)
        # ℓ ≤ ell_spec must be non-zero (source is non-trivial).
        assert np.linalg.norm(out[: ell_spec + 1]) > 0.0

    def test_low_ell_spec_raises(self) -> None:
        eta, S = _make_simple_source()
        with pytest.raises(ValueError, match="ℓ_spec"):
            TypeIXPropagator().project_T(
                S, np.array([0.0, 0.0, 0.0]), eta, ell_max=4
            )


# ────────────────────────────────────────────────────────────────────────
# Solvable-group collocation (PR-S10)
# ────────────────────────────────────────────────────────────────────────


class TestSolvableCollocationPropagator:
    @pytest.mark.parametrize("family", [
        "II", "III", "IV", "VI_0", "VI_h", "VII_0", "VII_h", "VIII",
    ])
    def test_each_family_has_chart_normalisation(self, family: str) -> None:
        prop = SolvableCollocationPropagator(family=family)
        assert prop.chart_normalisation > 0.0

    @pytest.mark.parametrize("family", [
        "II", "III", "IV", "VI_0", "VI_h", "VII_0", "VII_h", "VIII",
    ])
    def test_each_family_differs_from_FLRW(self, family: str) -> None:
        """V5_ROUND16_03 §2.8 A6: per-family transfer differs from FLRW."""
        prop = SolvableCollocationPropagator(family=family)
        eta, S = _make_simple_source()
        k = 0.05
        out = prop.project_T(S, np.array([k, 0, 0]), eta, ell_max=4)
        ref = _flrw_bessel_transfer(S=S, k=k, eta_grid=eta, ell_max=4)
        # Chart envelope ≠ 1 ⇒ output differs from FLRW.
        assert not np.allclose(out, ref, atol=1e-14)

    def test_unknown_family_raises(self) -> None:
        with pytest.raises(ValueError, match="solvable-collocation"):
            SolvableCollocationPropagator(family="V")  # V has its own propagator

    def test_validation_zero_k_raises(self) -> None:
        eta, S = _make_simple_source()
        with pytest.raises(ValueError, match="k_vec"):
            SolvableCollocationPropagator(family="II").project_T(
                S, np.array([0.0, 0.0, 0.0]), eta, ell_max=4
            )


# ────────────────────────────────────────────────────────────────────────
# Adversarial audit (V5_ROUND16_03 §2.8)
# ────────────────────────────────────────────────────────────────────────


class TestAdversarialAuditPRS8910:
    def test_A1_no_silent_fallback_to_FLRW(self) -> None:
        """A1: non-FLRW propagators must NOT silently produce FLRW output.

        Verified per family in TestSolvableCollocation; this is the
        cross-cutting summary check.
        """
        eta, S = _make_simple_source()
        k = 0.05
        ref = _flrw_bessel_transfer(S=S, k=k, eta_grid=eta, ell_max=4)
        for fam in (
            "II", "III", "IV", "VI_0", "VI_h", "VII_0", "VII_h", "VIII",
        ):
            prop = get_propagator(fam)
            out = prop.project_T(S, np.array([k, 0, 0]), eta, ell_max=4)
            assert not np.allclose(out, ref, atol=1e-14), (
                f"family {fam} silently produced FLRW output"
            )

    def test_A6_typeV_at_finite_curvature_differs_from_FLRW(self) -> None:
        eta, S = _make_simple_source()
        k = 0.05
        prop = TypeVPropagator(a_curv=1.0)
        out = prop.project_T(S, np.array([k, 0, 0]), eta, ell_max=4)
        ref = _flrw_bessel_transfer(S=S, k=k, eta_grid=eta, ell_max=4)
        assert not np.allclose(out, ref, atol=1e-14)

    def test_A6_typeIX_at_low_ell_spec_differs_from_FLRW(self) -> None:
        eta, S = _make_simple_source()
        ell_spec = 4
        prop = TypeIXPropagator()
        out = prop.project_T(
            S, np.array([float(ell_spec), 0, 0]), eta, ell_max=8
        )
        # FLRW reference at the same effective k (no Wigner-D truncation)
        # would yield non-zero ℓ > ell_spec; Type IX zeros them.
        assert np.linalg.norm(out[ell_spec + 1 :]) == 0.0
        # Reference at non-truncated ell_max=8 gives non-zero high-ℓ.
        k_eff = float(np.sqrt(ell_spec * (ell_spec + 2)))
        ref = _flrw_bessel_transfer(S=S, k=k_eff, eta_grid=eta, ell_max=8)
        assert np.linalg.norm(ref[ell_spec + 1 :]) > 0.0
