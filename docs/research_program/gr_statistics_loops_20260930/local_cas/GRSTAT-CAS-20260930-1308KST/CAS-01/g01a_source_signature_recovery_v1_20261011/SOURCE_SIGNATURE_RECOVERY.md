# G01-A optical source-signature recovery

Status: **partial source-signature recovery; not a geometric proof**.

This successor preserves the earlier `g01a_source_admission_v1_20261011`
blocker.  It records source material found after that assessment and makes no
claim that the missing geometric-to-Lean binding has been supplied.

## Bound source material

| Source | SHA-256 | Recovered interface material |
|---|---|---|
| `gr/OPTICAL_THEOREMS.md` | `5ae2b6a65a5704247bed3d7dc5f01924318063ee5443cfa95c30c452b0ea8c21` | §§1 and 4: smooth time-oriented Lorentzian spacetime of signature `(-+++)`; event `p`; future unit observer `o`; sourceward `n`; `K(0)=-o+n`; length-affine null ray, `∇_K K=0`; a parallel screen basis; `J(0)=0`, `J'(0)=I`, and `J''=ℛJ`; `d_A=sqrt(det J)` on the positive vertex branch; and the stated invariance of transverse inner products after a change of source-screen representative by a multiple of `K`. |
| `gr/FINITE_DISTANCE_THEOREM.md` | `d499eb7fdc523926fd981c5b65a37d7b9dd894560973b6be3a2046972a5e50ac` | Definitions: the same observer-normalized affine ray and a parallel transported screen basis; an explicit two-by-two Jacobi equation `D''=-Ropt D`, `D(0)=0`, `D'(0)=I`; and the claimed area-distance normalization and sign convention. |

The optical note is proposer-derived and explicitly “not independently
promoted”; the finite-distance note says “independent decision pending”.  They
are source material, not an independent theorem receipt.

## Concrete recovered mapping target

For a future formal bridge, the exact data to be represented are:

```text
M : smooth time-oriented Lorentzian spacetime, signature (-+++)
p : M
o : T_p M, future unit timelike
n : T_p M, o-orthogonal unit spacelike
γ : [0,L] -> M, γ(0)=p, γ'(0)=-o+n, ∇_{γ'}γ'=0
E : parallel orthonormal screen frame along γ
J : [0,L] -> End(R^2), J(0)=0, J'(0)=Id,
    J''(s) = -Ropt(s) J(s)
d_A(s) = sqrt(det J(s)) on the positive vertex branch.
```

The sign is deliberately frozen to the finite-distance source's `-Ropt` form.
`OPTICAL_THEOREMS.md` writes `J''=ℛJ`; any subsequent bridge must prove or
define `ℛ=-Ropt` rather than silently treating the two symbols as equal.

The required construction must populate the actual
`CAS07M05.JacobiPremises K L` structure: `D`, `D1`, `D2`, and `R`; both
within-interval derivative statements; continuity of `D2` and `R`; the two
vertex initial conditions; the Jacobi equation; and the all-interval operator
norm curvature bound.  Its determinant-distance theorem additionally consumes
`0 ≤ K`, `0 < L`, a selected `0 < s ≤ L`, and `eta K L < 1`.  A continuous
Euclidean `Ropt` alone is therefore not enough.  Only after a type-correct map
to all of those fields and hypotheses is the existing conditional CAS07
Jacobi-matrix majorant reusable.  That result does not construct `M`, `γ`,
`E`, `J`, or the area-distance observable.

## Still missing — no dispatchable universal theorem yet

1. A formal Lorentzian manifold/connection/curvature API with a declared
   Riemann sign and a definition of the optical tidal operator along `γ`.
2. A formal screen quotient/bundle and proof that the selected parallel frame
   produces a Euclidean operator `Ropt : [0,L] -> End(R^2)` with the displayed
   Jacobi equation.
3. A formal transition theorem for admissible screen representatives and the
   resulting equality of the geometric area-distance observable; the source's
   prose argument is not a machine-checked transition law.
4. A proof of the vertex positive branch and the map from the geometric `J` to
   every field of the exact `CAS07M05.JacobiPremises` type, including its
   derivative/continuity and interval-bound premises.  This cannot be replaced
   by assuming the requested final area-distance conclusion.

Accordingly a new Lean theorem with a typeclass that *assumes* items 1--4
would be a useful conditional wrapper only, not completion of G01-A.  The next
actual proof obligation is to specify and implement those geometric objects
and the mapping theorem, then validate only that successor and the affected
CAS07 interface.

## Scope boundary

No CAS01 finite component has been rerun, no CAS07 candidate has been
re-reviewed, and no four-axis or scientific status is changed.  In particular,
the recovery neither proves finite-distance estimates nor promotes the
proposer's optical statements to independent review.
