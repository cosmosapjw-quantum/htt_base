---
name: htt-solver-handoff-readiness-audit
summary: Audit low-ell Bianchi solver design documents for LLM coding-agent handoff readiness without implementing the solver in the current repo.
description: Use when reviewing external/native low-ell Bianchi solver design docs, solver handoff prompts, 1+3 PSTF/tetrad architecture, Bianchi family coverage, implementation skeletons, or solver-to-observer interface readiness.
---

# HTT Solver Handoff Readiness Audit Skill

## Purpose

Evaluate whether low-ell Bianchi solver design documents are implementation-ready for a coding agent. This skill does not implement the solver inside `htt_base`.

## Mandatory exclusions

Do not evaluate:

- completed solver code existence;
- runtime benchmarks;
- Planck/data fitting;
- observational posterior/evidence;
- conservative downclaiming of anisotropy goals.

## Required audit roles

1. Formalism fidelity: 1+3 PSTF authority + tetrad backend coherence.
2. Constraint identity: Gauss/Codazzi/Bianchi constraints as code contracts.
3. Family coverage: all 11 Bianchi types, orthogonal/tilted/local-boost separation.
4. Physics completeness: redshift, screen basis, electron-frame Thomson, TCA, neutrino, visibility, reionization, tilt, mode mixing.
5. Algorithm/pseudocode readiness: state vector, operators, adaptive step, interpolation, residual monitor, API.
6. Observables boundary: solver-core vs observer/statistics separation.
7. WBS workflow: PR list, scoreboard, hallucination/local-minima guards.
8. Overclaim honesty: solver-ready vs architecture slogans.

## Required output

```markdown
## Handoff readiness verdict
Choose: READY | READY WITH PATCHES | MAJOR DESIGN PATCHES | NOT READY

## Steelman of the design

## Blocking gaps

## Implementation-ready content

## Underdetermined content

## Family coverage audit

## Physics completeness audit

## API / state / operator readiness

## Required patches before coding-agent handoff
```

## Hard prohibitions

- Do not ask the current repo to implement the solver as part of pre-solver HTT PRs.
- Do not accept family naming without backend/IC/interface details.
- Do not accept mock spectrum fitting as a solver validation substitute.
