# Final JCAP/PRD adversarial referee report

## Artifact and claim boundary

- Owner: `COMMON`.
- Scope: internal, diagnostic-only pre-solver audit and advocate research ranking.
- Claim tier: `diagnostic_only`.
- Transfer source: `mixed_none_and_external_transfer_conditional`.
- Config hash: `sha256:c6fad2b48a92be732225a005079d98459f7429ffda357d8cc9f2d2bb7d286029`.
- Sky/mask status: `mixed_audit_only_no_directional_promotion`.
- Covariance/null status: `mixed_matched_proxy_blocked_and_not_statistical`.
- Generating command: `venv/bin/python -B scripts/audits/jcap_prd_20260714.py build-final-reports`.
- Git/worktree: `f96e8d9eed9d318141d9ea77ab3ce47c2acecef3` with recorded worktree hash `sha256:67f9d7e29f7886828508ec70e5a1a73593821fad7c83d8ce9424aafa9e49c256`.
- Input hashes:
  - `docs/audits/jcap_prd_adversarial_audit_20260714/advocate_candidate_ledger.json:sha256:0ff8d5d24642ba7fce1652aad406392287545d9a70071715a26d4d71e1a8742f`
  - `docs/audits/jcap_prd_adversarial_audit_20260714/criticism_response_matrix.json:sha256:f0c8c5316d8384bf223addd21c3f319039a26134bdc8507f4ae432206e7e9b0d`
  - `docs/audits/jcap_prd_adversarial_audit_20260714/web_crag_final.json:sha256:660090cf17d1edbb6aaacd1d777e7ff691461ffc79fe9d8bfeb1f42de6a8f218`
  - `docs/audits/jcap_prd_adversarial_audit_20260714/shortlist_freeze.json:sha256:f9e791fba2697e511130bf53c89e32ccf78684cccf40d7730f69ff678757c54b`
  - `docs/audits/jcap_prd_adversarial_audit_20260714/coverage_matrix.json:sha256:8d53a8e12524e4791466f27c1eb2b5a358b5de43afac6a82ffbfb971d2f95916`
  - `docs/audits/jcap_prd_adversarial_audit_20260714/agents/final_referees/jcap_referee_response.json:sha256:c72217aff3bea3aa18bf380945b2b856e066e024f667d3ff6d85e1575a7b10cf`
  - `docs/audits/jcap_prd_adversarial_audit_20260714/agents/final_referees/prd_referee_response.json:sha256:6e50184973274463e54e99da24681c844e322f88b0fef4dc9fe7f67efbb19bfb`
  - `docs/audits/jcap_prd_adversarial_audit_20260714/agents/final_referees/skeptical_referee_response.json:sha256:b74ea0c0bcb5f4b6791f384dba5b3ca4ae9419bf677e63d1ae8ed57eeb1c49c6`
- Baseline under audit: `8af39b36c1d5ed4f9b16f0bc71dbecd8b22548d4`.
- Current audit mechanics do not repair production results or validate an external/native transfer.
- Counterfactual family/geometry candidates remain `hypothesis_only=true`, `public_use=false`.
- DAG completion is bookkeeping, not scientific readiness.

## Editorial decision summary

| Referee | As-shipped decision | As-shipped score /10 | Post-surgery decision | Post-surgery score /10 |
|---|---|---:|---|---:|
| JCAP | REJECT | 1.0 | NEW_SUBMISSION_AFTER_MAJOR_REBUILD | 6.5 |
| PRD | REJECT | 1.5 | NEW SUBMISSION AFTER MAJOR REBUILD | 5.5 |
| Independent skeptical | REJECT | 1.5 | NEW_SUBMISSION_AFTER_MAJOR_REBUILD | 5.0 |

### JCAP referee decision

- **As-shipped:** REJECT (1.0/10).
- **Post-surgery:** NEW_SUBMISSION_AFTER_MAJOR_REBUILD (6.5/10).
- Thesis allowed by this referee: A defensible pre-solver paper is a methods and negative-audit result: hash-bound reruns and constructive counterexamples show that the shipped positive-science conclusions are not identified under their stated estimator, null, theorem-domain, transfer, and provenance assumptions, while a claim-tiered workflow can preserve conditional mathematics, numerical failure diagnostics, and explicitly blocked or set-valued outcomes without promoting an anisotropy, geometry, family, or native-transfer claim.

### PRD referee decision

- **As-shipped:** REJECT (1.5/10).
- **Post-surgery:** NEW SUBMISSION AFTER MAJOR REBUILD (5.5/10).
- Thesis allowed by this referee: The theorem-only contribution can be a frame- and domain-explicit proof that the declared low-rank observables possess cancellation and response-kernel directions and therefore cannot certify FLRW, global tilt, geometry, or a Bianchi family. The estimator-validation-only contribution can demonstrate, with exchangeable scans and independently implemented numerical oracles, how CF4 nuisance leakage and finite-null asymmetry invalidate the shipped anomaly while yielding honest non-identification or abstention. External-transfer examples remain transfer-conditional; any morphology, geometry, or family statement remains native-solver-dependent. This is a pre-solver methods and negative-audit thesis, not evidence for cosmic anisotropy.

### Independent skeptical referee decision

- **As-shipped:** REJECT (1.5/10).
- **Post-surgery:** NEW_SUBMISSION_AFTER_MAJOR_REBUILD (5.0/10).
- Thesis allowed by this referee: A sharply downclaimed paper can report a hash-receipted, claim-tiered adversarial audit of a pre-solver anisotropy framework: selected audit-only recomputations show that radial-monopole leakage, an unsupported velocity-shape correction, asymmetric null calibration, and false-green release gates invalidate specific shipped positive interpretations, while formal partial-identification and scientific-software challenge contracts define falsifiable repairs. This is a negative-audit and methods thesis, not an anisotropy detection, a corrected CF4 measurement, a validated cosmological likelihood, a native-transfer result, or Bianchi family/geometry identification.

## Audit census and delta discipline

The prior audit contributes 55 `KNOWN_OPEN` findings (P0 2 / P1 14 / P2 17 / P3 22) and 14 audit-completeness gaps. PR-117 contributes 33 distinct open atomic deltas (P1 22 / P2 11); it does not relabel prior findings as new. The prose/raw-ledger P1 inconsistency in the prior audit is preserved as an audited inconsistency rather than silently corrected.

The advocate matrix covers 102 criticisms exactly once. Dispositions are `{"abandoned": 3, "downclaimed": 43, "rebuild_required": 56}`. A disposition is a research response, not evidence that a production claim has passed.
The immutable-field root join converted three mapper-proposed rescues to `downclaimed` because their authoritative source state remains `KNOWN_OPEN`; no criticism is rescued in the final root matrix.

### Examination coverage ceiling

The generated-result coverage register contains 78 rows: 44 / 78 are `not_examined` and 34 / 78 are `sampled`. `not_examined` is not clearance; `sampled` is also not blanket clearance of the row, its consumers, or its scientific claim. Complete criticism accounting therefore does not imply complete scientific examination.

## As-shipped assessment

**Root decision: REJECT.** The shipped positive-science object cannot support anisotropy detection, global tilt, FLRW violation, precision growth tension, Bayesian evidence/PPC/LOOCV adequacy, native low-L morphology, geometry, or Bianchi-family conclusions. Two imported P0 findings remain open, the new audit adds 22 P1 and 11 P2 deltas, and decisive data inputs remain missing in several lanes. Passing governance/package checks demonstrably coexists with stale or scientifically invalid artifacts.

The audit-only recalculations are sensitivity and failure-localization evidence. They do not become corrected truth: CF4 changes from about 405 to 94 km/s under a monopole-orthogonal construction; raw/depth f-sigma8 behavior shifts materially; the Hermitian GRF defect reproduces; the DESI proxy null becomes unexceptional but exact-selection mocks remain absent; ACT is scientifically blocked; K6 is stencil-dominated; and JWST gains are small and provenance/covariance-limited.

Failure of the present anisotropy claims is not proof of exact isotropy and is not a new validation of LambdaCDM. Weak anisotropy remains a falsifiable but currently unsupported research program; the present result is non-identification rather than confirmation of either pole.

## Minimum-surgery assessment

**Root decision: NEW SUBMISSION AFTER MAJOR REBUILD, not a revision that retains the positive headline.** Remove the detection/tension/family narrative and reframe the work as a claim-tiered pre-solver methods and negative-audit paper. Its evidence-bearing contributions may be: exchangeable null construction, partial/non-identification theorems, independent numerical-oracle attacks, transfer/provenance contracts, and explicit demonstrations of when CF4/CMB/DESI/ACT/JWST examples remain blocked.

## Four-axis hostile and advocate synthesis

- **Theory:** one-way FLRW/almost-EGS statements and coefficient/domain claims must be rebuilt with frame, congruence, matter, regularity, order and remainder assumptions. Scalar or low-rank observables remain non-identifying; this negative theorem direction is the recoverable content.
- **Statistics:** fitted likelihood differences are not Bayes factors, plug-in residuals are not PPC, and channel ablations are not LOOCV. Exchangeable global scans, finite-null rank guarantees, calibrated abstention and honest identified sets are viable rebuilds.
- **Code:** clean-install failure, correlated self-oracles and false-green gates preclude reproducibility claims. Independent algorithms, mutation tests, content-addressed evidence and future adapter rejection fixtures can validate mechanics only.
- **Data analysis:** CF4, Planck/ACT, DESI and JWST lanes require row/input provenance, matched support/masks/nulls, selection and calibration covariance, and estimator-identical mocks. Current anomaly amplitudes are not retained.

## Advocate ranking and bounded final CRAG

Thirty-two no-web candidates (eight per axis) were scored by three non-author judges. The frozen shortlist has 12 candidates. Only those candidates entered the final CRAG; its authoritative packet contains 12 queries and 22 primary/official sources, while fuller raw agent lookups remain hash-bound. Final CRAG novelty checks reduced rather than inflated several novelty assessments.
The shortlist is now canonically replayable from the raw no-web author/judge packets and bound by `shortlist_freeze.json`. That freeze file was retrospectively materialized after the single CRAG lookup, so it proves assignment consistency but not independent filesystem ordering; this process limitation is retained rather than backdated.

The shortlist was frozen on the pre-CRAG selection scores. The totals below are recomputed after the bounded CRAG by replacing each track's novelty component with `novelty_after`; they are not compared against non-shortlisted candidates whose novelty was not rechecked.

| Candidate | Axis | Post-CRAG pre-solver | Post-CRAG post-native | Integrity eligible now | Final disposition | Novelty after CRAG |
|---|---|---:|---:|---|---|---:|
| CO-01 - Claim-addressed executable evidence graph | code | 78.0 | 74.75 | True | rebuild_required | 4.0 |
| CO-04 - Independent numerical-oracle and mutation laboratory | code | 81.15 | 77.25 | True | rebuild_required | 5.5 |
| CO-06 - Future-native adapter conformance corpus | code | 77.45 | 79.75 | True | native_solver_dependent | 4.5 |
| CO-07 - Blinded morphology-equivalence challenge harness | code | 54.75 | 81.0 | False | native_solver_dependent | 6.0 |
| DA-01 - CF4 constrained-flow injection and depth-tomography study | data_analysis | 78.95 | 58.5 | False | rebuild_required | 4.5 |
| DA-05 - DESI exact-selection dipole null experiment | data_analysis | 74.75 | 61.0 | False | rebuild_required | 3.5 |
| ST-03 - Exchangeable global scan calibration with finite-null guarantees | statistics | 81.5 | 77.0 | True | rebuild_required | 3.5 |
| ST-04 - Raw-CF4 nuisance-augmented identified set with honest non-identification | statistics | 79.1 | 62.25 | False | rebuild_required | 6.0 |
| ST-08 - Post-native morphology equivalence classes with partial family identification | statistics | 47.75 | 80.5 | False | native_solver_dependent | 6.0 |
| TH-01 - Convention-complete one-way FLRW and almost-EGS theorem reconstruction | theory | 80.05 | 63.0 | True | rebuild_required | 4.5 |
| TH-02 - Cancellation-preserving graded and PSD-cone non-identification theorem | theory | 81.65 | 75.5 | True | rebuild_required | 6.5 |
| TH-04 - Source-response equivalence graph as the native-atlas handoff interface | theory | 68.9 | 79.0 | False | native_solver_dependent | 6.0 |

## Pre-solver research to execute now

1. `ST-03`: rebuild the global scan so observation and nulls traverse an identical, frozen pipeline with finite-null uncertainty and tie handling.
2. `TH-02` and `TH-01`: prove non-identification and one-way theorem results with explicit assumptions, independent derivations and mutation/regeneration checks.
3. `CO-04` and `CO-01`: create independent numerical oracles and a claim-addressed evidence graph, while treating both as mechanics/provenance validation rather than scientific truth.
4. `DA-01` and `ST-04`: rebuild CF4 as a preregistered injection/coverage and identified-region analysis only after row/group/selection lineage is authenticated.
5. `DA-05`: use a two-tier DESI validation (large fast-mock covariance plus smaller high-realism selection mocks), with per-mock estimator refits and a receipted runner.

## Research deferred until the native solver/atlas arrives

`TH-04`, `ST-08`, `CO-06`, and `CO-07` remain interface/challenge-set work. Scientific use requires an authenticated native low-ell solver and morphology atlas, versioned coefficient conventions, held-out injections, matched masks/nulls/covariance, nuisance-rank checks, and explicit family-equivalence annotations. Even after those gates, the first permissible conclusion is morphology compatibility; family identification requires a separate external review.

## Strongest defensible thesis

The strongest defensible paper thesis is: *a fail-closed, claim-tiered pre-solver methodology can diagnose non-identification, estimator non-exchangeability, correlated numerical oracles, and transfer/provenance failure in low-ell anisotropy searches; the present CF4/CMB/DESI/ACT/JWST examples demonstrate blockers and identified research designs, not evidence for cosmic anisotropy or a Bianchi family.*

## Unexecuted blockers

- The two imported P0 scientific defects are not repaired in production outputs or manuscript numbers.
- ACT raw/upstream QE inputs and validated low-L reconstruction transfer are absent.
- Exact matched Planck end-to-end nulls and exact-selection DESI mock execution are not complete here.
- JWST authoritative row manifest, per-host errors, probabilistic crossmatch and shared calibration covariance are incomplete.
- Native solver/atlas, family-equivalence registry and external validation do not exist in this repository.
- Manuscript figure provenance/freshness failures remain scientific-publication blockers even if LaTeX compiles.

## Dissent and uncertainty

- **JCAP:** The audit's agents share repository state, orchestration, and model lineage; agreement is correlated review evidence, not an independent empirical replication. The audit-only diagnostics are strong invalidation and mechanism evidence but use simplified injections or incomplete covariance in important lanes, so their numerical replacements must remain diagnostic-only. The fixed CRAG substantially reduces novelty for permutation calibration, provenance graphs, manufactured-solution testing, schema conformance, Bianchi injection recovery, sector decomposition, and CF4 estimator studies; JCAP relevance therefore depends on an executed cross-lane scientific lesson rather than a collection of standard repairs. A corrected analysis may preserve some non-anomalous qualitative conclusions, but nothing reviewed supports a positive anisotropy, global-tilt, Bianchi-family, geometry, or native-transfer result. The 6.5 post-surgery score evaluates a distinct proposed methods/negative-audit paper, not a repaired version already demonstrated by the present positive-science manuscript; external domain-owner reruns could still lower that assessment.
- **PRD:** The audit provides unusually strong negative evidence because several failures are executable and directionally concordant, but the agents share repository evidence and are not an independent scientific replication. A focused paper centered on TH-02 non-identification, with TH-01 theorem hygiene and ST-03/DA-01 as bounded counterexamples, could become publishable after the stated derivations and coverage experiments; the broad software-governance and multi-survey package is less naturally a PRD contribution. The post-surgery score therefore evaluates potential after new work, not readiness of the current manuscript, and would fall if the revision retained any positive anisotropy headline or treated interface conformance as physics validation.
- **Independent skeptical:** The audit package is materially stronger than the manuscript it audits: sealed command receipts distinguish process_result from scientific_status, preserve input hashes, and openly block ACT and JWST promotion. That supports a methods appendix but does not validate the scientific estimands. The 102-row criticism matrix is complete as bookkeeping, but only three rows are marked rescued and neither P0 is among them. Two rescued gaps concern audit accounting/referee independence, not cosmological evidence. Six of the twelve shortlisted candidates are ineligible for retain under the ledger's own integrity veto because decisive provenance is absent. Their scores are prioritization heuristics, not evidence of readiness; their final rebuild_required or native_solver_dependent dispositions are the operative states. The DESI null and K6 convergence reruns are useful negative diagnostics, but exact survey support is missing for DESI and the K6 result is a stencil-dependent upper bound, not physical vorticity. A JCAP-relevant negative-audit paper may be possible, but the required surgery is structural rather than minimal. If the paper retains the existing multi-claim cosmology narrative, its strongest reproducible contribution will be obscured and the rejection recommendation remains unchanged.

Agreement among agents is correlated because they share repository evidence; it is not an independent replication. The digest-blind PR-117 referee samples and the separately authored PR-118 decisions reduce, but do not remove, this dependence.

## Proposed next DAG candidates

- `AUD-R01A` (pre_solver, OBSSTAT): Quarantine refuted CF4 corrections and rebuild estimator mechanics. Targets: imported P0 C1-K5-MV-F1, imported P0 C3-K5-VCORR-ML-F1, N-DATA-CF4-DOWNSTREAM. Entry gate: authenticated CF4 row/group/selection lineage and preregistered injection coverage. Maximum claim: observable-estimator validation only.
- `AUD-R01B` (pre_solver, HTT): Construct CF4 identified sets and downstream pushforwards. Targets: N-DATA-CF4-DOWNSTREAM, N-DATA-FS8-DEPTH. Entry gate: OBSSTAT estimator coverage receipt plus explicit nuisance/partial-identification contract. Maximum claim: identified-region result; no global-tilt truth claim.
- `AUD-R02A` (pre_solver, OBSSTAT): Build exchangeable observed/null calibration. Targets: N-STAT-K1-EXCHANGE, N-STAT-DEGENERATE-NULL. Entry gate: identical observed/null feature pipeline and finite-null calibration plan. Maximum claim: matched-null calibration.
- `AUD-R02B` (pre_solver, COMMON): Run independent mutation-oracle and false-green release campaign. Targets: N-CODE-FALSE-GREEN. Entry gate: predeclared oracle-killing mutations and independent implementation receipts. Maximum claim: release-mechanics validation only.
- `AUD-R03` (pre_solver, COMMON): Rebuild one-way FLRW/almost-EGS and coefficient-domain theorem surfaces. Targets: N-THEORY-FLRW-CONVERSE, N-THEORY-EGS-CONVERSE, N-THEORY-NT2-COEFFICIENT, N-THEORY-OMK-DOMAIN. Entry gate: two independent derivations with explicit frame/domain/remainder assumptions. Maximum claim: conditional mathematical result.
- `AUD-R04` (pre_solver, OBSSTAT): Acquire and rerun exact-support DESI/ACT/JWST validation inputs. Targets: N-DATA-DESI-READINESS, N-DATA-ACT-RANGE, N-DATA-JWST-ACQUISITION, N-DATA-JWST-COVARIANCE. Entry gate: input manifests, exact selection/mask transfer, covariance and matched-null provenance. Maximum claim: survey-conditional null or forecast result.
- `AUD-R05A` (post_native_solver, BASS_PY): Run authenticated native-adapter and atlas transport conformance. Targets: TH-04, CO-06. Entry gate: authenticated native solver/atlas with versioned conventions and rejection fixtures. Maximum claim: native transport/atlas conformance only.
- `AUD-R05B` (post_native_solver, OBSSTAT): Build matched-mask morphology challenge features and equivalence annotations. Targets: TH-04, ST-08, CO-07. Entry gate: authenticated atlas plus matched masks, nulls, covariance and held-out injections. Maximum claim: morphology compatibility feature validation.
- `AUD-R05C` (post_native_solver, HTT): Run blinded equivalence-set inference and abstention challenge. Targets: ST-08, CO-07. Entry gate: BASS transport and OBSSTAT matched-feature receipts plus nuisance-rank and equivalence contracts. Maximum claim: morphology compatibility before any separate family-identification review.

These cards are proposals only and were not inserted into the active completed DAG. Production corrections, manuscript number replacement, public upload and native solver implementation remain out of scope.
