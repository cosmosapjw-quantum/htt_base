# REV-R197 — In-house physical forward-mock significance + LVN-2024/CORAS 2MRS cross-reconstructions (rank-6/rank-7 unblock by substitution)

## Context

Two open-items were blocked on products we do not own. rev-r197 replaces both
with in-house physics + public data (owner ask: "replace the release mock with a
more realistic, physical model; substitute Nusser 2026 with the Lilow-Veena-
Nusser 2024 2MRS neural-network reconstruction"). CRAG-verified: the CF4TF
L-PICOLA release mocks (Qin+2021) are request-only; Nusser 2026 has no public
release; the LVN 2024 NN (arXiv:2404.02278) + CORAS 2021 (arXiv:2102.07291) 2MRS
reconstructions ARE public. Honest ceiling unchanged: bulk-flow-vs-LambdaCDM
kinematic only; no Bianchi family/geometry/detection claim.

## P0 repair (rev-r196 latent defect)

`tests/obsstat/test_cf4_mv_bulkflow.py::test_bulkflow_and_literature` shipped
FAILING at HEAD (a560119): the apex key (`apex_separation_from_published_deg` vs
the card's `apex50_...`, a KeyError) masked a second wrong assertion
(`amps == sorted(amps)` — the real |B|(R) is 173/135/263/405, NOT monotone; it
dips at R=100). Both fixed: the key, and the assertion re-stated to the true
physical claim (the R=200 deep-sample flow is the global maximum, exceeds the
R=50 flow, and rises across the deep tail). The rev-r196 "5+5+4 gate pass" claim
was inaccurate for this file (it was 4/1); now 5/5.

## Lane A — physical forward-mock calibrated significance (rank-6)

`htt/obsstat/pv_forward_mocks.py`: a linear peculiar-velocity Gaussian random
field on a 2 h⁻¹Gpc / 256³ FFT grid (v_j(k)=i√hf2 (k_j/k²)δ(k), shared EH98
σ₈-normalised P(k)) + the super-sample (>box) uniform bulk mode
(hf2/(6π²)∫₀^kf P dk, essential: it lifts the mock bulk-flow covariance from 0.72
to ~0.93 of analytic) + trilinear sampling at the CF4 positions.

`scripts/cf4_mock_calibrated_significance.py` → `cf4_mock_significance_card.json`:
250 boxes × 8 octant observers = **2000 survey-matched mocks**, each u_n = n̂·(v_GRF
+ b_super) + N(0,σ_tot) run through the identical MV weights (S-independent →
cached once; per-mock is a cheap `W@cS_mock`). Result @R=200: |B|_obs=405 vs the
mock null → **mock-calibrated parametric tension 5.76σ, empirical 2000-mock floor
>3.48σ**, with the **mock/analytic linear covariance ratio ρ=0.925** (the mock
reproduces the analytic linear bulk-flow covariance to the grid resolution).
Validation (all pass): mock bulk-flow isotropy ⟨B⟩=2.0 km/s, ρ∈[0.92,0.93] all R,
recomputed |B_obs| matches the committed MV card. σ_NL∈{150,250,350} sensitivity
per R.

**Honest headline**: the in-house physical (but LINEAR) mock reproduces the
analytic linear significance (~5.8σ, consistent with the rev-r196 4.4–5.4 range),
so the estimator + geometry + noise do NOT inflate the tension; the reduction to
the literature ~2–3σ (Whitford 2023, full nonlinear L-PICOLA mocks) is
attributable to nonlinear velocity power beyond this linear model — the
registered COLA residual, NOT claimed here. This discharges the "no mock at all"
state; the mock branch of `BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP` is DELIVERED,
the nonlinear-COLA refinement is the downgraded residual.

Heavy card (250 grid realisations, ~20 min); the gate test READS the committed
card (the ACT pattern), not a `--check` rerun. Gate
`tests/obsstat/test_cf4_mock_significance.py` (5 pass).

## Lane B — LVN 2024 NN + CORAS 2021 cross-reconstructions (rank-7 substitution)

Both public 2MRS reconstruction grids downloaded (Dropbox folder zips: LVN 100MB
`.npy` 128³ Galactic Cartesian CMB frame r<200; CORAS 415MB text → cached
`coras_velocity_zCMB.npy` 201³ comoving Galactic zCMB) to off-Dropbox NVMe.
`dl_pipeline/{config/sources.json,scripts/fetch.py}`: `cf4_reconstructions` +=
`lilow_nn_2mrs` + `coras_2mrs` folder-zip stages (env override + blocked
fallback); Nusser 2026 → `SUPERSEDED_BY_LILOW_2024_PUBLIC`.

`scripts/cf4_reconstruction_dependence.py`: `_lilow_nn_bulk()` (NaN-masked valid
sphere) + `_coras_bulk()` mirror `_carrick_bulk()` → the recon card is now a
**7-method** comparison (3 PV columns + CF4++ field + Carrick + LVN + CORAS),
amplitude spanning **140–341 km/s**. Convention validated: the LVN grid
reproduces the published |B|(50)≈220 km/s + l≈254 (a convention check in the
gate). The 2MRS reconstructions are reconstruction-vs-measurement (shallow 2MRS
regresses to the mean at large r) — documented as the expected gap, NOT a
tension. Gate updated (7 pass, incl. the LVN-amplitude convention check + the
extended data-presence skip).

## Wiring

Results table v9 +1 row `K5-MOCKSIG` (`measured`) + updated `K5-RECON` (7 methods)
→ 75 rows (v9 report reads the v8 table → no rebuild). CLAIM_LEDGER +1
(`k5.cf4_mock_calibrated_significance`) + updated `k5.cf4_reconstruction_dependence`.
BLOCKERS.md: `BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP` → in-house physical mock
DELIVERED (nonlinear COLA residual); `BLOCKED_MISSING_CROSS_RECONSTRUCTION` →
DISCHARGED_BY_SUBSTITUTION. Tickets: `cf4_wfcr.yaml` exit_gate notes the K5
in-house delivery (state stays `blocked` — the K6 field-realization branch is
untouched); `egs2/tickets/K5_release_matched_mocks.yaml` →
`in_house_physical_mock_delivered_nonlinear_cola_residual`. Open-items ledger →
**11 items** (rank-6 reframed to the nonlinear-COLA residual; rank-7 Nusser
removed — substituted + measured; renumbered, contract green).

## Frozen surfaces

x_C + W2_max bit-identical; rev-r195/r196 cards + K5 v7/v8/v9 cards + `cf4_groups.npz`
untouched; the recon card's 5 rev-r196 method values are byte-identical (only the
2 new reconstructions added). Downloaded data on gitignored NVMe, not git.
Diagnostic firewall intact on every card.
