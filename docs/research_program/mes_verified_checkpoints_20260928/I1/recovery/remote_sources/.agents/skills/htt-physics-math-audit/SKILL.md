---
name: htt-physics-math-audit
summary: Audit HTT/BASS/MIO physics and mathematical claims before they drive code or manuscript changes.
description: Use for GR/cosmology/statistical mechanics/kinetic-theory derivations, MES bounds, transfer functions, Bianchi/tilt variables, local/global anisotropy claims, units, signs, limits, and convention-sensitive equations in this repo.
---

# HTT Physics / Math Audit Skill

## Purpose

Prevent mathematically elegant but over-interpreted physics claims from entering code, reports, or paper text. This is a project-specific version of the generic physics audit skill, adapted to the current HTT/MIO/BASS/obsstat stack.

## Project conventions

- Metric signature: `(-,+,+,+)`.
- Keep `c`, `G`, `hbar`, `k_B` explicit unless a local module explicitly declares natural units.
- Distinguish normal-frame, electron-frame, matter-frame, CMB-frame, and local observer boost frame.
- Distinguish local peculiar velocity / local boost from global matter-frame tilt and from Bianchi/background geometry.
- Treat Teff/TSC as legacy/scope-audit material unless the PR explicitly touches legacy reproduction.

## Required audit steps

1. State the controlling assumptions.
2. State conventions: signature, units, tetrad/frame, harmonic/BiPoSH normalization, redshift/depth convention, metric/background convention.
3. Check dimensions and normalizations.
4. Check signs, especially in `x_C = Sigma^2 - W^2 + Omega_tilt + Omega_k_aniso` and in any vorticity/curvature term.
5. Check limits: FLRW, no-tilt, local-boost-only, global-tilt-only, isotropic covariance, zero denominator, rank-deficient response.
6. Separate proof, derivation, specification, numerical validation, and speculation.
7. Check whether a scalar statistic is being promoted to a geometry/family claim.
8. Check whether deterministic template effects and anisotropic covariance effects have been conflated.
9. Emit a claim-tier recommendation.

## HTT-specific red flags

- `x_C` described as an invariant anisotropy magnitude rather than a signed comparator coordinate.
- `Q` and `F` used interchangeably.
- `Pi(q)` described as truth probability rather than threshold exceedance.
- `G_F` described as global tilt evidence without local/systematic null calibration.
- BiPoSH/off-diagonal covariance described as sufficient for Bianchi geometry.
- AniCLASS/external transfer results described as native BASS transfer.
- Family identification claimed without native low-ell `a_lm`/template/BiPoSH/covariance atlas and equivalence-class breaking.

## Required output

```markdown
## Physics/math audit verdict

## Assumptions and conventions

## Equation and definition audit
| Item | Status | Issue | Required fix |
|---|---:|---|---|

## Dimensional/sign/limit checks

## Claim-tier implications

## Fatal blockers

## Safe claims

## Required tests or artifacts
```

## Hard prohibitions

- Do not call a result derived unless the assumptions and derivation are present.
- Do not infer Bianchi geometry from scalar summaries alone.
- Do not treat a transfer-policy-dependent result as transfer-independent physics.
- Do not let Teff/TSC legacy scope language revive as an active full solver claim.
