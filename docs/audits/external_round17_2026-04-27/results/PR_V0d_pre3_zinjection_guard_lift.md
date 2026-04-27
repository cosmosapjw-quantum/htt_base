# PR-V0d-pre3 — `cosmological_config.py` z_injection guard lift

**Run:** 2026-04-27. **Files touched:**
- `htt/bass/runtime/cosmological_config.py` (helper validation logic)
- `htt/bass/runtime/test_cosmological_config.py` (1 test replaced, 3 new)

## What this PR does

Replaces the legacy hard guard `z_injection ∈ [100, 5000]` in
`cosmological_critical_etas` with **species-table-aware validation**:

| Old behaviour (pre-pre3) | New behaviour (post-pre3) |
|---|---|
| `if not (100.0 <= z_injection <= 5000.0): raise` | `if z_injection <= 0: raise; if a_injection ∉ [bg_table.a[0], 1.0]: raise` |
| z = 50 → rejected | z = 50 → accepted (bg_table covers it) |
| z = 10000 → rejected | z = 10000 → accepted (bg_table covers up to z ≈ 10⁸) |
| z = 1.0 × 10¹⁰ → rejected | z = 1.0 × 10¹⁰ → rejected (outside bg_table; clear error) |
| z = 0 → "z must lie in [100, 5000]" | z = 0 → "z_injection must be positive (z=0 is the integration endpoint)" |
| z < 0 → "z must lie in [100, 5000]" | z < 0 → "z_injection must be positive" |

The new error for z outside the bg_table range explicitly points at
**PR-V0d-pre2** (species-extension): *"Extend the species registry
(Round-17 PR-V0d-pre2) for deeper anchors."*

## Why

The hard `[100, 5000]` guard was added during V5 Blocker-3 work
(commit `bce0eb9`) when the helper was first introduced as a
recombination-anchor convenience. At that point the helper's only
intended use was Planck-2018 z_* anchoring. Round-17 V0d (the audit
sweep that exposed the species-table-edge / IMEX-tuning gap) hit the
guard at z = 5000 (η ≈ 100 Mpc) and below, so V0d's monkey-patch
bypassed `build_cosmological_integrator_config` entirely.

The bg_table itself is built with `a_start = 1e-8` (z ≈ 10⁸) — the
hard guard was at least 4 orders of magnitude tighter than the actual
bg_table coverage. Lifting the guard:

- Unblocks V0d-style direct η_init sweeps via the helper (no monkey-patching needed).
- Documents the actual coverage limit (bg_table.a[0]) explicitly in the error message.
- Surfaces the species-extension prerequisite (PR-V0d-pre2) at the right place.

## Caveats (carried forward to pre2)

The bg_table coverage is **not** the same as the visibility/Γ_T/HYREC
coverage. The species registry warning at runtime (visible in the
test output) makes this explicit:

> *"recombination table z-range [0.0, 8000.0] does not fully cover
> FLRW η-grid (z ∈ [0.0, 99999999.0]); queries of x_e / T_m / tau_dot
> outside the table will raise."*

So `cosmological_critical_etas` post-pre3 accepts z ∈ (0, ~10⁸], but
downstream IMEX integration with `Γ_T(η)` evaluation will fail or
silently degrade at z > 8000 until the HYREC fixture is extended
(PR-V0d-pre2).

This boundary is currently the **load-bearing reason V0d cannot test
D-2 cleanly at η_init < ~100 Mpc** — confirmed by V0d post-pre1's
unchanged-or-worse behaviour at deeper anchors (PCHIP overflow
warnings firing at η_init ∈ {100, 70} where HYREC was extrapolating).

## Verification

- 287 Round-16 baseline + 304 perturbation + 14 tau_c-override + 15
  cosmological_config tests = **620 total passing in 18.60 s**.
- 4 new tests in `test_cosmological_config.py`:
  - `test_cosmological_critical_etas_rejects_non_positive_z` (replaces old)
  - `test_cosmological_critical_etas_rejects_z_outside_bg_table`
  - `test_cosmological_critical_etas_accepts_z_inside_bg_table_below_legacy_floor`
  - `test_cosmological_critical_etas_accepts_z_inside_bg_table_above_legacy_ceiling`

## Phase 0.5 status

- ✅ PR-V0d-pre1 (committed `125a989`): tau_c plumbing
- ✅ PR-V0d-pre3 (this commit): z_injection guard lift
- ⏳ PR-V0d-pre2 (sub-week-to-2w): species registry extension to z = 10⁹
  — the only remaining Phase-0.5 gate. After this lands, V0d can
  re-run on a clean baseline and the audit's monotone-collapse
  prediction can be tested.
