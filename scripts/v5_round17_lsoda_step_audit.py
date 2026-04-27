"""V5-RUNTIME Round-17 audit follow-up — LSODA step-count audit at deep TCA.

This is V0f in `docs/V5_ROUND17_AUDIT_VERDICT_AND_REVISED_PLAN.md §5.3`.
Direct response to the Round-17 audit finding (both reports + this
session's repo inspection) that the production FLRW path uses
`solve_ivp(method="LSODA")` rather than IMEX ARK4 with explicit/implicit
splitting. The relax-rate term `−a·Γ_T·(Π_2 − Π_2_alg)` from
`htt/bass/hierarchy/integrator.py:434-498` enters the unified RHS;
LSODA handles the stiffness via BDF mode automatically.

Open question. Is LSODA's BDF mode tractable across the 12-decade η
range that δ closure requires, or does the step count blow up such that
`imex_ark4.py` (currently a Round-16 primitive, NOT wired into the
production FLRW path) must be wired before δ?

Counter-test design.
  - Sweep η_init ∈ {261, 100, 30, 10, 3, 1, 0.3, 0.1, 0.03, 0.01,
    0.003, 0.001} Mpc.
  - For each, run a SHORT-RANGE integration over [η_init, η_init * 2]
    (just to avoid the full η_today range; we are auditing per-step
    cost density, not the full integration). Use `gamma_T_override`
    set to a synthetic deep-TCA value matched to the η_init redshift
    (`Γ_T ~ 1/τ_c` where τ_c ~ Hubble time at that z).
  - Record `solver_info.{nfev, njev, nlu, status, message}` and wall
    time. Compute "steps per Mpc" so different η ranges are comparable.

Predictions.
  - LSODA tractable: nfev/Δη scales sub-linearly with η_init⁻¹.
    Total nfev across the full δ range stays under ~10⁶.
  - LSODA blow-up: nfev/Δη scales like η_init⁻¹ or worse. Total nfev
    across δ exceeds ~10⁷ → impractical.

GO/NO-GO criterion. If δ-projected nfev > 10⁷, do NOT enter δ on the
LSODA path; wire `imex_ark4.py` first (~1-2 weeks of integration work).
If δ-projected nfev ≤ 10⁶, δ on LSODA is acceptable.

Wall time. ~1 h total — most runs 1-5 min each, a few may run longer.
The script applies a 600-second per-run timeout-equivalent by limiting
the integration interval.

Caveat. This script does NOT integrate to η_today; it only measures
step-cost density inside short windows that cover the deep-TCA regime
characteristic of each η_init anchor. The full δ integration would
chain these regions; if any of them shows blow-up, the chained run
would inherit it.

Usage::

    cd /home/cosmosapjw/Dropbox/bianchi/htt_base
    venv/bin/python scripts/v5_round17_lsoda_step_audit.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

_HTT_ROOT = Path(__file__).resolve().parents[1] / "htt"
_HTT_SRC = _HTT_ROOT / "src"
if _HTT_SRC.is_dir() and str(_HTT_SRC) not in sys.path:
    sys.path.insert(0, str(_HTT_SRC))
if str(_HTT_ROOT) not in sys.path:
    sys.path.insert(0, str(_HTT_ROOT))

import numpy as np

from bass.background.bianchi_types import get_type
from bass.background.einstein_bianchi import BianchiCosmology
from bass.hierarchy.integrator import (
    IntegratorConfig,
    LowellBianchiIntegrator,
)
from bass.species.registry import SpeciesBackgroundRegistry


# η_init anchors. Each one gets a short-range integration to audit
# step-cost density at that depth.
ETA_INIT_AUDITS_MPC = (
    261.0,
    100.0,
    30.0,
    10.0,
    3.0,
    1.0,
    0.3,
    0.1,
    0.03,
    0.01,
    0.003,
    0.001,
)


def _gamma_t_synthetic(eta_init_mpc: float) -> "callable":
    """Construct a deep-TCA `Γ_T(η)` synthetic.

    Models `Γ_T ∝ a^{-2}` (radiation-era Thomson scaling), normalized
    so that `Γ_T / H ~ 100` at η_init = 261 Mpc and grows ~1/η²
    smaller-η-wise. This is the auditing harness; the real production
    path uses the species registry's `Γ_T(η)`.

    The exact normalization isn't load-bearing for a step-count audit —
    only the order-of-magnitude `Γ_T / H` matters for the
    `combined_rhs` DAE-relaxation dispatch. We pick a value that puts
    every audit anchor deep above the threshold.
    """
    eta_ref = float(eta_init_mpc)

    def _gamma_T(eta: float) -> float:
        eta = max(float(eta), 1.0e-300)
        # Order-of-magnitude deep-TCA: Γ_T scales as 1/η^2 in radiation era.
        return 1.0e3 * (eta_ref / eta) ** 2

    return _gamma_T


def _audit_one(species, eta_init_mpc: float) -> dict:
    """Run a short-range integration starting at `eta_init_mpc` and
    return solver_info. Uses synthetic deep-TCA `Γ_T` to force the
    DAE-relaxation dispatch active throughout.
    """
    # Short-range: integrate from η_init to η_init × 1.5 OR up to 50 Mpc,
    # whichever is smaller. For very deep anchors (η_init = 0.001) the
    # 50% extension is `0.0005 Mpc` which is ample to measure step density.
    eta_final = min(eta_init_mpc * 1.5, 50.0)

    cfg = IntegratorConfig(
        L_max=8,
        eta_initial_mpc=float(eta_init_mpc),
        eta_final_mpc=float(eta_final),
        n_output=64,
        rtol=1.0e-6,
        atol=1.0e-9,
        bianchi_cosmo=BianchiCosmology(structure=get_type("I"), beta=0.0),
        gamma_T_over_H_threshold=100.0,
        solver_method="LSODA",
        gamma_T_override=_gamma_t_synthetic(eta_init_mpc),
        adiabatic_mode_seed=False,
    )

    integrator = LowellBianchiIntegrator(cfg, species)
    t0 = time.perf_counter()
    try:
        result = integrator.run()
        wall_s = time.perf_counter() - t0
        info = dict(result.solver_info)
        info.update(
            {
                "eta_init_mpc": eta_init_mpc,
                "eta_final_mpc": eta_final,
                "delta_eta_mpc": eta_final - eta_init_mpc,
                "wall_s": wall_s,
                "completed": True,
            }
        )
        if info["delta_eta_mpc"] > 0:
            info["nfev_per_mpc"] = info["nfev"] / info["delta_eta_mpc"]
        else:
            info["nfev_per_mpc"] = float("inf")
    except Exception as exc:  # noqa: BLE001
        wall_s = time.perf_counter() - t0
        info = {
            "eta_init_mpc": eta_init_mpc,
            "eta_final_mpc": eta_final,
            "delta_eta_mpc": eta_final - eta_init_mpc,
            "wall_s": wall_s,
            "completed": False,
            "error": f"{type(exc).__name__}: {exc}",
            "nfev": -1,
            "njev": -1,
            "nlu": -1,
            "nfev_per_mpc": float("nan"),
            "tca_tracker_any_active": False,
        }
    return info


def main() -> None:
    print("[t=0.0 min] V5 Round-17 V0f — LSODA step-count audit at deep TCA")
    print("            building Planck 2018 species registry...")
    t_start = time.perf_counter()

    species = SpeciesBackgroundRegistry.from_planck2018(
        recombination_warning_policy="ignore",
    )

    rows = []
    for eta_init in ETA_INIT_AUDITS_MPC:
        elapsed_min = (time.perf_counter() - t_start) / 60.0
        print(
            f"[t={elapsed_min:.1f} min] auditing η_init = {eta_init:.3e} Mpc "
            f"(short-range)..."
        )
        info = _audit_one(species, eta_init)
        rows.append(info)
        if info["completed"]:
            print(
                f"               nfev = {info['nfev']:>7d}  "
                f"njev = {info['njev']:>5d}  nlu = {info['nlu']:>5d}  "
                f"wall = {info['wall_s']:.1f} s  "
                f"TCA active = {info['tca_tracker_any_active']}"
            )
        else:
            print(f"               FAILED: {info['error']}")

    elapsed_min = (time.perf_counter() - t_start) / 60.0

    print()
    print("=" * 100)
    print("V5 Round-17 V0f — LSODA step-count audit RESULT TABLE")
    print("=" * 100)
    print(
        f"{'η_init [Mpc]':>14} {'Δη [Mpc]':>10} {'nfev':>8} {'njev':>6} "
        f"{'nlu':>6} {'nfev/Δη':>12} {'wall [s]':>10} {'TCA':>5}"
    )
    print("-" * 100)
    for r in rows:
        if r["completed"]:
            print(
                f"{r['eta_init_mpc']:>14.3e} "
                f"{r['delta_eta_mpc']:>10.3e} "
                f"{r['nfev']:>8d} {r['njev']:>6d} {r['nlu']:>6d} "
                f"{r['nfev_per_mpc']:>12.3e} {r['wall_s']:>10.2f} "
                f"{'Y' if r['tca_tracker_any_active'] else 'N':>5}"
            )
        else:
            print(
                f"{r['eta_init_mpc']:>14.3e} "
                f"{r['delta_eta_mpc']:>10.3e}   "
                f"(FAILED: {r.get('error', 'unknown')})"
            )
    print("=" * 100)
    print(f"Total wall time: {elapsed_min:.1f} min")
    print()

    # Project the δ-range nfev cost.
    completed = [r for r in rows if r["completed"] and np.isfinite(r["nfev_per_mpc"])]
    if completed:
        # Crude upper-bound projection: take the worst nfev/Δη density seen
        # and multiply by the full η-range each anchor would represent in
        # δ. The true δ run chains these together but with adaptive
        # step-size LSODA may share work; this projection is an upper
        # bound assuming no sharing.
        worst = max(completed, key=lambda r: r["nfev_per_mpc"])
        total_eta_today = 14147.0
        total_eta_init_target = 0.001
        projected_nfev = (
            worst["nfev_per_mpc"]
            * (total_eta_today - total_eta_init_target)
        )
        print(
            f"Worst nfev/Δη density: {worst['nfev_per_mpc']:.3e} at "
            f"η_init = {worst['eta_init_mpc']:.3e} Mpc."
        )
        print(
            f"Upper-bound projected δ nfev (η: 0.001 → 14147 Mpc): "
            f"{projected_nfev:.3e}"
        )
        if projected_nfev <= 1.0e6:
            print(
                "  >> LSODA path is TRACTABLE for δ. Proceed with the "
                "current production solver."
            )
        elif projected_nfev <= 1.0e7:
            print(
                "  >> LSODA path is MARGINAL. δ may run, but consider "
                "wiring imex_ark4.py before committing multi-month effort."
            )
        else:
            print(
                "  >> LSODA path is IMPRACTICAL for δ. Wire imex_ark4.py "
                "with proper f^I / f^E splitting BEFORE δ entry."
            )
    print()


if __name__ == "__main__":
    main()
