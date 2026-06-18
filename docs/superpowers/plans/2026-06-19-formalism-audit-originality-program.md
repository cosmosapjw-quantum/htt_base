# Formalism Audit and Originality Program Implementation Plan

owner: COMMON
implementation_scope: revision_plan
claim_tier: diagnostic_only
transfer_source: mixed_none_external_and_conditioned_legacy
sky_support_status: not_directional
null_mock_status: mixed_diagnostic_unmatched_and_not_applicable
config_hash: none_manual_2026_06_19_formalism_audit_originality_plan
input_hashes:
- `formalism_originality_program.zip`: `57c00c1f3868fe0e62270b9625d5e97386c57925363a9bfb21137d9d8348bbc9`
- `statistical_formalism_audit_report.zip`: `bdfb44061817bf01ca543356daaf3110cff70878edd14d3d4c5cc27cc4f34377`
- `AUDIT_REPORT (1).md`: `6da68d227f733049ac8664893534867db0dac0e6c9002f55b0650b84eb4e026c`
caveats:
- This is an execution plan, not a scientific validation artifact.
- All local/global, depth-gap, and matched-null items remain diagnostic or forecast-only until gates close.
- No native low-ell solver output, Bianchi geometry detection, or family identification is claimed.
generating_command: manual planning from incoming audit/proposal zips with web CRAG spot-check
git_commit_or_worktree_state: `40f789da0e8b70472d6384d1f7a7b12019b50329` with REV-R063 archive inputs before commit

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development`
> or `superpowers:executing-plans` to implement this plan task by task. Use repo-local
> HTT skills for claim firewall, physics/math audit, observable statistics, statistical
> hardening, plot provenance, manuscript figure audit, and LaTeX build work.

## Goal

Absorb the two incoming external packages:

- `statistical_formalism_audit_report.zip`
- `formalism_originality_program.zip`

into a staged post-DAG revision program. The revision must fix every manuscript-facing
semantic defect found by the audit, then extend the research as a methods/framework
contribution without claiming detection, evidence, native transfer validation, Bianchi
geometry, or family identification.

The revised research stance is:

> A claim-tiered, contract-enforced diagnostic algebra for FLRW departure, with signed
> comparator projections, fail-closed certification, registered exceedance semantics,
> depth-ratio confound separation, and machine-checkable claim firewalls.

## Evidence Read

Incoming files found at repo root:

- `formalism_originality_program.zip`
  - SHA256: `57c00c1f3868fe0e62270b9625d5e97386c57925363a9bfb21137d9d8348bbc9`
  - Contents: strategic overview, novelty ledger F1-F9, reframe/reorg plan,
    upgrade plan U1-U5, experiment program E1-E7, defense dossier, prior-art positioning,
    dependency-free reference code, experiment tracker.
- `statistical_formalism_audit_report.zip`
  - SHA256: `bdfb44061817bf01ca543356daaf3110cff70878edd14d3d4c5cc27cc4f34377`
  - Contents: `AUDIT_REPORT.md`, `verify_formalism_claims.py`.
- Root `AUDIT_REPORT (1).md`
  - SHA256 matches the zipped `AUDIT_REPORT.md`: `6da68d227f733049ac8664893534867db0dac0e6c9002f55b0650b84eb4e026c`.

Commands already run for intake:

```bash
unzip -l formalism_originality_program.zip
unzip -l statistical_formalism_audit_report.zip
python3 /tmp/htt_audit.oxpyDe/formalism/code/run_all.py
python3 /tmp/htt_audit.oxpyDe/audit/verify_formalism_claims.py docs/generated/current_science_plot_payload.json
```

Observed verification:

- Proposal reference experiments: `run_all complete: 6/6 ok`.
- Audit verifier against live `docs/generated/current_science_plot_payload.json`:
  - cancellation trap reproduced: `YES`.
  - semantic-split mismatch found: `YES`.
  - `Pi`, `F`, and `G_F` are currently misbound in `semantic_and_vectors.semantic_split`;
    `F` and `G_F` are also owner-swapped to `HTT` in that payload.

Web CRAG spot-check for prior-art framing:

- DES Y3 blinding papers page states the blinding transformation hides cosmology results
  until analysis decisions are finalized.
- DES Y6 papers page and arXiv summary confirm DES Y6 weak-lensing/galaxy-clustering
  methodology/results are current 2026 material and use rigorous blinding protocol.
- Steegen et al. 2016 is the canonical multiverse-analysis reference.
- Gelman and Loken 2013 is the canonical garden-of-forking-paths reference.

When implementing publication-facing prior-art language, rerun this CRAG step and cite
primary or official sources directly in the manuscript/bibliography.

## Non-Negotiable Scope

- No native low-ell solver implementation, simulation, or fake output.
- No external transfer may be called native or validated-as-native.
- No Bianchi geometry detection or family identification.
- No MIO posterior, MIO evidence, MIO Bayes factor, or truth certificate.
- `x_C`, `Q`, `Pi`, `F`, `G_F`, cancellation, direction coherence, and low-ell scalar
  features remain diagnostic-only unless an explicit HTT inference path with matched
  nulls, covariance, PPC, LOOCV, and prior-sensitivity gates is actually closed.
- The `G_F` matched-null boost-vs-tilt item is a forecast/diagnostic hardening path,
  not a current global-tilt claim.

## Role Divergence For Each PR

For every task below, run the repo-mandated role loop:

- Code cartographer: map existing production modules, generated surfaces, and tests;
  steelman reuse of current contracts before proposing new objects.
- Harness engineer: require deterministic generation, check mode, focused tests, and
  manifest validation; attack any manual-only artifact.
- Physics/statistics auditor: verify signs, comparator dependence, cancellation, null
  calibration, denominator policies, and claim tiers; attack any scalar-to-geometry leap.
- Claim-gate reviewer: scan wording, captions, manifests, owner/tier labels, MIO/HTT
  separation, and legacy promotion; attack any detection/evidence/native/family language.
- Regression tester: run focused tests, smoke/collect where relevant, figure/manuscript
  audit, and package checks; attack hidden dirty/generated state.

## Post-DAG Revision Slice

The main DAG is complete through `PR-115`. Implement this as a post-DAG revision slice
using the next `REV-R###` identifiers after `REV-R062`.

### REV-R063: Archive Incoming Audit/Proposal and Create Response Matrix

Files:

- Create `docs/audits/formalism_audit_2026-06-19/`
- Create `docs/generated/formalism_audit_originality_response_matrix.md`
- Update `docs/generated/statistical_formalism_reaudit_readiness.md`

Steps:

- [ ] Copy both incoming zip files, extracted markdown, and verifier scripts into the audit folder.
- [ ] Record SHA256 hashes, source filenames, extraction time, and current git state.
- [ ] Create a finding-to-action matrix covering:
  - fatal/high: semantic-split misdefinitions.
  - fatal/high: detection prose around direction-marginalized Bayes factors.
  - medium: 98 percent accuracy wording.
  - medium: `F` naming and `*_posterior` legacy filename exposure.
  - medium: `x_C`/`F` cancellation caveat missing from displays.
  - medium: legacy VER2 atlas/production labels.
  - low: comparator labels on every `x_C`/`Q`.
  - low: `G_F` floor reporting.
  - U1-U5 and E1-E7 proposal items.
- [ ] Re-run the external verifier from the archived path.
- [ ] Mark unresolved findings as blockers in the response matrix, not as fixed.

Validation:

```bash
python3 docs/audits/formalism_audit_2026-06-19/verify_formalism_claims.py docs/generated/current_science_plot_payload.json
venv/bin/python scripts/check_claim_language.py --dry-run --include-archives docs/generated/formalism_audit_originality_response_matrix.md
```

Commit:

```bash
git commit -m "REV-R063: archive formalism audit program"
```

### REV-R064: Fix Semantic-Split Figure Semantics and Add Symbol Registry Linter

Files:

- Modify generator that writes `docs/generated/current_science_plot_payload.json`.
- Add `scripts/verify_formalism_figure_labels.py`.
- Add `tests/contracts/test_formalism_figure_labels.py`.
- Regenerate affected figure payloads and manifests.

Steps:

- [ ] Locate the current semantic-split generator.
- [ ] Choose one of two safe fixes:
  - Preferred: repopulate `Pi`, `F`, `G_F` from canonical production formalism objects.
  - Conservative fallback: relabel the current bars as non-canonical quantities:
    `Q denominator-policy spread`, `local-null survival (1-FPR), HTT`,
    `null-bank depth envelope`.
- [ ] Add a canonical symbol registry for `x`, `Q`, `Pi`, `F`, `G_F` with owner,
  allowed definition keywords, and forbidden owner swaps.
- [ ] Fail if a figure/table uses a canonical symbol with a mismatched owner or definition.
- [ ] Re-run the audit verifier and require zero semantic-split mismatches.

Validation:

```bash
venv/bin/python scripts/verify_formalism_figure_labels.py docs/generated/current_science_plot_payload.json
python3 docs/audits/formalism_audit_2026-06-19/verify_formalism_claims.py docs/generated/current_science_plot_payload.json
venv/bin/python -m pytest tests/contracts/test_formalism_figure_labels.py -q
```

Commit:

```bash
git commit -m "REV-R064: enforce formalism figure semantics"
```

### REV-R065: Promote Detection-Language Claim Lint to Fail and Patch Manuscript Prose

Files:

- Modify `scripts/pdf_claim_lint.py`.
- Modify relevant manuscript chapters, at minimum:
  - `docs/manuscript/ch05_teff_corrections.tex`
  - `docs/manuscript/ch08_robustness.tex`
  - `docs/manuscript/ch09_discussion.tex`
- Regenerate `docs/generated/pdf_claim_lint_report.md`.

Steps:

- [ ] Promote `lnB` numeric plus high-strength language from `warn` to `fail`.
- [ ] Replace the audited phrases exactly:
  - "tilt detection" -> conditional, direction-marginalized diagnostic preference.
  - "spurious tilt detections" -> spurious tilt-preference signals under structured nulls.
  - "departure parameter detection" -> departure-parameter diagnostic.
  - "98% accuracy" -> transfer-conditional contribution fraction.
- [ ] Keep legitimate external-literature detections only when clearly attributed to external papers.
- [ ] Rebuild PDF and re-run the PDF claim lint.

Validation:

```bash
venv/bin/python scripts/pdf_claim_lint.py --check
latexmk -pdf -interaction=nonstopmode -halt-on-error docs/manuscript/main.tex
venv/bin/python scripts/pdf_claim_lint.py
```

Commit:

```bash
git commit -m "REV-R065: fail detection-language overclaims"
```

### REV-R066: Promote Sector-Resolved Departure Profile and Magnitude Companion

Files:

- Modify `htt/mio/formalism/component_breakdown.py`.
- Modify `htt/mio/formalism/departure_bundle.py`.
- Modify `htt/mio/formalism/filling_fraction.py`.
- Add or extend tests under `tests/mio/`.
- Update generated current-science payloads and figure captions.

Steps:

- [ ] Make the sector-resolved signed component vector, `absolute_component_total`,
  and `cancellation_index` required display metadata for every `x_C` and `F` summary.
- [ ] Add a total-anisotropy magnitude companion `M` or equivalent documented sector norm.
- [ ] Ensure `F` remains the signed projection over admissible MES-linear ceiling, no clipping,
  and not physical volume occupancy.
- [ ] Add a worked counterexample artifact showing `x_C ~= 0` with large signed sectors.
- [ ] Update captions so `x_C ~= 0` and `F ~= 0` cannot be read as isotropy.

Validation:

```bash
venv/bin/python -m pytest tests/mio/test_departure_bundle.py tests/mio/test_filling_fraction.py -q
venv/bin/python scripts/audit_manuscript_figures.py --dry-run
```

Commit:

```bash
git commit -m "REV-R066: report cancellation-aware departure profiles"
```

### REV-R067: Integrate Firewall Fuzzer and MIO/HTT Leakage Audit

Files:

- Add productionized version of `semantic_firewall_fuzz.py` under `scripts/` or `tests/contracts/`.
- Extend relevant common/MIO/HTT tests for reserved-language, owner/tier, and leakage attacks.
- Add generated firewall coverage report.

Steps:

- [ ] Port the proposal fuzzer to the production contracts rather than the dependency-free
  reference module.
- [ ] Cover attacks:
  - reserved language smuggling.
  - figure label owner/definition mismatch.
  - sign-dirty or super-ceiling `F`.
  - non-admissible external/observational ceiling certification.
  - post-hoc `Pi` threshold selection.
  - `G_F` "global tilt" language.
  - MIO diagnostic to HTT evidence/posterior leakage.
- [ ] Require zero successful smuggles and zero leakage paths.

Validation:

```bash
venv/bin/python -m pytest tests/contracts/test_semantic_firewall_fuzz.py tests/htt/test_posterior_pushforward.py tests/mio -q
```

Commit:

```bash
git commit -m "REV-R067: fuzz formalism claim firewalls"
```

### REV-R068: Comparator-Multiverse and Pi Measure-Kind Reporting

Files:

- Modify `htt/mio/formalism/normalized_score.py`.
- Modify `htt/mio/formalism/exceedance.py`.
- Update plot/list generators and manuscript captions.
- Add tests under `tests/mio/` and `tests/contracts/`.

Steps:

- [ ] Require comparator labels on every `x_C`/`Q` figure/table row.
- [ ] Generate comparator-multiverse summaries for admissible comparators.
- [ ] Display across-comparator spread as an explicit specification-curve sensitivity.
- [ ] Require `Pi.measure_kind`, threshold policy, registration hash status, and
  look-elsewhere trials whenever `Pi` is shown.
- [ ] Block any caption implying `Pi` is a p-value unless matched null/covariance status
  explicitly supports that interpretation.

Validation:

```bash
venv/bin/python -m pytest tests/mio/test_normalized_score.py tests/mio/test_exceedance.py -q
venv/bin/python scripts/verify_formalism_figure_labels.py docs/generated/current_science_plot_payload.json
```

Commit:

```bash
git commit -m "REV-R068: expose comparator and exceedance policies"
```

### REV-R069: G_F Floor, Denominator Split, and Matched-Null Forecast Path

Files:

- Modify `htt/mio/formalism/isotropy_gap.py`.
- Modify or add local/global diagnostic generators.
- Add tests under `tests/mio/`, `tests/htt/`, and `tests/contracts/`.
- Generate a forecast-only `G_F` matched-null report.

Steps:

- [ ] Surface `floor_applied_by_bin` wherever `G_F` is shown.
- [ ] Surface numerator-vs-denominator-evolution split wherever `G_F` is shown.
- [ ] Preserve current finding: existing null banks do not license local/global separation.
- [ ] Add a matched-null forecast experiment based on production mocks or clearly marked
  synthetic demonstration; do not promote it to observed-data evidence.
- [ ] If matched nulls do not drive FPR below threshold, report "blocked" rather than
  tuning until pass.
- [ ] If matched nulls pass in a forecast, label as forecast and keep global-tilt wording blocked.

Validation:

```bash
venv/bin/python -m pytest tests/mio/test_isotropy_gap.py tests/htt/test_matched_nulls.py -q
venv/bin/python scripts/check_publication_claim_freeze.py --check
```

Commit:

```bash
git commit -m "REV-R069: harden G_F null diagnostics"
```

### REV-R070: Normalize Legacy VER2 Readiness Labels

Files:

- Modify VER2 result-pack generator or postprocessor.
- Regenerate affected files under `docs/ver2_upgrade/generated/`.
- Update tests that currently expect legacy `production_candidate` or `atlas_ready` wording.

Steps:

- [ ] Over-stamp current-use legacy payload fields:
  - `atlas_available: true` -> `legacy_not_current` surface or explicit `false` plus caveat.
  - `atlas_ready` -> `legacy_not_current`.
  - `production_candidate` / `production-grade` -> no-current-production label for public packages.
- [ ] Preserve historical raw values only under an archived/prior-context namespace.
- [ ] Ensure audit packages and manuscript generators never surface stale promotion fields.

Validation:

```bash
venv/bin/python -m pytest tests/contracts/test_audit_package_generator.py tests/mio/test_ver2_manifest_status.py -q
rg -n "atlas_available.*true|atlas_ready|production-grade|production_candidate" docs/ver2_upgrade/generated docs/generated
```

Expected `rg`: only archived/prior-context lines with `legacy_not_current` caveats, or none.

Commit:

```bash
git commit -m "REV-R070: normalize legacy readiness labels"
```

### REV-R071: Reframe Manuscript as Methods/Framework Contribution

Files:

- Modify manuscript introduction/framework/results/discussion.
- Add or modify generated formalism-methods snippets.
- Update bibliography after CRAG verification.

Steps:

- [ ] Reframe headline from anomaly detection to diagnostic-algebra methodology.
- [ ] Add claim ladder:
  - exact signed comparator projection.
  - exact cancellation caveat.
  - MIO diagnostic-only owner/tier.
  - supported fail-closed `F`.
  - supported registered `Pi`.
  - supported denominator-split `G_F`.
  - forbidden detection/evidence/native/family claims.
  - forecast-only matched-null local/global discrimination.
- [ ] Add contribution paragraph covering F1-F9, with F1 semantic firewall as flagship.
- [ ] Add limitations section: no current detection, `G_F` FPR blocked under current nulls,
  transfer-conditional, no native solver, no family-ID.
- [ ] Re-verify and cite DES blinding, multiverse analysis, and garden-of-forking-paths
  prior art from primary/official sources.

Validation:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error docs/manuscript/main.tex
venv/bin/python scripts/pdf_claim_lint.py --check
venv/bin/python scripts/audit_manuscript_figures.py --dry-run
```

Commit:

```bash
git commit -m "REV-R071: reframe formalism as methods contribution"
```

### REV-R072: Regenerate Audit Package and External Re-Audit Prompt

Files:

- Modify `scripts/build_statistical_formalism_audit_package.py`.
- Update `docs/generated/statistical_formalism_audit_package.zip`.
- Update `docs/generated/statistical_formalism_audit_prompt.md`.
- Update package manifest and readiness report.

Steps:

- [ ] Include the response matrix, firewall fuzzer report, figure-label linter report,
  cancellation/magnitude artifacts, comparator-multiverse summaries, `Pi` policy summaries,
  `G_F` floor/split/null status, and revised manuscript source.
- [ ] Exclude PDFs unless explicitly requested.
- [ ] Keep code sampling minimal: include only production files needed to understand
  figures and formalism claims.
- [ ] Make the new prompt focus on:
  - whether the methods contribution is genuinely novel.
  - whether the semantic firewall is more than prose disclaimers.
  - whether cancellation and magnitude reporting prevent scalar overread.
  - whether `Pi`, `F`, and `G_F` are still overinterpreted.
  - whether any remaining `lnB` language leaks into detection.

Validation:

```bash
venv/bin/python scripts/build_statistical_formalism_audit_package.py --check
venv/bin/python -m pytest tests/contracts/test_statistical_formalism_audit_package.py -q
```

Commit:

```bash
git commit -m "REV-R072: rebuild formalism re-audit package"
```

## Full Validation Gate Before Re-Audit

Run:

```bash
venv/bin/python -m pytest tests/mio tests/htt/test_posterior_pushforward.py tests/contracts -q
venv/bin/python -m pytest -m smoke -q
venv/bin/python -m pytest --collect-only -q
venv/bin/python scripts/check_publication_claim_freeze.py --check
venv/bin/python scripts/audit_manuscript_figures.py --dry-run
venv/bin/python scripts/pdf_claim_lint.py --check
venv/bin/python scripts/build_statistical_formalism_audit_package.py --check
```

Expected:

- No failed tests in focused contract/formalism suite.
- Smoke passes.
- Collect-only has no new collection errors.
- Claim freeze has zero forbidden production claims.
- Figure audit has no unresolved canonical-symbol mismatch.
- PDF claim lint has zero failures; `lnB` plus detection-like language fails, not warns.
- Audit package check passes.

## Kill Switches

Stop and report a blocker if any task requires:

- native low-ell solver output;
- a native morphology atlas;
- treating external transfer as native;
- using MIO diagnostics as HTT evidence or posterior inputs;
- claiming local/global separation while matched-null FPR exceeds threshold;
- promoting scalar `x_C/Q/Pi/F/G_F` displays beyond their blocked diagnostic-only lane;
- silently clipping `F` or suppressing cancellation information;
- hiding stale legacy readiness labels in public/current packages.

## Final Deliverables

- Permanent archive of the two incoming packages.
- Response matrix with every finding and proposal item tracked.
- Corrected semantic-split figure or relabeled non-canonical bars.
- Canonical formalism figure-label linter.
- Detection-language claim lint promoted to fail.
- Revised manuscript prose and claim ladder.
- Sector-resolved departure profile, cancellation display, and magnitude companion.
- Comparator-multiverse and `Pi` policy displays.
- `G_F` floor/split/null-status displays and matched-null forecast report.
- Legacy readiness labels normalized for current/public surfaces.
- Rebuilt external re-audit ZIP and prompt focused on formalism originality and statistical semantics.
