# Open-items ledger — every unfinished research item, ranked by earliest executability

_Generated 2026-07-11 by `scripts/build_open_items_ledger.py` (dev-tier planning artifact; never rendered into any report). Fail-closed against ticket-state drift._

| # | Item | Source | State | Blocker | Executability | Exit gate |
|---|---|---|---|---|---|---|
| 1 | Manuscript downstream reconciliation of the MES vorticity-ceiling correction (Saadeh-MES gap magnitude; ch09 W^2~1e-15 aside; ch04 atlas ~1e6 strip) | REV-R190 ch04 correction (registry MES-MESB-TRACE); geodesic W2_max=3.3789e-13 changes the downstream numbers | — | — | **now** | recompute the Saadeh(9.01e-22)-vs-MES gap against the geodesic W2_max=3.3789e-13 (~8-9 OOM, was quoted ~6) and reconcile ch04 sec:atlas + ch09 Saadeh-MES gap subsection; ch04 MES theorems already corrected |
| 2 | Paper-A/B/C split of the audit-report material | registered plan (v9 report; user decision 2026-07-10: plan-only this cycle) | — | — | **decision_only** | user instruction to execute the split |
| 3 | K1 E2E-systematics null + BipoSH E2E upgrade | ticket EGS3-C1-k1-ffp10-npipe; BLOCKERS.md section 1 | blocked | BLOCKED_MISSING_PR4_E2E_ACCESS | **blocked** | PLA FFP10/NPIPE E2E ensembles on disk (download in flight, ~1TB); then the registered max-scan/global-p mechanics run unchanged |
| 4 | K6 Hoffman-Ribak constrained-realization vorticity posterior | ticket EGS3-C2-cf4-wfcr; BLOCKERS.md section 2 | blocked | BLOCKED_MISSING_FIELD_REALIZATIONS | **blocked** | owned CR ensemble over the CF4 3D WF field |
| 5 | K5 cosmic-variance coverage on release mocks | ticket EGS3-C2-cf4-wfcr; BLOCKERS.md section 3 | blocked | BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP | **blocked** | ownership of the CF4 release-mock pipeline (selection/Malmquist/grouping/correlated field) |
| 6 | PR08-006 joint posterior artifact | BLOCKERS.md section 4 | — | BLOCKED_UPSTREAM | **blocked** | close K1+K5+K6 first (items 2-4); then assemble with explicit measured/partial/fail-closed sectors |
| 7 | Native low-ell Bianchi solver atlas (theory-g CMB likelihood) | BLOCKERS.md section 5; PR10 project | — | AWAITING_NATIVE_LOWELL_SOLVER | **blocked** | PR10-scale separate solver project; fail-closed OutOfScopeError firewall stays until then |
| 8 | DESI number-count dipole: mock-calibrated significance | ticket EGS3-H1-desi-number-count-dipole; registry EXT-DESI | randoms_downloaded_window_corrected_measured | — | **blocked** | release-matched DESI BGS mocks to calibrate the mask-coupling amplitude bias + significance (and to separate the local clustering dipole from the kinematic dipole at BGS depths) |
| 9 | ACT DR6 low-ell kappa isotropy: mean-field debias (sims) | ticket EGS3-H2-act-dr6-kappa-isotropy; BLOCKERS.md; registry EXT-ACT | connected_bandpower_readout_blocked_on_sims | BLOCKED_MISSING_ACT_LENSING_SIMS | **blocked** | download the ACT DR6 lensing simulation ensemble (mean field + N0/N1); debias the low-ell kappa statistic; then EXT-ACT flips blocked -> measured (diagnostic-only) |
| 10 | MESb (PRD 51, 5942) INTERNAL non-geodesic derivation (Eqs 30-36 algebra) | ticket EGS3-G8-mes-full-rederivation (residual) | web_traced_in_house_refuted_geodesic_readopted | — | **blocked** | legitimate access to the print-only journal PDF; the accessible-range trace (REV-R190) already REFUTED the in-house triples and re-adopted the geodesic anchor, so only MESb's internal algebra remains |

## Notes

- **1.** the refuted-value theorem correction (thm:MES-omega/udot, prop:ordering) is DONE this cycle; only the downstream gap-magnitude prose remains.
- **3.** PLA/PL3 downloads in progress (2026-07-11).
- **4.** WF mean-field curl-suppression no-go already established.
- **5.** conditional coverage (fixed LCDM sigma_cv prior) already measured.
- **8.** REV-R192/R193: randoms downloaded (fetch.py --desi-randoms); window-corrected overdensity dipole MEASURED D=9.49e-3 (224x below the raw footprint, at the kinematic scale), EXT-DESI flipped to MEASURED_WINDOW_CORRECTED (diagnostic); only the mock-calibrated significance remains.
- **9.** REV-R191: real kappa a_lm + N_L + mask loaded, auto-bandpower readout; low-ell isotropy null blocked on sims.
- **10.** print-only (no arXiv/ADS/OA copy); the in-house (3/4,2,2/7)/(3/4,1,3/14) refutation + geodesic re-adoption is DONE; only MESb's own Eqs 30-36 derivation is blocked.

## Closed / held tickets (represented for completeness)

- `mes_full_rederivation.yaml` — state `web_traced_in_house_refuted_geodesic_readopted`: MES re-freeze EXECUTED (REV-R187/R188, registry MES-REFREEZE: geodesic derivation attached, W2_max 1.3087e-6 -> 3.3789e-13), then WEB-TRACED + the in-house non-geodesic triples REFUTED (REV-R190, registry MES-MESB-TRACE): they appear in no accessible source and exceed the companion's own reduced bound; the geodesic anchor SURVIVED five adversarial lanes and is re-adopted; ch04 corrected. Frozen anchor byte-identical; only MESb's internal Eqs 30-36 algebra stays print-only-blocked (rank 8)
- `k5_omega_k_higher_order_ceiling.yaml` — state `branch1_executed_slaving_transfer_ceilings_registered`: exit-gate branch 1 EXECUTED (REV-R184/R185, registry OMK-REOPEN): exact curvature->shear slaving kappa = -1/(2+q) on the LRS-III/KS slaved mode; six labeled attribution x era |Delta Omega_k| ceilings on a NEW card; the certified instantaneous null untouched; frozen U_k plugin NOT modified; nothing promoted
- `t3_king_ellis.yaml` — state `ten_item_program_executed_lower_w2_withdrawal_upgraded_to_dynamical`: the ten-item rotating-congruence program EXECUTED (REV-R181/R182, registry KE-FRAME/KE-OBS/KE-DYN): rotating perfect-fluid development exists at Omega_k>0; at Omega_k=0 doubly obstructed (momentum constraint + dynamical irrotationality) -- the lower-endpoint W^2 withdrawal is now dynamical within the group-invariant perfect-fluid class; W^2 re-attribution stays a registered interpretive question
- `gf_interval_latent_quotient_bug.yaml` — state `resolved_in_successor_and_iff_retracted_superseded_by_T2G`: closed by the v8 successor + v9 T2G retraction cycle
- `psd_cone_redesign.yaml` — state `reviewed_fixes_applied_behind_graded`: representation-only redesign, shipped behind the graded comparator; dual review signed off (v8-update)
- `teff_representative_nonclaims.yaml` — state `registered_nonclaims`: future obligations discharged in the v8-update cycle; the nonclaims registration itself is the steady state
