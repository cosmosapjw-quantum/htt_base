# R69 확장: 물리적 x를 실제로 입력할 때 Q, Π, F, G_F가 어떻게 제약되는가

2026-11-18, parent d45bce72c655ecccd6165fd750e3f1bcfe69b46f. Metric (-,+,+,+), c, ħ, k_B 유지. R68의 typed five-view 의미를 보존하고 R61–R69 실제 관측 결과를 재사용한다. 수치 source: RESULTS/FIVEVIEW_X_RESPONSE_ATLAS.json, scripts/r69/fiveview_response.py, tests/test_r69_fiveview_response.py. 이 연구는 cosmological discovery, 새로운 보편적인 통계학 정리, independent astrophysical significance를 주장하지 않는다.

## 0. 수학적 계약: x 자체와 함께 필요한 보조 물리 입력

하나의 관측 실험 E를 물리 referent θ, source/observer frame, likelihood P(D|θ,ψ), transmission/optical/kinetic map T, survey operator M, calibration/nuisance ψ, finite physical reference body K 및 measure μ로 정의하자. Signed x는 이러한 실험의 *명시적인 타입*을 가진 추정량/물리 상태다.

Q_K(x)=inf{t>0:x ∈ tK}, Π_L(x)=Pr_L(T(X)≥T(x)), F_{μ,K}(E_x)=μ(E_x∩K)/μ(K), G_F=F_j−F_i (identical physical referent with actual time/depth transport and correlated law)다. 모든 식은 해당 필요 구조가 있는 경우에만 정의한다. Q가 convex gauge가 아니라 nonconvex Einstein constraint residual인 경우 같은 Q라고 부르지 않는다; residual은 별도 진단이다. Gaussian whitened noise Q_stat와 physics gauge Q_phys도 다르다.

**비유일성 정리:** 동일 scalar x=.2라도 K=[−1,1] 또는 [−.5,.5]는 Q=.2,.4를 준다; Gaussian null N(0,1)과 N(0,.1²)은 양측 Π≈.8415와 .0455를 준다; E=[.1,.3], μ=dx와 dμ=(1+x)dx on [−1,1]은 F=.10과 .12를 준다. 미래 evolution이 다른 두 model은 동일 x(t0)에도 G_F가 다르다. 따라서 물리 equation/measure/null/transport 없이 universal x-only deterministic map은 없다. 이는 임의성을 늘리라는 뜻이 아니라 **물리 방정식이 제공하는 입력만 사용할 것**이라는 제약이다.

## 1. 광자 kinetic theory: x=(f_i=q_i/(ρc), S_ij=π_ij/ρ) [vector+tensor mixed]

비음수 photon angular intensity ν(dn), ∫ν=1, f=∫n dν, S=∫nn^T dν−I/3. 광자 moment realizability의 정확한 convex physical body는

K_γ={ (f,S): S=S^T, tr S=0, M=[[1,f^T],[f,I/3+S]] PSD }.

**필요성**은 M=∫(1,n)(1,n)^T dν가 PSD라는 사실. **충분성**은 M00=1, tr M_sp=1인 compact spectrahedron의 extreme points가 모두 rank1인 것으로 보인다. Rank r≥2면 range 위 symmetric perturbations가 r(r+1)/2≥3차원이고 두 affine constraint를 동시에 유지하는 nonzero perturbation을 골라 작은 ± 변화가 PSD를 유지하므로 extreme이 아니다. Rank1 extreme는 (1,n)(1,n)^T, |n|=1. 따라서 convex hull representation으로 모든 실현 가능한 M은 비음수 방향 분포의 mixture이다. 이는 기존 radiation moment realizability theory와 일치한다. Smooth blackbody/free-streaming Einstein–Boltzmann history의 실현과는 다른 문제다.

이에 대한 정확한 mixed physical gauge는

Q_γ(f,S)=max(0,−λ_min([[0,√3 f^T],[√3 f,3S]])).

증명: x∈tK_γ ⇔ [[t,f^T],[f,tI/3+S]] PSD. Positive D=diag(1,I/3)로 congruence 변환하면 tI+B PSD이므로 최소 t는 −λ_min(B)이다. Q≤1 ⇔ 실현 가능 moment. f=0에서 R68 radiation Q=max(0,−3λ_min S), S=0에서 Q=√3|f|. 따라서 stress positivity만으로는 photon-flux/stress physical consistency를 인증하지 못한다.

Π: 만약 N개 **독립 isotropic photon directions**을 직접 sampling하는 별도의 kinetic toy experiment면 covariance(f)=I_3/(3N), covariance(STF5 S)=2I_5/(15N), cross=0. CLT에서 T=N[3|f|²+(15/2)||S||_F²] → χ²_8와 Π≈tail_χ²8(T). 이 sampling null은 CMB의 cosmic variance, foreground, Commander telescope sky law가 아니다.

F: 동일 x=(f=0,S=0)라도 uniform sphere는 event |n_z|>.9에서 normalized energy cap=0.1, six symmetric beams ±x±y±z는 1/3을 준다. 따라서 **moment x만으로 photon energy angular occupancy F는 결정되지 않는다.** 특정 kinetic closure를 선언해야 한다. 예: max-entropy p(n|x)∝exp[λ·n+Λ_STF:nn]. S² 상에서 interior x의 exponential-family logZ Hessian은 sufficient-statistic covariance이므로 해당 closure의 multiplier는 국소적으로 유일하다. α/β 등의 실제 photon collision/transport를 자동 해결한 것은 아니다.

실제 구현된 β=.3의 boost thermal-intensity와 동일 1st/2nd moments를 갖춘 axisymmetric maximum-entropy closure: normalized x_flux axial=.3883495146, x_STFzz=.0776699029, max |moment error|=2.8e−17; |μ|>.9 cap F boost exact .1535975902, F ME .1529194181 (difference −.0006781721). Third moment도 .2451159464 vs .2443594615. 따라서 x 동일성이 F 또는 higher moments 동일성을 뜻하지 않는 physical-closure benchmark다. G_F는 collisionless/collisional Boltzmann transport와 같은 angular event/measure history를 제공할 때만 정의한다.

**실제 R66** retained photon stress S만 source-qualified finite-band에 기록됐고 동일 frame의 완전한 f는 없다. PR3 Q_stress=1.16370051e−5, PR4 Q_stress=1.24852860e−5는 계산 가능; Q_joint(f,S)는 실제 관측으로 인증되지 않는다. 모델 boost f를 별도로 가정하면 ~.002848인 comparator가 생성되나 measured joint moment로 쓰면 안 된다. Commander end-to-end Π, F, physical depth G_F는 현재 미정이다.

## 2. GR directional Hubble: x=(H=Θ/3,d=−A/c,S=σ)

Heinesen vertex cosmography에서 H(n)=H+d·n+n^TSn, tr S=0, H>0. 모든 방향에서 leading local Hubble redshift coefficient가 비음수가 되도록 정한 K_H={ (d/H,S/H): H(n)≥0 ∀ |n|=1 }는 convex body이며

Q_H(x)=−min_{|n|=1}[d·n+n^TSn]/H.

Full-sky 평균 of the square bracket=0이므로 minimum≤0. Q_H<1 iff H(n)>0 ∀n. 이것은 **物理 exact leading-vertex positivity test**이며 finite-z distance-defined H_D나 whole-history expansion positivity와 다르다.

축 p를 공유하는 acceleration과 axial shear S=s(pp−I/3), d=d_parallel p에서 u(t)=s(t²−1/3)+d_parallel t. s>0, |d_parallel|≤2s이면 min u=−s/3−d_parallel²/(4s), 따라서 Q_H=[s/3+d_parallel²/(4s)]/H; 그 밖(s≤0 포함) min u=2s/3−|d_parallel|, 따라서 Q_H=[|d_parallel|−2s/3]/H. Mixed shear–acceleration의 physical condition을 component norm 2개로 줄이지 않고 **한 방향의 total expansion**으로 판정하는 식이다. 일반 d,S는 spherical trust-region eigen/secular problem으로 global min을 계산하고 repeated eigenvalue hard case를 처리한다 (코드의 rotation regression 포함).

Π_H: source-shared covariance와 profile nuisance가 고정된 \hat u=(d,S)에서 T=\hat u^T V_u^{-1}\hat u를 Gaussian fixed-law에서만 \chi²_8으로 해석한다. Unknown preferred axis를 data에서 최적화하는 family는 regular Wilks가 아니며 R68 scanned-axis calibration이 필요. F_H: physical K_H, Lebesgue chart 또는 명시한 physical prior μ, 원-source confidence set E_x로 occupancy 계산할 때만. G_F: observer/source congruence, finite-z optical transfer 및 cross-depth covariance가 실제로 정의된 F(z)를 비교할 때만.

**실제 CF4 R62** K0 source tensor를 가정적으로 physical S/H로 두고 d=0,H=1로 설정하면 Q_H=0.0177026, min fractional H=0.9822974, Gaussian STF5 zero-tail Π≈.1046965. 하지만 실제 K0는 phenomenological finite-depth log-distance response이며 physical σ/H가 아니다. 해당 수치는 source gauge가 어떤 응답을 만드는지 보여주는 **conditional map**, cosmic anisotropy 상한이 아니다.

## 3. Distance-defined directional H(z,n): x=(η(z,n),η_z,η_zz,C_source)

D_L(z,n)=D_L,ref(z)exp(−η(z,n)), smooth flat reference χ(z), B(z)=H_ref(z)χ(z)/c에서

H_D/H_ref=e^η/(1−Bη_z), q_D=−1+(1+z)∂_z log H_D.

정의역 positivity는 Q_D[x;Z]=max{0,sup_{(z,n)∈Z} B(z)η_z(z,n)}<1에 의해 보증된다. 이것은 H_D 자체의 물리적 monotonicity/derivative domain에 대한 one-sided gauge이며 **spacetime Θ/3의 측정과 다르다**. x가 derivative field이면 같은 z에서 additive angular calibration a(n)가 η만 shift하고 η_z를 바꾸지 않아 Q_D가 불변이다. 실제 source estimator의 omission of angular terms와 mask에서는 calibration이 다른 fitted η_z를 만들어 이 함수 수준의 불변성이 깨질 수 있다.

Π: R64의 same-source 68/72D method/source nuisance를 유지한 fixed Gaussian nested angular-depth test. F: Z domain K_D와 source confidence set, explicit finite measure under the chosen observer frame; 없는 경우 UNAVAILABLE. G_F: 실제 optical/source transfer 및 C_ij와 matched angular support 후 occupancy contrast. \eta(z)-\eta(z*) 또는 H_D ratio는 별도 G_x이지 자동 G_F가 아니다. 한 R64 exemplar η_z≈−2.8516, denominator 1−Bη_z=1.232736>0에서는 one-point Q_D=0만 계산되며 전 sky/depth positivity를 입증하지 않는다.

## 4. Radio/source-count dipole: x={d_b, quadrupoles, flux membership, C_cross}

한 finite flux bin에 대한 선도 velocity response는 d_b=k_b β+u_b, k_b=2+(1+α)[S_lo g(S_lo)−S_hi g(S_hi)]/N_b. 알려진 k_b, source selection, intrinsic residual u_b 및 공동 covariance 아래서 \hatβ=(K^T C^-1 K)^-1K^T C^-1 d, residual T=(d-K\hatβ)^T C^-1(d-K\hatβ)와 model-conditional Π를 계산한다. u_b가 arbitrary이면 relative velocity β는 일반적으로 미식별된다.

Observed R65의 d_b는 log-intensity angular coefficients이며 exp(d·n)로 모델링하므로 **linear count positivity |d|≤1을 이 x의 physical Q라 부르면 안 된다**. Source-calibrated k_b와 u_b로 actual β를 식별한 때만 causal Q_β=|β|가 있다. 기존 동일 NVSS provider peak/integrated shared-source Δ=(-.001644,.00552467), C_Δ를 보존하면 Q_stat=sqrt(Δ^T C_Δ^-1Δ)=5.56682, fixed-Gaussian Π=1.86519e−7. 이는 실제 radio LSS/selection 물리적 anomaly 확률이 아닌 working-law tail이다.

F: 실제 survey/source population의 calibrated selection body+reference measure를 제공해야 함. GF: flux-cut path는 cosmological time/depth가 아니므로 NOT_APPLICABLE. 실제 redshift-resolved radio source distribution 및 transport가 도입되면 새로운 G_F(z) 가능.

## 5. Beyond-FLRW kinematics: x=(Θ,σ_ab,ω_a,A_a,β_a, matter moments)

Physical β는 causal unit ball Q_beta=|β|. CMB photon moments가 같은 frame으로 입력되면 Q_gamma(f,S)를 추가로 적용할 수 있다. 그러나 전체 Einstein initial-data solution manifold (Hamiltonian/Codazzi/Jacobi/field evolution)는 일반적으로 nonconvex라 보편적인 하나의 Q gauge로 대체할 수 없다. Physical state가 q,A,π 등도 포함할 때 perfect-fluid Euler (ε+p)A_a/c²+D_a p=0, Raychaudhuri 및 shear evolution이 각 component를 연결한다. x에 4개 kinematic component가 있다는 사실만으로 실제 survey가 각 성분을 측정한 것은 아니다.

Π: R61의 fixed Gaussian 11D conditioning 아래 apparent x zero-test와 동시에 calibration-body image. Vorticity는 현재 radial-only response에 식별 가능한 열이 없다. F: causal |β|<1에 균등 Euclidean measure라는 명시적 benchmark를 선택하면 R61 conditional outer r=1260.786 km/s/c=.00420553 ball occupancy 상한 r³=7.4381e−8. 이는 임의의 reference volume ratio이고 posterior/rarity/tail이 아니다. G_F: 실제 initial data→physical τ/redshift transport와 same-source cross-window covariance로 F path를 만든 경우에만. Existing R61 K(.08)−K(.02)는 separate signed G_x, not F occupancy evolution.

## 6. 모든 Bianchi type을 포함한 geometry/matter state: x=(a_i,n_ij,H,σ,π^N,q^N,ε_N,...)

Structure constants C^k_ij=ε_ijℓ n^{ℓ k}+a_i δ^k_j−a_j δ^k_i에는 Jacobi n^{ij}a_j=0. Hypersurface normal Gauss/Hamiltonian
\( {}^3R+(6H²−σ²)/c² = 16πG ε_N/c^4+2Λ \)
및 momentum/Codazzi는 physical state의 consistency equations이다. All-type constraint surface는 nonconvex이고 family strata와 topology가 바뀌므로 임의 single convex Q 대신 causal matter β, positive radiation body Q_gamma, source-weighted residual of constraints를 **구분**한다. Constraint residual은 original Minkowski Q와 동일한 함수가 아니라 auxiliary이다.

**정리: Einstein/kinetic stress와 intrinsic geometry가 signed STF 형태를 어떻게 움직이는가.** Geodesic homogeneous normal, Fermi orthonormal frame, fixed source convention에서
D_tσ=−3Hσ+\mathcal D,
\mathcal D=(8πG/c²)π^N−c² {}^3S.
I2=trσ², I3=trσ³, χ=√6 I3/I2^(3/2), σ≠0이면
\[
\boxed{
D_tχ=\frac{3\sqrt6}{I_2^{3/2}}
\left[\operatorname{tr}(σ²\mathcal D)
-\frac{I_3}{I_2}\operatorname{tr}(σ\mathcal D)\right].
}
\]
증명: \dot I2=2tr(σ\dotσ), \dot I3=3tr(σ²\dotσ)와 quotient differentiation에 \dotσ=−3Hσ+\mathcal D를 대입하면 모든 −3Hσ 기여가 상쇄된다. 따라서 **isotropic expansion dilution은 χ의 변화율에 직접 기여하지 않으며**, intrinsic 3-Ricci STF와 anisotropic normal stress의 드라이버가 형태를 변화시킨다. \mathcal D=λσ이면 χ constant. 비축대칭이 아닌 χ=±1 extreme에서는 첫 shape derivative가 0일 수도 있으므로 higher order와 eigenvalue splitting이 필요하다. Generic distinct eigenvalues frame에서는 \Omega_{ij}=\mathcal D_{ij}/(λ_j−λ_i); degenerate eigenvalues에서 eigenframe는 물리적으로 단일하게 정의되지 않는다.

Π: actual Bianchi type/mode/source polarization or optical response와 model priors에 따른 law가 있어야 하며, singular strata에 naïve Wilks를 쓰면 안 된다. F: noncompact family와 diffeomorphism gauge를 적절히 축약하고 finite measure를 지정해야 occupancy가 의미를 가진다. G_F: Einstein/kinetic time evolution under same Bianchi physical state/source frame가 있을 때만 physical. R62 apparent K0 shape χ≈−0.122766, p5_zero≈.1046965 및 conditional apparent one-sided Q≈.0177026은 실제 Bianchi label posterior가 아니다.

## 7. Local observer boost vs global matter–radiation tilt: x=(u_O,u_M,u_R, their histories)

관측자 O, 물질 M, 복사 R가 같은 사건에서 정규화된 4-velocities라면 Γ_MR=−g(u_M,u_R)/c², β_M|R=√(1−Γ_MR^-2). **Γ_MR는 observer의 local Lorentz chart 변경으로 바뀌지 않는다**. 그러나 서로 다른 위치·시간의 global tilt claim은 matter/radiation congruence identification 및 transport를 필요로 한다. Causal Q=|β_M|R가 진짜 relative velocity에 정의되며, observer-frame Gaia E1 proper motion은 observer acceleration/aberration drift이지 그 속도가 아니다.

Π: CMB aberration/count dipole/Gaia proper motion/CF4 bulk/kSZ remote dipole를 동일 physical history로 끌어오는 source-qualified forward maps와 실제 cross-source covariance를 가진 **하나의 law**가 존재한 뒤에 local-only vs global-tilt 비교. R63 CF4 compensated history separation bound가 거의 검정 size와 같았던 것은 restricted model result이지 전역 불가능 정리 아님. F: causal β ball reference measure는 Euclidean speed, hyperbolic rapidity, dynamical prior 중 선택에 따라 달라져 x만으로 결정되지 않는다. G_F: actual β_M|R(τ) matter/radiation evolution, observer source window overlap이 있을 때만; flux-bin 변화나 Gaia frame spin의 증가를 β history라고 부르지 않는다.

## 공통 F/G_F의 exact 동역학적 한계

Physical axial photon stress S=α(nn−I/3), K_α=[−1/2,1], confidence/event E_x=[α−r,α+r], reference uniform Lebesgue on K를 명시하면
F(α)=length(E_x∩K_α)/(3/2).
내부 α∈[−1/2+r,1−r]에서 F=2r/(3/2)로 항상 상수다. 따라서 **x가 실제로 변해도 G_F=0일 수 있다**. Dynamics 검정을 위해 signed G_x, shear χ and actual observed history를 auxiliary로 유지해야 한다. This does not redefine original occupancy F or G_F.

## 실제 자료 입력에 대한 상태별 출력

| 축 | Source-derived x | 계산된 Q | 법칙이 있는 Π | F / G_F |
|---|---|---|---|---|
| P1 | R61 conditional CF4 11D state and speed outer | Q_beta≤.00420553 | zero apparent response max nominal p11=.01534 | uniform causal β-ball outer F≤7.438e−8, chosen reference only; GF unavailable |
| P2 | R66 PR3/PR4 finite-band S | Q_rad=1.1637e−5 / 1.2485e−5 | Commander actual T null unavailable | actual flux missing for Q_joint; photon F needs intensity or closure; GF NA |
| Radio | R65 paired signed 2D Δ and C_Δ | Q_stat=5.56682; physical log-count Q absent | conditional Gaussian Π=1.8652e−7 | selection body/measure absent; flux-cut GF NA |
| P6 | R61 (s,a,beta), omega unmeasured | causal beta bound, full GR Q missing | fixed Gaussian working law, physical omega unidentifiable | canonical finite GR prior/transfer absent |
| P5 | R62 source K0 5D apparent | apparent Q_H=.0177026 if hypothetically physical | fixed Gaussian zero-STF Π≈.10470 | physical Bianchi x and measure/transfer absent |
| P3 | R64 (eta,eta_z,eta_zz) one exemplar | single-point Q_D=0; denominator1.232736>0 | source/operator Gaussian nested test | all-sky physical K_D and matched F depth absent |
| P4 | R63 history + solar observer boost model | Q_beta=|beta_rel| when actual same-frame β known | restricted CF4 history weak power | frame-matched beta prior and dynamical F absent |
| Gaia E/B | R69 actual 1.58m source x16 | B2 model tube Q depends on a sky-systematic allowance not measured | source-independent Gaussian B2 Π≈1.6e−9 (NOT astrophysical) | source-redshift/observer transfer, physical prior absent |

All x-to-four links and unavailable outputs are encoded in RESULTS/FIVEVIEW_X_RESPONSE_ATLAS.json. The numerical statuses deliberately prevent a conditional diagnostic from becoming a physical cosmological anomaly claim. Main methodological contribution: exact radiation kinetic moment body, physical Hubble positivity gauge, Einstein shear shape-driver, and source-specific null/closure/measure constraints, not new Fisher information.

## 심사 후 계산·물리 자격 정정 (R69)

독립 read-only 심사에서 Hubble gauge minimizer의 물리 단위 의존성과 cap discontinuity를 무시한 Gauss–Legendre 적분의 systematic bias가 발견됐다. 이제 (S,d)의 공통 스케일을 정규화하고 spherical trust-region KKT residual과 hard case를 검사한다. H=10^-12, S=diag(-10^-12,0,10^-12), d=(10^-12,0,0)에 대해 Q_H=2, min H(n)/H=-1을 회복했다. 단위계 재척도와 비자명한 hard-case regression을 보존했다.

beta=.3, cap abs(mu)>.9에서 두 cap의 불연속 경계를 분할 적분한 결과는 exact-boost F=.15359759018323188, ME closure F=.1529194181103092, 차이 -.00067817207292267이다. 이전 cap mask를 통째 Gaussian quadrature에 씌운 F=.1568503863/.1561683527은 INVALID historical outputs로 사용하지 않는다. 동일한 x로도 F가 closure에 따라 달라진다는 수리적 결론은 유지된다. CMB null/predictive law는 여전히 확보되지 않았다.

독립 심사에서 Bianchi-I fossil 텐서의 finite-anisotropy 정확한 비례 주장은 부적절하다고 확인되었다. PHYSICAL_THEOREMS_KO.md 정리 6/9는 이미 first-order plus O(epsilon²)로 수정했으며, 구현 docstring과 hypothesis status까지 정정했다. Codazzi q^N의 운동량 에너지밀도 versus 에너지 flux 단위도 분리했다. 각 실제 관측 atlas는 conditional working-likelihood이며 cosmological detection/physical Bianchi posterior가 아니다.


## 8. 물리적 x 변화에 대한 Q, Π, F, G_F의 미분 응답

앞선 각 x의 순간값과 그 물리적 시간·심도 변화는 별개의 입력이다. 이 차이를 명확히 하는 세 개의 반응 정리를 추가한다.

**정리 A (kinetic Qγ의 민감도).** B(f,S)= [[0,√3 f^T],[√3 f,3S]]의 최소 고유값 λ*(t)<0이 단순하고 normalized eigenvector w=(w0,w_vec)라면 Qγ=−λ*. Hellmann–Feynman 정리로
\[
\boxed{\frac{dQ_\gamma}{d\tau}
=-2\sqrt3\,w_0\boldsymbol w\cdot\dot{\boldsymbol f}
-3 w_iw_j\dot S_{ij}.}
\]
증명은 B(t)w(t)=λ*w(t) 미분 후 w^T으로 곱하면 w^T dot w 항이 상쇄되는 것이다. λ*=0에서 gauge kink, 반복 최소고유값에서는 일반 단일 미분 대신 subgradient/directional derivative가 필요하다. dot f, dot S는 실제 collisionless/collisional Boltzmann moment hierarchy에 의해 l≥3 및 source/metric과 coupling되므로 **하나의 순간 x=(f,S)만으로 Qγ의 미래를 결정할 수 없다**. kinetic_Q_susceptibility 함수는 단순고유값 조건 아래 대수 응답을 구현·중심차분 검산했다. 측정된 cosmic photon energy transfer를 구현했다는 뜻은 아니다.

**정리 B (directional QH의 envelope 응답).** 모든 방향의 \(\mathfrak H(n)=H+d\cdot n+nSn\) 중 최악방향 n*가 유일하고 smooth하며 m=d·n*+n*Sn*<0일 때 QH=−m/H. Envelope theorem으로
\[
\boxed{
\dot Q_H=
-\frac{\dot d\cdot n_*+n_*\dot S n_*}{H}
+\frac{m\,\dot H}{H^2}.
}
\]
n*의 시간미분이 없는 이유는 최솟값에서 tangent gradient가 0이기 때문이다. 물리적으로 QH의 증가가 꼭 shear 성장만을 뜻하지 않는다. dot d, dot S, dot H와 실제 최악방향을 함께 보아야 한다. Full-sky 최소의 퇴화나 m=0에서는 단일 derivative가 정의되지 않을 수 있다. Geodesic homogeneous d=0, sigma(t)∝a^-3이고 eigenframe 고정일 때 \(\dot Q_H/Q_H=-3H-\dot H/H\) (Q>0). 이것은 특정 물리 closure의 결과이지 보편적인 directional distance-H evolution이 아니다.

**정리 C (법칙 조건부 Π와 angular occupancy F의 변화).** 고정된 df k의 Gaussian law에서 Π(t)=survival_χ²_k(T(t))이고 T=delta x^T C^-1 delta x, delta x=x−mu이면
\[
\dot T=2\delta x^\top C^{-1}(\dot x-\dot\mu)
-\delta x^\top C^{-1}\dot C C^{-1}\delta x,\qquad
\dot\Pi=-f_{\chi_k^2}(T)\dot T.
\]
이는 **같은 null law family**가 유지되는 경우의 statistical response이며 실제 spacetime dynamics가 아니다. Rank/null/selection이 바뀌면 다른 law로 새로 calibration해야 한다.

동일 observer sky의 round-area measure를 지정하고 smooth sign field u(n,t)=d(t)·n+nS(t)n, \(F_\Omega(t)=(4\pi)^{-1}\int\Theta[u(n,t)]d\Omega\)라 두자. \(\nabla_{S^2}u\ne0\)인 regular zero contour에서 coarea theorem으로
\[
\boxed{
\dot F_\Omega=
\frac1{4\pi}\oint_{u=0}\frac{\dot u}{|\nabla_{S^2}u|}\,d\ell.
}
\]
증명: 분포론적 도함수 dΘ(u)/dt=δ(u)dot u를 구면에서 적분하고 coarea identity를 적용한다. 특히 u(n,t)=a(t)u0(n), a(t)>0이면 \(\dot u=(\dot a/a)u=0\) on u=0이므로 \(\dot F_\Omega=0\)이지만 \(\dot x\ne0\)일 수 있다. **즉 GF=0는 physical amplitude 진화가 없었다는 뜻이 아니다.** 실제 시간의 GF라고 해석하려면 동일 observer/source congruence, screen transport, physical sky measure 및 cross-epoch sampling law가 필요하다. 이 밖의 경우 FΩ(z)는 geometrical depth-labelled readout일 뿐 원래 physical GF가 아니다.

**물리적 함의:** 고정 x에 대해 Q는 feasibility margin, Π는 하나의 null law의 rare-event probability, F는 선택한 측도·사건의 크기, GF는 source-transferred occupancy history를 의미한다. 서로 다른 정보이므로 서로의 미분이나 크기를 대신할 수 없다. Isotropic dilution만으로 χ는 변화하지 않고, source-weighted FΩ는 진폭이 변해도 그대로일 수 있다. 이 두 불변성은 물리적 이유가 다르다.
