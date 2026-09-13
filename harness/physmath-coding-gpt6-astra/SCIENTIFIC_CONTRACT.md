# SCIENTIFIC_CONTRACT.md

이 파일은 프로젝트 값으로 채우는 템플릿이다. 빈 항목은 검증된 사실이 아니다. 비해당 항목은 이유와 함께 명시한다.

## Objective, motivation, authority

- original scientific motivation / novelty to preserve:
- measurable objective / observable:
- current bounded objective and acceptance:
- authority / SSOT and who selected it:
- exact source/data identity, semantic relationship:
- existing user authorization / protected boundaries:
- baseline claim ceiling:

## Definitions and derivation trace

| Quantity / claim | Definition / equation | Derivation / assumptions | Computational form | Implementation | Validation evidence |
|---|---|---|---|---|---|
| | | | | | |

## Conventions and regimes

- metric signature: (-,+,+,+) if project has no prior specified convention
- units: retain c, ħ, k_B unless natural units are explicitly selected
- indices / Fourier / signs / normalization / gauge:
- governing equations and closure:
- approximation and perturbative order:
- boundary / initial conditions:
- parameter, resolution and precision ranges:
- excluded singular or uncontrolled regimes:
- statistical model / likelihood / identifiability / uncertainty:

## Invariants and known limits

| Invariant / limit | Expected result | Error norm / tolerance | Independent reference | Regime | Test |
|---|---|---|---|---|---|
| | | | | | |

Use relevant dimensions, symmetry/covariance, conservation, positivity/realizability, exact identities and known limits. Do not relax tolerance because a candidate fails.

## Reference independence

- analytic toy / exact arithmetic reference:
- independently derived or implemented oracle:
- shared code, input, coefficients, interpolation or projection paths:
- published benchmark and source verification status:
- previous implementation and known limitations:

Agreement with the same implementation under a second wrapper is not independent validation.

## Numerical acceptance

- precision / error budget split: discretization, iteration, roundoff, sampling
- grid/timestep/precision convergence and expected scaling:
- conditioning / stiffness / solver sensitivity:
- derivative/JVP direction, independent oracle, step-size sweep and primal semantics:
- seed policy, ensemble size and statistical uncertainty:
- actual execution/time/memory budget and authorized retry limits:

## Failure semantics and claims

NaN/Inf, empty output, non-convergence, invalid clipping, missing data substitution and fallback outside its regime are explicit failures. Classify theory/math, statistics, numerics, implementation, runtime, permission and evidence-authority failures separately. Retain the first failure and repairs. Give actual process exit and evaluated/not-evaluated TestIDs.

Use explicit evidence status: established, literature-supported, derived, numerically checked, implementation-verified, conjectural, unresolved, blocked. Package structure or self-hash agreement proves neither scientific truth nor authority.

## Change control

Protected conventions, physical/output semantics, approximation/closure, baseline, tolerance and SSOT cannot change beyond existing user authorization. In-scope evidence-driven correction and phase transition do not require repeated permission. Escalate only the concrete new boundary that the current authorization does not cover.
