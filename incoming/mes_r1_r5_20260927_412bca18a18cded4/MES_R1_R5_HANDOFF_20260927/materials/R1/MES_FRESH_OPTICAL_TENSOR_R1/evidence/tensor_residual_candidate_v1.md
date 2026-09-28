# Exact positive shear block of the radiation transport equation

Status: new owner derivation for bounded independent verification, 2026-09-20. This is not an observed shear measurement or a global almost-EGS theorem.

## Definitions

At one event choose an observer orthonormal triad. Let B(e)>=0 be the bolometric photon energy density per solid angle, sufficiently regular on the unit sphere (C^1 suffices for the integration by parts below). Then rho=integral B dOmega and M2=integral B ee^T dOmega. B has units J m^-3 sr^-1, rho and M2 have units J m^-3. A direction-dependent Planck distribution gives B=a_R T(e)^4/(4 pi), a_R=pi^2 k_B^4/(15 hbar^3 c^3). Masked/noisy maps are not themselves the positive full-sky physical B; this distinction belongs to estimation.

Let V2 be the five-dimensional vector space of symmetric trace-free 3x3 tensors with Frobenius inner product. For a physical congruence shear S in s^-1, its angular/redshift part of the local bolometric Liouville operator is

    A_S B = -[(I-ee^T)Se].grad_S2 B + 4(e^TSe)B.

The 4 follows by integrating E^3 f(E,e) over energy and requiring vanishing E^4 f at 0 and infinity. Angular direction e is the photon propagation direction; the even sector is unchanged by n=-e. Other kinematic terms, spacetime derivatives and collisions are kept separately, not set to zero.

## Derivation

Set E(e)=ee^T-I/3, s=e^TSe, w=(I-ee^T)Se. On the unit sphere div w=-3s, and the directional derivative of E is (Se)e^T+e(Se)^T-2s ee^T. Since the sphere has no boundary, componentwise integration by parts gives

    L_B(S) := integral E A_S B dOmega
            = integral B[(Se)e^T+e(Se)^T-s ee^T-(I/3)s]dOmega.

The output is STF. In moment form,

    L_B(S)=S M2+M2 S-M4:S-(I/3)(M2:S),
    M4_ijkl=integral B e_i e_j e_k e_l dOmega.

Only B multipoles ell=0,2,4 enter, regardless of the strength of all other multipoles. This is an exact statement about the shear block, not a finite closure of the entire Boltzmann hierarchy.

For any S,T in V2,

    T:L_B(S)=integral B[2(Te).(Se)-(e^TTe)(e^TSe)]dOmega,

so the operator is self-adjoint. Since |e^TSe|^2<=|Se|^2,

    S:L_B(S)>=integral B|Se|^2 dOmega
             =tr(S^2 M2)
             >=lambda_min(M2)||S||_F^2.

Consequently M2>0 is a sufficient condition for a positive definite invertible 5x5 shear block. Strict positivity of B over the whole sphere is sufficient but stronger than needed. A singular M2 only defeats this sufficient test; it does not by itself prove that L_B is singular. In the isotropic limit B=rho/(4 pi), L_B=(8rho/15)I_V2. No small-anisotropy or Einstein-field-equation assumption was needed for this local block identity.

## Finite tensor residual inequality

Write the exact kinetic equation as A_S B + R_other = C, where R_other retains the time/spatial derivatives, expansion, acceleration, vorticity/basis transport contributions with declared conventions. Define r=integral E(C-R_other)dOmega. Then

    L_B(S)=r.

If r is known, S=L_B^-1 r. If only r belongs to a declared set R is known, the exact shear-compatible set for this block is

    S_set=L_B^-1 R.

For ||r||_F<=r_* and M2>0,

    ||S||_F <= r_*/lambda_min(M2).

The sharper constant is the smallest eigenvalue of the actual 5x5 operator L_B. A centered residual ellipsoid becomes a shear ellipsoid under L_B^-1, preserving directional information that a scalar norm bound discards. General residual sets can be propagated by support functions rather than collapsed to a scalar first. If B is uncertain, propagate its joint uncertainty with r; if r also depends on unknown kinematic variables, solve the joint conditional feasibility problem rather than treating it as observed.

This constructs a finite tensor inequality at arbitrary angular anisotropy. It does NOT remove all needed premises. A static CMB sky gives B and hence L_B in a chosen frame, but does not give the temporal/spatial radiation derivatives in r. A derivative/residual model, additional observations, or controlled analytic dynamics supplies that information. Nor does the local feasible set ensure global Einstein-matter realizability. The open empirical task is to obtain useful r sets from defensible data/assumptions.

## Relation to the original goal

The constructive replacement for a single universal scalar ceiling is a family of tensor-compatible regions indexed by an explicit physical residual class. This does not assume a particular Bianchi family. A MES small-derivative class is one conditional residual regime; the exact Bianchi I endpoint and stress calculation is a separate solvable pilot. Percentages can then use a declared directional/radial gauge of the admissible tensor set, while the full signed STF tensor remains available for morphology. Such a gauge is a new statistic, distinct from the existing x/Q/F definitions unless a reduction is proved.

Claim ceiling: the operator identity and coercivity bound are direct local derivations. Useful present-data constraints, a nonlinear almost-FLRW theorem, a canonical global percentage, and novelty remain unestablished.
