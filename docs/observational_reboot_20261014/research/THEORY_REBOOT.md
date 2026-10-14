# THEORY_REBOOT — dipole·local boost·global tilt·Bianchi 식별의 구성적 재시작
작성: 2026-10-14. 범위: R2–R5 및 R9. 아래 계산은 직접 유도이며 관측 fit/p 재실행이 아니다. metric \((- ,+,+,+)\), \(u^au_a=-1\), \(U^a=cu^a\), \(n=-e\), \(\beta=v/c\), rapidity \(\chi=\operatorname{atanh}|\beta|\). 단위·epoch·frame·sky support를 모든 객체에 붙인다.

## 1. 세 dipole와 두 velocity를 분리하는 실제 모형

절대 thermodynamic temperature의 dipole coefficient를 \(d_a\,[K]\), \(\Delta_a=d_a/T_0\)라 둔다. R은 등록된 복사 기준계, M은 물질 congruence, O는 관측자다. \(\beta_L=\beta_{RO}\)는 O의 endpoint 속도이고 \(\beta_G(z)=\beta_{RM}(z)\)는 M의 물질 tilt 이력이다. 일차에서 \(\beta_{RO}=\beta_{RM}+\beta_{MO}+O(\beta^2)\); 유한 boost에는 Lorentz velocity composition과 tetrad orientation을 사용한다.

\[
d^{abs}=T_0\beta_L+d^{int}+d^{late}+d^{fg/cal}+O(\beta^2T_0,\beta\,d^{int}).
\]
이는 \(\beta_G\)를 \(\beta_L\)와 동일시하지 않는 forward bookkeeping이다. 등록된 SMICA 처리 연산자 \(M\)에 대해
\[
d^{prod}=\Pi_1M[T^{abs}]+d^{res}.
\]
큰 dipole 제거, mask와 harmonic mixing, calibration이 \(M\) 안에 들어간다. 따라서 제품 residual dipole 하나를 위 \(d^{abs}\)로 복원하지 않는다. 공개 제품에는 절대 \(T_0\)·orbital/solar subtraction provenance와 bandpass 처리가 별도로 필요하다.

[PS06 Ferreira–Quartin, Eq.(1)]의 검정 가능한 벡터 모형은
\[
\Delta_1=\beta_L+\Delta_{int},\quad
\beta_D=\beta_L+(1+\alpha_{NG})\Delta_{int},\quad
\beta_A=\beta_L+L_d.
\]
여기서 \(\beta_D,\beta_A\)는 Doppler/aberration estimator response이고 \(L_d\)는 dipolar lensing이다. 자유로운 \(\Delta_{int},L_d,\alpha_{NG}\)에선 9개 observables에 10개 unknowns이므로 특정 모델 또는 외부 lensing 정보가 필요하다. 이는 작은 residual dipole가 global tilt를 측정한다는 모형이 아니다. 해당 문헌의 \(3.7\,mK\) 상한은 표준 dipolar-lensing 가정에 조건부인 intrinsic CMB dipole 결과다.

[PS05 Roldan et al., §§3–5]는 intrinsic potential이 Doppler/aberration-like coupling을 만들 수 있음을 보인다. Eq.(4.19)의 초기조건 항은 \(T_{\mathrm{Dopp,IC}}=-(5/3)(a_{NL}-1)\phi_d\Theta\). single-field에 가까운 \(a_{NL}\simeq1\)에서 Doppler-like degeneracy를 얻지만 논문은 유도를 large-scale·matter-domination 범위로 한정한다. 그 식을 모든 고차 \(\ell\), 모든 Bianchi, 모든 matter source의 분류 정리로 확장하지 않는다. Aberration은 dipolar-lensing radial profile에 민감하므로 별도 반응 채널로 유지한다.

## 2. endpoint Lorentz response의 직접 유도

Doppler weight 1에 대해 [PS04 Dai–Chluba, Eqs.(2)–(4)]
\[
T'(\tilde n)=\frac{T(n(\tilde n))}{\gamma(1-\beta\cdot\tilde n)},\quad
n=\tilde n-\beta+(\beta\cdot\tilde n)\tilde n+O(\beta^2).
\]
Taylor 전개하면
\[
\delta_\beta T=(\beta\cdot n)T-[\beta-(\beta\cdot n)n]\cdot\nabla_{S^2}T.
\]
\(T=T_0\)이면 \(\delta T=T_0\beta\cdot n\), \(T=Q_{ab}n^an^b\)이면
\[
\delta T_2=3(\beta\cdot n)Q_{ab}n^an^b-2(Q\beta)\cdot n
=3\beta_{\langle a}Q_{bc\rangle}n^an^bn^c-\frac45(Q\beta)\cdot n.
\]
마지막 등호는 \(n_an_bn_c=n_{\langle abc\rangle}+\frac15(\delta_{ab}n_c+\delta_{ac}n_b+\delta_{bc}n_a)\)에서 온다. 따라서 고정 quadrupole의 octupole response는 \(B_Q\beta=3\beta_{\langle a}Q_{bc\rangle}\)이며 dipole response도 동시에 생긴다. 일반 temperature와 mask에선 각각 \(\ell\pm1\) coupling과 처리 leakage를 모두 포함해야 한다.

완전 Frobenius 내적에서
\[
B_Q^*O=3(O:Q),\quad B_Q^*B_Q=3M_Q,\quad
M_Q=(Q:Q)I+\frac65Q^2.
\]
따라서 \(\hat\beta_{LS}=M_Q^{-1}(O:Q)\), \(Q\ne0\)에서 \(M_Q\succ0\).
trace-free eigenvalues \(\lambda_i\)에 \(I_2=\sum\lambda_i^2\)라 두면 \(\lambda_{\max}^2\le2I_2/3\), 최소 제곱을 x, 최대 제곱을 z라 두고 세 eigenvalue의 합이 0이라는 조건을 쓰면 \(3z-5x\le5I_2/3\). 이에 \((I_2+6z/5)/(I_2+6x/5)\le5/3\). 즉 잘 조건화된 inverse다. 그러나 \(O= B_Q\beta+O^{int}\)에서 \(O^{int}\)가 자유로우면 어떤 \(\beta\)에도 residual을 지정할 수 있으므로 이 대수 좌표만으로 실제 velocity를 추정하지 않는다.

실행 확인: DERIVATION_CHECKS.json에서 Gram residual \(3.85\times10^{-15}\), polynomial decomposition residual \(5.33\times10^{-15}\); 합성 임의 Q의 condition=1.66418. 이는 observation 검증이 아닌 algebra sanity check다. full-sky \(d=1\)의 E/B 비혼합 [PS04 §IV]과 cut-sky leakage를 분리한다.

## 3. nuisance quotient와 local/global 식별

처리된 관측을 선형화하여
\[
y=\mu_0+J_L\beta_L+J_Gg+N\nu+\epsilon,\quad \epsilon\sim(0,C)
\]
로 둔다. \(g\)는 등록된 tilt-history basis의 coefficient다. C가 positive-definite인 지지공간의 whitener W와 \(A_N=WN\)에
\[
P_N^\perp=I-A_NA_N^+,\quad A_L=P_N^\perp WJ_L,\quad A_G=P_N^\perp WJ_G.
\]
nuisance를 제거한 반응 차원은
\[
\operatorname{rank}(P_N^\perp WJ)=\operatorname{rank}[WN,WJ]-\operatorname{rank}(WN).
\]
증명: \(\operatorname{Im}[WN,WJ]\)를 nuisance image와 그 직교 여공간으로 분해하면 rank가 두 image 차원의 합이다. whitening이 invertible이면 unweighted quotient의 rank와 같다. 고차 source block \(K_{hi}\)를 nuisance에 넣을 때 image 증가에 따라 surviving image의 차원은 비증가한다. 다만 실제 finite-pixel \(K_{hi}\)를 계산하지 않고 연속 mask rank 결과를 승계하지 않는다.

같은 방향 response R을 두 속도에 복제한 [R,R]는 \((h,-h)\)를 kernel에 포함한다. 두 shell의 이상적 vector feature
\[
y_1=\beta_L+g_1\beta_G,\qquad y_2=\beta_L+g_2\beta_G
\]
이면 determinant가 \((g_2-g_1)^3\)인 6×6 block matrix가 생겨 \(g_1\ne g_2\)에서 full rank 6다. \(g_1=g_2\)면 rank 3. 실제로 \(g_1=0.5,g_2=2\) 합성 rank=6을 실행 확인했다. nuisance projection, survey 창과 covariance를 포함한 rank는 이 예에서 자동 따라오지 않는다. 두 shell이 있다는 명목이나 normalization으로 충분하지 않다.

global의 conditional 정보는
\[
I_{G|L}=A_G^T(I-A_LA_L^+)A_G.
\]
이 행렬의 작은 eigenvalues, principal angles와 response error 대비 singular gap을 보고한다. rank는 local linearized·interior 식별 진단이다. 제약 경계의 nonlinear uniqueness와 안정성은 따로 판정한다. 누적 response 오차 \(\|\Delta A\|_2\le\varepsilon_A\)면 \(\sigma_k(A_{true})\ge\sigma_k(A_{obs})-\varepsilon_A\), 양의 gap이 남는 방향만 certified survivor로 유지한다. finite grid의 최대는 전역 인증이 아니다.

radial velocity의 affine 전개 \(v(x)=b+Ax,\ x=rn\)에
\[
v_r=n^Tb+r\,\mathrm{tr}A/3+r\,n^TA_{\mathrm{STF}}n,\qquad n^TA_{\mathrm{skew}}n=0.
\]
따라서 full directional/depth design일 때 bulk3+expansion1+shear5는 가능하지만 solid rotation3은 이 관측에 사라진다. 이 정확한 반응 kernel은 해당 affine·radial 모형의 결과다. 모든 동역학적 와도/원격 채널에 대한 strong no-go가 아니다.

## 4. 공유 sky를 보존한 검정

실험 단위는 sky seed 하나의 전체 묶음 \(Z_i=(y_{SMICA},y_{NILC},y_{Commander},y_{SEVEM},y_{\mathrm{splits}},y_{\mathrm{depth}},\ldots)_i\)다. 지도/마스크/깊이를 각각 독립 복제로 세지 않는다. \(r=y_2-Ky_1\)의 covariance는
\[
V=C_{22}+KC_{11}K^T-C_{21}K^T-KC_{12}.
\]
동일한 scalar sky를 두 번 관측하면 \(C_{11}=C_{22}=C_{12}=1,K=1\)에서 true V=0, cross terms를 생략하면 V=2다. singular law의 covariance nullspace에 놓인 residual은 deterministic support condition으로 검사한다. ridge로 없애면 모델이 달라진다.

등록된 null에서 관측과 N개 sky bundles가 교환가능하고 전체 feature/fit/selection/score 사상이 row permutation equivariant이면
\[
p=\frac{1+\sum_{i=1}^N1\{S_i\ge S_0\}}{N+1}
\]
는 superuniform이다. 증명: ties 없을 때 관측 label의 rank는 1,…,N+1 위 균등; ties에서 upper-tail inclusive rank는 더 보수적이다. 핵심은 joint exchangeability이며 독립적인 지도 채널은 필요하지 않다. 반면 유한 300 noise realization의 cyclic 재사용은 reference rows의 iid나 교환가능성을 자동 제공하지 않는다.

실행 계약:
1. 제품/hash/units/mask/beam/fit low modes, dipole provenance, null·alternative·statistic·tail·N·seed·selection을 분석 전 고정한다.
2. 같은 seed의 모든 제품을 같은 처리 경로로 전파한다. 관측 한 행만 adaptive 선택하거나 data-only nuisance fit을 고정한 채 reference를 처리하지 않는다. 사전 독립 training과 고정 score 또는 모든 pseudo-observation의 같은 refit 규칙을 택한다.
3. 여러 mask/depth/statistic 중 선택할 경우 score \(S_i=\max_{j\in\mathcal J}T_j(Z_i)\)를 등록하고 동일 scan을 각 pseudo-observation에서 수행한다. 별도 marginal p들을 무조건 곱하지 않는다. 유효한 marginal들만 준비됐다면 \(\sum_j\alpha_j\le\alpha\) Bonferroni가 의존을 허용한다.
4. pointwise null \(H_{0,\eta}\)의 정확한 p를 먼저 구성한다. composite null은 \(\sup_{\eta\in H_0}p_\eta\)가 보수적이지만 실제 supremum 계산이 필요하다. \(\eta\)를 한 번 plug-in한 parametric bootstrap은 자동 exact가 아니며 synthetic coverage campaign으로 범위를 확인한다.
5. 계산 score enclosure \(L_i\le S_i\le U_i\)가 있으면
\[
p^-=\frac{1+\sum1\{L_i\ge U_0\}}{N+1},\quad
p^+=\frac{1+\sum1\{U_i\ge L_0\}}{N+1}.
\]
\(p^+\le\alpha\)만 certified rejection이다. \(p^-\)는 p-value가 아니다. 고정 통계량의 확실한 enclosure를 좁히는 수치 중단과 N·statistic을 계속 선택하는 통계 optional stopping은 다르다.
6. 알려진 C에 대한 Gaussian \(\chi^2_{\mathrm{rank}C}\) support inversion, 추정-C/cluster empirical law, PPC, posterior exceedance를 서로 다른 output type으로 반환한다. Hartlap correction은 tail calibration이 아니다.
7. 독립 sky B개를 만든다는 계약의 p floor는 \(1/(B+1)\)이다. 999 sky의 곱하기 noise reuse를 N=999×300 independent skies로 표기하지 않는다.

## 5. Bianchi 경로를 열린 채 유지하는 조건부 사상

family f별로 background/matter/IC/visibility/electron-frame collision/anisotropic transport를 묶은 \(\eta_f\)와 registered tangent/parameter \(\theta_f\)를 정한다.
\[
a_f^{T,E,B}(\theta_f,\xi)=a_f^{det}(\theta_f)+a_f^{stoch}(\theta_f,\xi),\quad
y=M_{obs}\mathcal B_{\beta_L}[a_f]+N\nu+\epsilon.
\]
global tilt는 \(\eta_f\)의 유체·collision·source·transport evolution에 들어가고 local boost는 endpoint \(\mathcal B\)다. Bianchi covariance는 일반적으로 \((\ell m,\ell'm')\) 비대각이므로 \(C_\ell\)-only 동일성은 같은 모델 law라는 근거가 아니다.

먼저 native atlas 없이 가능한 transfer-conditional analysis를 한다: 문헌 template 또는 제한된 synthetic \(\mathcal T_{\eta}\)를 정확히 표시하고 nuisance quotient·rank·inject/recover·noise sensitivity를 실행한다. 이 결과는 그 transfer의 분리 가능성/검정력을 보여준다. 현재 family identification claim에는 native harmonic/covariance atlas의 source·frame·IC·cutoff·error 인증이 더 필요하다.

이상적 restricted LRS Bianchi-I에서 \(a_\perp=ae^{-b},a_\parallel=ae^{2b}\), \(S=\dot b\,[s^{-1}]\), \(\sigma_{\hat i\hat j}=\mathrm{diag}(-S,-S,2S)\). 초기 b=0의 collisionless Planck radiation은
\[
T_n(t,\mu)=\frac{T_i a_i}{a}\big[e^{-2b}(1-\mu^2)+e^{4b}\mu^2\big]^{-1/2}
=\bar T[1+b(1-3\mu^2)+O(b^2)].
\]
그래서 \(\delta T=-2\bar T\,bP_2(\mu)+O(b^2)\), \(b(t)=\int Sdt\). quadrupole은 이 shear history에 반응하며 순간 shear와 동일하지 않다. normal frame의 coherent odd multipole은 \(\mu\mapsto-\mu\) 대칭으로 사라지지만 endpoint boost는 odd multipole을 만들 수 있다. 반대 stream의 flux 0과 이차 stress 비영도 동시에 가능하다. 이는 유용한 제한 benchmark이고 일반 cosmological last scattering·reionization·perturbation template은 아니다.

[PS07 Saadeh et al.]는 near-isotropic homogeneous flat/open family의 scalar/vector/regular-tensor/irregular-tensor modes와 T+polarization likelihood를 실제 결합했다. closed IX와 arbitrary matter stress·모든 family를 포함한 검출 정리로 사용하지 않는다. 그 vorticity upper limit를 무관한 모형의 independent observation으로 반복 넣지 않는다. \(\ln B\)는 prior와 full likelihood에 묶여 있고 MES ceiling은 data를 다시 독립 likelihood로 복제하는 항이 아니다.

family f,g의 관측 법칙이 native atlas 위에서 동일하면, normalized inactive parameter의 적분은 1이어서 이름/parameter count만으로 evidence 차이가 생기지 않는다. 반대로 \(\Delta\mu,\Delta C\)가 nuisance quotient 밖에 남으면 실제 model competition을 계산한다. 현 단계는 조건부 반응 구성과 native-atlas 의무를 남긴다. 새로운 strong no-go·최적성·novelty claim은 없다.

## 6. 구현으로 넘기는 최소 계약

각 response provider는 {source_commit, family, matter, frame, epoch, units, sky_support, parameter_order, output_layout, forward_or_endpoint, Jacobian, covariance, nuisance, validity_domain, remainder_bound, native_or_transfer_conditional}를 반환한다. source template 없는 물리 좌표는 zero가 아니라 unavailable이다.

calibrator는 {experiment_unit: sky_bundle, null_law, nuisance_fit_rule, selection_rule, exchangeability_evidence, score_tail, fixed_B, ties: inclusive, p/p_enclosure, empirical_vs_certified, MC_resolution}을 반환한다. figure에는 의미가 다른 PPC·empirical rank·posterior exceedance를 같은 p 범례로 합치지 않는다.

다음 실행점: historical K1의 정확한 score·pool dependence를 재현한 뒤 새 frozen statistic으로 matched whole-sky bundles를 생성하고 synthetic coverage와 observational conditional p를 분리해 낸다. 이어 native local/global J와 T/E/B atlas로 위 rank, likelihood·model comparison을 실제 채운다.

