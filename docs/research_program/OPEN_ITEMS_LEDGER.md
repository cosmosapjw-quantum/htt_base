# Open-items ledger — every unfinished research item, ranked by earliest executability

_Generated 2026-07-11 by `scripts/build_open_items_ledger.py` (dev-tier planning artifact; never rendered into any report). Fail-closed against ticket-state drift._

| # | Item | Source | State | Blocker | Executability | Exit gate |
|---|---|---|---|---|---|---|
| 1 | King-Ellis rotating-congruence rederivation (10-item program) | review R1 3.4 (2026-07-10); ticket EGS3-T3-king-ellis; registry T3-full/T3-int reclassification (v9) | constraint_witness_reclassified_lower_w2_withdrawn_dynamics_deferred | — | **now** | items 1-10 discharged as dual-engine (SymPy + Wolfram) seals: tilted-frame kinematics/constraints (king_ellis_frame_seal) + conservation/evolution/local development (king_ellis_dynamics_seal); ticket carries per-item dispositions |
| 2 | Anisotropic-Omega_k higher-order vorticity/curvature re-opening transfer (finite ceiling) | ticket EGS3-K5-omega-k-higher-order-ceiling (exit branch 1; branch 2 executed as documented null, REV-R162) | blocked_on_higher_order_transfer | BLOCKED_HIGHER_ORDER_VORTICITY_CURVATURE_REOPENING | **now** | registered higher-order Omega_k transfer producing a finite anisotropic-curvature ceiling, emitted as a NEW card artifact (frozen cards untouched) |
| 3 | MES registry re-freeze decision (coefficient-branch promotion) | ticket EGS3-G8-mes-full-rederivation (branch_registry_v9_2026_07_10); MES-BR seal (v9) | discrepancy_documented | — | **decision_only** | explicit owner sign-off selecting a coefficient branch; then a re-freeze cycle with a new W2_max anchor |
| 4 | Paper-A/B/C split of the audit-report material | registered plan (v9 report; user decision 2026-07-10: plan-only this cycle) | — | — | **decision_only** | user instruction to execute the split |
| 5 | K1 E2E-systematics null + BipoSH E2E upgrade | ticket EGS3-C1-k1-ffp10-npipe; BLOCKERS.md section 1 | blocked | BLOCKED_MISSING_PR4_E2E_ACCESS | **blocked** | PLA FFP10/NPIPE E2E ensembles on disk (download in flight, ~1TB); then the registered max-scan/global-p mechanics run unchanged |
| 6 | K6 Hoffman-Ribak constrained-realization vorticity posterior | ticket EGS3-C2-cf4-wfcr; BLOCKERS.md section 2 | blocked | BLOCKED_MISSING_FIELD_REALIZATIONS | **blocked** | owned CR ensemble over the CF4 3D WF field |
| 7 | K5 cosmic-variance coverage on release mocks | ticket EGS3-C2-cf4-wfcr; BLOCKERS.md section 3 | blocked | BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP | **blocked** | ownership of the CF4 release-mock pipeline (selection/Malmquist/grouping/correlated field) |
| 8 | PR08-006 joint posterior artifact | BLOCKERS.md section 4 | — | BLOCKED_UPSTREAM | **blocked** | close K1+K5+K6 first (items 5-7); then assemble with explicit measured/partial/fail-closed sectors |
| 9 | Native low-ell Bianchi solver atlas (theory-g CMB likelihood) | BLOCKERS.md section 5; PR10 project | — | AWAITING_NATIVE_LOWELL_SOLVER | **blocked** | PR10-scale separate solver project; fail-closed OutOfScopeError firewall stays until then |
| 10 | MESb (PRD 51, 5942) internal rederivation | ticket EGS3-G8-mes-full-rederivation (remaining) | discrepancy_documented | BLOCKED_MISSING_MESb_PRINT_ONLY_PAPER_II | **blocked** | legitimate access to the print-only journal PDF; then the existing rederivation machinery applies |

## Notes

- **1.** pure symbolic GR + numerics; BV-DYN (REV-R178) supplies the dynamical integrator machinery. EXECUTING this cycle (REV-R179..R183).
- **2.** substantial GR-transfer compute item, no external data; next candidate cycle after item 1.
- **3.** all compute done (3-branch registry, 3 labeled ceilings, eps1 attribution triple); registered values stay frozen until sign-off.
- **5.** PLA/PL3 downloads in progress (2026-07-11).
- **6.** WF mean-field curl-suppression no-go already established.
- **7.** conditional coverage (fixed LCDM sigma_cv prior) already measured.
- **10.** print-only (no arXiv/ADS/OA copy); SAG-1997 discrepancy already documented.

## Closed / held tickets (represented for completeness)

- `gf_interval_latent_quotient_bug.yaml` — state `resolved_in_successor_and_iff_retracted_superseded_by_T2G`: closed by the v8 successor + v9 T2G retraction cycle
- `psd_cone_redesign.yaml` — state `reviewed_fixes_applied_behind_graded`: representation-only redesign, shipped behind the graded comparator; dual review signed off (v8-update)
- `teff_representative_nonclaims.yaml` — state `registered_nonclaims`: future obligations discharged in the v8-update cycle; the nonclaims registration itself is the steady state
