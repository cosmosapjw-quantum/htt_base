# CAS-07 M05: determinant and distance bridge (Wolfram+xTensor axis)

## Physics/math audit verdict

The four contracted M05 statements follow by exact algebra and application of the admitted M01, M04, and C02 statements. This is a dependency composition on the stated domain. It does not re-prove those dependencies, the later `t` refinement, the parent CAS-07 theorem, or a physical/observational claim.

## Assumptions and conventions

Let `K>=0`, `L>0`, `0<s<=L`, and `eta_K(L)<1`. The admitted M04 Jacobi premises are retained unchanged. The screen is Euclidean `R^2`; `D(s)` is an arbitrary real linear map, and `||.||op` is the induced Euclidean operator norm. In particular no symmetry, normality, diagonalizability, positive definiteness, or commutation property is assumed. The metric signature in `COMMON_SPEC.md` is `(-,+,+,+)`; this component works on its positive Euclidean screen. Units: `[K]=L^-2`, `[s]=[f_K]=[d_A]=L`, `[eta_K]=1`, `[det D]=L^2`.

The accepted dependency statements, copied literally from `ADMITTED_INPUTS.json`, are:

> M01: Under K>=0, 0<s<=L and eta_K(L)<1, 0<=eta_K(s)<=eta_K(L)<1.

> M04: For the admitted Jacobi system, ||D(s)-s Id||op<=f_K(s)-s.

> C02: For arbitrary real 2x2 D, s>0, 0<=eta<1 and ||D-s Id||op<=s eta, both singular values lie in [s(1-eta),s(1+eta)], det(D)>0, and the positive sqrt(det(D)) lies in the same interval.

## Equation and definition audit

| Item | Status | Exact argument |
|---|---|---|
| `f_K(s)-s=s eta_K(s)` | PASS | Since `s>0`, `s(f_K(s)/s-1)=f_K(s)-s` on both `K=0` and `K>0` branches. |
| C02 norm premise | PASS | M01 gives `0<=eta_K(s)<1`; M04 and the equality above give `||D(s)-s Id||op<=s eta_K(s)`. |
| Determinant sign | PASS by admitted C02 | Apply C02 to this `D(s)`, `s`, and `eta_K(s)`. Its arbitrary-real-2x2 hypothesis covers nonsymmetric `D`. This yields `det(D(s))>0`; positivity was not a premise. |
| Distance bound | PASS by admitted C02 | Only after the sign is known, set `d_A(s)=sqrt(det(D(s)))` on the positive real branch. C02 yields `s(1-eta_K(s))<=d_A(s)<=s(1+eta_K(s))`. |

The Wolfram script checks the positive-`K` and zero-`K` algebra exactly, checks the scalar implication needed for the C02 premise using real quantifier elimination, and checks the composition of the accepted C02 consequent with that premise. It declares a 2D xTensor screen and contracts `delta^a_b delta^b_a=2`. It keeps a symbolic matrix with independent off-diagonal entries and obtains `det D=d11*d22-d12*d21`; the determinant sign is **not** inferred from this polynomial without C02. The script's composition checks encode the admitted C02 theorem as an implication, so their status must be read together with the accepted dependency statements above.

## Dimensional/sign/limit checks

At `K=0`, `f_0(s)=s` and `eta_0(s)=0`. M04 then gives `||D(s)-s Id||op<=0`, hence `D(s)=s Id`. In two dimensions, `det D=s^2>0` because `s>0`, and the positive square root is `d_A=s`. The script checks the determinant and positive branch exactly. At `eta_K(s)=0` the same conclusion follows. Values approaching `eta=1` from below keep the lower bound positive, but the target excludes `eta=1` and makes no caustic claim there. The vertex `s=0` is outside this determinant target.

## Claim-tier implications

This is a contracted analytic component result only, conditional on the accepted M01/M04/C02 dependencies and M04's Jacobi premises. Scientific admission remains `HOLD`. It does not identify a Bianchi family or validate a native transfer result.

## Fatal blockers

None for the exact M05 dependency composition if the frozen inputs and admitted dependency status remain valid. Runtime launch provenance is reported separately in `result.json`; it is not inferred from a local tool invocation.

## Safe claims

On the declared domain, the exact M05 determinant sign and distance bound follow from the admitted dependencies. The full CAS-07 theorem and any physical or observational conclusion remain outside this axis.

## Required tests or artifacts

Run `python3 -B .../wolfram_xact/run.py` from the repository root. The source, raw Wolfram stdout/stderr, exact boolean checks, hashes, and tool versions are retained in this unique result directory.
