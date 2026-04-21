# AUDIT_PRM-02_BASS_FAMILY_SWEEP_2026-04-22

## Scope

- packet: `PRM-02-BASS-FAMILY-SWEEP`
- authority: `docs/ver2_upgrade/*`
- mode: preliminary-results mode
- verification style: CoVe + metacognitive audit + equation-to-code consistency + touched-surface tests + script checks

## Target

Close the bounded representative family sweep for preliminary low-`\ell` results
without reopening deeper exactness work. The representative target set remains:

- `I`
- `V`
- `VII_0`
- `VIII`

The semantic solver domain remains all eleven Bianchi types with explicit
orthogonal-vs-tilted branching.

## Key finding

The main blocker was not runtime orchestration or exporter interoperability.
It was branch construction:

- representative **orthogonal** runs are executable on the native Tier-B path;
- representative **tilted** runs are currently blocked at the S1 Codazzi stage
  under the shipped global-tilt runtime construction.

Static/runtime probes showed:

- `V` has a non-trivial Codazzi operator and can satisfy single-species tilted
  projection at the IC-builder level, but the shipped all-species runtime tilt
  construction still fails the Codazzi surface;
- `VII_0` and `VIII` have a zero-rank Codazzi operator under the current
  representative tetrad/algebra path, so the current global-tilt runtime setup
  cannot realize those tilted branches and must remain an explicit block.

## Closure chosen

`PRM-02` closes by promoting:

1. a runnable representative **orthogonal** family sweep;
2. an explicit machine-readable **tilted runtime blocker** contract.

It does **not** fake a tilted fallback, local-boost reinterpretation, or
orthogonal relabel on failure.

## Code changes

- added executable evidence:
  - `validation.bass_representative_family_sweep`
- added CLI checks:
  - `htt/scripts/ver2_bass_validation.py --family-sweep-check`
  - `htt/scripts/ver2_bass_validation.py --family-sweep-json`
- added representative-family runtime tests:
  - orthogonal subset runs with expected algebra-aware propagator realizations
  - tilted subset fails controlledly with branch-specific Codazzi policy text
- mirrored the new campaign into the validation registry:
  - theorem
  - campaign
  - null manifest
  - injection manifest
  - hostile-audit runbook

## Physics / contract audit

- kept:
  - all-11-type domain metadata
  - explicit orthogonal-vs-tilted branch metadata
  - explicit global-tilt vs local-boost separation
  - PSTF/tetrad identity-derived constraint language
- refused:
  - silent tilted downgrade
  - local-boost substitution for global tilt
  - non-Type-I exactness promotion

## Verification

- `venv/bin/python -m py_compile htt/bass/validation/ver2_campaign_evidence.py htt/bass/runtime/test_ver2_tier_b_execution.py`
- `PYTHONPATH=htt:htt/src venv/bin/python -m pytest htt/bass/runtime/test_ver2_tier_b_execution.py htt/bass/validation/test_ver2_campaign_evidence.py htt/workspace/contracts/tests/test_ver2_validation_registry.py -q`
  - result: `37 passed`
- `PYTHONPATH=htt:htt/src venv/bin/python htt/scripts/ver2_bass_validation.py --family-sweep-check`
  - result: `PASS`
- `PYTHONPATH=htt:htt/src venv/bin/python htt/scripts/ver2_validation_registry.py --check`
  - result: `PASS`
- `PYTHONPATH=htt:htt/src venv/bin/python htt/scripts/ver2_hostile_audit.py --check`
  - result: `PASS`

Known warning retained:

- recombination table early-`z` coverage warning

## Carry-forward

- representative tilted runtime branches remain blocked on the shipped
  global-tilt runtime construction
- non-Type-I exact propagator remains approximate
- direction-resolved reionization microphysics remains absent

## Verdict

`PRM-02` is closed for preliminary-results mode.

The representative family sweep is now good enough to feed preliminary result
packs as long as:

- the orthogonal subset is used as the executable representative run set; and
- tilted runtime blockers remain explicit no-claim conditions.
