# Optical mapping: scientific contract and discriminating fixtures

Owner: HTT research; solver physics remains in `bass_py`, observable extraction in `obsstat`, inference in HTT, diagnostics in MIO. Status: specified targets, with limited direct algebraic review; no new production/CAS/observational admission.

## A. Semantic lock

Use metric (-,+,+,+), spatial epsilon_123=+1, future propagation direction e and source-pointing observed direction n=-e. Define a normalized timelike vector u.u=-1 with length-valued spacetime coordinates and physical momentum

\[
p^a=(\varepsilon/c)(u^a+e^a),\qquad \varepsilon=-c u_ap^a,
\qquad D_\gamma=(c/\varepsilon)p^a\nabla_a=(u+e)^a\nabla_a.
\]

Geometric theta, A, sigma, omega, H and covariant V have units length^-1. Physical expansion/shear/vorticity rates are c times their geometric counterparts; physical acceleration is c^2 A. This preserves c explicitly rather than silently inserting c=1. For an affine tangent k=dx/dv, separately define E=-u.k and its conversion to physical energy. The ZIP's `D_gamma=E^-1 d/dtau` must not leave tau ambiguously affine or proper time.

Define h_ab=g_ab+u_a u_b, P_ab=h_ab-e_a e_b, A=∇_u u, M_ab=h_a^c h_b^d ∇_d u_c. Select and record one axial convention. The attachment's signs are consistent with

\[
M_{ab}=\tfrac13\theta h_{ab}+\sigma_{ab}+\epsilon_{abc}\omega^c.
\]

For this choice omega is the negative of the spatial +(1/2)curl u convention. If current BASS uses varpi=(1/2)epsilon^{abc}D_b u_c, the conversion is omega=-varpi and the magnetic direction term changes sign. Never decide this from epsilon_123 alone. Freeze the Riemann commutator, screen connection, affine orientation and conformal-time adapter separately. A tetrad rotation contributes a coordinate term; it is not matter vorticity or null twist.

## B. First-jet map and inverse

Under the definitions above and an affinely propagated null momentum, the proposed local computational form is

\[
H=A\cdot e+e\cdot Me=\theta/3+A\cdot e+\sigma:ee,
\quad D_\gamma\ln\varepsilon=-H,
\]
\[
\nabla_{u+e}e=H u+V,\qquad V=He-A-Me
=-P(A+\sigma e)+\omega\times e.
\]

The full four-vector derivative is not V alone. Check u.V=e.V=0. A horizontal phase-space derivative or a moving-tetrad angular connection must account for basis transport exactly once.

With outward sphere orientation, Phi=A.e+(1/2)sigma:ee gives

\[
V=-\nabla_{S^2}\Phi+\omega\times e,\quad
\mathrm{div}_{S^2}V=2A\cdot e+3\sigma:ee,\quad
\mathrm{curl}_{S^2}V=2\omega\cdot e.
\]

The ideal inverse is

\[
\theta=\frac3{4\pi}\int H\,d\Omega,\quad
A_a=\frac3{4\pi}\int He_a\,d\Omega,\quad
\sigma_{ab}=\frac{15}{8\pi}\int H e_{\langle a}e_{b\rangle}\,d\Omega,
\quad \omega=\frac3{8\pi}\int e\times V\,d\Omega.
\]

Required derivation uses ∫e_a e_b=4pi h_ab/3, ∫e_<ab>e_<cd>=8pi P_STF/15 and ∫e×(omega×e)=8pi omega/3. This gives rank 12 **for H and V known at one event in one congruence**. H contains 9 scalar coefficients, V contains 11 E/B coefficients, with 8 E-mode consistency conditions div V=2H_1+3H_2. H alone omits omega; V alone omits theta. Processed data outside this range are not additional first-jet degrees of freedom.

This is a locally valid algebraic target, not an assertion that arbitrary first jets and curvatures independently define a global Einstein solution. No static temperature Q/O inversion to all twelve components is provided.

## C. Screen, curvature and redshift charts

For a smooth null gradient k_a=∇_a psi, affine null propagation and zero null twist hold in a smooth region. Zero null twist does not imply zero timelike omega. A rescaled gradient need not remain affine. Use an explicitly parallel-transported Sachs screen (or include its connection).

Choose the tidal matrix R_AB so the declared Jacobi equation is D''=-R D and positive Ricci contraction focuses the beam. Define

\[
\mathcal B=\mathcal D'\mathcal D^{-1},\quad
\vartheta=\mathrm{tr}\mathcal B,\quad
\varsigma=\mathrm{TF}\mathcal B,\quad
D_A=\sqrt{|\det\mathcal D|}.
\]

Then derive the signs of the Sachs equations from that convention. The observer vertex uses regular D(v_o)=0 and the correctly normalized D'(v_o); do not invert D there. The often-used D'(v_o)=I requires an observer-normalized affine tangent. Caustics require a patch/parity treatment and cannot pass an invertibility gate. Image shear/rotation are defined from the endpoint amplification decomposition and are not pointwise null shear/twist.

Write alpha_z=dv/dz, avoiding B for both a matrix and a scalar. On patches with z' nonzero and det D nonzero,

\[
\mathcal K_z=\alpha_z\mathcal B=(\partial_z\mathcal D)\mathcal D^{-1},
\quad \mathrm{tr}\mathcal K_z=2\partial_z\ln D_A.
\]

This is invariant under constant affine renormalization. The z Jacobi equation is

\[
\mathcal D_{zz}+\frac{z''}{(z')^2}\mathcal D_z
=-\frac{\mathcal R}{(z')^2}\mathcal D.
\]

Do not omit its first-derivative term. At z'=0 use affine evolution or a new chart and return the unsupported z-coordinate quantity as undefined.

**Unresolved source statement:** the ZIP's `(D_A^2/2) partial_z L_IJ` must not be copied into an orthonormal screen formula until L_IJ, its determinant constraint, index positions and zweibein are recovered from the cited source. Coordinate lower-index shear and orthonormal shear differ. The invariant K_z formula above is the working fallback. This limitation does not block invariant Jacobi work.

## D. Radiation and the complete endpoint map

Use a physical occupation distribution f=[exp(epsilon/(k_B T))-1]^-1 for a ray-resolved Planck spectrum. In collisionless achromatic geometric optics, I_nu/nu^3 is conserved and

\[
T_o(n_o)=\frac{T_e(x_e(n_o),e_e(n_o))}{1+z(n_o)}.
\]

The map Phi_geo=(x_e,e_e) requires a central geodesic, source hypersurface and boundary condition. The Jacobi matrix supplies its differential for neighboring rays; it does not uniquely determine the absolute endpoint map. Focusing changes angular/source mapping, not pointwise diffuse specific intensity by a separate inverse-square factor.

The collisionless temperature equation is `[horizontal (u+e).∇ + V^A∇_A + H]T=0` only with the agreed horizontal/tetrad convention. General Thomson angular mixing of different blackbodies does not preserve one exact Planck spectrum. A temperature-only collision model requires an explicit perturbative projection and remainder; finite-anisotropy collisions use frequency-dependent distribution/intensity with polarization and transported screen. Existing REC/REI is not replaced by an unspecified RHS in this equation.

Keep dimensional Kelvin tensors and dimensionless anisotropy distinct:

\[
\Theta(n)=T(n)/\bar T-1,\quad
\Theta_{A_\ell}=\Delta_\ell^{-1}\int\Theta(n)n_{\langle A_\ell\rangle}d\Omega,
\quad \Delta_\ell=4\pi\ell!/(2\ell+1)!!.
\]

Declare Q^K=barT Theta_2 and O^K=barT Theta_3 when this direct-expansion normalization is the selected convention; verify the donor's convention before applying it. Under n=-e, odd multipoles change sign. Brightness quadrupole and temperature quadrupole have a factor-four relation only at the appropriate linearized blackbody level, not universally.

## E. T9 independent physics oracle and bounded candidate

Inspected at R9 commit 5e4e899c... (identical selected blobs to default 50ea6d...):

- terms.py `T9_shear_down`: negative (ell+2), blob 22404331f3e5577ef6215e16d4c3ef529ebf5c7d.
- hierarchy_rhs.py: subtracts a times the sum of T terms, blob 045113460bc67eef3c415ee5923aa7fd7733687e.
- mode_mixing_blocks.py: negative `pre9`, blob c7d336dc6fb161d0d667ed576050db9fec7e7b39.
- packed_operators.py: builds its T9 operator from T9_shear_down, blob 04c1af0c7fbdd94d3f9761940b15c9713f02228f.

This confirms the source pattern, not an executed physics failure. Trace actual Pi, sigma, a, eta, STF and normalization definitions before changing it. The source textbook is unnamed in the ZIP; recover author/title/edition and full equations (5.84), (11.2), (11.49), or explicitly record that citation seal unavailable and use a separately documented kinetic derivation. Do not invent a book identity from equation numbers.

Independent reference: at an event with initially isotropic f=F(epsilon), zero acceleration/rotation/collision/spatial gradient, the local collisionless equation is

\[
\partial_s f-\varepsilon\sigma_{ab}e^ae^b\partial_\varepsilon f=0.
\]

For direct brightness Pi_l=∫epsilon^3 F_l d epsilon and epsilon^4 F→0 at both endpoints, integration by parts gives

\[
\partial_s\Pi_{ab}=-4\sigma_{ab}\Pi_0.
\]

Here s is length-valued proper time. With ds=a d eta the target is `dPi_2/deta=-4 a sigma Pi0`; physical-time code instead needs c sigma or the physical shear. For I_l=Delta_l Pi_l, the LHS coefficient is

\[
\frac{\ell(\ell-1)(\ell+2)}{(2\ell-1)(2\ell+1)},
\]

and is +8/15 at ell=2. Use F(epsilon)=exp(-epsilon/E_star), E_star>0, so epsilon^4 F vanishes and dimensions remain explicit. The isolated energy integral is (ell+2)∫epsilon^3 F. A temperature fixture has coefficient -1 rather than -4 and must not be mistaken for brightness.

If the full current adapter confirms the mismatch, change the T9/pre9 sign in the isolated candidate, keep the RHS convention and enumerate dependent specs/tests. If conventions account for it or it is already fixed in local work, do not flip again. Packed/full parity is secondary evidence only. Mutation criterion: wrong production sign must fail **code-to-reference comparison**; an independent correct reference derivation itself should remain valid. Audit any cached operator tables or affected generated results at their generating source.

## F. Finite fixtures and acceptance

These are proposed new fixtures, not previously executed tests. Use SI/geometric adapters as above. Fix inputs before evaluating the candidate. Exact rational cases must equal exactly; floating fixtures use normalized residual <=1e-10 where well-conditioned with O(1) nondimensional inputs, otherwise a justified absolute+relative enclosure recorded before the candidate run. Convergence alone remains empirical unless an actual bound is proved.

| ID | Fixed input or procedure | Decision it tests |
|---|---|---|
| O01 | first-jet basis: theta=1; A along each axis; five orthonormal STF tensors; omega along each axis | forward/inverse identity, 12 rank and 8 range constraints |
| O02 | scale length L_star; sigma L_star=diag(1,-1,0); pure expansion and acceleration separately | shear normalization, H units, tangency |
| O03 | Minkowski rotating congruence u_spatial≈Omega×r/c at origin, Omega along z | direct covariant V=-(Omega/c)×e; resolve axial sign and rotating tetrad |
| O04 | Gauss–Legendre 8-point mu × 16 uniform azimuths and doubled grid, analytic monomial reference | ideal sphere projections, parity and SO(3) covariance; numerical check is not all-mask certification |
| O05 | Minkowski D=(v-v_o)I; D_A=|v-v_o| | regular vertex, expansion=2/(v-v_o), zero null shear |
| O06 | dimensionless diagonal tidal R=diag(1,-1), D(0)=0,D'(0)=I; D=diag(sin v,sinh v), 0<v<=1/2 | curvature sign, determinant and Riccati/Jacobi agreement; mathematical optical fixture only |
| O07 | z(v)=v+v^2 on [0,1/2], affine rescale v→3v+2; separate z(v)=v-v^2 turning point | z'' term, affine normalization, explicit chart refusal |
| O08 | ray Planck spectrum, barT=2.7 K, source contrast q=1e-3 n_x n_y+5e-4 n_x n_y n_z; declared redshift; unit/rotated source map | full endpoint→Q/O, source direction, Kelvin vs dimensionless tensors |
| O09 | constant T_e under any smooth angular remapping with zero redshift | no spurious inverse-square intensity modulation |
| O10 | equal mixture of T0(1+delta) and T0(1-delta), delta=1e-2; compare dimensionless frequencies epsilon/(k_B T0)=1,3,7 | exact single-temperature closure fails; temperature-difference expansion order |
| O11 | Pi0=1 in declared brightness units; ell=2; a=1 and 2; five independent STF sigma; F=exp(-epsilon/E_star) | T9 sign/normalization in tensor, packed and mixed implementations |
| O12 | incoming n=-e; SO(3) rotation; deliberate omega/T9 sign flips and missing z'' term | false-convention consumers are rejected |
| O13 | full ray response, H-only, V-only, planar angular design, nuisance sharing a signal column | ideal vs processed rank; nullspace and unsupported target |
| O14 | static Q/O supplied without H,V or radiation derivatives | no automatic JET_RESPONSE_LAW, no empirical first-jet recovery |
| O15 | reuse R9 C2=C3 stochastic cancellation, same-depth/constant-H response and shared eta counterexamples | optical extension preserves noisy-source and calibration semantics |

Pure basis perturbations are algebraic first-jet fixtures; they do not establish a global physical background. O06 is not evidence for a native Bianchi spacetime. A collisionless optical path cannot admit a Thomson/polarization source operator.

## G. Observation, inference and literature boundaries

Local H,V are not observer-time redshift drift or proper motion. An actual measurement response must include emitter/observer worldlines, integrated geometry, source conditions and frame transformations. See the original scope of [Korzyński–Kopiński, arXiv:1711.00584](https://arxiv.org/abs/1711.00584) and [Marcori et al., arXiv:1805.12121](https://arxiv.org/abs/1805.12121). [Fleury–Pitrou–Uzan, arXiv:1410.8473](https://arxiv.org/abs/1410.8473) supplies a specific Bianchi-I optical reference. The primary pages/abstracts were checked in this planning turn; full equation-level comparison is a Local research action, not claimed completed here.

With forward response R and nuisance N, distinguish structural rank from rank([R,N])-rank(N), and practical conditioning after a declared physical/covariance metric. For singular covariance qualify its support; do not add arbitrary jitter to invent identifiability. A first-jet inverse conditioned on ideal generators is not a theorem that measured CMB alone determines that jet. Unknown emitted sky can absorb different transfer histories. Finite-pixel numerical containment remains distinct from continuum algebra.

New method priority remains unresolved. The ray, Sachs/Jacobi, Lorentz and covariant Boltzmann equations are prior theory. The candidate contribution is the particular factorization, inverse-domain constraints, uncertainty handling and demonstrated consumer. A missing priority certificate does not block an explanatory or negative result; it blocks a novelty claim.

Four-axis formal admission uses current `cas_gate.py run-adjudicate`, exact structured eligibility and current source/contract binding. Historical `adjudicate`, readiness probes, the attachment's Wolfram prose, or this plan's graph validator cannot issue new formal admission. Exploratory outputs may be published at their actual grade while the affected production claim remains held.
