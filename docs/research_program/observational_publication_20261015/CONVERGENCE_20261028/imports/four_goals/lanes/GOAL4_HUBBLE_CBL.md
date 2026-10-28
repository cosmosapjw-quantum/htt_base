# Goal 4 — directional expansion, optical transmission and a qualified CBL test

28 October 2026. Constructive theory work R2/R3/R4/R5/R7/R9 under PhysMath 1.3.0, using `WORK_PACKET.md`. This lane reads the supplied MF02 §§3.4 (pp.67–68), 4.6 (pp.81–82), 11.9 (p.130), the optical manuscript §IV–VI, and the current R36 optical response. No original acceptance or repository/controller state is changed. All new numerical results below are finite analytic/matrix controls, not catalogue fits.

## 1. The physical question and what the existing work already supplies

The original Hubble goal contains two different estimands. The first is the directional local expansion of a specified matter congruence,

$$\mathcal H_u(n)=H-\frac{A\cdot n}{c}+\sigma:nn.$$

The optical manuscript Eq.(21) and its nonlinear magnitude response already give its signed dipole/quadrupole interpretation. R36-04 supplies the selected-source Jacobian, full seven-component octupole budget and joint covariance pushforward. These are reusable physics and statistics. The finite-redshift source/selection remainder remains an explicit input for actual data.

The second estimand is a finite-redshift distance–expansion consistency relation. CBL uses a geometric distance $d=D_L/(1+z)$ and an independently qualified expansion response $H(z)$. In a general anisotropic spacetime, replacing $H(z)$ by an arbitrary direction-dependent fit does not establish the FLRW relation. We retain the original CBL null as a test of its metric/propagation premises, while using angular cosmographic jets for the directional Hubble question.

### A finite local expansion interval that includes opacity

Write the supplied local optical model as

$$D_{L,r}(z,n)=\frac{cz}{\mathcal H_u(n)}\exp\{r_g(z,n)+\tau_r(z,n)/2\},$$

where $r_g=O(z)$ is the logarithmic geometric/finite-distance remainder and $\tau_r$ is the effective optical depth of a calibrated source state and detector. This is an exact definition of the remainder within the chosen branch. Set $H_F=cz/D_{L,r}$, an observed flux-distance slope, not an assumed global Hubble rate. If $|r_g|\le b_g$ and $\tau_-\le\tau_r\le\tau_+$, then

$$H_F e^{-b_g+\tau_-/2}\le\mathcal H_u(n)\le H_F e^{b_g+\tau_+/2}.\tag{G4.1}$$

This gives a physical interval without a dynamical solver. Under smooth transparent-at-vertex propagation, $\tau_r(0,n)=0$, the zeroth-order local slope is unchanged; $\tau_r'(0,n)$ enters the next distance coefficient. An unknown angular calibration or foreground-screen offset $\tau_0(n)$ instead changes the limiting apparent slope to $\mathcal H_u(n)e^{-\tau_0(n)/2}$. Its angular modes are degenerate with the same expansion modes unless constrained by calibration or a second response. A common finite confidence event for the measured $H_F$ and the retained optical/nuisance coefficients can be pushed through (G4.1), preserving cross-direction covariance.

## 2. Calibrated optical tomography: what it determines

Use the source manuscript convention, with known $4\pi$ factors absorbed in observations:

$$y_{ij}=\operatorname{tr}[R_i\mathcal A(L_j)],\qquad
\mathcal A=s\mathcal P,\qquad s=D_L^{-2}.$$

For calibrated positive $L_j,R_i$ spanning the respective real Hermitian spaces, the observations determine a Hermiticity-preserving linear map. In orthonormal Hermitian coordinates, $y=Ma$ and $\|\delta a\|_2\le\|M^+\|_2\|\delta y\|_2$. The CP condition is an additional feasible-set restriction. This is ordinary process-tomography linear algebra, not a new universal theorem. The actual astronomy contract requires known source luminosity/polarization and detector response; uncalibrated source variation belongs in the nuisance design.

Let $Q_{\rm in}=\mathcal A^*(I)$. MF02 Theorem 3.4.2 is correct:

- If $\mathcal P$ is trace-preserving, $Q_{\rm in}=sI$, fixing $s$ and $\mathcal P$ uniquely.
- If it is only trace-nonincreasing, every $s\ge\lambda_{\max}(Q_{\rm in})$ is allowed, so $0<D_L\le\lambda_{\max}(Q_{\rm in})^{-1/2}$.

The second statement follows from $\mathcal P^*(I)=Q_{\rm in}/s\preceq I$, and positive rescaling preserves complete positivity. It is a degeneracy in this specified optical experiment, not a claim about all possible cosmological measurements.

**Constructive additional bound.** Suppose $Q_{\rm in}>0$ and external transmission calibration supplies $t_-I\preceq T=\mathcal P^*(I)\preceq t_+I$, with $0<t_-\le t_+$. Then the exact scalar factor interval is

$$\frac{\lambda_{\max}(Q_{\rm in})}{t_+}\le s\le
\frac{\lambda_{\min}(Q_{\rm in})}{t_-},$$

and hence

$$\sqrt{\frac{t_-}{\lambda_{\min}(Q_{\rm in})}}\le D_L\le
\sqrt{\frac{t_+}{\lambda_{\max}(Q_{\rm in})}}.\tag{G4.2}$$

Every scalar in the nonempty interval produces an admissible rescaled CP map, so these endpoints are attained. An empty interval rejects that transmission calibration jointly with the recovered map. For the supplied filter $K=\mathrm{diag}(1/3,1/5)$, $\mathcal A(X)=KXK^\dagger$, the TNI upper distance is 3 in the chosen length unit. Adding $0.1I\preceq T\preceq I$ gives $1.58114\le D_L\le3$.

The response distance $\mathcal D=(1+z)^{-1}Q_{\rm in}^{-1/2}$ is stable only away from undetected channels. If $Q,\widetilde Q\succeq mI>0$, resolvent representations of inverse square root and logarithm give

$$\|\mathcal D(Q)-\mathcal D(\widetilde Q)\|_F\le
\frac{\|Q-\widetilde Q\|_F}{2(1+z)m^{3/2}},\qquad
\|\Xi(Q)-\Xi(\widetilde Q)\|_F\le \frac{\|Q-\widetilde Q\|_F}{m}.\tag{G4.3}$$

Here $\Xi(X)=\log(X/q_*)-I\operatorname{tr}\log(X/q_*)/N$; the traceless projection contracts Frobenius norm. The bounds follow by integrating $\|(Q+tI)^{-1}\|\le(m+t)^{-1}$ and using the resolvent identity. They connect detector uncertainty to physically interpreted matrix outputs. Derivatives along redshift need corresponding derivative-control inputs; (G4.3) alone does not bound them.

## 3. Three repairs to the proposed channel protocol

**Traceless log determines relative transmission, not grey transmission.** Write $T=e^g e^\Xi$, where $g=\operatorname{tr}\log T/N$. Then $W=T^{-1/2}=e^{-g/2}e^{-\Xi/2}$. Measuring $\Xi$ fixes the relative eigen-transmissions and their basis orientation in a calibrated frame, but leaves $g$ undetermined. Therefore it cannot reconstruct the absolute $W$ or its grey redshift derivatives. This is already acknowledged in MF02 §4.6.1; the user's proposed reconstruction step should retain $g,g',g''$ as calibrated or bounded nuisance.

**Rank-one Choi means one Kraus operator.** A rank-one nonzero Choi matrix has $\mathcal A(X)=KXK^\dagger$. It can be a nonunitary filter: the diagonal $K$ above is an exact counterexample. In equal input/output dimensions, after a justified trace-preserving normalization, $K^\dagger K=I$ does imply a unitary channel. The rank-1 unitary versus rank-4 completely depolarizing comparison is correct for those named TP examples. In noisy observations, exact Choi rank should be replaced by a confidence region or an explicit small-eigenvalue threshold, propagated with the tomography covariance.

**Input and output normalization are different.** MF02 §4.6 uses $Q_{\rm in}=\mathcal A^*(I)$ for input-state-dependent transmission. MF02 §11.9 instead uses $Q_{\rm out}=\mathcal A(I)$ for the unital normalization $Q_{\rm out}^{-1/2}\mathcal A(\cdot)Q_{\rm out}^{-1/2}$. They are not interchangeable. A TP amplitude-damping channel with damping 0.3 gives $Q_{\rm in}=I$ but $Q_{\rm out}=\mathrm{diag}(1.3,0.7)$. Neither normalization asserts that physical loss has been measured and removed.

## 4. The CBL identities survive the noncommutative check

For length-valued $d(z)$ and $H$ in inverse time,

$$C[d]=1+\frac{H^2}{c^2}(dd''-d'^2)+\frac{HH'}{c^2}dd'.$$

The geometric FLRW construction makes $C[d]=0$. This is a necessary consistency condition, not a complete classification of spacetime: the original CBL paper exhibits non-FLRW possibilities satisfying it.

For a fixed calibrated source state, $d_r=d\exp(\tau_r/2)$ gives the exact identity

$$C[d_r]=1+e^{\tau_r}(C[d]-1)+
\frac{d_r^2}{2c^2}(H^2\tau_r''+HH'\tau_r').\tag{G4.4}$$

The squared first-derivative terms cancel. The source-frame variation of the state must be included in the total derivatives of $\tau_r$ if the state is not fixed.

For $\mathcal D=dW$, $W>0$, $D_zX=X'+[\mathcal A_z,X]$ with anti-Hermitian connection, and $X\circ Y=(XY+YX)/2$, define

$$\mathcal C=I+\frac{H^2}{c^2}[\mathcal D\circ D_z^2\mathcal D-(D_z\mathcal D)^2]
+\frac{HH'}{c^2}\mathcal D\circ D_z\mathcal D.$$

Leibniz expansion, without commuting any matrices, yields

$$\mathcal C=I+(C[d]-1)W^2+
\frac{d^2}{c^2}\left[H^2\{W\circ D_z^2W-(D_zW)^2\}+HH'W\circ D_zW\right].\tag{G4.5}$$

Under a redshift-dependent internal basis $U(z)$, the connection transforms as $\mathcal A_z\mapsto U\mathcal A_zU^\dagger-U'U^\dagger$, and $\mathcal C\mapsto U\mathcal C U^\dagger$. Thus its spectrum is gauge invariant. The Jordan ordering is a useful Hermitian diagnostic with the correct scalar limit; it is not uniquely mandated by general relativity. Equation (G4.5) algebraically separates two terms conditional on $W$; it does not observationally identify both terms when grey transmission is free.

## 5. A finite opacity-aware identified region

Solving (G4.4) for the geometric residual gives

$$C[d]=1+e^{-\tau_r}\left[C[d_r]-1-
\frac{d_r^2}{2c^2}(H^2\tau_r''+HH'\tau_r')\right].\tag{G4.6}$$

At a fixed redshift, suppose $\tau_-\le\tau_r\le\tau_+$ and $|\tau_r'|\le b_1$, $|\tau_r''|\le b_2$. Define

$$a=C[d_r]-1,\qquad B=\frac{d_r^2}{2c^2}(H^2b_2+|HH'|b_1),\qquad
t_-=e^{-\tau_+},\quad t_+=e^{-\tau_-}.$$

Then a certified outer interval for $C[d]$ is 1 plus the minimum/maximum of the four products $t_\pm(a\pm B)$. This follows from interval multiplication; it does not assume that all pointwise bounds are simultaneously attained by one smooth opacity history. A function-level set, for example constrained spline coefficients for $\tau_r$, can be much tighter.

For statistics, form one joint confidence event for fitted log-distance coefficients, their derivatives, expansion-response coefficients, photometric calibration and polarimetric quantities. Map that event and the physically allowed opacity-function set through (G4.6). Every resulting curve is a compatible geometric residual. If zero is excluded at a location using the joint event, its coverage has the same declared simultaneous bound. Independently fitted pointwise 95% derivative intervals do not automatically provide that joint guarantee. A Bayesian version instead supplies explicit priors over opacity/history and calibrations, retaining their common likelihood.

### A lower-derivative route worth prioritizing

The original CBL paper already recommends testing constancy of a curvature estimator to avoid a second distance derivative. With explicit units, use

$$\kappa(z)=\frac{H^2d'^2/c^2-1}{d^2},\qquad
\kappa'=\frac{2d'}{d^3}\,C[d].$$

Under opacity this becomes

$$\kappa(z)=\frac{(H^2/c^2)(d_r'-\tau_r'd_r/2)^2-e^{\tau_r}}{d_r^2}.\tag{G4.7}$$

The curvature estimator has inverse-length-squared units, and the positive sign in its derivative relation follows direct differentiation. Thus (G4.7), checked directly from $d=d_re^{-\tau_r/2}$, needs only first opacity and distance derivatives. Testing a common constant across several redshift windows is equivalent to the differential condition on an interval where $d'\ne0$, given regularity. This is a better first observational design than estimating a noisy $\tau''$ and $d_r''$. It still needs opacity bounds and calibrated $H$, and it becomes ill-conditioned near the vertex because of $d^{-2}$.

## 6. Executed controls and what they establish

The actual Wolfram evaluator returned exact residual 0 for (G4.4), the zero 2×2 matrix for (G4.5), and a nonzero rational commutator for the test $W$. Python independently used analytic matrix jets, without symbolic packages or differential-equation integration. On 201 redshift values:

| Check | Result |
|:--|--:|
| Noncommutative Jordan identity maximum Frobenius residual | $2.67\times10^{-14}$ |
| Redshift-dependent gauge covariance residual | $2.37\times10^{-14}$ |
| Noncommutator maximum norm | 0.133563 |
| Positive $W$ minimum eigenvalue | 1.81215 |
| Positive calibrated 2×2 source/effect tomography rank | 16 |
| Tomography reconstruction error | $1.70\times10^{-17}$ |
| Grey scaling change in $\Xi$ | 0 |

For the physically specified flat de Sitter control $H=H_0$, $d=cz/H_0$, take $\tau=0.2z$. At $z=1.5$, uncorrected $C[d_r]=-0.349859$ although geometric $C[d]=0$. Correcting with the supplied opacity recovers zero within $2.22\times10^{-16}$. With the declared outer opacity class $0\le\tau\le0.3$, $|\tau'|\le0.25$, $|\tau''|\le0.02$, the geometric outer interval at that point is $[-0.380231,0.0225]$, retaining the true zero. Constant calibration $d_r=1.1d$ gives residual $-0.21$; that example is a calibration offset on an interval, not a continuous transparent-at-vertex medium.

![Analytic flat geometry, attenuation-induced residual and a compatible geometric interval. These are synthetic controls.](../figures/goal4_cbl_opacity.png)

The optional SymPy dependency was absent. This execution-environment error was repaired by analytic NumPy matrix jets; exact symbolic results were already obtained through Wolfram. No scientific tolerance or model was changed. All code and numeric receipts are retained.

## 7. Concrete research unit and contribution boundary

The most useful near-term unit is **an opacity-qualified angular Hubble and curvature consistency analysis**, using the existing released SN/optical carrier and its joint calibration law. First construct (G4.1) for angular local slopes; then apply (G4.7) to several supplied redshift windows, with independently qualified $H$ and a bounded opacity class. Keep the common zero/constant decision as a physical compatibility test. A calibrated polarimetric branch supplies $\Xi$ and normalized channel shape; an independent distance/flux reference or a transmission model supplies the missing grey direction. Possible standards include a qualified angular-distance observable or standard-siren distance, with its own propagation assumptions and cross-covariance.

For the five existing coordinates: $x$ retains the signed angular/derivative/channel carrier; $F$ gives the compatible directional Hubble or curvature image; $Q$ measures distance from the declared geometric-and-transmission reference; $\Pi$ comes from the single fitted sampling/posterior law; and $G_F$ records the source-frame comparison, redshift derivative and cross-window covariance. No sixth coordinate or independent "matrix likelihood" is needed.

The scalar CBL relation, opacity–distance degeneracy, quantum-process tomography and matrix-function perturbation tools are established. The attached MF02 already derives (G4.4)–(G4.5). This lane's constructive addition is the explicit calibrated distance interval, finite observable-to-matrix error map, opacity-aware compatible residual/curvature region and local Hubble bound, together with falsifying controls for the proposed reconstruction shortcuts. A standalone paper should emphasize this physically qualified inference and demonstrate a gain over matched scalar opacity-aware inference; the mere use of a matrix CBL symbol does not establish priority or empirical advantage.

## Primary sources read

- Clarkson, Bassett and Lu, *A general test of the Copernican Principle*, Phys. Rev. Lett. 101, 011301 (2008), [arXiv:0712.3457](https://arxiv.org/abs/0712.3457), full primary PDF read: Eqs.(2)–(3), different-response H requirement, derivative-error discussion, and non-FLRW $C=0$ caveat.
- More, Bovy and Hogg, *Cosmic transparency: a test with the baryon acoustic feature and type Ia supernovae*, [arXiv:0810.5553](https://arxiv.org/abs/0810.5553), primary abstract/source text: transparency versus geometric distance duality and differential opacity.
- Avgoustidis et al., *Constraints on cosmic opacity and beyond the standard model physics from cosmological distance measurements*, JCAP 2010(10)024, [DOI](https://doi.org/10.1088/1475-7516/2010/10/024), primary text retrieved: photon conservation and flux/angle response separation.
- Wang, Wei, Li, Xia and Zhu, *Model-independent Constraints on Cosmic Curvature and Opacity*, ApJ 847,45 (2017), [arXiv:1709.07258](https://arxiv.org/abs/1709.07258), primary abstract read: joint curvature/opacity inference and strong degeneracy. SciSpace returned a duplicate with a 2022 repository date; the primary submission/publication identifies 2017.
- Poyatos, Cirac and Zoller, *Complete Characterization of a Quantum Process: the Two-Bit Quantum Gate*, PRL 78,390 (1997), [quant-ph/9611013](https://arxiv.org/abs/quant-ph/9611013), primary abstract read for the established process-tomography baseline.

No universal absence-of-prior-art statement is inferred from this finite search.
