# NSC self-adversarial audit — Stage 2: STEP-BACK (first principles per axis)

_What makes a JCAP/PRD result correct / novel / significant? Principles fixed BEFORE any lane
runs, so lane verdicts are judged against pre-registered criteria (not post-hoc rationalized)._

## Correctness (PRD referee standard)

1. Every quoted number must be reproducible from the shipped artifact chain (card -> script ->
   module), with stated assumptions sufficient to re-derive it.
2. An error bar is correct only if the quoted uncertainty dominates the known-omitted terms, or
   the omission is stated next to the number (not in a distant caveat).
3. A significance is correct only if the null distribution matches the estimator actually applied
   to the data (same window, mask, noise, selection). Analytic nulls that a cited paper has shown
   to be over-optimistic (Whitford 2023 for MV bulk flows) may not headline uncorrected.
4. A "consistency" or "upper limit" claim needs the same rigor as a detection: calibrated null,
   look-elsewhere accounting, and validated estimator (injection tests).
5. A structural result claimed "by construction" (e.g. Wiener-filter potential flow) must be
   labelled as by-construction, not presented as an empirical discovery.
6. Retracted/superseded results must be purged from every live claim surface (registry discipline).

## Novelty (JCAP referee standard)

1. Novelty is claimed relative to the published state of the art at submission date (2026-07),
   not relative to the project's own history.
2. Reproduction of a published measurement with a public catalogue is CONFIRMATORY, not novel —
   unless the method, the systematic control, or the combination is itself new and load-bearing.
3. Method novelty requires that no prior paper applied substantially the same estimator to
   substantially the same data for the same target quantity.
4. Framework novelty (identities, theorems, bound hierarchies) counts only if it enables an
   analysis or constraint that existing formalisms do not — otherwise it is re-derivation.
5. Missing citations to nearest prior art are a novelty finding regardless of verdict.

## Significance (editor standard)

1. Does the result change what a working cosmologist would do or believe? Null/consistency
   results are significant when they close a live controversy or retire a claimed anomaly with
   better systematics control than prior work.
2. Diagnostic-only results (project-internal validation, forecast machinery, estimator
   calibration) are supporting material, not headline significance.
3. A collection of small consistency checks does not sum to one significant paper unless unified
   by a framework that itself makes a falsifiable statement.
4. Venue fit: PRD/JCAP expect either a new constraint competitive with the field, a new method
   others will use, or a resolved discrepancy. Thesis-supporting infrastructure alone is neither.
5. The honest claim envelope (no family/geometry/detection claims; envelope in CLAUDE.md §1)
   caps the achievable significance — the audit must state what tier the current corpus reaches.

## Pre-registered scoring

Each axis scored 1–5 per cluster and overall: 5 = field-leading, 4 = solid PRD/JCAP,
3 = publishable with major revisions, 2 = workshop/technical-note tier, 1 = not publishable.
Recommendation vocabulary: accept / minor_revisions / major_revisions / reject_resubmit / reject.
