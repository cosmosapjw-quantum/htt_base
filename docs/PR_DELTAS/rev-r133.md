# REV-R133 - Report completeness verification + root research-evaluation package

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: mixed_none_observed_and_external_transfer_conditional
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Precisely re-verify that all development + research to date (before external data
finishes downloading) is fully reflected in the research report, and produce a
self-contained, context-independent zip + prompt at repo root for a critical &
constructive research-content evaluation.

## Report completeness audit (rev-r122 .. r132)

Cross-checked the report against every deliverable. Gap found + filled: the report
covered EGS3/PSD (\S8), the figure gallery + consolidated table (\S9), and the
K1/K5/K6 discharges (\S10), but did **not** reflect the rev-r129 **PR08-006 joint
comparator** or the cobaya K1 finding. Added to \S10:
- a "Joint comparator (PR08-006)" paragraph: Omega_tilt measured (K5), Sigma^2 partial
  (K1), W^2/Omega_k fail-closed (K6 no-go + no channel); data rank 2 separate from
  prior-conditioned rank; no collapsed x_C; no MIO-as-odds; no scalar->family;
- a cobaya note (planck_2018_lowl.TT gives the C_ell-level likelihood, not maps) + a
  pointer to K1_E2E_DOWNLOAD_GUIDE.md.
Report recompiled (23 pp), `pdf_claim_lint` 0 failed / 0 warning. The report now
reflects all research/development through rev-r132.

## Root research-evaluation package

`scripts/build_research_evaluation_package.py` (new) writes at **repo root**:
- `htt_base_research_evaluation_package.zip` (67 entries),
- `htt_base_research_evaluation_package_manifest.json`,
- `htt_base_research_evaluation_prompt.md`.

Self-contained + context-independent: the report (PDF+tex), the **essential research
code** that produces every headline (five-variable + graded/PSD comparator,
EGS2/EGS3 theorem modules, GR/Boltzmann transfer, the real-data estimators, the
K1/K5/K6 + PR08-006 discharge drivers, Wolfram cores), the **runnable gate tests**,
the **result records** (consolidated table, discharge JSONs, joint artifact, proofs),
and BLOCKERS + K1 guide. The prompt explains the project from scratch and asks for a
**critical AND constructive** research-content review (verdict, novelty, theorem +
statistics audits, constructive roadmap, claim-tier corrections) with the hard claim
boundaries stated. Deterministic (fixed zip date, sorted entries, content-addressed
provenance -> no git-state churn); `--check` + `tests/contracts/test_research_evaluation_package.py`.

## Claim discipline

Diagnostic-only / model-independent / conditional-theorem content. No family-ID,
geometry, native-solver, MIO-as-odds, or scalar->family. The evaluation prompt states
these boundaries so an external reviewer flags any violation.

## Validation

| Command | Status |
| --- | --- |
| `latexmk` report | PASS; 23 pages |
| `pdf_claim_lint` | Failed 0, Warning 0 |
| `build_research_evaluation_package.py` + `--check` | 67 entries, byte-deterministic |
| `pytest tests/contracts/` | 352 passed, 0 failed |
