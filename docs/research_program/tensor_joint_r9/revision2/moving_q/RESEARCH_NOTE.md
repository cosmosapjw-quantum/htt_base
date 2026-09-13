# Moving-q contraction fibre stability

Owner: HTT/common observable-tensor research. Revision 2, 2026-09-14.
Status: DIRECT_DERIVATION; independent disposition is recorded separately in REVIEW.md.
No formal/CAS or scientific admission and no novelty determination.

## Source and domain

The conventions below are inherited from T5 WU010 §§4–6 at
`af5d79ad572211247bd78ec4c1667f02b62bc087`, source
`docs/research_reports/theory_packs/T5_WU010_LOCAL_OBSERVER_RESPONSE_THEOREM_PACK.md`,
and the contraction-fibre note §§2–3 at
`d5a5444bab6be7dcc79e362a52811882dd0a66a3` (S54 in the compendium).
The fixed-q Hausdorff formula and sharp boundary path are from
`docs/research_reports/notes/QO_FIBRE_HAUSDORFF_STABILITY_20260907.md`
§§2–4 at `c09fa9f18f8a6c997f4d7420088653e1cb9af042` (S55).
Both companion notes were directly derived, noncanonical research, not independently
admitted CAS. The compendium at d514eabdbd6a464a92ff6e51e1aba91399a054db §9.3
and R9 revision2/THEORY_EXTENSION.md F3 at bc5e028d restate them. Their original
statuses are retained; the present bounds extend the parameter domain to moving q.
No proof-DB row is promoted or counted as a newly discovered antecedent.

Use one fixed ambient Euclidean frame, E=STF³(R³), with full Frobenius products.
Let q,q' be real STF² with norm one, and v,v' real 3-vectors. These normalized
observable Q/O shapes and dimensionless contractions are not physical shear,
vorticity, velocity, observer beta or global matter tilt. No quotient by rotations
or natural-units choice is made. Define

    L_q o = o:q,   B_q w = 3 STF(w tensor q),
    M_q = I + (6/5) q²,   R_q = B_q M_q^(-1),
    P_q = I_E - R_q L_q,   c=R_q v,
    eta=3 v^T M_q^(-1) v=||c||²,   rho=sqrt(1-eta).

Inherited identities are L_q*=B_q/3, L_q B_q=M_q,
L_q L_q*=M_q/3 and L_q R_q=I. Thus P_q is the orthogonal projection
onto N_q=ker L_q, of dimension four. For eta<1 the fibre is the nonconvex
three-sphere c+rho S(N_q); eta=1 gives {c}; eta>1 gives the empty set.
Every bound below assumes BOTH fibres nonempty. Empty fibres never enter
this finite Hausdorff comparison. Matrices here represent operators only on E.

## Proposition MQ1: explicit uniform modulus

Write h=||q-q'||_F, b=||v-v'||_2, epsilon=h+b, and set

    ell=sqrt(3/5),   k=sqrt(3)*ell=3/sqrt(5),
    A=sqrt(2)*k=3 sqrt(2/5).

For all nonempty pairs in this domain,

    d_H(F(q,v),F(q',v')) <= 2 A epsilon + sqrt(2 A) sqrt(epsilon).

Hence one explicit choice is C1=6 sqrt(2/5) and C2=sqrt(6 sqrt(2/5)).
The constants are sufficient, not asserted optimal. One may also take the
minimum with 2 because both fibres lie on the same ambient unit sphere.
A more informative separated estimate is

    D = sqrt(3)*b + A*h,
    d_H <= D + sqrt(2 D) + sqrt(2)*min(1,k*h).

The latter still need not be sharp. It is an analytic upper bound for the entire
nonconvex fibre, not a sampled supremum or a support-function reconstruction.

### Step 1: uniform operator bounds

For any real STF² tensor s, its eigenvalues sum to zero. If lambda is one
of them, the other two have sum -lambda, so their squared sum is at least
lambda²/2. Therefore ||s||op² <= (2/3)||s||F². Applying the inherited
normal-matrix identity to s, including s=q-q', yields

    ||L_s||² = || (||s||F² I + (6/5)s²)/3 ||op
              <= (3/5)||s||F².

For unit q, I <= M_q <= (9/5)I. Consequently

    ||L_q-L_q'|| <= ell*h,   ||R_q|| <= sqrt(3).

The difference L_q-L_q'=L_(q-q') is on the same fixed E; no coordinate
identification between different nullspace bases is used.

### Step 2: changing the kernel via projections

Abbreviate L,R,P and L',R',P'. Since L'P'=0 and LP=0,

    (I-P)P' = R(L-L')P',
    (I-P')P = R'(L'-L)P.

Each has operator norm at most k*h. Use the exact identity

    P-P' = P(I-P') - (I-P)P'.

The two output terms are orthogonal (in ran P and its orthogonal complement);
their input components (I-P')x and P'x are also orthogonal. The first operator
has norm equal to that of its adjoint (I-P')P. Taking squared norms therefore
gives ||P-P'|| <= k*h, and orthogonal projections also satisfy ||P-P'||<=1.
This argument neither chooses nor assumes a globally smooth kernel frame.

For any nonzero subspaces N,N' with orthogonal projections P,P', put p=||P-P'||.
If u in S(N) has t=||P'u||>0, choose u'=P'u/t. Then

    ||u-u'||²=2(1-t) <= 2(1-t²) <= 2 p².

If t=0, choose any u' in S(N'); then u and u' are orthogonal and p=1,
so the same bound holds. Reversing N,N' proves

    d_H(S(N),S(N')) <= sqrt(2)*p.

Our kernels have dimension four everywhere, so the required unit spheres exist.

### Step 3: centres

Let d=c-c'. Feasibility implies ||c||,||c'||<=1. Its two orthogonal pieces obey

    (I-P)d = R [v-v'-(L-L')c'],
    P d = -P c' = -P(I-P')c'.

Their norms are at most sqrt(3)*b+k*h and k*h, respectively. Thus

    ||d|| <= sqrt((sqrt(3)*b+k*h)²+(k*h)²)
            <= sqrt(3)*b+sqrt(2)*k*h = D <= A*epsilon.

The last step uses A>=sqrt(3). No unbounded v outside the feasible ellipsoid
was inserted into this estimate. It uses the actual centre c' of a nonempty fibre.

### Step 4: radii and Hausdorff comparison

Since eta=||c||², |eta-eta'| <= 2||d|| <= 2D. The nonnegative square-root
inequality gives |rho-rho'| <= sqrt(2D). A nearest unit-direction match between
the two kernels gives in both directed Hausdorff distances

    d_H(c+rho S(N), c'+rho' S(N'))
        <= ||d||+|rho-rho'|+min(rho,rho')*d_H(S(N),S(N')).

Indeed subtract two points, split the radial difference along either unit
vector, and choose the smaller radius as the coefficient of the direction
difference. If a radius is zero, its set is a singleton and this estimate still
holds. With min(rho,rho')<=1, the separated bound follows; replacing D by
A*epsilon and sqrt(2)*k*h by A*epsilon proves MQ1.

## Proposition MQ2: interior Lipschitz bound

Assume additionally 0<delta<=1 and eta,eta'<=1-delta. Then
||c||,||c'||<=sqrt(1-delta) while rho,rho'>=sqrt(delta), so

    |rho-rho'| = |eta-eta'|/(rho+rho')
               <= sqrt((1-delta)/delta)*||d||.

Combining the same centre and projection bounds gives

    d_H <= A [2+sqrt((1-delta)/delta)] * epsilon.

Thus C_delta=A[2+sqrt((1-delta)/delta)] is explicit and uniform over that
interior. At delta=1 the centres vanish and the expression remains valid.
There is no claim that these constants are optimal; the delta^(-1/2) growth
has the order forced by the inherited radial boundary example.

## Sharpness, exclusions and normalization

For fixed q and a boundary v_* with eta=1, the source S55 path
v_t=(1-t)v_* has d_H=sqrt(2t) and epsilon=t||v_*||_2. This path is a subfamily
of the moving-q domain, so no uniform exponent greater than 1/2 can replace
the global square-root modulus. This REUSES the prior example; it is neither a
new counterexample nor evidence of instability of the linear right inverse.
For 0<delta<1/4, take radial points with eta=1-delta and eta'=1-4delta.
Their radii differ by sqrt(delta), while epsilon is
3*delta*||v_*||/(sqrt(1-delta)+sqrt(1-4delta)). The inherited exact
fixed-q distance is at least the radius difference, so the ratio is at least
(sqrt(1-delta)+sqrt(1-4delta))/(3*||v_*||*sqrt(delta)). This forces the
delta^(-1/2) order; it does not determine our best constant.
The existing fixed-q support formula remains valid in its own domain, but its
support function also describes the convex hull and does not reconstruct the
unit-norm equality fibre. Fixing estimated q would change the problem.

To transfer a raw-Q perturbation bound, assume amplitudes r=||Q||F and
r'=||Q'||F are BOTH at least a0>0. With q=Q/r and q'=Q'/r',

    ||Q-Q'||F² = (r-r')² + r*r'*||q-q'||F²,

so h<=||Q-Q'||F/a0. Substitute this into epsilon, together with a separately
justified bound for b. If v=o:q is computed from uncertain O as well, a positive
lower bound for both O amplitudes is also needed: b<=ell*(||o-o'||F+h), and
normalized-o error is bounded in the same way. Q=0 has no defined normalized q;
it is a separate unavailable branch, not an epsilon regularization. For the
unnormalized contraction L_0 o=w with unit o, w=0 gives the whole STF3 unit
sphere and w!=0 gives the empty set, a different problem. O=0 likewise has no
unit normalized octupole. None of these deterministic bounds provides a
statistical law, confidence coverage, or physical kinematic response.

## Evidence grades and scope

MQ1/MQ2 are direct derivations pending independent review. Synthetic direction
samples can falsify component bounds and provide distance witnesses; their
maximum is only a LOWER witness for Hausdorff distance. The analytic argument
above supplies the upper bound. No probabilistic sampling is labelled observed.
The existing fixed-q 38 tests and 35-basis/two-environment comparison are not
repeated or promoted. New code must exercise changing q, cross-kernel distances,
interior and saturation cases, infeasible/undefined branches and the inherited
radial sharpness identity. Numerical checks do not become four-axis proof.

All empirical/production/novelty HOLDs, absent full selection/FP/group/CF3 law,
physical response and common state-jet-anchor coverage remain unchanged.
