# Observable Q/O contraction fibres and packet-consistency geometry

Date: 2026-09-07  
Status: DIRECTLY_DERIVED_RESEARCH_NOTE; NOT_CANONICAL; NO_PRODUCTION_CHANGE  
Purpose: connect the existing T5 contraction/projector algebra with the PR451 packet-image condition. This is a substantive finite-dimensional calculation, not another execution gate or a replacement decoder.

## 1. Basis, provenance and boundaries

The maintained objects are observable temperature tensors, not physical shear or velocity. Work in a declared three-dimensional Euclidean spatial frame with the full Frobenius tensor product. For nonzero amplitudes, set

\[
q=Q/A_Q,\qquad o=O/A_O,\qquad
A_Q=\sqrt{Q:Q},\quad A_O=\sqrt{O:O}.
\]

Here q is real STF2, o is real STF3, and both have unit Frobenius norm. The normalised tensors and the contraction vector v=o:q are dimensionless. **v is not a velocity and is not beta_RO, beta_RM or beta_MO.** No natural-units assumption or hidden c=1 convention is used. The physical frame and MES-sector state in Report A remain separate.

Freshly read source inputs:

| Input | Snapshot | Git blob | Role |
|---|---|---|---|
| `docs/research_reports/theory_packs/T5_WU010_LOCAL_OBSERVER_RESPONSE_THEOREM_PACK.md` | `af5d79ad572211247bd78ec4c1667f02b62bc087` | `108879669f96ddef53fb4df2c75fa0d0f407bb81` | Sections 4–6 give the STF map, adjoint, M and projector; section 8 supplies an exact witness |
| `htt/src/common/mes_krylov_completion.py` | `9f7d06dec0fce1c3a8a53fa5372c84d9c679c037` | `f22132c7a3f247abd00f01cf1cce13dcad091070` | Unit-shape packet, row-scaled STF3 solve and image/replay checks |
| `tests/common/test_mes_krylov_completion.py` | same PR451 snapshot | `32ff53f371b9f5d79c94cfad2073906df0dd34ad` | Fixed STF witness and normalisations |

The PR451 execution tree remains `6f2fdfd5b8fbf5e4ee3579288fb5aa3da1bb1060`. The main-local Git-return handoff already published at `af5d79ad572211247bd78ec4c1667f02b62bc087` remains the execution instruction. This note does not change its source, tests, thresholds, rcond, conditioning domain, resource budget or automatic-repair limits. No additional mandatory test or claim ID is created.

The T5 identities below are inherited source results. The unit-fibre, moment-only feasibility, sharp contraction and diagnostic-distance consequences are derived here. They are not represented as a fresh external proof, novelty claim or empirical inference.

## 2. Contraction map and its right inverse

For fixed nonzero q, define

\[
L_q:\mathrm{STF}_3(\mathbb R^3)\to\mathbb R^3,
\qquad (L_q h)_a=h_{abc}q_{bc},
\]

and use T5's algebraic STF map

\[
(\mathcal B_q w)_{abc}=3w_{\langle a}q_{bc\rangle}.
\]

The argument w is just a vector in this calculation. Reusing the algebraic map does not identify w with a physical boost.

Under the stated full contractions,

\[
L_q^*=\frac13\mathcal B_q,\qquad
L_q\mathcal B_q=M_q,
\qquad M_q=(q:q)I+\frac65q^2.
\]

Consequently

\[
L_qL_q^*=\frac13M_q\succ0.
\]

Thus L_q is surjective, its kernel has dimension 7-3=4, and its minimum-norm right inverse is

\[
R_q=L_q^*(L_qL_q^*)^{-1}=\mathcal B_q M_q^{-1}.
\]

Indeed, L_q R_q=I. For z in ker L_q, adjointness gives
\(\langle R_qv,z\rangle_F=0\), so all solutions of L_q o=v decompose uniquely as

\[
o=o_0+z,\qquad o_0=R_qv,\qquad z\in\ker L_q,
\]

with

\[
\|o\|_F^2=\|o_0\|_F^2+\|z\|_F^2,
\qquad
\|o_0\|_F^2=3v^TM_q^{-1}v.
\]

This proof uses the same factor of three as the corrected Report A section 8.2. Replacing L_q L_q^* by M_q would lose that factor.

## 3. Exact unit-norm contraction fibre

For a fixed unit q and declared vector v, define

\[
\eta(q,v)=3v^TM_q^{-1}v,\qquad
\mathcal F(q,v)=\{o\in\mathrm{STF}_3:\|o\|_F=1,\ L_qo=v\}.
\]

The preceding orthogonal decomposition gives the complete classification:

\[
\mathcal F(q,v)=
\begin{cases}
\varnothing,&\eta>1,\\
\{R_qv\},&\eta=1,\\
R_qv+\{z\in\ker L_q:\|z\|_F=\sqrt{1-\eta}\},&0\le\eta<1.
\end{cases}
\]

Because ker L_q has dimension four, the last set is a three-sphere in an affine four-dimensional space. It is not a four-sphere, and the sphere dimension is not the dimension of the full Q/O orbit space. At eta=1 the sphere collapses to one tensor. No rotational quotient is being taken here: q and v are already fixed in one declared frame.

This also proves that the image of the unit STF3 sphere under L_q is the **filled ellipsoid**

\[
\{v:3v^TM_q^{-1}v\le1\},
\]

not just its surface. The nonzero kernel supplies the remaining norm at every interior point.

This criterion is necessary and sufficient for the reduced problem (fixed q, fixed v, unit STF3 norm). It is only a necessary condition for an arbitrary full sixteen-entry Krylov packet: its ten trilinears must still correspond to the same tensor and replay the entire packet. It does not replace the existing forged-packet, trace, norm, orientation or forward-replay checks.

## 4. Feasibility from existing packet moments

The exact normalised STF2 Cayley–Hamilton identity is

\[
q^3=\frac12q+\frac{s_3}{3}I,
\qquad s_3=\operatorname{tr}q^3.
\]

It yields a useful closed form:

\[
\boxed{
M_q^{-1}
=\frac{40I+(15/2)s_3q-30q^2}{40+3s_3^2}.
}
\]

To check it without an eigendecomposition, multiply its numerator by
\(I+(6/5)q^2\). The result is

\[
40I+\frac{15}{2}s_3q+18q^2+9s_3q^3-36q^4.
\]

Substitute \(q^4=q^2/2+(s_3/3)q\). The q and q^2 terms cancel and the product is exactly \((40+3s_3^2)I\).

For the existing packet moments \(\mu_j=v^Tq^jv\),

\[
\boxed{
\eta
=\frac{120\mu_0+(45/2)s_3\mu_1-90\mu_2}{40+3s_3^2}.
}
\]

Equivalently multiply numerator and denominator by two. The denominator is strictly positive; for a real unit STF2 tensor, \(s_3^2\le1/6\), so it lies in [40,40.5]. That observation does not remove possible cancellation in the numerator or supply floating-point boundary tolerances.

This is an exact reduced-image diagnostic computable from values already in the packet. It assumes those values arise from a consistent real q and v; it does not itself establish the characteristic discriminant, positive Gram matrix or signed-volume condition. Even when those conditions and eta<=1 hold, arbitrary trilinears can remain inconsistent. In particular eta is a rotational scalar and cannot reconstruct a direction or morphology on its own.

For numerical use, a solve M_q x=v followed by eta=3 v^T x avoids an explicit inverse. The polynomial formula is a separate algebraic reference. A rounded eta just above or below one requires declared numerical-error handling; no production tolerance or gate is selected here.

## 5. A sharp contraction magnitude bound

The squared operator norm is

\[
\|L_q\|_2^2=\lambda_{\max}(M_q)/3.
\]

If a is an eigenvalue of a unit trace-free q, its other eigenvalues sum to -a. Therefore

\[
1=a^2+b^2+c^2\ge\frac32a^2,
\qquad a^2\le\frac23.
\]

It follows that

\[
\boxed{\|o:q\|_2^2\le\frac35\|o\|_F^2}
\quad (q:q=1),
\]

or in physical temperature units,

\[
\boxed{
\|O:Q\|_2^2\le\frac35(Q:Q)(O:O).
}
\]

Both sides of the last expression have fourth-power temperature units. The constant 3/5 is sharp on the full real STF2/STF3 space: take q=diag(-1,-1,2)/sqrt(6), w along its third eigenvector, and o=mathcal B_q w/||mathcal B_q w||_F. Then eta=1 and ||o:q||^2=3/5.

That equality example has repeated quadrupole eigenvalues and is **outside the cyclic Krylov chart**. It is a sharp universal contraction example, not an admitted production-decoder witness. The bound is retained as a necessary norm condition; no all-strata decoder is inferred.

## 6. Distance of a candidate to the contraction fibre

Let \(\widehat o\) be an arbitrary real STF3 candidate, while q and v remain fixed and exact. Define

\[
P_q=R_qL_q,\qquad
r_v=L_q\widehat o-v,\qquad
\widehat o_\perp=(I-P_q)\widehat o.
\]

P_q is the existing Frobenius-orthogonal projector. The minimum correction needed to reach the affine set L_q o=v is \(R_qr_v\), whose squared norm is

\[
\boxed{
\operatorname{dist}(\widehat o,\{o:L_qo=v\})^2
=3r_v^TM_q^{-1}r_v.
}
\]

For eta<=1 the unit-norm fibre is nonempty. Orthogonality and the distance to a sphere give the stronger exact formula

\[
\boxed{
\operatorname{dist}(\widehat o,\mathcal F(q,v))^2
=3r_v^TM_q^{-1}r_v
+\left(\|\widehat o_\perp\|_F-\sqrt{1-\eta}\right)^2.
}
\]

If the perpendicular candidate is zero and eta<1, the nearest point need not be unique, but the distance formula remains valid. At eta=1 it reduces to distance from the single point R_qv.

These are analytical diagnostics, not permission to project a malformed packet silently into the image. They do not check its trilinears. They require exact STF objects and the stated metric; applying them to an approximately symmetric reconstructed q needs explicit error treatment and must not silently change the input by projection.

Near eta=1 the radius sqrt(1-eta) has derivative -1/(2 sqrt(1-eta)). Thus the fibre radius is sensitive near saturation even though M_q is well conditioned. Conditioning of the contraction map, conditioning of the Krylov chart and sensitivity of the norm-boundary geometry are distinct issues.

## 7. Which information is still supplied by trilinears?

For fixed q and v, the interior fibre has three intrinsic dimensions; its four-dimensional residual subspace is constrained by one norm equation. Hence retaining q and its contraction with o does not generally retain octupole morphology. The trilinear part of the existing packet supplies the remaining information.

Let E be an orthonormal coefficient basis of STF3, A the ten-row trilinear design for an invertible fixed Krylov basis B, and N an orthonormal seven-by-four basis for the coefficient kernel of L_q. Exact injectivity of A implies rank(A N)=4. For two candidates that satisfy the same fixed contraction,

\[
\|o_1-o_2\|_F
\le
\frac{\|D(\tau_1-\tau_2)\|_2}
{\sigma_{\min}(D A N)},
\]

where D is any declared nonsingular positive row scaling, including the one used by the current solver. This follows by writing their coefficient difference as N delta-z and applying the smallest-singular-value inequality.

The bound is conditional on fixed B/q/v, consistent coordinates and the same scaling D. It does not cover simultaneous perturbation of the moments, Cholesky factor, q or amplitudes. A small packet residual without the corresponding singular-value scale is not by itself a small reconstructed-tensor-error certificate. No new threshold or compulsory test is introduced by stating this distinction.

## 8. Existing exact witness evaluated as a finite arithmetic check

The repository witness has unnormalised

\[
Q=\operatorname{diag}(1,2,-3),\quad Q:Q=14,\quad O:O=788,
\quad O:Q=(24,38,47).
\]

T5 already supplies
\(M_Q=\operatorname{diag}(76/5,94/5,124/5)\).
Normalising Q and O gives

\[
\eta
=\frac{3}{788}\left(\frac{24^2}{76/5}+\frac{38^2}{94/5}
+\frac{47^2}{124/5}\right)
=\frac{67693515}{87256816}
\approx0.775796299970423.
\]

Therefore

\[
1-\eta=\frac{19563301}{87256816}
\approx0.224203700029577,\qquad
\sqrt{1-\eta}\approx0.473501531179760.
\]

The rational result is obtained by direct fraction arithmetic. The displayed decimal value was checked with the web calculator via both the source expression and the rational expression. This is a finite arithmetic check, **not** a fresh NumPy decoder run, exact CAS verification of the general theorem, measured physical fraction or observational data analysis. It measures the remaining squared observable norm within this fixed synthetic contraction problem, not a cosmological intrinsic-octupole fraction.

## 9. Evidence status, limitations and existing next action

- Inherited/source-supported: T5 adjoint/projector/M identities and the registered synthetic witness; PR451 image/replay requirements and its existing implementation.
- Derived here: the unit-fibre classification, moment-only eta formula, sharp 3/5 contraction inequality, distance formula and fixed-contraction trilinear error bound. The derivations are explicit above.
- Arithmetic checked: the one displayed witness evaluation only.
- Not newly executed: Python/NumPy tests, SymPy/Lean proof, numerical stress, production decoder and PDF rendering. One shell call and one independent Python call returned ClientError before observable execution. One Wolfram connection returned MCP/SSE HTTP 404; no evaluator result was obtained.
- Review: result-informed main-assistant source/algebra review, not independent blind review. Novelty unresolved.
- Unchanged: production source, tests, thresholds, handoff, original ledgers/receipts, manuscript/PDF and existing accepted R2/K2/T2 evidence. Canonical remains T9 v4/30; candidate remains 40.

The narrow next executable task remains the already Git-published PR451 main-local handoff, not a new prerequisite built around this note. Local Codex performs only the still-needed native execution and any permitted in-scope repair, publishes the true result and returns immutable links directly to MAIN. A local task already in progress is not replaced by this note. PR450's registered-source replay and remaining integration/freeze decisions remain separate.

This calculation connects two existing parts of the observable methodology. It does not restore the retired scalar-only anomaly pipeline, supply a physical shear/vorticity/tilt response, strengthen an actual finite-HEALPix rank claim, or authorise observations/native-solver work.

## 10. Literature role

SciSpace was used to locate generalized-inverse/SVD context. It returned both original and reprint records, so publication identity was checked on the publishers' pages rather than adopting ingestion/reprint dates.

- R. Penrose, *A generalized inverse for matrices*, Mathematical Proceedings of the Cambridge Philosophical Society 51 (1955), 406–413, DOI `10.1017/S0305004100030401`.
- R. Penrose, *On best approximate solutions of linear matrix equations*, same journal 52 (1956), 17–19, DOI `10.1017/S0305004100030929`.
- G. Golub and W. Kahan, *Calculating the Singular Values and Pseudo-Inverse of a Matrix*, Journal of the Society for Industrial and Applied Mathematics, Series B: Numerical Analysis 2 (1965), 205–224, DOI `10.1137/0702016`.

Publisher extracts/abstracts establish these as original generalized-inverse and SVD/least-squares context. Their full proofs were not replayed in this pass. They are not cited as proving the repository-specific contraction-fibre formulas, nor added to the canonical Report-A bibliography by this note. The project-specific calculation follows explicitly from the declared T5 identities and orthogonal linear algebra.
