# Local continuation prompt — HTT tensorized report-first programme

Work only in `cosmosapjw-quantum/htt_base` and exclude native BASS solver work from this programme.

## Read first

1. `docs/research_reports/HTT_TENSORIZED_MES_RESPONSE_SYNTHESIS_20260903.md`
2. `docs/codex_handoff/htt_tensorized_report_first_20260903/AUTHORITY_LEDGER.yaml`
3. `docs/codex_handoff/htt_tensorized_report_first_20260903/REVISED_EXECUTION_PLAN.md`
4. PR #440 files under `docs/codex_handoff/mes_tensor_research_integration/`

## Non-negotiable supersession

- Do not use scalar-only MES ranks as current science.
- Do not reuse old WU-006--008 Q/O components, tensor ranks, foreground conclusions or injection-power interpretations as corrected output.
- Historical stored-real harmonic carrier bytes may be used only through their pinned Git identities.
- Do not create a new observed statistic after inspecting the corrected observation.
- Do not infer physical shear/vorticity, global tilt, local/global cause, foreground source or a Bianchi family from tensor morphology alone.

## Current task: R1 only

Use a fresh isolated checkout descended from:

```text
changeset/mes-tensor-research-integration-20260830
687234128d7c12d04e68aad0f303c21d2d470393
```

Confirm exact ancestry/tree before execution.

Run:

```bash
PYTHONPATH=htt/src python -m pytest -q -p no:cacheprovider \
  tests/common/test_mes_krylov_completion.py \
  tests/integration/test_mes_tensor_mapfree_repair.py

python -m py_compile \
  htt/src/common/mes_krylov_completion.py \
  scripts/observed_runs/rebuild_mes_tensor_carriers.py

git diff --check
```

If and only if those checks execute, run the map-free representation repair into a new directory:

```bash
python scripts/observed_runs/rebuild_mes_tensor_carriers.py \
  --repo . \
  --output-dir docs/generated/mes_tensor_representation_repair_run01 \
  --t0-uk 2725500 \
  --residual-epsilon1 0 \
  --execute
```

If that directory already exists, choose a new numbered directory. Never overwrite it.

## Load-bearing invariants

Verify and record:

```text
source commit = ccba350d7b725b227c64436e32af96abfe786449
source tree   = e91b8a4f57777c71c2bf1fc0f8c21395753481ba
paired carrier sha256 = 0a296c21902b691eb2e2b68a9b39f626020aa8c2b14fb93a1b12116215886b93
frozen scalar npz sha256 = b262425eb4f3a879513c02644bcbdd3ab313e487d101f6a29cb85284c30f845b
```

Stored convention:

```text
c_l0     = a_l0
c_lm,c   = sqrt(2) Re(a_lm)
c_lm,s   = -sqrt(2) Im(a_lm)
carrier metric = Euclidean
```

Tensor closure:

```text
Q:Q = 75/(8*pi) C2
O:O = 245/(8*pi) C3
```

MES conditional functions:

```text
epsilon2 = sqrt(75*C2/(8*pi))/T0
epsilon3 = sqrt(245*C3/(8*pi))/T0
B_sigma  = (5/3) epsilon1 + 3 epsilon2 + (3/7) epsilon3
B_omega  = (10/3) epsilon1 + (2/15) epsilon2
U_sigma  = (3/2) B_sigma^2
U_omega  = (3/2) B_omega^2
```

`epsilon1=0` is a declared conditional scenario, not an observed intrinsic-dipole result.

Rows:

- paired arm: one observed SMICA row + 300 ordered CMB+noise rows;
- CMB-only arm: one observed row + 999 CMB-only rows;
- include 00818;
- only 00970 is missing;
- same frozen observation carrier in both arms.

For noncyclic/ill-conditioned Krylov rows preserve original Q/O tensors and row membership. Do not invent axes.

## Required R1 terminal

Only one success-state wording is permitted:

```text
EXECUTED_PENDING_INDEPENDENT_REVIEW
```

Do not emit or promote:

- anomaly rank;
- p-value;
- preferred tensor statistic;
- local/global classification;
- empirical boost;
- physical source/family label.

## After R1

Stop and hand off the exact candidate head/tree, command log, input manifest, artifact hashes and pending terminal for an independent R2 review. Do not continue directly into observation evaluation.

After R2 passes, follow R3/R4 in `REVISED_EXECUTION_PLAN.md`. Resume WU-011 A4 only after the corrected observation programme is stable, unless the user explicitly reorders the DAG again.
