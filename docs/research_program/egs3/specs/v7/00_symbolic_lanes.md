# v7 spec — symbolic-engine seal lanes (Phase 1)

owner: COMMON
implementation_scope: research_gates/egs3 + wolfram + sage + formal
claim_tier: diagnostic_only

## Goal

Stand up four independent symbolic-proof lanes so every v7 strengthened theorem can
be certified by the engine best suited to it, following the existing exit-2
registered-blocker + `--check` house pattern (`scripts/run_pr07_wolfram_proofs.py`,
`scripts/run_egs3_symbolic_seals.py`).

## Lanes (all built + green in Phase 1)

| Lane | Runner | Make target | Artifact | First seal (validated) |
| --- | --- | --- | --- | --- |
| SymPy (report-gating) | `run_egs3_symbolic_seals.py` | `egs3-seals` | `parent_identity_seal.json`, `bianchi_v_constraint_seal.json` | existing (rev-r146) |
| SageMath + Singular | `run_egs3_sage_seals.py` → `sage/egs3_v7_polyhedra.sage` | `egs3-sage` | `egs3_sage_seal.json` | T1′/DL1 exact endpoints (open `[11/100,17/100]`, all `[9/100,17/100]`) + Bianchi V ideal membership |
| Lean 4 core | `run_egs3_lean_seals.py` → `formal/` | `egs3-lean` | `egs3_lean_seal.json` | gate-promotion Bool-lattice + rational endpoint certificates (`native_decide`) |
| Wolfram (+xAct) | `run_pr07_wolfram_proofs.py` (generic) | `v7-wolfram` | `egs3_v7_wolfram_proofs.json` | T4′ Hotelling/F two-stage coverage (F thr 16.14 > χ² 15.51; uncorrected size 0.0608 > 0.05) |

Aggregate target `make v7-seals` runs all four.

## Policy

- **Report-gating**: only SymPy seals are fail-closed inputs to the v7 report generator
  (`REQUIRED_ARTIFACTS`), matching the v6 policy that never gates the report build on an
  external engine. Sage/Lean/Wolfram seals are local-lane witnesses recorded in the
  results table + ledger.
- **Fail-closed**: each runner exits 2 (registered blocker) when its engine is absent,
  exits 1 on any false check, 0 only when every check is true. `--check` diffs the
  regenerated payload against disk.
- **Contract**: `tests/contracts/test_egs3_v7_symbolic_lanes.py` asserts each artifact
  PASS + skips engine re-runs when the engine is missing (host-portable).

## Engine assignment for the v7 theorems (Phase 2/3 targets)

| Theorem | Primary engine | Rationale |
| --- | --- | --- |
| T1′ + DL1/DL2 (F1) | SymPy (affine/split-var) + **Sage** exact endpoints | rational polytope image is exact |
| T2′ (M1) | SymPy both-direction + Python `Fraction` corner enum + **Sage** face incidence | zero-tolerance strictness classifier |
| T4′ (M3) | SymPy scale-factor + **Wolfram** `FRatioDistribution` | distribution algebra native to WL |
| T5′ (P35 exact) | SymPy/scipy closed form + **Wolfram** `TimeConstrained[Resolve]` unimodality | Φ-expression endpoints |
| T8′ (E3) | SymPy `d/dλ`>0 + scipy `ncx2` | MLR monotonicity |
| T9′ (m1) | **SymPy** species-summed `derive_parent_identity` | 1-species must fall out bit-identical |
| T3-lin (M2) | **Wolfram + xAct** covariant residual + Python realization module | tensor bookkeeping |
| MES ε rederivation (M4) | **Wolfram** explicit multipole hierarchy + SymPy mirror | Phase 3, timeboxed |
| gate-promotion (T9 review) | **Lean core** `decide` | software-contract lattice |

## Deferred

mathlib-backed general ∀-lemmas (T1′/T2′ over ℚ/ℝ): the pure-core Lean lane covers the
concrete certificates; the exact ∀-statements are covered by Sage (exact rational polytope)
and SymPy (both-direction). A `formal/` mathlib extension is attemptable but the mathlib
cache fetch is slow in-sandbox (8542 files) — tracked as a deferred enhancement, not a
v7 blocker.
