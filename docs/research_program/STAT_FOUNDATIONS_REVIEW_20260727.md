# Statistical Foundations of the Graded FLRW-Departure Programme

Document id: `STAT-FOUND-v1`  
Date: 2026-07-27  
Audited target: `053baee` (`research/pr04-multicomponent`)  
Claim posture: pre-solver methodology and executable contract.

Nothing in this document is a detection, a Bianchi-family identification, a
geometry measurement, or a native-solver validation.

## 1. Root diagnosis

The legacy scalar

```text
x_C = Sigma2 - W2 + Omega_tilt + DeltaOmega_k
```

has been asked to represent three inequivalent objects:

1. an exact signed Gauss/Friedmann budget coordinate;
2. a non-negative distance or occupancy;
3. a statistically identified estimand.

Only the first role is valid without additional structure.  The budget sign is
forced by the constraint, so cancellation is real in that projection.
Conversely, a distance must vanish only at the reference state, and an
estimand must be identified by the registered response.  A scalar combining
reachable and null sectors satisfies neither requirement.

The programme therefore preserves `x_C` exactly as a signed legacy projection
and replaces its other uses with typed state, anchor-stress, identified-set,
orbit and model-discrepancy objects.

## 2. Foundations

### D1 — state and reference

The comparator state is

```text
g = (Sigma2, W2, Omega_tilt, DeltaOmega_k)
```

over three non-negative sectors and one signed curvature coordinate.  Its
irreducible refinement is

```text
u = (sigma_ab[5], omega_a[3], beta_a[3], DeltaOmega_k[1]).
```

`g = 0` is necessary but not sufficient for FLRW.  Inhomogeneous degrees of
freedom and the regularity hypotheses required by an almost-EGS converse are
outside this comparator.

### D2 — typed anchors

An anchor is not a float.  It is the tuple

```text
(value; invariant, frame, congruence, normalization, order, branch,
 attribution, conditioning, validity domain, source equations,
 shared nuisance)
```

`REALIZATION_CONDITIONAL` and `ENSEMBLE_CALIBRATED` anchors are distinct.
Anchors derived from the same low-multipole realization as a numerator are
joint random objects, not fixed denominators.

### D3 — ratio well-posedness

`s_X = X/X_max` exists only when numerator and denominator refer to the same
invariant, frame, congruence, normalization, order and branch.  Missing anchors
and mismatched channels yield typed statuses, not NaN, infinity or zero.

### D4 — partial saturation

Only registered sectors may have saturation coordinates.  The geodesic MES
authority provides typed shear and vorticity anchors.  It provides no
four-acceleration ceiling, and MES provides no anisotropic-curvature ceiling.
Those sectors are represented by partial identification.

### One-way logic

For a registered linear premise `H_lin`,

```text
H_lin => s_X <= 1.
```

A controlled exceedance can falsify that registered linear consistency
premise.  A value below one supports no converse.  The evidence-bearing
quantity is the excess `E_X=max(s_X-1,0)`, routed through the existing
anytime-valid e-value machinery.

## 3. Anchor disposition

- `MES_G_SIGMA`: verified geodesic, uncorrected expression is active.
- `MES_G_OMEGA`: verified geodesic expression is active.
- `MES_G_ACCEL`: structural absence; status `NO_MES_ANCHOR`.
- anisotropic curvature: status `NO_MES_ANCHOR`.
- the `1 + 2.69 eps1` shear correction is
  `WITHHELD_DERIVATION_MISMATCH`.
- its historical ceiling, including the `6.4656e-6`-class value, is
  reproduction-only.
- `9.25e-6` is a historical S2a/CatWISE shear ceiling, never a combined
  denominator.
- non-geodesic vorticity and acceleration triples that cannot be reconstructed
  from accessible authority are legacy-reproduction data only.

No coefficient is rederived or newly activated in this change-set.  Any
attempt to reactivate the withheld correction requires a new four-axis CAS
contract.

## 4. Identification, priors and covariance

- A joint feasible set and support function are the native inferential output.
- Structural and leading-order nulls remain distinct.
- A ratio is finite only when its denominator identified interval is separated
  from zero under caller-declared `atol` and `rtol`.
- Otherwise the result is `RATIO_UNIDENTIFIED`, with an unbounded/Fieller-type
  set where appropriate.
- Physical priors live on identified base coordinates; saturation is a
  pushforward report.
- A one-centred empirical-Bayes prior is conditional and requires disjoint or
  cross-fitted selection and estimation data.
- A null-sector posterior is its prior in that direction and cannot be reported
  as data evidence.
- Claim-bearing multicomponent inference requires joint covariance.  Missing
  cross-block covariance never silently becomes zero.
- Estimated covariance uses a covariance-marginalized multivariate t under its
  registered Gaussian/Wishart assumptions.  Hartlap remains a diagnostic
  comparator.
- Singular covariance is evaluated on its supported quotient and reports the
  null residual separately.

## 5. Orbit and model discrepancy

Inference is equivariant and reporting is invariant.  O(3), including parity,
is part of the type.  The production rank is `rank(R)` for the actual
transfer, mask and covariance; no constant rank is inferred from dimensions.

The preregistered invariant catalogue includes

```text
tr(sigma^2), tr(sigma^3), beta^2,
beta.sigma.beta, beta.sigma^2.beta,
det[beta, sigma beta, sigma^2 beta].
```

The final quantity is parity-odd.  Catalogue-wide testing carries multiplicity
and an alignment-null contract.

Nonlinearity is reported through tangent/perpendicular residuals or distance to
an explicit candidate manifold.  A nonlinear candidate is only distinguished
after held-out or matched-injection comparison against linear, systematics,
frame-mismatch and derivative-failure alternatives.  Otherwise the result is
`UNATTRIBUTED_OFF_MANIFOLD`.

## 6. Backward-compatibility theorems

`BC1_LEGACY_PROJECTION`: `x_C` is the pushforward
`<(+1,-1,+1,+1), g>`.  Existing numeric `x_C` artifacts remain valid as this
marginal and are not regenerated by the refoundation.

`BC2_NO_REPRESENTATION_PROMOTION`: refining scalar to vector, tensor or orbit
space cannot promote a claim without new identifying data or channels.

Legacy `Q`, `F`, signed `F_C`, `Pi` and `G_F` values may be reproduced, but
their allowed use is explicitly typed.  `Pi` is exceedance, not truth
probability; `G_F` requires bin and null-calibration metadata.

## 7. Finding ledger

| ID | Finding | Required disposition |
|---|---|---|
| F1 | `eps_ell` applies a `C_l` formula directly to `D_l` | convert `D_l` to `C_l`; retain explicit legacy helper |
| F2 | `9.25e-6` is mislabeled combined and reused across sectors | type as S2a shear-only; remove scalar sector filling |
| F3 | refuted non-geodesic triples remain active-looking | remove from active authority; legacy reproduction only |
| F4 | PSD cone imports reciprocal-wrong shear lower bound | route through PR-128 coefficient authority |
| F5 | structural and leading-order nulls are flattened | preserve typed null kind |
| F6 | toy box widths are called MES ceilings | rename `SYNTHETIC_SUPPORT_BOUND` |
| F7 | duplicate Imbens-Manski critical-value conventions | one common implementation |
| F8 | `W2/V2` rename and `W_N2` collision remain | canonical `W2`, typed aliases only |
| F9 | `F`, signed `F_C` and `Q` reporting conflict | one typed legacy projection report |
| F10 | scenario dipoles are mis-keyed as `eps2/eps3` | rename to explicit `*_eps1` scenario fields |
| F11 | `2.69 eps1` derivation chain disagrees numerically | quarantine; no active correction |
| F12 | anchor conditioning and correlation are untyped | joint random-anchor contract |

The previously alleged `t/(2+t)` versus `t/(1+t)` conflict is withdrawn.  The
two expressions use distinct registered tilt normalizations and remain
regression-protected without reopening their derivation.

## 8. Claim ceiling

The implementation may produce conditional methodology, diagnostics,
identified sets and falsification instruments.  It may not produce a native
solver result, geometry detection, Bianchi-family identification, MIO
posterior, or model-independent truth certificate.

