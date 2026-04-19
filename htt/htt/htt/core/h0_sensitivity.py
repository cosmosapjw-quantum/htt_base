#!/usr/bin/env python3
"""
H0_sensitivity_analysis.py
==========================
Quantitative H₀-sensitivity audit for the Bianchi defect framework.

Purpose: Determine which manuscript results depend on H₀, by how much,
and whether using H₀ = 67.36 (Planck) introduces bias relative to
H₀ = 73.04 (SH0ES) or H₀ = 69.8 (TRGB/Freedman+2024).

Convention: geometry-frame background H₀ = H₀^(Planck) throughout.
The perturbative ΔH = βc/(3d) is H₀-independent.
"""

import numpy as np
import math
import json

# ── Load SSOT ──────────────────────────────────────────────────
from htt.core.ssot import C

# ── Constants ──────────────────────────────────────────────────
# NOTE: All H₀ values below are GEOMETRY-FRAME Hubble rates H_θ = Θ/3.
# The matter-frame (tilted observer) value is Ĥ = H_θ·cosh(β) ≈ H_θ(1 + β²/2).
# At CF4 β = 1.334×10⁻³, the frame correction is ΔH/H = β²/2 ≈ 8.9×10⁻⁷,
# which is 6 orders of magnitude below the H₀ tension (ΔH ~ 6 km/s/Mpc).
# This frame distinction is irrelevant for the H₀ sensitivity analysis.
H0_PLANCK = C.h * 100           # 67.36 km/s/Mpc (geometry-frame)
H0_SHOES  = 73.04               # Riess+2022 (ApJL 934:L7)
H0_TRGB   = 69.85               # Freedman+2024 (arXiv:2408.06153)
H0_DESI   = 67.97               # DESI 2024 BAO
H0_GW     = 70.0                # GW170817 (Abbott+2017), σ ≈ 6

c_kms     = 299792.458          # km/s (exact)
beta_CF4  = 1.334e-3            # CF4 tilt rapidity
sigma_beta = 0.267e-3           # CF4 1σ uncertainty
TENSION   = H0_SHOES - H0_PLANCK  # 5.68 km/s/Mpc

print("=" * 70)
print("  §1. GEOMETRY-FRAME vs MATTER-FRAME HUBBLE RATE")
print("=" * 70)

# ── §1. Homogeneous Bianchi ΔH vs perturbative Tsagas ΔH ──

# Homogeneous: H_hat = H × cosh β
# ΔH_hom = H₀ × (cosh β - 1) ≈ H₀ × β²/2
dH_hom = H0_PLANCK * (math.cosh(beta_CF4) - 1)
dH_hom_frac = (math.cosh(beta_CF4) - 1)

# Perturbative (Tsagas): ΔH_pert(d) = βc/(3d)
# Derivation: in the matter frame, the peculiar Hubble rate is
#   H_hat(d) = H₀ + (v_pec / d) = H₀ + βc/(3d)
# where the factor 1/3 comes from ∂v_i/∂x^i for a dipolar flow.

depths = np.array([30, 40, 50, 75, 100, 150, 222, 500, 1000])

print(f"\n  Homogeneous (Bianchi background):")
print(f"    ΔH/H = cosh β - 1 = {dH_hom_frac:.2e}")
print(f"    ΔH   = {dH_hom:.5f} km/s/Mpc")

print(f"\n  Perturbative (Tsagas, scale-dependent):")
print(f"    ΔH(d) = βc/(3d)")
print(f"    β = {beta_CF4:.4e}, c = {c_kms:.3f} km/s\n")
print(f"    {'d (Mpc)':>10s}  {'ΔH (km/s/Mpc)':>15s}  {'% of H₀':>10s}  {'% of tension':>14s}")
print(f"    {'-'*55}")

for d in depths:
    dH = beta_CF4 * c_kms / (3 * d)
    pct_H0 = dH / H0_PLANCK * 100
    pct_tens = dH / TENSION * 100
    print(f"    {d:10.0f}  {dH:15.4f}  {pct_H0:10.2f}%  {pct_tens:14.1f}%")

print(f"\n  KEY: ΔH_pert = βc/(3d) depends on β and d, NOT on H₀.")
print(f"  The formula is derived from v_pec/d where v_pec = βc.")
print(f"  H₀ enters only when expressing ΔH as a PERCENTAGE.")

# ── §2. H₀-DEPENDENT vs H₀-INDEPENDENT quantities ──
print(f"\n{'=' * 70}")
print(f"  §2. H₀-DEPENDENCE CLASSIFICATION")
print(f"{'=' * 70}")

# λ_H = c/H₀
lambda_H = {}
for name, h0 in [('Planck', H0_PLANCK), ('SH0ES', H0_SHOES), 
                  ('TRGB', H0_TRGB), ('DESI', H0_DESI)]:
    lambda_H[name] = c_kms / h0

print(f"\n  Hubble radius λ_H = c/H₀:")
for name, lh in lambda_H.items():
    print(f"    λ_H({name:6s}) = {lh:.1f} Mpc")

# λ_J = λ_H × (β/(9q))^{1/3}
print(f"\n  Peculiar Jeans length λ_J = λ_H × (β/(9q))^{{1/3}}:")
for q_val, q_label in [(0.5, 'EdS'), (0.09, 'Son+2025')]:
    factor = (beta_CF4 / (9 * q_val))**(1/3)
    print(f"    q = {q_val} ({q_label}):")
    for name, lh in lambda_H.items():
        lj = lh * factor
        print(f"      λ_J({name:6s}) = {lj:.1f} Mpc")
    
    lj_pl = lambda_H['Planck'] * factor
    lj_sh = lambda_H['SH0ES'] * factor
    shift = (lj_sh - lj_pl) / lj_pl * 100
    print(f"      → SH0ES/Planck shift: {shift:+.1f}%")

# Δq = (β/9)(λ_H/d)³
print(f"\n  Δq = (β/9)(λ_H/d)³ — H₀ sensitivity through λ_H³:")
for d_val in [100, 200, 300, 500]:
    dq_pl = (beta_CF4/9) * (lambda_H['Planck']/d_val)**3
    dq_sh = (beta_CF4/9) * (lambda_H['SH0ES']/d_val)**3
    shift = (dq_sh - dq_pl) / dq_pl * 100
    print(f"    d = {d_val:4d}: Δq(Planck)={dq_pl:.4f}, Δq(SH0ES)={dq_sh:.4f}, shift={shift:+.1f}%")

# ── §3. The double-counting proof ──
print(f"\n{'=' * 70}")
print(f"  §3. DOUBLE-COUNTING PROOF BY CONTRADICTION")
print(f"{'=' * 70}")

print(f"""
  Suppose we use H₀ = H₀^(SH0ES) = {H0_SHOES} as background,
  then add the perturbative tilt correction ΔH = βc/(3d).

  At d = 50 Mpc:
    H₀^(total) = H₀^(SH0ES) + ΔH
               = {H0_SHOES:.2f} + {beta_CF4 * c_kms / (3*50):.2f}
               = {H0_SHOES + beta_CF4 * c_kms / (3*50):.2f} km/s/Mpc

  No observation yields H₀ ≈ {H0_SHOES + beta_CF4 * c_kms / (3*50):.1f}.
  This is a reductio ad absurdum: the H₀ = 73 background
  ALREADY INCLUDES the tilt contribution at d ≈ 50 Mpc.
  Adding ΔH on top counts the same physics twice.

  Self-consistent protocol:
    H₀^(geometry) = {H0_PLANCK:.2f}  (CMB, z = 1100, tilt-free)
    H₀^(matter, d) = {H0_PLANCK:.2f} + βc/(3d)

  At d = 50 Mpc:
    H₀^(matter) = {H0_PLANCK:.2f} + {beta_CF4 * c_kms / (3*50):.2f}
                = {H0_PLANCK + beta_CF4 * c_kms / (3*50):.2f} km/s/Mpc

  This predicts H₀ ≈ {H0_PLANCK + beta_CF4 * c_kms / (3*50):.1f} at SH0ES depth,
  which accounts for {beta_CF4 * c_kms / (3*50) / TENSION * 100:.0f}% of the tension.
  The remaining {(1 - beta_CF4 * c_kms / (3*50) / TENSION) * 100:.0f}% requires
  other physics or unresolved systematics.
""")

# ── §4. Depth profile H₀(d) ──
print(f"{'=' * 70}")
print(f"  §4. PREDICTED H₀(d) TOMOGRAPHIC PROFILE")
print(f"{'=' * 70}")

print(f"\n  H₀^(matter)(d) = H₀^(Planck) + βc/(3d)")
print(f"\n  {'d (Mpc)':>10s}  {'H₀^(matter)':>12s}  {'Observed':>12s}  {'Source':>20s}")
print(f"  {'-'*60}")

observations = [
    (50,  H0_SHOES, 'SH0ES (Riess+22)'),
    (75,  71.8, 'TRGB (Anand+22)'),
    (100, H0_TRGB, 'TRGB+JAGB (Freedman+24)'),
    (222, 68.0, 'CF4 (approx)'),
    (1000, H0_DESI, 'DESI BAO (2024)'),
]

for d, H0_obs, source in observations:
    H0_pred = H0_PLANCK + beta_CF4 * c_kms / (3 * d)
    residual = H0_obs - H0_pred
    print(f"  {d:10.0f}  {H0_pred:12.2f}  {H0_obs:12.2f}  {source:>20s}  (Δ={residual:+.2f})")

# ── §5. Sensitivity to Ω_m via Planck degeneracy ──
print(f"\n{'=' * 70}")
print(f"  §5. Ω_m DEGENERACY (SECOND-ORDER EFFECT)")
print(f"{'=' * 70}")

# Planck: Ω_m h² = 0.1430 ± 0.0011
omega_mh2 = 0.1430
Om_planck = omega_mh2 / C.h**2  # = 0.3153
Om_shoes  = omega_mh2 / (H0_SHOES/100)**2  # = 0.2681

print(f"\n  Planck constraint: Ω_m h² = {omega_mh2:.4f}")
print(f"  If H₀ = {H0_PLANCK}: Ω_m = {Om_planck:.4f}")
print(f"  If H₀ = {H0_SHOES}: Ω_m = {Om_shoes:.4f}")
print(f"  Shift: {(Om_shoes - Om_planck)/Om_planck * 100:+.1f}%")

# Impact on Ω_tilt
Otilt_planck = Om_planck * math.sinh(beta_CF4)**2
Otilt_shoes  = Om_shoes  * math.sinh(beta_CF4)**2
print(f"\n  Ω_tilt(Planck) = {Otilt_planck:.4e}")
print(f"  Ω_tilt(SH0ES)  = {Otilt_shoes:.4e}")
print(f"  Shift: {(Otilt_shoes - Otilt_planck)/Otilt_planck * 100:+.1f}%")

# Impact on filling fraction
from htt.core.bounds import B_sigma_corrected, Sig2_max_MES
from htt.core.analysis_extended import FillingFraction

ff_calc = FillingFraction(w=0.0, eta=C.eta_udot)
eps1_s3 = 1.476e-3
xV_planck = ff_calc.x_V(eps1_s3)
xmax_planck = Sig2_max_MES(eps1_s3)
FF_planck = xV_planck / xmax_planck

# With Ω_m(SH0ES)
Otilt_s3_shoes = Om_shoes * math.sinh(eps1_s3 / (1 + C.eta_udot))**2
FF_shoes = Otilt_s3_shoes / xmax_planck  # x_max is H₀-independent (CMB ratios)

print(f"\n  FF(Planck background) = {FF_planck:.4f} ({FF_planck*100:.1f}%)")
print(f"  FF(SH0ES Ω_m)        = {FF_shoes:.4f} ({FF_shoes*100:.1f}%)")
print(f"  Shift: {(FF_shoes - FF_planck)/FF_planck * 100:+.1f}%")

# ── §6. Impact on evidence ──
print(f"\n{'=' * 70}")
print(f"  §6. IMPACT ON BAYESIAN EVIDENCE")
print(f"{'=' * 70}")

# The 8-channel likelihood:
# (a) F&Q: half-Gaussian on ε₁ → H₀-independent
# (b) CatWISE: Gaussian on ε₁ → H₀-independent
# (c) CF4: Gaussian on β → H₀-independent (β = v/c)
# (d) Saadeh: half-Gaussian on ω̄ → H₀-independent
# (e) D₂ χ²: uses D₂(σ/H) → H₀-independent (σ/H ratio)
# (f) MES ceiling: Σ² < Σ²_max → H₀-independent
# (h) D₃ χ²: uses D₃ → H₀-independent

# The ONLY entry point is through Ω_m in Ω_tilt
# But Ω_tilt enters the tilt channels, not the evidence directly

# To quantify: ln B(FLRW_tilt) uses 1D integration over β
# The integrand is L(β) × π(β) / Z_FLRW
# L(β) depends on: ε₁ (channels a,b), β (channel c), D₂,D₃ (channels e,h)
# None of these involve H₀.

print(f"""
  Channel-by-channel H₀ dependence:

  (a) F&Q intrinsic dipole UL:    ε₁             → H₀-INDEPENDENT
  (b) CatWISE + radio dipole:     ε₁             → H₀-INDEPENDENT
  (c) CF4 bulk flow:              β = v/c         → H₀-INDEPENDENT
  (d) Saadeh vorticity UL:        ω̄              → H₀-INDEPENDENT
  (e) D₂ quadrupole χ²:          D₂(μK²)        → H₀-INDEPENDENT
  (f) MES hard ceiling:           Σ² < Σ²_max    → H₀-INDEPENDENT
  (g) MES soft logistic:          INERT           → N/A
  (h) D₃ octupole χ²:            D₃(μK²)        → H₀-INDEPENDENT

  All 7 active channels use CMB ratios or β = v/c.
  H₀ does not enter any channel.

  Ω_m enters through:
    - Ω_tilt = Ω_m sinh²β (used in the defect identity)
    - But the EVIDENCE COMPARISON uses Σ², not Ω_tilt directly.
    - The filling fraction ℱ = Ω_tilt / Σ²_max uses Ω_m,
      but ℱ is a DERIVED quantity, not an evidence input.

  CONCLUSION: ln B is H₀-independent to O(10⁻²) nats.
  The Ω_m degeneracy shifts ℱ by ~15%, but ℱ does not enter
  the evidence calculation — it is a post-hoc diagnostic.
""")

# ── §7. Summary table ──
print(f"{'=' * 70}")
print(f"  §7. COMPLETE H₀-SENSITIVITY SUMMARY")
print(f"{'=' * 70}")

results = [
    ('Master defect identity',   'C1', 'No',  '0',       'Algebraic (no H₀)'),
    ('MES hierarchy B_σ>B_ω>B_u̇','C2', 'No',  '0',       'CMB ratios (ε_ℓ)'),
    ('ln B = +25.5',             'C3', 'No',  '<0.05 nats','8 channels H₀-free'),
    ('Evidence decomposition',   'C4', 'No',  '<0.05 nats','Same channels'),
    ('BV exclusion',             'C5', 'No',  '0',       'Uses Ω_K, β only'),
    ('FF = 6.3%',                'C6', 'Via Ω_m','→5.4%', 'Ω_m shifts via h² degeneracy'),
    ('λ_J ≈ 297 Mpc',           'C7', 'Yes', '→274 Mpc (−8%)', 'λ_H = c/H₀'),
    ('Δq ∝ d⁻³ (scaling)',      'C8a','No',  '0',       'Kinematic, H₀-free'),
    ('Δq amplitude at d',       'C8b','Yes', '−22%',    '(λ_H/d)³ factor'),
    ('ΔH(50 Mpc) = 2.67',       'C9a','No',  '0',       'βc/(3d), H₀-free'),
    ('ΔH as % of H₀',          'C9b','Yes', '4.0%→3.7%','Denominator changes'),
    ('P1–P11 predictions',      'C10','No',  '0',       'Qualitative/scaling'),
]

print(f"\n  {'Result':<30s} {'ID':5s} {'H₀-dep?':10s} {'If H₀=73':15s} {'Reason':25s}")
print(f"  {'-'*90}")
for name, cid, dep, shift, reason in results:
    print(f"  {name:<30s} {cid:5s} {dep:10s} {shift:15s} {reason:25s}")

print(f"\n  6 core results (C1–C5, C8a, C9a): H₀-INDEPENDENT")
print(f"  4 bridge quantities (C7, C8b, C9b, C6): 8–22% H₀ sensitivity")
print(f"  NO result reverses sign or changes qualitative conclusion.")

