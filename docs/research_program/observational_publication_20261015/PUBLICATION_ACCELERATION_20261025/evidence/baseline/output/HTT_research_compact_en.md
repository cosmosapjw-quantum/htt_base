# Tensor morphology, directional expansion, and kinematic information in cosmological observations

*Sharp quadrupole–octupole bounds, optical coupling, and joint distance and astrometric analyses*

\FloatBarrier

## Abstract

The low-multipole cosmic microwave background (CMB) retains relative orientation and parity information that is lost when the quadrupole and octupole are reduced to their powers. We study the full symmetric trace-free (STF) angular tensors \(Q\in\mathrm{STF}_2(\mathbb R^3)\) and \(O\in\mathrm{STF}_3(\mathbb R^3)\), and the pseudoscalar \(\chi=\det[v,Qv,Q^2v]\), where \(v=O:Q\). For fixed \(Q\) and octupole norm, we derive the exact image ellipsoid of \(v\) and the attained maximum of \(|\chi|\). Optimizing over quadrupole shape then gives the sharp inequality \( |\chi|\le(4\sqrt2/135)\|Q\|_F^6\|O\|_F^3 \), including all equality conditions and an explicit unit-norm witness. The resulting dimensionless coordinate is bounded by one and changes sign under a spatial reflection. Applied to 60 corrected, saved Planck PR3 processed E-mode quadrupole–octupole carriers from one sky, the coordinate is nonzero for every carrier; the primary full-map value is \(-0.09677\), while one matched half-mission value is \(+0.00876\). These values describe processing-sensitive morphology, without an independent-sky frequency interpretation.

The same contraction adjoint gives a second result: a local acceleration--shear coupling generates an optical magnitude octupole, with constructive inversion, a four-dimensional residual subspace and a finite angular remainder bound. We connect these tensor calculations to observations of distances, astrometry and the CMB. On 274 released Cosmicflows-4 distance rows, five-fold joint held-out Gaussian scores reverse the ranking of two angular models as a specified group-dependence covariance changes. For the 628-target frame, 354 unavailable distance outcomes force broad sharp intervals for a fixed out-of-fold residual-tail event. In a 755,850-row extragalactic proper-motion design, profiling 102 nuisance columns retains only \(1.58485\%\) of the six depth-slope trace information. The corresponding generalized information eigenvalues imply principal angles of \(7.115^\circ\)–\(7.499^\circ\) between the whitened slope and nuisance spaces. A common 24-coordinate depth carrier, its 18-coordinate image, and 4,096 Gaussian replicate rows show that cross-bin covariance materially changes both contrast scales and functional exceedance frequencies. An expanded CF4 analysis retains 35,970 groups and four correlated directional-rate windows, with monopole-only values from 74.629 to 70.810 km s$^{-1}$ Mpc$^{-1}$. The selected 274-row law gives an exact Gaussian-model finite-sample radius of 27.0585 for all fifteen coefficients; all four projected STF regions contain zero. Four delivered CMB frequencies retain 96 E/B coordinates, and a separate source-spin quotient gives a conditional Gaussian tail bound of 0.29018 for its nested astrometric comparison. Windowed-flow, two-radius design, and rotating-rest-space identities connect these calculations to the physical interpretation of direction and depth. The joint tensor representation preserves the distinct observation maps and their stated laws.

\clearpage
\setcounter{tocdepth}{2}
\tableofcontents
\clearpage

\FloatBarrier

## 1. The state represented by the sky and the state inferred from it

Low CMB multipoles encode the angular radiation field at an observer. Congruence shear describes the deformation of neighbouring physical worldlines. Both admit an STF rank-two representation, and a physical interpretation connects them through radiation transport, source evolution and the observing window. Our purpose is to retain the shape carried by the observable and to propagate its full uncertainty through the response needed for that interpretation. Multipole-vector and invariant descriptions provide the orientation-aware CMB setting [4–6], while tensor invariant constructions describe the relevant rotational and parity operations [7,8]. The exact result below concerns the attainable range and contraction fibres of one quadrupole–octupole pseudoscalar.

We denote the observable low-multipole state by \(Y_{\rm sky}=(Q_{ab},O_{abc},\ldots)\). A separately typed physical state may contain congruence shear \(\sigma_{ab}\), vorticity \(\omega_a\), acceleration \(A_a\), frame-relative velocities and curvature variables. A useful schematic notation is

$$
X_{\rm phys}=\bigl(\sigma_{ab},\omega_a,A_a;
\boldsymbol\beta_{\rm RO},\boldsymbol\beta_{\rm RM},\boldsymbol\beta_{\rm MO};
\Delta\Omega_k,\ldots\bigr).\tag{1}
$$

Here RO, RM and MO designate radiation–observer, radiation–matter and matter–observer relations. At first order in velocity, \(\boldsymbol\beta_{\rm RO}=\boldsymbol\beta_{\rm RM}+\boldsymbol\beta_{\rm MO}+O(\beta^2)\); this is a frame relation, not an inference of any one term from another. A physical component also needs its congruence, frame, epoch or depth window, averaging scale, units and perturbative branch. For example, the axial vorticity vector is the spatial dual of an antisymmetric rotation tensor, whereas the optical STF coefficient in a distance fit is a polar rank-two object. A pseudoscalar made by contracting an axial and a polar vector changes sign under reflection, while a squared magnitude does not. These representation and parity distinctions determine which comparisons can be made before choosing a scalar summary. A component that has not been supplied has a different mathematical meaning from one measured or constrained to be zero.

The observable analyses below use four different data objects: processed low-\(\ell\) CMB tensors from a single sky; selected galaxy distance moduli; a public supernova covariance subset; and reported-redshift bins of extragalactic proper motions [25,43]. Their likelihoods and processing operations are not interchangeable. We use the complete tensors or coefficient covariance where available, and preserve the dependence induced by repeated use of the same sky, shared galaxy groups, or common depth parameters. The numerical computations were fixed at the source revisions identified in the source note.[^source]

[^source]: The retained 29-page calculation uses [commit 10f3ea585c6608e794900efe7e4f8f42c0747a3b](https://github.com/cosmosapjw-quantum/htt_base/tree/10f3ea585c6608e794900efe7e4f8f42c0747a3b). The expanded observational account uses the [140-page source report at 4aebcc082175e2ec93bd76e754a30d6fd7e2ea50](https://github.com/cosmosapjw-quantum/htt_base/tree/4aebcc082175e2ec93bd76e754a30d6fd7e2ea50/docs/research_program/observational_publication_20261015/REPORT_20261024_REV1) and the [selected-tensor-law manuscript at c9df63efa4728255a5b785ad7cb752ecb8d8f3ef](https://github.com/cosmosapjw-quantum/htt_base/tree/c9df63efa4728255a5b785ad7cb752ecb8d8f3ef/docs/research_program/observational_publication_20261015/P1_SELECTED_TENSOR_LAW_20261024). Additional mathematical constructions are retained on [the branch at 2f10fbd64cfd0810a976bf2720186fd56b7bfde7](https://github.com/cosmosapjw-quantum/htt_base/tree/2f10fbd64cfd0810a976bf2720186fd56b7bfde7). The companion source index separates source-reported results from the numerical calculations performed for this article.

\FloatBarrier

## 2. From full harmonic coordinates to a parity-sensitive tensor

Let \(T_2(\hat n)=Q_{ab}n^an^b\) and \(T_3(\hat n)=O_{abc}n^an^bn^c\), where \(Q_{ab}=Q_{(ab)}\), \(Q^a{}_a=0\), \(O_{abc}=O_{(abc)}\), and \(O^a{}_{ac}=0\). We use full Frobenius contractions over all ordered tensor indices. For orthonormal real harmonics, the normalization is

$$
Q:Q={15\over8\pi}\|c_2\|_2^2={75\over8\pi}C_2,
\qquad
O:O={35\over8\pi}\|c_3\|_2^2={245\over8\pi}C_3.\tag{2}
$$

The tensors have temperature units when the harmonic coefficients do. Equation (2) is an observable conversion, unrelated to the Hubble-normalized physical shear used later. In particular, an independent-component norm of \(O\) is not the Frobenius norm: an \(O_{112}\) term occurs three times in the full contraction and an \(O_{123}\) term six times.

Fix an orientation of Euclidean three-space and define

$$
v_i=O_{ijk}Q_{jk},\qquad
K_{QO}=[v,Qv,Q^2v],\qquad
\chi(Q,O)=\det K_{QO}.\tag{3}
$$

If \(R\in O(3)\) acts by \(Q\mapsto RQR^{\mathsf T}\) and \(O\mapsto R^{\otimes3}O\), contraction gives \(v\mapsto Rv\). All three columns of \(K_{QO}\) therefore rotate together, yielding \(\chi(RQ R^{\mathsf T},R^{\otimes3}O)=\det(R)\chi(Q,O)\). A proper rotation preserves \(\chi\), whereas reflection reverses its sign. In particular, inversion maps \((Q,O)\) to \((Q,-O)\); both pairs have the same powers and many even contractions. When \(\chi\ne0\), no proper rotation maps one pair to the other. This supplies a constructive witness of mirror separation. If \(v\) misses a principal direction of \(Q\), the determinant can vanish even though another parity-odd functional may survive. Tensor-moment constructions and their blind spots are discussed in [9–11].

There is a useful orbit-geometric interpretation. At a generic quadrupole–octupole pair the two STF spaces have dimensions five and seven; quotienting by a locally free three-dimensional proper-rotation action leaves nine dimensions. For a cyclic \(K_{QO}\), the ordered Krylov columns give a coordinate chart for the projected pair \((Q,v)\), retaining its shape and orientation. The full octupole additionally carries the contraction-fibre coordinates described in Appendix A. Its Gram matrix is fixed by moments \(v^{\mathsf T}Q^rv\), and the sign of \(\det K_{QO}\) selects the orientation of a reconstructed representative. This construction has a declared chart domain. Repeated eigenvalues, a vanishing contraction component, zero tensors and ill-conditioned cyclic matrices require their own strata rather than a fabricated axis. The sharp inequality we now derive applies to every finite real STF pair, including those where the cyclic chart is unavailable.

\FloatBarrier

## 3. An attained chirality envelope

**Theorem 1 (fixed-quadrupole image and sharp joint envelope).** Let \(Q\ne0\) be a real symmetric trace-free rank-two tensor and \(O\) a real fully symmetric trace-free rank-three tensor in oriented Euclidean three-space. Set \(t=\operatorname{tr}Q^2\), \(j=\operatorname{tr}Q^3\), \(o=\|O\|_F\), and \(v=O:Q\). For a fixed \(Q\), the exact image of the sphere \(\|O\|_F=o\) under \(O\mapsto v\) is the solid ellipsoid

$$
v^{\mathsf T}M_Q^{-1}v\le o^2,
\qquad M_Q={t\over3}I+{2\over5}Q^2.\tag{4}
$$

In a positively oriented orthonormal eigenframe of \(Q\), write \(\lambda_i\) for its eigenvalues and \(V(\lambda)=\prod_{i<k}(\lambda_k-\lambda_i)\). Then the exact fixed-\(Q\) maximum is

$$
\max_{\|O\|_F=o}|\chi(Q,O)|
={|V(\lambda)|\sqrt{\det M_Q}\over3\sqrt3}\,o^3.\tag{5}
$$

Across all \(Q,O\), the homogeneous inequality

$$
\boxed{|\chi(Q,O)|\le{4\sqrt2\over135}\|Q\|_F^6\|O\|_F^3}\tag{6}
$$

is sharp. For simple-spectrum \(Q\) and \(o>0\), equality in (5) occurs exactly when the normalized contraction energy is equally divided among its three eigen-directions and \(O\) has no component in the contraction kernel. Global equality in (6) additionally requires \(j=0\). If \(Q\) has repeated eigenvalues, \(\chi=0\) for every \(O\), and every \(O\) attains the zero fixed-\(Q\) maximum.

*Proof.* Define the linear contraction \(L_Q:\mathrm{STF}_3\to\mathbb R^3\) by \(L_QO=O:Q\). Its Frobenius adjoint is the STF projection of the symmetrized product of \(w\in\mathbb R^3\) and \(Q\):

$$
(L_Q^*w)_{ijk}
={w_iQ_{jk}+w_jQ_{ik}+w_kQ_{ij}\over3}
-{2\over15}\{\delta_{ij}(Qw)_k+\delta_{ik}(Qw)_j+\delta_{jk}(Qw)_i\}.\tag{7}
$$

The trace of the first term is \(2Qw/3\), while the trace of the bracket is \(5Qw\). Thus (7) is trace-free. Contracting it against a symmetric trace-free \(O\) eliminates the delta terms and returns \(w\cdot (O:Q)\), verifying the adjoint. A second contraction with \(Q\) yields

$$
L_QL_Q^*w
={t\over3}w+{2\over3}Q^2w-{4\over15}Q^2w
=\left({t\over3}I+{2\over5}Q^2\right)w.\tag{8}
$$

Because \(t>0\), \(M_Q=L_QL_Q^*\) is positive definite. The contraction map is onto \(\mathbb R^3\), and its kernel has dimension \(7-3=4\). Every \(O\) producing a specified \(v\) has the unique orthogonal decomposition

$$
O=L_Q^*M_Q^{-1}v+K_0,
\qquad K_0\in\ker L_Q,
\qquad \|O\|_F^2=v^{\mathsf T}M_Q^{-1}v+\|K_0\|_F^2.\tag{9}
$$

The inequality in (4) is necessary. It is sufficient as well: select any kernel vector of squared norm \(o^2-v^{\mathsf T}M_Q^{-1}v\). Thus the full solid ellipsoid, not merely its boundary, is attained at the fixed octupole norm.

In the positively oriented eigenframe, \(M_Q\) is diagonal with \(m_i=t/3+2\lambda_i^2/5\). The determinant in (3) is

$$
\chi=v_1v_2v_3
(\lambda_2-\lambda_1)(\lambda_3-\lambda_1)(\lambda_3-\lambda_2).\tag{10}
$$

Write \(y_i=v_i/\sqrt{m_i}\). From (4), \(\sum_i y_i^2\le o^2\). Applying arithmetic–geometric mean to \(y_1^2,y_2^2,y_3^2\) gives \(|y_1y_2y_3|\le o^3/(3\sqrt3)\). Equality requires \(|y_i|=o/\sqrt3\) for each \(i\), exhausting the ellipsoid radius. Consequently \(K_0=0\) in (9), and \(O=L_Q^*M_Q^{-1}v\) is a constructive equality tensor. The eight sign choices for the \(v_i\) give both signs of the extremal determinant. This proves (5), including attainability.

Trace freedom and the cubic discriminant eliminate the individual eigenvalues:

$$
V(\lambda)^2={t^3\over2}-3j^2,
\qquad
\det M_Q={64t^3\over675}+{8j^2\over1125},
\qquad 0\le {j^2\over t^3}\le{1\over6}.\tag{11}
$$

For \(r=j^2/t^3\), the squared shape factor in (5), after extracting \(t^6o^6/27\), is \((1/2-3r)(64/675+8r/1125)\). Its derivative is \(-(316+48r)/1125<0\) throughout the allowed interval. The maximum occurs at \(j=0\), with eigenvalues \((-\sqrt{t/2},0,\sqrt{t/2})\) up to permutation. Substitution into (5) gives (6). To show that the global constant cannot be reduced, take

$$
Q_*=\operatorname{diag}(-1/\sqrt2,0,1/\sqrt2),
\quad w_*=(\sqrt{10}/4,1,\sqrt{10}/4),
\quad O_*=L_{Q_*}^*w_*.
$$

Direct contraction gives \(\|Q_*\|_F=\|O_*\|_F=1\) and \(\chi(Q_*,O_*)=4\sqrt2/135\). Replacing \(O_*\) by \(-O_*\) attains the negative endpoint. \(\square\)

![Analytic unit-norm STF quadrupole and octupole fields, their joint angular field attaining the positive endpoint, and its spatial reflection attaining the negative endpoint. Reflection changes the pseudoscalar sign while preserving the norm constraints.](../figures/fig08_tensor_mirror.png)

For nonzero tensors the theorem defines a bounded, parity-odd shape coordinate

$$
\mathcal C(Q,O)
={135\chi(Q,O)\over4\sqrt2\|Q\|_F^6\|O\|_F^3}
\in[-1,1].\tag{12}
$$

The homogeneity \(\chi(aQ,bO)=a^6b^3\chi(Q,O)\) shows why these powers remove overall amplitudes. A fixed-\(Q\) utilization, \(|\chi|/\chi_{\max}(Q,o)\), uses the more informative denominator (5) when the spectrum is simple and \(o>0\). A zero tensor remains a separate stratum where (12) is undefined. Nonzero \(\mathcal C\) is sufficient to distinguish the two proper-rotation orbits of a mirror pair; zero \(\mathcal C\) is inconclusive about chirality. The bound normalizes the observable shape independently of a stochastic reference law.

![The solid curves give the sharp fixed-quadrupole envelope as a function of \(j^2/t^3\), and the dotted lines give the attained global endpoints. Circles and squares show all primary and pilot processing configurations; the right panel enlarges their observed range.](../figures/fig01_chirality_envelope.png)

\FloatBarrier

## 4. Processing-sensitive CMB morphology on one sky

### 4.1 Stored carrier and normalization

The finite CMB application uses the corrected saved rank-two and rank-three STF carriers obtained from a masked, delivered QU polarization product. The retained E pseudo-\(a_{\ell m}\) coefficients are *processed-map* quantities: their definition includes the common sky, mask and polarization processing. The real Galactic harmonic convention is Condon–Shortley with coordinates \((a_{\ell0},\sqrt2\operatorname{Re}a_{\ell m},-\sqrt2\operatorname{Im}a_{\ell m})\). The registered independent coordinates are

$$
\begin{aligned}
q&=(Q_{xx},Q_{yy},Q_{xy},Q_{xz},Q_{yz}),\\
o_{\rm ind}&=(O_{xxx},O_{xxy},O_{xxz},O_{xyy},O_{xyz},O_{yyy},O_{yyz}).
\end{aligned}
$$
 Symmetry and trace freedom complete all remaining entries before any contraction. The two computational scales are the exact rational values \(q_0=o_0=10^{-5}\,\mathrm K_{\rm CMB}\), used to make the stored temperature tensors dimensionless. These fixed scales cancel from the amplitude-free shape coordinate.

The 60 carriers consist of 15 retained primary product/band combinations and 45 pilot-cache processing variations on the same observed PR3 sky. The main \(\ell_{\max}=32\) carrier and the \(64,128\) cuts, zero-window and secondary-window products permit a sensitivity comparison. All 60 saved completed tensors have nonzero exact \(\chi\); 15 signs are positive and 45 negative. The primary full \(\ell_{\max}=32\) tensor gives \(\mathcal C=-0.0967707\), \(j^2/t^3=0.0582918\), a fixed-\(Q\) envelope equal to \(0.808141\) times the global envelope, and fixed-\(Q\) utilization \(0.119745\). The first half-mission at the same registered processing gives \(\mathcal C=+0.00876054\). Thus a change in product can change the parity-odd coordinate even while both finite tensors individually satisfy the sharp inequality. The comparison holds the observed sky fixed while changing its processing.

There are 93 registered same-sky pair comparisons: 48 split/full comparisons at common settings, 15 pinned-primary versus pilot zero-window comparisons, and 30 pilot-window versus zero-window comparisons. Their recorded sign-change counts are 18, 0 and 3, respectively. The absence of sign changes in the middle comparison concerns only that particular source/processing pairing; the 18 split/full changes show that a sign is not globally invariant across the processing family. A sign count alone also suppresses magnitude: a carrier close to the zero-chirality stratum can change sign under a modest perturbation while two larger opposite values pose a different noise-calibration question. This is why the continuous bounded coordinate and the conservative radius certificate are reported alongside signs. The plotted heat map uses the newly bounded \(\mathcal C\), keeping products and windows as discrete processing choices. The earlier supplementary scalar \(\chi/m^9\), \(m^2=\|Q\|_F^2+\|O\|_F^2\), is not the same normalization: it remains sensitive to the quadrupole-to-octupole amplitude ratio. Reporting both exact definitions prevents an apparent change of numerical scale from being mistaken for new physical data.

![The bounded chirality coordinate of saved PR3 processed E carriers changes across products and windows applied to the same observed sky. A cell is a deterministic tensor calculation, and the product grid is not a collection of independent sky realizations.](../figures/fig02_chirality_processing.png)

### 4.2 Stability of a finite sign and the processing response

The recorded processing analysis also supplies a conservative perturbation certificate. On a joint Frobenius ball with radius \(m\), the three columns \(v,Qv,Q^2v\) have norms bounded by \(m^2,m^3,m^4\). Differentiating each column and applying determinant multilinearity with Hadamard's inequality gives \(|D\chi[h]|\le6m^8\|h\|\). A perturbation of norm at most \(r=\rho m\) is confined to the ball of radius (m+r); its sign is certainly unchanged whenever

$$
\chi^2>36\rho^2(1+\rho)^{16}(m^2)^9.\tag{13}
$$

All 60 finite carriers meet this sufficient condition at zero radius and at the hypothetical \(\rho=10^{-6}\) radius. Thirty-nine meet it at \(10^{-5}\), and none meet it at \(10^{-4},10^{-3}\), or \(0.05\). Failure of the sufficient condition does not demonstrate an actual sign reversal. The radii are mathematical scenarios, not measured foreground or instrumental uncertainties. The sensitivity summary records the exact numbers passing each sufficient certificate, 60, 60, 39, 0, 0, 0 for the six radii in order. These are nested scenarios on stored tensors, rather than six estimates of a true error scale. A later empirical error model could put probability mass on perturbations, but would still need the joint processing law to convert a deterministic sign condition into a coverage statement. The exact arithmetic starts with saved binary64 components and therefore cannot undo uncertainty or approximation incurred before those components were stored.

![Counts satisfying the sufficient chirality sign certificate at six hypothetical relative Frobenius radii, beside sign changes in registered same-sky processing pairs. An unsuccessful radius does not assert that a reversal occurred.](../figures/fig09_chirality_certificates.png)

For physical attribution, the local radiation–observer boost response must be kept separate from global matter tilt. A full-sky Lorentz transformation of temperature supplies one concrete radiation–observer lane, but does not by itself determine the map from congruence shear, global velocity or a Bianchi geometry to the tensor pair. Cut-sky processing adds a second problem. Let \(J\) be the low-source response Jacobian after the chosen sequence of boost, beam, pixel transfer, mask, joint harmonic fit and commonization. If \(K^{\rm hi}(L)\) spans a declared high-source nuisance image \(\mathcal H(L)\), then the rank of the identifiable low-source projection obeys the exact identity

$$
\operatorname{rank}\bigl(P_{\mathcal H(L)^\perp}J\bigr)
=\operatorname{rank}[K^{\rm hi}(L)\;J]-\operatorname{rank}K^{\rm hi}(L).\tag{14}
$$

The image is nested as the unrestricted high-source cutoff \(L\) increases. Its column count alone does not certify containment or a surviving rank. The registered continuum wide-mask calculation and a finite-pixel matched-control calculation have distinct operators; an exact axial continuum certificate is not an identity for every finite mask. Equation (14) is useful precisely because it identifies the object that a mask- and covariance-matched analysis has to estimate. Similarly, a CMB tail rank requires a full data-to-statistic rule applied equivariantly to the observation and matched reference skies, including harmonic extraction, chart failure and processing selection. The reference ensemble must therefore retain this complete processing law.

\FloatBarrier

### 4.3 Proper-rotation distance and conditional reference laws

The complete processed E quadrupole and octupole support a morphology comparison beyond their scalar powers. In the computational norm

$$
 \|v\|^2=\frac{\|T_2\|_F^2}{q_0^2}+
 \frac{\|T_3\|_F^2}{o_0^2},\qquad
 q_0=o_0=10^{-5}\,\mathrm K_{\rm CMB},
$$

define \(d_{\mathrm{SO}(3)}(v,w)=\min_R\|v-\rho(R)w\|\), where the minimum is over proper spatial rotations. This distance remains defined at zero tensors and degenerate eigenvalues, where an axis-based summary may be unstable. Admitting reflections instead would identify mirror pairs and change the morphology target.

At the primary cutoff 32, the four split/full lower certificates range from \(0.01265095\) to \(0.01801714\); evaluated proper rotations give upper bounds between \(0.01950063\) and \(0.02826828\). The lower endpoint uses invariants, while the upper endpoint uses a feasible rotation. No locally optimized upper value is called a certified global optimum. A phase intervention preserves both scalar powers to relative \(2.22\times10^{-16}\), but has the positive orbit lower bound \(2.6241071\times10^{-5}\) and feasible upper bound \(0.0114591541\). Power equality therefore leaves distinct proper-rotation morphologies even in this finite pair.

![Proper-rotation orbit-distance enclosures for four split/full pairs and the power-preserving phase control. The endpoints are invariant lower certificates and feasible-rotation upper bounds, rather than error bars or sampling confidence intervals. The phase-control lower endpoint is positive although small on the displayed common scale.](../figures/added_cmb_orbits.png)

This is one observed sky with several processed views. A split difference does not isolate the common CMB field from a common foreground: the simultaneous transformation \(g\mapsto g+h\), \(f_{\rm common}\mapsto f_{\rm common}-h\) leaves all splits unchanged. If two tensor errors are separately bounded by \(r_1,r_2\), the orbit triangle inequality widens \([L,U]\) to \([(L-r_1-r_2)_+,U+r_1+r_2]\). In the retained primary-cutoff sensitivity, all four lower certificates remain positive at relative radius 0.10 and reach zero by 0.25. A zero lower certificate means loss of discrimination by that certificate. The shared contaminant remains one common unknown across the pairs.

#### Equal Gram matrices do not determine the reference law

Arrange the sixty processed harmonic views as columns of \(X_\ell\), with Gram matrix \(G_\ell=X_\ell^TX_\ell\). One constructed law applies a shared spatial rotation \(D_\ell(R)\) to every view at each multipole, independently between \(\ell=2\) and 3. A second applies a shared Haar orthogonal matrix in the full five- or seven-dimensional coefficient space. Both preserve \(G_\ell\), and both have second moment

$$
 \mathbb E Y_{\ell,aj}Y_{\ell,bk}
 =\delta_{ab}\frac{(G_\ell)_{jk}}{2\ell+1}.
$$

Their full laws differ. A spatial rotation preserves the intrinsic STF shape of each multipole; a general coefficient-space orthogonal transformation need not. Thus Gram preservation and isotropic second moments do not specify a physical null law. The distinction between isotropy and stronger Gaussian coefficient properties is established in spherical random-field theory [39].

A separate 4096-draw pilot fixes the statistic transformation. Each law then uses 16,383 evaluation draws and one family statistic across its dependent views. The retained weak-tail results are

| Constructed law | Evaluation counts at least as large | Add-one rank | 99% Monte Carlo interval |
|---|---:|---:|---:|
| Shared spatial rotations | 7505 | 0.4581298828125 | [0.4480529, 0.4681651] |
| Shared Gram-preserving orthogonal actions | 7456 | 0.45513916015625 | [0.4450681, 0.4651698] |

Each rank is \((1+k)/(16383+1)\). Similar ranks for this statistic do not establish equality of the laws. The family statistic also remains attached to its named pilot transformation and reference law; masks, foregrounds and processing have not been shown invariant under those actions. These are conditional reference comparisons, rather than a calibrated low-multipole anomaly significance.

![Retained original comparison of spatial-rotation and Gram-preserving reference laws. The histograms and lower-panel shape projections retain all sixty correlated views in their inherited order. Their reference ranks concern constructed conditional laws on processed E pseudoalms of one sky.](../figures/added_cmb_gram.png)

### 4.4 Spectral information retained by a cleaned map

The frequency dependence needed to assess contamination can be lost before tensor morphology is computed. For each E/B field and multipole, the retained seven-frequency SMICA weights map a vector \(s\) to \(y=w^Ts\). They already include the specified beam and recalibration operations. We do not reset their sums to unity. The component-separation methodology and delivered polarization products are described by the Planck Collaboration [40].

For quadrupole and octupole together, across E and B, the input has \(7\times2\times(5+7)=168\) real coordinates and the output has \(2\times(5+7)=24\). Its block operator has rank 24 and kernel dimension 144. A frequency contrast \(a^Ts\) is recoverable from this compressed map for every \(s\) if and only if \(a\) belongs to its row space. Otherwise the explicit lost direction

$$
 h=\left(I-\frac{ww^T}{w^Tw}\right)a
$$

satisfies \(w^Th=0\) and \(a^Th=\|h\|^2>0\). Two source frequency vectors separated by \(h\) give the same cleaned coefficient but different values of the requested contrast.

For the tested pairwise frequency differences, the lost Euclidean norm fraction ranges from \(0.747908\) to \(0.999913\) in E, and from \(0.816872\) to \(0.999969\) in B. Each tested individual-frequency coordinate also has a nonzero lost component. The metric is Euclidean on the seven processed-frequency coordinates. These fractions measure compression, not foreground amplitudes, noise fractions or probabilities.

![Lost Euclidean norm fractions for the twenty-one pairwise differences among seven frequency channels, evaluated separately for E2, E3, B2 and B3 using the retained SMICA weights. The calculation characterizes the compression operator; it is not a seven-frequency sky measurement.](../figures/added_spectral_compression.png)

Actual frequency maps and a justified spectral-response model can supply information absent from the cleaned map [42]. This calculation does not replace them. In particular, the reported acquisition of all frequency inputs does not constitute a completed seven-frequency tensor result. The spectral kernel, the same-sky orbit comparisons and the astrometric response calculations identify distinct parts of the observational map. A physical joint inference must retain their source and processing relations before projecting to expansion, shear, vorticity or a Bianchi response.

### 4.5 Four delivered frequency fields on one support

A separate delivered-map projection supplies actual frequency contrasts alongside the compression calculation. The 30, 44, 70 and 100 GHz polarization maps were projected at their delivered pixel resolution on the same 30,021 selected cells. Each frequency retains all 24 real E2/E3/B2/B3 coordinates, giving 96 coordinates in total. The projection did not downgrade, smooth or deconvolve the Q/U maps. The delivered beams, foregrounds, pixelization and selected support therefore remain part of these pseudo-modes [40].

The six Euclidean contrast norms, in \(\mu\mathrm K_{\rm CMB}\), are 13.988940 (30–44), 17.227956 (30–70), 17.218702 (30–100), 3.410911 (44–70), 3.750079 (44–100) and 1.620688 (70–100). These differences retain the full 24-coordinate response; a scalar cleaned map cannot reconstruct them through the rank-24 operator above. Their frequency ordering provides an observed morphology input for a spectral model. A fit of that model would use its beams and joint noise/foreground law rather than interpreting the differences as pure foreground amplitudes.

![Six source-reported four-frequency contrasts, replotted in microkelvin. Every cell uses the full 24 real E2/E3/B2/B3 harmonic coordinates on the same selected support. The diagonal marks identical fields. This is a delivered-map comparison, with no new map projection or common-beam correction in the present calculation.](../figures/added_four_frequency.png)


### 4.6 An orientation generator from a tensor response

A static morphology and the rotation of that morphology along a registered path are different tensor functionals. Suppose a real symmetric tensor \(M\) has a measured symmetric response \(R=[M,W]\), where \(W^T=-W\) is an infinitesimal orientation generator in the chosen sign convention. In an orthonormal eigenframe of \(M\),

$$
R_{ij}=(\lambda_i-\lambda_j)W_{ij}.
$$

For simple spectrum, the off-diagonal response determines the three entries of \(W\). A repeated eigenvalue leaves the corresponding rotation invisible. This statement concerns the response supplied to the equation: in a moving eigenframe, eigenvalue changes and frame transport must be separated before assigning a physical rotation to \(W\).

There is a useful perturbation result without choosing a noisy eigenaxis by hand. Suppose \(\widehat M\) is symmetric, \(\widehat R\) is the supplied response, \(\|\widehat M-M\|_{\rm op}\leq\epsilon_M\), \(\|\widehat R-R\|_F\leq\epsilon_R\), and \(\|W\|_F\leq W_*\). Let \(\widehat W\) be the global least-squares solution over skew matrices and let \(\widehat\delta=\min_{i<j}|\widehat\lambda_i-\widehat\lambda_j|>0\). Then

$$
\|\widehat W-W\|_F
\leq\frac{\epsilon_R+2\epsilon_M W_*}{\widehat\delta}.
$$

To see this, the residual at the true \(W\) is
\(\widehat R-[\widehat M,W]=(\widehat R-R)-[\widehat M-M,W]\), whose norm is bounded by the numerator. Least squares projects this residual orthogonally onto the range of the commutator map. The squared norm of that map on skew matrices is a sum of \((\widehat\lambda_i-\widehat\lambda_j)^2W_{ij}^2\), so its smallest singular value is \(\widehat\delta\). Dividing proves the bound. Ordered eigenvalue perturbation also gives \(\widehat\delta\geq\delta-2\epsilon_M\).

This calculation supplies a stable orientation diagnostic when a tensor response and a nonzero spectral gap are available. It complements the static orbit distance: the latter compares full fields without choosing axes, whereas the response estimate resolves an infinitesimal generator with an explicit gap-dependent error. A sequence of processing windows does not by itself provide a physical time derivative. For a depth path, the transport convention and response remain part of the target.


\FloatBarrier

## 5. Conditional physical anchors and the signed comparator budget

A kinematical interpretation requires a stated congruence and response. Let \(H=\Theta/3>0\), \(\Sigma^2=\sigma_{ab}\sigma^{ab}/(6H^2)\), and \(W^2=\omega_{ab}\omega^{ab}/(6H^2)\). For a declared curvature comparator, a fluid rest-energy normalization \(\Omega\), equation-of-state ratio \(w\), and rapidity \(\rho\), we retain the signed functional

$$
x_C:=\Sigma^2-W^2+(1+w)\Omega\sinh^2\rho
 +(\Omega_k-\Omega_{k,\mathrm{ref}}).\tag{15}
$$

The minus sign and the signed curvature difference permit cancellation between nonzero sectors. Equation (15) defines a comparator functional. Its identification with a density deficit follows only after the frame, curvature contraction, Einstein constraint, and energy split are specified. The following derivation makes that requirement explicit. A hypersurface-normal comparator and a rotating matter-rest comparator occupy different domains.

The Maartens–Ellis–Stoeger (MES) programme instead provides conditional one-way bounds on kinematics from the radiation multipoles [1–3]. In a consistent temperature harmonic normalization, let

$$
\epsilon_2={1\over T_0}\sqrt{75C_2\over8\pi},
\quad \epsilon_3={1\over T_0}\sqrt{245C_3\over8\pi},
\quad B_\sigma={5\over3}\epsilon_1+3\epsilon_2+{3\over7}\epsilon_3,
\quad B_\omega={10\over3}\epsilon_1+{2\over15}\epsilon_2.\tag{16}
$$

With the source's full tensor norm, the expanding geodesic branch and common \(H=\Theta/3\) rate convention imply \(\Sigma^2<3B_\sigma^2/2\) and \(W^2<3B_\omega^2/2\). The factor \(3/2\) follows from \(\Theta^2/(6H^2)\). These expressions use *radiation temperature* multipole amplitudes and a stipulated residual cosmological dipole. The processed polarization E tensors in Section 4 are not the \(\epsilon_\ell\) in (16). Moreover, the all-observer/Copernican extension, frame, derivative-hierarchy reduction and dipole attribution are physical premises of the bound; an observed \(C_2,C_3\) in one sky do not prove them. Even the ordering \(B_\sigma>B_\omega\) follows only when \(\epsilon_1<43\epsilon_2/25+9\epsilon_3/35\). On the geodesic branch \(A_a=0\) is a model condition, rather than a separately observed numerical acceleration ceiling.

For matched, positive-radius Euclidean blocks \(B_j=\{x_j:\|x_j\|\le R_j\}\), the gauge of their product satisfies \(\rho_{\prod B_j}(x)=\max_j\|x_j\|/R_j\). A violation in one kinematical block cannot cancel an excess in another through the signed sum (15). This product formula applies to the factorized anchor, not automatically to its intersection with an observational response. More generally, for a physical domain \(D_\eta\), premise-conditioned MES body \(B_{\rm MES}(y;\eta)\), response \(\mathcal R_\eta\) and compatible-observation region \(C_y(\eta)\), the joint feasible object is

$$
\Theta(y;\eta)=D_\eta\cap B_{\rm MES}(y;\eta)
\cap\mathcal R_\eta^{-1}\bigl(C_y(\eta)\bigr).\tag{17}
$$

A data-derived anchor and compatibility region built from the same sky are two constraints in this one joint problem, not independent factors in a likelihood. With an exact linear response, a feasible point \(X_0\) is unique exactly when no nonzero \(h\in\ker\mathcal R_\eta\) leaves \(X_0+h\) in the physical feasible body. Noise adds a separate sampling-law and coverage question [13,14]. This construction places the physical restrictions and the observed tensor response in the same state space.

\FloatBarrier

### 5.1 Congruence and curvature contraction

In this geometric subsection we set \(c=1\), use signature \((-+++)\), and normalize \(u^au_a=-1\). Let \(h_{ab}=g_{ab}+u_au_b\), and decompose the projected velocity gradient as
$$
V_{ab}=h_a{}^ch_b{}^d\nabla_cu_d
      =\frac{\theta}{3}h_{ab}+\sigma_{ab}+\omega_{ab},
\qquad H=\theta/3.
$$
Here \(\sigma_{ab}\) is symmetric and trace free and \(\omega_{ab}\) is antisymmetric. Consequently,
$$
V_{ab}V^{ab}=\frac{\theta^2}{3}+\sigma_{ab}\sigma^{ab}
                         +\omega_{ab}\omega^{ab},\qquad
V_{ab}V^{ba}=\frac{\theta^2}{3}+\sigma_{ab}\sigma^{ab}
                         -\omega_{ab}\omega^{ab}.
$$
The distinction between these contractions matters whenever the rest distribution rotates.

In a compatible orthonormal frame, write \(A_C\) for the projected rest-bundle connection and \(c^E{}_{CD}\) for the frame bracket. Its curvature uses the full bracket:
$$
\mathcal R_{CD}
=e_CA_D-e_DA_C+[A_C,A_D]-c^E{}_{CD}A_E.
$$
Dropping the vertical bracket produces another expression, related by
$$
\mathcal R_{kl}=\mathcal R^{\rm drop}_{kl}
                   -2\omega_{kl}A_0.
$$
The full expression transforms by conjugation under a change of spatial triad. The dropped expression acquires the corresponding time-dependent triad-spin term. It therefore cannot be assigned the same intrinsic meaning when \(\omega\ne0\).

Let \(R_{\rm proj}\) denote the stated spatial double contraction of the spacetime Riemann tensor. With the curvature and slot conventions used here, the full-bracket Gauss scalar is
$$
R_{\rm rest}=R_{\rm proj}-\theta^2+V_{ab}V^{ba},
$$
whereas the same-order expression is
$$
R_{\rm same}=R_{\rm proj}-\theta^2+V_{ab}V^{ab}
            =R_{\rm rest}+2\omega_{ab}\omega^{ab}.
$$
For example, take a pure antisymmetric spatial gradient with
\(\omega_{12}=w=-\omega_{21}\). Then
\(\omega_{ab}\omega^{ab}=2w^2\), and the scalar difference is \(4w^2\).
At \(\omega=0\) the two expressions coincide.

This also specifies what is required before a signed comparator becomes an Einstein constraint identity. If the adopted Einstein contraction supplies
\(R_{\rm proj}=2\kappa\rho_u+2\Lambda\), substitution gives
$$
1=\Omega_{\rho_u}+\Omega_\Lambda+\Omega_k
        +\Sigma^2-W^2,
\quad
\Omega_k=-\frac{R_{\rm rest}}{6H^2},\quad
\Sigma^2=\frac{\sigma_{ab}\sigma^{ab}}{6H^2},\quad
W^2=\frac{\omega_{ab}\omega^{ab}}{6H^2},
$$
with \(\Omega_{\rho_u}=\kappa\rho_u/(3H^2)\) and
\(\Omega_\Lambda=\Lambda/(3H^2)\). This requires \(H\ne0\).
Writing \(\rho_u=\rho_{\rm base}+\rho_{\rm tilt}\) further requires an explicit energy split. A density deficit relative to a comparator is then obtained by subtracting the two specified constraints. The subtraction is not an identity supplied by the signed functional alone.

Using \(R_{\rm same}\) instead changes the curvature parameter:
\(\Omega_k^{\rm same}=\Omega_k-2W^2\). With that parameter the same constraint reads
$$
1=\Omega_{\rho_u}+\Omega_\Lambda+
                   \Omega_k^{\rm same}+\Sigma^2+W^2.
$$
Thus a change of contraction cannot leave both the curvature definition and the displayed vorticity sign untouched. These formulas are direct consequences of the declared conventions, rather than interchangeable curvature notations.

There is a separate restriction for a hypersurface normal. If
\(n_a=-N\partial_at\), \(N>0\), the Hessian of \(t\) is symmetric and the connection is torsion free. Hence
$$
\nabla_{[a}n_{b]}=(\partial_{[a}\log N)n_{b]},
\qquad h_a{}^ch_b{}^dn_d=0,
$$
so \(\omega_{ab}[n]=0\). A comparator defined on \(n\) cannot independently vary its vorticity sector.

For a concrete illustration, the algebraic box
$$
\Sigma^2=.12,\quad W^2\in[0,.04],\quad
\Omega_{\rm tilt}=.03,\quad \Omega_k\in[0,.02]
$$
gives \(x_C=\Sigma^2-W^2+\Omega_{\rm tilt}+\Omega_k\in[.11,.17]\).
For the specified hypersurface-normal constraint construction, however,
\(W^2[n]=0\), so values below \(.15\) are excluded before evolution is considered. The algebraic lower corner cannot be restored by replacing vorticity with another sector. An instantaneous Bianchi-V constraint witness realizes the upper value \(.17\); local or global development requires additional dynamical arguments. The rotating matter congruence \(u\) is a different construction and requires a frame-consistent bridge.



For the remaining observational formulas we restore the explicit powers of \(c\). The rest-bundle statements above concern compatible one-event connection and frame data; an evolving homogeneous solution imposes additional field equations.

### 5.2 Relative velocity and the orbit normal

A covariant derivative channel is \(J=h\nabla_XU\), with
\(J-h\partial_XU=h\Gamma_XU\). It is not automatically a measured proper motion. In a declared flat, instantaneous, low-velocity model at distance \(D>0\), the tangential drift is
$$
\mu=P_n(Sn)+(\omega-\Omega_{\rm frame})\times n
                       +D^{-1}P_ne.
$$
Thus isotropic expansion is invisible, intrinsic rotation is degenerate with frame spin, and non-comoving residuals introduce inverse-distance dependence. Optical propagation and relativistic corrections need their own remainder control; the source does not supply an empirical calibration.

Orbit-normal tilt instead uses independently supplied spacelike generators with positive-definite Gram matrix, their future unit normal \(N\), and future unit \(u\):
$$
\gamma_{uN}=-g(u,N),\qquad
\beta_{uN}^2=1-\gamma_{uN}^{-2}.
$$
Reverse Lorentz Cauchy–Schwarz gives
\(\gamma_{uN}=1\iff\beta_{uN}=0\iff u=N\).
A passive common coordinate change preserves this contraction. Changing the physical vector is a different operation. For example, \(\gamma_{uN}=5/3\) and \(\beta_{uN}^2=16/25\) can coexist with \(\gamma_{uo}=1\) for another observer \(o=u\). Observer-relative speed therefore cannot replace orbit-normal tilt. Pointwise generators and a tilt value do not by themselves establish a Bianchi family.



\FloatBarrier

## 6. Distance predictions under group-dependent covariance

### 6.1 The released cohort and three directional designs

Cosmicflows-4 assembles heterogeneous galaxy distances and group information [21]. The frozen analysis begins from 628 selected targets. A usable released DMbest modulus exists for 274, leaving 354 selected targets with undefined distance outcomes in this intake. The analyzed rows have CMB-frame velocities of \(317\)–\(10{,}459\,\mathrm{km\,s^{-1}}\), measured log linewidths and errors, directions uniquely joined by PGC identifier, and recorded group memberships. The CMB-frame velocity logarithm is a covariate, neither a true distance nor an independent peculiar-velocity measurement. All three candidate regressions use a common baseline: intercept, centered log CMB velocity, measured log linewidth and linewidth error. They condition on the realized outcome marks without adding sparsely populated outcome-dummy columns to the held-out design.

Model A adds a shared angular dipole in modulus units and a vector-flow shape \(K_i\boldsymbol n_i\), with \(K_i=-5/[\ln(10)V_{{\rm CMB},i}]\) in \(\mathrm{mag}/(\mathrm{km\,s^{-1}})\). Model B adds the same angular dipole and five Frobenius-orthonormal STF quadrupole columns \(n_i^an_i^b E^{(r)}_{ab}\). Model C includes the union, counting the common angular dipole once. The vector coefficients, five STF coefficients and their cross-block covariance are retained. These are finite-window response coordinates. The STF shape of a distance-modulus regression term does not establish a congruence shear. Likewise \(K_i\) is a linearized, low-redshift response shape, not a full optical transport calculation.

The four total covariance scenarios are deliberately explicit:

$$
V(a,b)=\operatorname{diag}(s_i^2-a^2)
+a^2\boldsymbol1\boldsymbol1^{\mathsf T}+b^2GG^{\mathsf T},
\quad a\in\{0,0.055\},\quad b\in\{0,0.29\}\,\mathrm{mag}.\tag{18}
$$

Here \(s_i\) is the released modulus error, \(G\) is the fixed group-incidence matrix restricted to released rows, \(a\) reallocates a common component while preserving the released diagonal before the group term, and \(b\) sets a specified group-dependence scale. The two scales parameterize the covariance sensitivity analysis. No additional width/Tully–Fisher or peculiar-velocity covariance was appended. All four matrices and their foldwise predictive Schur blocks are positive definite in the saved analysis.

### 6.2 Joint held-out prediction

A five-fold partition keeps every observed group in a single fold. For a held-out block \(H\) and training block \(T\), the fitted Gaussian mean \(X\widehat\theta_T\) and the covariance blocks of (18) produce the conditional predictive mean and Schur covariance

$$
\mu_{H\mid T}=X_H\widehat\theta_T
+V_{HT}V_{TT}^{-1}(y_T-X_T\widehat\theta_T),
\quad
S_{H\mid T}=V_{HH}-V_{HT}V_{TT}^{-1}V_{TH}.\tag{19}
$$

The joint log density of \(y_H\) under this mean and covariance, with the training maximum-likelihood scale, is summed over folds. The normalized multivariate density includes the log determinant and block dimension, so it responds to group dependence as well as residual size. The score conditions on the training estimates of the coefficients and scale; all comparisons use the same held-out groups within a specified covariance scenario. A Cholesky decomposition can attribute arithmetic terms to row order, but those terms are not independent row likelihoods.

| Covariance \(a,b\) (mag) | A: angular + flow | B: angular + STF | C: union | A minus B |
|---|---:|---:|---:|---:|
| \(0,0\) | −220.320 | −196.843 | −518.194 | −23.477 |
| \(0,0.29\) | −194.273 | −195.138 | −209.534 | +0.865 |
| \(0.055,0\) | −231.855 | −198.340 | −651.993 | −33.515 |
| \(0.055,0.29\) | −193.723 | −194.545 | −209.465 | +0.822 |

A higher log score is better only within the same covariance row. B ranks ahead of A when \(b=0\), while A narrowly ranks ahead when \(b=0.29\,\mathrm{mag}\), for either \(a\). The reversal is a direct dependence-sensitive discriminator. It also shows why treating all 274 released rows as independent would answer a different question. Model C loses heavily at \(b=0\); the fold holding out PGC9031, with \(V_{\rm CMB}=317\,\mathrm{km\,s^{-1}}\), includes a very negative Cholesky row contribution \(-317.04\) or \(-448.51\), depending on \(a\). The reciprocal-velocity \(K_i\) becomes large in that part of its domain, and the flexible union inherits the instability. Removing the galaxy after inspecting the score would change the fixed cohort and its comparison; the observed sensitivity instead motivates a physically justified domain or improved forward response.

![Joint five-fold Gaussian held-out scores for three directional distance models at four discrete covariance scenarios. The A–B ordering reverses when the specified group covariance is included; connecting scenario points would imply an unmeasured continuous calibration path.](../figures/fig03_distance_covariance_ranking.png)

The released fits preserve signed out-of-fold residuals, direction, depth tercile and the original outcome marks. At \(a=0.055,b=0.29\,\mathrm{mag}\), for example, the shallow/middle/deep signed mean residuals are \((-0.019,-0.061,+0.013)\) mag for A, \((-0.030,-0.055,+0.019)\) for B, and \((-0.011,-0.052,+0.008)\) for C. Small aggregate means do not determine a full residual law. The useful result is the dependence of a joint predictive comparison on the declared covariance, while the fitted vector/STF coefficients remain available for a later physical response calculation.

\FloatBarrier

### 6.3 A normalized selected-row likelihood and finite-sample tensor region

The 274-row distance cohort admits a more specific statistical construction than a Gaussian reference assigned directly to fitted coefficients. For the full model containing four baseline terms, one calibration dipole, the three inverse-velocity response columns and five STF magnitude coordinates, let

$$
 Y\mid X,\text{selected marks};\beta,\sigma^2,s
 \sim N_{274}(X\beta,\sigma^2V_s),\qquad \beta\in\mathbb R^{15}.
$$

The covariance shape \(V_s\) is one of the four declared choices in the distance comparison. It is fixed in this experiment; the common positive scale \(\sigma^2\) is unknown. For \(G_s=X^TV_s^{-1}X\) and generalized least-squares residual quadratic \(q_s\), the normalized likelihood is

$$
 \log L_s(\beta,\sigma^2;Y)=-\frac12\left[
 274\log(2\pi\sigma^2)+\log|V_s|+
 \frac{q_s+(\beta-\widehat\beta_s)^TG_s(\beta-\widehat\beta_s)}{\sigma^2}
 \right].
$$

Thus the covariance normalization and all 274 response coordinates remain in the likelihood. The fitted scale \(q_s/274\) must be distinguished from the unbiased residual scale \(q_s/259\).

| Common scale \(a\) [mag] | Group scale \(b\) [mag] | \(q_s\) | \(\widehat\sigma^2_{\rm ML}\) | \(\log L_{s,\max}\) |
|---:|---:|---:|---:|---:|
| 0 | 0 | 651.218204 | 2.376709 | −168.298506 |
| 0 | 0.29 | 324.919303 | 1.185837 | −173.029455 |
| 0.055 | 0 | 682.763995 | 2.491839 | −170.021994 |
| 0.055 | 0.29 | 330.452668 | 1.206032 | −173.703843 |

Under this selected-data Gaussian mean model, full column rank and fixed positive-definite shape, the joint coefficient event has the exact model-conditional region

$$
 (\beta-\widehat\beta_s)^TC_{{\rm ML},s}^{-1}
 (\beta-\widehat\beta_s)\le c_{0.05},\qquad
 C_{{\rm ML},s}=\frac{q_s}{274}G_s^{-1},
$$

$$
 c_{0.05}=\frac{274\times15}{259}F_{15,259;0.95}
 =27.058502419705658.
$$

This radius exceeds the earlier fixed-Gaussian comparison \(\chi^2_{15;0.95}=24.995790139728616\), because the unknown scale is estimated from the responses. Projection to the five STF coordinates retains the fifteen-dimensional radius. It does not substitute a five-dimensional threshold or condition the nuisance coefficients on their fitted values.

The signed STF coordinates, in magnitudes, are as follows. Their covariance is the corresponding block of the full joint covariance before the region is projected.

| \((a,b)\) [mag] | \(b_1\) | \(b_2\) | \(b_3\) | \(b_4\) | \(b_5\) |
|---|---:|---:|---:|---:|---:|
| (0, 0) | 0.183056 | 0.808292 | −0.010452 | 0.045121 | 0.126844 |
| (0, 0.29) | 0.195454 | 0.595818 | 0.038591 | −0.028036 | 0.128076 |
| (0.055, 0) | 0.180529 | 0.831115 | −0.017713 | 0.048508 | 0.127592 |
| (0.055, 0.29) | 0.195170 | 0.599207 | 0.037642 | −0.026498 | 0.128246 |

For the zero tensor, the projected quadratics computed from the saved full-model coefficient and covariance blocks are \(9.846158\), \(6.031362\), \(10.413226\) and \(6.068341\), all below \(c_{0.05}\). All four projected regions contain zero. This is a statement about the selected magnitude tensor within the assumed law, and supplies neither a physical shear bound nor evidence that physical anisotropy is absent.

The union across covariance shapes contains the valid region of whichever shape is true. Consequently it has coverage at least 95% if one of these four fixed shapes is correct and all four fits refer to the same coefficient target. The argument does not hold for an arbitrary true covariance outside this class, or for shape-dependent pseudo-true targets under misspecification. It assigns no probability weights to the four shapes.

The later held-out diagnostic also differs from the saved plug-in prediction score. For training block \(t\), validation block \(v\), and \(R_s=V_{vt,s}V_{tt,s}^{-1}\), set

$$
 W_s=V_{vv,s}-V_{vt,s}V_{tt,s}^{-1}V_{tv,s},\qquad
 D_s=X_v-R_sX_t,
$$

$$
 \widehat Y_v=R_sY_t+D_s\widehat\beta_{t,s},\qquad
 M_s=W_s+D_s(X_t^TV_{tt,s}^{-1}X_t)^{-1}D_s^T.
$$

The added term carries training-coefficient uncertainty. The resulting repeated-sample predictive quadratic has an \(F_{m,n_t-15}\) law after division by the unbiased training scale, under the same Gaussian assumptions. The smallest two-sided tail among the twenty saved shape–fold diagnostics is \(0.0232647\); none crosses the retrospective \(0.0025\) threshold. Only the five diagnostics belonging to a true shape automatically have their stated reference law under a single-true-shape assumption. This model criticism is compatible with poor plug-in prediction scores, and does not establish source selection or physical adequacy.

### 6.4 Directional rate fields in four overlapping windows

The individual-galaxy cohort and the grouped Cosmicflows sample define different experiments. We now use 35,970 released groups to examine a rate field across four overlapping redshift windows. This calculation retains the published shifted moduli, their errors, CMB-frame redshifts and ICRS directions. Its distance is the observed transformation \(d_i=10^{(\mu_i-25)/5}\,\mathrm{Mpc}\), and \(u_i=cz_{{\rm CMB},i}\) is a linear recession proxy. Neither is a recovered latent cosmological variable.

For the window centred at \(z_c\), define

$$
 H_W=\frac{\sum_i w_i d_i u_i}{\sum_i w_i d_i^2},\qquad
 w_i=\frac{\exp[-(z_i-z_c)^2/(2s_z^2)](1+\alpha n_{iz})}{s_i^2},
 \qquad s_z=0.012,
$$

where the working velocity variance is

$$
 s_i^2=(250\,\mathrm{km\,s^{-1}})^2+
 \left[70\,\mathrm{km\,s^{-1}\,Mpc^{-1}}\,
       \frac{\ln10}{5}d_i e_{\mu,i}\right]^2.
$$

We compare this monopole-only estimator with a joint nine-coordinate fit,

$$
 u_i=d_i\{h_0+D_an_i^a+S_{ab}n_i^an_i^b\}+e_i,
 \qquad S_{ab}=S_{ba},\qquad S^a{}_a=0.
$$

The five STF coordinates use a Frobenius-orthonormal basis. Their Euclidean norm is consequently \(\|S\|_F\). In the following table every rate coefficient and tensor norm has units \(\mathrm{km\,s^{-1}\,Mpc^{-1}}\); FP share means the fundamental-plane fraction of the distance-weighted denominator, \(\sum_iw_id_i^2\).

| \(z_c\) | \(H_W\), \(\alpha=0\) | Joint \(h_0\) | \(\|D\|\) | \(\|S\|_F\) | FP share |
|---:|---:|---:|---:|---:|---:|
| 0.025 | 74.629348 | 75.167996 | 3.332161 | 2.166730 | 0.303715 |
| 0.040 | 74.343818 | 75.303212 | 2.996321 | 3.175257 | 0.534917 |
| 0.060 | 72.516333 | 74.559217 | 2.708324 | 3.753386 | 0.802412 |
| 0.080 | 70.810223 | 72.445152 | 1.876692 | 1.952792 | 0.901890 |

The monopole-only and joint monopoles differ by \(0.538648\), \(0.959393\), \(2.042884\) and \(1.634929\), respectively. The FP share also rises from approximately 30% to 90%. Thus the change with reported redshift combines angular response, radial weighting and method composition. A physical \(H(z,\boldsymbol n)\) would require a model connecting all three to the source and observer variables. The selected rate field retains the estimator-level information needed to compare physical response models [20,31,37,38].

![Four overlapping Gaussian redshift windows in the same 35,970-group sample. The first panel distinguishes monopole-only and joint-fit rate coefficients; the second retains vector and STF amplitudes; the third shows the changing distance-weighted method composition. Connecting lines organize the four windows and do not interpolate a physical expansion history.](../figures/added_cf4_windows.png)

The angular effect can be made explicit. Substitute the declared response

$$
 u_i=H_0d_i+d_iD\cdot n_i+B\cdot n_i+d_iS:n_in_i
$$

into the estimator. With \(N_W=\sum_iw_id_i^2\), the result is exactly

$$
 H_W=H_0+D\cdot m_W+B\cdot b_W+S:Q_W,
$$

$$
 m_W=\frac{\sum_iw_id_i^2n_i}{N_W},\qquad
 b_W=\frac{\sum_iw_id_in_i}{N_W},\qquad
 Q_W=\frac{\sum_iw_id_i^2(n_in_i-I/3)}{N_W}.
$$

Here \(D\) and \(S\) are rate responses, whereas \(B\) has velocity units. Antipodal symmetry removes the two odd moments; an isotropic weighted second angular moment is additionally needed to remove \(S:Q_W\). At one fixed distance the \(D\) and \(B\) columns are proportional. Their different dimensional meanings do not make them identifiable from one angular shell. The north-weighted calculation, \(\alpha=0.6\), gives \(H_W=(74.315905,74.040630,72.382225,70.828381)\) in the four windows. It is a deterministic sensitivity calculation on the same sources.

All four nine-coordinate fits form one 36-coordinate carrier. If \(A_r\) maps the shared velocity rows to the coefficients in window \(r\), its working covariance is

$$
 C_{rs}=A_r\operatorname{diag}(s_i^2)A_s^T.
$$

The first two joint monopoles have correlation \(0.701821\). Their difference has formal standard deviation \(0.096102\), while deleting their covariance would give \(0.175896\). These are consequences of the stated diagonal row law. They are not an empirical calibration of the shared zero point or peculiar-velocity field.

Deleting one method family changes the fitted monopole, vector and STF coordinates by maxima \(0.880\), \(1.559\) and \(2.726\), respectively; deleting one of the twelve fixed ICRS sky patches gives maxima \(0.557\), \(1.185\) and \(1.623\). The maxima occur at different deletions and windows. Such shifts expose sensitivity to the selected support. They do not estimate an independent systematic-error distribution.

There is also a calibration ambiguity already at the mean-design level. For a partition into four method families, the columns \(Z_{im}=d_i\mathbf1\{i\in m\}\) satisfy \(\sum_mZ_{im}=d_i\), the common monopole column. The combined thirteen-column design therefore has one exact dependence; the reported design rank is twelve. Profiling those method columns leaves eight angular directions. This statement holds for the fixed-distance, fixed-weight linear design. A supplied calibration constraint or a nonlinear latent-distance model changes its identifying assumptions.

### 6.5 Windowed bulk motion and correlated depth responses

Suppose \(v(x)=v_0+u(x)\) almost everywhere and define
$$
B_W[v]=\int W(x)v(x)\,d\nu(x).
$$
Integrability immediately gives
$$
B_W[v]=\left(\int W\,d\nu\right)v_0+B_W[u].
$$
Thus a normalized window has unit homogeneous-mode gain, but its measured value still contains \(B_W[u]\).

For zero-mean scalar components \(a,b\), assume the joint integrability needed for Fubini and the cross-spectrum representation
$$
\mathbb E[a(x)b(y)]
 =\int e^{ik\cdot(x-y)}p_{ab}(k)\,d\mu(k).
$$
With \(\widehat W(k)=\int e^{-ik\cdot x}W(x)\,d\nu(x)\),
$$
{\rm Cov}(B_W[a],B_{W'}[b])
 =\int \overline{\widehat W(k)}
              \widehat W'(k)p_{ab}(k)\,d\mu(k).
$$
The proof substitutes the cross-spectrum into the double window integral and interchanges integrals. Every pair of windows contributes; overlapping or related windows do not become independent by using different depth labels.

A small example makes the residual explicit. Give the four fields
\(\cos x,-\sin x,-\cos x,\sin x\) equal probability. Their mean is zero and their covariance is \(\cos(x-y)/2\). Point windows at \(0\) and \(1\) have residual variance \(1/2\) and cross covariance \(\cos(1)/2\ne0\). A measured bulk value therefore cannot be substituted pointwise for the homogeneous mode, even though its expectation can equal that mode.

Calling the residual “finite-\(k\)” additionally requires exclusion of spectral mass at \(k=0\); otherwise it contains a constant component degenerate with \(v_0\). The spectral representation, integrability, frame, and selection/calibration remainder bounds must be supplied for an observational application.



### 6.6 A constructive two-radius design

Consider
$$
y_i=E_4(n_i)a+\frac{r_i}{c}E_9(n_i)h,
\qquad X=[E_4,D E_9],\quad D={\rm diag}(r_i/c).
$$
The four columns of \(E_4\) span \(1,n_x,n_y,n_z\). The nine columns of \(E_9\) span degrees at most two, including the five STF coordinates, and include \(E_4\). Let \(L\) embed the four coefficients so that \(E_9L=E_4\).

Take nine unisolvent directions at \(R_1>0\), and repeat four of them at \(R_2>0\). Suppose \(c>0\), \(R_1\ne R_2\), the nine-direction \(E_9\) matrix is invertible, and the repeated four-direction \(E_4\) matrix is invertible. The first nine equations of \(X(a,h)=0\) give
$$
h=-\frac{c}{R_1}La.
$$
The remaining four equations reduce to
$$
(1-R_2/R_1)E_{4,{\rm repeat}}a=0.
$$
The hypotheses force \(a=0\), then \(h=0\); hence \(X\) has rank thirteen. Equal radii instead retain the four-dimensional ambiguity \(h=-(c/R_1)La\), giving rank at most nine.

A rational example uses the six signed coordinate axes and
\((.6,.8,0),(.6,0,.8),(0,.6,.8)\), with repeated directions
\(e_1,-e_1,e_2,e_3\). In the stated basis,
\(\det E_9=331776/15625\), \(\det E_{4,{\rm repeat}}=-2\), and elimination gives
$$
\det X=\frac{R_1^5(R_1-R_2)^4}{c^9}
              \det E_9\det E_{4,{\rm repeat}}.
$$
Rank is a structural condition. As the radii approach equality, the inverse problem can become poorly conditioned despite retaining rank thirteen. Precision therefore also needs source covariance, signal scale and conditioning in declared coordinates.



For the rational unit directions above, the raw-coordinate condition number is \(1.634438\times10^6\) at \(R_2/R_1-1=10^{-5}\), and \(30.16385\) when \(R_2/R_1=2\), with \(R_1=c=1\) in the synthetic coordinate system. The determinant was checked exactly at four radius ratios. Column rescaling changes this condition number; the rank statement and the loss of four directions at equal radii do not depend on an invertible change of coefficient basis.

![A synthetic two-radius design using nine rational unit directions and four repeated directions. Four singular values vanish as the radii coincide. The right panel shows the raw-coordinate condition number, demonstrating why a nonzero determinant alone does not establish observational precision.](../figures/theory_rank13.png)


\FloatBarrier

## 7. What the unreleased distance outcomes permit

The cross-validation calculation uses only the 274 released distance outcomes. To ask a separate, finite-frame question, fix the strict binary event \(E_i(t)=\mathbf1\{|r_i^{\rm OOF}|>t\}\), with an out-of-fold signed residual and a declared threshold \(t\). At \(t=0.5\,\mathrm{mag}\), the twelve combinations of models and covariance settings have 71–80 events among the released rows. This statistic describes a tail in fitted residuals; it does not use a residual for any of the 354 selected targets whose distance is undefined.

We first make a transparent sensitivity model on the released cohort. Let its uniform reference measure assign mass \(1/274\) to each row. Permit density weights \(1/\Gamma\le w_i\le\Gamma\), \(\sum_iw_i/274=1\), with \(\Gamma\ge1\). If the empirical event fraction is \(e=m/274\), then the attainable weighted event rate has sharp endpoints

$$
L_\Gamma(e)=\max\{e/\Gamma,\;1-\Gamma(1-e)\},
\qquad
U_\Gamma(e)=\min\{\Gamma e,\;1-(1-e)/\Gamma\}.\tag{20}
$$

The first lower bound assigns the minimum allowed weight to event rows; the second follows because non-event rows cannot carry more than \(\Gamma(1-e)\) of total mass. The two upper expressions follow by interchanging event and non-event rows. These are not merely relaxations. A constant weight for all event rows and another for all non-event rows attains each endpoint whenever its active constraint applies; normalization fixes the complementary class weight. Thus (20) is the exact range for the declared density-ratio model. The strict \(>\) convention assigns a residual exactly equal to \(t\) to the non-event class throughout.

No selection weight in (20) supplies the undefined binary outcomes. On the known 628-target frame, allow each of those 354 events to be zero or one. The attainable overall rate is

$$
\left[{274L_\Gamma(e)\over628},
{274U_\Gamma(e)+354\over628}\right].\tag{21}
$$

At \(\Gamma=1\), even an exactly known released-cohort rate leaves width \(354/628=0.563694\). At \(\Gamma=2\) the width spans \(0.7333\)–\(0.7548\) across the twelve fixed cases; at \(\Gamma=4\) it is approximately \(0.8909\). The computation is a partial-identification statement for this 628-member frame. The availability fraction \(274/628\) is not a measured inclusion propensity for the larger Cosmicflows parent catalogue. Nor are the intervals confidence limits for a physical anisotropy parameter: no sampling law for inclusion or missing outcomes was fitted.

![Sharp strict-tail-rate intervals for the released cohort and the 628-target frame as the bounded density ratio changes. The fixed \(0.5\,\mathrm{mag}\) event and all twelve model/covariance cases are retained; missing binary outcomes create a width floor even at \(\Gamma=1\).](../figures/fig04_selection_partial_identification.png)

The distinction is more severe for an unrestricted signed-residual mean. Hold the 274 released outcomes fixed and assign an arbitrary common residual \(M\) to each of the 354 undefined rows. The full-frame mean contains \((354/628)M\), which is unbounded in either direction as \(M\to\pm\infty\). This explicit completion witness shows what additional support or selection restrictions a physical mean would need. For the binary event, recovering the 354 event indicators and a source-grounded inclusion law on the same frame are direct ways to narrow (21).

\FloatBarrier

## 8. An independent supernova comparison

The Pantheon+ public release supplies a useful comparison of angular columns with a released covariance, without merging its scores with the CF4 analysis [22–24]. We retain 277 original-order rows satisfying \(\mathrm{USED\_IN\_SH0ES\_HF}=1\) and \(0.0222\le z_{\rm CMB}\le0.14882\). They represent 238 literal CIDs across 15 survey codes; repeated release rows cannot simply be counted as independent supernovae. One 277-by-277 subblock of the public total statistical-plus-systematic covariance is symmetrized and used in all generalized least-squares fits. The baseline has a common offset. Additional designs contain an angular-calibration vector, a frozen source-flow vector, their joint columns, or survey indicators together with the joint columns.

The generalized residual quadratics and degrees of freedom are, in that order, \(242.376/276\), \(237.460/273\), \(233.145/273\), \(230.426/270\), and \(209.902/256\). Relative to the offset fit, calibration alone reduces the quadratic by \(4.916\), frozen flow alone by \(9.231\), and their joint columns by \(11.950\). The joint coefficient estimates are \((-0.0514,-0.00353,-0.0414)\,\mathrm{mag}\) for calibration and \((-390,-90.3,-304)\,\mathrm{km\,s^{-1}}\) for the frozen-flow columns, with cross covariance retained. Their sensitivity to survey-indicator columns is part of the comparison. These nested fits describe the selected covariance subblock and its response columns. CF4's conditional predictive log scores and these supernova residual quadratics have different data, units and joint covariance; their numerical differences are not a cross-survey evidence term. The known redshift and peculiar-velocity treatment in supernova analyses further motivates a full response rather than identifying a \(K\boldsymbol n\) regression column with a cosmic velocity [24,26].

\FloatBarrier

## 9. Proper-motion depth slopes as a projection problem

### 9.1 Rows, design and the six-dimensional Schur complement

The astrometric calculation is based on a single pass over 755,850 rows of an extragalactic proper-motion working sample. Three bins of *reported* redshift, \([0,1),[1,2),[2,10]\), contain 200,785, 369,335 and 185,730 rows. The question posed by the chosen design is whether six continuous E1 polar and B1 axial slopes proportional to \(g(z)=z/(1+z)\) add information beyond 102 existing angular/depth columns. The fitted slope vector is

$$
\widehat\theta=(6.602,\;0.292,\;-1.501,\;-10.185,\;-7.647,\;0.482)
\;\mu\mathrm{as\,yr^{-1}}.\tag{22}
$$

An E1 polar vector and a B1 axial vector have different parity and physical meanings. Their coefficients are not six directly observed source velocities; a proper-motion source response, distance selection and reference-frame effects would enter such an interpretation. Vector-spherical-harmonic analysis of astrometric catalogues and correlated extragalactic proper motions provides the appropriate methodological setting [16–18,25]. The result here is a precise fixed-design information calculation on reported-z coordinates.

To expose the source of the information loss, whiten the design by the declared row covariance. Let \(N\) be the whitened old-column matrix, \(S\) the whitened matrix of six slope columns, and \(P_N=N(N^{\mathsf T}N)^{-1}N^{\mathsf T}\). If the full column ranks required by these inverses hold, the unprofiled and profiled slope information matrices are

$$
A=S^{\mathsf T}S,
\qquad
F=S^{\mathsf T}(I-P_N)S
=A-S^{\mathsf T}N(N^{\mathsf T}N)^{-1}N^{\mathsf T}S.\tag{23}
$$

The second expression is the Schur complement of the old-column block of the joint normal matrix. It removes exactly the slope components that the old design can reproduce. The recorded matrices retain all six profiled directions, but \(\operatorname{tr}F/\operatorname{tr}A=0.0158485\): only about \(1.585\%\) of the unprofiled trace information survives. The six generalized retained eigenvalues of \(Fq=\lambda Aq\) range from \(0.0153424\) to \(0.0170346\); the profiled Fisher eigenvalues range from \(0.0394922\) to \(0.0734802\,(\mu\mathrm{as\,yr^{-1}})^{-2}\).

The generalized eigenvalues have a direct geometric meaning. For a slope vector \(q\), the ratio \(q^{\mathsf T}Fq/q^{\mathsf T}Aq\) is the squared norm of the slope-column combination after projection off \(N\), divided by its original squared norm. The stationary ratios are squared sines of the principal angles between the column spaces of \(S\) and \(N\). Thus

$$
\vartheta_i=\arcsin\sqrt{\lambda_i}
\in[7.115^\circ,7.499^\circ].\tag{24}
$$

Between \(98.30\%\) and \(98.47\%\) of each canonical slope-direction information lies in the nuisance projection. The trace fraction is a weighted aggregate of the directional information. The angles are obtained directly from the stored Schur information matrices.

Under the same Gaussian independent-row working law, the six-degree quadratic score is \(12.140206\), below the \(5\%\) \(\chi_6^2\) reference value \(12.591587\). Its working-law upper tail is \(0.058913\). At \(80\%\) Wald power in the strongest and weakest profiled eigen-directions, required slope amplitudes are \(13.617\) and \(18.574\,\mu\mathrm{as\,yr^{-1}}\), respectively. Those are power properties of the chosen design and law. Spatially correlated proper motions, reported-to-true-redshift transport, source selection and different depth functions can alter the physical question and its information geometry.

![Six principal angles obtained by applying \(\arcsin\sqrt{\lambda}\) to the generalized Schur-information eigenvalues, together with the six-slope quadratic score and its Gaussian reference threshold. The bins use reported redshift and a fixed \(z/(1+z)\) slope basis.](../figures/fig05_depth_information_geometry.png)

### 9.2 Preserving the common mode and cross-bin covariance

A common 24-coordinate Gaussian carrier stores the three-bin E1/B1 vector intercepts and their shared six slope coordinates with a full 24-by-24 covariance. The reported-bin functional map \(M:\mathbb R^{24}\to\mathbb R^{18}\) has rank 18, leaving a six-dimensional nullspace. We retain the full carrier because a derived 18-coordinate image cannot reconstruct those six directions. Within the 18-dimensional image, the transform from the three bin values \((Y_0,Y_1,Y_2)\) to the anchored form

$$
Z_{18}=(Y_0,\;Y_1-Y_0,\;Y_2-Y_1)\tag{25}
$$

is invertible. If only the two differences are kept, the resulting rank-12 map removes the common mode. Equation (25) allows the reader to see change with depth without discarding the starting value on which an absolute response could depend. The bin values are obtained from the common state and slope, rather than substituting the raw bin intercepts for the reported-bin functional image. That distinction matters numerically: such a substitution would change functional means by as much as \(8.02452\,\mu\mathrm{as\,yr^{-1}}\), covariance entries by as much as \(10.2636\,(\mu\mathrm{as\,yr^{-1}})^2\), and many subsequent exceedance cells.

For any two bins, a difference \(\Delta_{ab}=Y_a-Y_b\) has covariance

$$
C_{\Delta,ab}=C_{aa}+C_{bb}-C_{ab}-C_{ba}.\tag{26}
$$

The two cross terms are part of the same joint law. Setting them to zero produces a counterfactual model, not an automatically conservative substitute. Across six E1/B1 adjacent and deep-minus-shallow three-vector contrasts, the ratio of the full covariance's largest-eigenvalue standard deviation to that of the zero-cross counterfactual ranges from \(0.195986\) to \(0.326478\). For E1 bin 1 minus bin 0, the two largest eigenvalues are \(0.7072\) and \(18.4118\,(\mu\mathrm{as\,yr^{-1}})^2\), giving a spectral standard-deviation ratio \(0.195986\). The common contribution cancels in the contrast under the specified covariance. It must be learned or justified as a cross-bin block, rather than assumed away.

![Spectral standard deviations of six three-vector depth contrasts from the full joint covariance and from the explicit zero-cross-bin counterfactual. The smaller full-law scales measure cancellation of shared uncertainty within the stated reported-bin Gaussian carrier. The right panel counts positive conservative norm lower bounds as the common full-state radius increases.](../figures/fig06_depth_covariance_support.png)

The 36-coordinate functional image contains the E1 and B1 vectors in all three bins, both adjacent contrasts, and the deep-minus-shallow contrast, with their complete 36-by-36 transformed covariance. A coordinate support calculation can be exact under a fixed ellipsoidal carrier region; a nonlinear norm interval obtained by the triangle inequality and largest singular value is instead a certified outer interval. These distinctions matter when the image approaches zero or changes sign. The bin labels still refer to reported redshift. A physical history would require the mapping to true depth, selection, orientation transport and a source model [19,20].

\FloatBarrier

### 9.3 Reported-depth equality under covariance and bias envelopes

The six continuous \(g(z)=z/(1+z)\) slopes and equality of the three reported-bin vector levels answer different questions. We retain the full 24-coordinate state \(\mu_{24}=(\gamma_0,\gamma_1,\gamma_2,\theta)\) and covariance \(C_{24}\). Its bin values obey

$$
 Y_b=\gamma_b+c_b\theta,\qquad
 (c_0,c_1,c_2)=\left(\frac14,\frac7{12},\frac{26}{33}\right).
$$

Let \(M\) be this eighteen-coordinate map and

$$
 A=\left[\begin{pmatrix}-1&1&0\\0&-1&1\end{pmatrix}
 \otimes I_6\right]M,\qquad d=A\widehat\mu_{24}.
$$

Then \(A\) has rank twelve, and \(d=0\) expresses common E1 and B1 levels across all three reported-redshift bins. It is not the earlier six-restriction null \(\theta=0\).

We examine the declared covariance envelope

$$
 V_\tau=A(C_{24}+\tau^2I_{24})A^T,
 \qquad T_\tau=d^TV_\tau^{-1}d.
$$

The scenario parameter \(\tau\), in \(\mu\mathrm{as\,yr^{-1}}\), is an added full-state coefficient scale. It is not an estimated spatial covariance for Gaia sources. All original covariance cross blocks are retained.

| \(\tau\) [\(\mu\mathrm{as\,yr^{-1}}\)] | \(T_\tau\) | Gaussian reference survival | Moment upper bound |
|---:|---:|---:|---:|
| 0 | 381.199232 | \(3.60205\times10^{-74}\) | 0.031480 |
| 0.1 | 365.703533 | \(6.78851\times10^{-71}\) | 0.032813 |
| 0.3 | 277.269896 | \(2.73919\times10^{-52}\) | 0.043279 |
| 1 | 78.081312 | \(9.57251\times10^{-12}\) | 0.153686 |
| 3 | 11.075522 | 0.522458 | 1 |
| 10 | 1.032367 | 0.999983 | 1 |

The two last columns require different assumptions. For zero mean and covariance domination \(\operatorname{Cov}(d)\preceq V_\tau\), we have \(\mathbb E T_\tau\le12\); Markov's inequality gives \(\min(1,12/T_\tau)\). A centred Gaussian law under the same domination gives the stronger \(\chi^2_{12}\) reference bound. At level 0.05 the moment threshold is crossed at \(\tau=0.377552\), whereas the Gaussian threshold is crossed at \(\tau=2.139565\). The difference quantifies the additional distributional premise. The very small uninflated Gaussian tail does not by itself calibrate an observational significance.

![Reported-depth equality under the full covariance plus a declared isotropic coefficient envelope. The left panel shows the same quadratic against two reference thresholds. The right panel compares the centred-Gaussian reference with the distribution-free moment bound. Both require the stated covariance domination; the envelope scale is hypothetical.](../figures/added_depth_covariance.png)

A separate deterministic bias scenario asks how far the estimated state must move before its contrast enters the reference region:

$$
 \min_{\|b\|\le\delta}(d-Ab)^TV_\tau^{-1}(d-Ab).
$$

Allowing bias in all 24 coordinates, the zero-inflation Gaussian threshold is reached at \(\delta=7.563904\,\mu\mathrm{as\,yr^{-1}}\). Exact zero contrast requires \(10.178814\,\mu\mathrm{as\,yr^{-1}}\), independently of \(\tau\). These values concern a Euclidean ball in the stated coefficient coordinates. Restricting bias to the six slopes leaves an unrestricted least-squares floor \(232.249387\) at \(\tau=0\), so slope bias alone cannot eliminate the full twelve-coordinate contrast. The retained witnesses reproduce the stated contrast quadratics; they are allowed scenarios, not measurements of Gaia systematics.

![Saved minimized contrast quadratics when bias acts in all 24 coordinates or only in the six shared slopes. Points are the retained scenario grid; connecting segments organize those points. The same covariance cross blocks are retained in both panels. The bias and inflation radii are not observed systematic-error bounds.](../figures/added_depth_bias.png)

#### Information within a restricted history-response domain

Full rank does not ensure useful power at the amplitudes allowed by a physical approximation. A separate six-parameter history/local-response experiment retains a profiled covariance for its three-dimensional history-response amplitude with eigenvalues

$$
 (0.663189609,0.696790781,0.878898866)
 \ (\mu\mathrm{as\,yr^{-1}})^2.
$$

In the illustrative response \(a=K_Hb\), take \(K_H=14.76646685987891\,\mu\mathrm{as\,yr^{-1}}\) and restrict \(R\|b\|\le\epsilon\), with \(R=7499.25\). These constants define the retained response scenario. They are not inferred from the reported-bin constancy statistic. For fixed Gaussian covariance \(C_{aa}\), the largest Mahalanobis displacement is

$$
 d_{\max}^2=\left(\frac{K_H\epsilon}{R}\right)^2
 \lambda_{\max}(C_{aa}^{-1}).
$$

Even a simple-direction oracle at size \(\alpha\) has power no larger than \(\Phi\{\Phi^{-1}(\alpha)+d_{\max}\}\). At \(\alpha=0.05\), the powers for \(\epsilon=0.01,0.1,0.3\) are \(0.050002493775\), \(0.050024942216\) and \(0.050074856412\). At the largest of these scenario domains, 80% oracle power would require a uniform information multiplier \(1.1750215\times10^7\) with the same response. This is a requirement in the fixed experiment. It is not a forecast that such an improvement can be achieved, nor an impossibility statement for every other astrometric observable. The chosen small parameter also does not certify every omitted physical remainder.

![Oracle power and the information required for 80% power within the specified Gaussian history-response experiment. The left axis magnifies the excess over test size by one million. The allowed-domain parameter is illustrative, and the information multiplier is a requirement within this response model.](../figures/added_history_power.png)

### 9.4 Angular pairs and an exact common-spin quotient

A separate Gaia frame-source calculation retains 4756 selected objects and all \(4756\times4755/2=11,307,390\) distinct pairs, arranged in nine angular-separation bins. For source directions \(n_i\) and tangent motions \(v_i\), define

$$
 \kappa_{ij}=v_i\cdot n_j+n_i\cdot v_j
 =\frac{d}{dt}(n_i\cdot n_j).
$$

This is the derivative of the cosine of the angular separation, after the stated unit conversion. It avoids dividing by \(\sin\theta_{ij}\) at the endpoints. A common frame spin \(v_i=\omega\times n_i\) cancels exactly, since its two scalar triple products have opposite signs. Vector-spherical-harmonic methods distinguish this rotational pattern from gradient-like astrometric responses [16].

The binned response is \(d=Hy\), with a \(117\times9512\) operator and thirteen mean-response columns: one vector and two five-coordinate STF parities. Under the independent-source working covariance,

$$
 C_d=HC_0H^T,\qquad C_0=\operatorname{blockdiag}(C_i).
$$

The same source contributes to many pairs. Those pairs therefore remain correlated even in this row-independent source model. Their count does not give eleven million independent measurements. The retained pair counts are 315, 895, 3,569, 24,624, 85,342, 816,145, 2,118,284, 5,222,601, and 3,035,615, summing to the full distinct-pair count.

![Vector and STF angular-pair responses with the number of distinct pairs per retained angular bin. These are binned response coordinates, not estimated field coefficients. Bin indices preserve the archived ordering; angular separation is not physical depth. Source sharing remains in the propagated covariance.](../figures/added_gaia_pairs.png)

The original covariance projection kept 88 of 117 modes at its stated numerical threshold. The modes discarded there were positive or unresolved, rather than established physical null modes. Its representative residual quadratics were \(87.0026023\) and \(75.0786229\) for the three-coordinate and thirteen-coordinate designs, respectively. Their difference is descriptive until the image rank and numerical covariance error are controlled.

The retained subsequent finite-source certificate imposes exact spin removal with

$$
 H_*=H\{I-B(B^TB)^{-1}B^T\},
$$

where \(B\) contains the three source-spin columns. For the same fixed covariance-derived projection \(W\), it reports complete mean ranks three and thirteen and

$$
 \|\operatorname{Cov}(WH_*Y)-I\|_2
 \le1.3599702443948884\times10^{-9}.
$$

The nested quadratic difference is enclosed by

$$
 11.923978483828927\le\Delta\le11.923980198308788.
$$

Under the matching three-coordinate Gaussian mean null, its conservative tail upper bound is \(0.29017657168415\). A projected-mean ball of dimensionless radius at most \(10.954451326468204\) has at least 95% coverage under that finite Gaussian working experiment and arithmetic enclosure. The numerical certificate concerns the archived finite source coordinates, fixed projection, within-source covariance and specified binary64 arithmetic model. It does not qualify unknown cross-source covariance or a material-worldline response. This conditional bound is therefore separate from a calibrated cosmological significance.

\FloatBarrier

## 10. Functional images and strict exceedance under one joint replicate law

The common 24-coordinate Gaussian carrier also permits a transparent example of how a vector-valued observation is mapped to scalar and pseudoscalar questions without discarding its covariance. We use the 4,096 retained replicate rows already generated from its declared full joint Gaussian working law. Each row is transformed by the *same* 24-to-18 bin map and the same bin/contrast functional map; the replicate array is not resampled independently at each depth. The resulting sample-by-functional object has twelve three-vector norms: E1 and B1 in each reported bin, the two adjacent contrasts, and the deep-minus-shallow contrast. For each of the six bin or contrast locations, the dot product of its E1 polar and B1 axial vectors is a parity-odd pseudoscalar. Unlike a norm, this dot product is signed and can cross zero.

For a scalar functional \(\phi_k\), such as a vector norm or an E1–B1 dot product, define the finite strict frequency at threshold \(c\) by

$$
\widehat\Pi_k(c\mid\nu_{\rm G})
={1\over4096}\sum_{r=1}^{4096}
\mathbf1\{\phi_k(X^{(r)})>c\},\tag{27}
$$

where \(\nu_{\rm G}\) names this particular joint Gaussian replicate law. For norms, the thresholds are \(0,1,2,5,10,20\,\mu\mathrm{as\,yr^{-1}}\). For the E1–B1 dot products they are \(-25,0,25\,(\mu\mathrm{as\,yr^{-1}})^2\). Equality with the threshold is not an exceedance. Their reference is the stated finite joint Gaussian sample. Their precision as fractions of 4,096 describes the retained replicate computation, while physical coverage would require an appropriate selected-survey law.

The joint law yields nontrivial values rather than a compulsory zero or one. For the E1 bin1-minus-bin0 contrast, strict norm exceedance above (1) and \(2\,\mu\mathrm{as\,yr^{-1}}\) is \(0.931152\) and \(0.482178\); above (5) it is zero among these 4,096 rows. The corresponding E1 bin2-minus-bin1 values are \(0.989746\), \(0.861572\), and \(0.0129395\). The B1 bin2-minus-bin0 contrast exceeds \(10\,\mu\mathrm{as\,yr^{-1}}\) in \(0.306641\) of the retained rows. Signed E1–B1 products make a different query: for bin 0, the fraction strictly above zero is \(0.102051\), whereas the deep-minus-shallow product's fraction is \(0.893311\). All these frequencies remain linked through their common 24-dimensional draws.

![Strict depth-contrast norm exceedance frequencies computed from the same 4,096 full-24 Gaussian replicate rows. E1 polar and B1 axial contrasts are separate functionals, with discrete thresholds and no interpolation between them.](../figures/fig07_joint_exceedance.png)

A reference ball of radius \(10\,\mu\mathrm{as\,yr^{-1}}\) may be used to normalize a *computational* score on this carrier; it is not a matched MES physical anchor. An ellipsoidal full-24 region with radii \(\rho=0,1,2,4,8\) has exact coordinate supports. For its nonlinear norm images, the spectral-norm and triangle inequalities give conservative outer intervals rather than necessarily sharp endpoints. Of the twelve vector norms, positive certified lower endpoints number 12, 12, 10, 4 and 1 as \(\rho\) moves through those five values. This progression reflects a growing common uncertainty region and the way a nonlinear norm images that region. The carrier, anchored path, vector contrasts, outer intervals and replicate frequencies answer different but compatible questions; reducing them to one “filling fraction” would erase their targets and laws.

### 10.1 The tensorized \((x,F,\Pi,Q_{\mathcal A},G_F)\) representation

Let \(X^{(s)}\) denote one retained joint state and let \(\Phi\) be a declared family of tensor-valued and scalar functions. The sample-by-functional array is

$$
x_{s\phi}=\phi(X^{(s)}),\qquad \phi\in\Phi.
$$

Vector components, STF blocks, norms and parity-odd contractions remain labelled by their units and representations. In the astrometric example, the same row contains all three bin vectors, their contrasts and E1–B1 dot products. In the CMB example, it contains the full quadrupole and octupole as well as \(\chi\), \(\mathcal C\) and the shape parameter. This makes a derived scalar reproducible from the state that generated it.

For a closed convex acceptance body \(\mathcal A\) containing the origin in its interior, define the anchor coordinate by its Minkowski gauge,

$$
Q_{\mathcal A}(x)=\inf\{a>0:x\in a\mathcal A\}.
$$

The subscript distinguishes this quantity from the CMB quadrupole \(Q\). An anchor may be a stipulated computational body or a premise-qualified physical body; its interpretation is carried with its definition. In particular, the exact geometric range \(-1\le\mathcal C\le1\) is available for every nonzero tensor pair even where no physical shear denominator has been supplied.

A joint state region \(\mathcal E\) induces a functional image \(\mathcal I_\phi=\phi(\mathcal E)\). Directional supports retain more than its largest radius:

$$
F_\phi(u)=h_{\mathcal I_\phi}(u)
=\sup_{X\in\mathcal E}\langle u,\phi(X)\rangle.
$$

When \(\mathcal A\) is also bounded, \(h_{\mathcal A}(u)>0\) for every nonzero \(u\), and the ratio \(F_\phi(u)/h_{\mathcal A}(u)\) expresses the support in anchor units. Bounds in all directions determine containment in the closed convex anchor. For a linear vector image \(\phi(X)=JX\) of an ellipsoid with centre \(\bar X\) and shape matrix \(C\), the exact support is

$$
F_\phi(u)=u^{\mathsf T}J\bar X+
\rho\sqrt{u^{\mathsf T}JCJ^{\mathsf T}u}.
$$

The depth support calculations use this common-region formula. Applying a norm then yields the conservative intervals shown above. The contraction ellipsoid in Theorem 1 is stronger in a different sense: it is the exact nonlinear-pair image after one quadrupole is fixed, so its chirality extremum is attained rather than merely outer bounded.

The coordinate \(\Pi\) adds a law to a functional query. Equation (27) gives its exact meaning for the retained finite empirical measure; an integral against a specified continuous law would be a different calculation. The depth object \(G_F\) retains an ordered path of these functionals, including its first value and full cross-depth dependence. Equation (25) supplies an invertible path representation of the 18-dimensional bin image. It records the progression of the vector response while preserving the common mode.

If \(\mathcal E(Y)\) is a jointly calibrated state region satisfying \(P\{X_*\in\mathcal E(Y)\}\ge1-\alpha\), then on this same event every declared function obeys \(\phi(X_*)\in\phi(\mathcal E(Y))\). Thus all function images inherit one simultaneous inclusion event. This implication follows directly from set membership and does not require multiplying their marginal probabilities. The retained Gaussian regions illustrate the geometry under their stated working law; their interpretation for the selected survey depends on calibration of that state region. Keeping \(x,F,\Pi,Q_{\mathcal A}\) and \(G_F\) attached to the same state, region and law makes these different questions compatible.

\FloatBarrier

## 11. Optical morphology from acceleration and shear

### 11.1 The retained finite-window magnitude response

The distance model's STF coefficient has a useful, but specific, tensor image. If an angular modulus term is \(B(\hat n)=B_{ab}n^an^b\), its formal low-order effective normalization is

$$
\left({\sigma_{\rm eff}\over H}\right)_{ab}
=-{\ln10\over5}B_{ab}.\tag{28}
$$

The adjective *effective* matters: this conversion changes coefficient units for a finite-window optical fit. It does not identify the tensor with \(\sigma_{ab}\) of the geometry congruence in (1). For B and C across four covariance settings, point norms \(\|\sigma_{\rm eff}/H\|_F\) range from \(0.29555\) to \(0.39676\). The declared Gaussian coefficient reference ellipsoids contain zero in all eight settings and have upper norm limits between \(1.048\) and \(1.156\). A stipulated full-sky \(L^2(h_2/H)\) remainder radius of \(0.25\) changes conditional upper values of \(\Sigma_{\rm eff}^2\) to \(0.500\)–\(0.565\), with zero lower endpoints; at zero stipulated remainder, the upper values are \(0.183\)–\(0.223\). The wide algebraic image is a direct reminder that a fitted point tensor and an inferred physical tensor have different uncertainty and response requirements.

A separate synthetic response isolates what a nuisance projection can remove even when the underlying angular function is nonlinear. At the same 274 directions, set an artificial zero-shear function

$$
f_i(a,d)=-{5\over\ln10}\log(1-a\,d\cdot n_i)\;\mathrm{mag},
\qquad 0\le a\le0.3,\quad\|d\|=1.\tag{29}
$$

There are eight prespecified directions. The registered twelve-column nuisance span absorbs the linear and quadratic angular terms in the expansion. For \(x=d\cdot n\), the projected cubic relation is \(P_Wx^3=(2/5)P_WP_3(x)\); the scaled check of that identity is \(2.32\times10^{-14}\). This equation identifies the leading term that survives in the specified finite sky and projection.

At \(a=0.3\), the whitened projected separation \(d_0\) ranges from \(0.006451\) to \(0.087437\) over directions and covariance settings. With hypothetical known noise \(\tau=0.5\), the one-sided \(5\%\) oracle powers span only \(0.051345\)–\(0.070784\). If both null and alternative may contain a projected remainder in the same ball of radius \(\rho\), their balls overlap when \(\rho=d_0/2\); at that threshold the maximin benchmark returns to \(0.05\). The result is a conditional geometric calculation on the stated projection and noise. It gives a concrete scale for a future finite-redshift remainder argument instead of assuming that fitting an angular tensor isolates its physical source.

\FloatBarrier

### 11.2 Directional expansion and a nonlinear observable

The local expansion tensor supplies a direct physical interpretation of a directional Hubble law. We use signature $(-,+,+,+)$, proper length $s=c\tau$, a unit timelike congruence $u$, and a source direction $n$ in its instantaneous rest space. With physical expansion and shear rates measured in inverse time,
$$
\nabla_a u_b=-u_aA_b/c^2+(H/c)h_{ab}+\sigma_{ab}/c+\omega_{ab}/c.
$$
The past-directed null direction is $\ell^a=-u^a+n^a$, so that $u\cdot\ell=1$. Its contraction gives
$$
\mathcal H_u(n)=c\ell^a\ell^b\nabla_a u_b
=H-\frac{A\cdot n}{c}+\sigma:nn.
\tag{T1}
$$
The acceleration sign follows from this definition of the source direction. Antisymmetry removes the vorticity contraction. Under the regular local optical assumptions, with emitter and observer following this congruence, $d_L(z,n)=cz/\mathcal H_u(n)+O(z^2)$. This is the local covariant cosmography developed by Kristian and Sachs and by Heinesen; observer changes require the accompanying redshift, distance, and angular transformations [27–29].

Assume $H>0$ and introduce dimensionless quantities
$$
 d=-\frac{A}{cH},\qquad S=\frac{\sigma}{H},\qquad
 q(n)=d\cdot n+S:nn,\qquad
 \mathcal H_u(n)=H[1+q(n)].
\tag{T2}
$$
Here $S$ is a real symmetric trace-free rank-two tensor. We also assume $1+q(n)>0$ on the full sphere, so that the local positive-redshift distance law and its logarithm are defined in every direction. The directional rate contains only a monopole, dipole, and quadrupole at this event. The corresponding magnitude field need not have this angular truncation. Subtracting the isotropic magnitude at the same sufficiently small positive redshift and taking the local limit gives
$$
 f_\mu(n)=\lim_{z\downarrow0}5\log_{10}
 \frac{d_L(z,n)}{cz/H}
 =-\kappa\log[1+q(n)],\qquad \kappa=\frac5{\ln10}.
\tag{T3}
$$
The limit concerns the angular part of a local distance law; the individual magnitudes themselves diverge as $z\downarrow0$. The nonlinear map in (T3) generates higher angular multipoles even when (T1) has none. This distinction is useful whenever angular shape is used to interpret departures from an isotropic Hubble law.

There is an exact inverse statement for the complete ideal local field. Even if $f_\mu$ is known only up to a direction-independent intercept, define
$$
 r(n)=\frac{\exp[-f_\mu(n)/\kappa]}
 {\langle\exp[-f_\mu/\kappa]\rangle},\qquad
 \langle g\rangle=\frac1{4\pi}\int_{S^2}g\,d\Omega.
$$
Since $\langle q\rangle=0$, we obtain $r=1+q$ and
$$
 d_a=3\langle rn_a\rangle,\qquad
 S_{ab}=\frac{15}{2}\left\langle r
 \left(n_an_b-\frac{\delta_{ab}}3\right)\right\rangle.
\tag{T4}
$$
Thus the dimensionless local angular shape can be reconstructed without the absolute magnitude intercept under this observation law. The absolute quantities $H$, $A$, and $\sigma$ still require normalization. Selected angular support, finite-redshift fitting, and source-dependent magnitude calibration alter the observation map and must be retained in an application. In particular, exponentiating a truncated or noisy harmonic fit is not the same operation as applying (T4) to the complete field.

### 11.3 Acceleration--shear coupling in the magnitude octupole

We now obtain the leading induced octupole and its error. Let $\mathsf P_3$ be the full-sphere orthogonal projector onto degree three. Define the rank-three STF tensor $O_\mu$ by
$$
 \mathsf P_3f_\mu(n)=O_{\mu,abc}n^an^bn^c,
 \qquad
 O_{\mu,abc}=\frac{35}{2}\langle f_\mu n_{\langle a}n_bn_{c\rangle}\rangle.
\tag{T5}
$$
This is an optical magnitude tensor, with magnitude units. We use a different symbol for a CMB temperature or polarization octupole: equal tensor rank does not imply equal physical response.

For a vector $d$ and an STF tensor $S$, set
$$
 \begin{split}
 [L_Sd]_{abc}
 &=d_{(a}S_{bc)}
 -\frac{2}{15}\left[
 \delta_{ab}(Sd)_c+\delta_{ac}(Sd)_b+\delta_{bc}(Sd)_a\right],\\
 (L_Sd):n^3
 &=(d\cdot n)(S:nn)-\frac25(Sd)\cdot n.
 \end{split}
\tag{T6}
$$
Parentheses denote the average over the three distinct terms in $d_{(a}S_{bc)}$. The subtracted term removes its trace. Expanding (T3) through second order gives
$$
 -\kappa\left(q-\frac{q^2}{2}\right).
$$
The linear term has degrees one and two. In $q^2$, $(d\cdot n)^2$ and $(S:nn)^2$ are antipodally even, while the cross term is $2(d\cdot n)(S:nn)$. Its degree-three part is (T6). Consequently
$$
 O_\mu=\kappa L_Sd+R_3.
\tag{T7}
$$
The vector and shear therefore generate a seven-component angular octupole at second order. This is a coupling of already specified kinematics; it is not an additional free rank-three kinematic field.

Suppose a known bound satisfies
$$
 \sup_n|q(n)|\leq\epsilon<1.
$$
A sufficient choice is $\epsilon\geq |d|+\|S\|_{\rm op}$. The absolutely convergent logarithm series gives
$$
 \left|\log(1+q)-q+\frac{q^2}{2}\right|
 \leq\frac{\epsilon^3}{3(1-\epsilon)}.
$$
For any STF rank-three tensor $T$, spherical sixth moments give
$$
 \langle(T:n^3)^2\rangle=\frac{2}{35}T:T.
$$
Since $\mathsf P_3$ is an $L^2$ contraction under the normalized full-sphere measure, (T7) obeys the finite bound
$$
 \boxed{\quad
 \|R_3\|_F\leq E_3(\epsilon)
 :=\sqrt{\frac{35}{2}}\,
 \frac{\kappa\epsilon^3}{3(1-\epsilon)}.
 \quad}
\tag{T8}
$$
This bound controls truncation in the finite angular variable of the local law. It does not bound the omitted finite-redshift terms in $d_L$, an observer-frame error, or catalogue selection.

When $S=0$, the quadratic coupling vanishes and the leading optical octupole is cubic:
$$
 O_\mu=-\frac{\kappa}{3}\operatorname{STF}(d^{\otimes3})+R_{3,d},
 \qquad
 \|R_{3,d}\|_F\leq
 \sqrt{\frac{35}{2}}\,
 \frac{\kappa|d|^5}{5(1-|d|^2)},\quad |d|<1.
\tag{T9}
$$
Only the odd powers of the logarithm contribute to degree three, which proves the fifth-order remainder bound. For $d=-a\hat d$, (T9) has the positive sign of $-\kappa\log(1-a\hat d\cdot n)$ used in the retained zero-shear finite-source calculation. The acceleration--shear term in (T7) can therefore dominate that pure-dipole octupole when both dimensionless fields are of the same small order.

### 11.4 Constructive inversion and the residual morphology

For fixed $S\ne0$, the coupling map retains all three components of $d$. Its useful identities are
$$
 \begin{split}
 \|L_Sd\|_F^2
 &=\frac{S:S}{3}|d|^2+\frac25|Sd|^2,\\
 (L_Sd):S&=K_Sd,\qquad
 K_S=\frac{S:S}{3}I+\frac25S^2.
 \end{split}
\tag{T10}
$$
To prove the first equation, write $T_{abc}=d_{(a}S_{bc)}$. Then
$$
 T:T=\frac13|d|^2(S:S)+\frac23|Sd|^2,
 \qquad T_{aac}=\frac23(Sd)_c.
$$
For a symmetric rank-three tensor, removing its trace subtracts $3|T_{aa\cdot}|^2/5$ from its squared norm, which gives the first line of (T10). Contracting (T6) with $S_{bc}$ gives the second. In particular, $K_S\succeq(S:S)I/3>0$. If $\lambda_i$ are the eigenvalues of $S$, the singular values of $L_S$ are
$$
 s_i(L_S)=\sqrt{\frac{S:S}{3}+\frac25\lambda_i^2}.
\tag{T11}
$$
No choice of shear eigenaxes is needed to use $K_S$.

For an octupole $O$, define the least-squares coupling vector and residual by
$$
 \widehat d_S(O)=\frac1\kappa K_S^{-1}(O:S),\qquad
 O_\perp=O-\kappa L_S\widehat d_S(O).
\tag{T12}
$$
The contraction $O:S$ is the adjoint $L_S^*O$, so (T12) is the orthogonal projection onto the three-dimensional image of $L_S$. The residual lies in a four-dimensional complement and satisfies $O_\perp:S=0$. For the exact logarithmic local response,
$$
 \|O_{\mu,\perp}\|_F\leq E_3(\epsilon),\qquad
 |\widehat d_S(O_\mu)-d|
 \leq\frac{E_3(\epsilon)}{\kappa\min_i s_i(L_S)}.
\tag{T13}
$$
Projection cannot increase the remainder norm, and the second inequality follows from the pseudoinverse norm. As $S\to0$, the vector reconstruction becomes increasingly sensitive to fixed absolute octupole errors; the separate pure-dipole cubic law (T9) remains available. For nonzero $S$, the relative condition number of $L_S$ is bounded by $\sqrt{9/5}$: trace freedom gives $\lambda_i^2\leq2(S:S)/3$, while (T11) bounds its squared singular values between $(S:S)/3$ and $3(S:S)/5$. The divergence is in absolute inverse gain as the shear amplitude vanishes. Equations (T12)--(T13) describe a concrete morphology test: at quadratic order a general seven-component magnitude octupole must lie close to a specified three-dimensional coupling image, rather than merely share an axis or a scalar power with the quadrupole. The result also indicates which information an axis-only summary would discard.

### 11.5 The contraction geometry gains a physical realization

The operator in (T10) is the same positive operator that appears in the exact contraction ellipsoid of the quadrupole--octupole theorem. To see the connection, let $C_S:\mathrm{STF}_3\to\mathbb R^3$ denote $C_SO=O:S$. Then $C_S^*=L_S$ and $C_SC_S^*=K_S$. The abstract decomposition
$$
 O=L_SK_S^{-1}(O:S)+O_\perp,\qquad O_\perp\in\ker C_S
$$
is therefore the optical decomposition (T12). The quadratic response selects the minimum-norm lift of its contracted vector. Its four contraction-fibre coordinates vanish at that order; the full logarithmic response fills them only through the remainder in (T7). This connects the sharp tensor theorem to an explicit local observable mechanism.

The same relation gives a parity-sensitive consequence. For any vector $b$ define $\chi(S,b)=\det[b,Sb,S^2b]$, and for an octupole use the contraction definition $\chi(S,O)=\chi(S,O:S)$. On the quadratic optical response $O^{(2)}_\mu=\kappa L_Sd$,
$$
 \chi(S,O^{(2)}_\mu)
 =\kappa^3\det K_S\,\det[d,Sd,S^2d].
\tag{T13a}
$$
Indeed, $O^{(2)}_\mu:S=\kappa K_Sd$, and $K_S$ commutes with $S$, so that the same matrix $\kappa K_S$ multiplies all three determinant columns. Since $\det K_S>0$, the coupling preserves the sign of this local vector--shear pseudoscalar. For simple-spectrum $S$, in a positively oriented eigenframe its sign is that of
$$
 d_1d_2d_3\prod_{i<j}(\lambda_j-\lambda_i).
$$
Thus a generic acceleration direction with components along all three shear eigendirections can induce a chiral quadrupole--octupole pair in the magnitude field. Repeated eigenvalues or a missing vector component make this particular pseudoscalar vanish. This is a local geometric handedness under proper rotations, not a statement about parity violation in a stochastic cosmological ensemble. For the full logarithm the perturbation is controlled by (T8), and chirality stability must include that perturbation.

### 11.6 Embedding the bridge in the departure bundle

The physical state can now be propagated through an explicit tensor map. For a common state $Z$ containing $d$, $S$, angular response, calibration, and allowed errors, useful retained functionals are
$$
 x_\phi(Z)=\bigl(d,S,O_\mu,O_{\mu,\perp}\bigr),
 \qquad
 \Sigma_u^2=\frac{S:S}{6}.
\tag{T14}
$$
A joint region $C$ supplies the image $\phi(C)$; its support function describes the convex outer geometry while retaining the underlying tensor image for nonlinear morphology. Both $S$ and $d$ must be transformed with the same physical rotation. If a full-sphere octupole error radius $e_O$ and a bound $\epsilon$ are justified on the same event, then for fixed known $S\ne0$ a useful positive anchor radius is $E_3(\epsilon)+e_O$. The score
$$
 Q_{\rm coupling}
 =\frac{\|O_{\mu,\perp}\|_F}{E_3(\epsilon)+e_O}
\tag{T15}
$$
compares retained morphology with that specified response envelope. Uncertain $S$ requires the joint image over its admissible values, rather than insertion of a best-fit eigenframe into (T12). A zero anchor is handled by the corresponding exact set-membership question. The score is conditional on this optical model and on its supplied error bounds.

Under a named joint measure $\mu$, the associated exceedance is $\Pi_\mu(t)=\mu\{Q_{\rm coupling}>t\}$. A working Gaussian law, a posterior, and a finite collection of response scenarios give different versions of this quantity. The directional or tensor support information belongs to $F$; it does not determine $\mu$. Applying the construction across physically registered redshift or distance windows supplies a path $G_F$, with shared calibration and cross-window covariance retained. Window-dependent departures can then distinguish a change in dimensionless local morphology from changes induced by optical depth or processing. Such a path becomes a statement about $H(z,n)$ only when its windows, source congruence, and finite-redshift response have been specified.

The same STF and proper-rotation machinery can organize low-multipole CMB morphology. The bridge is mathematical and observational: nonlinear response can create a higher angular multipole, and full tensors reveal whether it has the constrained shape of a specified coupling. A common cosmological explanation of optical and CMB tensors additionally needs a model's distinct radiation-transfer and observer responses. Spatial homogeneity and a Bianchi Lie-algebra type are further structures; neither follows from (T1), (T7), or an agreement of tensor axes.

### 11.7 Synthetic verification

We evaluated the logarithmic response on a Gauss--Legendre--azimuthal full-sphere grid. The illustrative family uses
$$
 d=t(1,2,3)/\sqrt{14},\qquad S=t\operatorname{diag}(0.6,-0.2,-0.4),
 \qquad 0.002\leq t\leq0.25.
$$
The sufficient uniform bound is $\epsilon=1.6t\leq0.4$. Seven exact-rational cases verify the STF trace, norm identity, and contraction identity in (T10). For 45 amplitudes, the quadrature reproduces the quadratic coefficient and the reconstruction in (T12), and every measured exact-logarithm remainder lies below (T8). Comparing $40\times80$ and $60\times120$ grids gives a maximum octupole tensor difference $1.21\times10^{-14}$ magnitude. This quadrature comparison checks the finite synthetic calculation; the analytic bound follows from the proof above.

![Induced optical magnitude octupoles in a local angular response. Left: the exact logarithmic octupole (solid) and its leading acceleration--shear quadratic approximation (dashed), compared with the exact acceleration-only response and its cubic approximation (dotted). The coupled signal is quadratic at small common amplitude, while the pure-dipole signal is cubic. Right: the coupled approximation error and the analytic uniform envelope (T8). The parameters are dimensionless synthetic kinematics, not an observational fit. No finite-redshift propagation or CMB transfer is included.](../figures/theory_induced_octupole.png)



\FloatBarrier



### 11.8 A kinetic constraint for the acceleration input

A specified physical source model can constrain the vector entering the optical coupling. In a smooth energy frame with zero energy flux, conserved stress tensor, positive energy density \(\varepsilon\), and positive-semidefinite spatial stress \(P=pI+\pi\), the spatial momentum equation is

$$
M\frac{A}{c^2}=-g,\qquad M=\varepsilon I+P,\qquad
 g_a=D_ap+D^b\pi_{ab}.
$$

Since \(M\succeq\varepsilon I\), it has the explicit solution \(A=-c^2M^{-1}g\) and bound \(\|A\|\le c^2\|g\|/\varepsilon\). This follows from positivity and momentum conservation in the stipulated frame [32]. If \(\lambda_{\min}(M)\ge m>0\), \(\|\Delta M\|_{\rm op}\le\eta<m\), and \(\|\Delta g\|\le r\), the inverse resolvent identity gives

$$
\|\Delta A\|\le c^2\left\{\frac{r}{m-\eta}
+\frac{\eta\|g\|}{m(m-\eta)}\right\}.
$$

Dividing by a jointly bounded \(cH\) propagates this source information into \(d\). The gradient and stress must be determined for that energy frame; a source-centroid dipole alone does not supply them. Perturbative Vlasov predictions provide examples of scale-dependent acceleration and shear responses [41], whereas the present calculation uses the conservation equation algebraically and performs no kinetic evolution.


\FloatBarrier

## 12. From tensor morphology to cosmological interpretation

### 12.1 Four observable questions in a common representation

The full tensor representation makes four distinct questions accessible. Low-multipole morphology concerns the rotation orbit of an angular field. Kinematic inference concerns the expansion, shear, acceleration, and rotation of a stated congruence. Homogeneous-space classification concerns spatial symmetries and their evolution. A directional Hubble measurement concerns a distance--redshift response averaged over a stated observational window. The same STF algebra appears in several of these questions, but the maps between them carry physical information.

For the CMB, the sharp chirality envelope fixes a geometric normalization before a reference distribution is chosen. The processed Planck tensors then locate an observed morphology in this bounded shape space. Orbit intervals, phase interventions, and frequency contrasts retain information that a power spectrum or a fitted axis discards. A statistical anomaly requires a law for the processed field [44]. A convenient way to express the distinction is to retain both the geometric coordinate \(\mathcal C(y)\) and the law-indexed probability \(\Pi_\nu(t)=\nu\{\mathcal C(Y)>t\}\). The coordinate is fixed by the tensor; the probability also depends on \(\nu\), the statistic selection, and the treatment of processing.

For distances, the local map in Section 11 connects dimensionless acceleration and shear to optical angular multipoles. The exact ideal-field inverse recovers \(d\) and \(S\) from a normalized exponential of the complete magnitude field. A catalogue analysis instead estimates its selected-window coefficients. The four CF4 windows retain a monopole, a dipole, and a full STF quadrupole with their cross-window covariance. Their variation is therefore a measured property of that estimator and source cohort. To interpret it as \(H(z,n)\), one supplies the window response and finite-redshift remainder. Recent general cosmography develops precisely this distinction between a local coefficient and an effective finite-range fit [20,27–31].

For astrometry, the full reported-depth carrier and the spin-free pair statistic answer complementary questions. The former retains vector modes, cross-depth differences, and the common mode. The latter removes a rigid angular rotation through an exact algebraic identity. Their different kernels explain which components survive each reduction. Neither operation imposes the source-centroid response of a dust worldline. That response enters when a proper motion is mapped into the matter-frame quantities in the departure state.

### 12.2 Anisotropy classification and homogeneous geometry

A real STF rank-two tensor has a complete single-tensor rotation classification through its eigenvalues. Equivalently, its quadratic and cubic traces determine the characteristic polynomial

$$
\det(\lambda I-S)=\lambda^3-\frac12\operatorname{tr}(S^2)\lambda-\frac13\operatorname{tr}(S^3).
$$

Zero norm is the isotropic stratum; a repeated nonzero eigenvalue gives an axial stratum; three distinct eigenvalues give a triaxial stratum. For a tensor pair one also retains relative orientation and the octupole fibre. The sharp envelope and the four-dimensional kernel in Section 3 provide an explicit organization of that extra information. These are classifications of tensor morphology.

A Bianchi type specifies a three-dimensional Lie algebra acting transitively on spatial slices. In an orthonormal frame its structure constants can be written

$$
C^a{}_{bc}=\epsilon_{bcd}n^{da}+a_b\delta^a_c-a_c\delta^a_b,
\qquad n^{ab}=n^{ba},\qquad n^{ab}a_b=0.
$$

These structure variables are different from the shear eigenvalues. The spatially flat Bianchi I case has \(a=0,n=0\); the Bianchi V case has \(n=0\) and a nonzero \(a\). The constraint construction in Section 5 uses this distinction explicitly. It changes the allowed curvature while keeping the prescribed shear magnitude and tilt contribution. Conversely, the isotropic limits of spatially flat and open homogeneous models can have identical instantaneous \(H\), zero shear, and zero vorticity while retaining different spatial curvature. Local expansion data alone therefore leave these two examples unresolved. This example concerns those observables; adding curvature-sensitive or history-dependent measurements changes the observation map.

For a specified family \(b\), let \(\mathcal X_b\) contain its admissible matter, geometry, initial data, and history, and let \(\mathcal R_b\) map this state to the delivered temperature, polarization, distance, or astrometric coordinates. With an observational error set \(E\), its observable image is

$$
\mathcal M_b=\{\mathcal R_b(X,\eta):X\in\mathcal X_b,\ \eta\in\mathcal N_b\},
\qquad \mathcal K(y)=\{b:(y-E)\cap\mathcal M_b\ne\varnothing\}.
$$

This construction yields compatibility with the stated families. If two images intersect after their nuisance and error responses are included, the observation does not separate those points. If a valid error event holds, the true model image intersects \(y-E\); projecting this event supplies a confidence statement only within that specified family collection. The rotation action must be applied jointly to every tensor block and its covariance. Treating temperature and polarization orientations independently would enlarge the physical image.

The retained BIANCHI package temperature template supplies a concrete first image: a finite fit through \(\ell=12\) has rank 169, unit-variant scale \(2724.999989\), relative scale residual \(5.60\times10^{-8}\), and residual fraction \(0.134339\). It is a temperature representation with an unqualified absolute frame. The existing full E/B frequency coordinates specify additional observable blocks for a future common response. Near-isotropic Bianchi mode and polarized-transfer constructions provide the physical setting for that extension [33–36].

### 12.3 Joint tensor images and a redshift path

For each dataset we retain \(y_j=\mathcal R_j(X,\eta)+e_j\), with shared nuisance variables left shared. The common compatible state is obtained by intersecting the inverse images of the observational regions before computing a scalar functional. This order preserves calibration cancellation, covariance, and physical constraints. A support function summarizes the convex outer geometry of the resulting state; its underlying nonconvex image remains available for parity and family questions.

The departure bundle then has an explicit operational meaning. The tensor or scalar \(x_\phi\) records the chosen physical or observable functional. \(F\) retains its directional support and, where a measure and eligible sector exist, a supported fraction. \(Q\) compares the functional with a declared positive anchor. \(\Pi\) is its strict exceedance under a named joint measure. \(G_F\) records a registered depth path, including the reference state and cross-window uncertainty. These components can be evaluated at the observational level while a separately typed physical image is developed. In particular, a window index becomes a cosmological depth only through the specified source and optical response.

The calculations furnish a connected set of results in this representation. Chirality and orbit geometry characterize low-multipole morphology; the optical coupling supplies an explicit kinematic shape mechanism; the two-radius theorem isolates how radial diversity separates angular responses; and the windowed-flow identity keeps homogeneous motion distinct from residual structure. The selected likelihood, covariance unions, and source-specific sensitivity calculations then determine the statistical precision at which those mathematical distinctions can be used. A small conditional residual is informative about that model, while a large retained kernel identifies the additional response information needed to resolve the next physical question.


\FloatBarrier

## 13. Conclusions

The quadrupole--octupole contraction has an exact image ellipsoid, a four-dimensional kernel, and an attained chirality envelope with constant \(4\sqrt2/135\). These results organize amplitude, shape and handedness before a stochastic reference law is chosen. The local optical calculation supplies a physical use of the same adjoint: acceleration and shear generate a constrained three-dimensional magnitude-octupole image at quadratic order. Its complementary four components and an explicit angular remainder bound provide a test of that response shape. The full ideal angular field also admits an intercept-independent reconstruction of the dimensionless acceleration and shear.

The observational calculations retain the information needed to apply such mechanisms. Planck processing and frequency contrasts characterize finite low-multipole tensors; a power-preserving phase intervention changes the proper-rotation orbit. The grouped CF4 analysis gives four correlated directional rate fields, while the smaller selected cohort supports an explicit normalized likelihood and model-conditional finite-sample region. Its covariance-sensitive model ordering survives that more precise statistical formulation. Proper-motion depth contrasts, bias envelopes, and the spin-free pair construction expose different identifiable combinations, and the history-response power calculation shows why rank alone does not give useful precision.

The recovered mathematical results complete the connection. A normalized bulk-flow window retains finite-scale residuals and their cross-window covariance. Two radii can remove a four-dimensional angular-design ambiguity. The curvature contraction and congruence determine the vorticity sign in a normalized constraint; a hypersurface-normal construction has zero vorticity. Together these results give a tensor-based account of observed anisotropy, source response, and the information still needed for homogeneous-family comparison. The retained tensors, joint uncertainty and depth paths can be passed through a specified physical response without reconstructing their lost information from scalar summaries.

\clearpage

\FloatBarrier

## Appendix A. Fibres, orientation, and degeneracies of the tensor contraction

This appendix develops the geometry behind the contraction
\(v_i=O_{ijk}Q_{jk}\). The sharp envelope controls a particular pseudoscalar of
the tensor pair, whereas the contraction itself retains only three of the
seven octupole components. Describing the information that survives, and the
information left in its fibres, makes the equality and zero sets explicit.

Throughout, the ambient space is oriented Euclidean three-space. The tensors
\(Q\in\operatorname{STF}^2\) and \(O\in\operatorname{STF}^3\) are real,
and all norms use full ordered-index Frobenius contractions. Write

$$
t=\operatorname{tr}(Q^2),\qquad j=\operatorname{tr}(Q^3),\qquad
o=\|O\|,\qquad
L_QO=O:Q,\qquad M_Q=\frac t3I+\frac25Q^2.
\tag{A1}
$$

The contraction adjoint satisfies \(L_QL_Q^*=M_Q\). In particular,
\(M_Q\) is positive definite whenever \(Q\ne0\).

### A.1. Exact fibres and their rotation covariance

Fix \(Q\ne0\), a norm \(o\ge0\), and a contraction vector \(v\).
Define the minimum-norm lift

$$
O_0(Q,v)=L_Q^*M_Q^{-1}v.
\tag{A2}
$$

Every tensor with contraction \(v\) admits the unique decomposition

$$
O=O_0(Q,v)+K,\qquad K\in\ker L_Q.
\tag{A3}
$$

The two terms are orthogonal: for every such \(K\),
\(\langle L_Q^*M_Q^{-1}v,K\rangle
=\langle M_Q^{-1}v,L_QK\rangle=0\). Therefore

$$
\|O\|^2=v^TM_Q^{-1}v+\|K\|^2.
\tag{A4}
$$

Since \(L_Q\) is onto, its kernel has dimension four. It follows that the
image of the sphere \(\|O\|=o\) is exactly the solid ellipsoid

$$
\mathcal E_{Q,o}
=\{v\in\mathbb R^3:v^TM_Q^{-1}v\le o^2\}.
\tag{A5}
$$

This is a solid image even though the domain has fixed norm. For an interior
point, the residual norm in (A4) can be assigned to any direction in the
four-dimensional kernel. More precisely, the fibre above \(v\) is

$$
\mathcal F_{Q,o}(v)=O_0(Q,v)+
\left\{K\in\ker L_Q:
\|K\|^2=o^2-v^TM_Q^{-1}v\right\}.
\tag{A6}
$$

It is empty outside the ellipsoid, a translated three-sphere at an interior
point, and a single tensor at a boundary point. The radius of the three-sphere
is the square root of the residual in (A6). At \(o=0\), the ellipsoid and its
only nonempty fibre both reduce to zero. The zero quadrupole is different:
then \(L_Q=0\), the kernel has dimension seven, and the image consists only
of \(v=0\).

The construction is covariant under rotations. If
\(Q'=RQR^T\) and \(O'=R^{\otimes3}O\), with \(R\in SO(3)\), direct
contraction gives \(L_{Q'}O'=R(L_QO)\), while
\(M_{Q'}=RM_QR^T\). Thus

$$
R\mathcal E_{Q,o}=\mathcal E_{Q',o},\qquad
R^{\otimes3}\mathcal F_{Q,o}(v)=\mathcal F_{Q',o}(Rv).
\tag{A7}
$$

The entire family is \(SO(3)\)-equivariant. For an individually fixed
\(Q\), equivariance applies to its stabilizer, the rotations satisfying
\(RQR^T=Q\). This distinction prevents an arbitrary rotation of \(v\) from
being interpreted as an operation that leaves a prescribed quadrupole fixed.

The kernel itself has a useful explicit basis. In an orthonormal eigenframe
of a nonzero quadrupole, put

$$
d=(\lambda_2-\lambda_3,\lambda_3-\lambda_1,
\lambda_1-\lambda_2).
\tag{A7a}
$$

For each \(i\), define a symmetric tensor \(K^{(i)}\) by
\(K^{(i)}_{ijj}=d_j\) for \(j=1,2,3\), with all entries outside the
permutations of these triples set to zero. Finally, let \(K^{(0)}\) have
value one on the six permutations of \(123\) and zero elsewhere.
The identities \(\sum_jd_j=0\) and \(\sum_j\lambda_jd_j=0\) show
respectively that each tensor is trace free and lies in the contraction
kernel. Their component supports are disjoint, so they are mutually
orthogonal. Since \(d\ne0\), all four are nonzero and form a basis.

The norms are also explicit:

$$
\|K^{(0)}\|^2=6,\qquad
\|K^{(i)}\|^2=d_i^2+3\sum_{j\ne i}d_j^2
=9t-2d_i^2,
\tag{A7b}
$$

where \(\sum_jd_j^2=3t\) was used. Dividing by these norms gives an
orthonormal basis \(E^{(0)},\ldots,E^{(3)}\). An interior fibre can
therefore be parameterized without further linear equations as

$$
O=O_0(Q,v)+\rho\sum_{a=0}^3\eta_a E^{(a)},\qquad
\sum_{a=0}^3\eta_a^2=1,\qquad
\rho^2=o^2-v^TM_Q^{-1}v.
\tag{A7c}
$$

This construction remains valid for a nonzero quadrupole with repeated
eigenvalues; only the chosen eigenframe becomes nonunique. It separates the
contraction constraint, already solved by \(O_0\), from the remaining norm
constraint, represented by an ordinary unit sphere. In particular, changes
of the four parameters \(\eta_a\) leave \(v\), all its quadrupole
iterates, and their determinant unchanged. The existence of these explicit
directions is the source of the octupole ambiguity, independently of any
numerical inversion procedure.

### A.2. Component conventions and a saturated lift

Symmetry does not make the independent tensor entries orthonormal
coordinates. If \([Q]=q\) and \([O]=u\) denote their amplitude units, the
following formulas specify both dimensions and multiplicities.

| Quantity | Full-contraction formula | Units and component weights |
|---|---|---|
| \(t\) | \(\sum_iQ_{ii}^2+2\sum_{i<j}Q_{ij}^2\) | \(q^2\); weights 1, 2 |
| \(o^2\) | \(\sum_iO_{iii}^2+3\sum_{i\ne j}O_{iij}^2+6O_{123}^2\) | \(u^2\); weights 1, 3, 6 |
| \(v_i\) | \(\sum_jO_{ijj}Q_{jj}+2\sum_{j<k}O_{ijk}Q_{jk}\) | \(qu\); contraction weights 1, 2 |
| \(M_Q\) | \(tI/3+2Q^2/5\) | \(q^2\) |
| \(\chi\) | \(\det[v,Qv,Q^2v]\) | \(q^6u^3\) |
| \(C\) | \(135\chi/(4\sqrt2\,t^3o^3)\) | dimensionless |

A concrete boundary lift also displays the sharpness of the global envelope.
Take

$$
Q_* =\operatorname{diag}(-1/\sqrt2,0,1/\sqrt2),\qquad
w_*=(\sqrt{10}/4,1,\sqrt{10}/4),\qquad
O_*=L_{Q_*}^*w_*.
\tag{A8}
$$

The nonzero independent components are

$$
\begin{aligned}
O_{111}&=-3\sqrt5/20,& O_{333}&=3\sqrt5/20,\\
O_{112}&=-\sqrt2/6,& O_{233}&=\sqrt2/6,\\
O_{113}&=-7\sqrt5/60,& O_{133}&=7\sqrt5/60,\\
O_{122}&=\sqrt5/30,& O_{223}&=-\sqrt5/30,
\end{aligned}
\tag{A9}
$$

with \(O_{123}=O_{222}=0\) and permutation symmetry supplying the remaining
entries. Each trace vanishes. The multiplicities in the table give the exact
norm check

$$
\|O_*\|^2=\frac9{40}+\frac13+\frac{49}{120}+\frac1{30}=1.
\tag{A10}
$$

Moreover,

$$
M_{Q_*}=\operatorname{diag}(8/15,1/3,8/15),\qquad
v_*=(2\sqrt{10}/15,1/3,2\sqrt{10}/15),
\qquad \chi(Q_*,O_*)=\frac{4\sqrt2}{135}.
\tag{A11}
$$

These component identities check the trace projection, norm convention, and
determinant sign simultaneously. Multiplying the two tensors by positive
constants supplies a saturated pair at any prescribed nonzero norms.
Replacing \(O_*\) by \(-O_*\) gives the opposite endpoint.

### A.3. Equality strata and the normalized shape domain

Suppose first that \(Q\ne0\) has distinct eigenvalues and \(o>0\).
Choose a positively oriented orthonormal eigenframe and set

$$
m_i=\frac t3+\frac25\lambda_i^2,\qquad
z_i=\frac{v_i}{o\sqrt{m_i}}.
\tag{A12}
$$

The ellipsoid becomes the unit ball \(\sum_i z_i^2\le1\). If
\(\chi_{\max}(Q,o)\) is the positive fixed-quadrupole maximum, then

$$
\frac{|\chi|}{\chi_{\max}(Q,o)}
=3\sqrt3\,|z_1z_2z_3|.
\tag{A13}
$$

Consequently saturation occurs precisely at the eight boundary points
\(z_i=\epsilon_i/\sqrt3\), where \(\epsilon_i=\pm1\). Their fibres are
singletons, so no kernel component can be added while preserving both the
norm and saturation. Four choices give each sign of chirality. In contrast,
the zero set inside the ball is the union of its three coordinate-plane
sections. An interior point of that zero set still supports a three-sphere
of octupoles with the same contraction.

The eight saturated vectors need not be regarded as eight distinct shapes
of the pair. The proper rotations preserving a simple diagonal quadrupole
are the diagonal sign matrices with determinant one. They connect the four
balanced sign choices having a given product
\(\epsilon_1\epsilon_2\epsilon_3\). Thus the saturated lifts form two
rotation classes at fixed \(Q\), distinguished by the sign of chirality.
This also explains why arbitrary choices of eigenvector signs cannot change
the signed answer when a positively oriented frame is maintained.

The dependence on quadrupole shape can be expressed without an eigenvalue
ordering. For \(t>0\), define

$$
r=\frac{j^2}{t^3},\qquad 0\le r\le\frac16.
\tag{A14}
$$

Combining the discriminant and image-ellipsoid determinant gives the exact
normalized envelope

$$
|C|\le E(r),\qquad
E(r)^2=(1-6r)\left(1+\frac{3r}{40}\right).
\tag{A15}
$$

The value \(r=0\) contains the global equality shapes; \(r=1/6\) is the
repeated-eigenvalue endpoint. At that endpoint every octupole has
\(\chi=0\), so every octupole attains the zero fixed-quadrupole maximum.
The balanced-coordinate equality characterization is therefore restricted
to simple spectra. Repeated eigenspaces also remove any distinguished choice
of the corresponding eigenvectors.

The signed score \(C\) is defined for \(t>0\) and \(o>0\), including
repeated spectra, where it equals zero. The utilization
\(|C|/E(r)\) requires the additional restriction \(r<1/6\).
Neither ratio has a prescribed value on its excluded strata. The underlying
polynomial \(\chi\) and its unnormalized inequality remain well defined
there. Positive amplitude rescalings cancel from \(C\); reversing the sign
of \(O\) reverses \(C\), whereas reversing the sign of \(Q\) leaves it
unchanged, consistently with
\(\chi(aQ,bO)=a^6b^3\chi(Q,O)\).

### A.4. Gram determinant and the cyclic frame

Let \(B=[v,Qv,Q^2v]\) and define moments
\(h_k=v^TQ^kv\). The squared chirality is the Gram determinant

$$
\chi^2=\det(B^TB)
=\det\begin{pmatrix}
h_0&h_1&h_2\\
h_1&h_2&h_3\\
h_2&h_3&h_4
\end{pmatrix}.
\tag{A16}
$$

Thus \(|\chi|\) is the volume of the parallelepiped formed by the three
contraction-derived vectors. This description uses no eigenframe. It also
separates orientation from metric information: the Gram matrix determines
the squared volume but cannot determine its sign.

The trace-free characteristic identity is

$$
Q^3=\frac t2Q+\frac j3I.
\tag{A17}
$$

It reduces the last two moments to
\(h_3=(t/2)h_1+(j/3)h_0\) and
\(h_4=(t/2)h_2+(j/3)h_1\). Equations (A16)–(A17) therefore express
\(\chi^2\) using only \(t,j,h_0,h_1,h_2\), providing a direct algebraic
consistency relation among these scalars.

For a simple spectrum, the first three moments recover the squared
eigenframe components of the contraction. With
\(\{i,j,k\}=\{1,2,3\}\), the explicit inversion is

$$
v_i^2=
\frac{h_2-(\lambda_j+\lambda_k)h_1+\lambda_j\lambda_kh_0}
{(\lambda_i-\lambda_j)(\lambda_i-\lambda_k)}.
\tag{A17a}
$$

To verify it, substitute \(h_a=\sum_\ell\lambda_\ell^av_\ell^2\)
into the numerator. The polynomial
\((x-\lambda_j)(x-\lambda_k)\) annihilates the contributions from the
other two eigendirections, leaving precisely the denominator times
\(v_i^2\). Nonnegativity of these three recovered values is a necessary
consistency condition on proposed moment data. Together with
\(\sum_i v_i^2/m_i\le o^2\), it is also sufficient for realization by
some octupole of the prescribed norm: choose square roots with any desired
component signs and use (A6). A claimed signed determinant must additionally
agree with their product and the eigenvalue Vandermonde factor. This provides
an explicit realization test rather than treating every collection of
scalar moments as automatically admissible.

When \(\chi\ne0\), the columns of \(B\) form a basis and

$$
Q=BJB^{-1},\qquad
J=\begin{pmatrix}
0&0&j/3\\
1&0&t/2\\
0&1&0
\end{pmatrix}.
\tag{A18}
$$

Indeed, the first two columns of \(QB\) shift to the next columns of
\(B\), and its last column is fixed by (A17). If two nonsingular cyclic
frames have the same Gram matrix, their connecting matrix is orthogonal.
If their determinants have the same sign, it is a proper rotation. With the
same \(t,j\), (A18) then also maps one quadrupole to the other. Accordingly,
the Gram data and orientation determine the rotation class of the projected
pair \((Q,v)\) on this nonsingular stratum.

This conclusion does not reconstruct the full octupole. At a fixed norm, an
interior contraction still has the three-sphere ambiguity in (A6), even when
its cyclic frame is invertible. Only a boundary contraction has a unique lift
under the stipulated norm constraint.

### A.5. A chiral tensor pair with zero contraction

Call a pair achiral if an orientation-reversing orthogonal transformation
preserves both tensors. A nonzero \(\chi\) excludes such a transformation,
because \(\chi\) changes sign under it. The converse fails, as the following
explicit pair demonstrates.

Take \(Q=\operatorname{diag}(-1,0,1)\). Specify the independent octupole
components by

$$
\begin{array}{c|rrrrrrrrrr}
ijk&111&112&113&122&123&133&222&223&233&333\\\hline
O_{ijk}&1&1&1&-2&0&1&-2&-2&1&1
\end{array}
\tag{A19}
$$

and extend by permutation symmetry. Each of its three traces is
\(1-2+1=0\). Direct contraction gives

$$
v_i=-O_{i11}+O_{i33}=0,\qquad
\|Q\|^2=2,\qquad \|O\|^2=6+3(12)=42.
\tag{A20}
$$

Thus \(\chi=0\) and \(C=0\), despite both tensors being nonzero and the
quadrupole having a simple spectrum.

To determine the symmetry of the pair, let \(R\) be orthogonal and suppose
\(RQR^T=Q\). Multiplication on the right by \(R\) gives \(RQ=QR\).
Because the three eigenvalues are distinct, \(R\) preserves each
one-dimensional eigenspace. Hence
\(R=\operatorname{diag}(s_1,s_2,s_3)\), with \(s_i=\pm1\).
Preservation of the three nonzero components
\(O_{111}=1\), \(O_{222}=-2\), and \(O_{333}=1\) requires
\(s_i^3=1\) for each \(i\), so all three signs equal \(+1\).
The joint orthogonal stabilizer is therefore the identity. In particular,
there is no improper symmetry, and the pair is chiral under the stated
definition.

The example lies at the centre of the contraction ellipsoid. It shows
explicitly how orientation information in the octupole can survive entirely
within \(\ker L_Q\), beyond the three vectors used to form \(\chi\).
The same mechanism is not confined to this particular choice of integers.
For any simple-spectrum quadrupole, every \(d_i\) in (A7a) is nonzero.
A kernel tensor whose coefficients along all three \(K^{(i)}\) are
nonzero consequently has three nonzero pure components \(O_{iii}\).
The preceding sign argument again excludes every nonidentity orthogonal
stabilizer. These coefficient choices form an open dense subset of the
four-dimensional kernel, and of each nonzero fixed-norm sphere within it.
All of them have zero contraction. Thus chirality of the pair is compatible
with a completely collapsed contraction-derived frame across a full family
of tensors, not only at a single exceptional example.
Consequently, the vanishing of this pseudoscalar detects a degeneracy of the
chosen contraction-derived frame; it does not certify an improper symmetry
of the original tensor pair.

\clearpage

\FloatBarrier

## Appendix B. Numerical tensor-shape catalogue

The table lists every retained processing configuration. P denotes the pinned-primary source and C the cached-pilot source; Full, HM1/HM2 and OE1/OE2 denote the full, half-mission and odd/even products. All rows refer to one observed sky. The cutoff column records the registered processing setting, while the tensors analysed here retain multipoles two and three. The secondary angular window is given in degrees. The shape coordinate is \(r=j^2/t^3\), and \(U\) is the absolute chirality divided by the sharp fixed-quadrupole envelope. \(U\) is defined here because all sixty quadrupoles have distinct eigenvalues and both tensor norms are positive. Values are rounded only for display; the accompanying data file retains exact rational squared quantities.

| Source | Cutoff | Window | Product | C | r | \(U\) |
|:--|--:|--:|:--|--:|--:|--:|
| P | 32 | 0 | FULL | -0.0967707 | 0.0582918 | 0.1197448 |
| P | 32 | 0 | HM1 | +0.0087605 | 0.0276758 | 0.0095832 |
| P | 32 | 0 | HM2 | -0.1360855 | 0.0149100 | 0.1425344 |
| P | 32 | 0 | OE1 | -0.1112312 | 0.0326117 | 0.1238737 |
| P | 32 | 0 | OE2 | -0.0727370 | 0.0008517 | 0.0729213 |
| P | 64 | 0 | FULL | -0.0967707 | 0.0582918 | 0.1197448 |
| P | 64 | 0 | HM1 | +0.0087605 | 0.0276758 | 0.0095832 |
| P | 64 | 0 | HM2 | -0.1360855 | 0.0149100 | 0.1425344 |
| P | 64 | 0 | OE1 | -0.1112312 | 0.0326117 | 0.1238737 |
| P | 64 | 0 | OE2 | -0.0727370 | 0.0008517 | 0.0729213 |
| P | 128 | 0 | FULL | -0.0967707 | 0.0582918 | 0.1197448 |
| P | 128 | 0 | HM1 | +0.0087605 | 0.0276758 | 0.0095832 |
| P | 128 | 0 | HM2 | -0.1360855 | 0.0149100 | 0.1425344 |
| P | 128 | 0 | OE1 | -0.1112312 | 0.0326117 | 0.1238737 |
| P | 128 | 0 | OE2 | -0.0727370 | 0.0008517 | 0.0729213 |
| C | 32 | 0 | FULL | -0.0967544 | 0.0582656 | 0.1197103 |
| C | 32 | 20 | FULL | -0.0329415 | 0.1609136 | 0.1762429 |
| C | 32 | 30 | FULL | +0.0787905 | 0.1284010 | 0.1636487 |
| C | 32 | 0 | HM1 | +0.0087791 | 0.0276764 | 0.0096035 |
| C | 32 | 20 | HM1 | +0.0467971 | 0.1370341 | 0.1104176 |
| C | 32 | 30 | HM1 | +0.0185430 | 0.1376431 | 0.0442078 |
| C | 32 | 0 | HM2 | -0.1360759 | 0.0149228 | 0.1425303 |
| C | 32 | 20 | HM2 | -0.1210560 | 0.0171039 | 0.1277087 |
| C | 32 | 30 | HM2 | -0.0542555 | 0.0973739 | 0.0838386 |
| C | 32 | 0 | OE1 | -0.1112154 | 0.0326035 | 0.1238524 |
| C | 32 | 20 | OE1 | -0.0726205 | 0.1292157 | 0.1524608 |
| C | 32 | 30 | OE1 | -0.0208359 | 0.1360021 | 0.0483297 |
| C | 32 | 0 | OE2 | -0.0727282 | 0.0008529 | 0.0729127 |
| C | 32 | 20 | OE2 | -0.1018649 | 0.0525224 | 0.1228480 |
| C | 32 | 30 | OE2 | -0.0589879 | 0.1378452 | 0.1411223 |
| C | 64 | 0 | FULL | -0.0967663 | 0.0582445 | 0.1197134 |
| C | 64 | 20 | FULL | -0.0309071 | 0.1609380 | 0.1657113 |
| C | 64 | 30 | FULL | +0.0784533 | 0.1285145 | 0.1631896 |
| C | 64 | 0 | HM1 | +0.0087820 | 0.0276551 | 0.0096060 |
| C | 64 | 20 | HM1 | +0.0484694 | 0.1369326 | 0.1141685 |
| C | 64 | 30 | HM1 | +0.0194851 | 0.1395579 | 0.0480630 |
| C | 64 | 0 | HM2 | -0.1360822 | 0.0149188 | 0.1425351 |
| C | 64 | 20 | HM2 | -0.1168030 | 0.0161830 | 0.1228487 |
| C | 64 | 30 | HM2 | -0.0547424 | 0.1011119 | 0.0869572 |
| C | 64 | 0 | OE1 | -0.1111977 | 0.0325869 | 0.1238250 |
| C | 64 | 20 | OE1 | -0.0646239 | 0.1304295 | 0.1379199 |
| C | 64 | 30 | OE1 | -0.0202729 | 0.1365426 | 0.0474430 |
| C | 64 | 0 | OE2 | -0.0727238 | 0.0008528 | 0.0729082 |
| C | 64 | 20 | OE2 | -0.1054807 | 0.0521083 | 0.1269805 |
| C | 64 | 30 | OE2 | -0.0592737 | 0.1373823 | 0.1406835 |
| C | 128 | 0 | FULL | -0.0968182 | 0.0582357 | 0.1197728 |
| C | 128 | 20 | FULL | -0.0321132 | 0.1605578 | 0.1667358 |
| C | 128 | 30 | FULL | +0.0783902 | 0.1258484 | 0.1576589 |
| C | 128 | 0 | HM1 | +0.0087588 | 0.0276634 | 0.0095809 |
| C | 128 | 20 | HM1 | +0.0463241 | 0.1376598 | 0.1104716 |
| C | 128 | 30 | HM1 | +0.0196692 | 0.1377823 | 0.0470054 |
| C | 128 | 0 | HM2 | -0.1361120 | 0.0149401 | 0.1425761 |
| C | 128 | 20 | HM2 | -0.1185700 | 0.0158968 | 0.1245900 |
| C | 128 | 30 | HM2 | -0.0487727 | 0.1013958 | 0.0776420 |
| C | 128 | 0 | OE1 | -0.1112554 | 0.0325753 | 0.1238840 |
| C | 128 | 20 | OE1 | -0.0660810 | 0.1310960 | 0.1423410 |
| C | 128 | 30 | OE1 | -0.0201044 | 0.1347275 | 0.0456951 |
| C | 128 | 0 | OE2 | -0.0727252 | 0.0008517 | 0.0729094 |
| C | 128 | 20 | OE2 | -0.1057087 | 0.0526604 | 0.1275601 |
| C | 128 | 30 | OE2 | -0.0531381 | 0.1387269 | 0.1291134 |

At zero secondary window the primary values are identical across the three recorded cutoffs at the stored precision. This repeats the same low-order tensor information; it does not supply additional realizations. The pilot zero-window entries provide a comparison with independently cached processing, and the nonzero-window rows change the angular operator. Keeping these identifiers with each tensor makes these different sources of repetition explicit.

\clearpage

\FloatBarrier

## References


[1] Maartens, R., Ellis, G. F. R. & Stoeger, W. R., “Limits on anisotropy and inhomogeneity from the cosmic background radiation,” *Phys. Rev. D* **51**, 1525–1535 (1995). [DOI](https://doi.org/10.1103/PhysRevD.51.1525).

[2] Stoeger, W. R., Maartens, R. & Ellis, G. F. R., “Proving almost-homogeneity of the universe,” *ApJ* **443**, 1–5 (1995). [DOI](https://doi.org/10.1086/175496).

[3] Nilsson, U. S., Uggla, C., Wainwright, J. & Lim, W. C., “An almost isotropic cosmic microwave temperature does not imply an almost isotropic universe,” *ApJ* **522**, L1 (1999). [DOI](https://doi.org/10.1086/312209).

[4] Copi, C. J., Huterer, D. & Starkman, G. D., “Multipole vectors—a new representation of the CMB sky,” *Phys. Rev. D* **70**, 043515 (2004). [DOI](https://doi.org/10.1103/PhysRevD.70.043515).

[5] Land, K. & Magueijo, J., “The multipole vectors of the Wilkinson Microwave Anisotropy Probe, and their frames and invariants,” *MNRAS* **362**, 838–846 (2005). [DOI](https://doi.org/10.1111/j.1365-2966.2005.09310.x).

[6] Dennis, M. R. & Land, K., “Probability density of the multipole vectors for a Gaussian cosmic microwave background,” *MNRAS* **383**, 424–434 (2008). [DOI](https://doi.org/10.1111/j.1365-2966.2007.12484.x).

[7] Smith, G. F., “On isotropic functions of symmetric tensors, skew-symmetric tensors and vectors,” *Int. J. Eng. Sci.* **9**, 899–916 (1971). [DOI](https://doi.org/10.1016/0020-7225(71)90023-1).

[8] Olive, M. & Auffray, N., “Isotropic invariants of a completely symmetric third-order tensor,” *J. Math. Phys.* **55**, 092901 (2014). [DOI](https://doi.org/10.1063/1.4895466).

[9] Harris, A. B., Kamien, R. D. & Lubensky, T. C., “Molecular chirality and chiral parameters,” *Rev. Mod. Phys.* **71**, 1745–1757 (1999). [DOI](https://doi.org/10.1103/RevModPhys.71.1745).

[10] Hattne, J. & Lamzin, V. S., “A moment invariant for evaluating the chirality of three-dimensional objects,” *J. R. Soc. Interface* **8**, 144–151 (2011). [DOI](https://doi.org/10.1098/rsif.2010.0297).

[11] Pisanty, E. *et al.*, “Chiral moments make chiral measures” (2026). [arXiv:2603.26793](https://arxiv.org/abs/2603.26793).

[12] Chandrasekaran, V., Recht, B., Parrilo, P. A. & Willsky, A. S., “The convex geometry of linear inverse problems,” *Found. Comput. Math.* **12**, 805–849 (2012). [DOI](https://doi.org/10.1007/s10208-012-9135-7).

[13] Beresteanu, A. & Molinari, F., “Asymptotic properties for a class of partially identified models,” *Econometrica* **76**, 763–814 (2008). [DOI](https://doi.org/10.1111/j.1468-0262.2008.00859.x).

[14] Beresteanu, A., Molchanov, I. & Molinari, F., “Partial identification using random set theory,” *J. Econometrics* **166**, 17–32 (2012). [DOI](https://doi.org/10.1016/j.jeconom.2011.06.003).

[15] Makarov, G. D., “Estimates for the distribution function of a sum of two random variables when the marginal distributions are fixed,” *Theory Probab. Appl.* **26**, 803–806 (1982). [DOI](https://doi.org/10.1137/1126086).

[16] Mignard, F. & Klioner, S., “Analysis of astrometric catalogues with vector spherical harmonics,” *A&A* **547**, A59 (2012). [DOI](https://doi.org/10.1051/0004-6361/201219927).

[17] Hall, A., “Cosmology with extragalactic proper motions: harmonic formalism, estimators, and forecasts,” *MNRAS* **486**, 145 (2019). [DOI](https://doi.org/10.1093/mnras/stz648).

[18] Makarov, V. V., “Kinematic distortions of the high-redshift universe as seen from quasar proper motions,” *Nature Astronomy* (2025). [DOI](https://doi.org/10.1038/s41550-025-02591-x).

[19] von Hausegger, S. & Dalang, C., “Redshift tomography of the kinematic matter dipole” (2025). [arXiv:2412.13162](https://arxiv.org/abs/2412.13162).

[20] Adamek, J. *et al.*, “Towards cosmography of the local universe,” *Open J. Astrophys.* **7** (2024). [DOI](https://doi.org/10.33232/001c.118782).

[21] Tully, R. B. *et al.*, “Cosmicflows-4,” *ApJ* **944**, 94 (2023). [arXiv:2209.11238](https://arxiv.org/abs/2209.11238).

[22] Scolnic, D. *et al.*, “The Pantheon+ analysis: the full data set and light-curve release,” *ApJ* **938**, 113 (2022). [arXiv:2112.03863](https://arxiv.org/abs/2112.03863).

[23] Brout, D. *et al.*, “The Pantheon+ analysis: SuperCal-Fragilistic cross calibration, retrained SALT2 light curve model, and calibration systematic uncertainty,” *ApJ* **938**, 111 (2022). [arXiv:2112.03864](https://arxiv.org/abs/2112.03864).

[24] Brout, D. *et al.*, “The Pantheon+ analysis: cosmological constraints,” *ApJ* **938**, 110 (2022). [arXiv:2202.04077](https://arxiv.org/abs/2202.04077).

[25] Gaia Collaboration, “Gaia Early Data Release 3: The celestial reference frame (Gaia-CRF3),” *A&A* **667**, A148 (2022). [arXiv:2204.12574](https://arxiv.org/abs/2204.12574).

[26] Carr, A. *et al.*, “The Pantheon+ analysis: improving the redshifts and peculiar velocities of Type Ia supernovae,” *PASA* **39**, e046 (2022). [arXiv:2112.01471](https://arxiv.org/abs/2112.01471).


[27] Kristian, J. & Sachs, R. K., “Observations in cosmology,” *ApJ* **143**, 379 (1966); republication in *Gen. Relativ. Gravit.* **43** (2011). [DOI](https://doi.org/10.1007/s10714-010-1114-1).

[28] Heinesen, A., “Multipole decomposition of the general luminosity distance 'Hubble law'—a new framework for observational cosmology,” *JCAP* **05**, 008 (2021). [arXiv:2010.06534](https://arxiv.org/abs/2010.06534).

[29] Maartens, R., Santiago, J., Clarkson, C., Kalbouneh, B. & Marinoni, C., “Covariant cosmography: the observer-dependence of the Hubble parameter,” *JCAP* **09**, 070 (2024). [arXiv:2312.09875](https://arxiv.org/abs/2312.09875).

[30] Bendtsen, J. B., Heinesen, A. & Koksbang, S. M., “Cosmography for a general spacetime centred at arbitrary redshift” (2026). [arXiv:2608.07008](https://arxiv.org/abs/2608.07008).

[31] Kalbouneh, B. *et al.*, “The anisotropic expansion rate of the local Universe and its covariant cosmographic interpretation,” *JCAP* **03**, 084 (2026). [arXiv:2510.02510](https://arxiv.org/abs/2510.02510).

[32] Clarkson, C. & Maartens, R., “Beyond dust in local cosmography: covariant kinetic theory” (2026). [arXiv:2610.04284v1](https://arxiv.org/abs/2610.04284v1).

[33] Pontzen, A. & Challinor, A., “Linearization of homogeneous, nearly-isotropic cosmological models,” *Class. Quantum Grav.* **28**, 185007 (2011). [arXiv:1009.3935](https://arxiv.org/abs/1009.3935).

[34] Saadeh, D., Feeney, S. M., Pontzen, A., Peiris, H. V. & McEwen, J. D., “A framework for testing isotropy with the cosmic microwave background,” *MNRAS* **462**, 1802–1811 (2016). [arXiv:1604.01024](https://arxiv.org/abs/1604.01024).

[35] Saadeh, D. *et al.*, “How isotropic is the Universe?”, *Phys. Rev. Lett.* **117**, 131302 (2016). [DOI](https://doi.org/10.1103/PhysRevLett.117.131302).

[36] Sung, R., Short, J. & Coles, P., “Statistical characterization of temperature patterns in anisotropic cosmologies,” *MNRAS* **412**, 492–502 (2011). [arXiv:1004.1925](https://arxiv.org/abs/1004.1925).

[37] Boubel, P., Colless, M., Said, K. & Staveley-Smith, L., “Testing anisotropic Hubble expansion” (2024). [arXiv:2412.14607](https://arxiv.org/abs/2412.14607).

[38] Salzano, V., Beltrán Jiménez, J., Bettoni, D., Brax, P. & Valade, A., “Updates on dipolar anisotropy in local measurements of the Hubble constant from Cosmicflows-4” (2026 revision). [arXiv:2512.02526v2](https://arxiv.org/abs/2512.02526v2).

[39] Baldi, P. & Marinucci, D., “Some characterizations of the spherical harmonics coefficients for isotropic random fields,” *Statist. Probab. Lett.* **77**, 490–496 (2007). [arXiv:math/0606709](https://arxiv.org/abs/math/0606709).

[40] Planck Collaboration, “Planck 2018 results. IV. Diffuse component separation,” *A&A* **641**, A4 (2020). [arXiv:1807.06208](https://arxiv.org/abs/1807.06208).

[41] Clarkson, C. & Maartens, R., “Beyond dust in local cosmography: perturbative Vlasov predictions” (2026). [arXiv:2610.25145v1](https://arxiv.org/abs/2610.25145v1).

[42] Remazeilles, M., Delabrouille, J. & Cardoso, J.-F., “CMB and SZ effect separation with constrained internal linear combinations,” *MNRAS* **410**, 2481–2487 (2011). [arXiv:1006.5599](https://arxiv.org/abs/1006.5599).

[43] Storey-Fisher, K. *et al.*, “Quaia, the Gaia-unWISE quasar catalog: an all-sky spectroscopic quasar sample,” *ApJ* **964**, 69 (2024). [arXiv:2306.17749](https://arxiv.org/abs/2306.17749).

[44] Planck Collaboration, “Planck 2018 results. VII. Isotropy and statistics of the CMB,” *A&A* **641**, A7 (2020). [DOI](https://doi.org/10.1051/0004-6361/201935201).
