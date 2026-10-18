# L02 statistic family fixed for this execution

Owner: obsstat. Scope: source-bound, diagnostic-only, C0. Transfer source: none.
Acceptance remains the original L02 requirement: conservation under SO(3)/O(3)
and no posthoc preregistration. Independent review and L01/X03 dependency
acceptance are separate from this execution.

This declaration is written before this package computes its descriptors.
The input sky and historical findings have already been seen by the project.
Application to this archive is **retrospective**. It is not preregistration, and
the historical selected p=.039 is neither an input nor an output here. The
algorithm below can be frozen prospectively for future source-matched null rows;
that future use needs the L03 observational law and L04 joint-selection analysis.

## Source, units, basis and physical group action

Use exactly `htt_mes_eps_loop9_20261015/inputs/retained_common_support_coefficients.npz`,
SHA256 `900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459`.
Nine T products and eight E/B products are processing alternatives/splits of
**one physical sky**, not 25 independent skies. T support is 26,846 NSIDE64 pixels;
polarization support is 30,021. They are different supports. The source is the
original finite cut-sky least-squares estimator, not the newer native matched
estimator. E/B high-ell leakage is not calibrated by this computation.

Coefficients are microK_CMB in orthonormal Condon--Shortley real harmonics ordered
per ell as m0, sqrt(2)Re(Y_l1), sqrt(2)Im(Y_l1), ... . Thus stored complex
a_lm=(c_cos-i*c_sin)/sqrt(2). Split E/B by the archive's explicit per-column
metadata, never by an assumed contiguous 32-column cut. Existing
`obsstat.reboot_tensor_features.tensors_from_real` and
`obsstat.planck_lowell_irrep_projection` supply the STF map for ell=2/3.

For active M in O(3), Q' = p M Q M^T and
O'_ijk = p M_ia M_jb M_kc O_abc, where p=1 for T/E and p=det(M) for B.
Under inversion the coefficient factor is (-1)^ell for T/E and
(-1)^(ell+1) for B. B therefore uses axial STF tensors. This is the standard
E-even/B-odd parity convention, not a claim of physical parity violation.
Primary source: [Zaldarriaga & Seljak (1997)](https://arxiv.org/abs/astro-ph/9609170),
doi:10.1103/PhysRevD.55.1830.

## Fixed descriptors and separation of families

All quantities below are computed for every available product; no product is
selected for a favorable value. Let q=Q/||Q||_F, o=O/||O||_F,
A_ij=o_iab o_jab and v_i=o_ijk q_jk. The fixed ell set is {2,3}.

1. Power: C2=sum(c2^2)/5 and C3=sum(c3^2)/7, in microK_CMB^2.
2. Signed SO(3) descriptors: s=tr(q^3), k=lambda_max(A),
   a=tr(q^2 A), h=v dot ((qv) cross (Av))/(||v||||qv||||Av||).
   These are incomplete orbit signatures, not coordinates separating every orbit.
   Under an improper physical action, (s,k,a,h) picks up signs
   (+,+,+,-) for T/E and (-,+,+,+) for B. In particular, B's h is parity even.
3. O(3) orbit summaries: (abs(s),k,a,abs(h)) for T/E and
   (abs(s),k,a,h) for B. The loss of sign is explicit; no distance or complete
   SO(3)/O(3) orbit classification is claimed.
4. Joint multipole axes: principal *headless* eigenaxes of q^2 and A, represented
   by rank-one projectors P2 and P3. tr(P2 P3) is a rotation/reflection invariant
   squared-axis overlap. It does not select one signed Q eigenvalue, which would
   change under B's axial sign. All three Galactic Cartesian diagonal entries
   of each projector are the fixed external-axis orientation family. The full
   projectors are retained to test covariance P' = M P M^T. These entries are
   coordinate-dependent orientation descriptors, not invariants with axes held
   fixed. Co-transforming the axes restores covariance. No sky-axis optimization,
   axis fitted from this sky, depth scan, or fabricated depth information is used.
5. Same-product cross-fields: normalized Frobenius overlaps Q_F:Q_G and
   O_F:O_G for TE/TB/EB, plus the P2 and P3 squared-axis overlaps. TE contractions
   are O(3) even; TB/EB contractions are SO(3) scalars and O(3) odd. Their absolute
   values are separately supplied as O(3) summaries. T and E/B have different
   supports, so cross-fields are processed-feature geometry, not a physical
   full-sky cross-spectrum.

## Unknowns, numerics and complete trial inventory

All input rows must be finite real vectors. Non-STF or non-orthogonal transforms
are rejected. Zero tensors have unknown normalized descriptors and orientation.
For normalized tensors, a principal axis is UNKNOWN if its leading eigengap is
<=1e-10 times its spectral scale. Chirality is UNKNOWN if any of its three
normalized vectors has norm <=1e-10; no zero is substituted. Undefined rows stay
in outputs with explicit statuses. Tests use abs tolerance 2e-11 for normalized
descriptors/projectors and 2e-10 for harmonic synthesis; these are finite numerical
checks, not outward-rounded certificates or formal all-input proofs.

The selection inventory is nine T, eight E, eight B field rows, ell={2,3},
the descriptors above, three fixed external axes, all three available cross-field
pairs for eight shared product names, and no depth choices. Signed and absolute
parity summaries and shape/orientation families are all declared. No family
maximum, look-elsewhere-corrected score, null rank, p-value or posterior is
reported. Any future data-dependent choice among these alternatives belongs to
the full joint selection family applied identically to observed and null rows.
Historical choices not enumerated here remain retrospective additional trials;
this list does not erase them.

## Consuming decision and limits

This package supplies actual feature vectors and mathematical metamorphic tests
for L02 review. It does not accept L01, qualify a null law, identify a Bianchi
family, estimate matter shear/vorticity, or establish publication readiness.
Stop interpretation if source identity/basis/support changes. Future native
vectors require a separate explicit estimator/source identity before use.
