# G03-A source recovery

Task card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip:HTT_ALL_OBLIGATIONS_20261011/tasks/G03-A.json`
(parent GR-CAS-03, source_snapshot a30d84c7). Repository HEAD when this was read: c5a683eb (read-only).
Paths below are relative to `docs/research_program/gr_statistics_loops_20260930/` unless they are absolute.

## Recovered statements, with file:line

| Item | Source (sha256) | Line(s) | What it says |
|---|---|---|---|
| Original theorem | `gr/OPTICAL_THEOREMS.md` (5ae2b6a6…8c21) | 231 | **Theorem 5.** A degree-2 slope admits a normalized source jet with A(p)=0 **iff** the Lorentz-self-adjoint S^a_b has a timelike eigenvector. Its timelike eigenvalue s_t is unique, and so is B=S−s_t g. |
| Eigen equation | same | 226–229 (eq. 24) | S^a_b u^b = s u^a, s = −S(u,u), B = S − s g. |
| Fibre and kernel dimension | same | 233–235 (eq. 25) | E_t = ker(S − s_t). If r spatial eigenvalues b_i of B vanish, then dim E_t = 1+r and the fibre is H^r. "Velocity is unique precisely when all three b_i ≠ 0. Repeated **nonzero** spatial eigenvalues do not destroy uniqueness." |
| Proof sketch | same | 237 | Eigenvectors of distinct eigenvalues are orthogonal. Two timelike vectors cannot be orthogonal. u⊥ is positive definite and S-invariant, so an ordinary real orthogonal eigenbasis exists. |
| Premise is not automatic | same | 241 | "An arbitrary measured symmetric representative is not guaranteed to have one; timelike existence is part of the geodesic image condition." |
| Only smoothness statement in the optical source | same | 259 | "Individual nondegenerate points permit local spectral perturbation control." There is no family S(q), no parameter domain and no stated conclusion. |
| Claim card | `gr/OPTICAL_CLAIMS.json` (93cb4afc…28e1) | 175–191 | OPT07, with the limitation "Not every real S has a timelike eigenvector." |
| Contract | `cas/contracts/CAS-03.json` (e1218901…26c1) | 43, 50–51, 81, 109 | C01: "…without inferring a timelike eigenline exists for every Lorentz-self-adjoint S". Assumptions: "A(p)=0; timelike eigenvector exists where claimed" and "S^a_b=g^-1 S Lorentz self-adjoint". Singular locus GEO-NOTIMELIKE: "self-adjoint alone insufficient". |
| Conventions | `cas/COMMON_SPEC.md` (4714827e…7fe1897) | 4, 8 | Signature (−,+,+,+); g=diag(−1,1,1,1); future u with g(u,u)=−1; h = g + u⊗u. |
| Analogous IFT assertion (different object) | `gr/ENERGYFRAME_THEOREMS.md` (dd66030a…6855) | 91 | "An isolated timelike eigenline depends smoothly on a smooth g-self-adjoint endomorphism near a point where L is invertible … IFT, whose spatial linearization is L." This is a stress-tensor statement. It is used here **only** as the template for the conditional branch hypothesis; it is not silently identified with the optical S. |
| Implementation | `htt/src/common/relativistic_kinematics.py` (9ae767f9…9d5e) | 116–160 | `hubble_tensor_lift` takes geodesicity as a supplied premise (`geodesic is True`). It builds S (S00=h0, S0i=−h1/2, Sij=q), diagonalises `METRIC @ S` (the mixed g⁻¹S), and rejects a complex spectrum. It keeps only timelike eigenvectors and requires the timelike eigenvalue to be **separated from all other eigenvalues** (`gap > relative_gap*scale`), normalised to g(u,u)=−1 with u⁰>0. This is the same isolation condition formalised here (C3, D1). |
| Prior admission | `local_cas/…/CAS-03/g03a_source_admission_v1_20261011/{RETURN.json,BLOCKER.md}` | — | PARTIAL. No smooth family S(q), parameter domain or isolated-line hypothesis is bound by the optical source. |

## Reused accepted Lean, imported unchanged

| Module | Path (under `local_cas/GRSTAT-CAS-20260930-1308KST/`) | sha256 | Status |
|---|---|---|---|
| `C01` (namespace CAS03C01) | `CAS-03/c01_input_aligned_v1_20261005/lean/C01.lean` | 979a2cce8d2c8a03dca3d2b050f1027088868cd4b237ca8adf55eeba40dd992b | CAS-03-C01, PR #478 (commit f7f6231c). `git show f7f6231c:<path>` has an identical sha256. FINITE_C01_CAS_4AXIS_PASS_REVIEW_PASS_WITH_DISCLOSED_LIMITATIONS. |
| `Proof` (namespace GRSTATCAS04) | `CAS-04/completion_20261003/lean/Proof.lean` | 8a870e4e0178d8aa1dd1438dfb79b4764b01f05829be05c7e837f1ccc2088144 | Dependency of G04-A. Supplies Vec4, Mat4, eta, lorentzDot, matVec, restProj. |
| `G04AEigenline` (namespace G04A) | `CAS-04/g04a_smooth_eigenline_v1_20261013/lean/G04AEigenline.lean` | 4d36cde1361a4f833636b2ad83a04755cf5725eb240947aeeb0bc4a477f1906f | G04-A, FORMALLY_CHECKED_SCOPED, review PASS_SCOPED. Supplies EtaSelfAdjoint, RestGapInjective, FutureUnitEigen, RestEigenbasis, E1_smooth_eigenline, E1u_unique, bordered_inj, isInvertible_of_injective, E0_gap_iff_eigenvalues, selfAdj_dot. |

CAS-03-C02 (PR #491, `CAS-03/c02_geodesic_family_v1_20261008/lean/Cas03C02.lean`, sha256 f1898d2e…a1157) proves the diagonal kernel finrank = zero count and the repeated-nonzero controls. It is cited, not imported: C2 below proves the general (non-diagonal) symmetric version directly.

## Representation bridge (a modelling choice, proved rather than assumed)

C01 represents a covariant symmetric S as `SymCov` (a, b, d) on V = ℝ × (Fin 3 → ℝ), with `mixed s v = g (act s v)`. G04-A works on `Vec4 = Fin 4 → ℝ` with mixed matrices `Mat4`. This packet defines `ofV` (Fin.cons) and `toMixed s a b = eta a * toMatrix s a b` (S^a_b = g^{ab} S_bc). It then proves `toMixed_matVec : matVec (toMixed s) (ofV v) = ofV (mixed s v)`, `ofV_mass`, and `toMixed_selfAdjoint`.

## What the source does NOT bind (residual, not invented)

1. **The family.** The optical source supplies no smooth family S(q), no parameter space and no regularity class. D1/D2/D3 are therefore stated **conditionally, for any** C^n family (n finite, n ≥ 1) on an open subset of any real Banach parameter space E (D2: E = Vec4 through G04-A unchanged). Nothing asserts that the physical optical slope field is such a family. Unlock: an owner-supplied binding of the optical S(q) family and its regularity.
2. **Isolation.** The source's isolation/nondegeneracy wording ("individual nondegenerate points", OPTICAL_THEOREMS.md:259) is formalised as `RestGapInjective (S q0) u0 (−s0)`. C3 proves this equivalent to: every rest eigenvalue differs from s_t; the rest kernel is ⊥; and dim E_t = 1 (simple timelike eigenvalue = unique velocity, Theorem 5 with r = 0). D3 states the branch theorem in the dim E_t = 1 form.
3. **Smoothness of individual eigenvectors.** It is not claimed anywhere. E3 proves that it fails at a rest-eigenvalue collision, even for continuity.
