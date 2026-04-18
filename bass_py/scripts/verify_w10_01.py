"""
scripts/verify_w10_01.py
=========================

Independent physics verification of W10-01 C_ℓ assembly + Route B
sentinel. Runs outside pytest to serve as a redundant witness.

Eight verification blocks:

  1. Route B D_2(Σ²=1e-8) = 0.1741 μK² (formula identity)
  2. Primordial P_R(k) power-law shape (log-log slope = n_s - 1)
  3. Isotropic C_ℓ positivity, linearity in A_s
  4. Bianchi diagonal C_ℓ reduces to isotropic when m=±2=0 (bit-exact)
  5. C_ℓ^{BB} identically zero (Bianchi I)
  6. D_ℓ conversion formula identity (ℓ(ℓ+1) T_CMB² / 2π)
  7. Michaelis-Menten fitter recovers Route B (C1, C2) within 0.5%
  8. σ² scan produces monotonic D_2 in the linear regime
"""
from __future__ import annotations

import sys

import numpy as np
from scipy.special import spherical_jn

from bass.spectrum.cl_assembly import (
    ROUTE_B_C1, ROUTE_B_C2,
    CLAssemblyConfig,
    primordial_power_spectrum,
    assemble_cl_TT_isotropic, assemble_cl_TT_bianchi,
    assemble_cl_EE_isotropic, assemble_cl_BB_bianchi,
    compute_dl,
    route_b_d2_lookup,
    fit_michaelis_menten,
    sigma_squared_scan,
)
from bass.los.bianchi_propagator import BianchiTransferFunctions


# ============================================================================
# Helpers
# ============================================================================

def sw_transfer_factory(sigma_sq: float = 0.0, ell_max: int = 10):
    """Synthetic SW transfer with optional m=±2 activation."""
    A_m0 = 1.0e-5
    A_m2 = np.sqrt(max(sigma_sq, 0.0)) * 1.0e-3
    def _transfer(k: float) -> BianchiTransferFunctions:
        x = k * 280.0  # k · η_*
        jl = np.array([spherical_jn(ell, x) for ell in range(ell_max + 1)])
        return BianchiTransferFunctions(
            delta_T_m0=A_m0 * jl,
            delta_T_m_plus2=A_m2 * jl,
            delta_T_m_minus2=A_m2 * jl,
            delta_E_m0=np.zeros(ell_max + 1),
            delta_E_m_plus2=np.zeros(ell_max + 1),
            delta_E_m_minus2=np.zeros(ell_max + 1),
            delta_B_all_zero=np.zeros(ell_max + 1),
        )
    return _transfer


def separator(label: str):
    print("=" * 72)
    print(f"Block {label}")
    print("=" * 72)


results = []


def record(name: str, passed: bool, detail: str):
    results.append((name, passed, detail))
    marker = "[PASS]" if passed else "[FAIL]"
    print(f"  {marker} {name}   — {detail}")


# ============================================================================
# Block 1 — Route B sentinel D_2(Σ²=1e-8)
# ============================================================================

separator("1 — Route B D_2(Σ²=1e-8) = 0.174 μK² (formula identity)")

d2 = route_b_d2_lookup(1e-8)
expected_formula = 1.753e7 * 1e-8 / (1.0 + 6.825e5 * 1e-8)
record(
    "D_2 = C1·σ² / (1 + C2·σ²) at σ²=1e-8",
    d2 == expected_formula,
    f"D_2 = {d2:.6f} μK², formula = {expected_formula:.6f} μK², diff = {abs(d2 - expected_formula):.2e}",
)
record(
    "D_2 ≈ 0.1741 μK² (three sig figs match SSOT)",
    abs(d2 - 0.1741) < 1e-3,
    f"|D_2 - 0.1741| = {abs(d2 - 0.1741):.2e}",
)


# ============================================================================
# Block 2 — Primordial P_R(k) power-law shape
# ============================================================================

separator("2 — Primordial P_R(k) log-log slope = n_s - 1")

cfg = CLAssemblyConfig(ell_max=10)
k_arr = np.logspace(-4, -1, 20)
p_arr = primordial_power_spectrum(k_arr, cfg)
# Fit log-log slope
log_k = np.log(k_arr); log_p = np.log(p_arr)
slope, intercept = np.polyfit(log_k, log_p, 1)
expected_slope = cfg.n_s - 1.0
record(
    f"Slope = n_s - 1 = {expected_slope:.6f}",
    abs(slope - expected_slope) < 1e-12,
    f"Measured slope = {slope:.6f}, diff = {abs(slope - expected_slope):.2e}",
)
# P(k_pivot) = A_s exactly
p_pivot = primordial_power_spectrum(cfg.k_pivot_mpc, cfg)
record(
    "P(k_pivot) = A_s exactly",
    p_pivot == cfg.A_s,
    f"P(k_pivot) = {p_pivot:.6e}, A_s = {cfg.A_s:.6e}",
)


# ============================================================================
# Block 3 — Isotropic C_ℓ^{TT} positivity + A_s linearity
# ============================================================================

separator("3 — Isotropic C_ℓ^{TT}: positivity + A_s linearity")

xf = sw_transfer_factory(sigma_sq=0.0, ell_max=10)
cl_tt = assemble_cl_TT_isotropic(xf, cfg)
record(
    "C_ℓ^{TT} non-negative for all ℓ",
    np.min(cl_tt) >= 0.0,
    f"min C_ℓ = {np.min(cl_tt):.3e}, max C_ℓ = {np.max(cl_tt):.3e}",
)

cfg_2x = CLAssemblyConfig(ell_max=10, A_s=2 * cfg.A_s)
cl_tt_2x = assemble_cl_TT_isotropic(xf, cfg_2x)
ratios = cl_tt_2x[2:] / np.maximum(cl_tt[2:], 1e-300)
max_rel = float(np.max(np.abs(ratios - 2.0) / 2.0))
record(
    "2·A_s → 2·C_ℓ (linear weighting)",
    max_rel < 1e-13,
    f"worst |ratio - 2|/2 = {max_rel:.2e} across ℓ ∈ [2, 10]",
)


# ============================================================================
# Block 4 — Bianchi FLRW recovery (m=±2=0 → iso == bianchi)
# ============================================================================

separator("4 — Bianchi diagonal ≡ isotropic when m=±2 sources vanish")

xf_flrw_limit = sw_transfer_factory(sigma_sq=0.0, ell_max=10)
cl_iso = assemble_cl_TT_isotropic(xf_flrw_limit, cfg)
cl_bianchi = assemble_cl_TT_bianchi(xf_flrw_limit, cfg)
record(
    "C_ℓ^{TT,bianchi} == C_ℓ^{TT,iso} bit-exact",
    np.array_equal(cl_iso, cl_bianchi),
    f"max |diff| = {np.max(np.abs(cl_bianchi - cl_iso)):.2e}",
)


# ============================================================================
# Block 5 — C_ℓ^{BB} identically zero (Bianchi I)
# ============================================================================

separator("5 — C_ℓ^{BB} identically zero (Bianchi I, ψ'=0)")

# Even with m=±2 activated, BB assembler returns zeros
xf_active = sw_transfer_factory(sigma_sq=1e-4, ell_max=10)
cl_bb = assemble_cl_BB_bianchi(xf_active, cfg)
record(
    "C_ℓ^{BB} = 0 exactly across all ℓ",
    np.all(cl_bb == 0.0),
    f"max |C_ℓ^BB| = {np.max(np.abs(cl_bb)):.2e}",
)


# ============================================================================
# Block 6 — D_ℓ conversion formula identity
# ============================================================================

separator("6 — D_ℓ = ℓ(ℓ+1) C_ℓ T_CMB² / (2π) formula identity")

cl_unit = np.ones(5)
dl = compute_dl(cl_unit)
# D_2 = 2·3 · (2.7255e6)² / (2π) = 6/(2π) · (2.7255e6)²
expected_d2 = 2 * 3 / (2 * np.pi) * (2.7255e6) ** 2
record(
    "D_2(C=1) = 6 T_CMB² / (2π) exactly",
    abs(dl[2] - expected_d2) / expected_d2 < 1e-14,
    f"D_2 = {dl[2]:.6e}, expected = {expected_d2:.6e}, rel = {abs(dl[2] - expected_d2) / expected_d2:.2e}",
)
# Check T_CMB² scaling: T_CMB=2x → D_ℓ = 4x
dl_2x = compute_dl(cl_unit, T_CMB_K=2 * 2.7255)
ratio_2x = dl_2x[2] / dl[2]
record(
    "T_CMB doubling → D_ℓ × 4 (quadratic)",
    abs(ratio_2x - 4.0) < 1e-14,
    f"ratio = {ratio_2x:.10f}",
)


# ============================================================================
# Block 7 — Michaelis-Menten fitter recovers Route B parameters
# ============================================================================

separator("7 — M-M fitter recovers (C1, C2) from Route B samples")

sigma_arr = np.logspace(-10, -4, 8)
d_arr = route_b_d2_lookup(sigma_arr)
fit = fit_michaelis_menten(sigma_arr, d_arr, initial_guess=(1e7, 1e5))
c1_rel_err = abs(fit["C1"] - ROUTE_B_C1) / ROUTE_B_C1
c2_rel_err = abs(fit["C2"] - ROUTE_B_C2) / ROUTE_B_C2
record(
    "C1 recovery within 0.5%",
    c1_rel_err < 5e-3,
    f"fit C1 = {fit['C1']:.4e}, true = {ROUTE_B_C1:.4e}, rel = {c1_rel_err:.2e}",
)
record(
    "C2 recovery within 0.5%",
    c2_rel_err < 5e-3,
    f"fit C2 = {fit['C2']:.4e}, true = {ROUTE_B_C2:.4e}, rel = {c2_rel_err:.2e}",
)


# ============================================================================
# Block 8 — σ² scan produces monotonic D_2 in linear regime
# ============================================================================

separator("8 — σ² scan: D_2(σ²) monotonic in linear regime via Route B")

sigma_values = [1e-10, 1e-8, 1e-6, 1e-4]
d2_values = [route_b_d2_lookup(s) for s in sigma_values]
is_monotonic = all(d2_values[i] < d2_values[i + 1] for i in range(len(d2_values) - 1))
record(
    "Route B lookup monotonic over σ² ladder",
    is_monotonic,
    f"D_2 values: {[f'{v:.4e}' for v in d2_values]}",
)

# Linear regime check: D_2(1e-10) / D_2(1e-8) should be ~ 1/100 (if no saturation)
# But at σ²=1e-8, C2·σ² = 6.825e-3 (small) → linear regime
ratio_decade = d2_values[1] / d2_values[0]  # σ²=1e-8 / σ²=1e-10
# In pure linear: ratio = 100. Actual: 100 · (1 + 6.825e-5) / (1 + 6.825e-3)
# ≈ 100 · 0.99322 = 99.32
expected_ratio = (1e-8 / (1 + 6.825e5 * 1e-8)) / (1e-10 / (1 + 6.825e5 * 1e-10))
record(
    "Decade ratio matches analytic formula",
    abs(ratio_decade - expected_ratio) / expected_ratio < 1e-10,
    f"ratio = {ratio_decade:.6f}, expected = {expected_ratio:.6f}",
)


# ============================================================================
# SUMMARY
# ============================================================================

print()
print("=" * 72)
print("SUMMARY")
print("=" * 72)
all_pass = all(p for _, p, _ in results)
for name, passed, _ in results:
    marker = "✓" if passed else "✗"
    print(f"  {marker} {name}")
print("=" * 72)
if all_pass:
    print(f"  ALL {len(results)} BLOCKS PASS — W10-01 physics verified independently.")
    sys.exit(0)
else:
    failed = sum(1 for _, p, _ in results if not p)
    print(f"  {failed} of {len(results)} BLOCKS FAILED — inspect above.")
    sys.exit(1)
