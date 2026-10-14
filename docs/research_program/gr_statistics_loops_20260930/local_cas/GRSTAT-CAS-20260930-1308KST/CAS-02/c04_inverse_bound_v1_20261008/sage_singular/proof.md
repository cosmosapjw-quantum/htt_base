# CAS-02-C04 Sage/Singular finite certificate

## Physics/math audit verdict

The stated finite inverse bound follows for the admitted real matrices and future unit vectors in one fixed orthonormal observer frame. This is a component result only; global extension, projection, statistics, and physical admission remain outside the contract.

## Assumptions and conventions

The frame metric is `diag(-1,1,1,1)`. All inequalities use positive Euclidean vector, Frobenius matrix, and induced spectral norms. The matrices `S_j` are real symmetric and use the tracefree optical embedding from `COMMON_SPEC.md`. The vectors are `u_j=(sqrt(1+||d_j||²),d_j)` with the positive root and `||d_j||≤sinh R`. There is at least one admitted pair. Thus `0≤||d_j||≤sinh R` implies `R≥0`; this is a deduction, not an extra assumption. The units of `S`, `B`, `epsilonH`, and `L` agree; `M` and `epsilonZ` are dimensionless.

## Equation and definition audit

Write `D=S₂-S₁`, `e=u₂-u₁`, and `q_j=u_jᵀ S_j u_j`. Symmetry gives both exact polynomial identities:

`q₂-q₁ = u₂ᵀ D u₂ + eᵀ S₁(u₂+u₁)`;

`q₂-q₁ = u₁ᵀ D u₁ + eᵀ S₂(u₂+u₁)`.

Sage and Singular independently reduce both unrestricted polynomial differences to zero. Their four-component Lagrange identity is an exact sum-of-squares certificate for Euclidean Cauchy–Schwarz. The symmetric spectral theorem gives `|vᵀSw|≤||S||op ||v||₂ ||w||₂`; this norm theorem is used as an analytic inequality, while the CAS verifies the polynomial identities it acts on.

For `||S₁||op≤||S₂||op`, use the first identity, so its anchored norm is `L=||S₁||op`. For `||S₂||op<||S₁||op`, use the second identity, so `L=||S₂||op`. These two cases exhaust the real order, including equality in the first case. Hence in either case

`|q₂-q₁| ≤ ||D||F max(||u₁||₂²,||u₂||₂²) + L ||e||₂ (||u₁||₂+||u₂||₂)`.

The chart identity `||u_j||₂²=1+2||d_j||₂²` is certified in Sage modulo `u_j⁰²=1+||d_j||₂²`. Since `R≥0`, `||u_j||₂²≤1+2sinh²R=cosh(2R)=M²`; the chosen positive root yields `||u_j||₂≤M`. Therefore `|q₂-q₁|≤M² epsilonH+2ML epsilonZ`.

The fixed metric has `||g||F=2`. From `B_j=S_j+q_j g`, the Frobenius triangle inequality yields

`||B₂-B₁||F≤epsilonH+2|q₂-q₁|≤(1+2M²)epsilonH+4ML epsilonZ`.

## Dimensional/sign/limit checks

Sage verifies the optical embedding identity `epsilonH²=delta h0²+||delta h1||²/2+||delta h2||F²` with symmetric tracefree `delta h2`. It also verifies `g(u,u)=-1` under the chart relation. At `R=0`, both `d_j=0`; the result remains valid. At `epsilonH=0` or `epsilonZ=0`, the same identities apply without division. Either matrix can realize `L`, including a tie. The positive root is used only to select the future branch; the polynomial certificates are valid before that branch restriction.

## Claim-tier implications and fatal blockers

There is no finite algebra blocker under the frozen assumptions. This axis result is not a four-axis aggregate or a scientific admission. The contract's excluded global, statistical, and observational claims remain `HOLD`.

## Required tests or artifacts

`run.py` emits exactly one JSON document with `checks.CAS-02-C04`, `domain_assumption_diff`, and `counterexample`. It invokes the Sage-bundled Singular 4.4.1 executable on `certificate.sing`; raw stdout/stderr and version logs are retained in this axis directory. `axis_result.json` and `check_axis.json` bind the result to the frozen contract hash.
