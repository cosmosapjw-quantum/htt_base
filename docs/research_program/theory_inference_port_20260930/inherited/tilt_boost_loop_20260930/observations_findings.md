# Observer/source/normal discrimination: observational findings

Date: 2026-09-30 KST. Scope: theory and source inspection; no real-data inference, no Boltzmann execution. Signature (-,+,+,+), physical four-velocities have norm -c². Source results below are separated from direct derivations.

## 1. Three comparisons, not one label

Let N be an independently specified future unit normal (physical normalization N²=-c²) to a homogeneous spacelike orbit, U the selected matter/source congruence, and W the observer velocity. Three different questions are: U=N (matter non-tilt); U≠N over the declared domain (matter tilt); and W≠U at the observer (observer boost). Radiation's energy frame U_r is a fourth field. W/U_r from CMB Doppler-aberration does not by itself measure U/N. Relative matter/radiation streaming also does not by itself establish Bianchi matter tilt.

Non-tilted anisotropic Bianchi already permits anisotropic optical propagation. Therefore rejection of a Lorentz-boosted isotropic sky is not rejection of all non-tilted Bianchi geometries. Nonzero source vorticity excludes equality to a hypersurface-normal field throughout a neighbourhood, but not value equality at a single event without further assumptions. Spatial symmetry inheritance permits the stronger orbit-level exclusion. Zero vorticity does not establish equality.

## 2. Exact endpoint algebra (direct derivation)

For future photon momentum p, write p=(E_N/c²)(N+c e), where e²=1 and N·e=0. If V=γ(N+cβ), then

    E_V = -p·V = D_V E_N,   D_V=γ(1-β·e).

The sourceward sky direction is n=-e; in that convention D=γ(1+β·n). With source U_s and observer W_o,

    1+z_obs = [D_s/D_o] (1+z_N).

This is an identity at the two endpoints for the same physical photon path. No choice of metric, field equation or photon hierarchy is needed. The normal-frame redshift includes propagation and changes when the physical geometry or normal field changes. It is not an independently measured background redshift.

Changing only the observer at the same event gives

    1+z′(n′)=(1+z(n))/D_o(n).

The angular argument must be aberrated. Holding the source event and narrow bundle fixed, aberration gives dΩ′=D_o^-2 dΩ, hence d_A′=D_o d_A. For transparent metric propagation and Etherington reciprocity, d_L′=D_o^-1 d_L. Thus

    R := (1+z)d_A = d_L/(1+z)

is unchanged by an observer endpoint boost for the same source, while its sky representation is reindexed. This is not the corrected distance used for Hubble-slope reconstruction: that correction is d_L/(1+z)²=d_A. The distinction matters.

Primary support: Challinor & van Leeuwen (2002), equations (1)–(3) and the solid-angle relation following (4), https://arxiv.org/html/astro-ph/0112457v1 ; Maartens et al. (2024), equations (27), (59), (62), (63), https://arxiv.org/html/2312.09875v3 . The displayed invariant R is derived here from those transformation laws.

## 3. Same-ray contrasts and a finite-angle bound (direct derivation)

For two fixed source/absorber events on the same incoming null generator, received at the same observer event, the Doppler multiplier D_o is common, independently of photon frequency. Therefore

    (1+z′_1)/(1+z′_2) = (1+z_1)/(1+z_2).

The contrast L_12=ln(1+z_1)-ln(1+z_2) removes the observer endpoint. It retains source Dopplers, geometry and propagation. It is not a direct tilt estimator. The same physical source identities must be used: defining bins by measured z and comparing ln(1+z) across those bins is tautological, not tomography. An independent distance/age label or a physically identified multi-absorber sightline is required for a useful forward comparison.

For rays separated by angle δ in the unprimed observer sky, with |β_o|≤β_max<1,

    |ln D_o(n_1)-ln D_o(n_2)|
       ≤ β_max |n_1-n_2|/(1-β_max)
       = 2β_max sin(δ/2)/(1-β_max).

Proof: apply the mean-value bound |ln a-ln b|≤|a-b|/min(a,b) to 1+β·n; the common γ cancels. This supplies a conservative deterministic error term for near-coincident sightlines. Interpolation, lensing-image identification, source selection, distance error and covariance are additional terms. The bound does not justify cancellation for arbitrary widely separated catalogue sources.

## 4. Positive solver-free observer/matter reconstruction route

Literature-supported foundation: Maartens, Santiago, Clarkson, Kalbouneh & Marinoni, JCAP 09 (2024) 070, arXiv:2312.09875v3. Their derivation concerns a smooth dust matter congruence, assumes geodesic motion and negligible vorticity, and treats a distinct boosted observer at one event. Their equations (32)–(34) show that the boosted covariant Hubble sky has only monopole, dipole and quadrupole; the nine measured coefficients encode expansion, shear and relative observer velocity. The reference should not be described as a claim for arbitrary accelerated sources or as a Bianchi-normal reconstruction theorem.

Let u=U/c, w=W/c. Define the physical symmetric expansion tensor B_ab=∇_(a U_b), with units s^-1. Under geodesic source motion B_ab u^b=0. Let k be past directed, normalized into K=-w+n at the observer. Define H_W(n)=B_ab K^a K^b. In the observer orthonormal tetrad write

    H_W(n)=h0+h1_i n^i+h2_ij n^i n^j,

where h2 is symmetric tracefree. Construct the symmetric tensor representative

    S00=h0,  S0i=-h1_i/2,  Sij=h2_ij.

Every symmetric tensor with the same null contraction differs from S by λg: a symmetric form vanishing on the null cone is proportional to the metric. Hence B=S+λg. Since B u=0, u is a timelike eigenvector of the mixed endomorphism S^a_b, with eigenvalue -λ.

Direct conditional reconstruction proposition: if the physical source congruence is geodesic, the measured H_W is indeed the covariant Hubble field above, and S^a_b possesses a unique future timelike eigenline with eigenvalue s_t, then

    u = normalized future timelike eigenvector(S^a_b),
    B = S - s_t g,
    γ_UW=-u·w,  β_UW²=1-γ_UW^-2.

This is algebraic and requires neither background evolution nor Boltzmann transport. A sufficient nondegeneracy condition on a realizable tensor is that the three eigenvalues of B in the matter rest space are all nonzero: the zero timelike eigenvalue then has a spectral gap from its spatial eigenvalues. If a spatial expansion eigenvalue vanishes, B has an enlarged kernel that may contain a continuum of timelike vectors, so this route can fail. Conditions on finite-error eigenframes and likelihood coverage remain to be supplied; raw numerical eigenvalue selection is not a scientific certificate.

Proof of the lift ambiguity: let a symmetric tensor Z obey Z_ab(-w+n)^a(-w+n)^b=0 for every unit n. Taking odd parts gives Z0i=0. The even part says Z00+Zij n^i n^j=0 for all unit n. A constant quadratic form on the sphere has Zij=a δij and Z00=-a. Thus Z=a g. Conversely g(K,K)=0, proving that the complete null-sky kernel is exactly span(g), rather than merely asserting a dimension count.

Proof of the timelike selection: differentiating U²=-c² gives U^b∇_aU_b=0. The other half of B_abU^b is A_a/2, so geodesicity gives B_abU^b=0. In a U-adapted orthonormal basis the mixed B is diag(0,b1,b2,b3). If every bi is nonzero, the only timelike eigenvectors of S^a_b=B^a_b-λδ^a_b are in the one-dimensional U eigenspace: every distinct eigenspace lies in the positive-definite U-rest space. This also shows why repeated nonzero spatial eigenvalues do not invalidate the reconstruction. The argument is local at one event and is kinematic; it neither establishes homogeneous-orbit existence nor the Einstein equations.

Explicit rank-deficient jet counterexample: B_ab=diag(0,0,b2,b3) in an observer tetrad gives H(n)=b2 n2²+b3 n3². For every real rapidity χ, u_χ=(coshχ,sinhχ,0,0) is a future unit timelike kernel vector. Each such assignment can have ∇_(aU_b)=B_ab at the event with zero acceleration there; for example choose the antisymmetric derivative zero at that event, which is consistent with differentiating U². The one-event Hubble sky therefore leaves a continuous velocity family. This is an instantaneous kinematic jet counterexample, not a claimed family of globally homogeneous Einstein solutions or identical full redshift-distance laws.

Direct slope convention: fix the observation event and W, set w=W/c and past null K=-w+n with -w²=1. Use length-valued affine separation ℓ normalized so x_s=x_o+ℓK+O(ℓ²) and d_A=ℓ+O(ℓ²). Along the same ray, 1+z=K·u_s at first order, after affine parallel transport of K. Therefore

    z0(n)=K·u_o-1,
    c [∂z/∂d_A]_(d_A=0,n)=K^aK^b∇_aU_b=H_W(n).

The intercept is zero only if U_o=W. Writing U_o=γ(W+cβ_m/W) gives z0=γ(1+β_m/W·n)-1. This is the same as D_o^-1-1 when the latter Doppler factor is expressed in the matter frame and the two directions are aberration matched. No expansion in β is used. Ordinary fitted z/d_A is not the derivative above when z0 is nonzero.

An additional positive route follows immediately and limits the scope of the slope-only counterexample. If the smooth source field extends to the observer and the zero-distance intercept is identifiable in every direction, write Z(n)=lim_(d_A→0)(1+z)=ζ0+ζ_i n^i. Then ζ0=γ, ζ=γβ_m/W, so

    ζ0²-|ζ|²=1,  ζ0≥1,  β_m/W=ζ/ζ0.

This zeroth-order observer/source reconstruction does not require geodesic sources and does not require an expansion eigengap. It does require a meaningful common source congruence at the observer and identifiable distance-zero extrapolation; it is not obtained merely from a finite redshift catalogue. Thus a rank-deficient Hubble derivative cannot be advertised as an impossibility theorem for the full joint intercept+distance data. In cosmology the local virialized region and the coarse-graining scale often prevent direct access to this formal limit. An inferred intercept must carry the uncertainty from extrapolating across that region.

The proof uses only geodesic motion to remove B·u; antisymmetric vorticity does not enter the null contraction. Thus the algebraic extension to nonzero vorticity at the event is a direct derivation, not an assertion that the cited paper developed that entire extension or the required cosmographic measurement procedure.

At first order in the observer velocity relative to matter, with H and σ measured in s^-1,

    h0=H+O(β²),  h2=σ+O(β²),
    h1=-2(H I+σ) β_o/U+O(β²),
    β_o/U=-(1/2)(h0 I+h2)^-1 h1+O(β²),

provided the expansion matrix is nonsingular. Exact covariant inversion avoids small-β expansion. This determines W relative to U, not U relative to N.

Measurement caveats from the same paper: with physical units H_W=c dz/dd_A at the zero-distance endpoint. For a boosted observer the redshift intercept is z0=D_o^-1-1, not generally zero. For flux distances use d_L/(1+z)², or explicitly transform the slope; forcing an uncorrected d_L fit produces wrong multipoles. Real catalogues only support an extrapolated finite-distance slope, requiring covariance, smooth-congruence scale selection, higher-order terms and a quantified remainder. Accelerated sources supply an intrinsic directional-Hubble dipole -A·n/c; leaving A unrestricted destroys the above simple velocity identification.

## 5. CMB and drift: what adds information

Challinor & van Leeuwen derive a kinematic Lorentz kernel K(β) for full sky intensity/polarization. Planck 2013 XXVII (published A&A 571 A27, 2014) detects its aberration/modulation signature independently of the large monopole-generated dipole. This supports a conditional observer/radiation relative-velocity measurement. Its statistical interpretation relies on a constrained intrinsic sky; the paper's covariance analysis uses statistical isotropy.

Direct no-identification construction: on the full radiation field, Lorentz transformations are invertible. If intrinsic field f is completely unrestricted, every β admits f_β=K(β)^-1 f_obs. Likewise an unrestricted intrinsic covariance can be chosen C_β=K(β)^-1 C_obs K(β)^-†, preserving positive semidefiniteness. Thus off-diagonal correlations do not universally distinguish observer motion from arbitrary intrinsic correlations. Masks do not restore information already absent in the full field. An isotropy assumption or constrained intrinsic covariance family is the condition that makes a velocity estimator informative. Empirical C_l can be used as nuisance functions without running a Boltzmann code, but then their uncertainty and signal dependence must be retained.

For a local nonrelativistic low-distance illustration, let sources have a smooth velocity field v_s(x)=v0+B x+O(r²), an observer have velocity v_o, and n=x/r. Then the angular motion contains

    μ(n,r)=P_n(v0-v_o)/r+P_n B n+O(r),

where P_n=I-nn^T. This separates a relative bulk translation term proportional to 1/r from a velocity-gradient term constant in r only when smoothness, distance calibration and observer/source model restrictions hold. It does not separate v0 from v_o individually. Secular aberration from acceleration adds an approximately distance-independent electric dipole; astrometric frame spin adds a magnetic dipole. A fixed one-event boost does not specify observer acceleration, so it does not specify the full time-drift template.

Heinesen (2021) derives non-FLRW redshift drift cosmography and emphasizes source-congruence and convergence restrictions. Heinesen & Korzyński (2024) provide joint position/redshift-drift expansions. Neither supplies an unrestricted finite-catalogue Bianchi tilt detector. Their geodesic/congruence approximations and frame transport conventions must be preserved. Redshift drift is an additional future/available-data-dependent channel, not assumed present in the user's current catalogue inventory.

## 6. Concrete bounded observational contract

1. Fit an observer/source relation first: use the corrected luminosity-distance/area-distance cosmography with monopole+dipole+quadrupole, a free boosted intercept, common source-congruence assumptions, survey masks and higher-distance terms. Return a joint set for (U,B), or a nonidentification flag if the timelike eigenline is not isolated.
2. Independently obtain an observer/radiation relation only under an explicit intrinsic CMB covariance family. Compare U with U_r; report matter/radiation streaming, not Bianchi tilt.
3. Use same-ray redshift ratios and R=(1+z)d_A as endpoint-boost controls. Keep source labels and the aberration map. These can falsify a proposed boost explanation under its stated source/geometry model.
4. Infer admissible homogeneous normals N from the geometric classification branch. For every compatible (U,N), evaluate γ_UN=-U·N/c² and β_UN²=1-γ_UN^-2. If all admissible pairs have β_UN bounded away from zero, non-tilt is conditionally excluded. If zero survives, report an upper bound or unresolved classification. Exact non-tilt from finite noisy data generally requires a structural model or equivalence tolerance.
5. A significant residual after fitting one shared β_o only rejects the declared observer-boost null family; it is not automatically evidence for global tilt, Bianchi geometry, or one Bianchi type.

## Sources and retrieval locators

- Challinor & van Leeuwen, Phys Rev D65 (2002)103001, https://arxiv.org/abs/astro-ph/0112457 and full text https://arxiv.org/html/astro-ph/0112457v1 . Retrieved refs turn93view1, turn94view0, turn97view2. Primary text inspected for Lorentz laws and isotropic covariance assumption.
- Planck Collaboration, A&A571 (2014)A27, https://arxiv.org/abs/1303.5087 . Retrieved turn93view2. Abstract inspected; no new reproduction of published velocity estimate.
- Maartens et al., JCAP09 (2024)070, https://arxiv.org/abs/2312.09875 and https://arxiv.org/html/2312.09875v3 . Retrieved turn100view0, turn101view0, turn102view0–3. Primary sections 2–4 inspected; equations 27,32–34,59,62–68,72 support the stated literature bridge.
- Heinesen, Phys Rev D104 (2021)123527, https://arxiv.org/html/2107.08674v2 . Retrieved turn94view1, turn97view3. Primary limitations/observer acceleration sections inspected.
- Heinesen & Korzyński, Phys Rev D110 (2024)043525, https://arxiv.org/html/2406.06167v1 . Retrieved turn97view0, turn99view3–5. Primary definitions and drift expansions inspected.
- Coley, Hervik & Lim, Fluid observers and tilting cosmology, https://arxiv.org/abs/gr-qc/0605128 . Retrieved turn99view2; abstract-level corroboration only for geometrical versus fluid congruences.
- Inoue et al., https://arxiv.org/abs/1911.01467 ; Gaia EDR3 acceleration paper https://arxiv.org/abs/2012.02036 . Retrieved turn99view0–1; supporting leads, not used as independent derivation evidence.

No novelty claim is made for the endpoint relations or Hubble multipole inversion literature. The exact eigenline formulation, finite-angle contrast bound and integration into the normal/source/observer set-valued test are direct deductions in this work unit and should receive independent review before promotion.
