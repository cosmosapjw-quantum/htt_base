# Independent review — observational reboot, 2026-10-14

Status: **PASS_SCOPE_ONLY**. All four scoped findings are closed; no BLOCK_NOW finding remains. This verdict covers the RB00 enabling package and its exploratory/synthetic results, not full physical Planck null admission, native family identification, or completion of the all-feasible analysis campaign.
Reviewer: separate fresh-context read-only reviewer; not an author. No remote mutation, new checkout, expensive scientific rerun, or child reviewer was performed. Requested model/effort: gpt-6-astra/ultra, as recorded by the parent in final DELIVERY.json; observed model/effort: UNKNOWN. The requested configuration is not observed runtime attestation. Review baseline: `b2afb6e2e60695f75ed0dbae21e9fde691bf926c`, tree `da485ff072a67370ad7f0583e7a7719c1bc22fb9`, branch `obs/legacy-reboot-20261014`, primary checkout `/home/cosmosapjw/Dropbox/bianchi/htt_base`.

## Scope and evidence read

Read current `AGENTS.md`, `docs/harness/CURRENT_CODEX_RUNTIME.md`, and the repo physics/math, statistical-hardening, scientific-code-validation, manuscript-figure, DAG, local/global and adversarial-review skills. The current native-execution and existing-checkout provisions take precedence over historical CUH-G instructions. Read the four candidate scripts and four focused test files; retained rank core and harmonic-design/cache-gate functions; `THEORY_REBOOT.md`, `LEGACY_REBOOT_REVIEW.md`, `METHODS.md`, source audit, analysis opportunity inventory, detailed reboot DAG, autonomous goals and handoff. Checked the original extracted legacy report's §§12–13 and 20–22, rather than treating the research agent's summary as an independent verdict. This is a scoped review, not a fresh audit of the entire historical repository.

Independent external verification:

- Planck 2018 IV, §3.5: https://arxiv.org/html/1807.06208v2 . Retrieved text confirms 300 independent noise-plus-systematics simulations, 999 CMB-only simulations, and fixed actual-data component-separation weights that permit separate linear propagation. Direct A&A open failed; indexed/arXiv primary-paper text succeeded.
- Maintained `plancklens.sims.planck2018_sims`: https://plancklens.readthedocs.io/en/latest/_modules/plancklens/sims/planck2018_sims.html . Actual source lines 39–68 confirm delivered temperature signal-plus-noise map addition, field0 and conversion K→microK. This supports the recipe, not upstream byte identity or physical adequacy for this particular low-ell statistic.

Actual remote PNGs inspected: synthetic calibration campaign, response-identifiability laboratory, and SMICA joint-null maximum. Source/result JSON and test/repair receipts were read on the remote primary checkout. The reviewer did not repeat the 512 MB cache projection; the executed cache-hash gate and output receipts are retained evidence.

## Findings and targeted closeout

1. **CLOSED — figure title clipping.** `scripts/calibrate_reboot_statistics.py:plot_result` puts the complete long pilot label in a one-line title. The actual `results/smica_pilot/joint_null_maximum.png` clips the right-hand end of `NOT physical Planck p`. Wrap or shorten the title with an explicit visible scope subtitle; regenerate PNG/PDF from retained scores without rerunning the data analysis. Closeout: the parent wrapped the title at60 characters, and the reviewer inspected the actual remote regenerated PNG; the complete restriction is now visible. Synthetic campaign and response-laboratory PNGs are legible and internally consistent.
2. **CLOSED — bounded numerical helper nuisance scaling.** `scripts/analyze_reboot_identifiability.py:information` thresholds nuisance singular values at `1e-10*max(s[0],1)`. An exact nuisance reparameterization can change the computed span: with `g=[0,1,2]^T`, `b=[1,1,1]^T`, `C=I`, the existing helper returns information approximately2; replacing b with `1e-12*b` returns5 although the mathematical answer remains2. Reproduced by independently executing the candidate function in scratch. The delivered laboratory uses declared dimensionless order-one columns, so no reported laboratory result is invalidated. The parent normalized nonzero whitened nuisance columns before SVD and added reparameterization/zero-nuisance regressions. The reviewer independently repeated the minimal falsifier against the revised local function: normal and1e-12-scaled nuisance both give2 within floating-point rounding; zero nuisance gives5. Remote final hashes match the reviewed local source, and `evidence/final_tests` records24passing tests; closeout complete.

The earlier cache identity-kind failure was an author-discovered actual defect, not an independent finding: `evidence/run_2.json` records exit2 before projection. The repaired code compares the gate's `cache_hash` field with the pinned cache digest, then the existing provider hashes the actual cache. `repair_0` records 5 passing pilot tests and `repair_1` records the successful actual pilot. Preserve both failure and repair; do not reinterpret this as a failed physical null.

## Physics/math audit verdict

No blocking sign or normalization defect found in the scoped theory and current calculations. Metric(-,+,+,+), sky direction n=-e, beta=v/c, thermodynamic Doppler weight1, declared frames and temperature units are explicit. Direct first-order pullback gives `delta T=(beta.n)T-[beta-(beta.n)n].grad(T)` and quadrupole decomposition `3 beta_<a Q_bc> n^a n^b n^c -(4/5)(Q beta).n`, consistent with the legacy source. The stated full-Frobenius Gram and STF normalizations agree with the conventions; Q/O temperatures are not equated with shear/vorticity.

The nuisance quotient identity, shared-response kernel, correlated difference covariance, and conditional Fisher formula have the proper scope. The two-shell full-rank example is explicitly synthetic, not a survey guarantee. The radial affine skew kernel is not promoted to a universal vorticity no-go. The restricted LRS Bianchi-I temperature law is an idealized history-dependent benchmark, not an implemented native cosmological solver. No native family detection, source attribution, unrestricted uniqueness, optimum statistic or novelty claim follows.

The legacy archive's D_l/C_l and epsilon conventions are kept separate. Old PPC tails, K1 morphology ranks, posterior exceedance, and source-conditional evidence are distinct objects. The new four-power pilot is not a replication of the historical six-statistic p=.039.

## Statistical/code assessment

- `pooled_rank_p` is reused with observation-inclusive `(1+k)/(B+1)` and conservative `>=` ties. Exactness requires pooled exchangeability; the +1 is not offered as a validity proof.
- The complete joint row is the simulation unit. Shared/correlated features remain columns, and each full row undergoes the same max transform. The global result and adjusted component ranks claim complete-null control only; strong familywise control under partial alternatives is not asserted.
- Independent training determines centers/scales before calibration. No observed or held-out row enters these estimates. IDs are disjoint in the current 60/240 split; no signal or noise recycling is used among the selected300 pairs. Unique IDs are correctly not treated as a proof of the physical probability law.
- Clopper–Pearson intervals target the IID null exceedance probability q conditional on the observed threshold and training. They are not intervals for the realized discrete rank and are not simultaneous feature intervals. This distinction is correct.
- The real harmonic design uses `[Y_l0,sqrt(2)ReY_lm,sqrt(2)ImY_lm]`. Full ell0–5 is fitted together; the first4 monopole/dipole coordinates are dropped only after fitting. Signal/noise coefficient addition preserves linear projection and the power cross term. Reported selected-sky fitted powers are estimator-specific, not unbiased recovered full-sky C_l.
- Cache identity, support, shape, finite-value, unit and numerical conditioning guards are appropriate for the fixed current pilot. Omitted high-ell leakage and true observed/simulation foreground/systematic matching remain science inputs, not solved by internal low-mode injection.

## Actual executed evidence

| Evidence | Observed outcome | Interpretation |
|---|---|---|
| `evidence/run_0` | 23 tests passed, exit0; unused Axes3D import warning | Focused implementation evidence, before gate repair |
| `evidence/run_1` | Synthetic campaign exit0 | B999,1000 repetitions; joint-max60/1000, naive selected-min145/1000 |
| `evidence/repair_0` | Pilot tests5passed, exit0 | Corrected gate-field identity check regression |
| `evidence/repair_1` | Actual SMICA pilot exit0,16.345 s outer elapsed | Cache projection completed; script receipt15.327 s, peak RSS571240 KiB |
| `evidence/final_tests` |24 tests passed,exit0; optional Axes3D warning | Final repaired focused suite |
| `evidence/response_final` | Exit0 | Rebuilt fixed laboratory after nuisance-column normalization |
| `results/response_laboratory` | Ranks0,3,0; information2 and26/49 | Known-SPD synthetic laboratory only |

The synthetic joint-max rejection frequency .06 has95% binomial interval [.046095,.076560]; it is a diagnostic compatible with nominal .05, not a new theorem or a threshold-based admission PASS. The response laboratory shows near-degenerate singular values shrink with the added depth-response amplitude, so formal full rank alone does not ensure useful precision.

Actual SMICA result: train60/calibration240; selected pixels38413 of49152; full36-column OLS Gram condition6.388756; operator/design identity residual2.11e-15. Global high-extreme score1.161365,128 exceedances,0 ties: rank129/241=.5352697095, finite floor1/241=.00414938; q_hat128/240=.5333333 and95% q interval [.46805793,.59777530]. C2 unadjusted rank27/241=.1120332. The current result is an **exploratory retrospective conditional delivered-simulation rank**, not confirmatory physical Planck significance, an isotropy proof, a local/global posterior, or Bianchi detection.

## Current blockers versus future scientific inputs

No remaining numerical/figure delivery blocker after the targeted repairs. Final GOALS/DELIVERY/README/handoff, generated Markdown report, all4 rendered PDF pages, integrated DAG evidence and final source identities have been checked. All9 paths in the remote candidate_hashes.json matched an independent actual-byte hash read. The5 source-script identities and REBOOT_PLAN/GOALS hashes also match the locally reviewed source. The expanded-packet AO17 mapping was corrected to COSMOS-Web descriptive selection/depth work and checked in local final source. Report prose was also corrected: archive .078/.079 are the multichannel T_all PPC (dipole, CF4, D2/D3), and historical sourced numbers are separated from newly generated numerical values.

Real future science inputs: physical observed/simulation adequacy and residual-systematic response; finite-pixel/high-mode leakage bounds; source-bound physical dipole and local/global responses; selected CF4 law and cross-data covariance; posterior/admitted transfer outputs; native morphology atlas and family-equivalence controls for native family claims. These limit their associated claims. They do not block conditional analysis, implemented diagnostics, source acquisition or other ready goals.

The broad goals and detailed DAG correctly distinguish enabling-unit completion, execution-ready work and scientific admission. The opportunity census explicitly remains sampled/expandable. No assertion that all feasible analyses are already finished is supported by this review.


## Final report, DAG and identity closeout

The actual four-page PDF was inspected at `/tmp/reboot_report_render_20261014/page-1.png` through `page-4.png`: table values, figure labels, scope restrictions, captions and source pointers are legible; no clipped claim text or missing figure remains. The PDF is an English report and the paired Markdown report is Korean. PDF SHA256: `801c81831f3f619249fc7881ba5985b92d0251a6e2d3dd0e47221ee735142000`.

`evidence/integration_checks.json` records exit0 for expanded packet tests, packet DAG, mirror synchronization, strict canonical DAG and report generation. Actual logs show5expanded packet tests passed and237canonical PRs form a valid DAG. The reviewer independently compared each of23task IDs/titles/dependencies against its canonical PR mapping: no mismatch. The9goals cover all22pending tasks and all20opportunities. Both canonical backlog/status mirrors were byte-identical at review. `PR-OBS-REBOOT` was in_progress at closeout; changing that scoped card to completed after this verdict, syncing and validating the status is the parent's next action. All22successor cards remain pending.

The report builder's new results derive from retained JSON; historical numbers have explicit source prose. Initial pilot execution used the pre-title-repair calibrator hash; the final calibrator change only wraps the figure title and the plot was regenerated from saved numerical inputs. The original numerical receipt is retained rather than overwritten to pretend a rerun.

Final reviewed source identities:

| Path | SHA256 |
|---|---|
| scripts/calibrate_reboot_statistics.py |64a147a6424573429d9cdcbf29be0b5b88dbaeaa2fb93402f102caeeca4a269a|
| scripts/run_smica_reboot_pilot.py |9bc43dbba074c6f8b8c79154f54b87c620825e6960a3625e727f5f1f39f6beea|
| scripts/analyze_reboot_identifiability.py |14d4d6df2ec4564afd9d6545ab8ce029a33bfa4cbe1c5e6a600340e7d3e791f5|
| scripts/reboot_task_packet.py |f233e520ed5a1b9131b87bc00b2813e93ef76dad71e249441901ad12028c86bc|
| scripts/build_reboot_report.py |78b583fb559542be48748dc4d1498681e4a28f0e4135ee6ba01fedc9e8a753a5|
| docs/observational_reboot_20261014/REBOOT_PLAN.json |6726239caca48de5c5f3faa789d0214abc16b558b7b611dc76c824b75db4dc61|
| docs/observational_reboot_20261014/GOALS.json |1414315c4c9f752063d1938a4efbd92e671e1c901f2f0d90c1a777a536e969d2|
| docs/observational_reboot_20261014/results/report/report.json |baf3ea28d028ba20aaa3521d19c235e4fa3da8bb8156f781959ca47afffa3d3a|

The final verdict does not verify a later Git push/merge. The parent should proceed with the already-authorized scoped publication, record actual ref/commit/tree, then continue the ready goal queue. Future scientific-input limitations are preserved; they are not blockers to publishing this accurately scoped enabling result.


## Editorial addendum — model/reasoning recommendations, 2026-10-14

**PASS_SCOPE_ONLY maintained.** Reviewed only the five new/updated local documents `MODEL_POLICY_KO.md`, `MODEL_POLICY.json`, `CODEX_HANDOFF_KO.md`, `README.md` and `NEXT_TASK.json`. No new broad audit, numerical execution, remote mutation or review dispatch was performed; prior scientific/code/results review remains unchanged.

The human-readable and machine-readable allocations agree: parent `gpt-6.1-sol/high`; physics/statistics and independent reviewer `gpt-6-astra/xhigh`; implementation `gpt-6.1-sol/medium` with escalation to `high`; bounded low-cost work `gpt-6-luna/medium`. These are prospective recommendations, not a benchmark or retroactive runtime claim. The previous reviewer request `gpt-6-astra/ultra` remains a historical request; the new recommended reviewer setting does not rewrite it.

All five documents preserve the four-agent limit including the parent, sole production writer, independent nonrecursive review, requested/observed runtime separation, and autonomous continuation through the ready goal queue. The optional Ultra/Max descriptions do not override those limits or assert an actually executed run. The observed remote config is explicitly described as unchanged `gpt-6-sol/medium`; advertised model-cache support is separated from execution evidence, with unknown observations retained as UNKNOWN. No model upgrade is treated as replacement for missing data, physical-law validity or scientific admission. No new permission requirement or scientific claim promotion is introduced.

This addendum checks editorial/contract consistency against the parent's supplied official-source/config evidence; it is not a fresh product-documentation audit or independent config readback. Both JSON files parse successfully. No actionable finding remains in this bounded change.

Reviewed local document hashes:

| Path | SHA256 |
|---|---|
| docs/observational_reboot_20261014/MODEL_POLICY_KO.md | aabbba703cffcbe67cdbc2a3e70f14ea473aaa355d44c788a894f307261625e0 |
| docs/observational_reboot_20261014/MODEL_POLICY.json | 7d256fc061f679093afbe2705c69bbd99b7263eec77d7f3a9aa4ac55930ed394 |
| docs/observational_reboot_20261014/CODEX_HANDOFF_KO.md | a2b29c6081f1f0ca559e1d86f43f3c825bb169af037fce41c1bc2b5a33981991 |
| docs/observational_reboot_20261014/README.md | e476c37b35888e83f2df1a2ff33a41abc94f05ba6e6dba1f4ac4c0f90d085991 |
| docs/observational_reboot_20261014/NEXT_TASK.json | 3eb65c211a21d38022eb64f4fdda1ba7a6b11ec744284954d96c5047098e15e3 |
