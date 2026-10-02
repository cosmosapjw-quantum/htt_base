# CAS-01 SageMath and Singular finite component certificate

Inputs: `EXECUTION_CONTRACT.json` (SHA-256 `edc2df3348528a699b987ae1893ab76630e96b9915d11117db7916d005c406f1`) and `COMMON_SPEC.md` (SHA-256 `4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897`). The proof uses no other mathematical source or sibling result. `run.py` constructs the polynomials independently; `SINGULAR_TRANSCRIPT.json` records every direct Singular command and response. Singular reduces the actual target polynomials, including the generic tensor identities and both directions of the null-cone kernel ideal, rather than merely reducing a generator of its own ideal.

## Domain and algebra

The signature is `(-,+,+,+)`, `u^T g u=-1`, `u^0>0`, and `c>0`. The quotient ideal includes `u^T g u+1` and `c*z-1`, with `z` an inverse witness. Thus division by `c` is used only on the nonzero locus; the positive sign of `c` and the future inequality are retained as real-domain conditions. No denominator is cleared outside that locus. The algebraic identities are valid on both unit timelike sheets, hence in particular the stipulated future sheet. The positive square-root branch used in C04 has value `+1` at the vertex. All products use covariant `S,B,Q,W` and contravariant `u`; `u_flat=g u`.

Let `P=I+u u_flat^T`, `B=S+(u^T S u)g`, `b=B u`, `W=P^T T P` for an arbitrary skew `T`, and `Q=B+b u_flat^T-u_flat b^T+W`. On the unit shell, `P u=0`, `P^2=P`, and `P^T W P=W`. Every spatial skew `W` is represented by the choice `T=W`, so the parameterization does not restrict the universal target.

## C01

`u^T B u=(u^T S u)(1+u^T g u)=0`. For `S'=S+a g`, its scalar contraction changes by `-a`, so `B'=S+a g+(u^T S u-a)g=B`. Sage and Singular reduce these generic polynomials modulo the unit-shell ideal.

For an independently generic symmetric form `M`, set `F(n)=(-1,n)^T M(-1,n)` and reduce it modulo `n_1^2+n_2^2+n_3^2-1`. The nine coefficient constraints of that remainder generate precisely `M_0i=0`, `M_ij=0` for `i<j`, and `M_ii+M_00=0`. The script computes both ideal containments in Sage and Singular. Necessity over the **real** sphere follows without a density assumption: comparing `F(n)` and `F(-n)` at each coordinate axis gives `M_0i=0`; evaluation at each axis then gives `M_ii=-M_00`; evaluation at `(e_i+e_j)/sqrt(2)` gives `M_ij=0`. Conversely, these conditions make `M=(-M_00)g`, whose null-cone contraction vanishes. No kernel conclusion is placed in the elimination ideal before its coefficient constraints are computed.

## C02

Since `B(u,u)=0`, `b^T u=0`. The projected skew form satisfies `W u=0` and `W^T=-W`. Direct contraction gives `Q u=b+b(u_flat^T u)-u_flat(b^T u)+Wu=0`; symmetrization gives `sym(Q)=B`; transpose contraction gives `Q^T u=2b`, so `A_cov=c Q^T u=2c b`. The script reduces all components of these identities for generic `u,S,T` in both engines.

Define `h=g+u_flat u_flat^T`, `D=P^T B P`, `theta=tr(g B)`, and `sigma=D-theta h/3`. The script checks `D u=sigma u=0`, symmetry, `tr(g D)=theta`, and `tr(g sigma)=0`. In the rest frame, `theta` has units of inverse time because `Q=∇U` is derivative-first with dimension velocity per length. If one instead defines `B` from `∇u`, the physical acceleration is `2c^2 B u`, rather than `2c B u`. For spatial `W_ij=epsilon_ijk omega_k`, direct index evaluation gives `W x=-omega×x`; the derivative-first convention is `W=-c omega_book`. These convention statements are algebraic/sign bookkeeping, not new dynamical claims.

## C03

At `u=(1,0,0,0)`, `B_00=0`, `theta=sum_i B_ii`, `sigma_ij=B_ij-theta delta_ij/3`, and `A_i=2c B_i0`. With `K=(-1,n)` and `n^2=1`, direct expansion gives `B(K,K)=theta/3+sigma_ij n_i n_j-A_i n_i/c`. The quotient uses the sphere equation and `c*z=1`. For the independent STF form `S_00=h0`, `S_0i=-h1_i/2`, `S_ij=h2_ij`, the direct expansion is `S(K,K)=h0+h1·n+h2:nn`. Both engines verify the polynomial identities. This is the sourceward convention and does not swap a source-forward propagation sign.

## C04 and limit

Let `J^b_a=z g^{bd} Q_ad`, `v=u+Jx`, and `N=-g(v,v)`. The script differentiates this quadratic polynomial in each `x^a` at zero. The unit shell gives `N(0)=1`; `∂_a N(0)=-2 g(u,J_a)=-2z(Q u)_a=0`. The derivative of `v/sqrt(N)` on the positive branch is `J_a-u ∂_a N(0)/2=J_a`, so the normalized field has value `u` and derivative `g^{bd}Q_ad/c` at the vertex. Sage and Singular reduce each derivative polynomial modulo the unit shell and nonzero-`c` ideal. This is a first-jet certificate only. Smooth timelike neighborhood, local flow/source extension, and Jacobi vertex Taylor order and screen invariance remain **OPEN**; no finite algebra certificate proves them.

The first development run returned C01 false because it extracted rational coefficients from a polynomial ring where the form entries were variables. The corrected script groups terms by the three sphere variables before forming the nine coefficient constraints. The observed failed output and correction are retained in `FAILED_ATTEMPTS.md`; the final run has all four computed finite checks true.
