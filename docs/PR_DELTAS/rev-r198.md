# REV-R198 — runnable-now statistical analyses: ML fσ8 + DESI dipole mock significance + K6 curl on the real field

## Context

Owner ask: run every statistical analysis executable at the current point (long
runs included), watching only for OOM, excluding the PL3-dependent lanes (the
FFP10 SMICA / K1 CMB E2E download is still in flight). From the 11-item
open-items ledger the runnable-now analyses were rank-2 (ML fσ8), rank-9 (DESI
dipole mock significance), rank-5 (K6 CR vorticity) and rank-10 (ACT N0/N1). K1
E2E (rank-4) is PL3-dependent → excluded; rank-6 (nonlinear COLA suite) is a
genuine external multi-day track; rank-1/3/8/11 are non-statistical /
decision-only / print-only. Honest ceiling unchanged: kinematic/statistical
measurements + consistency tests only; no Bianchi family/geometry/detection.

## rank-2 — ML noise-aware velocity-field f σ₈ (DELIVERED, the registered exit-gate)

`htt/obsstat/velocity_correlation_ml.py` + `scripts/cf4_velocity_correlation_ml.py`
→ `cf4_velocity_correlation_ml_card.json`. The precision upgrade of the rev-r196
pair-correlation diagnostic: the field-level maximum-likelihood estimator on the
binned CF4 cells, `C(A) = A·G + N` (G the fiducial linear velocity covariance,
N the per-cell noise) maximised over the velocity-field amplitude
`A = (fσ8/fσ8_fid)²` via a whitened-eigenbasis profile (O(N) after one
eigendecomposition). **fσ8 = 0.40 ± 0.02 (Vpec, shape-corrected to the standard
linear σ_v; conservative octant jackknife ± 0.10), consistent with the published
CF4 ~0.38 and Planck ~0.44.** An 80-realisation injection Monte Carlo recovers
the amplitude UNBIASED (mean A=1.02, pull 1.4σ), and its scatter matches the
Fisher error (confirming the Fisher error; the octant jackknife over-estimates,
octant deletion over-perturbs the large-scale field). The direct Vpds is
noise-limited (its ML amplitude rails, as the rev-r196 diagnostic found) →
flagged; Vpec is the clean measurement. Successor pattern (the rev-r196 diagnostic
card + module stay byte-frozen). Gate 5.

## rank-9 — DESI dipole mock-calibrated significance (in-house LambdaCDM clustering mock)

`htt/obsstat/number_count_dipole.py` + `scripts/desi_dipole_mock_significance.py`
→ `desi_dipole_mock_card.json` (the rev-r197 in-house-mock pattern applied to the
number-count dipole). The analytic shot-noise floor separates shot noise from
clustering; the exact ℓ=1 projection of the observed dN/dz gives the LambdaCDM
clustering C_ℓ; GRF sky maps with that C_ℓ, masked to the real BGS footprint and
Poisson-sampled at the random-encoded selection, run through the IDENTICAL dipole
estimator give the LambdaCDM null (400 mocks × 3 bias values). **Finding: the
observed dipole D=9.49e-3 is CLUSTERING-dominated (13.5σ above the shot-noise
floor) and CONSISTENT with LambdaCDM clustering cosmic variance (mock
|D|=0.021±0.009, p=0.90 at bias 1.5; robust across bias 1.2–2.0) — NOT an
excess/anomaly.** The kinematic dipole is sub-dominant to the clustering cosmic
variance at BGS depths. Discharges the significance residual; only the
clustering/kinematic separation (BGS low-z) remains. Gate 4.

## rank-5 — K6 vorticity on the REAL CF4++ 3-D WF field (PARTIAL)

`htt/obsstat/velocity_field_curl.py` + `scripts/cf4pp_vorticity_posterior.py` →
`cf4pp_vorticity_card.json`. The rev-r127 K6 no-go was abstract; this quantifies
it on the real 3-D CF4++ WF field: **the WF mean-field curl/div ratio = 0.009
(RMS|curl| << RMS|div|, potential flow) — the no-go CONFIRMED on the real field.**
A correlated-residual constrained-realization vorticity distribution (a GRF
residual scaled to the per-cell WF std) upgrades the per-cell-independent toy, but
is residual-dominated and correlation-length-dependent (RMS|curl| 14–48 (km/s)/Mpc
across R=7.8–30 Mpc), because the residual correlations are not fixed by
(v_mean, v_std) alone. So a DEFINITIVE ensemble still needs the full WF residual
covariance / operator → `BLOCKED_MISSING_FIELD_REALIZATIONS` stays PARTIAL. Gate 4.

## rank-10 — ACT N0/N1 RDN0 debias (BLOCKED-on-QE, not fabricated)

Only the reconstructed κ a_lm (data + 400 sims) are on disk — a true
realisation-dependent N0 (RDN0) needs the quadratic-estimator pipeline / raw CMB
maps, which are not available. The sim-null already includes N0+N1 correctly for
the isotropy test (p=0.35 CONSISTENT unaffected), so nothing is fixed for
isotropy and no RDN0 is fabricated. Documented as blocked-on-QE (NOT a PL3
exclusion) in BLOCKERS.md + the open-items ledger.

## Wiring

Results table v9 +3 rows (`K5-VCORR-ML`, `K6-CURL`, `EXT-DESI-MOCK`, all
`measured`) → 78 rows (the v9 report reads the v8 table → no rebuild). CLAIM_LEDGER
+3 (`k5.cf4_velocity_correlation_ml`, `k5.cf4pp_vorticity`, `ext.desi_dipole_mock`).
BLOCKERS.md: `BLOCKED_MISSING_FIELD_REALIZATIONS` PARTIAL updated (mean-field curl
quantified + correlated-CR upgrade; definitive needs the operator);
`BLOCKED_MISSING_DESI_RANDOMS` residual → significance mock-calibrated (ΛCDM-
consistent); the ACT N0/N1 residual → blocked-on-QE. Tickets:
`desi_number_count_dipole.yaml` → `mock_calibrated_consistent_with_lcdm_clustering`
(+ the mock block). Open-items ledger → **10 items** (rank-2 ML fσ8 resolved +
removed; rank-4 K6 + rank-8 DESI + rank-9 ACT notes updated; renumbered, contract
green). Gates `tests/obsstat/test_cf4_velocity_correlation_ml.py` +
`test_desi_dipole_mock_significance.py` + `test_cf4pp_vorticity.py` (5 + 4 + 4).

## Frozen surfaces

x_C + W2_max bit-identical; rev-r195/r196/r197 cards + K5 v7/v8/v9 cards +
`cf4_groups.npz` untouched (the three new cards are standalone successors); all
three new cards `--check` byte-stable; downloaded data on gitignored workdir /
off-Dropbox NVMe, not git. Diagnostic firewall intact on every card.
