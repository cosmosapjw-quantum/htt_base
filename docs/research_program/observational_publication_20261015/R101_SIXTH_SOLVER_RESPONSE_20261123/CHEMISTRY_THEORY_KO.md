# R101 고유시간 화학 반응망과 방향별 Thomson 광학깊이

R100의 `_opacity_per_efold`는 주어진 스칼라 이력에서 $x_e$를 보간한다. 이번 구현은 명시적으로 공급한 유한 화학 반응률에서 $x_e$, 셀별 Thomson 광학깊이, 마지막 산란의 구간 확률과 이들의 비시간 모수 방향미분을 계산한다. 중간상태를 보존하므로 지연 채널과 그 초기 점유도 다룬다. 아래의 식은 **derived**, 이산 전파와 열 개 시험은 **implementation-verified**다.

## 보존류와 두 시계

공간적으로 균일한 class A 우주에서 수소 핵류가 보존되고 화학 반응계와 산란 전자가 벌크 속도를 공유한다고 가정한다. 부호는 $(-,+,+,+)$이며 $N=\ln a$, $dN/dt_n=H_n>0$, $u_b=\Gamma(n+\beta^i e_i)$, $\beta=v_b/c$다. 밀도는 $n_{H,\mathrm{rest}}\Gamma a^3=\mathcal N_H$를 만족한다. 셀마다 고정된 proper-time 열 생성자 $R$의 단위는 $\mathrm{s}^{-1}$이다. 비대각 원소가 음이 아니고 $\mathbf 1^TR=0$이다. $p$는 정규화한 유한 상태 점유, $y$는 각 상태의 수소 핵당 자유전자 수다. 외부의 포획·재결합·이온화율을 $R$에 넣을 수 있다. 비선형 반응기에서 추출한 이력 의존률은 그 반응기에서 총미분도 공급해야 한다.

$$
\frac{dN}{d\tau_b}=\Gamma H_n,\qquad
\frac{dp}{dN}=A p,\qquad A=\frac{R}{\Gamma H_n},\qquad x_e=y^Tp .
$$

정규 직교 tetrad의 **광자 진행 방향**을 $\hat n$으로 정하면 $-u_b\cdot k/E_n=\Gamma(1-\beta\cdot\hat n)$이다. 전자 proper density와 이 인자를 곱하면

$$
\alpha_N=\frac{\sigma_Tc\,\mathcal N_H}{H_n}
 e^{-3N}(1-\beta\cdot\hat n)y^Tp
$$

를 얻는다. $\sigma_T[\mathrm{m^2}],c[\mathrm{m/s}],\mathcal N_H[\mathrm{m^{-3}}],H_n[\mathrm{s^{-1}}]$이므로 $\alpha_N$는 무차원이다. 기하학적 $\Gamma$의 상쇄 뒤에도 $p$에는 proper-time 반응 속도가 남는다. $H_n=0$이나 $N$의 방향 반전은 이 좌표의 정의역 밖이다. 시계는 셀 내 모든 미시상태에 공통이다. 상태에 의존하는 다른 속도 $ds/dt=v_i>0$를 사용할 경우 해당 열 생성자는 $R\,\mathrm{diag}(1/v_i)$다.

## 보존적 전파와 민감도

폭 $h$인 셀에서 $A,y,H_n,\beta,\hat n$를 고정한다. 밀도의 $e^{-3N}$은 셀 안에서 그대로 적분한다. 필요한 두 행렬함수는

$$
P_h=e^{hA},\qquad w_h=\int_0^h e^{-3u}y^T e^{uA}\,du .
$$

셀 $j$에서 $p_{j+1}=P_hp_j$, $\Delta\kappa_j=f_j w_h p_j$이고 $f_j=\sigma_Tc\mathcal N_H e^{-3N_j}(1-\beta_j\cdot\hat n_j)/H_{n,j}$이다. $A$에 영모드나 Jordan 블록이 있어도 성립한다. 짧은 구간에서 하삼각 블록 생성자 $\left(\begin{smallmatrix}A-3I&0\\y^T&0\end{smallmatrix}\right)$의 지수로 $e^{-3h}P_h,w_h$를 얻고 다음 합성법으로 원래 폭을 복원한다.

$$
P_{2h}=P_h^2,\qquad w_{2h}=w_h+e^{-3h}w_hP_h .
$$

확률합의 부동소수 오차가 반복 제곱에서 커지는 것을 막기 위해 매 합성 단계마다 열별로 정규화하고 동일 연산의 미분을 적용한다. 초기 짧은 구간은 $3h$와 최대 이탈률에 $h$를 곱한 값이 1 이하가 되게 선택한다. $e^{-3h}$는 실제 구간 폭으로 다시 평가한다. 셀당 비용은 $k$개 화학상태에 대해 $O(k^3[1+\log_2(1+\max(3,\max_i(-A_{ii}))\Delta N)])$, 작업 메모리는 $O(k^2)$다.

모수 $\theta$는 진화 좌표와 독립이다. $N_j$와 관측자를 고정한 방향미분에서

$$
\dot A=\frac{\dot R}{\Gamma H_n}+
A\left[-\Gamma^2\beta\cdot\dot\beta-\dot H_n/H_n\right],\qquad
\dot p_{j+1}=\dot P_h p_j+P_h\dot p_j .
$$

초기 상태, 원자율, 상태별 전자 수, $H_n,\beta,\hat n,\mathcal N_H$의 변화를 전달한다. $\mathbf1^T\dot p_0=0,\mathbf1^T\dot R=0,\hat n\cdot\dot{\hat n}=0$이다. 미분행렬은 음의 성분을 가질 수 있다. 관측자의 깊이 경계조건 $\kappa_M=0$에서 $\kappa_j=\sum_{\ell\ge j}\Delta\kappa_\ell$이고

$$
v_j=e^{-\kappa_{j+1}}(1-e^{-\Delta\kappa_j}),\quad
\dot v_j=e^{-\kappa_{j+1}}
\big\{e^{-\Delta\kappa_j}\Delta\dot\kappa_j-(1-e^{-\Delta\kappa_j})\dot\kappa_{j+1}\big\}.
$$

따라서 $\sum_j v_j=1-e^{-\kappa_0}$다. 셀 창 자체가 움직이면 경계에 Leibniz 항이 추가된다.

화학 반응망의 Metzler·열보존 전파는 양성과 질량을 유지한다. 구간 고정 생성자의 지연 중간상태를 정확히 소거하면 $Be^{D u}C$ 꼴의 MZ 기억과 $Be^{D u}p_{\rm hidden}(0)$ 초기힘이 생긴다. 코드에서는 이 두 항을 원래 양의 보조상태에 운반한다. 셀들의 $R$가 달라지면 실제 순서로 합성한다. 반복률 $\lambda$의 두 단계 채널에서 흡수된 분기는 $b[1-e^{-\lambda \tau}(1+\lambda\tau)]$가 되며, 후속 셀에서 재이온화할 수 있다. 여기서 분기 확률 $b$는 시험용 입력이다.

## 원 시계의 복구

BASS commit `ee298e24a6bac85bb11a81393f37499a8b0ddbe3`의 `research/typeii_native_hyrec_expansion_20261102/generate_typeii_H_grid.py`는 $\Delta N=\ln[(1+1700)/(1+z_{\mathrm{mean}})]$에서 $q=N'_1/N_1+4\Sigma_+$, $(\ln H)'=-(1+q)$를 적분한다. 생긴 H2248은 $z\le1700$에서 FLRW 기준점에 정규화된 normal-frame $H_n$이며, $z>1700$에서는 원 FLRW Hubble이다. 생성기 SHA-256은 `b7c2a7d63dd731b96ba72df6c87a2ba6d26f090ca0c438cbfe46f5a5467c48f4`, 출력은 `09f09528f845dbef4df71ed0dfb2a165f65a8920c2055dc2f66945a665a3d4d6`이다. 같은 commit의 `run_native_typeii_proper_current.py`는 $\Gamma(1700)/\Gamma(z)$를 수소 proper 밀도에만 곱한다. `history.c`의 열두 군데와 `helium.c`의 네 군데에서 밀도 표현을 바꾸며, 기존 H2248을 C 이력함수에 그대로 공급한다.

이로써 과거 산출물의 H 시계는 판별되었다. `hydrogen.c`의 SWIFT Lyα 유효율에는 $H/n_H$, 다광자 빈의 $\Delta\tau$에는 $n_H/H$, 최종 물질 $dx/d\ln a$에는 proper 반응원의 $1/H$가 들어간다. `helium.c`에도 선 탈출과 최종 분모 양쪽 사용처가 있다. 따라서 과거 H+density 이력의 조건은 명시할 수 있으며, 실제 tilted 화학과 방사선장에 맞게 확장하려면 물질시계와 방사선 주파수 drift를 별도 전달해야 한다. 이 구현은 공급된 화학률을 변환하는 측면을 해결했다. EMLA 계수와 ALI 방사선장, 방향별 광자장 및 patchy REI의 피드백은 해당 물리 모듈에서 얻어야 한다.

## 검산과 사용 범위

- 별도 적분변수 $\tau_b$의 DOP853 해와 점유 및 깊이를 비교했다.
- R100과 같은 `compute_tau_dot_conformal_Mpc` × $d\chi/dN$의 FLRW 구적값을 재현했다.
- 반복률 REC 분기와 후속 REI, 구간 광학깊이 및 투과율의 합, 물질시계–opacity 분리, 고정 셀 분할 불변성, $x_e=0$, 얇은 빈, 정의역 오류를 시험했다.
- 7개 입력을 동시에 교란한 중심차분으로 다섯 출력의 방향미분을 비교했다. $10^{15}$ transitions/e-fold인 두 상태의 정확 해로 정상상태 극한과 그 도함수를 따로 확인했다.
- 매끄러운 입력률과 기하량을 8/16/32개 셀의 중점에서 고정한 근사에서 2차 수렴을 관측했다. 비연속 이벤트는 명시적인 셀 경계에 둔다.
- 모듈 `bass.recombination.clocked_chemistry`, 함수 `evolve_clocked_chemistry`, 출력 `history.delta_optical_depth`와 `history.tangent.delta_optical_depth`이다. 단일 광자 방향의 $\Delta\kappa$를 공통 각도 충돌계수로 사용하는 합성 검산은 $\beta=0$에서 가능하다. 일반 tilt에서 각도별 scatter-in 재분배에는 별도의 frame transform이 필요하다.

소스 식별자는 `CHEMISTRY_EVIDENCE.json`에 있다. 원자 계수와 우주론적 상태는 Ali-Haïmoud & Hirata (2010), *Ultrafast effective multi-level atom method for primordial hydrogen recombination*, [arXiv:1006.1355](https://arxiv.org/abs/1006.1355), Lee & Ali-Haïmoud (2020), *HYREC-2*, [arXiv:2007.14114](https://arxiv.org/abs/2007.14114)를 참고했다. 행렬지수의 방향미분은 Al-Mohy & Higham (2009), [DOI 10.1137/080716426](https://doi.org/10.1137/080716426)을 따른다.
