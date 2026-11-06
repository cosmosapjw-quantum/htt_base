# GitHub PR, legacy and source audit — R38 intake

## Audit scope and reproducibility

Repository: cosmosapjw-quantum/htt_base. The default branch is main. The latest convergence/science integration branch inspected for this task is research/htt-adaptive-methods-20261023 at merged PR #564 commit cab89d25af52a1b978a4da8c11eecdc25bb22759. The new R38 branch is rooted at that commit. Main was not changed.

GitHub REST pull-request inventory: 561 records across six pages (100+100+100+100+100+61). A title/key-term screen returned 71 potentially relevant entries. This is a full PR inventory and relevance screen, not a line-by-line review of all 561 diffs. Detailed scientific claim review focused on the central branches and their source/acceptance boundaries; other relevant open candidates are listed below for local uptake.

## Central scientific ancestry

### PR #364 / PR-256 — local/global velocity frame decomposition
Merged into the multicomponent research line. It introduces beta_RO, beta_RM and beta_MO, first-order composition beta_RO=beta_RM+beta_MO+O(beta^2), a shared covariance and nuisance-projected response-space comparison. Its SEPARABLE_CANDIDATE is a registered tangent-space diagnostic in analytic/synthetic observable units with transfer source none. The PR explicitly rejects source detection, global-tilt detection, FLRW departure, native-solver validation and Bianchi-family identification. Reuse frame labels and response geometry; do not reuse its synthetic separability result as observational evidence.

### PR #365 / PR-257 — low-ell morphology
Merged diagnostic-only matched counterpairs, O(3) parity typing, harmonic provenance, BipoSH features, supported-rank and abstention tests. The preregistered benchmark is synthetic-only. It does not establish an observed anomaly, physical source or Bianchi family. Missing directional-wavelet/T-E-B cross-morphology providers remain missing, not zero.

### PR #378 / PR-281 — orbit and anisotropy-type acceptance
Merged fail-closed dimension-aware orbit-type logic and response-direction projection. Claim ceiling remained diagnostic-only, transfer_source=none, completeness unproven and family identification blocked pre-native-atlas. Do not infer a Bianchi family from local STF orbit class.

### PR #394 / PR-306 — Planck PR3 low-ell operator
Merged beam/pixel commonization, mask, multipole-vector, same-sky covariance and FFP10 identity closure. The recorded science disposition explicitly says observed statistic not seen, observed science not executed and scientific effect synthetic/null-only operator validation. It is an implementation predecessor, not an empirical low-ell result.

### PR #396 / PR-313 — CF4 status provenance
Merged a provenance/status closeout after PR-312's exhausted candidate. It records observed_statistic_seen=false and observed_science_executed=false. Preserve this failed/closed history; do not treat a completed provenance record as a completed CF4 physical result.

### PR #399 / PR-310 — HSC/KiDS spin-2 operator
Merged typed HSC S19A/KiDS-1000 operators and covariance-rank contracts. The claim ceiling says no observed statistic, no admitted/authorized/executed lane, and synthetic spin-2 operator diagnostic only. Use the covariance and E/B conventions, but await actual normalized products and full cross-covariance.

### PR #401 and #402 / PR-311 — DESI DR1 selection and successor operator
Merged official DR1 selection semantics (BGS BRIGHT r<19.5; BGS_BRIGHT-21.5 M_r<-21.5; 0.1<z<0.4) and an observer-side response/selection operator. The operator closure used 1,000 EZmocks and 25 held-out Abacus realizations; data disposition was blocked without canonical admission; observed_statistic_seen=false and observed_science_executed=false. This is not a measured directional cosmology result and is DR1-specific. R38 should use current DR2 data contracts only after official row/selection reconciliation.

### PR #403 / PR-314 — Planck SMICA attended candidate
Still open/external-audit candidate. It reports a diagnostic using one SMICA observed map and 300 paired FFP10 CMB+noise rows: feature-family rank 19/43, covariance rank 12/12 and replay match. Its own claim boundary forbids Commander robustness, joint Planck response, local/global attribution, source attribution and Bianchi identification. No fresh raw download was made in that PR. Treat it as a conditional single-map diagnostic, not a general detection.

### PR #548–#557 — October 2026 idle-data and source-locked drafts
Open drafts include shared-selection/sky-null/observer-rank and Bianchi-I theory precursors (#548); CF4 CDS 404 recovery (#549); original-source audit with a 35,970 selected group operator and PR3 mask gates (#550); CF4 angular calibration Fisher gauge and finite Planck-source scan (#551); Planck T inverse and CF4 signed intervals (#552); real T-mask spin-2 pilot and CF4 transfer bounds (#553); Planck mask/polarization response and source lock (#554–#557). They are not all merged into R37.

PR #550 says the 55,877-row CF4 Table 2 and 38,053-row Tables 3/4 were available in a prior local run, but raw bytes were not mounted in that execution context; a separate 35,970-row NPZ was used for selected sample-geometry analysis. It explicitly states that sample geometry is not physical anisotropy and inverse-selection bounds are conventions, not measured completeness. Actual PR3 mask-pixel analysis was NOT_RUN in that context.

PR #557 records a finite two-mask operator difference based on user-local NPZ inputs but leaves physical ell>8 tail, beam/noise/foreground/FFP matched null and independent operator-error bounds absent. It is a geometry-only conditional bound, not an observed B-mode or global anisotropy claim.

### PR #563 / observable bridge reconciliation
Merged to the current research branch in October 2026. It integrated R32/R36 results, conditional radiation/optical/Bianchi/directional-Hubble contracts and source-bound handoff while preserving original external acceptance 17/42 (18/42 only under the recorded analytic V03 alternate). It did not execute a new local campaign, run a native solver/ODE, or qualify all observational consumers. Its selected CI/test receipts validate code/contract layers, not an observational posterior.

### PR #564 / R37 convergence delivery
Merged at cab89d25af52a1b978a4da8c11eecdc25bb22759. It adds a source-bound baseline report, six bounded delivery tasks and an updated 6-node R37 finite report-first DAG while preserving the original 42 nodes and six paper contracts. Its body states all six execution cards remain pending after the integration card; no raw catalogue acquisition, MC100 qualification, native solver/ODE or journal submission occurred. It records a broader test attempt with errors and does not claim a whole-suite pass. R38 must not mark R37 science cards complete because documentation merged.

## User-pinned theorem source

Pinned source: docs/research_program/observational_publication_20261015/METHOD_REBOOT_20261023/THEOREMS.md at commit dfaf171c37f2636c942a99bf2b9803b57295ac14; matching README_KO.md was also fetched. The theorem file distinguishes:
- five-variable tensor-functional inference state from independent measurements;
- conditional radiation and optical response claims from data detections;
- source-measure exceedance law Pi from a frequentist p-value;
- full-sky STF optical reconstruction from masked-sky response;
- covariance-preserving confidence objects from scalar score reduction;
- prior-induced rank from data identification.

It includes a positive radiation-stress/acceleration response, local optical shear inversion with a full-sky factor, orbit-distance and fibre-identification theorems, Berger–Boos nuisance treatment, and a Gaia-summary low-power result for a narrow working Gaussian experiment. These are important mathematical/method foundations, but none alone is a multi-probe observed detection or journal-novel claim.

## Library documents reinterpreted

Supplied Library files located and read:
- HTT_FIVE_THEORY_LOOPS.pdf (2026-10-26): five independent theory loops A–E (radiation/shear, intrinsic CMB dipole, beyond-FLRW kinematics, Bianchi geometry, directional Hubble); it explicitly presents conditional derivations and does not claim new fits to actual CMB/CF4/quasar catalogues.
- HTT_physical_research_en.pdf (2026-10-25): processed Planck carrier, selected CF4 and optical/Gaia results with covariance/selection conditions. The 60 processed Planck carriers are processing alternatives on one CMB sky, not 60 independent skies.
- HTT_METHOD_FOUNDATIONS_20261028.pdf: (x,Q,F,Pi,G_F) semantics, kinematic target and observer-frame distinction, exact geometric null versus stochastic perturbed-FLRW null.
- HTT_FOUR_GOALS_FIBRE_20261028.pdf: 23D/20D radiation carrier, optical/astrometric rank, Bianchi finite-family and directional-Hubble bridges.
- HTT_NOVELTY_STRATEGY_V15.pdf: prior-art warnings for boost/mode coupling, temperature calibration and entropy/spectral effects; strongest candidate lies in quantitative response/observable identifiability rather than relabelling established operations.
These are project-internal evidence, not independent peer review.

## Project catalogue and source identity

docs/project_catalog/database/manifest.json describes a 10.82GB uncompressed SQLite file split into 57 compressed chunks. It indexes project/external asset roots; it is not the raw survey payload. docs/project_catalog/sources.json contains historical checkout, worktree and external storage paths and records scientific_execution as NOT_EXECUTED for that inventory. It cannot certify that a particular file is currently mounted.

Relevant historic branch families include low-ell PR-257/PR-251, local/global velocity PR-256, Planck PR3/SMICA and FFP work, CF4 raw/group/calibration, DESI DR1 selection and covariance, HSC/KiDS spin-2, and Gaia/optical E1/B1 versus E2/STF5 products. Use exact saved result identities from their consumer contracts; never rerun a one-use producer merely to regenerate a receipt.

## Audit limitation and interpretation

The 561 PR records were enumerated and 71 title-screened. The PRs above received detailed body/status/claim-boundary inspection; nearby open drafts were indexed for local follow-up. This is not a literal full patch-line audit of every historic PR or every file in the 36k+ tree. The current result establishes the principal scientific lineage and claim ceilings; the local agent must inspect any exact source file it modifies and preserve the relevant PR receipt.