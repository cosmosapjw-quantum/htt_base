# G15-A source recovery (photon energy and rest direction from the normalized velocity jet)

Repository HEAD at recovery: `ac3c7d2c5ca93c82802e6e2b777f4fc35a9eec5b`.
Task card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip` (sha256
`2d0b6da9308ab43e070a620f49241640b5aa7c80c277e1f0857edea22bc4af6f`), member
`HTT_ALL_OBLIGATIONS_20261011/tasks/G15-A.json` (sha256
`41b79b1f567955ce4fb9ece3f52c3643bbdba5acdef628478216ac659c78916d`), card
`source_snapshot` `a30d84c7918b54238a48fa62e2ef482f7e6d36fa`.

Paths below are relative to `docs/research_program/gr_statistics_loops_20260930/`.

## Bound sources

| Source | sha256 | Used for |
|---|---|---|
| `cas/COMMON_SPEC.md` | `4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897` | conventions (lines 4-12, 17-18) |
| `supplements/DOSSIER_POSITIVE_BRIDGE.md` | `00c1fcb0b786bb874f13e52442af4b7b8a125287d84decb799ea68fd03915ebd` | (P0) lines 6-13; (B1) lines 72-84 |
| `cas/contracts/CAS-15.json` | `eccc10a3f5105970a46a73412d8c82a27a1e82a6116013bc0abc6656816f8eee` | C01 definition; uncontracted target line 261 |
| `cas/contracts/CAS-01.json` | `9f1bbb018e211b4d50c50532b57cf708acffdd6a01f06a24f5cb8cbb21709b57` | jet form Q=B+b u♭ᵀ−u♭bᵀ+W (line 40); B(K,K) (line 41), cross-check only |

The card requires the dossier as a source path; the CAS-15 contract's
blind-independence list forbids `supplements/**` to blind CAS workers.  This
G15-A author task was explicitly given the dossier by the card and caller; it
is therefore not a blind CAS axis run and no CAS-axis independence is claimed.

## Recovered conventions (COMMON_SPEC.md)

- line 4: signature (−,+,+,+); future u with g(u,u)=−1; U=c u; c>0.
- line 5: g=diag(−1,1,1,1) in the stated orthonormal frame.
- line 6: Q_ab=∇_a U_b is derivative-first.
- line 7: Q u=0 means Q_ab u^b=0; A_b = c u^a Q_ab.
- line 8: h_ab = g_ab + u_a u_b; h^a_b = δ^a_b + u^a u_b.
- lines 10-11: spatial trace/STF/skew parts define θ, σ, W; W_ij=ε_ijk ω_k, so
  W x = −ω×x; derivative-first W = −c × (book velocity-first vorticity).
- line 17: source-forward propagation uses L=U+c e, e·u=0, e·e=1; this is a
  different direction convention from the sourceward K=(−1,n) of line 14.
- line 18: ray derivatives are not observer-time derivatives.

## Recovered source statement (DOSSIER_POSITIVE_BRIDGE.md)

(P0), lines 6-9:
  ∇_a U_b = D_ab + W_ab − u_a A_b / c,  D = (θ/3) h + σ,  W_ab = −W_ba,  W_ab u^b = 0,
signature (−+++), U=c u, derivative-first (line 11); W_ij = ε_ijk ω_k, W x = −ω×x (line 12).

(B1), lines 74-82:
  propagation direction e in the source rest space (not the sourceward n);
  L = U + c e;  a = A/c;  H_u = θ/3;  R(e) = H_u + a·e + σ:ee;
  F(e) = P_e(a + σ e),  P_e = I − e eᵀ;
  h∇_L e = −F(e) + W e,   ∇_L ln E = −R(e).

Sign and normalization proof, line 84 (source's own sketch): future photon
momentum p = (E/c²) L; geodesic equation implies ∇_L L = R L; contract with u
using (P0); the spatial part of ∇_L U is A + c(D e − W e); insert in
∇_L(U + c e) = R L.

Statement scope: (B1) is a pointwise identity at an event on the ray, for the
given e (one direction at a time), with covariant derivatives along L.  It is
a rest-space vector identity (h∇_L e) plus one scalar identity (∇_L ln E).  It
is not stated as a full tensor theorem over all directions simultaneously
beyond "for each e"; the formalization keeps exactly that scope (universal in
the test covector Y only, which is the vector identity itself).

CAS-15 contract component C01 (line for `CAS-15-C01`): "Derive the local photon
direction/energy contractions from the specified normalized velocity jet and
source-forward null L=U+c e, with the same vorticity sign."  The full formulas
appear in `full_theorem_boundary.uncontracted_research_targets` (line 261):
"h∇_L e=-F+We;F=(I-eeT)(a+sigma e),a=A/c; ∇_LlogE=-(theta/3+a·e+sigma:ee)".

## Cross-check with CAS-01 (no reuse of CAS-01 proof objects)

CAS-01 line 41: for observer-rest u, B(K,K) = θ/3 + σ_ij n_i n_j − A_i n_i / c
with sourceward K = (−1, n).  With n = −e, K = −L/c and B(K,K) = Q(L,L)/c² =
θ/3 + a·e + σ:ee = R(e).  This agrees in sign with the dossier R(e).  It is a
consistency remark only; G15-A does not import CAS-01 Lean artifacts (the
CAS-01 `lean/Main.lean` does not export a jet-decomposition theorem usable
here).  The jet is used here in the dossier (P0) form, which is the same
tensor as CAS-01's Q = B + b u♭ᵀ − u♭ bᵀ + W once b = B u and
A_b = c u^a Q_ab are substituted.

Prior CAS-15 local work (c03 commutator inverse, c04 stacked commutant,
ls_projection_continuation, spectral_wrapper) concerns C03/C04 and the
downstream spectral inverse; none of it formalizes (B1).  No `c01*`
directory exists under CAS-15 at this HEAD.  The top-level CAS-15 ADJUDICATION
records C01 as false on the sympy and sage axes because the permitted blind
inputs did not define the jet or the photon energy; that gap is what this
source recovery closes for the author lane.

## Modelling choice (recorded)

1. Pointwise at one event, but with genuine derivatives: the ray is modelled
   by a real parameter s with tangent L, and vector fields along the ray are
   represented by their components `ℝ → (Fin 4 → ℝ)` in a parallel-propagated
   orthonormal frame.  In such a frame the metric components are constant
   (diag(−1,1,1,1)) and the covariant derivative along the curve equals the
   ordinary derivative of components.  Existence of the parallel orthonormal
   frame along a curve is standard and is NOT formalized here.
2. Geodesic hypothesis: the photon momentum p = (E/c²) L along the ray obeys
   ∇_L p = 0 (from ∇_p p = 0 and L = (c²/E) p); formalized as
   `HasDerivAt (fun s => pvec c (E s) (U s) (e s)) 0 t`.  This is a 4-vector
   equation; it is not the conclusion.  ∇_L L = R L is NOT assumed; it is derived.
3. Jet hypothesis: ∇_L U = L^a ∇_a U at the event, i.e. the lowered ray
   derivative of U equals the (P0) jet contracted with L in the derivative
   slot: `∀ Y, mink U' Y = Qjet … (Lvec c (U t) (e t)) Y`.
4. Constraints: g(e,U)=0 must hold along the ray near the event (it is
   differentiated); g(U,U)=−c², g(e,e)=1 and E>0 are only used at the event.
   Using fewer constraints than the source makes the theorem a fortiori.
5. σ trace-freeness is not used; the identities hold for any symmetric
   spatial σ (a fortiori for the STF σ of the source).
6. "(W e)·Y" is W_ab Y^a e^b = W(Y, e); this follows from (W e)_i = W_ij e_j
   with the derivative-first W.  "F·Y" is the covector of P_e(a + σ e).
