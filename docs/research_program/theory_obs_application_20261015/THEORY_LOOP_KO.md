# HTT 기존 이론의 실제 CMB/CF4 관측 적용: 이론 연구 루프

**2026-10-15.** 출발 커밋 13d8d85fa470d645d008986e8f77d8d0f70fdf54. 목표는 완성된 GR 광학 역산, 국소 Lorentz boost와 부분식별 정리를 실제 보유 관측상품의 고정 연산자로 연결하는 것이다. Native Bianchi Boltzmann solver와 새로운 물리 검출은 연구 범위가 아니다.

## R1–R3: 목표, 원전과 이론 계약

**문제 A (SMICA):** local boost의 열역학적 온도 생성자를 실제 mask·동시 harmonic 적합에 전달하면 보존된 32개 온도 계수는 어떤 접선 반응을 나타내는가? 소스 복원 상한 및 허용된 고차 source nuisance에 따라 얼마나 변하는가?

**문제 B (CF4):** 현재 실제 CF4 그룹의 방향·깊이 분포가 광학적 절편 4개와 기울기 9개의 결합 설계 공간을 분리할 조건을 갖추는가? 좁은 depth shell과 방법별 자유 영점 nuisance는 얼마만큼 정보를 잠식하는가?

근거: HTT Report A R3 (2026-09-04) §§3–11, HTT 종합이론 보고서 (2026-09-13) §§8–13·16–24, GR·통계 보고서 (2026-09-30) §§3–4. 기존 회전불변량, boost response와 exact optical inverse 정리는 각각 등록된 전제 안에서만 재사용하였다.

원전 비교:
- Planck Collaboration, A&A (2014), Doppler boosting of the CMB: https://www.aanda.org/articles/aa/full_html/2014/11/aa21556-13/aa21556-13.html
- Dai/Chluba 계열 harmonic aberration kernels: https://arxiv.org/abs/1403.6117
- Heinesen, JCAP 05 (2021) 008, anisotropic Hubble law: https://iopscience.iop.org/article/10.1088/1475-7516/2021/05/008
- Tully et al., ApJ 944, 94 (2023), Cosmicflows-4: https://iopscience.iop.org/article/10.3847/1538-4357/ac94d8
- Duangchan et al., A&A (2026), CF4 forward modelling: https://www.aanda.org/articles/aa/full_html/2026/04/aa56645-25/aa56645-25.html

CMB는 Galactic HEALPix, outward sky direction n, beta=v/c, thermodynamic Doppler weight 1, temperature fluctuations in microK. CF4는 J2000 equatorial RA/Dec, published DMzp and e_DMzp with frame-derived Vcmb. 서로 다른 방향계의 관측량을 공통 물리 frame으로 사상하지 않았다. 여기서 CF4 proxy z=Vcmb/c는 이상적 absolute vertex redshift intercept가 아니다.

## R4–R5: 구성적 유도

### A. Mask와 fitting을 포함하는 local boost Jacobian

계량 부호 (-,+,+,+), outward direction n과 e_theta,e_phi에 대해 일차 로런츠 generator의 Cartesian 세 열은

\[
 {\cal G}_a[T](n)=n_a T(n)
  -(e_\theta)_a\partial_\theta T(n)
  -(e_\phi)_a\frac{\partial_\phi T(n)}{\sin\theta}.
\]

관측 mask M에 고정된 ell0..5 simultaneous OLS projection P_M (36 x N_selected)와 ell2..5 retained selector R (32 x 36)을 적용하면

\[
 J_L=R P_M {\cal G}[T_L]|_M,\qquad
 T_L(n)=\sum_{\ell\le L,m}a_{\ell m}^{(L)}Y_{\ell m}^{\rm real}(n),
 \quad L\in\{5,8,12\}.
\]

여기서 source a^(L)은 **이미 관측된** SMICA 하늘을 mask 안에서 L까지 재적합한 계수다. 즉 J_L은 관측된 source surrogate에 새로운 미소 boost를 주입하는 접선 연산자이지, 원래의 unboosted intrinsic source field, 실제 observer beta 또는 full Planck compsep transfer를 역복원한 결과가 아니다.

정확한 monopole 제어: G[T0]=T0 n은 순수 ell1 성분이다. 따라서 retained ell2..5에서 R P_M n = 0. 이것은 O(beta^2) kinetic quadrupole, beam effects 또는 frequency conversion이 없다는 주장이 아니다.

모의실현 표본 공분산 C가 SPD, 미해결 ell6..12 source response가 K일 때, 사전에 정한 **추가적인** stochastic nuisance 진폭 A를 가정한 조건부 Fisher stress는

\[
 C_t=C+tKK^T,\quad t=A^2,\qquad
 F_\beta(t)=J^T C_t^{-1}J.
\]

직접 미분하여

\[
 \frac{dF_\beta}{dt}
 =-J^T C_t^{-1}KK^T C_t^{-1}J\preceq0.
\]

이는 유한 선형-Gaussian *가정 모델* 안에서 정확하다. 미해결 모드에 추가한 A^2KK^T는 기존 CMB 모의표본에 이미 포함된 high-ell cosmic variance를 중복계산할 수 있으므로, 검증되지 않은 물리 likelihood 항으로 사용하지 않는다.

### B. 광학 절편–기울기 공간과 calibration nuisance

기존 광학 역산의 자유 설계는

\[
 X=[E_4(n_i),(r_i/r_\mathrm{ref})E_9(n_i)]
 \in {\mathbb R}^{N\times13}.
\]

E4는 monopole+dipole, E9는 monopole+dipole+STF quadrupole이다. 이 13개는 실제 velocity mass-shell 제약을 적용하기 이전의 unconstrained 계수다. CF4에서는 오직 기하 배치 평가용으로

\[
 z_\mathrm{proxy}=V_\mathrm{cmb}/299792.458,\quad
 d_{L,\mathrm{proxy}}=10^{(\mathrm{DMzp}-25)/5}\,\mathrm{Mpc},
 \quad r_\mathrm{proxy}=d_{L,\mathrm{proxy}}/(1+z_\mathrm{proxy})^2
\]

를 사용했다. 이 r은 실제 optical-vertex d_A의 인증 결과가 아니다.

동일 shell r_i=R에서는 col(E4) subset col(E9)여서 rank(X) <= 9. 서로 다른 깊이 표본에서는 rank13 회복이 가능하지만 principal angle이 작으면 수치적 분리는 불안정하다. 방법별 독립 자유 영점 지시행렬 F를 추가하면 전역 상수열이 col(F)에 속하므로, W로 가중한 설계의 projection (I-P_WF) W X에서 적어도 상수 절편 한 방향이 사라진다. 현재 데이터에서는 rank13 ->12.

관측오차 stress는 w_i=median(e_DMzp)/e_DMzp_i로 선언. 이 오차는 redshift의 오류가 아니므로 W가 완전한 joint likelihood whitening이라고 주장하지 않는다.

## R6–R7: 비판적 검증과 경량 연산

- Wolfram exact: HTT의 Q->O boost normal matrix identity 잔차 0; Fisher 단조감소 미분을 2x2 symbolic case에서 잔차 0으로 확인.
- SciPy sph_harm_y vs HEALPix libsharp alm2map_der1: map, dtheta, dphi/sin(theta)의 최대 잔차 10^-12 이하.
- 실제 SMICA 관측 하늘의 L=5 surrogate에 exact finite-boost thermodynamic pullback을 적용했을 때, 중앙차분 h=4e-4,2e-4,1e-4의 Jacobian 상대 잔차는 6.23e-7,1.56e-7,3.90e-8 (예상한 O(h^2) 수렴).
- 해당 exact-pullback 검산에는 양의 절대온도를 만족시키기 위해 인공적인 +1500 microK offset을 사용했다. 실제 측정한 T0가 아니다.
- 실제 가용 CF4 원본의 gzip SHA-256과 1PGC ID, 관측조건, method-family, 독립 거리계수 오차를 확인했다. 새로운 physical source first jet을 측정한 것은 아니다.
- 독립적인 native subagent 검증은 NOT_RUN: 현재 호스트에 agent-spawn 기능 노출되지 않음. 한 모델의 코드 검토를 다른 독립 심사자로 기록하지 않았다.

## R8–R9: 관측적 결론과 계산 계약

**Planck 조건부 실행.** 고정 reference |beta|=0.00123357 방향에 대한 추가 boost 접선의 ||J_L beta|| (microK):
- mask>0.5: L5 0.249173, L8 0.301678, L12 0.365444.
- mask>0.8: L5 0.249188, L8 0.302654, L12 0.379152.

||J||_F는 L12/L5에서 mask>0.5 기준 1.28027, mask>0.8 기준 1.30603. 이것과 주입 방향으로 제한된 ||J beta|| 증가율은 서로 다른 양이다.

저장한 240개 heldout simulated sky pair의 공분산을 사용하면 sqrt(beta^T F_beta(0) beta)는 0.015-0.020이다. 이는 source surrogate의 주입 민감도/조건부 산포 비율일 뿐, 물리 velocity 검출 significance, 실제 joint posterior 또는 p-value가 아니다. L12에서 250회의 pair-row bootstrap은 covariance-estimation Monte Carlo 민감도이고 같은 Planck 하늘을 독립 검출한 것이 아니다. ell6..12의 K는 등록한 두 mask에 대해 finite 행 rank32이나, 물리 고차 모드가 제한 없다는 no-go 주장은 하지 않는다.

**CF4 조건부 실행.** 38,053 groups 중 35,970개가 z_proxy in [0.01,0.1]. 전체 free rank13; 방법별 영점을 임의로 자유롭게 두면 projected rank12. diagonal eDM design weighting에서:
- 전체 smallest principal sine 0.413385, method-dipole squared overlap 0.282976.
- central-depth 2% 구간에서는 sine 0.00827748, full rank지만 거의 퇴화.
- upper-depth half에서는 sine 0.168322, method-dipole squared overlap 0.543501.

이것은 실제 관측자료의 방향과 거리 layout으로 **이론적 역산에 필요한 정보의 상대적 배치**를 분석한 것이다. 실제 가속도 A, expansion/shear, global tilt, H0 또는 FLRW departure 추론이 아니다.

## R10: 보존과 다음 실제 단계

현재 authoritative 결과는 results/cmb_processed_boost_v2, results/cf4_optical_design_v1 및 evidence/scientific_oracles.json. 최초 실행 v1은 귀속으로 오독될 수 있는 필드 이름을 사용하여 v2가 바로잡았으며 둘의 수치 계수는 일치한다.

다음 개발에서 물리적 CMB likelihood로 승격하려면 실제 compsep/beam/frequency 처리 및 모든 고차 source의 end-to-end response, 진짜 물리 null와 공유 오차 법칙이 필요하다. CF4의 실제 local optical inverse에는 절대 적색편이 절편, latent redshift-distance sampling과 방법별 공유 selection/calibration, 유한 광학거리 잔차·곡률 bound가 필요하다. 이는 향후 모델 개발의 실질적인 물리 입력이며, 현재 진행한 두 조건부 관측 분석의 실행 자체를 막지는 않는다.


## 추가 분석: 유한 NSIDE64 처리에서 고차 nuisance image의 구성적 확인

기존 R4–R9 유도에서 nuisance 행렬의 실제 finite-pixel image가
완전한 저차 관측계수 공간을 덮는지를 확인했다. 여기서

\[
K=P_{M,\,\ell=2:5}\,Y_{\ell=6:12}
\in\mathbb R^{32\times133},\qquad
J_\mathrm{surv}=(I-KK^+)J
\]

로 정의한다. 마스크, 일차 국소 boost의 방향 및 적합 기저는 위에서
선언한 것과 동일하다. 완전히 자유로운 실수 고차 계수를 갖는
이 선형 문제에서 rank(K)=32이면 col(K)=R^32이고 J_surv=0이다.

실제 보존된 Planck SMICA NSIDE64 공통 mask의 threshold 0.5와 0.8에서
SVD 및 pivoted QR로 rank(K)=32를 각각 확인했다. 최소/최대
특이값 비는 0.0062152931 및 0.0079168927이었다. 세 boost
열 전부에 대해 ||J-KK^+J||_F/||J||_F가 10^-14 이하였고,
기준속도에 대한 상쇄 벡터 a_*=-K^+J beta_ref를 구성했다.

mask 0.5, source L12: ||a_*||=5.60170 microK,
||J beta_ref + K a_*||=1.43e-15 microK.
mask 0.8, source L12: ||a_*||=4.57787 microK,
잔차 1.36e-15 microK. 이는 평균적으로 물리적으로 실현가능한
source 모형이라는 주장이 아니라, 지정한 harmonic basis의
최소 Euclidean-norm 상쇄 계수라는 의미이다.

결론: **이 유한 cache-stage OLS 연산자에서 전혀 제한되지 않은
ell6..12 source coefficients는 저차 boost tangent를 완전히 가릴
수 있다.** 이는 이전 연속 wide-mask 분석에서 남겨진 이산 랭크
확인 의무에 대한 직접 수치 증거다. 그러나 Planck beam/compsep
upstream transfer, 실제 high-l prior, 물질 운동학/전단 전달,
공동 covariance가 빠져 있어 새로운 보편적인 물리 no-go를
입증하지는 않는다. 경계/확률 모델로 제한한 nuisance는 위의
조건부 Fisher 계산으로 분석한다. 문헌상의 독창성 검토도
여전히 별도 의무다.

실제 SVD 및 QR, 잔차, source별 최소 norm 결과:
evidence/processed_nuisance_quotient.json.
재현 코드: scripts/verify_htt_processed_nuisance_quotient_20261015.py.
