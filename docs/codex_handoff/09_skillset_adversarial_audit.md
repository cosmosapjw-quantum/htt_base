# Skillset Adversarial Audit and Refinement Notes

## Audit verdict

The uploaded generic research-harness skills were useful but too broad for this repo. They lacked explicit HTT/MIO/BASS ownership rules, transfer-provenance gates, `x,Q,Pi,F,G` semantics, local/global tilt discrimination, native solver handoff boundaries, and family-identification kill-switches.

## Major corrections made

1. Added `htt-` prefixes to avoid collisions with user/global skills.
2. Added project-specific claim vocabulary: `CONDITIONAL`, `DIAGNOSTIC_ONLY`, claim tiers C0--C6, transfer source fields.
3. Added explicit MIO/HTT no-merge rules.
4. Added external/native transfer source gates.
5. Added family-identification gate as a separate skill.
6. Added solver design handoff audit skill that reviews external low-ell solver specs without implementing the solver in this repo.
7. Added scripts for skill layout verification, claim scanning, forbidden-claim scanning, LaTeX log scan, missing figure scan, validation dispatch, and handoff packaging.

## Remaining risks

- Skill descriptions must remain concise enough for implicit activation. If Codex stops invoking a skill, shorten the description but preserve the hard rules inside `SKILL.md`.
- Project-local rules only load after trusting the project `.codex` layer.
- Scripts are conservative static checks. They do not replace human review or domain validation.
- Some previous v2 skills and new template skills overlap. The trigger matrix resolves the order: domain-specific skill first, generic/ledger skill second, adversarial review last.

## Installation gate

A package installation is acceptable only if:

```bash
python scripts/codex_harness/verify_skill_layout.py .
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
```

both pass.
