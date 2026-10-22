# G10-C frozen targets (frozen 2026-10-13 before any proof attempt)

Source: INFORMATION_LIMIT_THEOREMS.md Theorem III construction (sha256 775b7d15...), C04 quintic
(CutoffExtrema.lean sha256 ab2f98d2...). See SOURCE_RECOVERY.md. Lean file:
`lean/G10CSmoothCutoff.lean`, namespace `G10C`, toolchain Lean 4.31.0 + mathlib fabf563a.

## Definitions (faithful to source)

- `F t = 1 - 10 t^3 + 15 t^4 - 6 t^5`, `Fp t = -30 t^2 (1-t)^2`, `Fpp t = -60 t (1-t)(1-2t)`
  (verbatim C04).
- `clamp01 t = max 0 (min t 1)`, `G t = F (clamp01 t)`  (= 1 for t<=0, F on [0,1], 0 for t>=1).
- `q0 a r = G (2*r/a - 1/2)` : the source's C^2 cutoff on all of R
  (1 for r<=a/4, F(2r/a-1/2) on [a/4,3a/4], 0 afterwards).
- `qe a r = q0 a r * q0 a (-r)` : even, compactly supported version; equals `q0 a` on
  `[-a/4, inf)` (so on the whole radial domain r>=0).
- `IsMollifier a rho := ContDiff R (top : N∞) rho ∧ (∀ t, 0 <= rho t) ∧ ∫ rho = 1 ∧
  (∀ t, rho t ≠ 0 → |t| <= a/8)`  ("any nonnegative unit-integral C^inf mollifier supported in
  [-a/8,a/8]").
- `smoothCutoff a rho = rho ⋆[mul R R, volume] qe a`.

All theorems below assume `0 < a` (source: radial cutout a>0); M1/M2/M4/M5 additionally assume
`IsMollifier a rho` for an arbitrary rho (source: "any" mollifier), and M0 gives existence.

## Targets

- **M0** `exists_mollifier : ∃ rho, IsMollifier a rho`.
- **M1** for every mollifier rho, with `q := smoothCutoff a rho`:
  `ContDiff R (top : N∞) q`; `∀ r, 0 <= q r ∧ q r <= 1`; `|r| <= a/8 → q r = 1`;
  `7*a/8 <= |r| → q r = 0`.
- **M2** (the source's "same derivative bounds", exact constants, no delta loss):
  `∀ r, |deriv q r| <= 15/(4*a)` and `∀ r, |deriv (deriv q) r| <= 40/(sqrt 3 * a^2)`.
  Fallback rule (frozen): if the exact constants could not be met, only `bound + delta` for
  every delta>0 would be claimed and recorded; not expected, since convolution with a
  probability density does not increase sup norms.
- **M3** quintic regularity stated correctly:
  `q0` piecewise identities (=1 on r<=a/4, =F(2r/a-1/2) on [a/4,3a/4], =0 on r>=3a/4);
  `0 <= q0 <= 1`; `ContDiff R 2 (q0 a)`; `¬ ContDiff R 3 (q0 a)`; hence
  `¬ ContDiff R (top : N∞) (q0 a)` (the finite quintic cutoff is NOT C^inf);
  source bounds `|deriv (q0 a) r| <= 15/(4a)`, `|deriv (deriv (q0 a)) r| <= 40/(sqrt3 a^2)`.
- **M4** relation quintic ↔ smooth cutoff (as the source intends: q = rho * q0):
  for `-a/8 <= r` the source's literal convolution `rho ⋆ q0 a` exists at r and equals
  `smoothCutoff a rho r` (in particular on the whole radial domain r >= 0). Also
  `qe a r = q0 a r` for `-a/4 <= r`.
- **M5** smooth radial extension: for any real inner product space E,
  `X x := smoothCutoff a rho ‖x‖` satisfies `ContDiff R (top : N∞) X`, `0 <= X <= 1`,
  `‖x‖ <= a/8 → X x = 1`, `7a/8 <= ‖x‖ → X x = 0`, and for `‖n‖ = 1`, `0 <= r`:
  `X (r • n) = smoothCutoff a rho r` (ray restriction, which carries the M2 bounds along rays).
- **MAIN** `g10c_main`: packages M0+M1+M2+M4+M5 as an existential over the cutoff chi.

## Not claimed
The I13/I14 chain, the rational margin 1147/1152<1 (C04, unchanged), the exp/sqrt auxiliary
inputs, any information/identifiability consequence, two-point probability bounds, any
scientific admission.
