# Goal 2 — detector-qualified kinematic inversion

28 October 2026. Internal constructive theory unit. Skill context: PhysMath 1.3.0, selected R2/R3/R4/R5/R7/R9 and the shared WORK_PACKET.md. The calculations below reuse the attached optical manuscript and MF02 rather than claiming their algebraic identities as newly discovered results. No native solver, ODE evolution, catalogue refit, repository push or acceptance change was performed.

## 1. The result

The matrix extension makes the original kinematic question more precise: which components of a specified matter/response gradient survive the source, transport, detector and frame calibration? The exact longitudinal–transverse inverse in MF02 can be turned into a finite measurement-rank theorem and a joint confidence image. This yields a constructive alternative to the phrase “100% vorticity reconstruction.”

For a two-dimensional internal space, a general Hermitian-valued spatial gradient has 36 real components. In the executed ideal-response design, total-intensity channels retain 9, two helicity channels retain 18, and an informationally complete four-effect instrument retains all 36. Radial data alone retain 24. An unknown common catalogue spin removes three geometric antisymmetric directions even from the complete instrument, leaving rank 33. Those losses have distinct mechanisms and remain explicit in the physical result.

A second result concerns the matrix-log bridge. The Fréchet matrix-log identity is correct, but a measured scalar channel magnitude uses the logarithm *after* detector contraction. These two operations differ. In the executed two-state example, the channel log derivative is \(1/3\), while the detector pairing with the matrix-log derivative is \(\log 2/2\). The matrix extension therefore needs a measured Stokes/coherency carrier or its full detector likelihood; it cannot be inserted into a scalar magnitude pipeline by replacing one formula.

## 2. Source and convention map

The attached main.pdf was read throughout its 14 pages. Its retained results include the STF contraction image and sharp chirality bound, the local scalar optical response (21)–(24), the finite coupled octupole (26), the constructive inverse and four-component kernel (30)–(35), and the complete-field inverse (38)–(39). These results are preserved.

MF02 was read at §§1.12 (pp.34–35), 2.7 (pp.55–56) and 2.8 (pp.57–58), with the gradient convention in §§1.2–1.3 (pp.10–12). The rendered p.58 was inspected to resolve index order in (2.8.11). Current R36-03-PM-HISTORY and R36-04-OPTICAL-JOINT interpretations are reused with their later formal qualification records, which supersede the older “pending review” prose. The branch is pinned at 7f3f49a6b6d95b6ae0323d5bebd3afce0067b1a7.

Use signature \((-+++)\). In this note \(K_{ab}=h_a{}^ch_b{}^d\nabla_d u_c\) has the velocity index first and the derivative index second, and has physical inverse-time units:
\[
K_{ab}=Hh_{ab}+\Sigma_{ab}+W_{ab},\qquad
W_{ab}=\epsilon_{abc}\Omega_c .
\]
Thus \(Wn=n\times\Omega\) with the displayed axial-vector convention. The attached optical manuscript writes its spacetime derivative in the opposite index order; its radial contraction is unaffected by the antisymmetric transpose, while transverse signs must be translated.

Use \(u^au_a=-c^2\) for the physical velocity here, and \(\bar u=u/c\) for the unit velocity used in the optical manuscript. Its past-directed null vector is therefore \(\ell=-\bar u+n=-u/c+n\) in the present notation. With outward source direction this yields
\[
\mathcal H_u(n)=H-A\cdot n/c+\Sigma:nn.
\]
MF02 §2.8 instead uses the future-null \(r=u/c+n\), yielding the displayed plus sign in its acceleration term. Both formulas have their stated conventions; copying the sign from one into the other would be an error.

Geometric \(u\), internal drift \(\Delta_a\), and detector effects \(R\) are different objects. A Hermitian response \(Z=r^ar^b\mathcal D_a\mathcal U_b\) does not by definition become the measured photon redshift. MF02 explicitly retains that physical qualification.

## 3. The axial STF bridge

For a real STF matrix \(S\) and any vector \(w\), define
\[
(L_Sw)_{ijk}=\frac13(S_{ij}w_k+S_{ik}w_j+S_{jk}w_i)
-\frac{2}{15}\bigl[\delta_{ij}(Sw)_k+\delta_{ik}(Sw)_j+\delta_{jk}(Sw)_i\bigr].
\]
Taking one trace gives zero, and on the unit sphere
\[
(S:nn)(w\cdot n)=(L_Sw):n^3+\frac25(Sw)\cdot n.
\]
This is main.pdf (28) and MF02 (1.12.8), with the same lift. Its singular-value and minimum-norm inverse results survive unchanged when \(w\) carries an axial rather than polar representation.

Under an improper orthogonal \(R\), an axial vector transforms as \(w'\!=\det(R)Rw\); hence
\[
L_{RSR^T}w'=\det(R)\,R^{\otimes3}L_Sw .
\]
The coefficient is then a rank-three pseudotensor. This algebra does not say that matter vorticity generates a scalar luminosity-distance octupole. The radial contraction itself removes \(W_{ab}\), and any axial coupling needs a parity-sensitive physical response. For example, the specified spin-raising adapter \(P_B=i\kappa\eth^2\Psi\) in MF02 removes the \(\ell=1\) term and maps a pseudoscalar cubic to a magnetic-type spin-2 pattern, but its coupling constant and applicability must come from transport/detector physics. Stokes \(V\) and CMB \(B\) are distinct observables.

Exact Wolfram checking returned zero for the cubic Laplacian and for the six-axis inverse below. The first call used an incorrect differentiation syntax for the Laplacian, produced D::ivar, and is retained alongside the corrected call. The Python product-decomposition residual is \(8.33\times10^{-17}\); the axial parity transformation and STF trace were also checked.

## 4. From the continuum identity to finite detector data

Let \(\mathcal K_{ab}\in\mathrm{Herm}(E)\) be the spatial response gradient at one event in a common fibre. Define
\[
\mathcal H(n)=n_an_b\mathcal K_{ab},\qquad
\mathcal Q_a(n)=(\delta_{ab}-n_an_b)\mathcal K_{bc}n_c.
\]
Then
\[
n_a\mathcal H+\mathcal Q_a=\mathcal K_{ab}n_b,
\qquad
\mathcal K_{ab}=3\left\langle[n_a\mathcal H(n)+\mathcal Q_a(n)]n_b\right\rangle.
\]
The proof uses only \(\langle n_bn_c\rangle=\delta_{bc}/3\). Consequently any discrete angular design whose weighted second moment is \(I/3\) gives the same ideal inverse. Six antipodal Cartesian directions already suffice when *all matrix-valued radial and transverse responses* are supplied. This is an exact reconstruction of a spatial gradient, not of all spacetime derivatives or of acceleration by itself.

Now choose an orthonormal Hermitian basis \(E_A\), \(A=1,\ldots,r\), \(r=\dim_\mathbb R\mathrm{Herm}(E)\), and write
\[
\mathcal K_{ab}=\sum_A k^A_{ab}E_A,\qquad B_{iA}=\operatorname{tr}(R_iE_A).
\]
Assume the calibrated instrument gives the linear responses
\[
h_{ij}=\operatorname{tr}[R_i\mathcal H(n_j)],\qquad
q_{ij,a}=\operatorname{tr}[R_i\mathcal Q_a(n_j)].
\]
Assemble \(b_{ij}=n_jh_{ij}+q_{ij}\). If \(N=[n_1,\ldots,n_J]\), the map is, up to vectorization order,
\[
b=(B\otimes N^T\otimes I_3)\,k.
\]

**Finite detector-rank proposition.** For fixed calibrated effects, fixed fibre identifications and a common physical response, the assembled map has rank
\[
\boxed{\operatorname{rank}J
=3\,\operatorname{rank}B\,\operatorname{rank}N.}
\]
This follows from the rank of a Kronecker product. Thus complete spatial-gradient recovery requires both a three-dimensional direction span and an informationally complete internal detector span. If only radial responses are supplied and the angular quadratic design spans \(\mathrm{Sym}_3\), the rank is \(6\operatorname{rank}B\). Every internal antisymmetric gradient sector is then invisible. Tangential data alone additionally remove each isotropic expansion sector.

These are applications of finite linear inverse theory to the supplied matrix response, not claims of a new general rank theorem. They identify exactly which measurement additions change the answer.

For ordinary polarimetric flux, the primitive measurement is \(\operatorname{tr}[R_i\mathcal A(L)]\). The assumption that it realizes \(h_{ij}\) or \(q_{ij}\) above is an additional source/response contract. A measured polarization rotation is not automatically a transverse velocity-gradient measurement. Likewise the proper motion of a distant quasar uses endpoint, observer and history terms, not the instantaneous neighbouring-worldline formula without qualification.

## 5. What geometric vorticity can actually be separated?

Suppose
\[
\mathcal K_{ab}=K_{ab}I+J_{ab}.
\]
If \(\operatorname{tr}J_{ab}=0\) in the stated physical decomposition, then
\[
K_{ab}=\operatorname{tr}\mathcal K_{ab}/\dim E.
\]
Expansion, shear and vorticity are linear functions of that trace:
\[
H=\tfrac13K_{aa},\qquad
\Sigma_{ab}=K_{(ab)}-H\delta_{ab},\qquad
\Omega_a=\tfrac12\epsilon_{abc}K_{bc}.
\]
If the trace-free condition is not supplied, the transformation
\[
K\mapsto K+D,\qquad J\mapsto J-DI
\]
leaves \(\mathcal K\) unchanged. No detector reconstruction of \(\mathcal K\) alone distinguishes that split. Choosing a matter frame or an internal-trace convention is part of the physical target, not another measured component.

An unknown rotation of the catalogue triad adds precisely the identity-sector antisymmetric field. Profiling a completely free three-vector spin therefore removes the three geometric vorticity directions, even if the internal instrument is complete. Internal traceless antisymmetric response may remain accessible if the instrument measures it. A calibrated nonrotating frame, external frame-spin constraint, or a physically specified multi-epoch/frame model is needed for geometric vorticity.

This accords with Mignard–Klioner (2012), whose toroidal \(\ell=1\) VSH coefficients describe frame rotation, while spheroidal \(\ell=1\) describes glide/acceleration in its source model. Their full vector treatment is a required baseline. Adding polarization does not by itself supply the missing absolute frame.

Acceleration is a separate target. In the manuscript's same-congruence scalar branch,
\[
d=-A/(cH).
\]
In the qualified geodesic-dust moving-observer branch, R36-04 instead has
\[
d_{\rm boost}=-2(I+S)\beta+O(\beta^2)
\]
in the corrected optical chart. Both can span a three-component observed dipole, but they have different physical referents. One should compare these response families or introduce a jointly derived source law, rather than summing their formulas without deriving the mixed setting. The fibre dipole coefficient further contains \(\dot\Delta/c-K^T\Delta/c\). Inferring acceleration from that coefficient requires separating these terms.

## 6. Joint confidence regions with calibration and finite response error

For a chosen physical linearization let
\[
y=J\theta+N\eta+b+\epsilon,\qquad
\epsilon\sim N(0,C),\qquad C\succ0.
\]
Here \(J\) includes the actual angular/transport/detector response, \(N\eta\) includes frame spin and other common nuisance, and \(b\) is a bounded source or truncation remainder. Set \(W C W^T=I\), \(M=I-P_{WN}\), \(B=MWJ\), and
\[
F=B^TB,\qquad P=F^+F,\qquad
\widehat\theta=F^+B^TMWy.
\]
For \(b=0\), \(\widehat\theta\) estimates \(P\theta\), with covariance \(F^+\). The unobservable kernel is retained, not assigned zero physical value. If \(r_F=\operatorname{rank}F\), the exact linear-Gaussian image event is
\[
(\widehat\theta-\theta)^TF(\widehat\theta-\theta)
\le\chi^2_{r_F,1-\alpha}.
\]
This confidence set concerns the identifiable mean coordinates. An additional residual-space statistic is needed for overall model adequacy.

If the specified physical error obeys \(\|MWb\|\le\varepsilon\), then
\[
\boxed{\|F^{1/2}(\widehat\theta-\theta)\|
\le\sqrt{\chi^2_{r_F,1-\alpha}}+\varepsilon}
\]
has coverage at least \(1-\alpha\). To prove it, the standardized bias is the projection of \(MWb\) onto \(\operatorname{col}B\), so its norm is at most \(\varepsilon\); the stochastic term has the norm of \(r_F\) independent standard normals. The triangle inequality gives the stated event. More structured remainder sets can be propagated without replacing them by a ball.

The parent integration in `JOINT_REMAINDER.md` supplies the sharper physical-error Gram and the exact noncentral-chi-square worst-bias radius for the fixed Gaussian experiment. The ball here is the elementary rank-deficient specialization; the same observable quotient can use that tighter common construction.

For a scalar physical functional \(l^T\theta\) satisfying \(l\perp\ker F\), the same event gives the simultaneous half-width
\[
\Delta_l=
\bigl(\sqrt{\chi^2_{r_F,1-\alpha}}+\varepsilon\bigr)
\sqrt{l^TF^+l}.
\]
If \(l\) has a component in the kernel, its unconstrained image is unbounded. This is the appropriate directional support \(F\) for the five-coordinate inference framework; a physically declared domain may further restrict that image. A fixed MES/physical body supplies \(Q\), a calibrated event/posterior supplies \(\Pi\), and cross-window maps with the full covariance supply \(G_F\). These layers do not recover a missing detector direction or manufacture a frame calibration.

## 7. Executed finite example

The code uses 12 icosahedral directions, radial plus two orthonormal tangent components, and the positive four-effect tetrahedral qubit POVM \(R_i=(I+a_i\cdot\sigma)/4\). With the orthonormal Hermitian basis \((I,\sigma_x,\sigma_y,\sigma_z)/\sqrt2\), the full design has 144 real measurements for 36 gradient components. Gaussian errors have nonconstant diagonal variances and two known correlated modes. Three common frame-spin columns are profiled. All amplitudes are declared synthetic inverse-time units.

| Measurement | Identifiable real dimension |
|:--|--:|
| Total trace, radial + transverse | 9 |
| Two helicity channels, radial + transverse | 18 |
| Full internal instrument, radial only | 24 |
| Full internal instrument, transverse only | 32 |
| Full internal instrument, radial + transverse | 36 |
| Full instrument with unknown common frame spin | 33 |

The exact six-axis matrix inverse has maximum error \(1.11\times10^{-16}\). Simultaneously conjugating the Hermitian fields and detector effects changes predictions by at most \(2.22\times10^{-16}\). The nuisance-profiled estimator differs from the true identifiable image by \(1.57\times10^{-15}\) on noiseless data.

With 30,000 draws and seed 20261028, the nominal joint 95% region covers 94.970% (Monte Carlo standard error 0.126 percentage points). Adding a fixed whitened remainder of norm 0.4 and using the derived inflated region gives 98.507% coverage (standard error 0.070 percentage points). This conservatism is expected from the triangle bound. It is a guarantee for the specified error class, not a claim of an empirically calibrated astrometric noise law.

The plot goal2_kinematic_design shows rank by instrument choice and second-order convergence of the matrix-log derivative check. The machine-readable result includes the full positive information spectrum and all residuals.

## 8. The scalar magnitude and matrix logarithm must remain distinct

For the unitary single-path law in MF02,
\[
F_o=gUL_eU^\dagger,\qquad \Xi=(\delta U)U^\dagger,\quad
\alpha=\delta\log g,
\]
the supplied identity is
\[
\delta\log(F_o/F_*)=
\alpha I+[\Xi,\log(F_o/F_*)]
+D\log_{F_o}[gU\delta L_eU^\dagger].
\]
It holds for a positive-definite coherency matrix. It is the Fréchet derivative of a matrix function, not a scalar magnitude formula.

For a fixed calibrated effect \(R\), the actual channel response obeys
\[
\delta\log F_R=\frac{\operatorname{tr}(R\,\delta F_o)}
{\operatorname{tr}(R F_o)}.
\]
Generally this differs from \(\operatorname{tr}[R\,\delta\log F_o]\). A changing effect contributes its own \(\operatorname{tr}[(\delta R)F_o]\) term.

The verified example uses
\[
F_o=\operatorname{diag}(2,1),\quad
\Xi=\begin{pmatrix}0&-1/2\\1/2&0\end{pmatrix},\quad
R_x=(I+\sigma_x)/2.
\]
Then \(\delta F_o\) has off-diagonal entries \(1/2\). Total trace and a diagonal analyzer see zero first-order change; \(R_x\) sees \(1/2\). Yet
\[
\delta\log F_{R_x}=1/3,\qquad
\operatorname{tr}(R_x\,\delta\log F_o)=\log2/2.
\]
The central-difference errors in the matrix-log identity decrease by a factor near four each time the step is halved.

This gives a clean physical bridge: scalar flux can hide a relative unitary rotation, while an analyzer sensitive to the affected coherence can observe it. The same rotation is a basis redundancy if state and detector are transformed together. If the source is unpolarized, the commutator vanishes; if source coherence is an unconstrained nuisance, it can mimic or cancel the rotation. Those alternatives belong in the forward likelihood.

## 9. Two paragraphs suitable for the optical manuscript

*The antisymmetric part of the congruence gradient is absent from the directional scalar rate because it is contracted with two copies of the same null direction. The lift used here nevertheless has an immediate representation-theoretic extension. Replacing the polar vector in \(L_Sd=\mathrm{STF}(S\otimes d)\) by an axial vector gives the same contraction and minimum-norm geometry, with pseudotensor rather than polar parity. A physical use of that axial sector requires a parity-sensitive observable and its transfer response; the tensor identity alone does not insert vorticity into the scalar luminosity-distance law. Joint longitudinal and transverse response fields provide a complementary route: when both are calibrated in a common frame, their angular moments recover the full spatial gradient.*

*A polarization-resolved extension can retain the source coherency matrix and the detector transfer map before taking a scalar flux. For a single unitary path the variation of the matrix logarithm contains the commutator with the transported polarization rotation, together with the scalar geometric dilution and the source variation. A calibrated analyzer can therefore retain a relative rotation that total flux removes. Its measured magnitude still involves the logarithm of the detector-contracted flux, whose derivative follows from the same joint observation model. This construction extends the response domain of the retained tensor carrier while preserving the distinction between optical geometry, internal transport and source or frame nuisance.*

These are proposed insertions, not edits of main.pdf. The first fits at the end of the local-response or discussion section; the second belongs in the outlook unless a detector-level worked example is added to the manuscript.

## 10. Concrete continuation and significance

The immediately useful next product is a source-qualified *local* radial/tangential joint fit with a retained calibration nullspace. Reuse the existing R36 selected-source Jacobians, signed STF coordinates, shared seven-component octupole budget and corrected observer chart. Supply the actual paired observable law before interpreting its fitted carrier as \(K\). The latest R36 common E2 PM response constrains \(2c(B_o-B_s)/D-\dot B_o\), with the existing selected-design 80% power radii 1.60963–2.29431 microarcseconds/year; it should be used as that finite-history response rather than renamed instantaneous shear.

For the matrix extension, begin with a declared two-state source/linear optical instrument and retain only the internal effects that the physical target needs. Compare the exact detector likelihood with the retained tensor carrier under the same covariance and source nuisance. Report the confidence image of geometric shear, frame-relative vorticity and internal drift separately, and plot sensitivity to frame calibration and finite-depth remainders. This produces a physical inference result without building a hierarchy solver.

The general inverse and Fisher-rank statements have established linear-algebra/statistical antecedents. The application contribution is the explicit chain from a covariant kinematic response, through the actual detector and frame kernel, to a bounded physical confidence image. The optical manuscript's sharp STF geometry can be reused within that chain, while the new matrix extension supplies additional observables only when the source and analyzer really carry them.

## Primary sources actually consulted

- A. Heinesen, *Multipole decomposition of the general luminosity distance “Hubble law” — a new framework for observational cosmology*, JCAP 05 (2021) 008, arXiv:2010.06534. Primary abstract/publisher record retrieved through Exa; local response compared with the attached manuscript's explicit conventions. https://arxiv.org/abs/2010.06534
- O. H. Marcori, C. Pitrou, J.-P. Uzan and T. S. Pereira, *Direction and redshift drifts for general observers and their applications in cosmology*, Phys. Rev. D 98 (2018) 023517, arXiv:1805.12121. Primary abstract consulted; the qualified R36 translation of Eq.5.13 is reused. https://arxiv.org/abs/1805.12121
- R. Maartens et al., *Covariant cosmography: the observer-dependence of the Hubble parameter*, arXiv:2312.09875v3, primary HTML accessed; R36 optical chart contract retains its equation-specific transformation. https://arxiv.org/html/2312.09875v3
- F. Mignard and S. Klioner, *Analysis of astrometric catalogues with vector spherical harmonics*, A&A 547 (2012) A59, especially §7 for frame rotation, glide and source/systematic assumptions. https://www.aanda.org/articles/aa/full_html/2012/11/aa19927-12/aa19927-12.html
- User attachments: MF02 §§1.2–1.3,1.12,2.7–2.8 and main.pdf §§II–VII. User-source identities are in the parent checkpoint.

