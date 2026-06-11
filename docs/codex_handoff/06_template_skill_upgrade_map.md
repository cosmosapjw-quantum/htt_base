# Template Skill Upgrade Map

This package integrates the uploaded `custom-codex-skills-template` into the HTT/BASS/MIO pre-solver Codex handoff package.

## Source template skills and upgraded repo skills

| Uploaded template skill | Upgraded repo skill | Main changes |
|---|---|---|
| `physics-math-audit` | `htt-physics-math-audit` | Added `x,Q,Pi,F,G`, local/global tilt, transfer provenance, Bianchi/MES/family-identification claim gates. |
| `scientific-code-validation` | `htt-scientific-code-validation` | Added HTT/MIO/common pytest subsets, DAG validation, mock/demo leakage scanner, transfer/claim-tier checks. |
| `latex-paper-build` | `htt-latex-paper-build` | Added figure provenance, missing figure scan, manuscript claim language audit, Teff legacy downclaim rules. |
| `ssot-handoff-maintainer` | `htt-ssot-handoff-maintainer` | Added five-PR checkpoint, generated status/claim ledger, PR progress, blocker tracking. |
| `claim-provenance-ledger` | `htt-claim-provenance-ledger` | Added owner/scope/claim-tier fields and forbidden patterns for MIO/HTT/Teff/family claims. |
| `reviewer-mode-pre-submission` | `htt-reviewer-mode-pre-submission` | Added severe multi-role review focused on cosmology, inference, reproducibility, family ID, and release gates. |
| `research-plot-summary` | `htt-research-plot-summary` | Added plot categories, manifest requirements, local/global and transfer sensitivity plot guidance. |

## New skills added beyond the template

| Skill | Reason |
|---|---|
| `htt-solver-handoff-readiness-audit` | Encodes the external low-ell solver design-document audit prompt as a reusable repo skill while preventing accidental solver implementation inside `htt_base`. |
| `htt-family-identification-gate` | Guards C5/C6 geometry/family claims, equivalence-class breaking, and native morphology atlas requirements. |

## Integration principle

These skills supplement the existing HTT repo skills. They do not replace the DAG, AGENTS, subagents, or rules. They add research-harness depth: mathematical audit, validation discipline, LaTeX/figure audit, SSOT handoff, claim provenance, pre-submission review, plotting provenance, solver handoff audit, and family-identification safety.
