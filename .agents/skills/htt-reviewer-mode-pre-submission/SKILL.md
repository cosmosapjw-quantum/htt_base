---
name: htt-reviewer-mode-pre-submission
summary: Run severe pre-submission or pre-release peer review for HTT/MIO/BASS manuscripts, reports, PRs, and external audit packages.
description: Use before public release, external audit handoff, manuscript freeze, major PR merge, family-identification claims, or result-pack publication.
---

# HTT Reviewer Mode / Pre-submission Audit Skill

## Purpose

Simulate a severe but fair reviewer for the current project. This skill is not for encouragement; it is for finding what will break under scrutiny.

## Required reviewer roles

Run at least these distinct views:

1. Relativistic cosmology reviewer: GR/Bianchi/tilt/frame validity.
2. Statistical inference reviewer: likelihood, priors, nulls, look-elsewhere, PPC/LOOCV.
3. Numerical methods reviewer: convergence, stability, reproducibility, optional dependencies.
4. Software/reproducibility reviewer: packaging, tests, artifacts, manifests, installability.
5. Claim-hygiene editor: allowed language, caveats, publication tier.
6. Skeptical family-identification reviewer: equivalence classes, response rank, transfer provenance.

## Required output

```markdown
## Verdict
Choose one: PASS | PASS WITH MINOR REVISIONS | MAJOR REVISIONS | REJECT / NOT READY | INTERNAL ONLY

## Minimal publishable claim

## Strengths

## Fatal blockers

## Major concerns

## Minor concerns

## Novelty and scope

## Required validation

## Downclaims required

## Stronger claims allowed

## Merge/release decision
```

## Project-specific rejection triggers

- Bianchi family identification before native low-ell morphology atlas.
- HTT posterior/MIO certificate merge.
- Missing transfer provenance in result cards.
- Missing figure provenance in manuscript freeze.
- Tests or artifacts claimed as passed without recorded commands.
- `x,Q,Pi,F,G` semantics collapsed.

## Hard prohibitions

- Do not rescue a weak result by rhetoric.
- Do not ignore missing validation.
- Do not confuse ambition with demonstrated contribution.
- Do not accept cosmetic claim gates if the underlying evidence plumbing is redundant or wrong.
