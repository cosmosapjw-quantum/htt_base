# P6 K02 연구 결과: 실제 CF4 apparent STF의 물리적 수송 미식별성

2026-10-15 KST. 연구 브랜치 \`research/htt-k02-transfer-identification-20261015\`, 기준 \`f0125c27605a505efcb7647e1bed8bfd129cd8bd\`. 사용자가 원래 legacy HTT에서 추구한 \((x,F,\Pi,Q,G_F)\)와 1+3 \(\sigma_{ab},\omega_a,A_a,\beta_a\)의 관측가능성 질문을 유지하면서, 최신 source-conditioned CF4 Schur 정보, H01–H03 거리관측, 그리고 직전 K01 정확한 공변 국소 광자 수송을 결합했다.

## 1. 원본 이론과 관측량 사이의 빠진 물리학을 분리

\((-+++)\), \(\epsilon_{123}=+1\). 실제 K01에서 도출한 photon proper-congruence equation은 한 사건의 incoming ray에서
\[
-\frac{d\ln E}{dt_u}=H-A_an^a+\sigma_{ab}n^a n^b.
\]
\(n^a\)는 source를 향한 sky LOOK이며, propagation \(e^a=-n^a\). \(A_a,\sigma_{ab},H\)는 \(\mathrm s^{-1}\), normalized \(\Sigma=|\sigma|/H,\ |\sigma|=\sqrt{\sigma_{ab}\sigma^{ab}/2}\)는 무차원이다. Antisymmetric \(\omega_{ab}\)는 위 한 사건 에너지 수축에서 직접 소거되지만, 장시간의 방향/화면 수송 효과는 배제되지 않는다. 물질/복사/관측자 \(\beta\)도 별도 congruence 의존량이다.

반면 실제 CF4 \(\mu_i=\mathrm{DMzp}_i\), \(z_i=\mathrm{Vcmb}_i/c\), \(n_i^{\rm J2000}\)에서 출발한 observable은
\[
y_i=\mu_i-\mu_{\Lambda{\rm CDM}}(z_i)
\]
이며, \(\mu_{\Lambda{\rm CDM}}\)는 H0=74.6 km/s/Mpc, \(\Omega_m=.3153\)를 **데이터에 맞추지 않고 고정한 reference**다. 원래 H01/H02가 분석했던 \(H_{\rm eff}=cz/d_L\)과도 별개로 정의가 분명하다. \(y_i\)는 **한 사건의** \(-d\ln E/dt_u\)가 아니다. 그 둘 사이에는 실제 광선수송의 emitter/observer velocity, 선택함수, 거리지표, source time, curvature/lensing, calibration covariance가 필요하다.

구분을 유지하면서 CF4의 조건부 angular model을
\[
y_i=N_{i\alpha}\eta^\alpha-\frac5{\ln10}g(z_i)\,
 n_i^a(T_A)_{ab}n_i^b\,\gamma^A+\varepsilon_i,\quad A=1,\dots,5
\]
라고 **선언된 radial-response 가정** \(g(z)\)으로 적는다. 여기서 \(\gamma^A\)는 *apparent* STF coefficient이지 물리적 \(\sigma_{ab}/H\)가 아니다. \(N\)은 4방법 FP/OTHER/SN/TF별 intercept 및 log(z) slope(8), bulk velocity 3, angular dipole 3 = 14 nuisance columns. 고정 Gaussian working std는
\[
s_i=\sqrt{(\mathrm{eDMzp}_i)^2 + (0.15\,\mathrm{mag})^2+
  [250\,{\rm km/s}\,(\partial\mu/\partial v)_i]^2}
\]
이며, 이 대각 law는 실측된 cosmic correlated covariance나 survey selection law가 아니다.

## 2. 구성적 Schur/profile 미분과 수송 의존적 STF 식별성

\(B_g\)를 apparent STF response, \(Z\)를 nuisance, \(W=\mathrm{diag}(1/s_i^2)\)라 하면
\[
P_N=W-WZ(Z^\top WZ)^{-1}Z^\top W,\quad
F_g=B_g^\top P_N B_g,\quad
\hat\gamma_g=F_g^{-1}B_g^\top P_N y.
\]
기존 2026-10-15 cf4_schur_information.py의 QR-기반 \(O(Np^2)\) profile을 실제로 재사용하여 \(35,970\times35,970\) dense covariance나 projector를 생성하지 않는다. 전 35,970 CF4 그룹의 source bytes SHA는 86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c이고 group-ID checksum도 이전 PR255와 일치한다.

**아래 네 가지 \(g(z)\)는 실제 Bianchi 광선수송 해가 아니며**, 가능한 불확정 radial sensitivity를 보여주는 explicit source conditional 계산이다.

| declared g(z) | fitted apparent 5D STF norm | baseline STF cosine | nuisance-profiled min relative Fisher eigenvalue |
|---|---:|---:|---:|
| \(1\) | .03325774236 | 1 | .3715910955 |
| \(z/.05\) | .03139014852 | .9688397350 | .1875989564 |
| \(.05/z\) | .01600670596 | .8877476202 | .7049033012 |
| \((1+z)/1.05\) | .03362973448 | .9999412041 | .3593992279 |

\(g=1\)의 \(\hat\gamma=(-.0155720884,-.0178128286,.0081087686,.0201661170,.0085945460)\)는 기존 고정 연구 \`cf4_schur_loop8_20261015\` all-source coefficient와 정확한 source regression을 통과했다. 이 표의 STF norm/angle은 14 nuisance와 분산 가정을 고정했을 때의 *apparent* 추정량이다. \(F_g\) 고유값은 관측원 연산자 정보율이며, \(\sigma_{ab}\) 물리 posterior confidence 또는 likelihood odds가 아니다.

## 3. 전체 amplitude 미식별성: 정확한 모형 대칭

고정 shape의 실제 물리 수송 정규화 \(\lambda>0\)를 아직 구하지 않았다면, \(B_{\lambda g}=\lambda B_g\)이다. 같은 \(y,N,W\)를 사용하면
\[
\hat\gamma_{\lambda g}=\hat\gamma_g/\lambda,\qquad
{\rm Cov}_{\lambda g}={\rm Cov}_g/\lambda^2,\qquad
\lambda_j(F_{\lambda g},F_{0,\lambda g})=\lambda_j(F_g,F_{0,g}).
\]
이는 Wolfram 정확 대수로 검증하고, 실제 같은 CF4 데이터를 gain 0.1,1,10 아래 **다시 적합**해 검증했다. apparent STF norm은 각각 **.3325774236, .03325774236, .00332577424**로 정확히 \(1/\lambda\)를 따른다.

이 수송 정규화에 외부 제약이 없으면 물리적 \(\Sigma\) 진폭에 유한한 상한/신뢰구간을 부여할 수 없다. 물리적 부호, 공간방향, congruence가 확정된 것이 아니므로 실제 source에서 \(\Sigma\) 자체가 관측되었다는 주장은 보류한다. 고정 shape 및 **양의** 전역 gain을 가정할 때만 STF 계수벡터의 방향이 scale 변경에 불변이다. shape의 적색편이 의존성을 달리하면 방향도 바뀐다.

## 4. 독립적인 method-anisotropy counterexample

네 가지 거리측정 방법 각각에 *가상으로* 방향별 STF calibration 오차를 무제한 허용하는 모형에서는
\[
(B_g)_{iA}=\sum_{m\in\{\mathrm{FP,OTHER,SN,TF}\}}
{\bf1}_{m(i)=m}(B_g)_{iA}.
\]
따라서 global 5D STF response는 20개 method-STF nuisance의 column span에 완전히 속한다. 실제 35,970개 그룹에서 20개 method-local STF design rank=20, global STF projection residual relative **3.365906248e-16**, global STF residual rank=**0**, 정확한 pointwise B−Σ_m B_m 최대 잔차=0. 이것은 외부 계통오차를 가정 없이 모든 방향에 허용한다는 사실에서 나오는 **범위 한정 비식별성 구성적 반례**이지, 실제 CF4에 해당 오차가 존재함을 검출한 것이 아니다.

한편 기존 nuisance를 유지한 5×20 alias susceptibility Jacobian \(L=\partial\hat\gamma/\partial \alpha_{mA}\)를 실제 source에서 계산했다. 네 방법이 모두 동일한 angular modulus calibration \(\alpha_A\)를 가질 경우 \(g=1\)에서 정확히 \(\delta\hat\gamma_A=-\alpha_A/\kappa,\ \kappa=5/\ln10\)이다. 오직 illustrative amplitude \(\alpha=(.03,0,0,0,0)\,\mathrm{mag}\)라면 apparent 5D norm의 shift는 **0.01381551056**이다. 이는 0.03 mag가 **실제 관측되었다는 사실이 아니라**, unmeasured method-angular calibration의 충분조건부 변화율이다.

## 5. 물리적 identified set과 legacy 통계 연결

K01 one-event optical angular design에서는 \(H,A_3,\sigma_5\) rank=9, direct radial \(\omega_3\) rank=0; 새 CF4 modulus model의 \(\gamma_5\) rank=5는 매우 제한된 observational hypothesis 아래에서만 유지된다. 새로운 실제 source-free amplitude \(\lambda\)와 method-specific angular nuisance를 열면 physical \(\sigma/H\)는 source data alone으로 bounded identified interval이 아니다. \(\omega_a,A_a,\beta_a\)는 각각 nonradial response 및 물질/복사/관측자 congruence history가 필요하다. Apparent \(\|\gamma\|/3\) 또는 현재 conditional covariance를 물리 \(\Sigma=|\sigma|/H\) posterior라 하지 않는다.

원래 legacy \((x,F,\Pi,Q,G_F)\)는 동일한 물리 source posterior를 요구한다. CF4의 한 angular STF proxy로 signed \(x\)의 미관측 curvature/tilt/vorticity sector를 채우거나 단정적 \(\Pi(t)\)를 계산하지 않는다. 기존 Planck 2018 CMB 저차형태 및 MES eps2/3는 별도 **한 실제 CMB 하늘**이고 독립적인 CF4 물리 shear 정보로 중복 곱하지 않는다. K02는 observational *identification-bound* 방법론 진전이지 새로운 beyond-FLRW detection이 아니다.

## 6. 문헌 대조, 코드, DAG

출판상 중복 위험: Boubel et al., JCAP 03 (2025) 066, doi:10.1088/1475-7516/2025/03/066, 이미 CF4 directional H0 dipole과 bulk flow/cosmological anisotropy 구분을 실측·simulation으로 비교했고; Whitford, Howlett & Davis MNRAS (2023), doi:10.1093/mnras/stad2764는 CF4 velocity estimator와 geometry-dependent bias/covariance 문제를 정량화했다. Courtois et al. A&A (2023), doi:10.1051/0004-6361/202245331은 CF4 3D velocity/density reconstructions를 제공한다. 새로운 물리적 shear claim은 이러한 연구를 넘어서는 proper-time/emission-source response 및 independent observational validation 없이는 제출 불가다.

실제 구현:
- htt/obsstat/cf4_physical_transfer_identification.py: dimensionless declared g(z), 5D source Schur, exact unknown normalization counterexample, method-specific angular systematic nullspace and alias Jacobian.
- scripts/run_htt_cf4_k02_transfer_identification.py: source pin + previous PR255/K01/H01 regression, real 4 shape fits, separate exact gain re-fits, method angular calibration full rank null witness and fixed-source injection.
- tests/obsstat/test_cf4_physical_transfer_identification.py and tests/obsstat/test_htt_k02_source_acceptance.py.
- Canonical results: docs/research_program/observational_publication_20261015/results/K02_cf4_transfer_uncertain_v1/{result.json,cf4_transfer_conditional_stf.npz,cf4_physical_transfer_unknown_sensitivity.png,REPORT_KO.md}. New independent REPLAY and source SHA verification to be included in receipt.

K02 acceptance is **scoped identified-space/unknown-sector report**, not physical cosmological shear measurement. K02 may be marked completed_scoped if code/source replay and optical comparison tests pass. K03 remains external-input-blocked for nonradial physical vorticity/acceleration/tilt observations; K04 remains blocked until H04 true CF4 selection and physical source law. P6 manuscript completion remains 0/1; all six papers submission gates remain 0/6. User original source checkout has pre-existing 57 uncommitted paths; preserve.

Native subagents unavailable in current host inventory (NOT_RUN); local Codex NOT_USED. This is local Ubuntu numeric code execution with OpenBLAS threads pinned 2.
