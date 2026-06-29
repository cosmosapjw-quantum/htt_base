# Critical Re-review — BASS/HTT departure-decomposition programme

**Verdict: MAJOR REVISIONS.** 52/52 package tests pass, and the claim firewall is materially better than the earlier PR04 state. However, the current report still over-promotes several conditional/synthetic objects into publishable-sounding results, and the report's reproducibility section references commands and proof records that are not shipped in the evaluation package. The programme is **not rejected** because the central idea is salvageable and the hard boundaries are mostly enforced, but it is not submission-ready.

## Minimal defensible claim

Today the project can honestly claim a diagnostic, provenance-bound comparator framework for four sectors `(Sigma2, W2, Omega_tilt, Omega_k)`, with a rank-aware analysis showing that the registered low-ell CMB-T and radial peculiar-velocity channels reach only `Sigma2` partially and `Omega_tilt` as a kinematic bulk-flow descriptor, while `W2` and `Omega_k` remain fail-closed. It also contains useful conditional theorem/gate mechanics for nuisance-projected identifiability, radial-vorticity blindness, transverse re-opening, PSD bookkeeping, and restricted Bianchi-I moment dynamics. It **does not** yet establish an anisotropic geometry, Bianchi family, global tilt posterior, native low-ell solver validation, globally significant CMB anomaly, or physical vorticity measurement.

## Novelty assessment

The publishable novelty is not “Bianchi detection” and not “solving the CMB anomalies.” The credible novelty is a **methods/theory paper**: a rank-aware graded comparator that refuses scalar collapse when sectors are blind, plus explicit no-go/re-opening channels and Bianchi-I multifluid tilt-moment counterexamples showing why scalar summaries are not dynamically sufficient. Without a native low-ell Bianchi-Boltzmann solver this is still publishable if framed as identifiability/calibration methodology and conditional GR/Boltzmann theorem infrastructure. It becomes much weaker if phrased as a measured cosmological departure.

## Fatal blockers / blockers that invalidate stated results

1. **K5 coverage is not yet full release-matched cosmic-variance coverage.** The script keeps real positions and per-group errors, then draws a Gaussian bulk flow with a fixed `sigma_cv=150 km/s` per component. That validates conditional mechanics, not the published phrase “release-matched forward mocks” including Malmquist, grouping, selection, correlated velocity fields, and cosmic variance. See `scripts/k5_cf4_release_coverage.py:69-113`, `docs/generated/k5_cf4_release_coverage.json:1-65`, `docs/final_report/main.tex:1128-1139`.

2. **The report's reproducibility section is stale.** It advertises multiple commands and proof records not present in this self-contained archive, including `scripts/prove_egs_lowell_theorems.py`, `scripts/make_lowell_morphology_real_map.py`, `scripts/make_cf4_bulkflow_likelihood.py`, `scripts/make_cf4_affine_flow.py`, `docs/generated/egs_lowell_theorem_proofs.json`, and `docs/generated/pr04_paper_theorem_proofs.json`. See `docs/final_report/main.tex:1240-1274` and `outputs/missing_report_references.json`.

3. **Several theorem labels are still over-strong relative to their assumptions.** The main text carefully downgrades NT-A1/NT-A3/NT-B3, but the consolidated table still says “Quadrupole-filling EGS identity” and “G_F=1 iff depth-steady shear.” The NT2/EGS3 “genuine Fisher-CR floor” and “nonzero quadrupole forbids zero shear” statements are only valid under registered response/closure assumptions, not as physical CMB statements. See `docs/generated/egs_results_table.md:12-24`, `docs/final_report/main.tex:838-870`, `docs/final_report/main.tex:1023-1032`.

4. **K6 is a structural no-go on the WF field, not a discharged vorticity posterior.** The code still uses independent per-cell Gaussian draws from `v_mean/v_std` and explicitly says cell-cell covariance is ignored. This supports “curl-suppressed reconstruction,” not a physical vorticity posterior nor a true constrained-realization posterior. See `scripts/k6_cf4_curl_posterior.py:69-108`, `scripts/k6_cf4_curl_posterior.py:111-167`, `docs/generated/k6_cf4_curl_posterior.json:1-36`.

## Theorem audit

| Item | Status | Issue | Required fix |
|---|---|---|---|
| NT-A1 | Minor revision | Main theorem is now closure-conditional, good. But table/proof labels still call it an EGS identity, and `kappa=4/21` attribution remains incomplete. | Rename everywhere to “closure-conditional quadrupole–filling identity.” Keep `kappa` symbolic unless exact ETM equation/convention is provided. |
| NT-A3 | Minor revision | Main theorem is correctly a single-estimator sampling variance. EGS2/EGS3 still uses “genuine Fisher-CR floor” language based partly on toy/semi-native response. | Split actual full-sky estimator variance from response-model Fisher floor. Use “conditional Fisher floor under registered response model.” |
| NT-B3 | Minor revision | Main theorem uses additive contrast and rank-gated attribution; good. Generated table still says `G_F=1 iff`, which reintroduces the zero-denominator branch problem. | Regenerate results table and figures with contrast-language only. |
| NT2-A1 / EGS3-B1 Fisher floor | Major | `egs2_fisher.py` uses a toy response; `shear_quadrupole_seminative.py` uses a Gaussian visibility and single-mode transfer, not a native Boltzmann solver. | Downgrade “genuine” and “nothing beats.” State “conditional on the registered response profile; physical calibration awaits CAMB/CLASS or native solver.” |
| NT2-B1 / bracket | Major | “Nonzero quadrupole forbids zero shear-filling” is false in ordinary CMB interpretation unless the closure/H3 hypotheses are loaded. The constants include placeholders (`C_up=9`, `R_STAR=1`). | Restrict to “within the registered closure and H3 derivative-correction model.” Do not present as a data theorem. |
| EGS3-A1 rank-2 | Minor/Major wording | The rank-2 statement is correct for the registered channel model, but not a universal theorem about all low-ell CMB or all peculiar-velocity information. | Use “within the registered leading-channel response map.” Keep re-opening channels explicit. |
| EGS3-PSD | Minor | Faithful as a representation of the nonnegative sector vector and useful for fail-closed bookkeeping. But `M=diag(g)` is not yet a physical covariance/moment matrix. | Call it “PSD bookkeeping / cone representation,” not a new physical PSD moment until off-diagonal sector covariance is defined. |
| Volterra depth memory | Minor | Correct as a constant-H or registered-H ODE/integrating-factor result. It is not an observed depth-gap attribution. | Require explicit H(z), source ownership, and response-rank test before applying to data. |
| Vorticity re-opening | Pass with caveat | Algebraic radial no-go and transverse re-opening are correct. CMB polarization/B-mode re-opening is only named, not transfer-calibrated. | Keep transverse velocity theorem; mark CMB polarization as future transfer-owner work. |

## Statistics audit

| Item | Status | Issue | Required fix |
|---|---|---|---|
| K1 null/look-elsewhere | Partial pass | The max-scan mechanics are valid and global `p=0.097` is clearly under an isotropic GRF null. But PR4/NPIPE/FFP10 E2E remains unbound; parity ratio/asymmetry duplicate information. | Keep as partial. Run E2E summaries remotely; deduplicate or pre-register parity pair treatment. |
| K5 coverage | Major revision | Current mocks are geometry+error matched, not selection/Malmquist/grouping/correlated-field matched. The `±102 km/s` is conditional on a chosen Gaussian bulk-flow prior. | Rename to “conditional prior-inflated coverage.” Build realistic CF4 forward mocks with selection, grouping, distance-method errors, and correlated velocity field. |
| K6 no-go | Minor/Major wording | The structural no-go is honest for the WF mean field. But `blocker_resolved`/“CR posterior” language is too strong because only independent per-cell draws are used. | Keep “curl-suppressed WF no-go.” Remove “discharged field-realization posterior” unless true CR ensemble is owned. |
| PR08-006 rank assembly | Conditional pass | Fail-closed assembly is correct: no scalar `x_C`, no family promotion. But it relies on K5 as measured and K1 as partial; K5 is conditional. | Report rank-2 as `rank-2 conditional/partial`, not fully measured. |
| Identifiability rank | Conditional pass | Correct linear algebra under fixed response/covariance. Needs explicit “local linear response” and model-owner caveats. | Add response-owner IDs, covariance-owner IDs, and numerical-rank tolerance to every rank statement. |

## Claim-tier corrections

Replace:

> “honest publishable envelope … recovers the established low-ell CMB anomalies…”

with:

> “The defensible envelope is a diagnostic methods-and-calibration framework: it reports local/look-elsewhere low-ell morphology under an isotropic GRF null, conditional CF4 bulk-flow descriptors, and a curl-suppressed-reconstruction no-go. It does not establish a globally significant low-ell anomaly or anisotropic geometry.”

Replace:

> “measured rank-2 graded comparator on real data”

with:

> “rank-2 graded comparator with one measured kinematic sector (`Omega_tilt` as CF4 bulk-flow descriptor), one partial CMB sector (`Sigma2` under non-E2E null), and two fail-closed sectors.”

Replace:

> “release-matched forward mocks”

with:

> “geometry-and-error matched Gaussian bulk-flow mock mechanics, conditional on the adopted LambdaCDM bulk-flow prior.”

Replace:

> “BLOCKED_MISSING_FIELD_REALIZATIONS discharged”

with:

> “WF mean-field curl-suppression no-go established; true constrained-realization posterior remains a local-repo task.”

Replace:

> “genuine Fisher-CR floor”

with:

> “Fisher floor conditional on the registered shear-response profile.”

Replace:

> “nonzero quadrupole forbids vanishing shear-filling”

with:

> “within the registered closure/H3 derivative-correction model, the shear-filling is bounded away from zero; this is not a generic statement about observed CMB quadrupole.”

## Claims safe as stated

- No Bianchi family or anisotropic geometry is identified.
- No scalar diagnostic is used as posterior odds or family evidence.
- K1 `p=0.097` is not a detection and remains non-E2E-calibrated.
- K6 is a curl-suppressed WF structural no-go, not a physical vorticity detection.
- `x_C` is withheld when blind sectors would have to be zeroed.
- The rank argument is valid for the declared finite linear response model.
- Radial peculiar velocities are exactly blind to antisymmetric vorticity in the affine model.
- The old/native low-ell solver is not admitted as validation.

## Constructive roadmap

### PR09-001 — Report and table claim surgery
Regenerate `egs_results_table.*`, figure captions, abstract, and blocker dossier. Gate: `claim_lint.py` returns zero hits.

### PR09-002 — Reproducibility repair
Make every command in `main.tex:1240-1274` exist or replace it with the actual package command. Gate: `check_report_references.py` passes in a clean clone.

### PR09-003 — K5 realistic forward mocks
Replace Gaussian bulk-vector prior mocks with correlated velocity-field mocks and release selection. Include Malmquist/grouping/method errors. Gate: coverage for amplitude and components over >2000 mocks; archive exact prior/cosmology/window.

### PR09-004 — K6 true field-realization posterior
Obtain or generate a CR/WF field ensemble. Apply affine decomposition to every realization. Gate: posterior over vector components first, norms second; no per-cell independent draws used as covariance.

### PR09-005 — K1 E2E null
Run frozen max-scan on FFP10 or PR4/NPIPE E2E maps. Gate: provenance manifest with map IDs, mask, beam, NSIDE, component-separation method, exact statistic family.

### PR09-006 — Theorem scope formalization
Make every theorem include `hypotheses`, `response_owner`, `covariance_owner`, `branch`, `not_a_data_claim`. Gate: theorem registry rejects ambiguous “EGS identity/floor/forbids” language.

### PR09-007 — Native solver boundary
Keep native low-ell solver as separate PR10. Gate before any family statement: exact FLRW TT/TE/EE comparator, visibility, polarization, LOS convergence, family support matrix.
