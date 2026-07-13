# REV-R196 — CF4 MV ideal-window bulk flow + reconstruction-dependence suite

## Context

rev-r195 measured the CF4 weighted-GLS bulk flow but WITHHELD the ΛCDM
significance (the noise-weighted GLS window aliases nonlinear small-scale power →
its linear cosmic variance is a lower bound → a spurious ~9σ). This cycle
delivers the registered unblock path — the **minimum-variance ideal-window
estimator** — and a **reconstruction-method-dependence suite** (the statistical
result depends on how the peculiar-velocity field is reconstructed) with a
**reconstruction-independent statistic**. Ran while the PR3/PR4 download lagged.

Honest ceiling respected throughout: bulk-flow-vs-ΛCDM kinematic results only, no
Bianchi family/geometry/detection claim.

## Shared primitive

`htt/obsstat/velocity_power.py` — self-contained EH98 σ₈-normalised linear P(k) +
`velocity_correlation_functions` (Górski Ψ∥/Ψ⊥ closed form) + the (100f)²
prefactor and σ_v,1D. The frozen rev-r195 script keeps its own copy (successor
pattern; the shared module is used by the two new lanes).

## Track A — MV ideal-window estimator (resolves the withheld significance)

`htt/obsstat/mv_bulkflow.py` (Watkins–Feldman–Hudson): `pair_velocity_covariance`
R^(v) via the closed-form Ψ∥/Ψ⊥ (well-converged, no solid-angle grid),
`ideal_window_target` Q(R) for a Gaussian window of scale R (analytic), Lagrange-
constrained `mv_weights` (Gᵀw=I → a uniform flow is recovered exactly), split
cosmic/noise covariance. The MV weights tie the estimator to the *specified*
large-scale W_R, so R^(v) is the FAITHFUL cosmic variance (not the GLS lower
bound) and the ΛCDM significance is reportable.

`scripts/cf4_mv_bulkflow.py` → `cf4_mv_bulkflow_card.json`: |B|(R), apex, split
covariance, χ²→σ for R∈{50,100,150,200} h⁻¹Mpc. **Fixed a latent distance bug**:
SGX/SGY/SGZ are in **km/s (cz)**, not Mpc (norm/V3k=0.99); the MV now uses the
`Dist` column (Mpc)×n̂. Result: **|B|(200)=405 km/s (±3 binning systematic),
consistent with the published CF4 419±36; apex@50 8.5° from the published flow;
ΛCDM tension ~4.4–5.4σ (P(k)-corrected → fiducial)**. Honesty: the significance
is a treatment-dependent RANGE and a LIKELY OVER-ESTIMATE (Whitford 2023: MV
uncertainties are typically underestimated; the fiducial EH σ_v runs ~15% low);
the AMPLITUDE is the robust quantity — the apex swings at large R (the sparse
deep CF4 sample dominates), well-constrained only at R≤100. Validation gates
(all pass): injected uniform flow recovered to 1e-14, single-cell σ_v to <0.1%,
converged vs a finer grid, literature band. The definitive mock-calibrated
significance stays `BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP` (mock branch).

Note: the rev-r195 card has the same latent SG-is-km/s distance issue in its
off-diagonal cosmic variance, but it WITHHELD its significance, so no false claim
was made; the frozen card is left untouched (documented).

## Track B — reconstruction dependence + reconstruction-independent statistic

- **B1a** `dl_pipeline/scripts/extract_cf4_pv_variants.py`: re-extracts the three
  CF4 PV columns `Vpds` (Davis–Scrimgeour direct), `Vpwf` (pure WF), `Vpec`
  (ramp) from the on-disk `table4.dat` → new `cf4_pv_variants.npz` (never
  rewrites the frozen `cf4_groups.npz`).
- **B2/B3** `scripts/cf4_reconstruction_dependence.py` →
  `cf4_reconstruction_dependence_card.json`: the identical weighted-GLS estimator
  on the three PV columns + the CF4++ WF field + the external **Carrick 2015
  2M++ field** (downloaded, an independent tracer) → **amplitude spans
  145–341 km/s (spread 196) across 5 reconstruction methods** (the pure WF
  shrinks the flow toward zero); apex spread 28°. ZoA |b|-cut sensitivity small
  (5 km/s / 1.4° — CF4 has good sky coverage).
- **B1b** `htt/obsstat/velocity_correlation.py` + `scripts/cf4_velocity_correlation.py`
  → `cf4_velocity_correlation_card.json`: the reconstruction-INDEPENDENT
  statistic (the physical, well-posed replacement for the ill-posed angular
  pseudo-Cℓ the user rejected) — the Górski velocity correlation function
  Ψ∥(r)/Ψ⊥(r) from LOS-velocity pairs (no field reconstruction), bulk-subtracted
  + inverse-error-weighted. **DIAGNOSTIC f σ₈ = 0.38 (Vpec, matching the
  published CF4 ~0.38) / 0.75 (direct Vpds, noise-limited)** — treatment-
  dependent; a precision value needs the max-likelihood noise-aware estimator
  (Johnson 2014; CF4 2604.08314, registered exit-gate). Cosmic Mach number
  reported. Deterministic 12k subsample (the full 1.25e8 pairs make the octant
  jackknife infeasible).
- **B4** `fetch.py` stage `cf4_reconstructions` + `sources.json`: Carrick 2M++
  (public, `cosmicflows.iap.fr/assets/data/twompp_velocity.npy`) downloaded +
  CONNECTED; Nusser 2026 2MRS (arXiv:2606.08593) has no confirmed public release
  → `BLOCKED_MISSING_CROSS_RECONSTRUCTION`.

## Wiring

Results table v9 +3 rows (K5-MV `measured`, K5-RECON/K5-VCORR `measured_diagnostic`;
74 rows; the v9 report reads the v8 table → no rebuild). CLAIM_LEDGER +3
(k5.cf4_mv_bulkflow / cf4_reconstruction_dependence / cf4_velocity_correlation).
BLOCKERS.md: the MV route DELIVERED (release-mock blocker → PARTIAL, mock branch
open) + new `BLOCKED_MISSING_CROSS_RECONSTRUCTION`. Open-items ledger → 12 items
(rank-2 ML-fσ8 estimator = now; rank-6 K5 definitive significance; rank-7 Nusser
cross-recon). Gate tests `tests/obsstat/test_cf4_{mv_bulkflow,reconstruction_dependence,velocity_correlation}.py`
(5 + 5 + 4 pass).

## Frozen surfaces

x_C + W2_max bit-identical; rev-r195 card + K5 v7/v8/v9 cards untouched;
`cf4_groups.npz` byte-identical (new `cf4_pv_variants.npz` written separately);
downloaded data on gitignored workdir / off-Dropbox NVMe, not git. Diagnostic
firewall intact on every card (no detection/family/geometry/native-solver token).
