# 12 — REPRO / INSPECTION COMMANDS

## A. State reconstruction — run first

```bash
git ls-remote https://github.com/cosmosapjw-quantum/htt_base.git \
  refs/heads/research/htt-referee-seeded-program-20260907-r1 \
  refs/heads/research/pr04-multicomponent
```

Pinned values at handoff generation:

```text
research/htt-referee-seeded-program-20260907-r1
  0e2d6e3a890ae44303440e8534fb6080d1dac881
research/pr04-multicomponent
  50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb
```

If the active master branch moved, **do not reset it**. Read the newer owner-approved state and reconcile this packet.

With an existing checkout:

```bash
git fetch origin --prune

git show 0e2d6e3a890ae44303440e8534fb6080d1dac881:docs/research_program/referee_seeded_20260907/00_MASTER_PLAN_KO.md
git show 0e2d6e3a890ae44303440e8534fb6080d1dac881:docs/research_program/referee_seeded_20260907/03_PROGRAM_DAG.yaml
git show b4d04e62d664997eb9e1858b6195c35e4ece3378:docs/research_program/post_review_20260907/THEORY_RESULTS.md
git show b4d04e62d664997eb9e1858b6195c35e4ece3378:docs/research_program/post_review_20260907/IMPLEMENTATION_CONTRACT.md
git show fa86d940f6d954af554bae5b577d5eb465aa2ae1:docs/research_program/review_seeded_20260907/REUSE_AND_DATA_MAP.md
```

## B. Accepted report identity — do not rerender for reassurance

Pedagogical artifact publication commit:

```text
9c86759f4ac7054d01d88689290a658e8ffd5863
```

Recorded PDF SHA-256 from its render receipt:

```text
6b6e7311ce782f1ce770326832aaae70382c1a42c218eb2692058d5392cc9ce4
```

R3 publication commit:

```text
d8894f1c526bdc5c8ebbb295ad91a0d92a4c8deb
```

## C. Exact donor/source inspection at future C0

```bash
git show 9f7d06dec0fce1c3a8a53fa5372c84d9c679c037:htt/src/common/mes_krylov_completion.py
git show 50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb:htt/obsstat/constrained_realizations.py
git show 50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb:htt/obsstat/affine_flow.py
git show 50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb:dl_pipeline/scripts/extract_desi_compact.py
git show 50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb:scripts/desi_dipole_measure.py
```

For nested packages, record the actual imported file before trusting a module name:

```python
import module_name
print(module_name.__file__)
```

## D. Commands intentionally NOT defined yet

There is **no canonical observed-analysis command** in this packet because `M1_CMB_MODEL`, `M2_REDSHIFT_MODEL`, `M3_EXPERIMENT` and `THEORY_FREEZE` are incomplete.

A fresh thread must not invent:

- final PR3/FFP10 pairing or null-pool construction;
- final redshift likelihood command;
- masks/bins/parameter grid;
- observed-fit thresholds or nuisance prior;
- new survey acquisition commands.

These must be emitted by the immutable M3/`THEORY_FREEZE` handoff.

## E. Historical completed suites — reuse by identity

Do not rerun the PR451 28-test decoder suite, PR455 80-test authority/T2 suite, PR458 90-test source replay, K2/R2 or report rendering merely to rebuild confidence. Re-run only affected regressions if a changed consumer actually depends on them.

## F. Git-return policy after freeze

Local Codex must publish readable source/diff/receipts/logs/results and `RETURN_TO_MAIN.md` on an isolated non-force branch/Draft PR. Large raw data stay local; Git stores only manifests/selected hashes/results needed to reproduce the run.
