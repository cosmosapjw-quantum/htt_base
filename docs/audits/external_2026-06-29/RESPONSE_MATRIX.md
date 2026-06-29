# External-audit response matrix — 2026-06-29 (rev-r135)

Two external audit packs arrived (separate from the internal phys-math-code audit,
committed at `ee22a1f` / CHANGELOG rev-r134):

- `htt_research_evaluation_review` — **MINOR REVISIONS** (research-content review of the
  evaluation package). Verdict: near-publishable methods/identifiability/bounds program;
  one substantive item (the Ω_k half of the no-go is not the same kind of null as W²) plus
  calibration caveats. 5/5 independent re-checks confirmed (`reviewer_verification.py`).
- `pr08_reassessment_audit_pack` — **MAJOR REVISIONS** (claim-firewall re-review). Verdict:
  not rejected, central idea salvageable, hard boundaries mostly enforced, but several
  conditional/synthetic objects over-promoted and the report's reproducibility section cited
  commands not shipped in the package. 52/52 package tests pass; no fatal family/native/MIO
  violation, "rhetoric overclaims remain".

Both reviewers read the **committed report/table/artifact surfaces**, which lagged behind the
module-level fixes the internal audit (rev-r134) had already landed (`NULL_SECTOR_KIND`,
`exceedance_evalue_finite_null`, the PSD Ω_k-signed fix). rev-r135 propagates those fixes into
the surfaces, downgrades the genuine K5/K6 over-claims, builds the K1 noise-only long-run mode,
makes the evaluation package self-contained, and hardens the linter.

| # | Audit | Finding | Fix (rev-r135) | Where |
|---|---|---|---|---|
| 1 | rev1 §5 / rev2 EGS3-A1 | "joint null {W²,Ω_k}" conflates two different nulls | Relabelled everywhere: **structural null {W²}** (order-independent; response column a genuine zero, not Σ²-collinear) **+ leading-EGS-order no-channel {Ω_k}** (re-opens beyond leading order). New gate proves genuine-zero vs Σ²-collinear-degeneracy (rank alone can't tell them apart). | `build_egs_results_table.py`, `run_egs3_experiments.py`, `main.tex` §EGS3, `egs3_graded_comparator.py` docstring, `pr08_006_joint_artifact.py`, `test_egs3_axis_a.py::test_omega_k_column_is_a_genuine_zero_not_sigma2_collinear` |
| 2 | rev2 theorem audit | NT-A1 still "Quadrupole-filling EGS identity" | → "Closure-conditional quadrupole-filling identity"; κ=4/21 marked registered-ETM-convention | table + report |
| 3 | rev2 / claim_lint | "genuine multi-multipole Fisher-CR floor", "floor nothing beats", "strictly below" | → "Multi-multipole Fisher floor conditional on the registered shear-response profile"; physical calibration awaits native transfer | table + report + figure captions |
| 4 | rev1 NT2-A1 / EGS3-B1 | floor scope not stated | EGS3-B1 marked **single-mode, finite-k**; full-response floor needs the shear-power mode integral | table + report |
| 5 | rev2 NT-B3 | "G_F=1 iff steady" reintroduces zero-denominator branch | → contrast language ("G_F=1 contrast for depth-steady shear") | table + report |
| 6 | rev2 NT2-B1 | "nonzero quadrupole forbids vanishing shear-filling" | → "within the registered closure/H3 model, nonzero a₂ bounds the closure-defined shear-filling away from zero; NOT a generic CMB statement"; C_up=9 documented | table + report |
| 7 | rev1 §6 / rev2 K5 | "release-matched forward mocks" over-claim | → "geometry-and-error matched Gaussian bulk-flow mock mechanics, conditional on a fixed ΛCDM σ_cv=150 km/s/comp prior"; ΛCDM ~150-250 km/s expectation noted; bulk flow stays a measurement; full selection/Malmquist mocks remain a gate | table + report + BLOCKERS + artifact |
| 8 | rev1 §6 / rev2 K6 | "BLOCKED_MISSING_FIELD_REALIZATIONS discharged" over-claim | → "WF mean-field curl-suppression no-go established; true Hoffman-Ribak CR posterior remains blocked"; injection = single solid-body mode; suppression is the WF prior's across modes | table + report + BLOCKERS + artifact |
| 9 | rev1 §6 / rev1 D | K1 component-separation dependence quiet | SMICA 0.097 vs Commander 0.121 (~25%) flagged as a foreground/cleaning systematic, reported side by side, **not averaged**, neither E2E-calibrated | table + report |
| 10 | rev1 B / rev2 PR08-006 | "measured rank-2 comparator" flattens maturity | → "rank-2 = one measured (Ω_tilt) + one partial (Σ²) + two fail-closed"; one full plus one partial, not two measured | report + BLOCKERS + artifact |
| 11 | rev1 §1 / rev2 abstract | "honest publishable envelope … recovers the established low-ℓ CMB anomalies" | → diagnostic methods-and-calibration framing; explicit "does NOT establish a globally significant anomaly, geometry, or family-ID" | abstract |
| 12 | rev1 §C / EGS3-A3 | e-value null idealisation unstated | GRF-ΛCDM null idealisation stated; finite-null α=(k+1)/(n+1) referenced (`exceedance_evalue_finite_null`, already in module) | report §EGS3 + `run_egs3_experiments.py` |
| 13 | rev2 PR09-002 | report cites commands not shipped in the eval package | The 13 referenced scripts/proofs (+ `research_gates/pr04/tests`) bundled into the package; `check_report_references` passes against the `research_evaluation/` subtree | `build_research_evaluation_package.py` + `test_research_evaluation_package.py` |
| 14 | rev1 F | K5 figure title "minimum-variance" vs "weighted-GLS" caption | PNG title was already "weighted-GLS"; stale docstring/caveat fixed | `make_cf4_bulkflow_likelihood.py` |
| 15 | rev1 §E (7th) | manuscript carries "2 genuine pdf_claim_lint findings" | Verified: current manuscript PDF lints **0 failed / 66 warnings** (all `lnB numeric`), identical to the blessed report — does not reproduce; blessed lint report left untouched | (verification only) |
| 16 | rev1 §7.2 / rev2 PR09-005 | K1 E2E null is the one real gating measurement | Built the **noise-augmented long-run mode** (`k1_global_maxscan.py --noise-mc-dir`, route 4): adds a local ΛCDM signal to the real per-method noise sims → separate artifact; method-matched; stays measured_partial (upgrade of, not replacement for, the blocked full E2E). Ready to run when the ~300 noise files land. | `k1_global_maxscan.py` + `test_k1_noise_mode.py` |
| 17 | both packs | over-claims could re-enter | Folded both packs' forbidden-phrase set into a permanent repo gate; committed the independent re-check script | `scripts/claim_lint_research_surfaces.py`, `research_gates/external_audit_2026_06_29/reviewer_verification.py`, `tests/contracts/test_external_audit_2026_06_29.py` |

## Not changed (deliberately)

- The honest content the reviewers praised (fail-closed sectors, ΛCDM-null labelling,
  structural-no-go framing, the corrected NT-A3) is preserved as-is.
- The full CF4 selection/Malmquist mocks (rev2 PR09-003) and the true Hoffman-Ribak CR
  posterior (rev2 PR09-004) are major data tasks, not wording fixes; they remain registered
  blockers (`BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP`, `BLOCKED_MISSING_FIELD_REALIZATIONS`).
- The native low-ℓ solver (rev2 PR09-007 / PR10) stays a separate project.
- No published number changed; x_C bit-identity preserved.
