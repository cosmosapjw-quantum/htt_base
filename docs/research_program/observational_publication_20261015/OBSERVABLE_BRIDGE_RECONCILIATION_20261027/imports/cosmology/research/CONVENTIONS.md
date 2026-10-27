# Observed spherical coefficients and the covariant radiation hierarchy

Internal convention note, 2026-10-26. Scope: bounded source/convention work (R2–R3); v15 improves the existing HTT observation-to-physics map. No new novelty study, source edit, solver or publication action is involved.

## 1. Pin the observed field and the hierarchy index

A coefficient denoted \(C_{\ell m}\) must carry a field label. For an outward sky direction \(n\), write
\[
X(n)=\sum_{\ell m}C^X_{\ell m}Y_{\ell m}(n),\qquad
C^X_{\ell m}=\int X(n)Y^*_{\ell m}(n)\,d\Omega,
\quad\int|Y_{\ell m}|^2d\Omega=1.
\tag{1}
\]
Examples are temperature coefficients in K, dimensionless \(\Theta=\delta T/T_0\), frequency radiance coefficients, and bolometric energy-density coefficients. For a real map, \(C^X_{\ell,-m}=(-1)^mC^{X*}_{\ell m}\). The map power
\(\widehat C^X_\ell=(2\ell+1)^{-1}\sum_m|C^X_{\ell m}|^2\)
is a different object, with squared units; a theoretical ensemble \(C_\ell\) is a further statistical specification. Powers alone discard the phase/orientation information needed to reconstruct a particular radiation tensor.

Use signature \((-+++)\), observer \(U^2=-c^2\), photon propagation direction \(e=-n\), spatial momentum magnitude \(q\), energy \(E^2=m^2c^4+c^2q^2\), and dimensionless speed \(v=cq/E\). Paper I v15, `eq:massive-velocity-hierarchy`, defines
\[
J^{(i)}_{\langle A_\ell\rangle}
=\int E v^{\ell+2i}e_{\langle A_\ell\rangle}f\,d\nu_U,
\qquad d\nu_U=\frac{g_s}{(2\pi\hbar)^3}q^2dq\,d\Omega,
\quad i=0,1,\ldots.
\tag{2}
\]
This reproduces Lewis–Challinor (2002), eq. (10), after restoring units, state counting and the positive spatial metric. **Their superscript is \(i\); their \(n=\ell+2i\) is the total velocity degree.** A notation \(J^{(n)}\) must therefore declare whether it means the radial index \(i\), this total degree, or another energy-weight convention. Angular rank \(\ell\), radial index \(i\), and energy-power order \(p\) are not interchangeable.

Lewis–Challinor use \((+---)\), \(c=1\), and a factor \((-1)^\ell\Delta_\ell\) in their lower-index convention. V15's positive spatial metric uses \(+\Delta_\ell\). This metric conversion is separate from the physical direction change \(e=-n\). MGE (1999) instead write brightness **expansion coefficients** \(\Pi_{A_\ell}=\int E^3F_{A_\ell}\,dE\), eq. (50), and footnote 11 identifies an older \(J^{(\ell)}_{A_\ell}=\Delta_\ell\Pi_{A_\ell}\). That superscript labels angular rank in that cited notation, not Lewis–Challinor's radial index. Keep the defining integral beside any imported \(J\).

## 2. Exact massless harmonic ↔ STF map

Let \(I(n)\) be physical bolometric energy density per solid angle, in J m\(^{-3}\) sr\(^{-1}\). A spectral **radiance** \(\mathscr I_\nu\) gives \(I=c^{-1}\int\mathscr I_\nu d\nu\). For photons with \(g_s=2\),
\[
I(n)=\frac{2}{(2\pi\hbar)^3c^3}\int_0^\infty E^3 f(E,-n)\,dE.
\tag{3}
\]
Thus energy density and radiance differ by \(c\); bolometric radiance must not be inserted directly as energy density.

For massless particles \(v=1\), so all radial indices in (2) coincide at fixed \(\ell\):
\[
J^{(i)}_{A_\ell}=J_{A_\ell}
=(-1)^\ell\int I(n)n_{\langle A_\ell\rangle}\,d\Omega.
\tag{4}
\]
Define STF harmonic tensors by \(Y_{\ell m}(n)=\mathcal Y^{\ell m}_{A_\ell}n^{A_\ell}\), and let
\[
\Delta_\ell=\frac{4\pi\ell!}{(2\ell+1)!!},\qquad
\mathcal Y^{\ell m*}:\mathcal Y^{\ell m'}=\frac{\delta_{mm'}}{\Delta_\ell}.
\]
For bolometric coefficients \(b_{\ell m}=C^I_{\ell m}\), the exact adapters are
\[
\boxed{J_{A_\ell}=(-1)^\ell\Delta_\ell
\sum_m b_{\ell m}\mathcal Y^{\ell m}_{A_\ell},\qquad
b_{\ell m}=(-1)^\ell\mathcal Y^{\ell m*}:J_{A_\ell}.}
\tag{5}
\]
Consequently \(J:J=\Delta_\ell\sum_m|b_{\ell m}|^2\). In a real orthonormal STF basis \(E_{\ell a}\), equivalently use \(Z_{\ell a}=E_{\ell a}:n^\ell/\sqrt{\Delta_\ell}\), giving \(J=(-1)^\ell\sqrt{\Delta_\ell}\sum_a b_{\ell a}E_{\ell a}\). The map is an isometry after this known scale and retains every component.

| Rank | \(\Delta_\ell\) | Radiation quantity, with physical units |
|---|---|---|
| 0 | \(4\pi\) | \(\rho=J=\sqrt{4\pi}\,b_{00}\), energy density |
| 1 | \(4\pi/3\) | Physical energy flux \(Q_a=cJ_a=-c\int I(n)n_a d\Omega\); physical momentum density \(J_a/c\) |
| 2 | \(8\pi/15\) | Anisotropic stress \(\pi_{ab}=J_{ab}\); pressure \(P=\rho/3\) |
| 3 | \(8\pi/35\) | Bolometric octupole \(H_{abc}=J_{abc}\), energy-density units |
| 4 | \(32\pi/315\) | Bolometric hexadecapole \(H_{abcd}=J_{abcd}\), energy-density units |

Derivation: expand \(f=\sum F_{A_\ell}e^{A_\ell}\), apply \(\int e_{\langle A_\ell\rangle}e^{\langle B_k\rangle}d\Omega=\Delta_\ell\delta_{\ell k}\mathrm{Id}_{STF}\), then integrate the radial energy. Ellis et al., eqs. (5.81)–(5.83), (5.95)–(5.101), and MGE eqs. (47), (49)–(50), supply precisely this convention. The raw moment is \(\Delta_\ell\) times the brightness expansion tensor; confusing the two changes transport coefficients.

## 3. A temperature map needs its nonlinear bolometric conversion

For Planckian rays—or the v15 energy-calibrated photon temperature defined from the full bolometric energy—
\[
I(n)=C_\gamma T_E(n)^4,\qquad
C_\gamma=\frac{\pi k_B^4}{60\hbar^3c^3}.
\]
Writing \(T_E=T_0(1+\Theta)\), \(I_0=C_\gamma T_0^4\),
\[
b_{\ell m}=I_0\int[1+4\Theta+6\Theta^2+4\Theta^3+\Theta^4]Y^*_{\ell m}\,d\Omega.
\tag{6}
\]
Products are harmonic convolutions with Gaunt coefficients. This is exact in \(\Theta\); it is not a linear conversion of temperature powers. For \(\ell\ge1\), only at first order does \(b_{\ell m}=4I_0C^\Theta_{\ell m}+O(\Theta^2)\). If \(\Theta_2=Q^\Theta_{ab}n^an^b\), this gives
\[
\pi_{ab}=\frac{8\rho_0}{15}Q^\Theta_{ab}+O(\Theta^2),
\qquad\rho_0=4\pi I_0.
\tag{7}
\]
For an outward temperature dipole \(\Theta=d\cdot n\), \(Q_a=-(4/3)c\rho_0d_a+O(d^3)\), while even a pure temperature dipole generates
\(\pi_{ab}=\rho_0(4/5+4|d|^2/35)d_{\langle a}d_{b\rangle}\).
More generally, if \(\Theta=d_an^a+Q^\Theta_{ab}n^an^b+O^\Theta_{abc}n^an^bn^c\), with all three carriers small and STF where applicable, the joint stress is
\[
\frac{\pi_{ab}}\rho=\frac8{15}Q^\Theta_{ab}
+\frac45d_{\langle a}d_{b\rangle}
+\frac{24}{35}d^cO^\Theta_{abc}
+\frac{16}{35}Q^\Theta_{c\langle a}Q^{\Theta c}_{b\rangle}
+\frac8{35}O^\Theta_{\langle a|cd|}O^{\Theta\,cd}_{b\rangle}
+O(\Theta^3).
\tag{8}
\]
This is a constraint on the full joint coefficients, including their relative orientations. Exact isotropic pairing counts independently check the quadratic terms: the rank-six angular moment has denominator105 and6 surviving d–O or8 Q–Q pairings; the rank-eight moment has denominator945 and36 O–O pairings. Multiplication by the coefficient6 in (6), and by2 for the d–O cross term, gives (8). Odd d–Q and Q–O terms vanish. Normalization by the actual \(\rho\) first changes these terms at cubic order because \(\langle\Theta\rangle=0\). A finite temperature cutoff therefore does not equal a brightness cutoff; omitted temperature modes can feed low brightness modes. A reported thermodynamic-K channel map is a calibrated detector product: equating it to the full \(T_E\) additionally requires the spectral/reference model.

**A specific primary-source discrepancy:** MGE arXiv v2 PDF p. 15, eq. (81), visibly prints \(\tau_{ab}\simeq15\pi_{ab}/(2\rho_R)\). Its own eqs. (50) and (80) imply \(15\pi_{ab}/(8\rho_R)\), which agrees with (7), direct angular integration and the attached report. Use the latter normalization. This is a localized factor-four inconsistency in the displayed equation, not a change of convention or a claim about a journal erratum.

## 4. What observations constrain and what bandpasses change

Calibrated full bolometric coefficients constrain \(\rho,Q_a,P,\pi_{ab},H_3,H_4,\ldots\) at the observer's event, with their joint covariance and frame. For photons, different \(i\) in (2) add no independent information. Massive-particle \(J^{(i)}\) require the appropriate speed-weighted radial data; CMB temperature coefficients do not measure a neutrino/matter hierarchy by substitution.

A finite channel measures its own kernel,
\[
d_{r,\ell m}=\int d\nu\,R_r(\nu)
\int d\Omega\,Y^*_{\ell m}(n)\mathscr I_\nu(n),
\tag{9}
\]
with beam/mask/estimator operators included in actual use. These are band-weighted radiation moments. Bolometric (3) requires a calibrated spectral completion or a bounded omitted-band contribution. V15 supplies the ray-energy calibration, response derivatives and separation of unresolved spectral from angular information; it does not infer that completion from a finite coefficient list. Band integration also modifies transport: \(\int_{E_1}^{E_2}E^4\partial_Ef\,dE=[E^4f]_{E_1}^{E_2}-4\int_{E_1}^{E_2}E^3f\,dE\). The endpoint terms remain, so the uncorrected bolometric hierarchy cannot be applied independently to each band.

The existing HTT physical route is therefore: joint calibrated coefficients → brightness/STF moments by (3)–(6) → the declared transport/optical response → a joint feasible set or likelihood. Matter shear, vorticity, acceleration, tilt and curvature additionally require their response, derivatives and nuisance assumptions. This note fixes their radiation input rather than replacing that inference by morphology or entropy alone.

**Sources read:** Paper I v15 `02_one_field_state_space.tex`, `03b_angular_response.tex`, `03c_massive_calculus.tex`, `07_physical_interpretation.tex`; prior internal Loops A/B/C; attached *Relativistic Cosmology*, printed pp. 104–108 (PDF pp. 120–124), especially (5.81)–(5.83), (5.95)–(5.101); MGE, [astro-ph/9808163v2](https://arxiv.org/abs/astro-ph/9808163v2), PDF pp. 10, 14–15, eqs. (47), (49)–(50), (77)–(81), with p. 15 visually inspected; Lewis–Challinor, [astro-ph/0203507](https://arxiv.org/html/astro-ph/0203507), §II eqs. (2), (4), (10)–(12), §III massless reduction. Primary retrieval checked 2026-10-26. No numerical or transport execution was needed for these convention identities.
