# R69: GR, kinetic theory, cosmography, hemispherical morphology에 특화한 수리물리 정리와 실자료 검산

연구일 2026-11-18. 기준 commit d45bce72c655ecccd6165fd750e3f1bcfe69b46f. Metric (-,+,+,+); observer-to-source 방향 n, c, ħ, k_B 유지. **이번 문서는 새로운 일반 GR 정리의 최초성이나 검출을 주장하지 않고**, 선행 물리 방정식에서 실제로 반증할 수 있는 관측 명제를 유도하고 기존 CF4/Gaia/Commander 데이터를 조건부로 시험한다. 재현 코드는 scripts/r69/physical_bridges.py, scripts/r69/gaia_e2_b2.py; 수치 결과는 RESULTS 아래 두 JSON에 기록한다.

## 정리 1. 국소 GR cosmography의 방향별 운동학 분해

**전제:** smooth timelike observer congruence u, u·u=-c², H=Θ/3, n은 sourceward unit spatial vector, regular lightcone vertex, 동일 emitter/observer congruence와 선도 z→0 luminosity-distance expansion. A^a=u^b∇_b u^a, σ는 STF shear, ω는 반대칭 vorticity이다.

\[
\mathfrak H_o(n)=H_o-A_a n^a/c+\sigma_{ab}n^a n^b,\qquad
D_L(z,n)=cz/\mathfrak H_o(n)+O(z^2).
\]
전천 각평균의 정확한 moment를 이용하면
\[
\boxed{H_o=\langle\mathfrak H_o\rangle,\quad
A_a=-3c\langle\mathfrak H_o n_a\rangle,\quad
\sigma_{ab}=(15/2)\langle\mathfrak H_o n_{\langle a}n_{b\rangle}\rangle.}
\]
**증명:** \(\langle n_i n_j\rangle=\delta_{ij}/3\), \(\langle n_i n_j n_k n_l\rangle=(\delta_{ij}\delta_{kl}+\delta_{ik}\delta_{jl}+\delta_{il}\delta_{jk})/15\), odd moments=0, trσ=0. \(\omega_{ij}n^i n^j=0\)이므로 선도 expansion observable에는 ω가 없다. 이는 ω=0이거나 고차 광학에서 ω가 결코 나타나지 않는다는 no-go가 아니다. 원전 Heinesen 2020 arxiv:2010.06534의 방향 multipole을 c와 n convention에 따라 재표현한 것.

## 정리 2. 완전한 반구 평균의 parity 선택과 실측 mask의 shear 누출

완전한 반구 H±를 축 p와 n·p≷0로 정의하면 \(\langle n\rangle_\pm=\pm p/2,\langle nn^\top\rangle_\pm=I/3\), 따라서
\[
\boxed{\langle \mathfrak H_o\rangle_+-\langle \mathfrak H_o\rangle_-=-A\cdot p/c.}
\]
반구 **평균 차이만으로 shear quadrupole을 측정할 수 없다.** 실제 catalogue selection·weight에서 \(M_\pm=\sum_{i\in H_\pm}w_i n_i n_i^\top/\sum_{i\in H_\pm}w_i\)라면
\[
\Delta_{\rm mask}
=d\cdot(\bar n_+-\bar n_-)+\sigma:(M_+-M_-)_{\rm STF},\quad d=-A/c,
\]
\[
\boxed{|\Delta_{\rm shear\to hemisphere}|
\le \|\sigma\|_F\|(M_+-M_-)_{\rm STF}\|_F.}
\]
**증명:** 선택된 방향들의 선형·이차 평균을 전개하고 STF Frobenius Cauchy–Schwarz를 적용한다. CF4 원본 38,053개 group의 비가중 geometry로 계산한 Galactic north 누출 계수는 거리(Mpc)별 0–40:0.137740; 40–80:0.203646; 80–140:0.198420; 140–220:0.231386; 220–400:0.225747; 400+:0.315648. CMB dipole Galactic 방향 (l=264.021°,b=48.253°) 기준 400 Mpc 이상 4,277개 그룹 중 4,187개 대 90개로 나뉘어 STF leakage norm=0.72211. 이는 **실제 cosmic shear 진폭의 측정이 아니라 원본 survey window의 공간기하 진단**이다. R64/P3과 R62/P5에서 올바른 같은 source/weight를 넣어야 한다.

## 정리 3. Quadrupole의 전천 2차·3차 모멘트와 signed STF 형태

\(f(n)=n^i S_{ij}n^j\), \(S\in\mathrm{STF}(3)\)이면,
\[
\boxed{\langle f^2\rangle=(2/15)\operatorname{tr}S^2,\qquad
\langle f^3\rangle=(8/105)\operatorname{tr}S^3.}
\]
이에 따라 R68 signed shape \(\chi=\sqrt6\,\mathrm{tr}S^3/(\mathrm{tr}S^2)^{3/2}\)는
\[
\boxed{\chi=1.565247584249853\,\langle f^3\rangle/\langle f^2\rangle^{3/2}.}
\]
증명은 SO(3) 대각화 후 \(S=\mathrm{diag}(a,b,-a-b)\)를 구면 적분하는 것으로 충분하며, Wolfram exact 결과는 m2=4(a²+ab+b²)/15, m3=-8ab(a+b)/35였다. 이는 기존 harmonic tensor의 다른 수학적 좌표이지 full-sky likelihood 대비 정보량 증가가 아니다. 실제 mask에서는 spherical moments에 mask mode coupling을 적용해야 하므로 위 계수로 masked skewness를 직접 물리 χ라 선언하지 않는다.

## 정리 4. Collisionless photon Boltzmann 방정식과 정확한 Bianchi I redshift

Diagonal Bianchi I에서
\[
ds^2=-c^2dt^2+a(t)^2\sum_i e^{2\beta_i(t)}(dx^i)^2,\quad\sum_i\beta_i=0.
\]
Spatial Killing momentum p_i는 null geodesic을 따라 일정하고, \(E(t)=(c/a(t))\sqrt{\sum_i p_i^2e^{-2\beta_i(t)}}\). Observer tetrad 방향 n_o를 쓰면
\[
\boxed{1+z(n_o)=\frac{a_o}{a_*}
\sqrt{\sum_i n_{o,i}^2\exp[2(\beta_i(o)-\beta_i(*))]}.}
\]
등방 Planck photon distribution이 emitter에서 주어지고 이후 collisionless Liouville \(p^\mu\nabla_\mu f=0\)이면 \(f_o(E_o,n_o)=f_*(E_o[1+z(n_o)])\), 즉 \(T_o(n)=T_*/[1+z(n)]\)이다. \(\Delta\beta_i=\beta_i(o)-\beta_i(*)=\int_{t_*}^{t_o}\sigma_i(t)\,dt\)이면 small-shear에서 \(\delta T/\bar T=-\Delta\beta_{ij}n^in^j+O(\Delta\beta^2)\). 광자 \(T^4\) pressure moment에 대입해
\[
\boxed{\pi^\gamma_{ij}/\rho_\gamma=-(8/15)\Delta\beta_{ij}+O(\Delta\beta^2).}
\]
정확한 finite beta redshift와 \(\ell=2\) shear 근사를 구분한다. 이를 R66 photon tensor에 적용하려면 primordial emission anisotropy, Thomson scattering, beam/foreground 및 source-frame 법칙이 필요하다. 원전 Fleury, Pitrou, Uzan PRD91(2015)043511. 수치 검산은 64×128 Gauss-Legendre/azimuth로 직접 \(T^4\) pressure를 계산, \(\epsilon=10^{-2}, 3\times10^{-3},10^{-3}\)에서 선형식 대비 오차가 각각 5.94×10^-6,5.33×10^-7,5.91×10^-8로 이차 scaling; source 통계 검정 아님.

## 정리 5. Boosted isotropic photons의 rank-one stress와 R66 적용

Radiation 정지계 \(T_*^{ab}=(\rho_*+p_*)U_*^aU_*^b/c^2+p_*g^{ab}\), \(p_*=\rho_*/3\), relative β=v/c라면 Lorentz tensor transformation으로
\[
\rho=\rho_*\Gamma^2(1+\beta^2/3),\quad
|\boldsymbol q|/(\rho c)=4\beta/(3+\beta^2),
\]
\[
\boxed{\pi^\gamma_{ij}/\rho=
[4\beta^2/(3+\beta^2)](\hat v_i\hat v_j-\delta_{ij}/3).}
\]
**비영 boost-only photon stress는 반드시 축대칭이고 signed shape χ=+1**이다. Exact STF tensor를 사용해야 하며 scalar \(C_2\) 크기만으로는 이 필요조건을 확인할 수 없다. R66 retained \(\ell\le6\) model의 \(\chi\)는 PR3 -0.70745, PR4 -0.69503, β≈0.0012335735에서 pure-boost χ=+1. Boost-only tensor와 data tensor의 cosine PR3 0.1356, PR4 0.1519. 이 모델에서 두 tensor가 동일하지 않다는 **조건부 대수 결과**이며 실제 intrinsic CMB quadrupole 검출·significance는 미확정이다.

## 정리 6. Anisotropic-stress-free Bianchi I의 약한 비등방 fossil 관계

Geodesic homogeneous normal, diagonal Bianchi I, spatial Ricci STF=0, **total normal anisotropic stress** \(\pi^N_{ab}=0\), Einstein tracefree spatial equations에서
\[
\dot\sigma_{ab}+3H\sigma_{ab}=0,\qquad
\sigma(t)=\sigma_o[a_o/a(t)]^3.
\]
Photon은 초기 등방·무충돌 test radiation이라고 추가로 가정한다. \(\mathcal I=\int_{t_*}^{t_o}(a_o/a)^3dt>0\)와 \(\epsilon=\|\mathcal I\sigma_o\|_F\ll1\)에서 **선형 차수에만**
\[
\boxed{\frac{\mathsf Q^\gamma_{\rm CMB}}{T_0}
=-\mathcal I\sigma_o+O(\epsilon^2)}
\]
를 얻는다. 여기서 \(\mathsf Q^\gamma\)는 온도 STF quadrupole이며, 그 정상화된 radiation stress는 선형으로 \(\pi_\gamma/\rho_\gamma=(8/15)\mathsf Q^\gamma/T_0+O(\epsilon^2)\)다.

이 **diagonal fixed-eigenframe Bianchi I**에서 exact collisionless photon 전파가 고유축을 보존하는 것은 유한 \(\epsilon\)에서도 성립하지만, eigenvalues의 정확한 비례성과 \(\chi(Q)=-\chi(\sigma)\)는 일반적으로 성립하지 않는다. Nonzero \(\sigma\)의 fixed shape가 검증되었을 때 weak-\(\epsilon\)에서 normalized opposite cosine은 \(1+O(\epsilon^2)\), signed \(\chi(Q)=-\chi(\sigma)+O(\epsilon)\)이다. 독립 심사의 finite-shear 반례 \(\beta_e=(0.4,-0.1,-0.3),\ \beta_o=0\)에서 exact kinetic STF의 \(\chi\)는 linear prediction과 다르다.

선언한 flat benchmark \(\Omega_m=.3153,\Omega_r=10^{-4},\Omega_\Lambda=1-\Omega_m-\Omega_r,z_*=1100\)의 \(\,H_0\mathcal I=\int_0^{1100}(1+z)^2/E(z)\,dz=39523.656338\)를 사용한다. 실제 R66의 retained \(\pi/\rho\)에서 boost-only tensor를 **대수적으로 차분**한 formal template를 역대입하면 PR3/PR4 \(\|\int\sigma dt\|=9.3230\times10^{-6},9.9245\times10^{-6}\), formal \(\|\sigma_o/H_0\|=2.3588\times10^{-10},2.5110\times10^{-10}\)이다. **이것은 Lorentz deboost도, 실제 CMB intrinsic quadrupole 분리도, 물리적으로 정당화된 현재 shear 측정/상한도 아니다.** 순수 boost-only 응력을 정규화된 실제 총응력에서 단순 차감해 rest-frame stress를 복원할 수 없다. Full \(T^{ab}\) energy/flux/stress 및 frame transform, intrinsic emission quadrupole, Thomson source, cosmic variance가 필요하다. Photon anisotropic stress backreaction까지 포함할 때 total \(\pi^N=0\) closure 자체의 유효범위를 재검토해야 한다.

## 정리 7. Local-affine screen motion의 E2/B1/B2 selection rule

같은 국소 Fermi observer와 comoving source의 relative velocity를 \(v^i=B^i{}_j x^j\), \(B=HI+\sigma+\omega\)로 제한한 Euclidean affine tangent 모형에서 \(\dot n=P_n Bn,\ P_n=I-nn^\top\). \(\omega n=\boldsymbol\Omega\times n\)이라는 부호 convention이면
\[
\boxed{\dot n=P_n\sigma n+\boldsymbol\Omega\times n,\quad
P_n\sigma n=\frac12\nabla_{S^2}(n^\top\sigma n).}
\]
따라서 homogeneous local symmetric shear는 E2의 5성분, rigid rotation은 B1의 3성분, **독립 B2는 이 국소 affine gradient에서는 생성되지 않는다**. 두 분야는 spherical full sky에서 직교하며 \(\langle|P_n\sigma n|^2\rangle=\|\sigma\|_F^2/5\), \(\langle|\Omega\times n|^2\rangle=2\Omega^2/3\). 증명: \(P_n\sigma n=\sigma n-n(n\sigma n)\)과 구면 2·4차 angular identities에 직접 대입한다. 실제 cosmological quasar proper motion은 source redshift, null geodesics, observer acceleration, frame rotation, AGN variability에 따른 추가항을 가져 이 local affine 공식 자체가 complete cosmology transfer는 아니다. 2026년 Makarov–Heinesen–Schücker(CQG43 125012) 및 Kouvelis et al.(JCAP06 034)은 degree-2 position drift 신호와 redshift/systematics를 별도로 검토한다.

**실자료** Gaia-CRF3 원본 1,614,173 source, quality 1,580,645. ICRS PMRA* 및 PMDEC 2×2 오류, 16성분 E1/B1/E2/B2 joint Gaussian working fit는 rank16, Fisher condition 7.7007. Coefficient vector norm μas/year: E1 5.1072, B1 4.3304, E2 5.9370, B2 3.9379, E2 signed χ=0.71089. Source-independent nominal Wald p는 E2 약1.0×10^-23, B2 약1.6×10^-9지만 천체물리적 유의도가 아니다. 192 sky-patch score-sandwich에서 E2 성분별 오차는 1.10–1.73 μas/year vs source formal 0.50–0.56이고, 북/남 별도 E2 norm12.16/10.59 및 B2 norm11.07/11.02가 나와 실제 sky footprint/AGN systematics에 민감하다. 이 E2를 무비판적으로 local σ라 해석하면 H0=70km/s/Mpc 기준 \(\|\sigma/H_0\|\simeq0.402\), 약한 균질 shear 근사에 대한 model-adequacy warning일 뿐 cosmic shear detection/limit가 아니다.

## 정리 8. Bianchi I와 V의 normal momentum constraint가 STF shape에 부여하는 조건

Spatially homogeneous normal-frame Codazzi의 **단위와 부호 convention**을 먼저 고정한다. 좌표 \(x^0=ct\), ADM future unit normal \(n^an_a=-1\), \(K_{ij}=-h_i{}^ah_j{}^b\nabla_an_b\) (단위 m^-1), \(j_i^N=-h_i{}^aT_{ab}n^b\) (normal momentum-density times c, J/m^3)로 정의하면
\[
D_j(K^j{}_i-K\delta^j_i)=\frac{8\pi G}{c^4}j_i^N,
\qquad [\mathrm{LHS}]=[\mathrm{RHS}]=\mathrm{m}^{-2}.
\]
물리적 복사 **에너지 flux** \(q_i^{\rm flux}\) (J m^-2 s^-1)를 사용한다면 \(j_i^N=q_i^{\rm flux}/c\)이므로 우변은 \(8\pi G q_i^{\rm flux}/c^5\)로 바뀐다. 이 식은 위 K와 normal orientation에서의 부호이며, R62의 dimensionless Active-BASS \(D_i+\kappa q_i=0\)는 정규화한 \((H,\sigma,a,n,q)\) 및 별도 source-sign convention으로 사용한다. 이 두 표현의 q를 단위·부호 확인 없이 동일시하지 않는다. Type I은 \(a_i=0,n_{ij}=0\), homogeneous spatial connection가 없는 경우 \(q_i^N=0\). 단일 perfect fluid와 positive enthalpy \(\rho+p>0\), subluminal tilt에서는 \(q_i^N\propto(\rho+p)\Gamma^2 v_i\), 따라서 \(v=0\)이다. **Single-fluid Type I tilt는 불허**지만 반대 방향 속도를 갖는 둘 이상의 fluid는 total momentum이 보상될 수 있다.

Type V에서 \(n=0\), nonzero structure vector a, total q^N=0이면 active convention에서 \(3\sigma_{ij}a^j=0\). 따라서 detσ=0, STF spectrum=(λ,−λ,0)이고, σ≠0일 때
\[
\boxed{\operatorname{tr}\sigma^3=0,\qquad\chi(\sigma)=0.}
\]
조건부 필요조건이다. Observer-frame shear로 실제 source-qualified 복원된 χ가 0을 제외할 때만 특정 untilted/normal-q=0 Type V family를 배제할 수 있다. 이번 Gaia E2와 R66 photon stress는 직접 그 normal shear가 아니다. Tilted V에서는 q≠0일 수 있으며 R62가 실제 tilted IX 상태의 존재를 구현으로 검증했다. Instantaneous STF tensor가 Bianchi Lie algebra label이 되는 것은 아니다.

## 정리 9. Full-frame fossil consistency의 계층적 필요조건과 scalar 형태의 함정

제한된 diagonal Bianchi I의 small-\(\epsilon\) photon/Einstein 조건에서만
\[
\frac{\mathsf Q_{\rm CMB}}{T_0}
=-\mathcal I\sigma_o+O(\epsilon^2).
\]
Exact fixed eigenaxes에서 텐서 commutator는 0이어야 하지만, **비례성 및 opposite signed \(\chi\)**는 선형 근사에서만 필요하다. \(C_-=-Q:\sigma/(\|Q\|\|\sigma\|)=1+O(\epsilon^2)\)와 \(\chi(Q)=-\chi(\sigma)+O(\epsilon)\)의 remainder는 체계적으로 유지해야 한다.

R66 Galactic finite-band 텐서를 Astropy SO(3)로 ICRS에 회전시키고, source-qualified current normal shear가 **아닌** R69 Gaia apparent E2와 비교하는 counterfactual: PR4 raw retained \(\chi_{\rm CMB}=-0.6950\), Gaia E2 \(\chi=+0.7109\). 스칼라 \(\chi\) 값의 부호·크기가 가까워도 full tensor normalized opposite cosine은 \(-0.0221\), normalized commutator는 \(1.0295\)다. PR3도 cosine \(-0.0739\), commutator \(0.9987\)이다. R66과 pure boost-only template의 **대수적 차**를 취하면 PR4 \(\chi\approx-0.02465\), cosine \(-0.0500\)이다. 이 차이는 물리적 rest-frame intrinsic tensor가 아니라 비교용 template difference다.

따라서 이 계산은 **실제 Bianchi I 또는 global tilt의 배제가 아니다**. 두 자료가 같은 physical referent를 측정한다는 validated lightcone/frame map과 cross-probe covariance가 없다. 그것이 확보될 때 scalar shape \(\chi\), signed inner product, commutator, redshift response를 모두 동일 likelihood에서 비교할 유용한 hierarchy를 얻는다.

## 10. 일곱 연구 주제에 걸친 다음 실증 경로와 우선순위

| 축 | 물리적 observable 및 바로 시험할 예측 | 현재 결과·다음의 최소 입력 |
|---|---|---|
| P1 tensorized five views | 동일 physical experiment에서 signed tensor, positivity Q, law-specific Π, measure-defined occupancy F, transported G_F. 새 실측정보가 아니라 constrained physics의 설명력 검사. | R69 full tensor χ matching 반례로 scalar reduction 검증; actual R64/ R67 full-covariance 같은 source 실험과 비교. |
| P2 low-ell CMB | collisionless Liouville photon temperature, signed radiation π/ρ, boost-only χ=+1, integrated shear fossil closure. | R66 finite-band readout와 R69 kinematic boost 차분 완료; Commander 실제 T/E/B matched MC, KQ/beam/foreground 필요. |
| Dipole anomaly | 반구 odd/even parity, source selection, boost count response k(S)β, clustering-law conditional vector. | R65 peak-integrated same-source covariance 재사용; flux cut과 mask에서 k/selection law 식별. |
| P6 kinematics | directional H multipole H,A,σ; nonradial E2/B1/B2 local affine screen; Type I/V constraint shape. | Actual Gaia 16D fit 완료, l2 redshift/observer/jet source response와 VLBA reference frame 필요. |
| P5 Bianchi morphology | Type V q=0 ⇒ physical χ(σ)=0, restricted Type I fossil exact shared frame and signed inversion. | R62 fixed-Gaussian tensor shape classes 모두 compatible; 실제 물리 response 추가 전에는 classification 미확정. |
| P3 directional H | full-sky hemisphere mean은 dipole, mask에서는 STF contamination ΔM; \(\mathfrak H\) 9 modes. | CF4 actual original 38,053 group mask leakage 완료, R64 grouping/weight/covariance로 source selection correction 검증. |
| P4 local boost/global tilt | photon Lorentz boost-only stress, Gaia observer proper-motion E1 ≠ β velocity, actual matter/radiation relative drift. | R63 CF4 compensated history practically unresolved; independent kSZ remote dipole or CMB aberration mapping 필요. |

**일차 출판 후보 (조건부):** (1) Source-response corrected hemispherical directional-H test with full weighted tensor vs naive hemispheric mean, same CF4 sample, method selection; (2) Gaia E2/B2 residual parity and redshift selection with source-frame systematics, compared under same response to 2026 position-drift literature; (3) R66 signed CMB stress and one Bianchi I photon-kinematic transfer injection, matched Commander null necessary. 물리적 transfer가 없으면 joint physical likelihood는 생성하지 않는다.

**성공 기준:** 한 common physical functional의 source-qualified identified interval과 coverage 또는 finite hypothesis family recovery / calibrated exclusion을 산출. **실패/중단:** 물리 frame/optical transfer 또는 independent calibration data가 없으면 conditional numerical diagnostics로 보존하고 검출·Bianchi 귀속을 주장하지 않는다. Existing P1–P6 publication acceptance and R68 scientific results untouched.

## 실측·수치 증거 상태

- established / literature-supported: Heinesen 2020 multipole directional cosmography; Fleury–Pitrou–Uzan PRD91(2015) Bianchi I light propagation; relativistic radiation kinetic moments; 2026 Gaia Bianchi position drift; original R62 Bianchi Codazzi mechanics.
- derived: 천구 hemisphere parity와 mask leakage, angular second/third STF moments, exact diagonal Bianchi I redshift and linear CMB stress, boost-only photon stress χ requirement, restricted Type V shape χ, local-affine E2/B1/B2 and conditional tensor fossil relation.
- numerically checked: Wolfram exact angular moment and hemisphere identities, 43 final focused source/mathematical/code tests after bounded repairs; actual CF4 sky mask 38,053 groups; actual R66 finite-band π/ρ, Gaia 1,580,645 source 16 coefficient fit; Gaussian conditional numeric likelihood and kinetic Gauss-Legendre quadrature. Each result in RESULTS includes its own scope.
- unresolved: full real-world physical and statistical qualification, actual CMB/Gaia source transfer and optical kinematics, complete correlated Gaia scanning law, source-matched joint p-values, Bianchi type/model posterior. This project is not reporting a new cosmological discovery.
