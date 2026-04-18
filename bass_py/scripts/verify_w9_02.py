"""
scripts/verify_w9_02.py
========================

Independent physics verification of the W9-02 Bianchi I matrix
propagator. Runs outside the pytest framework to serve as a redundant
witness — if this script agrees with the test suite, both must agree
with the underlying physics, not just with each other.

Eight verification blocks:

  1. FLRW recovery bit-exact
  2. σ-ladder linearity (machine-precision ratios of 100×)
  3. m=+2 ≡ m=-2 parity symmetry for real shear
  4. Tensor-T kernel identity with W9-01 E-kernel
  5. Axisymmetric shear leaves m=±2 silent
  6. Non-axisymmetric shear activates m=±2
  7. B-mode identically zero for Bianchi I
  8. k-vector ⇄ (|k|, cos_θ_k) interface consistency
"""
from __future__ import annotations

import sys

import numpy as np
from scipy.special import erfc, spherical_jn

from bass.los.bianchi_propagator import (
    BianchiProjectorConfig, BianchiSourceTerms,
    tensor_temperature_kernel, tensor_b_mode_kernel,
    matrix_propagator_m0_m2, matrix_propagator_from_k_vector,
    verify_flrw_recovery, sigma_ladder_convergence,
)
from bass.los.flrw_bessel_projector import (
    FLRWSourceTerms, _zero_callable, e_mode_projection_factor,
)
from bass.transport.bianchi_i_hierarchy import (
    DiagonalShearTensor, MChannelAmplitudes,
    make_axisymmetric_shear, decompose_shear_to_m_channels,
)


# ============================================================================
# Shared fixtures (mirror the test-suite defaults)
# ============================================================================

ETA_0 = 1.4e4
ETA_STAR = 280.0
SIGMA_VIS = 30.0


def g_of_eta(eta):
    return np.exp(-0.5 * ((eta - ETA_STAR) / SIGMA_VIS) ** 2) / (
        SIGMA_VIS * np.sqrt(2.0 * np.pi)
    )


def kappa_of_eta(eta):
    return 0.5 * erfc((eta - ETA_STAR) / SIGMA_VIS)


def make_source_m0():
    return FLRWSourceTerms.with_all(
        theta_0=lambda eta: 1e-5 * np.exp(-((eta - ETA_STAR) / 50.0) ** 2),
        psi=lambda eta: 1e-5,
        pi=lambda eta: 1e-6,
        phi_dot_plus_psi_dot=_zero_callable,
        v_b=_zero_callable,
    )


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
# Block 1 — FLRW recovery bit-exact
# ============================================================================

separator("1 — FLRW recovery bit-exact via matrix propagator")

cfg = BianchiProjectorConfig(ell_max=20, eta_0_mpc=ETA_0, quadrature="simpson")
eta = np.linspace(100.0, ETA_0 - 10.0, 1001)
src_m0 = make_source_m0()

for k in [1e-4, 5e-3, 5e-2]:
    result = verify_flrw_recovery(src_m0, g_of_eta, kappa_of_eta, k=k, eta_grid=eta, config=cfg)
    record(
        f"FLRW recovery at k={k}",
        result["passes"] and result["T_rel_diff"] == 0.0 and result["E_rel_diff"] == 0.0,
        f"T_rel = {result['T_rel_diff']:.2e}, E_rel = {result['E_rel_diff']:.2e}",
    )


# ============================================================================
# Block 2 — σ-ladder linearity
# ============================================================================

separator("2 — σ-ladder machine-precision linearity")

ladder = sigma_ladder_convergence(
    sigma_values=[1e-8, 1e-7, 1e-6, 1e-5, 1e-4],
    sources_m0=src_m0, sources_m2_template=src_m0,
    visibility_g=g_of_eta, kappa_of_eta=kappa_of_eta,
    k_magnitude=5e-3, cos_theta_k=0.5,
    eta_grid=eta, config=cfg,
)
scales = {s: np.max(np.abs(ladder[s].delta_T_m0)) for s in ladder}

# Each decade up in σ should multiply output by 10 (linear regime)
decades = sorted(scales.keys())
max_rel_error = 0.0
for i in range(1, len(decades)):
    ratio = scales[decades[i]] / scales[decades[i - 1]]
    rel_err = abs(ratio - 10.0) / 10.0
    max_rel_error = max(max_rel_error, rel_err)

record(
    "σ-ladder decade ratio = 10× at machine precision",
    max_rel_error < 1e-10,
    f"worst |r - 10|/10 = {max_rel_error:.2e} across 4 decades",
)


# ============================================================================
# Block 3 — m=+2 ≡ m=-2 parity symmetry (real shear)
# ============================================================================

separator("3 — Real-shear m=+2 ≡ m=-2 symmetry")

shear_non_axi = DiagonalShearTensor(sigma_xx=1e-4, sigma_yy=-1e-4, sigma_zz=0.0)
amps = decompose_shear_to_m_channels(shear_non_axi)
bsrcs = BianchiSourceTerms.from_m_channel_state(amps, src_m0, src_m0)
tf = matrix_propagator_m0_m2(
    5e-3, 0.5, bsrcs,
    g_of_eta, kappa_of_eta, eta, cfg,
)
T_plus_minus_eq = np.array_equal(tf.delta_T_m_plus2, tf.delta_T_m_minus2)
E_plus_minus_eq = np.array_equal(tf.delta_E_m_plus2, tf.delta_E_m_minus2)
record(
    "Δ_T^{+2} == Δ_T^{-2}",
    T_plus_minus_eq,
    f"max |Δ_T^+2 - Δ_T^-2| = {np.max(np.abs(tf.delta_T_m_plus2 - tf.delta_T_m_minus2)):.2e}",
)
record(
    "Δ_E^{+2} == Δ_E^{-2}",
    E_plus_minus_eq,
    f"max |Δ_E^+2 - Δ_E^-2| = {np.max(np.abs(tf.delta_E_m_plus2 - tf.delta_E_m_minus2)):.2e}",
)


# ============================================================================
# Block 4 — Tensor-T kernel matches W9-01 E-kernel identically
# ============================================================================

separator("4 — Tensor-T kernel identity with W9-01 E-kernel")

max_abs_diff = 0.0
n_points = 0
for ell in [2, 3, 5, 8, 10, 15, 20]:
    for x in [0.01, 0.1, 1.0, 5.0, 20.0, 100.0]:
        tk = tensor_temperature_kernel(ell, x)
        ek = e_mode_projection_factor(ell, x)
        diff = abs(tk - ek)
        max_abs_diff = max(max_abs_diff, diff)
        n_points += 1
record(
    f"F_T(ℓ,x) == P^E(ℓ,x) over {n_points} (ℓ,x) points",
    max_abs_diff == 0.0,
    f"max abs diff = {max_abs_diff:.2e}",
)


# ============================================================================
# Block 5 — Axisymmetric shear keeps m=±2 silent
# ============================================================================

separator("5 — Axisymmetric shear → m=±2 silent")

shear_axi = make_axisymmetric_shear(s_zz=1e-4)
amps_axi = decompose_shear_to_m_channels(shear_axi)
bsrcs_axi = BianchiSourceTerms.from_m_channel_state(amps_axi, src_m0, src_m0)
tf_axi = matrix_propagator_m0_m2(
    5e-3, 0.5, bsrcs_axi,
    g_of_eta, kappa_of_eta, eta, cfg,
)
m2_T_max = np.max(np.abs(tf_axi.delta_T_m_plus2))
m2_E_max = np.max(np.abs(tf_axi.delta_E_m_plus2))
record(
    "s_m2 = 0 → Δ_T^+2 = 0 exactly",
    m2_T_max == 0.0,
    f"max|Δ_T^+2| = {m2_T_max:.2e}, s_m2 = {amps_axi.s_m2}",
)
record(
    "s_m2 = 0 → Δ_E^+2 = 0 exactly",
    m2_E_max == 0.0,
    f"max|Δ_E^+2| = {m2_E_max:.2e}",
)
record(
    "m=0 channel still active (not corrupted)",
    np.max(np.abs(tf_axi.delta_T_m0)) > 0,
    f"max|Δ_T^0| = {np.max(np.abs(tf_axi.delta_T_m0)):.2e}",
)


# ============================================================================
# Block 6 — Non-axisymmetric shear activates m=±2
# ============================================================================

separator("6 — Non-axisymmetric shear activates m=±2 channels")

# σ_xx = -σ_yy → s_plus ≠ 0, s_m0 = 0
shear_full = DiagonalShearTensor(sigma_xx=5e-5, sigma_yy=-5e-5, sigma_zz=0.0)
amps_full = decompose_shear_to_m_channels(shear_full)
bsrcs_full = BianchiSourceTerms.from_m_channel_state(amps_full, src_m0, src_m0)
tf_full = matrix_propagator_m0_m2(
    5e-3, 0.5, bsrcs_full,
    g_of_eta, kappa_of_eta, eta, cfg,
)
record(
    "s_m2 ≠ 0 activates Δ_T^+2 ≠ 0",
    np.max(np.abs(tf_full.delta_T_m_plus2)) > 1e-20,
    f"s_m2 = {amps_full.s_m2:.2e}, max|Δ_T^+2| = {np.max(np.abs(tf_full.delta_T_m_plus2)):.2e}",
)
record(
    "s_m2 ≠ 0 activates Δ_E^+2 ≠ 0 for ℓ≥2",
    np.max(np.abs(tf_full.delta_E_m_plus2[2:])) > 1e-20,
    f"max|Δ_E^+2[ℓ≥2]| = {np.max(np.abs(tf_full.delta_E_m_plus2[2:])):.2e}",
)


# ============================================================================
# Block 7 — B-mode identically zero for Bianchi I
# ============================================================================

separator("7 — B-mode identically zero (Bianchi I has ψ' = 0)")

# Kernel level
max_kernel_b = 0.0
for ell in range(0, 15):
    for x in np.linspace(0.01, 50.0, 20):
        max_kernel_b = max(max_kernel_b, abs(tensor_b_mode_kernel(ell, x)))
record(
    "tensor_b_mode_kernel(ℓ, x) ≡ 0 across 15 ℓ × 20 x values",
    max_kernel_b == 0.0,
    f"max |F_B| = {max_kernel_b:.2e}",
)

# Propagator level (even with activated m=±2)
record(
    "Δ_ℓ^B in BianchiTransferFunctions ≡ 0",
    np.all(tf_full.delta_B_all_zero == 0.0),
    f"max|Δ_ℓ^B| = {np.max(np.abs(tf_full.delta_B_all_zero)):.2e}",
)


# ============================================================================
# Block 8 — k-vector interface consistency
# ============================================================================

separator("8 — k-vector ⇄ (|k|, cos_θ_k) interface")

amps_test = MChannelAmplitudes(s_m0=1e-3, s_m2=5e-4)
bsrcs_test = BianchiSourceTerms.from_m_channel_state(amps_test, src_m0, src_m0)

# (3, 0, 4)/100 → |k| = 5e-2, cos_θ = 0.8
k_vec = np.array([0.03, 0.0, 0.04])
tf_vec = matrix_propagator_from_k_vector(
    k_vec, bsrcs_test,
    g_of_eta, kappa_of_eta, eta, cfg,
)
tf_scalar = matrix_propagator_m0_m2(
    0.05, 0.8, bsrcs_test,
    g_of_eta, kappa_of_eta, eta, cfg,
)
match_T = np.array_equal(tf_vec.delta_T_m0, tf_scalar.delta_T_m0)
match_E2 = np.array_equal(tf_vec.delta_E_m_plus2, tf_scalar.delta_E_m_plus2)
record(
    "k_vector path == (|k|, cos_θ) path: Δ_T^m0",
    match_T,
    f"max diff = {np.max(np.abs(tf_vec.delta_T_m0 - tf_scalar.delta_T_m0)):.2e}",
)
record(
    "k_vector path == (|k|, cos_θ) path: Δ_E^+2",
    match_E2,
    f"max diff = {np.max(np.abs(tf_vec.delta_E_m_plus2 - tf_scalar.delta_E_m_plus2)):.2e}",
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
    print(f"  ALL {len(results)} BLOCKS PASS — W9-02 physics verified independently.")
    sys.exit(0)
else:
    failed = sum(1 for _, p, _ in results if not p)
    print(f"  {failed} of {len(results)} BLOCKS FAILED — inspect above.")
    sys.exit(1)
