"""V5 Round-17 P3.5 PR-V0d-pre1 — regression for ``tau_c`` parameter behaviour.

These tests pin the API contract introduced when
``htt/bass/perturbation/regular_adiabatic_ic.py::_seed_formulae`` gained
the ``tau_c: float | None`` keyword (2026-04-27, post-Round-17 audit).

Audit Round-17 V0d demonstrated that the legacy ``_approx_tau_c``
heuristic (``0.15 · η_init / √a_init``) overestimates radiation-era
photon-Thomson scattering time by ~100-1000× and produces a 23-orders-
of-magnitude D_2 explosion when η_init is shrunk from 261 → 50 Mpc.
The heuristic is retained as a fallback for backward compatibility,
but production callers (``ver2_native_integrator.py``) now pass a real
``tau_c = 1 / Γ_T(η_init)`` from the species table.
"""
from __future__ import annotations

import numpy as np
import pytest

# Import bass.hierarchy.ic first to break a circular import:
# regular_adiabatic_ic → collision → hierarchy → seed_compatibility →
# regular_adiabatic_ic. The same workaround appears in
# `test_fb53_regular_adiabatic_ic_skeleton.py`.
from bass.hierarchy.ic import zero_IC  # noqa: F401
from bass.perturbation.regular_adiabatic_ic import (
    _approx_tau_c,
    _seed_formulae,
    make_camb_regular_adiabatic_seed,
    regular_adiabatic_formulae,
)


# Reference setup: Planck-2018-like η_init = 261 Mpc, a ≈ 9.17e-4
# (z ≈ 1090 recombination), k = 0.01 Mpc⁻¹ inside Lowell-validity range.
ETA_INIT_REF = 261.0
A_INIT_REF = 9.17e-4
K_REF = 0.01


class TestTauCFallback:
    """The heuristic fallback path remains numerically identical to pre-PR."""

    def test_default_tau_c_uses_approx_tau_c(self) -> None:
        formulas = _seed_formulae(
            k_comoving=K_REF,
            eta_initial=ETA_INIT_REF,
            a_initial=A_INIT_REF,
        )
        expected_tau_c = _approx_tau_c(ETA_INIT_REF, A_INIT_REF)
        assert formulas["tau_c"] == pytest.approx(expected_tau_c, rel=1e-15)

    def test_explicit_none_uses_approx_tau_c(self) -> None:
        formulas = _seed_formulae(
            k_comoving=K_REF,
            eta_initial=ETA_INIT_REF,
            a_initial=A_INIT_REF,
            tau_c=None,
        )
        expected_tau_c = _approx_tau_c(ETA_INIT_REF, A_INIT_REF)
        assert formulas["tau_c"] == pytest.approx(expected_tau_c, rel=1e-15)


class TestTauCOverride:
    """Explicit ``tau_c`` is used directly; pi_gamma scales linearly with it."""

    def test_explicit_tau_c_propagates_to_dict(self) -> None:
        explicit_tau = 2.5
        formulas = _seed_formulae(
            k_comoving=K_REF,
            eta_initial=ETA_INIT_REF,
            a_initial=A_INIT_REF,
            tau_c=explicit_tau,
        )
        assert formulas["tau_c"] == pytest.approx(explicit_tau, rel=1e-15)

    def test_pi_gamma_scales_linearly_with_tau_c(self) -> None:
        formulas_low = _seed_formulae(
            k_comoving=K_REF,
            eta_initial=ETA_INIT_REF,
            a_initial=A_INIT_REF,
            tau_c=1.0,
        )
        formulas_high = _seed_formulae(
            k_comoving=K_REF,
            eta_initial=ETA_INIT_REF,
            a_initial=A_INIT_REF,
            tau_c=10.0,
        )
        ratio = formulas_high["pi_gamma"] / formulas_low["pi_gamma"]
        assert ratio == pytest.approx(10.0, rel=1e-12)

    def test_e2_scales_linearly_with_tau_c(self) -> None:
        formulas_low = _seed_formulae(
            k_comoving=K_REF,
            eta_initial=ETA_INIT_REF,
            a_initial=A_INIT_REF,
            tau_c=0.5,
        )
        formulas_high = _seed_formulae(
            k_comoving=K_REF,
            eta_initial=ETA_INIT_REF,
            a_initial=A_INIT_REF,
            tau_c=5.0,
        )
        ratio = formulas_high["E_2"] / formulas_low["E_2"]
        assert ratio == pytest.approx(10.0, rel=1e-12)

    def test_other_moments_unaffected_by_tau_c(self) -> None:
        formulas_low = _seed_formulae(
            k_comoving=K_REF,
            eta_initial=ETA_INIT_REF,
            a_initial=A_INIT_REF,
            tau_c=0.1,
        )
        formulas_high = _seed_formulae(
            k_comoving=K_REF,
            eta_initial=ETA_INIT_REF,
            a_initial=A_INIT_REF,
            tau_c=100.0,
        )
        for key in (
            "delta_gamma",
            "delta_b",
            "theta_gamma",
            "theta_nu",
            "pi_nu",
            "G_3",
            "Z",
            "eta_cov",
        ):
            assert formulas_high[key] == pytest.approx(
                formulas_low[key], rel=1e-15
            )


class TestTauCValidation:
    """Invalid ``tau_c`` values are rejected at the formula level."""

    @pytest.mark.parametrize("bad_val", [-1.0, 0.0, float("nan"), float("inf")])
    def test_non_positive_or_non_finite_tau_c_raises(self, bad_val: float) -> None:
        with pytest.raises(ValueError, match="tau_c must be finite and positive"):
            _seed_formulae(
                k_comoving=K_REF,
                eta_initial=ETA_INIT_REF,
                a_initial=A_INIT_REF,
                tau_c=bad_val,
            )


class TestPublicWrappers:
    """``regular_adiabatic_formulae`` and ``make_camb_regular_adiabatic_seed``
    correctly thread ``tau_c`` through to the underlying ``_seed_formulae``.
    """

    def test_regular_adiabatic_formulae_passes_tau_c(self) -> None:
        explicit_tau = 3.7
        formulas = regular_adiabatic_formulae(
            k_comoving=K_REF,
            eta_initial=ETA_INIT_REF,
            a_initial=A_INIT_REF,
            tau_c=explicit_tau,
        )
        assert formulas["tau_c"] == pytest.approx(explicit_tau, rel=1e-15)
        # And pi_gamma reflects the explicit value.
        ref = _seed_formulae(
            k_comoving=K_REF,
            eta_initial=ETA_INIT_REF,
            a_initial=A_INIT_REF,
            tau_c=explicit_tau,
        )
        assert formulas["pi_gamma"] == pytest.approx(ref["pi_gamma"], rel=1e-15)

    def test_regular_adiabatic_formulae_default_None_uses_heuristic(self) -> None:
        formulas = regular_adiabatic_formulae(
            k_comoving=K_REF,
            eta_initial=ETA_INIT_REF,
            a_initial=A_INIT_REF,
        )
        expected_tau_c = _approx_tau_c(ETA_INIT_REF, A_INIT_REF)
        assert formulas["tau_c"] == pytest.approx(expected_tau_c, rel=1e-15)

    def test_make_camb_regular_adiabatic_seed_with_tau_c(self) -> None:
        explicit_tau = 0.7
        seed_with = make_camb_regular_adiabatic_seed(
            k_comoving=K_REF,
            eta_initial=ETA_INIT_REF,
            a_initial=A_INIT_REF,
            L_max=4,
            b_k_sq=1.0,
            tau_c=explicit_tau,
        )
        seed_default = make_camb_regular_adiabatic_seed(
            k_comoving=K_REF,
            eta_initial=ETA_INIT_REF,
            a_initial=A_INIT_REF,
            L_max=4,
            b_k_sq=1.0,
        )
        assert seed_with.shape == seed_default.shape
        # The two seed vectors should differ (different pi_gamma → different
        # photon-T[ℓ=2] entry, and different E_2 → different photon-E[ℓ=2] entry).
        assert not np.allclose(seed_with, seed_default, rtol=1e-9, atol=0.0)


class TestHeuristicVsRealAtRecombination:
    """At η_init = 261 Mpc (recombination), the legacy heuristic over-estimates
    Γ_T-related quantities by ~600× — quantify the gap as a regression anchor.
    """

    def test_heuristic_overestimates_tau_c_at_recombination(self) -> None:
        # Heuristic at recombination
        heuristic_tau_c = _approx_tau_c(ETA_INIT_REF, A_INIT_REF)

        # Real radiation/recombination-era τ_c ≈ 1 / Γ_T at recombination
        # is ~ 2 Mpc (Γ_T ≈ 0.5 Mpc⁻¹). The heuristic gives ~ 1294 Mpc.
        # The exact ratio depends on the species background; here we just
        # pin the order-of-magnitude property.
        assert heuristic_tau_c > 100.0, (
            f"heuristic τ_c at recombination should be >> 100 Mpc but got "
            f"{heuristic_tau_c:.3f}"
        )
        # And the formulas built with an explicit small (physical) τ_c
        # produce a much smaller pi_gamma:
        formulas_real = _seed_formulae(
            k_comoving=K_REF,
            eta_initial=ETA_INIT_REF,
            a_initial=A_INIT_REF,
            tau_c=2.0,
        )
        formulas_heuristic = _seed_formulae(
            k_comoving=K_REF,
            eta_initial=ETA_INIT_REF,
            a_initial=A_INIT_REF,
            tau_c=None,  # uses heuristic
        )
        ratio = (
            abs(formulas_heuristic["pi_gamma"])
            / abs(formulas_real["pi_gamma"])
        )
        # Heuristic / real ≈ heuristic_tau_c / 2.0; expect ≫ 100
        assert ratio > 100.0, (
            f"heuristic pi_gamma / physical pi_gamma at recombination should "
            f"be >> 100 (heuristic over-estimates τ_c by ~600× at z=1090) "
            f"but got {ratio:.3f}"
        )
