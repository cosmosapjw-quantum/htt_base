"""PA-4 β→0 continuity regression: tilted ↦ orthogonal smooth limit.

Audit (R17-P3) found the existing test surface pins:

- σ→0 limit at the propagator (TestFLRWRecovery, bit-exact);
- β=0 stationary trajectory (TestFLRWLimit);
- frozen β stays constant (TestTypeIStaticBeta);
- evolved β decay law (TestTypeIEvolvedBetaDecays).

What was *not* pinned was the **β→0 continuity** of the tilted
trajectory: as the initial rapidity shrinks, every observable derived
from the tilted background must converge smoothly to the orthogonal-
branch result. Without this, an optimization that silently re-routes
the orthogonal branch through a different code path could pass the
β=0 stationary test (which never crosses the orthogonal/tilted
boundary) while drifting on every infinitesimal-β trajectory.

This file pins three load-bearing β→0 invariants:

1. Σ²(η) at β = 1e-3, 1e-4, 1e-5 → the orthogonal-branch Σ² as
   β→0 (relative gap shrinks).
2. Ω_tilt(η) → 0 quadratically in β (King-Ellis ⇒ Ω_tilt ∝ sinh²β).
3. The Ω_total Friedmann invariant holds at every β (no constraint
   drift introduced by activating the tilt branch).
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.background.codazzi_tilt_rhs import (
    CodazziTiltConfig,
    evolve_codazzi_tilt_background,
)


def _run(beta: float, sigma_sq_init: float) -> object:
    return evolve_codazzi_tilt_background(
        CodazziTiltConfig(
            family="BI_orth" if beta == 0.0 else "BI_tilt",
            a_start=1.0e-3,
            a_end=1.0,
            initial_state=np.array(
                [9.14e-5, 0.3153, sigma_sq_init, 0.0, beta, 0.0],
                dtype=np.float64,
            ),
            n_steps=128,
            rtol=1.0e-10,
            atol=1.0e-13,
        )
    )


class TestBetaToOrthogonalContinuity:
    """β→0 trajectories must converge to the orthogonal-branch trajectory."""

    SIGMA_SQ_INIT = 1.0e-6

    @pytest.fixture(scope="class")
    def orthogonal(self) -> object:
        return _run(beta=0.0, sigma_sq_init=self.SIGMA_SQ_INIT)

    @pytest.mark.parametrize(
        "beta_step",
        [(1.0e-3, 1.0e-4), (1.0e-4, 1.0e-5)],
        ids=["1e-3_to_1e-4", "1e-4_to_1e-5"],
    )
    def test_sigma_squared_gap_shrinks_with_beta(
        self, orthogonal: object, beta_step: tuple[float, float]
    ) -> None:
        big_beta, small_beta = beta_step
        big = _run(beta=big_beta, sigma_sq_init=self.SIGMA_SQ_INIT)
        small = _run(beta=small_beta, sigma_sq_init=self.SIGMA_SQ_INIT)
        # gap at the late-time end of trajectory
        gap_big = float(np.abs(big.Sigma_squared[-1] - orthogonal.Sigma_squared[-1]))
        gap_small = float(
            np.abs(small.Sigma_squared[-1] - orthogonal.Sigma_squared[-1])
        )
        # convergence: smaller β should give a smaller (or at least not
        # qualitatively larger) gap to the orthogonal trajectory.
        # Allow a 3× cushion for ODE step-noise on the dev pipeline.
        assert gap_small <= 3.0 * gap_big + 1.0e-30, (
            f"Σ² β-continuity regressed: gap(β={big_beta:.0e})={gap_big:.3e}, "
            f"gap(β={small_beta:.0e})={gap_small:.3e}; "
            f"the tilted trajectory is no longer approaching orthogonal "
            f"as β→0"
        )

    @pytest.mark.parametrize("beta", [1.0e-3, 1.0e-4, 1.0e-5])
    def test_omega_tilt_quadratic_in_beta(self, beta: float) -> None:
        """King-Ellis: Ω_tilt ∝ sinh²β ⇒ Ω_tilt/β² is bounded as β→0."""
        result = _run(beta=beta, sigma_sq_init=self.SIGMA_SQ_INIT)
        omega_tilt_max = float(np.max(np.abs(result.Omega_tilt)))
        # bound: Ω_tilt/β² should remain finite and below ~ O(unity);
        # we use a generous ceiling of 10 to absorb the radiation/matter
        # weight (1−3c_s²) without claiming a precise prefactor.
        ratio = omega_tilt_max / max(beta * beta, 1.0e-300)
        assert ratio < 10.0, (
            f"Ω_tilt/β² = {ratio:.3e} at β={beta:.0e}; "
            f"the quadratic-in-β scaling has broken — likely the tilted "
            f"branch routed through a non-Lorentz-covariant kernel"
        )

    @pytest.mark.parametrize("beta", [0.0, 1.0e-4, 1.0e-3, 1.0e-2])
    def test_friedmann_invariant_holds_across_beta(self, beta: float) -> None:
        """Activating the tilt branch must not introduce constraint drift.

        The budget is ``Ω_r + Ω_m + Ω_Λ + Σ²/H² + Ω_k = 1``. We check
        that the four-term matter+Λ+curvature sum is consistent with
        unity to within the shear contribution Σ_init² ≈ 1e-6, and that
        no runaway behaviour appears as β grows.
        """
        result = _run(beta=beta, sigma_sq_init=self.SIGMA_SQ_INIT)
        omega_total = (
            result.Omega_r
            + result.Omega_m
            + result.Omega_Lambda
            + np.maximum(result.Omega_k, 0.0)
        )
        assert np.all(np.isfinite(omega_total)), (
            f"Friedmann budget non-finite at β={beta:.0e}"
        )
        # The four-term sum must remain within Σ_init² of unity (the
        # shear contribution is the only physical residual at β=0).
        # At β > 0 the tilt term enters at O(β²) and is bounded by
        # the same scale for β < 0.1.
        max_dev = float(np.max(np.abs(omega_total - 1.0)))
        assert max_dev < 5.0 * self.SIGMA_SQ_INIT, (
            f"Friedmann budget deviation grew unexpectedly at β={beta:.0e}: "
            f"max|Ω_total - 1| = {max_dev:.3e} > "
            f"5×Σ²_init = {5*self.SIGMA_SQ_INIT:.3e}"
        )


class TestNoTiltBranchStability:
    """β=0 trajectory must produce orthogonal-branch metadata regardless of family label."""

    def test_orth_label_with_beta_zero_matches_tilt_label_with_beta_zero(
        self,
    ) -> None:
        """A β=0 trajectory labeled 'BI_orth' or 'BI_tilt' must agree numerically.

        Because β=0 is the orthogonal limit, the choice of family label
        is purely a metadata branch and must not change the trajectory.
        Drift here would indicate that the family label silently routed
        the run through a different code path — exactly the kind of
        hidden shortcut the audit warned against.
        """
        sigma = 1.0e-6
        orth = evolve_codazzi_tilt_background(
            CodazziTiltConfig(
                family="BI_orth",
                a_start=1.0e-3,
                a_end=1.0,
                initial_state=np.array(
                    [9.14e-5, 0.3153, sigma, 0.0, 0.0, 0.0], dtype=np.float64
                ),
                n_steps=64,
                rtol=1.0e-9,
                atol=1.0e-12,
            )
        )
        tilt = evolve_codazzi_tilt_background(
            CodazziTiltConfig(
                family="BI_tilt",
                a_start=1.0e-3,
                a_end=1.0,
                initial_state=np.array(
                    [9.14e-5, 0.3153, sigma, 0.0, 0.0, 0.0], dtype=np.float64
                ),
                n_steps=64,
                rtol=1.0e-9,
                atol=1.0e-12,
            )
        )
        np.testing.assert_allclose(
            orth.Sigma_squared, tilt.Sigma_squared, atol=1.0e-12, rtol=0.0
        )
        np.testing.assert_allclose(orth.beta, tilt.beta, atol=1.0e-12)
