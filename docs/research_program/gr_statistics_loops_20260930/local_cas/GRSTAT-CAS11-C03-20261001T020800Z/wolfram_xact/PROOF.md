# CAS11-C03 weighted projection: arbitrary finite dimensions

The contracted field is real. Let `E` have dimension `n >= 0` and a positive-definite symmetric bilinear form `W`; write `⟨x,y⟩_W` and `||x||²_W=⟨x,x⟩_W`. Let `V` be any subspace of dimension `m`, `0 <= m <= n`. The empty basis is permitted. No Lorentz metric from other contract components is used here. These are mathematical statements about finite vector spaces; they establish no physical residual construction or statistical inference.

## Orthogonal projector

Choose a basis `b_1,...,b_m` of `V` and let `B:R^m→E` be its synthesis map. For `m>0`, `G=Bᵀ W B` is positive definite: for nonzero `c`, `cᵀGc=||Bc||²_W>0`, since basis independence makes `Bc≠0`. Thus `G` is invertible. Define `P=B G⁻¹ Bᵀ W`. For `m=0`, define `P=0`; the empty map and sums make all following identities valid. This uses the same `W` in the Gram matrix and projection.

For any `c`, `P(Bc)=B G⁻¹ Gc=Bc`. Also `Px∈V` for every `x`. Hence `P²x=P(Px)=Px` for every `x`. For `v=Bc`, `⟨v,(I-P)x⟩_W=cᵀ(BᵀWx-GG⁻¹BᵀWx)=0`. These are universal vector identities. Equivalently, a `W`-orthonormal basis adapted to `V` makes `P` diagonal with `m` ones and `n-m` zeroes; the engine checks the corresponding coordinate identities `p²=p` and `p(1-p)=0`. If `V=0`, `P=0`; if `V=E`, `P=I` (also when `n=0`); zero vectors cause no exception.

## Residual Gram matrix

For any finite family `K_1,...,K_f` with `f>=0`, set `r_i=(I-P)K_i` and `R_ij=⟨r_i,r_j⟩_W`. Symmetry of `W` makes `R` symmetric. For every real `a∈R^f`, finite bilinearity gives

`aᵀRa = Σ_i Σ_j a_i a_j ⟨r_i,r_j⟩_W = ⟨Σ_i a_i r_i, Σ_j a_j r_j⟩_W = ||Σ_i a_i r_i||²_W >= 0`.

The final inequality follows from positive definiteness of `W`; it says `R` is positive *semidefinite*. Equality holds exactly when `Σ_i a_i r_i=0`, so dependent or zero residuals legitimately make `R` singular. For `f=0`, the unique coefficient vector and empty sum give `0=||0||²_W`. The engine expands a representative all-indeterminate finite polynomial to check the distributive algebra; the preceding argument supplies the arbitrary-family quantifier. Neither the engine nor the proof assumes `R⁻¹`.

## Cauchy–Schwarz by a square certificate

For arbitrary `x,y∈E`, put `q=||y||²_W`, `s=⟨x,y⟩_W`, and `t=||x||²_W`. If `q=0`, positive definiteness gives `y=0`, hence `s=0` and `s²<=tq=0` with equality. If `q>0`, define `z=x-(s/q)y`. Bilinearity and symmetry give `||z||²_W=t-s²/q>=0`; multiplying by `q>0` gives `s²<=tq`. The engine checks the exact scalar polynomial `q||z||²_W=qt-s²`. Equality for `q>0` holds exactly when `z=0`, namely `x=(s/q)y`. This also covers `x=0` and all zero-dimensional cases. Over the real field, `|s|²=s²`.

## Scope of engine certificate

`weighted_projection.wl` loads xAct xTensor and checks contraction symmetry for symbolic vectors and a symmetric metric. Wolfram checks the projector's per-coordinate identities, a finite all-indeterminate Gram distributivity polynomial, and the scalar square identity under `q>0`; it also executes empty-family and dependent-residual controls. The engine checks do not prove existence of a `W`-orthonormal adapted frame, positivity of arbitrary `W`, or unbounded-size summation by themselves. Those universal steps are proved above from finite-dimensional linear algebra and the explicit positive-definiteness assumption. The xAct 3-dimensional tensor check is an algebraic symmetry check, not a restriction of the theorem to dimension three.

The result is limited to the finite deterministic Gram component. Measure-space null equivalence and integrability, continuum limits, physical residual bounds, observational covariance, catalogue fitting, and the parent CAS-11 theorem remain open. Claim tier: finite mathematical component only; no scientific admission.
