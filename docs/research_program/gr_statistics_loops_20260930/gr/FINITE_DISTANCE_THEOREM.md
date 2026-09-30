# Finite-distance covariant remainder: analytical candidate GR-FD

Status: proposer-derived; independent decision pending. This is deterministic GR/optics, with no probability model. It combines standard Jacobi transport and Taylor's theorem; priority or a major new theorem is not asserted.

## Definitions and assumptions

Signature is (-,+,+,+). Fix observer o=O/c at p. Along a past null ray set K(0)=-o+n, o.K(0)=1, and use the length-valued affine parameter s>=0 with K=dx/ds, ∇_K K=0. A smooth source congruence is u=U/c, u.u=-1, and Z(s,n)=1+z=u.K, using the same absolute spectral standard. Parallel transport a screen basis from p. Its 2 by 2 Jacobi matrix obeys

    D''(s)=-Ropt(s)D(s),  D(0)=0, D'(0)=I.

This equation defines the sign of Ropt; the bound below is sign independent. Suppose ||Ropt(s)||op<=Kc with Kc>=0, and |d²Z/ds²|<=M2, on the full ray segment 0<=s<=L. Kc and M2 have dimensions length^-2. They are physical assumptions about a segment, not estimates provided automatically by a sky map or local curvature value. The source field must extend smoothly to p. Regularity may be stated as continuous Ropt and C² Z; the Volterra bound extends to bounded measurable Ropt.

Let H0(n)=c Z'(0,n)=B_ab K^a K^b, B=∇_(a U_b), and Z0(n)=u(p).K(0). Define

    f(s)=sinh(sqrt(Kc)s)/sqrt(Kc),
    eta(s)=f(s)/s-1,

with f=s and eta=0 when Kc=0, and eta(0)=0 by continuity. Assume eta(L)<1.

## Theorem

On 0<s<=L,

    ||D(s)-s I||op <= f(s)-s = s eta(s),
    s[1-eta(s)] <= d_A(s)=sqrt(det D(s)) <= s[1+eta(s)],
    |Z(s,n)-Z0(n)-H0(n)d_A(s)/c|
       <= M2 s²/2 + |H0(n)| s eta(s)/c.                    (FD1)

In particular the Jacobi matrix has no zero determinant on this interval. Writing etaL=eta(L), s<=d_A/(1-etaL) gives the conservative bound in measured distance

    |Z-Z0-H0 d_A/c|
       <= M2 d_A²/[2(1-etaL)²]
          + |H0| d_A etaL/[c(1-etaL)].                    (FD2)

The second term in FD1 is O(|H0| Kc s³/c) at small distance. FD2 sacrifices this local cubic order to use one uniform etaL. A tighter distance-only envelope uses t=min(L,d_A/(1-etaL)) in the right side of FD1 whenever the declared segment constraints are satisfied.

If Z0 is known, the secant slope satisfies

    |c(Z-Z0)/d_A-H0|
      <= c M2 s/[2(1-eta(s))]
         + |H0| eta(s)/[1-eta(s)].                       (FD3)

For a boosted observer Z0 is generally not one. Replacing Z-Z0 by z introduces the separate bias c(Z0-1)/d_A, which can diverge toward p.

## Proof

Integrating the Jacobi equation twice gives D=sI-∫₀ˢ(s-t)Ropt(t)D(t)dt. Iterating this Volterra equation, bounding each ordered product by Kc, and summing the absolutely convergent majorant yields ||D(s)||<=f(s). Applying the same bound to D-sI gives

    ||D-sI|| <= Kc ∫₀ˢ(s-t)f(t)dt = f(s)-s.

For Kc=0 the equation is D=sI exactly. The displayed integral identity and eta expansion were checked with a lightweight Wolfram call; the Volterra argument is the proof.

Every singular value of D/s lies between 1-eta and 1+eta. Eta(L)<1 and monotonicity imply invertibility throughout (0,L]. The determinant is positive near the vertex and cannot change sign. The product of the two singular values equals det(D)/s², giving the area-distance interval. This uses the observer solid-angle normalization; screen area is invariant under changing the source screen representative by a multiple of K, as in Ellis et al. §7.3.

Taylor's theorem with integral remainder gives |Z-Z0-sH0/c|<=M2 s²/2. Adding |H0||s-d_A|/c proves FD1. Monotonic eta and d_A>=s(1-etaL) prove FD2. Dividing FD1 by d_A/c proves FD3. No weak anisotropy, particular Bianchi algebra, Friedmann background, or radiation hierarchy evolution has been used.

## Covariant content of the derivative assumption

Since K is affine-parallel,

    Z'' = K^a K^b K^c ∇_a ∇_b u_c.

Thus M2 is a bound on this transported null contraction along the segment. It is not a bound inferred from the size of low multipoles at p. The optical tidal norm contains Ricci and Weyl focusing. Under Einstein gravity it depends on physical stress and Weyl curvature; imposing Einstein's equations alone does not provide a numerical Kc or M2.

## Limits and claim boundary

Flat spacetime with a constant source congruence has Kc=M2=H0=0 and exact Z=Z0. Nonzero expansion in flat spacetime can give H0!=0 while Kc=0; the first remainder term still remains. For nonzero curvature, a finite Kc bound at one event cannot replace the segment bound. Eta(L)>=1 means this sufficient certificate is inconclusive, not that a caustic exists. This is not a sharp bound on conjugate distance.

Measured distances may themselves be uncertain; that is a later inference problem. Luminosity distances must first use the appropriate reciprocity relation d_A=d_L/(1+z)² when its assumptions hold. No positivity of expansion or monotonicity of redshift is required here. The theorem does not turn a finite catalogue into an exactly measured endpoint derivative.

## Sources

Supplied Ellis, Maartens & MacCallum, Relativistic Cosmology (2012), printed pp.159–165, PDF pp.175–181: screen geometry, geodesic deviation (7.29), observer area distance (7.40)–(7.41), and reciprocal distances. Maartens et al. (2024), arXiv:2312.09875v3 §§4.1–4.3: boosted area/luminosity distances, the free redshift intercept and finite-distance contamination. The explicit norm envelope above is a direct derivation from these transport laws and elementary integral bounds, with novelty unresolved.
