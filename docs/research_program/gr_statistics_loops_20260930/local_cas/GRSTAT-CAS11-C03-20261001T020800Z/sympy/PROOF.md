# CAS11-C03 weighted projection: SymPy axis

## Scope and conventions

Let `E` be a real vector space of any finite dimension `n >= 0`, with symmetric positive-definite bilinear form `W`; `⟨x,y⟩_W = xᵀWy`. Let `V <= E` have dimension `k`, `0 <= k <= n`. A basis of `V` gives an `n × k` matrix `B` with independent columns. For `k > 0`, `G=BᵀWB` is positive definite: `cᵀGc=⟨Bc,Bc⟩_W>0` for nonzero `c`. Thus `G` is invertible. Define `P=BG⁻¹BᵀW`. For `k=0`, define `P=0`; no inverse of an empty matrix is needed. This is the unique `W`-orthogonal projection onto `V`, independent of the chosen basis. In the zero-dimensional ambient space all maps and sums are empty and the claims hold vacuously. No Lorentz metric is used in this component.

## Universal proof

For `k>0`, `PB=B G⁻¹ G=B`, so `P` is the identity on `V`. Every `Px` lies in `V`, hence `P²x=Px` for every `x`. Also `BᵀW(I-P)x=BᵀWx-GG⁻¹BᵀWx=0`. Every `v∈V` equals `Bc`, hence `⟨v,(I-P)x⟩_W=cᵀBᵀW(I-P)x=0`. For `k=0`, `P=0`, `V={0}`, and both identities follow directly. For `k=n`, `V=E`, hence `P=I`, and every residual vanishes. A basis change `B'=BS` with invertible `S` gives `G'=SᵀGS` and `B'(G')⁻¹B'ᵀW=P`. These are identities for any allowed dimensions and positive-definite `W`, not finite-size experimental extrapolations.

For any finite family `K_1,…,K_m`, including `m=0`, put `r_i=(I-P)K_i`, `R_ij=⟨r_i,r_j⟩_W`. Bilinearity gives, for every `a∈ℝ^m`, `aᵀRa=Σ_ij a_i a_j⟨r_i,r_j⟩_W=⟨Σ_i a_i r_i, Σ_j a_j r_j⟩_W=||Σ_i a_i r_i||²_W≥0`. For `m=0`, both sides are zero. Positive definiteness of `W` supplies the final nonnegativity. `R` is only positive semidefinite: zero and dependent residuals permit singular `R`. No residual independence or inverse of `R` is assumed.

For all `x,y∈E`, write `X=⟨x,x⟩_W`, `Y=⟨y,y⟩_W`, `C=⟨x,y⟩_W`. If `Y=0`, positive definiteness implies `y=0` and `C=0`, so `C²≤XY` is equality. If `Y>0`, the one-dimensional `W`-projection of `x` onto `span{y}` has residual `z=x-(C/Y)y`. Its norm identity is `||z||²_W=X-C²/Y≥0`, whence `C²≤XY`. Equality iff `z=0`, equivalently `x` and `y` are linearly dependent in this branch. The `y=0` branch also gives equality. This includes `x=0` and `n=0` without division by zero. Since the real form is symmetric, `|C|²=C²`.

An independent sum-of-squares version follows by choosing any invertible `L` with `W=LᵀL` (positive-definite Cholesky), and `u=Lx`, `v=Ly`. Expansion and swapping dummy indices give `XY-C² = (1/2) Σ_{i,j}(u_i v_j-u_j v_i)² = Σ_{i<j}(u_i v_j-u_j v_i)² ≥0`. For `n=0` or `1`, the pair sum is empty and zero. This identity has no norm division, so it includes zero vectors. Equality means every `2×2` minor vanishes, equivalently dependence when at least one vector is nonzero. The proof only uses finite sums, real scalars, and positive definiteness.

## Executed symbolic obligations and boundary

`run_axis.py` uses SymPy to verify the scalar identities from which the universal algebraic steps follow: inverse cancellation in the Gram coordinate, the residual Gram coefficient expansion, the one-dimensional projection norm, and the two-index Lagrange square identity. The program also checks exact matrices in edge configurations and high-precision numeric examples as supplemental falsifiers. The arbitrary-dimension conclusion rests on the indexed algebra above; small matrices alone do not certify it. The script returns an inconclusive nonzero outcome if any symbolic identity or supplemental check fails. Its JSON `checks` field is true only after all implemented checks complete, alongside this explicit universal derivation.

The contract's separate measure-space null classes and integrability, physical residual construction and error bounds, observational covariance, catalogue fitting, and scientific admission remain open/out of scope.
