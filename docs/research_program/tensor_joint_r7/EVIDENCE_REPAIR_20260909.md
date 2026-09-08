# R7 evidence-consumer repair (2026-09-09)

Base: `433433409ee95f48759fca4193b727a43bde4872`. This is a new bounded task after the prior full-plan STOP_INVALID. It repairs R7-A01/A02 and stale review consumption; it does not rerun or re-admit unchanged science.

## Fixed acceptance

- [x] E1: Fail/blocked CAS notes containing CAS_4AXIS_PASS emit no certification capability.
- [x] E2: Matching current contract and four valid observed PASS axes retain only the existing narrow mathematical capability.
- [x] E3: CAS missing-to-present and contract changes invalidate their node and affected descendants only.
- [x] E4: Donor-only byte changes trigger pin checking at intake and consumption without repinning.
- [x] E5: Review PASS requires its final_source_sha256 to match the actual reviewed files.
- [x] E6: Unchanged input/source/contract/evidence resume creates no new attempts.

## Execution boundary

One root writer owns code/docs/tests. A read-only evidence mapper may identify the existing CAS schema; one independent reviewer examines the completed patch. A coherent repair episode can include multiple cause-specific edits and targeted validations. A narrow confirmation of the registered review findings is part of the declared closeout, not a new assurance wave. Existing source pins, scientific arrays, laws, figures, CAS execution records and prior failure verdicts stay unchanged. No global rule or hook changes are part of this unit.

R7-A03 (orbit refinement), R7-A04 (per-test donor obligations), R7-A05 (non-axis-aligned singular support), new law execution and review87 physical adaptation remain separately scoped work. The corrected attribution for the ten donor failures is selective-port compatibility/evidence-path omissions; they were not demonstrated baseline failures and not all are publication wrappers.

## Validation and preserved evidence

The common evidence consumer checks exact aggregate and per-axis outcomes, runner-observed execution eligibility, the current contract hash, its named source pins, all seven typed obligation results, domain differences and counterexamples. It supports only the existing R7 four-axis algebra scope. Missing or malformed optional CAS evidence withholds certification while preserving independently tested elementary algebra. `adjudicate` and preflight cannot supply observed-execution eligibility.

Named missing/present file states now participate in resume fingerprints. CAS evidence, contract and contract sources bind R7-01; individual donor files bind R7-00 and R7-02; review evidence and its source map bind R7-23. R7-02 also checks the current donor bytes at consumption, independently of cached intake. A review status alone no longer issues `FINAL_AUDIT`.

The targeted command was run with the existing workstation Python and verified target-worktree imports:

```bash
/mnt/sn850x2t/htt_base_e2e/venvs/htt_base-py312-20260829/bin/python -B -m pytest -o addopts='' --import-mode=importlib tests/r7/test_evidence_binding.py tests/r7/test_campaign_routing.py -q
```

Host result: **51 passed in 3.01 s**. Independent reviewer execution: **51 passed in 3.25 s**; final review disposition is recorded below. Tests use isolated evidence and routing fixtures, not scientific simulations. They check selective invalidation, preserved old attempts and zero new attempts on unchanged resume. Existing routing failure scenarios remain covered.

Run evidence is under `.agent-harness/runs/TENSOR-JOINT-R7-EVIDENCE-20260909/`. `raw_logs/baseline-reproduction.txt` loads the `43343340` driver in memory and reproduces the false capabilities, stale donor/review consumption and dependency omissions; its dependency fixtures use the repaired generic file-state runner. Its 29 failures include assertions about new metadata, so this is not a count of 29 distinct defects. Earlier `before.txt` and `after-first.txt` retain test-fixture construction failures; they are not scientific validation failures. `raw_logs/targeted.txt` is the passing host run.

`artifacts/current_binding.json` records that all **31 selected donor pins** match and the preserved observed CAS report still matches its original contract and source inputs. The old review now fails current-source binding for the two changed drivers, as required. No tracked historical R7 generated artifact or old CAS run file differs from `43343340`. Gaussian trials, CAS engines, observed analyses and figure generation were not rerun. The conditional qiso result, original `STOP_INVALID`, failed donor logs and earlier attempts remain historical evidence with their original scope.

The pre-existing worktree active-run pointer referred to the old completed R7 unit. Its close validator rejected historical envelope/launch fields; the pointer was cleared using `close_run.py --abandon`, which preserved the entire old run directory. The mapper's native stop hook also resolved the unrelated original checkout, and its read-only role did not write a result envelope. Its delivered schema guidance is recorded separately in `artifacts/cas_schema_delivery.json`. These operational limitations are not CAS failures; no global hook, old envelope or original checkout active run was repaired or rewritten.

## Bounded disposition

Independent technical review: **PASS**, no blocking findings. Besides the 51 assigned tests, the reviewer ran **9 independent tests in 0.36 s**, including CAS removal, contract arrival and review arrival/removal. The result and exact reviewed source identities are in `results/evidence_review.json`; scripts and logs are in `artifacts/evidence_review/`. A final document-only closeout check binds this disposition to the completed task record; no implementation changed after independent testing. The review establishes these six evidence-consumption boundaries, not new mathematical proofs, scientific coverage, reviewer-independence certification or whole-plan completion.

The native stop hook rejected that review's operational closeout because it resolved the unrelated original checkout/run. The result explicitly records `REJECTED_WRONG_CHECKOUT_RUN_CONTEXT`; no hook PASS or verified launch receipt is claimed. Host adjudication in `ADJUDICATION.md` and `artifacts/acceptance.json` records local E1–E6 acceptance separately from that operational limitation and the unchanged full-R7 `STOP_INVALID`.

This increment is a local implementation commit. The published `43343340` remains the prior remote checkpoint; this unit does not automatically push or merge its changes. The next scientific work remains orbit-distance/rank refinement and additional qualified observed-law execution in separately bounded units.
