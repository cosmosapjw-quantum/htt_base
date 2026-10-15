# HTT observational publication research continuation: S02, L01, H02

2026-10-15 KST. Parent commit f48ff9ee50c16f9f101562ebdc0d801e2105c63b.
Original owner checkout HEAD 13d8d85fa470d645d008986e8f77d8d0f70fdf54 and 57 pre-existing dirty paths are read-only. All new output paths are scoped to the active independent worktree, with no local Codex.

## Literature and theory actually reused

1. Planck Collaboration IV, A&A 641 A4 (2020), https://doi.org/10.1051/0004-6361/201833881: native SMICA/NILC multiple product methods and finite masks, complex systematics of polarized maps.
2. Planck Collaboration VII, A&A 641 A7 (2020), https://doi.org/10.1051/0004-6361/201935201: polarized Q/U and E/B large-scale statistics, end-to-end FFP10 and its fixed-weight systematics, noise-dominated polarization B and need for masks matched to simulations. Previous FFP10 K1 fixed weights 999 CMB and 300 independent noise sources do not prove observed/null exchangeability.
3. Maartens–Ellis–Stoeger PRD 51 1525 (1995), https://arxiv.org/abs/astro-ph/9501016, and Stoeger–Araujo–Gebbie ApJ 476 435 (1997), https://arxiv.org/abs/astro-ph/9904346: conditional all-observer almost-EGS derivative bounds and spherical-power to PSTF tensor multipole normalisation.
4. Cosmicflows-4 Tully et al., ApJ 944 94, https://doi.org/10.3847/1538-4357/ac94d8; Stiskalek et al. MNRAS 546 (2026), https://doi.org/10.1093/mnras/staf2048; Desmond et al 2025, https://arxiv.org/abs/2511.03394. The latter emphasizes nontrivial distance prior and selection effects, not assumed-resolved by CF4 selected group table.
5. Previous local rec_bianchi HEAD 5694a5c physical normal-material **one-event** screen/Jones matrix and rei_bianchi HEAD 0fcb2ddd synthetic positive source-age quadrature were checked; neither supplies physical cosmological anisotropic CMB line-of-sight atlas, source-specific Planck null or CF4 velocity covariance.

## H02. Real CF4 method-calibration × depth-window confounding

Read-only source file:
docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz
SHA-256 86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c. Published 35,970 selected groups, 4 source method families FP/OTHER/SN/TF, same z and J2000 groups as earlier H01. No invented new cosmological sky, no empirical group selection law or measured method zero-point covariance.

For fixed source weights L_Wi and log distance-modulus estimator y_i=ln(cz_i) -(ln10/5)(mu_i-25), let

    f_{Wm} = sum_{i:method(i)=m} L_Wi,
    kappa = ln(10)/5.
    d ln H_W/d delta_mu_m = -kappa f_{Wm}.

This relation is EXACT for additive method-specific distance modulus shifts at fixed weights and sample membership, not a first-order approximation in the magnitudes. If each |delta_mu_m| <= a_m is a **declared hypothetical scenario**,

    |delta(ln H_W - ln H_V)| <= kappa sum_m |f_Wm - f_Vm| a_m.

For an assumed PSD covariance C_mu in mag^2, the propagated covariance is
C_cal = kappa^2 F C_mu F^T, and the contrast variance must be computed stably as
kappa^2 (f_W-f_V) C_mu (f_W-f_V)^T. A common zero point delta_mu_m = lambda for all m cancels exactly from contrasts because sum_m(f_Wm-f_Vm)=0, even though it shifts each window H.

Wolfram exact rational 2-method sanity test:
f_near=(4/5,1/5), f_far=(1/5,4/5), a=(1/10,1/10),
support size = (3 Log[10])/125 ≈ .0552620, and perfect common-mode covariance makes contrast variance exactly zero.

**Actual CF4 weighted source fractions (FP OTHER SN TF):**

| Window z | FP | OTHER | SN | TF |
|---|---:|---:|---:|---:|
| .010–.030 | .159896 | .150420 | .161671 | .528013 |
| .030–.050 | .575352 | .102279 | .172519 | .149851 |
| .050–.075 | .832523 | .011667 | .142716 | .013094 |
| .075–.100 | .937693 | .000974 | .058624 | .002710 |

The observed source-conditioned H_eff ratio far/near is 68.8862449/74.0872728,
log ratio -0.0727872412. Under *hypothetical* independent method zero-point
boxes (NOT measured uncertainties), per-method +/-0.03, .05, .10 mag:
  max allowed |delta far-near logH| = 0.0214913130,0.0358188550,0.0716377100.
The 0.1-mag support equals 98.4207% of the observed log-H depth difference.
This DOES NOT establish that actual calibration explains it, nor measure H(z).
The scenario assumes the same subset and inverse-error weights.

Under another independently chosen *hypothetical* covariance model with
independent .05 mag source zero-point standard deviations, contrast standard
deviation = 0.0220118431 in logH. Under a completely common .05 mag
covariance across methods, the stable result is 2.06e-17 (analytically 0).

Observed computational defect closed: the first algorithm formed Var(W-V)
using Var(W)+Var(V)-2Cov, which suffered catastrophic cancellation for rank-one
common offsets (spurious 4.66e-10). Fixed in production code by whitening the
small method covariance first, applying the contrast Jacobian, and discarding
positive eigenvalues below 64 epsilon times the dominant eigenvalue as
unresolved numerical rank, not a physical prior. New regression checks common
rank-one covariance. Create-only v2 is authoritative; v1 is preserved as
a superseded numerical receipt. Actual source shifted-magnitude injection
matches predicted log-H shift to 3.08e-15. Overlapping 7-window working
covariance has rank 4 as it is composed from four disjoint shells, and cannot
be naively treated as seven independent observables.

Outputs: htt/obsstat/cf4_method_window_calibration.py,
tests/obsstat/test_cf4_method_window_calibration.py,
scripts/run_htt_cf4_method_calibration_h02.py;
results/H02_cf4_method_calibration_v2/{result.json,REPORT_KO.md,cf4_method_calibration_envelope.png}.
H02 **still input-blocked**: real empirical CF4 method zero-point calibration,
survey-selection and peculiar-velocity cross-group covariance required to
turn these scenario supports into observed statistical uncertainties.

## L01. Actual Planck polarized E/B and finite higher-harmonic response

Immutable actual Planck source:
docs/research_program/htt_mes_eps_loop9_20261015/inputs/retained_common_support_coefficients.npz
SHA 900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459,
eight same-physical-sky processing products (SMICA HM/OE/full, NILC HM/full).
Raw original SMICA_FULL PR3 source:
 /mnt/extdrive/workdir/raw/planck_data/COM_CMB_IQU-smica_2048_R3.00_full.fits
source SHA 60952c645eb33d151905ddf5837477e15ca02a3261feca4ceca3c3feece4f9ac,
native NSIDE2048 NESTED, Q_STOKES/U_STOKES in K_CMB. Source read only.

Source common pol mask: official Int? NO; three exact **polarization PMASK**
(native official common POL, HM missing POL, OE missing POL) with NSIDE2048
NESTED -> NSIDE64 RING selected 30,021 pixels. Temperature mask selected
26,846 pixels and must not be substituted for polarization.

Physical spin-2 Q/U harmonic design (for each ell, E and B real m0,
cos/sin modes with sqrt2 complex map convention). The masked joint
least-squares projector, finite span ell=2..5 (64 coefficients), recovers
the archived SMICA_FULL lowell E/B coefficients from direct native RAW
FITS with EXACT recorded max error 0.0 microK. The same native raw sky
then independently fits ell2..8 (154 coefficients), without changing
mask and Stokes conventions.

**Source-matched finite fit results, μK²:**

| ell | mode | lmax5 C | lmax8 C | ratio |
|---|---|---:|---:|---:|
| 2 | EE | 0.088112235 | 0.092120884 | 1.0455 |
| 2 | BB | 0.095676553 | 0.112974085 | 1.18079 |
| 3 | EE | 0.026899198 | 0.025981096 | 0.9659 |
| 3 | BB | 0.008281592 | 0.013571676 | 1.63878 |

Actual low ell2..5 64-vector movement norm = 0.306411176 microK;
selected-stokes Q/U fit residual RMS decreases from 1.26071273 to
1.25777712 microK when adding ell6..8. Model dimension increased from
64 to 154; high-l noise/foreground remains, so neither is a physically
debiased fullsky E/B signal or Planck anomaly probability.

For synthetic unit amplitudes in finite ell6..8 with the **actual**
30,021 POL mask, the source lowell B<-E operator 2-norm is 0.934495,
while on complete NSIDE64 pixels ≈0.000174067. The full 8 product
same-sky lowell E/B processing-power figures are in
results/L01_planck_spin2_pol_v1. The operator norm is not an upper
bound on actual sky contamination without a bound on the amplitudes
and ell>8 remainder.

Outputs:
htt/obsstat/planck_spin2_source_response.py,
scripts/run_htt_planck_spin2_source_l01.py,
scripts/run_htt_planck_raw_spin2_fit_l01.py,
tests/obsstat/test_planck_spin2_source_response.py,
tests/obsstat/test_planck_raw_spin2_reduce.py,
results/L01_planck_spin2_pol_v1,
results/L01_raw_SMICA_spin2_v1.

The original raw 2GB FITS is NOT stored in Git; exact SHA and
small full/low fitted harmonics are stored for reproduction. Native
raw pixel reduction and corresponding basis construction have
small-NSIDE injection tests with independent NESTED->RING and
sentinel/missing coverage references. Physical beam transfer, high
ell>8/source polarization noise model, Stokes cross-systematic
and independent end-to-end matched null remain unavailable.
L01 remains **PARTIAL_EXECUTED_PENDING**.

## S02. Observed CMB source conditional MES denominator, not physical Q posterior

Use the SAME nine T source-processing products from the previous
Planck investigation (one physical sky) and corrected SAG Eqs15/17
\epsilon2,\epsilon3 from the original modes; adopt the mathematical
branch epsilon1=0 and MES C1/C2 derivative **assumptions** for a
hypothetical geodesic shear/vorticity algebraic ceiling.

    U_sigma = (3/2) (3eps2 + (3/7)eps3)^2
    U_omega = (3/2) ((2/15)eps2)^2.

Wolfram exact:
    U_omega/U_sigma = 196 eps2^2 / [2025 (7eps2+eps3)^2].

Actual one-sky nine processing images:
  U_sigma range 2.5108328815e-9 ... 2.5933214862e-9,
  U_omega range 2.9427415431e-12 ... 3.0734051401e-12,
  relative U_sigma processing spread vs SMICA_FULL 3.195694%.
No posterior weights are attached to these nine alternative processing
methods. This is a measured-source processing sensitivity under
unverified Copernican/observer hypotheses, not an observational MES
geodesic shear upper bound.

Additional counterfactual assumptions flat, untilted, 0<=Sigma2<=U_sigma,
0<=W2<=U_omega imply signed Q=x_C/U_sigma belongs to
[-U_omega/U_sigma,1], where lower edge approximately -0.00117.
If the unknown curvature DeltaOmega_k is still an unrestricted real
signed sector, Q and x_C span all reals, no finite total-x bound follows,
and for ANY finite threshold t and unknown physical posterior the
conservative \Pi_Q(t) identified set is [0,1]. F and G_F remain
unidentified because their positive sector and depth-coupled posterior
inputs are absent. This is a conditional algebraic incompleteness
witness, NOT a universal no-go theorem or a cosmological null p-value.

Source/implementation:
htt/obsstat/publication_source_partial_identification.py,
tests/obsstat/test_publication_source_partial_identification.py,
scripts/run_htt_p1_source_partial_identification_s02.py;
results/S02_real_planck_typed_partial_v1.
S02 **PARTIAL_EXECUTED_PENDING**: requires real joined source-conditioned
posteriors, correct nonzero/unknown domain handling and common
source-congruence geometry to progress beyond this conservative envelope.

## Updated publication DAG decision

The 42-node six-paper plan remains authoritative. S01/H01/H03 (earlier
scoped) retain DONE. H02 remains BLOCKED_EXTERNAL with actual source
scenario results; L01 remains PENDING with valid actual polarized T/E/B
operator and lmax perturbation, pending full beam/noise/source null;
S02 remains PENDING with real same-sky CMB MES source denominator but
without signed x likelihood. No task is marked full physical complete
merely because a measurement-model diagnostic finished. All six paper
submission decisions remain NOT_READY_TO_SUBMIT.

Native subagent NOT_RUN: no exposed create/spawn interface. Local
Codex NOT_USED. Wolfram CAS equalities actually evaluated; SciSpace
and Exa looked up primary Planck sources. Other branches/repos were
inspected read-only; no native geometry atlas was silently imported.
