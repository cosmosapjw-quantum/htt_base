# Bianchi 대수형의 관측 식별가능성과 HTT 5변수 연결

기준일: 2026-11-09  
연구 노드: R48-T22  
판정: **PASS_SCOPED (합성 oracle only)**

## 1. 질문

목표는 BASS solver를 확장하는 것이 아니다. Bianchi 구조상수의 대수적 차이가 normal-frame matter tilt와 국소 관측 응답으로 전달되는지, 그리고 그 정보가 하나의 공동 posterior에서 유도되는 HTT \(T=(x,Q,\Pi,F,G_F)\)에 남는지 판정한다. 모든 결과는 instantaneous constraint 및 명시적 synthetic response law에 제한된다.

## 2. Momentum constraint와 exact tilt inversion

Loop D의 정규화에서
\[
M_i\equiv\kappa q_i
=3a_jS_{ji}+\epsilon_{ijk}n_{j\ell}S_{k\ell},\qquad
q_i=(\rho+p)\Gamma^2\beta_i,\quad \Gamma=(1-\beta^2)^{-1/2}.
\]
여기서 \(S_{ij}\)는 normal-frame STF shear다. \(w=\kappa(\rho+p)>0\), \(r=\|M\|/w\)라 두면 \(r=\beta/(1-\beta^2)\)이므로
\[
\beta=\frac{2r}{1+\sqrt{1+4r^2}},\qquad
\boldsymbol\beta=\beta\,\frac{M}{\|M\|}.
\]
이는 exact algebraic inversion이며 small-tilt approximation이 아니다. \(M=0\)이면 \(\beta=0\)이다. Enthalpy가 알려져 있지 않으면 flux amplitude와 tilt amplitude는 별도로 식별되지 않는다.

## 3. Algebraic rank strata

### Class A

\(a=0,\ n=\operatorname{diag}(n_1,n_2,n_3)\)이면
\[
M_A=\big((n_2-n_3)S_{23},\ (n_3-n_1)S_{13},\
(n_1-n_2)S_{12}\big).
\]
고정된 \(S\)에 대해
\[
J_A=\frac{\partial M_A}{\partial(n_1,n_2,n_3)}
=\begin{pmatrix}0&S_{23}&-S_{23}\\-S_{13}&0&S_{13}\\S_{12}&-S_{12}&0\end{pmatrix},
\quad J_A(1,1,1)^T=0.
\]
따라서 rank는 최대 2이며 generic off-diagonal shear에서 2다. 공통 trace shift \(n\mapsto n+cI\)는 momentum-flux map의 정확한 kernel이다.

예를 들어
\[
n_{\rm II}=(1,0,0),\qquad n_{\rm IX}=(2,1,1)
=n_{\rm II}+(1,1,1)
\]
이면 임의의 같은 STF \(S\)에서 \(M_{\rm II}=M_{\rm IX}\)다. 동일 enthalpy 아래 normal-frame tilt도 같다. 하지만 이 둘의 intrinsic 3-Ricci eigenvalue는 각각 \((-1/2,-1/2,1/2)\), \((0,0,2)\)로 다르다. 이것은 두 기하가 같은 것이 아니라 **그 instantaneous momentum observable 하나가 algebraic 차이를 소거한다**는 결과다.

### Class B

canonical axes \(a=(a,0,0),\ n=\operatorname{diag}(0,n_2,n_3)\)이면
\[
M_B=\big(3aS_{11}+(n_2-n_3)S_{23},\
3aS_{12}+n_3S_{13},\ 3aS_{13}-n_2S_{12}\big).
\]
\[
J_B=\begin{pmatrix}3S_{11}&S_{23}&-S_{23}\\3S_{12}&0&S_{13}\\3S_{13}&-S_{12}&0\end{pmatrix},
\quad
\det J_B=3\big[S_{11}S_{12}S_{13}+S_{23}(S_{12}^2+S_{13}^2)\big].
\]
따라서 determinant가 0이 아닌 generic shear에서는 고정된 \(S\), enthalpy, triad 아래 \((a,n_2,n_3)\)를 국소 복원할 수 있다. determinant-zero strata, unknown enthalpy, frame/triad nuisance는 남는다. 이를 Class B 전역적 식별 정리로 승격하지 않는다.

## 4. 국소 관측 응답 및 곡률 차수

normal congruence의 leading directional Hubble coefficient는
\[
H_N(\mathbf n)=\Theta_N/3+\sigma^{(N)}_{ij}n^in^j-A^{(N)}_in^i.
\]
synchronous geodesic normal congruence에서는 \(A_N=0\). 이 응답은 expansion monopole와 STF shear quadrupole를 읽지만 Bianchi structure constants나 matter tilt를 독립적으로 측정하지 않는다. Tilt는 별도의 matter-frame count/astrometric response와 frame arrow가 필요하다.

regular beam vertex에서 Sachs focusing은
\[
D_A''=-\left[\frac12R_{ab}k^ak^b+|\hat\sigma|^2\right]D_A,\qquad
D_A(s)=s-\frac{(R_{ab}k^ak^b)_o}{12}s^3+O(s^4).
\]
따라서 **direct optical-focusing Ricci term**은 affine distance에서 cubic, 역전한 local distance-redshift expansion에서 \(z^3\) 차수에 기여한다. Einstein/evolution equations를 대입하면 다른 계수에도 curvature가 들어갈 수 있으므로 모든 curvature 정보가 오직 \(z^3\)에서만 시작한다고 말하지 않는다.

중요하게도 \(R_{ab}k^ak^b\)는 spacetime Ricci contraction이고 한 slice의 intrinsic \({}^3R_{ij}\)가 아니다. Extrinsic curvature, Weyl curvature, time transport와 source/observer boundary conditions 없이 서로 대체할 수 없다. 이 mock의 3-Ricci eigenvalue carrier는 IDEALIZED_ORACLE_ONLY다.

## 5. Geometry presentation controls

- Flat: Bianchi I \((a=0,n=0)\)와 special VII\(_0\) \((a=0,n=(0,p,p))\)는 isotropic FLRW limit에서 \({}^3R_{ij}=0\)인 같은 local Euclidean spatial metric의 서로 다른 simply-transitive group presentation이다.
- Open: Bianchi V \((a=(a,0,0),n=0)\)와 special VII\(_h\) \((a=(a,0,0),n=(0,p,p))\), \(h=a^2/p^2>0\), 는 isotropic FLRW limit에서 \({}^3R_{ij}=-2a^2\delta_{ij}\), \(K=-a^2\)로 같다.

이 degeneracy는 corresponding isotropic embedding에 한정된다. 임의의 anisotropic embedding까지 두 시공간을 동일시하지 않는다. Local metric observables는 동일한 local metric 및 observer structure에 대해서는 group-presentation label을 복원할 수 없다.

## 6. Finite synthetic mock

- Latent shear scale \(\lambda\), fixed-II/IX algebra pair, exact momentum constraint and exact tilt inversion.
- R/O frame은 homogeneous normal, M은 tilted fluid로 선언. Collinear inverse-boost closure에서 \(\beta_{RM}=\beta_{NM}\), \(\beta_{MO}=-\beta_{NM}\), \(\beta_{RO}=0\).
- Kinematic vector: 3 count-dipole-like + 3 Gaia-E1-like + 3 abstract STF5 shear windows = 21D. Full covariance는 cross-carrier/window correlation을 포함한다.
- Count scale 1.25와 E1-like scale 0.80은 synthetic calibration이지 NVSS/Quaia/Gaia calibration이 아니다.
- Curvature channel: sorted eigenvalues of \({}^3R_{ij}\)에 대한 3D Gaussian oracle, component standard deviation \(\sqrt{3/8}\). 실제 catalog response가 아니다.

이진 equal-prior, equal-covariance Gaussian label model에서
\[
\ell(d)=\Delta\mu^TC^{-1}\left[d-\frac{\mu_0+\mu_1}{2}\right]
\]
는 label에 대한 정확한 log-likelihood ratio다. 따라서 이 oracle 안에서는 \(x\)에 \(\ell\)을 보존하면 target posterior KL loss가 0이고, geometry carrier를 제거하면 전체 label information이 손실된다. Kinematic-only likelihood는 II와 IX에 대해 동일하므로 label information이 정확히 0이다.

Nuisance projection은 \(J_{\rm eff}=(I-P_\eta)C^{-1/2}J\). Geometry contrast와 정확히 평행한 unrestricted calibration nuisance를 두면 label-separation rank는 1에서 0으로 떨어진다.

## 7. HTT five views

각 posterior draw는 단일 sample_id를 공유한다.
- \(x\): \(\sigma,\beta_{NM},\beta_{RM},\beta_{MO},\beta_{RO}\), mixed \(\sigma:\beta\beta/H_{\rm ref}\), count/E1/shear carriers, idealized curvature vector 및 binary LLR.
- \(Q\): instantaneous constraint/frame/mock calibration 상태를 type하고 real catalogue anchor와 dynamical transport는 unavailable로 남긴다.
- \(\Pi\): posterior \(|\beta_{MO}|\) exceedance와 같은 pipeline의 zero-tilt injection matched-null exceedance.
- \(F\): posterior mean-centered deviation hull의 directional support를 mock anchor radius와 비교한다.
- \(G_F\): 세 abstract windows의 full posterior/data cross-window covariance; transport는 identity mock only.

5개 변수는 하나의 posterior의 coordinated views이며 독립 likelihood factors가 아니다. Null, resampling, split과 covariance는 sample-ID identity를 보존한다.

## 8. Numerical result and claim ceiling

Seed 20261109, prior-predictive/label replications 30,000, shared posterior samples 12,000, 512 zero-tilt null data realizations × 32 posterior draws:
| Quantity | Result |
|---|---:|
| \(M=\kappa q\) | \((0,-0.08,0.10)\) |
| \(|\beta_{NM}|\) | 0.12602845 |
| Class-A momentum Jacobian rank | 2; trace-kernel residual 0 |
| Class-B fixture Jacobian rank | 3; determinant 0.007752 |
| Kinematic-only label information | 0 nat |
| Curvature-oracle Mahalanobis separation | 7.333333 |
| Curvature-oracle label information / expected target KL | 0.47891896 nat |
| MAP accuracy | 0.9122 |
| Brier | 0.0639951 |
| Full \(x\)+LLR target KL loss | 0 nat |
| Geometry-carrier ablation loss | 0.47891896 nat |
| Randomized-rank SBC | \(\chi^2_9=8.7573,\ p=0.4600\) |
| Parallel nuisance | label rank \(1\to0\) |

These are prior-, noise-, operator- and enthalpy-dependent synthetic design results, not detection forecast or evidence from the sky. No real-data Bianchi family identification, all-type tilted Einstein-fluid solution, physical curvature sensor, Bianchi transfer, global HTT sufficiency or broad novelty claim is established.

## 9. Prior art and novelty boundary

Ellis–MacCallum (1969) and King–Ellis (1973) are standard Bianchi/tilt foundations. Kristian–Sachs (1966) and Heinesen (2021) cover generic local light-cone and luminosity-distance expansion. Kalbouneh–Marinoni–Maartens (2024) and Maartens et al. (2024) address local covariant cosmography and observer dependence. Pereira–Pitrou (2019) analyze Bianchi/perturbed-FLRW correspondence. The 2026 Clifford-algebraic Bianchi author preprint is direct overlap risk. We claim neither a new Bianchi formalism nor a new general invariant theory.

References:
- Ellis & MacCallum 1969: https://doi.org/10.1007/BF01645908
- King & Ellis 1973: https://doi.org/10.1007/BF01646266
- Kristian & Sachs 1966: https://doi.org/10.1086/148522
- Heinesen 2021: https://doi.org/10.1088/1475-7516/2021/05/008
- Kalbouneh et al. 2024: https://doi.org/10.1088/1475-7516/2024/09/069
- Maartens et al. 2024: https://doi.org/10.1088/1475-7516/2024/09/070
- Pereira & Pitrou 2019: https://doi.org/10.1103/PhysRevD.100.123534
