# Two retained applications: polarization morphology and optical kinematics

The same tensorized inference programme can consume different physical carriers without identifying them. This addition joins the user's Planck example and Hubble-diagram inverse to the radiation-stress construction. The relevant current carrier is
\[
X=(Q_E,O_E;\ \rho_\gamma,f_\gamma,P_\gamma;\ d,S,O_\mu;\ \eta),
\]
where semicolons distinguish polarization morphology, intensity stress, optical kinematics and their joint nuisances. Each channel has its own observation map, invariant group and error body. Cross-channel physical conclusions require an explicit response connecting them.

## 1. The Planck example is a measured morphology result

The retained report's pinned-primary PR3 E-mode row, processing cutoff 32, secondary window 0 degrees, FULL product, gives

| Quantity | Retained value |
|---|---:|
| Quadrupole shape r | 0.0582918 |
| Signed chirality C | -0.0967707 |
| Fixed-shape envelope E(r) | 0.808141 |
| Envelope utilization U | 0.1197448 |

Here \(r=j^2/t^3\), \(t=\mathrm{tr}Q_E^2\), \(j=\mathrm{tr}Q_E^3\), and
\[
E(r)^2=(1-6r)(1+3r/40),\qquad U=|\mathcal C|/E(r).
\tag{P1}
\]
The fields analysed are degrees two and three of a processed polarization E pseudo-harmonic product; 32 is its processing cutoff. The values were verified against the pinned report, not by re-extracting the original maps during this loop. The cached-pilot row is a different source and is not substituted.

**A fresh ideal Gaussian benchmark.** Conditional on any simple-spectrum quadrupole, an independent isotropic Gaussian STF3 octupole has a uniform normalized direction on the seven-dimensional Frobenius sphere. Diagonalizing its three-dimensional contraction image and dividing by the sharp envelope gives
\[
U\ \overset{d}{=}\ 3\sqrt3\,|z_1z_2z_3|,\qquad z\sim\operatorname{Unif}(S^6).
\tag{P2}
\]
The result follows because the three contraction singular values and the quadrupole Vandermonde cancel against that envelope. The remaining four coordinates lie in the contraction kernel. Its moments provide checks:
\[
\mathbb E U=\frac{15\sqrt3}{64\pi},\qquad \mathbb E U^2=\frac3{77}.
\tag{P3}
\]
With seed 20261026 and 1,048,576 draws, 662,397 fall below the displayed U. The estimated CDF is **0.631711**, with binomial Monte Carlo 95% interval **[0.630787,0.632634]**; the upper tail is **0.368289**. This independently supports the proposed approximately 63.1% benchmark. The original historical percentile's receipt was not recovered. Equation (P2) is an ideal Gaussian reference, not a Planck mask/noise/foreground-calibrated probability; random spatial rotation of a fixed octupole is also a different null.

**Sign stability is a separate property.** The retained report uses \(\bar Q=Q_E/q_0\), \(\bar O=O_E/o_0\), with \(q_0=o_0=10^{-5}\,\mathrm K_{CMB}\), and joint full-tensor Frobenius norm \(m^2=\|\bar Q\|^2+\|\bar O\|^2\). For perturbations of norm at most \(\rho_{stab}m\), its sufficient certificate is
\[
\chi^2>36\rho_{stab}^2(1+\rho_{stab})^{16}(m^2)^9.
\tag{P4}
\]
All 60 saved processing carriers pass at \(\rho_{stab}=10^{-6}\); 39 pass at \(10^{-5}\). This is the saved report's certificate, not a newly estimated physical error radius. Each carrier retains its own sign locally; the 60 signs are not all equal, and the carriers are correlated views of one sky. A stable sign may have an ordinary null percentile, as this example does. The accessible compact report numbers (P4) as equation (13); the current R32-01 equation (35) is a different optical sign bound.

On the four axes: the E tensors are rotation-covariant observables; C is a proper-rotation invariant pseudoscalar, U is reflection-even, and (P4) is deterministic local robustness. None alone establishes statistical parity violation. E(n) is not positive bolometric intensity, so substituting it into I=C_gamma T_E^4 would be physically invalid. Its interpretation remains polarization morphology until an appropriate polarized response is supplied.

## 2. The Hubble inverse becomes one joint physical test

The pinned local optical model defines
\[
d=-\frac A{cH},\quad S=\frac\sigma H,\qquad
f_\mu(n)=-\kappa\log[1+d\cdot n+S:nn],\quad\kappa=5/\ln10.
\tag{H1}
\]
Thus d is normalized acceleration of the declared common observer/emitter congruence; it is not the CMB dipole or an arbitrary velocity dipole. S is the directional Hubble-slope quadrupole; the magnitude quadrupole instead obeys Q_mu=-kappa S plus a finite nonlinear remainder. For \(\sup|d\cdot n+S:nn|\le\epsilon<1\),
\[
O_\mu=\kappa L_Sd+R_3,\quad
\|R_3\|\le E_3(\epsilon)
=\sqrt{35/2}\frac{\kappa\epsilon^3}{3(1-\epsilon)},
\quad M_S=L_S^*L_S=\frac{S:S}{3}\mathrm{Id}+\frac25S^2.
\tag{H2}
\]
The proposed inverse and perpendicular residual are retained. The constructive repair is to preserve their **shared** error budget. For fixed measured \(\widehat S\ne0\), a joint event with \(\|S-\widehat S\|\le e_S\), \(|d|\le D_{max}\) permits
\[
B=E_3+e_O+B_z+B_{sel}
+|\kappa|\sqrt{3/5}\,e_SD_{max}.
\tag{H3}
\]
The last term follows from \(\|L_{S-\widehat S}\|\le\sqrt{3/5}e_S\). Error ownership must prevent double counting. The finite-distance order also needs correction: \(d_L=cz/\mathcal H+O(z^2)\) generally gives an **O(z) magnitude correction**. An O(z squared) magnitude remainder requires the first correction to be modeled or removed. Selection and frame terms are separately bounded by their actual response.

For an exact direct estimate d_obs, the key identity is
\[
\begin{aligned}
\|\widehat O-\kappa L_{\widehat S}d_{obs}\|^2
={}&\|\widehat O_\perp\|^2\\
&+\kappa^2(\widehat d-d_{obs})^TM_{\widehat S}
(\widehat d-d_{obs}).
\end{aligned}\tag{H4}
\]
The joint right-hand side must be at most B squared. Separate bounds on the two terms are only necessary. The finite control in the source package has separate normalized scores **0.8 and 0.8**, but joint score **1.13137085**; both separate tests pass while the common model-error ball is missed.

For a direct-vector error ball \(|d-d_{obs}|\le e_d\), use
\[
Q_{joint,min}^2=\frac{\|\widehat O_\perp\|^2+
\kappa^2\min_{|d-d_{obs}|\le e_d}
(\widehat d-d)^TM_{\widehat S}(\widehat d-d)}{B^2}.
\tag{H5}
\]
This is a three-dimensional convex minimization. A value above one rejects the specified joint response/error model. For full correlated data, use the original joint region rather than replacing it by independent balls. Near S=0 use direct response-set testing; the inverse has unbounded absolute gain there. At B=0 test exact membership rather than assigning a ratio.

Agreement means compatibility with the local acceleration–shear response; it does not prove that mechanism alone. Separating finite-redshift, selection and source-frame alternatives requires their distinct registered responses across depth/processing windows, with cross-window covariance. This is the appropriate role for the existing G_F machinery.

## 3. Revised contribution target

The coherent paper target is a **response-qualified tensor statistical analysis**: retain the measured Planck morphology and its deterministic stability, infer radiation stress from intensity moments through v15, and test the optical acceleration–shear image with one shared uncertainty budget. The same mathematical tensor operations serve three different carriers. Their invariants and physical meanings remain typed throughout.

The new ideal U benchmark and shared-budget test are completed constructions. A claim of improved cosmological constraints needs a common-data comparison with existing estimators and calibrated processing/noise models. The next short observational step is to supply those joint input products, not to build a native Boltzmann solver or to identify Bianchi geometry from an E-mode chirality score.
