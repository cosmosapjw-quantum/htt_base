# R65 R9/C9 independent final review

Verdict: **NEEDS_CORRECTION**. Three LOW-severity provenance/documentation corrections are required before scoped branch publication. I found no blocking defect in the implemented conditional likelihood, paired source-influence covariance, stated numerical results, weighted RACS transport, or the finalizer's additive original42/P4 preservation logic. This verdict does not call for another fit, bootstrap, scientific test pass, source download, or research loop.

Submission status: **NOT_READY_TO_SUBMIT**. Journal submission: **NOT_READY_TO_SUBMIT**. A subsequent scoped PASS would certify the reviewed package within its stated working models; it would not certify cosmological significance, standalone novelty, or the original P4 scientific acceptance.

## Identity and actual review scope

- Reviewer: one fresh independent R9/C9 lane, not an author of the reviewed calculations. Requested profile `gpt-6-astra/xhigh`; observed runtime identity **UNKNOWN**. No children spawned.
- Native checkout: `/home/cosmosapjw/Dropbox/bianchi/htt_base`; assigned branch `research/r65-dipole-anomaly-20261117`; parent/base `d76ef3a4e9b33c4703a02647b3aa850004d04253`.
- All native operations were read-only: focused file reads, file inventory, JSON extraction/summary, existing small-file SHA-256 calculation, and inspection of canonical YAML/JSON. I did not execute science code, fits, bootstrap, pytest, or finalization; download datasets; change native files; clone/worktree; commit/push; or inspect/rewrite the 1,084 protected preexisting untracked files.
- Read the root and HTT `AGENTS.md` and native `htt-reviewer-mode-pre-submission/SKILL.md`. Examined the cosmological/frame, inference, numerical, software/provenance, claim-hygiene, and family-identification views within this one reviewer.
- Read the three new inference modules, all five R65 scripts, three test files, full theory/design/report/plan/refinement/validation documents, history and source notes, test/CAS/execution receipts, and relevant saved-result fields. Read the reused R58 `fit_linear` implementation (lines 34–158). Result JSONs were inspected through focused summaries, not every nested posterior-manifest field. No independent visual QA is claimed; the root separately reported checking the paired figure.
- Existing test logs show 24 original cases plus 13 overlap cases, with process return code 0. Eleven saved SymPy checks are true; the Wolfram receipt contains the reported symbolic identities. Actual production receipts record return code 0. I inspected this execution evidence rather than issuing a new PASS from a rerun.
- Reopened the authoritative NRAO catalogue help at `https://www.cv.nrao.edu/NVSS/NVSShelp.html`, especially its raw/fitted/deconvolved semantics (lines 1–6 and 18–20). A bounded attempt to reopen the version-pinned provider plotting source through the web tool failed with `DisabledError`; its prior successful source inspection remains documented in `REVIEW/r65_nvss_flux_source.md`. No new comprehensive literature search or priority certification was performed.

Hereafter `D` denotes `docs/research_program/observational_publication_20261015/R65_DIPOLE_ANOMALY_20261117` relative to the native checkout.

## Complete finding set for the single bounded correction episode

### R65-R9-01 — LOW — OPEN: provider correction provenance is asserted more strongly than established

**Claim at issue.** The active result labels the named-table field “corrected peak”, and the plan states that survey bias correction and rounding *were applied*. The evidence establishes a distinct provider `peak_flux` field and numerical consistency with correction/rounding, while explicitly saying that the extraction/correction pipeline was not located or replayed. Knowing that the NRAO fitted-output convention applies bias corrections does not establish which exact procedure produced this third-party table.

**Evidence.** `D/RESEARCH_PLAN_KO.md:100`–102 explicitly says “survey bias correction과 rounding이 적용된”. In contrast, `D/REVIEW/r65_nvss_flux_source.md:32` and `:50` qualify the unavailable extraction pipeline and only claim consistency of the differences with correction and rounding. The stronger label appears in `D/REPORT_KO.md:8`, `:59`, `:169`, `:240`; `scripts/r65/run_r65_integrated_flux.py:42`, `:62`, `:65`; `scripts/r65/summarize_r65.py:165`, `:167`, and the paired-figure label; `D/RESULTS/INTERPRETATION_SUMMARY.json:39`, `:1418`, `:2010`, `:2111`; and the finalizer's README text at `scripts/r65/finalize_r65_dag.py:260`.

**Minimal correction.** Use the neutral, exactly bound label **provider peak (`peak_flux`)** in active prose, figure labels, source metadata, and corresponding generator strings. Explain once that the differences from raw FITS peak are consistent with known bias corrections/rounding, but the exact provider extraction/correction procedure remains unreproduced. Preserve the field's peak-intensity interpretation, units, exact provider identity, all estimates/covariances/memberships, and the integrated-input-gap closure. An addendum can clarify any historical source-note shorthand without erasing its original inspection evidence. No data refit or new source research is needed; update presentation metadata and, if necessary, render the saved-result figure again.

**Impact.** This is a source-provenance overstatement, not evidence that the measured provider-peak versus integrated contrast is incorrect. Its numerical target is already defined directly by the two actual fields.

### R65-R9-02 — LOW — OPEN: final handoff still references construction filenames and an outdated figure inventory

**Claim at issue.** The final plan presents scratch/construction names as the authoritative numerical/design/theory inputs, and the theory names a symbolic script that is not the delivered script. The figure-status paragraph does not clearly distinguish the already generated fourth figure from genuinely future panels.

**Evidence.** `D/RESEARCH_PLAN_KO.md:8`–14 points to `r65_interpretation_summary.json`, `r65_design.md`, and `r65_theory.md`; the delivered native files are `RESULTS/INTERPRETATION_SUMMARY.json`, `DESIGN.md`, and `THEORY.md`. The literature/source notes are under `REVIEW/`, while the scripts/modules have their explicit repository locations. `D/THEORY.md:499` names `r65_math_checks.py`; the delivered/executed oracle is `scripts/r65/verify_r65_algebra.py` as bound by `RESULTS/AFFECTED_TEST_RECEIPT.json`. `D/RESEARCH_PLAN_KO.md:328`–330 discusses the three existing figures and the provider paired figure alongside future panels; the file inventory and `RESULTS/FINAL_INTERPRETATION_EXECUTION.json` establish that `NVSS_PEAK_VS_INTEGRATED` already exists and four figures were generated.

**Minimal correction.** Replace the construction references with resolvable native relative links/paths. Keep historical lane execution qualifications intact when changing the oracle filename. State that the original three figures plus the provider paired figure are generated; the additional precision/thermal panels and any membership annotation remain planned. This is a documentation-only correction, requiring no tests or scientific reruns.

**Impact.** Current numerical evidence exists, but the finite paper handoff should resolve to that evidence without guessing aliases or wrongly scheduling completed work.

### R65-R9-03 — LOW — OPEN: high-level next-step wording reintroduces an unconditional LSS gate

**Claim at issue.** The corrected plan and machine-DAG candidate allow the narrow source-selection companion to finish through finite A/B/F work, and require full LSS inputs for an expanded physical-excess claim. Two active summaries still describe LSS calibration as an undifferentiated publication requirement.

**Evidence.** `D/REPORT_KO.md:366`–372 describes bin-dependent LSS covariance calculation as part of “실제 출판을 위한 다음 작업” without the claim-dependent qualification. `scripts/r65/summarize_r65.py:214` and the generated `D/RESULTS/INTERPRETATION_SUMMARY.json:1372` say “P4 companion consolidation and source/LSS-calibrated interpretation remain necessary.” This is broader than `RESEARCH_PLAN_KO.md` section 7's explicit narrow path and `scripts/r65/finalize_r65_dag.py:222`–224, where PAPER depends only on SOURCE-NULL/MATCHED-COMPARISON and LSS-CROSS is required for a physical-excess claim. The README sentence at finalizer line 264 also bundles source/LSS gates without distinguishing the branches.

**Minimal correction.** Align these few summary/generator sentences with the existing decision: finite source/component-null qualification plus one matched conventional comparison are the narrow companion's remaining work; source-matched LSS is required before a physical-excess significance claim, and the RACS refit remains optional for the stronger same-nuisance comparison. Do not weaken the explicit current covariance limitations, original P4 acceptance, or `NOT_READY_TO_SUBMIT`. No new science or additional gate is requested.

**Impact.** This is a finite-scope inconsistency, not permission to call the present Poisson tail cosmological or to declare the original P4 paper ready.

## Scientific and implementation assessment

The exact quotient is correctly restricted to the discrete pixel-centre loglinear Poisson model. Conditioning each ring gives the stated multinomial partition, score, and information; ring-constant axial dipole/axisymmetric STF terms disappear. The physical linear-density counterexample retains its second-order axial sensitivity, so no universal no-go is smuggled into the result. Angular STF is kept distinct from spacetime shear, and the missing axial component is not assigned a finite physical variance.

The production fit retains full nuisance covariance and checks identified information and Newton convergence. In the saved independent/common/shared-response fit objects, the largest reported absolute score is about `1.0143e-5` in one clean-mask model against positive information eigenvalues; most are orders of magnitude smaller. The provider primary scores are below `2e-10`. These are consistent with stationary finite fits, not proof of physical selection correctness. Fixed-CMB nuisance diagnostics are not stored as complete fit objects, so I did not independently inspect their curvature/score; their likelihood results and successful production receipt are preserved.

The source-overlap implementation is the empirical event Gram of profiled per-source influences, with the shared-count margins checked and the full cross block retained. The resulting covariance-of-difference formula and right-minus-left sign convention are consistent. Tests use independent explicit source rows, identical-selection zero contrast, disjoint-selection variance addition, frame transport, invalid margins, and a known-information example. This supports the implementation within the independent-component/source-Poisson influence approximation; it does not account for LSS or common galaxy parents.

The core saved numbers agree with the report: provider counts `241892/263158`, overlap `241892`, integrated counts `(127130,72123,63905)`, contrast `(-0.0016440241048542,0.0055246718267598)`, paired SD `(0.0008983629267304,0.0010299225889981)`, Wald `30.9894689604834`, and working 2-df tail `1.86518672871015e-7`. Omitting the cross block gives `1.31543967282267`. The integrated common-bin LR `2.68303023928328`, 6-df fixed-CMB tail `0.0013169967959857`, and 2-df shared-beta/CMB tail `6.58587477609468e-5` represent different questions and are kept separate. Common-u and shared-beta are correctly identified as nonnested when the responses differ.

Finite-bin boundary response has the correct upper and lower terms under its restricted integrated-flux/SED assumptions. The beta-plus-common-residual diagnostic genuinely has rank four for the supplied unequal responses, while the saved correlations near `-0.997185` and beta errors of `9.206/10.386` CMB-speed units establish weak practical separation rather than impossibility. The reused R58 Cholesky/SVD kernel transports the complete covariance.

RACS code preserves the original nested weights, zero-weight rows, coordinate convention, speed normalization, posterior population moments, and inverse weighted-CDF quantiles. The transverse CMB normalization is appropriate. Six source models are projected, with no new likelihood/training or independent NVSS product. The saved manifest fields retain actual dirty/reproducible states (low3 fiducial clean/reproducible; the other five marked dirty/non-reproducible); no clean-source assertion was invented. The existing ablation and posterior-versus-likelihood caveats are adequate for this scoped use.

## Novelty, acceptance, and bounded closeout

The minimal defensible current claim is a measured provider-field-selection dependence of the transverse NVSS component-count dipole under a declared declination-conditional model, with actual shared-source uncertainty, plus secondary source-posterior RACS projections. The report appropriately refuses estimator/GLS/five-view priority, independent information gains, a cosmological anomaly resolution, global tilt, and Bianchi attribution. The independent-component working-law tail must remain labelled as such.

I directly inspected the current canonical state: 42 nodes with canonical serialized SHA-256 `e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d`, backlog/status counts 288/223, and the existing P4 R63 pointer and submission contract intact. The finalizer checks all prior cards and metadata, restores papers after removing only the new additive pointer, preserves the original42 digest, and permits only the one 289/224 insertion. Its current future dependency structure is appropriate. I did not execute it; root must still obtain actual canonical/mirror/publication-DAG validation and publication receipts.

Close all three wording/provenance findings in **one bounded correction episode**, preserve numerical arrays and original execution evidence, and return the corrected file identities plus the focused changes for one limited closeout review. No additional reviewer, science fit, bootstrap, full suite, speculative audit, new acquisition, or successor loop is needed. The submission state remains `NOT_READY_TO_SUBMIT` throughout.

Selected reviewed input identities:

- `r65_count_quotient.py`: `3cfa8dc552f4399cf77e8dd4cf744c59a065c831f5cd3f71485369b9c9832b91`
- `r65_overlap.py`: `764050b1b39b3d8934f66135f707e8b88457f49311c29f847a1026332bfacef1`
- `r65_racs.py`: `2e6552994b98c25d17d9ed61be65d46493abef35d01ede5a8e5103953fd32405`
- `scripts/r65/summarize_r65.py`: `74fca10f5040341b342a31cb0022bdb273888fc6c6c031b4cb69b7166e390fe5`
- `scripts/r65/finalize_r65_dag.py`: `e9e76e2158f7ea9487c593298f3657e9c2b80c06922c7e8a4c7007a5e74d8b8d`
- `D/RESULTS/INTERPRETATION_SUMMARY.json`: `d09fdb7398db9f44888309bdf7b42460a1376ef6565ada70ab9b922b178bf274`
- `D/REPORT_KO.md`: `39eddab32b481c823f18a5f5022f647c0eaeca7b6b23f51689d156c9696915d5`
- `D/RESEARCH_PLAN_KO.md`: `56041b84a896a8d4124f742a7ee55286cd779967b180bad50cbc34864942e097`
