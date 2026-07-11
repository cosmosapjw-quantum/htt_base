# Open-items ledger — every unfinished research item, ranked by earliest executability

_Generated 2026-07-11 by `scripts/build_open_items_ledger.py` (dev-tier planning artifact; never rendered into any report). Fail-closed against ticket-state drift._

| # | Item | Source | State | Blocker | Executability | Exit gate |
|---|---|---|---|---|---|---|
| 1 | Paper-A/B/C split of the audit-report material | registered plan (v9 report; user decision 2026-07-10: plan-only this cycle) | — | — | **decision_only** | user instruction to execute the split |
| 2 | K1 E2E-systematics null + BipoSH E2E upgrade | ticket EGS3-C1-k1-ffp10-npipe; BLOCKERS.md section 1 | blocked | BLOCKED_MISSING_PR4_E2E_ACCESS | **blocked** | PLA FFP10/NPIPE E2E ensembles on disk (download in flight, ~1TB); then the registered max-scan/global-p mechanics run unchanged |
| 3 | K6 Hoffman-Ribak constrained-realization vorticity posterior | ticket EGS3-C2-cf4-wfcr; BLOCKERS.md section 2 | blocked | BLOCKED_MISSING_FIELD_REALIZATIONS | **blocked** | owned CR ensemble over the CF4 3D WF field |
| 4 | K5 cosmic-variance coverage on release mocks | ticket EGS3-C2-cf4-wfcr; BLOCKERS.md section 3 | blocked | BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP | **blocked** | ownership of the CF4 release-mock pipeline (selection/Malmquist/grouping/correlated field) |
| 5 | PR08-006 joint posterior artifact | BLOCKERS.md section 4 | — | BLOCKED_UPSTREAM | **blocked** | close K1+K5+K6 first (items 2-4); then assemble with explicit measured/partial/fail-closed sectors |
| 6 | Native low-ell Bianchi solver atlas (theory-g CMB likelihood) | BLOCKERS.md section 5; PR10 project | — | AWAITING_NATIVE_LOWELL_SOLVER | **blocked** | PR10-scale separate solver project; fail-closed OutOfScopeError firewall stays until then |
| 7 | MESb (PRD 51, 5942) internal rederivation | ticket EGS3-G8-mes-full-rederivation (remaining) | re_frozen_to_geodesic_sag_consistent_anchor | BLOCKED_MISSING_MESb_PRINT_ONLY_PAPER_II | **blocked** | legitimate access to the print-only journal PDF; then the existing rederivation machinery applies |

## Notes

- **2.** PLA/PL3 downloads in progress (2026-07-11).
- **3.** WF mean-field curl-suppression no-go already established.
- **4.** conditional coverage (fixed LCDM sigma_cv prior) already measured.
- **7.** print-only (no arXiv/ADS/OA copy); SAG-1997 discrepancy already documented.

## Closed / held tickets (represented for completeness)

- `mes_full_rederivation.yaml` — state `re_frozen_to_geodesic_sag_consistent_anchor`: MES re-freeze EXECUTED with explicit owner sign-off (REV-R187/R188, registry MES-REFREEZE): the actual geodesic derivation attached (two engines), the hierarchy-preservation theorem forces e1=0, W2_max re-frozen 1.3087e-6 -> 3.3789e-13; frozen anchor preserved byte-identical (successor pattern); MESb print-only internal rederivation remains blocked (rank 7)
- `k5_omega_k_higher_order_ceiling.yaml` — state `branch1_executed_slaving_transfer_ceilings_registered`: exit-gate branch 1 EXECUTED (REV-R184/R185, registry OMK-REOPEN): exact curvature->shear slaving kappa = -1/(2+q) on the LRS-III/KS slaved mode; six labeled attribution x era |Delta Omega_k| ceilings on a NEW card; the certified instantaneous null untouched; frozen U_k plugin NOT modified; nothing promoted
- `t3_king_ellis.yaml` — state `ten_item_program_executed_lower_w2_withdrawal_upgraded_to_dynamical`: the ten-item rotating-congruence program EXECUTED (REV-R181/R182, registry KE-FRAME/KE-OBS/KE-DYN): rotating perfect-fluid development exists at Omega_k>0; at Omega_k=0 doubly obstructed (momentum constraint + dynamical irrotationality) -- the lower-endpoint W^2 withdrawal is now dynamical within the group-invariant perfect-fluid class; W^2 re-attribution stays a registered interpretive question
- `gf_interval_latent_quotient_bug.yaml` — state `resolved_in_successor_and_iff_retracted_superseded_by_T2G`: closed by the v8 successor + v9 T2G retraction cycle
- `psd_cone_redesign.yaml` — state `reviewed_fixes_applied_behind_graded`: representation-only redesign, shipped behind the graded comparator; dual review signed off (v8-update)
- `teff_representative_nonclaims.yaml` — state `registered_nonclaims`: future obligations discharged in the v8-update cycle; the nonclaims registration itself is the steady state
