# P05-A source recovery (orbit curvature and eigenframe connection)

Task card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip` member
`HTT_ALL_OBLIGATIONS_20261011/tasks/P05-A.json` (member sha256
`0d31538c90d70835d765718df0d1feb1cb30c3e1b60bb0bfaf8817a4162e0427`; zip sha256
`2d0b6da9308ab43e070a620f49241640b5aa7c80c277e1f0857edea22bc4af6f`). Card source snapshot
`a30d84c7918b54238a48fa62e2ef482f7e6d36fa`.

All paths below are relative to the repository root. Line numbers are those of the working
tree that was read on 2026-10-14. File hashes are sha256.

## 1. Statement recovered from the contract

| item | citation | verbatim |
|---|---|---|
| CAS-05 identity | `docs/research_program/theory_inference_port_20260930/CAS_CONTRACT.json:62-73` (sha256 `904d95fe…389fad`) | `R3=-tr(n^2)+(tr n)^2/2-6a.a; Gamma^j_ki=D_kT_ij/(lambda_i-lambda_j)` |
| CAS-05 assumptions | same, line 66 | `n symmetric; n*a=0; homogeneous invariant T and simple spectrum` |
| signature | same, line 4 | `-+++` (only the spatial Riemannian block is used here) |
| BIC-02 limit | `PORT_MAP.json:252-264` (sha256 `d0050aa3…ce5e0`) | `Spacelike simply transitive orbit required; positive R3 implication not a catalogue classifier; converse false` |
| BIC-03 limit | `PORT_MAP.json:265-276` | `Full supplied invariant Ricci tensor derivative and homogeneous neighborhood; simple spectrum only` |
| BIC-03b limit | `PORT_MAP.json:277-288` | `General invariant spatial tensor supplied in its eigenframe; sky morphology not automatically that tensor` |

## 2. Inherited theory claims (BIC-02 / BIC-03 / BIC-03b)

`docs/research_program/theory_inference_port_20260930/inherited/bianchi_identification_20260929/CLAIMS.json`
(sha256 `5d7280b7…bd536c`):

* line 67: `R3=-6 a^2-(1/2) sum_i n_i^2+sum_(i<j) n_i n_j` (diagonal form; equals the CAS-05 trace
  form for diagonal `n`).
* lines 89-93: mandatory correction "Keep the simply-transitive spacelike G3-orbit assumption … exclude
  Kantowski-Sachs and arbitrary rotating rest spaces"; prohibited upgrade "A measured FLRW curvature
  parameter or matter-frame scalar automatically identifies type IX".
* lines 106-107: `Gamma^j_ki=(D_k Ric)_ij/(lambda_i-lambda_j), i!=j`; `C^j_ki=Gamma^j_ki-Gamma^j_ik`.
* lines 126-130: "Torsion-freeness then determines invariant-frame brackets"; "Record division by
  the spectral gap as an instability near repeated eigenvalues".
* lines 143-145: `Gamma^j_ki=(D_k T)_ij/(lambda_i-lambda_j), i!=j`; `simple T and DT=0 => common
  symmetry algebra abelian`.

## 3. Structure-constant (n, a) convention

`…/bianchi_identification_20260929/evidence/wolfram_curvature.wl` (sha256 `60cd5e1d…faeb39`):

* line 3: `cc[[i,j,k]] = Sum[eps[[j,k,l]] nn[[l,i]],{l,3}] + av[[j]] KroneckerDelta[i,k] - av[[k]] KroneckerDelta[i,j]`,
  i.e. `C^i_{jk} = eps_{jkl} n^{li} + a_j delta^i_k - a_k delta^i_j` with `[e_j,e_k] = C^i_{jk} e_i`.
  This is the Ellis-MacCallum form `C^k_{ij} = eps_{ijl} n^{lk} + a_i delta^k_j - a_j delta^k_i`
  after renaming indices.
* line 4: Koszul coefficients `gg[[i,j,k]] = (cc[[i,j,k]] - cc[[j,k,i]] + cc[[k,i,j]])/2`.
* line 5: Riemann `rr[[i,l,j,k]] = Sum_m gg[[m,k,l]] gg[[i,j,m]] - gg[[m,j,l]] gg[[i,k,m]] - cc[[m,j,k]] gg[[i,m,l]]`.
* line 6: scalar `Sum[rr[[i,j,i,j]]]`.
* line 7: Jacobi residual for the (1,2,3) cycle; recorded output (`wolfram_curvature.json`, sha256
  `5b469e8b…5339`): `Jacobi123 -> {-2*a*n1, 0, 0}` for `n=diag(n1,n2,n3)`, `a=(a,0,0)`; and
  `ScalarCurvature -> -6*a^2 - n1^2/2 + n1*n2 - n2^2/2 + n1*n3 + n2*n3 - n3^2/2`,
  `TypeIXPositiveExample -> 3/2`, `TypeIXNegativeExample -> -5/2`.

The Wolfram evidence covers only the diagonalised case (`n` diagonal, `a` along axis 1). The Lean
statements below use a general symmetric `n` and general `a`.

## 4. Implementation conventions (`htt/src/common/relativistic_kinematics.py`, sha256 `9ae767f9…59d5e`, last commit `bc45fb92`)

* lines 248-259 `homogeneous_scalar_curvature(n, a)`: docstring "R3=-tr(n^2)+(tr n)^2/2-6a^2, C convention
  in BIC-02 … Supplied orthonormal orbit frame, inverse-length n,a; n a=0 is Jacobi"; line 256 rejects
  `|n a| > tol`; line 258 returns `-tr(n@n)+tr(n)**2/2-6 a@a`.
* lines 262-278 `homogeneous_connection(structure)`: docstring `C[k,i,j] for [e_i,e_j]=C[k,i,j] e_k -> Gamma[k,i,j]`;
  line 268 Jacobi residual `einsum('mjk,lim->lijk')+…`; line 276 `g[k,i,j]=(c[k,i,j]-c[i,j,k]+c[j,k,i])/2`.
* lines 363-388 `invariant_eigenframe_structure(eigenvalues, derivative, …)`: `derivative[k,i,j]=(D_k T)_ij`;
  line 385 `g[j,k,i] = dt[k,i,j]/(lam[i]-lam[j])` for `i != j`; line 386 `c = g - g.swapaxes(1,2)`;
  raises `NumericalUnresolved` when the spectrum is not separated (collision branch).

Lean conventions adopted (identical index order to the Python arrays):

* `C k i j` = `C^k_{ij}`, `[e_i, e_j] = Σ_k C k i j • e_k` (Python `C[k,i,j]`).
* `Cna n a k i j = Σ_l eps i j l * n l k + a i * δ k j - a j * δ k i` (Wolfram line 3 after renaming).
* `koszul C k i j = (C k i j - C i j k + C j k i)/2` = `Γ^k_{ij}` = `<∇_{e_i} e_j, e_k>` (Python `Gamma[k,i,j]`).
* `riem C i l j k` = `<R(e_j,e_k) e_l, e_i>` with the Wolfram line-5 formula; `scal C = Σ_{i,j} riem C i j i j`.
* `DT Γ T k i j = -(Σ_m Γ m k i T m j) - (Σ_m Γ m k j T i m)` = `(∇_{e_k} T)(e_i,e_j)` for frame-constant
  components (Python `derivative[k,i,j]`).

## 5. Prior reviewed Lean reused unchanged

`docs/research_program/theory_inference_port_20260930/local_execution/PORT-CAS-05/eigenframe_gap_bridge_v1_20261011/EigenframeGap.lean`
(sha256 `de20d2e4a76d526602a8b3696b883dd94b655d70bbc18902b6d8966433b16268`, status
FORMALLY_CHECKED_SCOPED per its `RETURN.json`). It is compiled from its original path into
`raw/imports/EigenframeGap.olean` and imported; `recover_coefficient` and `repeated_gap_nonunique`
are reused.

## 6. Items not recoverable / not formalised

* Manifold-level statement (left-invariant orthonormal frame on a simply transitive spacelike
  G3 orbit, Levi-Civita connection of the induced metric, homogeneity on an open neighborhood):
  Mathlib at the pinned commit has no usable Levi-Civita/Riemann-curvature API for a Lie group with a
  left-invariant metric. Searched: Mathlib `Geometry/Manifold`, `Analysis/InnerProductSpace`; the
  repository (`htt/`, `docs/research_program/*/gr`) contains only the algebraic formulas above.
  Unlock condition: a formal bridge from left-invariant frame fields to the frame-component formulas
  (Koszul on constant-component fields; `e_k(T_ij)=0` for invariant `T`). Here these appear only as the
  algebraic model and the documented reading of the definitions.
* Bianchi class labels: the Lean witnesses use isomorphism invariants (`C = 0` and the trace form
  `Σ_k C^k_{ik}`) only as named functions of the data; a formal proof that these are
  Lie-isomorphism invariants is not attempted.
