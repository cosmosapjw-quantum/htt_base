# EVIDENCE LEDGER

## Primary literature anchors

### Covariant radiation / CMB PSTF hierarchy
1. Gebbie & Ellis, "1+3 Covariant Cosmic Microwave Background anisotropies I:
   Algebraic relations for mode and multipole representations",
   Annals of Physics 282 (2000), DOI 10.1006/aphy.2000.6033,
   arXiv:astro-ph/9804316.
   Role: PSTF radiation multipoles and relation to conventional harmonic descriptions.

2. Gebbie, Dunsby & Ellis, "1+3 Covariant Cosmic Microwave Background anisotropies II:
   The almost-Friedmann-Lemaitre model",
   Annals of Physics 282 (2000), DOI 10.1006/aphy.2000.6034,
   arXiv:astro-ph/9904408.
   Role: transport hierarchy and line-of-sight solutions.

3. Ellis & Dunsby, "The 1+3 Covariant Approach to CMB Anisotropies" (2001).
   Role: complete frame-independent nonlinear Boltzmann radiation hierarchy.

4. Challinor, "Microwave background anisotropies from gravitational waves:
   the 1+3 covariant approach", CQG 17 (2000), DOI 10.1088/0264-9381/17/4/309.
   Role: explicit shear/Weyl/radiation multipole coupling in almost-FRW.

### General-spacetime cosmography and redshift
5. A. Heinesen, "Multipole decomposition of the general luminosity distance Hubble law",
   JCAP 05 (2021) 008, DOI 10.1088/1475-7516/2021/05/008,
   arXiv:2010.06534.
   Role: exact local directional Hubble parameter and general d_L(z,n) expansion;
   9/25/61 degrees of freedom through O(z), O(z^2), O(z^3).

6. R. Maartens et al., "Covariant cosmography: the observer-dependence of the Hubble parameter",
   JCAP 09 (2024) 070, DOI 10.1088/1475-7516/2024/09/070,
   arXiv:2312.09875.
   Role: observer boosts; expansion anisotropy; shear/velocity disentangling issues.

7. A. Heinesen, "Multipole decomposition of redshift drift:
   Model-independent mapping of the expansion history of the Universe",
   Phys. Rev. D 103, 023537 (2021), DOI 10.1103/PhysRevD.103.023537,
   arXiv:2011.10048.
   Role: redshift drift is not simply a local H(z); line-of-sight structure enters.

8. O. H. Marcori, C. Pitrou, J.-P. Uzan, T. S. Pereira,
   "Direction and redshift drifts for general observers and their applications in cosmology",
   Phys. Rev. D 98, 023517 (2018), DOI 10.1103/PhysRevD.98.023517,
   arXiv:1805.12121.
   Role: direction drift, aberration/parallax, dipole vs shear quadrupole.

### Remote-CMB tomography
9. A.-S. Deutsch et al., "Reconstruction of the remote dipole and quadrupole fields
   from the kinetic Sunyaev-Zel'dovich and polarized Sunyaev-Zel'dovich effects",
   Phys. Rev. D 98, 123501 (2018), DOI 10.1103/PhysRevD.98.123501,
   arXiv:1707.08129.
   Role: redshift-tagged remote CMB dipole/quadrupole; quadratic estimators; PCA of
   independent accessible modes.

10. J. Cayuso & M. C. Johnson,
    "Towards testing CMB anomalies using the kinetic and polarized Sunyaev-Zel'dovich effects",
    Phys. Rev. D 101, 123508 (2020), DOI 10.1103/PhysRevD.101.123508.
    Role: remote fields as genuinely new 3D information beyond the local primary CMB.

### CMB monopole temperature vs redshift
11. Planck/SZ-era literature measuring T_CMB(z), e.g. Luzzi et al. JCAP 09 (2015) 011
    and Hurier et al. A&A 561 A143 (2014).
    Role: standard adiabatic T_CMB(z)=T0(1+z) test; independent redshift-dependent
    radiation observable.

## Repository evidence inspected

Repository ref: 50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb.

- docs/lowell_bianchi/02_multipole_hierarchy_spec.md
  declares a nine-term nonlinear PSTF brightness hierarchy.

- htt/bass/hierarchy/terms.py
  implements:
  T4 acceleration-divergence at ell=0 with prefactor 2/3;
  T7 shear-up at ell=0 with prefactor 2/15;
  T9 ell=2 monopole-to-quadrupole term -4 sigma_ab Pi.

- htt/bass/hierarchy/hierarchy_rhs.py
  applies T4 at ell=0 when acceleration is nonzero and T7 at ell=0 when shear is nonzero.

Therefore the code path retains the physically required monopole acceleration/shear
couplings even though one documentation table says they are dropped.

## Wolfram execution evidence

1. Exact S^2 second/fourth angular moments.
2. Exact directional-Hubble contraction and inversion.
3. Exact zero dependence on antisymmetric omega_ab in the scalar null-direction contraction.
4. Exact hierarchy coefficient evaluation at ell=0,1,2.
5. Exact nonlinear blackbody T^4 multipole-mixing example.
6. Exact quotient-rule derivation of local near-isotropic temperature-multipole evolution.
7. Exact determinants for redshift-kernel Kronecker designs.
8. Exact near-coincident-depth degeneracy:
   det(T^T T)=(z1-z2)^2/(z1^2 z2^2).

One initial all-sphere symbolic integration call returned a Wolfram transport 502.
The calculation was then decomposed into smaller exact integrals, which succeeded.
No scientific conclusion relies on the failed call.
