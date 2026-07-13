---
name: htt-physmath-audit
description: Run evidence-locked, multi-role physics, mathematics, statistics, code, and data audits in htt_base using the vendored physmath GPT-5.6 coding/research harnesses. Use for JCAP/PRD-style hostile review, counterfactual advocate exploration, audit evidence packaging, or independent referee debates without weakening HTT/MIO/BASS/obsstat ownership, transfer provenance, or family-identification gates.
---

# HTT Physmath Audit

Use the unauthenticated upstream methodology snapshot as prompts and checklists,
not as scientific evidence or repository authority. `AGENTS.md`, the active
PR-DAG, COMMON contracts, and repo-local HTT skills always win.

## Vendored sources

- Coding harness: `harness_templates/vendor/physmath-gpt56/3.1.0/coding`
- Research harness: `harness_templates/vendor/physmath-gpt56/3.1.0/research`
- Never run either upstream initializer in the repository or immutable vendor
  roots. Initializer behavior may be tested only in a disposable copy.
- Run upstream validators only inside the vendored roots or disposable copies.
- Keep mutable run state under `docs/audits/<run>/state`; never write RUN_STATE,
  EVIDENCE, HYPOTHESIS, DECISION, or CLOSEOUT state into a vendor tree.

## Workflow

1. Freeze the task contract, Git/worktree state, input hashes, claim tier, and
   resource limits.
2. Map prior findings before new review. Treat a repeated finding as new only
   when there is downstream propagation, regression, contradictory independent
   evidence, severity change, or a historical antecedent.
3. Acquire and ledger external evidence, then seal a web-lock if the audit calls
   for offline brainstorming.
4. Run distinct theory, statistics, code, data, and claim-gate roles. Require
   each role to steelman its own case before attacking alternatives.
5. Preserve raw prompts, responses, commands, exit codes, seeds, environment,
   input/output hashes, and blockers. Never infer success from a missing log.
6. Keep counterfactual family/geometry work `hypothesis_only` and
   `public_use=false`, mapped to `ClaimTier.EXPLORATORY`,
   `ArtifactMode.INTERNAL_EXPLORATORY`, and `AllowedUse.INTERNAL_ONLY`; do not
   modify production guards or promote it into manuscripts, generated result
   tables, HTT evidence, or MIO certificates.
7. Rank survivors with independent judges. Candidate producers cannot promote
   their own proposals.
8. Run repo validation, claim/provenance checks, adversarial diff review, and
   pre-submission referee review before closeout.

## Scientific invariants

- HTT owns posterior/evidence/PPC/LOOCV; MIO owns diagnostic-only certificates.
- OBSSTAT extracts observables and null features; it does not infer families.
- BASS owns `TransferFunctionSpec`, atlas metadata, and the future native
  adapter; the native adapter remains schema-only and fail-closed.
- External/AniCLASS transfer output remains transfer-conditional and is never
  native BASS evidence.
- Scalar, directional, or external-transfer-only evidence cannot establish a
  Bianchi geometry or family.
- Teff/TSC is legacy evidence only.
- A blocked or timed-out decisive run remains `BLOCKED`; do not replace it with
  a smaller smoke result while keeping the original claim.
- The audit package is COMMON-owned `BundleKind.COMMON_CONTRACT`; record the
  audited component separately as `subject_owner` and never launder ownership.
- Namespace upstream terms as `audit_evidence`, `workflow_check_passed`,
  `audit_survivor`, and `hypothesis_class`; none imply Bayesian evidence,
  canonical validation, publication promotion, or Bianchi-family inference.
- Shared prompts and source ledgers create correlated viewpoints, not
  independent scientific replications.

## Required closeout

Emit a manifest-backed audit package with owner, scope, claim tier, transfer
source, config/input hashes, sky/mask status, covariance/null status, caveats,
generating command, and Git/worktree state. Separate as-shipped verdict,
minimal defensible claim, pre-solver program, post-native-solver program, and
accepted residual risks.
