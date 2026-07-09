# Preregistered analysis protocol template for a closed HTT observational lane

## 1. Lane identity

- Lane name: K1 low-ell / K5 CF4 depth-flow / DESI directional-response / other
- Scientific estimand: signed comparator interval / scalar statistic / BiPoSH statistic / depth-gap interval / e-value curve
- Explicit non-claims: no family assignment; no posterior unless HTT likelihood manifest exists; no native solver result unless transfer contract is satisfied

## 2. Data products and hashes

| product | version | source | local path | sha256 | license/usage note |
|---|---|---|---|---|---|
| | | | | | |

## 3. Observable vector and response map

- Define y:
- Define covariance C_y:
- Define whitening L:
- Define response R in registered g basis:
- Numerical rank of LR:
- Null columns:
- Nuisance projection:

## 4. Null/covariance policy

- Known covariance / estimated covariance / bootstrap / jackknife / simulation ensemble:
- If estimated covariance: p, Nsim, Hartlap factor, Sellentin-Heavens option:
- Null simulations or random catalogs:
- Finite-cover or multiple-threshold policy:
- e-value construction if used:

## 5. Identified-set and status policy

- Physical cone:
- MES/full-covariance ceilings:
- Missing sectors:
- EMPTY condition:
- UNBOUNDED condition:
- CEILING-UNFIT condition:
- Endpoint CI method:

## 6. Blinding and selection/mask policy

- Blinding rule:
- Mask choices and variations:
- Selection weights:
- Data-random/random-random estimator if survey data:
- Map-product or catalog-product stability check:

## 7. Acceptance gates before interpretation

- [ ] Reproducible script path and hashes present
- [ ] Rank/null certificate saved
- [ ] Covariance policy saved
- [ ] Null calibration passes
- [ ] Sensitivity table passes
- [ ] Captions do not overclaim posterior/evidence/geometry

## 8. Output contract

- Required tables:
- Required figures:
- Sidecar fields:
- Conditions under which result is withheld:

