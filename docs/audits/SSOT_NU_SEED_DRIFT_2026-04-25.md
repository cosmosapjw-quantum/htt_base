# SSOT drift audit — ν regular-adiabatic seed amplitude factor

**Date**: 2026-04-25
**Track**: V5-RUNTIME Round-10 (R9-D follow-up; bug located 2026-04-24
commit `5e4d3ea`)
**Scope**: `htt/bass/perturbation/regular_adiabatic_ic.py::_seed_formulae`
two-line fix + 3 regression tests + this audit document. Single-commit
landing per user approval (2026-04-25).
**Template**: matches `docs/audits/SSOT_TCMB_DRIFT_2026-04-19.md`.

---

## 1. Finding

`_seed_formulae` (lines 144-145) computed the regular-adiabatic
neutrino quadrupole `π_ν` and octupole `G_3` without the `B_K_sq`
amplitude factor that scales every other perturbation in the same
function:

| Field | Pre-fix | B_K_sq linear? |
|---|---|---|
| `eta_cov` | `2 * B_K_sq * (1 − x²/12 · (...))` | yes |
| `delta_gamma` | `(B_K_sq / 3) * x² − ...` | yes |
| `delta_b` | `(B_K_sq / 4) * x² − ...` | yes |
| `theta_gamma` | `(B_K_sq / 27) * x³` | yes |
| `theta_nu` | `(B_K_sq / 27) * ((4R_ν+23)/denom) * x³` | yes |
| **`pi_nu`** | `-(4 / (3·denom)) * x²` | **NO — bug** |
| **`G_3`** | `-(4 / (21·denom)) * x³` | **NO — bug** |
| `Z` | `-(B_K_sq / 2) * k * η_init + ...` | yes |
| `pi_gamma` | `-(32/45) * k * τ_c * theta_gamma` | yes (via `theta_gamma`) |
| `E_2` | `0.25 * pi_gamma` | yes (via `pi_gamma`) |

Of the 11 leading-order seed formulas, 9 are linear in `B_K_sq` and 2
are not. There is no docstring or comment indicating the two
outliers are intentionally amplitude-independent.

## 2. Why this matters (physics)

Per Ma-Bertschinger 1995 §7 / eq. 96-99, the regular adiabatic mode
is a **single-parameter family** indexed by the integration constant
`C` (which in BASS plays the role of `B_K_sq`):

```
δ_γ = -(2/3) · C · (kτ)²
δ_b = δ_c = (3/4) δ_γ
σ_ν = (1/15) · 2C / (4R_ν + 15) · (kτ)²
F_ν,3 ∝ C · (kτ)³ / (4R_ν + 15)
```

Every leading-order perturbation is linear in `C`. At `C = 0` the
mode is the unperturbed FLRW background — **all** perturbations
vanish. This is not a convention choice; it is the mathematical
content of "regular adiabatic mode" in linear perturbation theory.

The CAMB notes' apparently amplitude-free expressions
`π_ν = -4 x²/(3·denom)` and `G_3 = -4 x³/(21·denom)` are amplitude-
free *only because CAMB has fixed* `χ_0 = -1` *as the unit
normalization* (auditor #6, citing CAMB notes §IX). When BASS exposed
an arbitrary-amplitude API via `b_k_sq`, the factor had to be
restored on these two lines but was not.

## 3. Empirical evidence (already in repo, pre-fix)

R9-D bias-floor probe (`scripts/v5_round9_bias_floor_probe.py`,
output `transcripts/R9D_bias_floor_probe.txt`):

| k [Mpc⁻¹] | Δ_bias(ℓ=2) | Δ_target(ℓ=2) | α(ℓ=2) | \|Δ_b\|/\|Δ_t\| |
|---|---|---|---|---|
| 1e-5 | +5.81 | -3.02 | -8.83 | 1.93 |
| 3e-5 | +7.33 | -3.24 | -10.57 | 2.26 |
| 1e-4 | +7.89 | -2.56 | -10.45 | **3.08** |
| 3e-4 | +1.81 | -0.89 | -2.70 | 2.03 |
| 1e-3 | -0.003 | +0.009 | +0.013 | 0.36 |

Bias floor at `b_k_sq=0` is non-zero, structured, and exceeds the
linear target signal in magnitude across the super-horizon range
with opposite sign — the unique signature of an additive ζ-
independent contamination at the seed level (ruling out projector,
integrator, or normalization origins; see Round-9 audit Step 4).

## 4. External audit chain

Six independent external auditors received the bundle
`v5_round9_audit_bundle.zip` (or repo-direct prompt
`docs/V5_ROUND9_EXTERNAL_AGENT_AUDIT_PROMPT.md`) and produced
verdicts in `report{1..6}.txt` (untracked, 2026-04-24).

**All six CONFIRMED.** Differences were limited to:
- D_2 anchor impact (resolved against `_d2_anchor_golden.json`:
  Rust-source path → 0% shift)
- Trial-fix residual ~7.6e+02 ratio (independent R9-B/C convention
  question, deferred)
- Cosmetic naming and follow-up scope (deferred)

## 5. Fix landed (this commit)

`htt/bass/perturbation/regular_adiabatic_ic.py` lines 144-145:

```diff
- pi_nu = -(4.0 / (3.0 * denom)) * x2
- G_3   = -(4.0 / (21.0 * denom)) * x3
+ pi_nu = -B_K_sq * (4.0 / (3.0 * denom)) * x2
+ G_3   = -B_K_sq * (4.0 / (21.0 * denom)) * x3
```

Test changes (`test_fb53_regular_adiabatic_ic_skeleton.py`):

- `test_fb53_zero_amplitude_seed_has_no_neutrino_perturbation`:
  removed `pytest.mark.xfail(strict=True)`; widened from {`pi_nu`,
  `G_3`} to all 14 amplitude-dependent fields (auditor #3 rec. 1).
- New: `test_fb53_packed_state_zero_at_zero_amplitude` — asserts the
  full packed seed array contains zeros except at the background `a`
  slot (auditor #3 rec. 2; guards future fields added to the packer
  but forgotten to scale by `B_K_sq`).
- New: `test_fb53_seed_scales_linearly_with_b_k_sq` parametrized at
  `b_k_sq = 2.0` vs `1.0` (auditor #3 rec. 5; the key regression —
  the bug went undetected because no prior test exercised
  `b_k_sq ≠ 1`).

## 6. Numerical impact

Per consensus auditor analysis + verified against
`_d2_anchor_golden.json`:

- **Route-B Rust `D_2 = 1002.086744 μK²` anchor**: `0% — bit-
  identical`. The Rust binary `dump_dl_spectrum_sparse` is the MB-95
  sync-gauge production path (`sync_gauge_camb.rs`) and does not
  consume `regular_adiabatic_ic.py`.
- **Route-B Python golden** (`route_b_d2_lookup` MM-curve in
  `_d2_anchor_golden.json`): `0% — analytic`. This is the
  `(C1, C2) = (17530000, 682500)` MM curve evaluated at fixed Σ²
  points — no ν seed in the path.
- **PSTF Python R9-B convention audit** ratio: `~22× reduction`
  (1.7e+04 → 7.6e+02 at N_k=12; trial-fix measurements concordant
  across auditors #1 and #5).

The legacy bit-identical anchor is preserved because the buggy
formulas are no-ops at `b_k_sq = 1.0` (the historical default), and
the Rust Route-B path does not consume the Python `_seed_formulae`.

## 7. Sign-off gate

- [x] bug located (commit `5e4d3ea`, 2026-04-24)
- [x] xfail regression marker placed (commit `6a072e6`, 2026-04-24)
- [x] external audit bundle published
  (`v5_round9_audit_bundle.zip`, 2026-04-24)
- [x] external audit prompt published
  (`docs/V5_ROUND9_EXTERNAL_AGENT_AUDIT_PROMPT.md`, 2026-04-24)
- [x] 6/6 external auditors CONFIRMED (2026-04-24)
- [x] user approval on Round-10 fix plan (2026-04-25)
- [x] **fix landed** in this commit

## 8. Out of scope (deferred)

- **Round-11 — residual ~7.6e+02 PSTF convention ratio**. Auditors
  #1 and #5 confirm this is independent of the seed bug; it is the
  R9-B/C convention question that remained open at the end of
  Round-9. Likely root: B_K_sq vs ζ vs ζ² semantic mismatch at the
  pipeline boundary, plus N_k quadrature artifacts on the residual
  super-horizon spike.
- **Round-11 — `B_K_sq` naming cleanup**. Auditors #2 and #6
  recommend splitting into `amplitude` + `beta2_geom` (CAMB Notes
  geometric eigenvalue). Cosmetic; defer to keep the bugfix commit
  surgical.
- **Round-12 — `eta_cov` convention re-check**. Auditor #2 flags
  this as also potentially questionable. `eta_cov` is currently a
  metadata-only field (does not enter the integrator state vector;
  see Round-9 §5 code archaeology), so the runtime fix is unaffected.
- **`B_K_sq` docstring reword**. The docstring at lines 113-117 of
  `regular_adiabatic_ic.py` calls `b_k_sq` "primordial amplitude
  squared", which several auditors note is misleading (the variable
  is used linearly on every field). Defer with the naming cleanup.
