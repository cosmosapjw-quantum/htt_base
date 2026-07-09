# M4 resolution — MES bound-coefficient provenance from primary sources

Resolves external-review finding **M4** ("the MES ε-coefficients are registered-external,
never rederived"). Ticket: `docs/research_program/egs3/tickets/mes_full_rederivation.yaml`.

## Primary sources (web-retrieved 2026-07-10, archived in this directory)

| Tag | Reference | arXiv | Local text |
|-----|-----------|-------|-----------|
| **MESa** (Paper I) | Maartens, Ellis, Stoeger, *Limits on anisotropy and inhomogeneity from the CBR*, **Phys. Rev. D 51, 1525 (1995)** | `astro-ph/9501016` | `mesa_astro-ph_9501016_PRD51_1525.txt` |
| **companion** | Maartens, Ellis, Stoeger, *Anisotropy and inhomogeneity of the universe from ΔT/T* | `astro-ph/9510126` | `companion_astro-ph_9510126_deltaT.txt` |
| **MESb** (Paper II) | Maartens, Ellis, Stoeger, *Improved limits …*, **Phys. Rev. D 51, 5942 (1995)** | *not on arXiv (print-only)* | — |

MESa assumes **geodesic flow** (`u̇_a = 0`, MESa p.123) — so MESa contains **no
acceleration bound**, and its vorticity bound differs from the registry (see below).
MESb relaxes the assumptions to be "in principle observational", which is where the
registered ω/accel coefficients and the acceleration bound come from.

## Registry under audit (`htt/tsc/admissibility/three_bound_hierarchy.py:106-113`)

```
B_sigma = (5/3) e1 + 3   e2 + (3/7)  e3
B_omega = (3/4) e1 + 2   e2 + (2/7)  e3
B_accel = (3/4) e1 + 1   e2 + (3/14) e3
```
where `e1,e2,e3` bound the residual-dipole / quadrupole / octopole ΔT/T amplitudes.
Ceilings `X²_max = (3/2) B_X²` → registered `W2_max = 1.309e-6` (load-bearing).

## Result 1 — σ coefficients: GENUINE bit-exact rederivation ✓

MESa **eq (51)** (raw shear bound, before the observational reduction; identical to
companion **eq (6)**), reading the leading rational as `8/3` (the extracted `"3/8"` is a
digit-swap — only `8/3` closes the reduction, and both eq (7) and eq (59) give `3 e2`):

```
|σ|/Θ  <  (8/3) e2  +  e2*  +  5 e1'  +  (9/7) e3'
```
Reduction assumptions, stated in MESa:
- **C1** (spatial ≤ time-derivative): `e_L' ≤ e_L*`, `e_L'' ≤ e_L**`, …
- **C2** (time-derivative ≈ multipole / characteristic time, with `Θ t_R ≃ 3`):
  `e_L* ≃ e_L/3`, `e_L** ≃ e_L/9`, `e_L*** ≃ e_L/27`.

Applying C1 then C2:
```
(8/3) e2 + e2*  → (8/3) e2 + (1/3) e2 = 3 e2
5 e1'           → 5 e1* → 5·(1/3) e1  = (5/3) e1
(9/7) e3'       → (9/7) e3* → (9/7)(1/3) e3 = (3/7) e3
```
→ `|σ|/Θ < (5/3) e1 + 3 e2 + (3/7) e3`  =  MESa **eq (59)** = companion **eq (7)**
= registered `B_sigma`. **Exact.** The σ coefficients are now rederived, not registered-external.

## Result 2 — machinery validated on MESa's ω (eq 52 → eq 60) ✓

MESa **eq (52)** raw vorticity bound `|ω|/Θ < 9 e1' + 3 e1'* + (6/5) e2''`, under C1/C2:
```
9 e1'   → 9 e1*  → 9·(1/3) e1  = 3 e1
3 e1'*  → 3 e1** → 3·(1/9) e1  = (1/3) e1
(6/5)e2'' → (6/5)e2** → (6/5)(1/9) e2 = (2/15) e2
```
→ `|ω|/Θ < (10/3) e1 + (2/15) e2` = MESa **eq (60)**. **Exact.** This validates that the
reduction machinery is understood correctly.

## Result 3 — ω/accel registry ≠ MESa: they are MESb (Paper II) values

MESa's **rederived** ω is `(10/3, 2/15, 0)` — it does **not** equal the registered
`B_omega = (3/4, 2, 2/7)`, and MESa has no accel bound at all. The registry is therefore
citing **MESb Eqs (30)–(36)** (the companion, astro-ph/9510126 lines 196/248, states the
σ bound is "MESb Eq (24)" and "the remaining limits are given in MESb (Eq. (30)–(36))").
MESb relaxes MESa's geodesic assumption, which (i) revises ω away from the MESa value and
(ii) introduces the acceleration bound. **MESb is print-only (not on arXiv)**, so its
internal derivation of `(3/4,2,2/7)` and `(3/4,1,3/14)` is not reconstructable in-repo.

**Honest status:** σ is rederived (bit-exact) from MESa. ω/accel are pinned to their exact
MESb primary-source citation with the Paper-I→Paper-II lineage documented; they remain
`primary_sourced_not_rederivable` (MESb print-only) rather than the previous vague
`registered_external`. This is the ticket `exit_gate`'s "documented discrepancy/provenance
report (itself a publishable finding)" branch. The `Thm 3.1/3.2/3.3, Eq. 3.7/3.12/3.15`
labels in the registry are a **secondary-source reorganization**, not MESa/MESb primary
equation numbers; the primary crosswalk above supersedes them.

## Invariance

No coefficient value changes. `B_sigma/B_omega/B_accel`, the ceilings, `W2_max = 1.309e-6`,
and every `x_C` anchor stay **bit-identical**; this is a provenance upgrade only.
