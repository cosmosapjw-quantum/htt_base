# R98 네 번째 연구 사이클 · Bianchi 시간 의존 배경과 편광 수송

**판정.** 부피척도 (a=1/1601)에 지정한 제약식 적합 초기값에서 (a=1)까지 Einstein–Euler 궤적을 직접 풀었다. 각 시각의 전단·공간접속·팽창률로 같은 시각의 복사 소스, 각방향 수송, 광학깊이를 구성했다. FLRW, I, V, VII_h (h=1/4), VI_h (h=−1/9)의 결과를 보존했다. 구현 검증 범위는 공간적으로 균질한 시험 복사장, 정상계 정지 전자, 지정된 이온화 이력의 선형 Thomson 충돌이다. 측정된 Bianchi 성분, 가족 식별, 완전한 Einstein–Boltzmann 해 및 SQ-NATIVE 판정은 열려 있다.

## R1–R3 · 문제와 기존 해의 경계

R1. R97의 `_family_rescaled_trajectory_history`는 제한된 R49 궤적의 마지막 점에서 기하량을 정규화했다. `evolve_coupled_m_system`은 이 기하 연산자를 고정하고 임의의 적색편이 전단 감쇠를 곱한다. 여기서는 “동일한 초기값·전단 소스·전자 밀도·시간 간격에서 각방향 연산자의 이력만 고정하면 최종 부호 있는 계수는 얼마나 바뀌는가?”를 계산한다. 응답은 다섯 조건부 초기값의 계산량이다.

R2. Pontzen–Challinor의 식 (5)는 대칭 공간의 Lie 대수와 Jacobi 관계를, §3과 식 (44)–(45)는 적색이동 소스와 방향 이류를, 식 (55)–(56)는 Thomson 사중극 혼합 및 전자 쌍극자를 준다. 이 논문의 우주론적 위계는 FRW 극한을 가지며 재결합까지 비등방성이 작은 계열에 대한 1차식이다. VI_h 계산은 R49 접속에 대한 별도 초기값 계산이다. 원 논문을 VI_h의 일반 정리로 연장하지 않는다. H 원자 화학 비교는 Lee–Ali-Haïmoud의 HyRec-2 표 및 종래 유효 수소 원자 방정식의 적용 대상을 구별한다. [Pontzen & Challinor](https://arxiv.org/html/0706.2075v2) · [HyRec-2](https://arxiv.org/abs/2007.14114) · [Seager, Sasselov & Scott](https://arxiv.org/abs/astro-ph/9912182) · [AniLoS/AniCLASS의 near-isotropy 비교 대상](https://arxiv.org/abs/2506.07786).

| 기존 원본·위치 | 복원한 내용과 이번 사용 |
|---|---|
| `legacy/bass_htt_mio_github_ready_current/src/bass/PR13AG_projected_multipole_solver_restoration.py` | 75–105행의 synthetic \gamma/shear와 유한 L 수렴 코드 확인. SHA-256 `2d2678fe868138e7f06dce4df9cffa1ade10519bcf26331582d7505d05e64680`. 유한 위계/수렴 비교의 선행 구현으로 보존. |
| `htt/bass/background/general_tilted_evolution.py`, `tilted_bianchi_state.py` | 실제 양의 H, 전체 전단/구조상수, 종별 정상계 에너지·운동량, Jacobi/Hamiltonian/Codazzi와 공형시계. 초기 H는 전체 정상계 에너지로 결정. |
| `htt/bass/transport/general_bianchi_transfer.py` | 4D 역방향 null geodesic/Sachs RK4와 spin harmonics. 별도 각광선 에너지로 충돌 없는 T를 대조. |
| R95 / R96 / R97-REM | HyRec-2 CSV, tanh 재이온화, 전단 사중극 변환, exact full all-m Galerkin Liouville 연산자와 양의 T–E 비대각 Thomson 원소 재사용. R95의 FLRW 팽창 시계는 R49의 H(N)으로 교체. |
| `../rec_bianchi/research/rec_history_clock_r6_20261014/code/clock_compare.py` | `NativeSeries.bracket`, `exact_clock_split`의 동일 부피시계/동일 고유시계 분리와 외삽 차단을 확인했다. 이번 비교는 동일 N 및 동일 소스다. SHA-256 `b7025bf924ab3bba6c151efe87ee45906156c405eae29ac0e107ecf9ed7eb6fc`. |
| `../rec_bianchi/src/full_bianchi_hyrec/trajectory/hyrec_source_adapter.py` | 원 HyRec snapshot 기반 가상 선 복사 소스와 directional optical depth 인터페이스 확인. 해당 선 광학깊이는 CMB Thomson 광학깊이와 물리적으로 다르다. 보존한 원본 history ownership 경계를 따른다. |
| `../rei_bianchi/docs/research_sync/REI-REC-BASS-SYNC02-20261005/loop2/research/independent_history_check.py` | `physics/rhs`의 팽창 Peebles 수소율과 정상계 `cn_e σ_T dt`를 재사용했다. 상수 matter-dominated H와 n_H0을 실제 H(N) 및 표 metadata의 n_H0으로 바꿔 1200–1000에서 독립 적분. SHA-256 `d0a3b0b3a8ef718093c9ab0bef0a5a7d97193cb2c7ebc821007970b1a131efc3`. |

R3. 계량 부호는 $−,+,+,+$, tetrad는 R49 geodesic normal/Fermi–Walker. 좌표 n은 관측자가 보는 하늘 방향, 광자 진행방향은 p=−n이다. $N=\ln a$는 공간 hypersurface의 부피시계이고 $z_v=e^{-N}-1$이다. 방향별 측정 적색편이는 null ray의 에너지 비로 따로 결정한다. `radiation`은 유효 복사 perfect fluid다. `cdm`은 단순 압력 없는 비중입자 성분, `baryon`은 정상계 정지 dust다. 자유흐름 중성미자 및 실제 대질량 종 분해는 이 초기값의 대상 밖이다.

## R4–R6 · 구성, 유도, 반례

R4. 초기 물리적 기준 주파수는 $H_*=H_\mathrm{ref}(z_v=1600)$이며 단위는 s⁻¹이다. 초기 rest energy는 $8\pi G\epsilon_j/(c^2 H_*^2)=3(H_{0,\mathrm{ref}}/H_*)^2\Omega_{j,0}a_i^{-3(1+w_j)}$이며 이 식에서 에너지 밀도는 J/m³이다. R49 변수는 이를 기하 단위 $\kappa=1$로 쓴다. 부피 정규화 $a_o=1$을 사용하고 실제 $H_o$는 궤적의 출력이다. 진공항은 $\Lambda c^2/H_*^2$로 같은 차원을 쓴다. 초기에 $\sigma/H_* = \epsilon S$, $\epsilon=10^{-5}$, $S=[[-1,.4,-.3],[.4,.3,.2],[-.3,.2,.7]]$. 복사속도 $v_r/c=0.1\epsilon(1,-.5,.25)$이며 FLRW는 전단과 속도가 모두 0이다. 공간구조 기준 $\gamma=3\times10^{-4}$에서 V는 $A_1=\gamma$, VII_h는 $A_1=\gamma/2,n_{22}=n_{33}=\gamma$, VI_h는 $A_1=2\gamma/3,n_{22}=\gamma,n_{33}=-4\gamma$다. 나머지 성분은 0이고 A, n의 단위는 코드에서 $H_*$로 나눈 기하 주파수다.

R5. 종별 $\rho_n=(\hat\epsilon+\hat p)\Gamma^2-\hat p, q_i=(\hat\epsilon+\hat p)\Gamma^2 v_i$. 정상계 무차원 속도 $v$에서 dust flux 잔여분 $q=-D_j\sigma^j{}_i-q_r$에 대해 $v=2q/(w+\sqrt{w^2+4q^2})$, $w=\hat\epsilon_d$. 이는 Codazzi를 충족하면서 약한 tilt의 감산 소실을 제거한다. Hamiltonian 초기값은 $3H^2=\rho_n+\Lambda+\sigma_{ab}\sigma^{ab}/2-{}^{(3)}R/2$. R49는 이를 초기화할 때만 풀며 이후 $H,\sigma,A,n$ 및 종별 Euler 방정식을 적분한다. $\Gamma^a{}_{bc}$는 $H,\sigma,A,n$에 선형이고, k=0 정상계 각방향 방정식에서 순수 isotropic $H$는 소거된다. 따라서 전단 STF 5개, 구조벡터 3개 및 대칭 n 6개에 대해
$$
\frac{dy}{dN}=\bigg[\sum_{j=1}^{14} g_j(N)M_j + \frac{c\sigma_T n_e}{H(N)}K\bigg]y+S_2(\sigma/H),
\qquad S_{T,2m}=-\int d\Omega\,Y^*_{2m}\hat n^i\hat n^j\sigma_{ij}/H .
$$
R97의 $Q\pm iU=-\sum(E_{\ell m}\pm iB_{\ell m}){}_{\pm2}Y_{\ell m}$ convention에서 $K_{TE}=K_{ET}=+\sqrt6/10$. $\Pi_L$로 끝나는 유한 위계이고 각 $\ell$에서 $-\ell\le m\le\ell$ 전부를 보존한다. $y(N_i)=0$이고 관측자 boost는 0이다. 선형 홍색이동 소스, 주어진 배경의 정확한 각방향 이류, 선형 Thomson 충돌을 조합한다. 광자 고차모멘트의 역반응은 방정식의 독립 항으로 열려 있다.

R6. $dt/dN=1/H_{\rm SI}$ s, $d\chi/dN=c/(aH_{\rm SI})$를 Mpc로 환산한다. $\dot\tau_\chi=a\sigma_T n_e$ (길이 단위 환산), $n_e=x_e n_{H0}a^{-3}$이므로 $d\tau_{\rm accum}/dN=c\sigma_T n_e/H>0$. $\tau_{\rm accum}$은 광선 전방으로 더한 산란량이다. source와 geometry를 고정하는 효과는 다르므로, freeze 대조는 $g_jM_j$만 마지막 시각에 고정한다. 소스·시계·opacity·시작 계수는 완전히 동일하다. VI_h의 tracefree spatial Ricci가 초기 작은 전단에만 비례할 필요는 없으며, 이 계열에 대해 전단 진폭 선형성 결과를 외삽하지 않는다.

## R7–R10 · 계산, 판정, 인계

R7. $x=y_{T,E,B;\ell m}$의 부호를 보존한 전방 모델 계수에 대해 다음 값은 $\ell=2,\ldots,5$ 모든 m의 복소 Euclidean norm이다. 기준은 L=12, 310구간. 단위는 무차원 시험장 진폭이다.

| 초기값 | T | E | B | 마지막 기하로 고정한 B 차이 / 시간 의존 B norm |
|---|---:|---:|---:|---:|
| FLRW | 0 | 0 | 0 | 미정의 |
| I | 7.26840e−6 | 5.15916e−7 | 7.49e−19 | 미실행 |
| V | 7.26463e−6 | 5.15821e−7 | 2.83735e−9 | 미실행 |
| VII_h | 7.26709e−6 | 5.15867e−7 | 4.85993e−9 | 1.04956 |
| VI_h | 1.30393e−3 | 4.54787e−6 | 1.79133e−7 | 0.21327 |

R8. VII_h의 고정 대조 $\ell=2..5$ 상대 계수차는 T 1.516%, E 1.036%, B 104.956%이고 B 절대차는 $5.101\times10^{-9}$이다. 이는 해당 작은 분모와 주어진 계수 벡터의 차이다. 모형 식별력이나 관측 검출 유의도는 이 수치에서 따르지 않는다. $Q,\Pi,F,G_F$에는 각각 물리적 body, 법칙으로 보정한 null, 유한측도, 점유의 수송법칙이 더 필요하다. 이 실행은 signed carrier를 산출하며 네 종속 뷰를 관측량으로 부여하지 않는다.

R9. 수소 재결합 IVP를 별도로 $1200\ge z_v\ge1000$에 설정했다. 초기 $ x_H=0.3220815$를 HyRec 표의 값에서 채택해 두 계산에 똑같이 넣었다. $T_m=T_\gamma=T_0/a$, 수소 원자만, 정상계 isotropic Sobolev/유효 3준위율을 사용한다. legacy의 $C=[\Lambda_{2s}+3R_\mathrm{esc}]/[\Lambda_{2s}+3R_\mathrm{esc}+\beta]$, $R_\mathrm{esc}\propto H/[n_H(1-x_H)]$와 $dx_H/dN=-C[n_H\alpha x_H^2-\beta(1-x_H)e^{-E_\alpha/(k_BT)}]/H$를 사용한다. H를 실제 VI_h와 기준 FLRW로 바꾼 결과 공통 화학의 $\Delta x_H(1000)=+5.638\times10^{-9}$, $\Delta\tau=-3.766\times10^{-7}$이다. 두 tolerance 간 최대 광학깊이차는 $2.70\times10^{-12}$. FLRW 화학 자체는 $x_H(1000)=0.04847304$이고 표의 $x_e=0.04865097$이다. 서로 다른 물리 근사 간 차이가 검출한 조건부 팽창 반응보다 크다. 이 구간 결과는 주 수송의 HyRec-2 $x_e$에 이어붙이지 않았다.

R10. 시간 의존 배경–기하–소스 의존성을 재현 가능하게 제거한 범위는 위 다섯 IVP다. 광자운동량과 응력에서 baryon/Euler로 돌아가는 교환항, 비열적 다극자, He·선 수송을 포함한 방향성 재결합과 재이온화, 원시 regular mode 또는 관측으로 추정한 초기조건은 MODEL. 다주파 beam/mask/잡음·likelihood로 이 특정 atlas를 대조하는 작업은 DATA/ADDITIONAL_ANALYSIS다. 가까운 추가 계산은 R49 Euler에 $-Q^a_{\gamma b}$를, 복사 모멘트에 대응되는 $+Q^a_{\gamma b}$를 같은 사각틀에서 구현하고 합산 보존, FLRW tight-coupling, 근-FRW AniCLASS 공통 regular mode에서 signed T/E/B를 비교하는 것이다. 현재의 개별 유체 보존 closure를 통과한 결과는 그 상호작용 검증을 대신하지 않는다.

## C1–C8 · 구현 검증과 재현

| 단계 | 산출물 |
|---|---|
| C1 | 기준 R97-REM `52fee3f277d715cdb982dfbe751fefac10513060`. R98 새 모듈과 별도 테스트에만 구현. |
| C2 | `early_state/background`는 초기 대수, 정상계 flux, 실제 R49 이력을 구성. `background_checks`는 늦은 시각 단위에 독립적인 Hamiltonian 및 Jacobi 잔차를 계산. |
| C3 | `Angular`는 14개 독립 텐서 좌표에서 구적한 행렬을 저장한다. 각 midpoint에서 계수로 다시 결합한 full Liouville에 `expm_multiply`의 affine 확장 지수중점법을 쓴다. `timeline`은 실제 N 구간만 허용하고 배경비와 log H를 cubic spline으로 보간. |
| C4 | R49 DOP853 641 샘플 → 155/310/620 광학구간 → all-m L12, L16 → 독립 null-ray. 단일 BLAS/OMP, CPU. SDE나 난수 seed는 없다. |
| C5 | `scripts/r98/bianchi_history.py`, `tests/obsstat/test_r98_bianchi_history.py`, `BIANCHI_HISTORY_RESULTS.json`. JSON에는 L12 복소 계수의 실수·허수, 종별 시간측도, 제한구간 화학, 원본 SHA-256, 하드웨어 아키텍처와 실행 측정값을 담았다. |
| C6 | pytest 9개가 전체 epoch 및 four-family 제약, FLRW 수치해·영 sky, 실제 quadrature에 대한 14-coordinate 투영 선형성, Y20 절대 부호·정규화, 시간축 외삽 거부, freeze 대조와 화학을 검증한다. |
| C7 | FLRW analytic (H(a)) 최대 상대차 (4.69\times10^{-9}) 미만. 다섯 모델에서 (|\mathcal H|/(3H^2)<9.37\times10^{-9}), 총 개별 flux와 divergence의 합 크기로 나눈 Codazzi (<4.29\times10^{-8}). (|nA|/H^2<1.10\times10^{-24})이고 h는 초기값에 대해 (2\times10^{-15}) 이내. Type V에서는 (n=0)이므로 (|nA|/(|n|,|A|))가 수치 잡음의 방향을 측정한다. 보고한 대수 scale은 (|A|^2+|n|_F^2)이며 (H^2) 정규화도 함께 보존했다. |
| C8 | VII_h, 155→310→620구간. 310 대 620의 T/E/B 상대차 (6.043\times10^{-5},1.004\times10^{-4},1.097\times10^{-5}). L12→16 상대차 (<5.50\times10^{-15}), 배경 641→1281 샘플 차이는 (<9.44\times10^{-11}). 초기 전단·tilt를 절반으로 한 동일 VII_h 모델에서 (2y(\epsilon/2)-y(\epsilon)) 상대차는 T/E/B (1.13,1.01,6.60\times10^{-6}) 수준. 충돌 없는 독립 비교는 (\ln(a_o/a_i)-\ln(E_i/E_o))의 scalar multipoles를 사용. 641샘플/512광선적분스텝에서 (8.579\times10^{-5}), 1281샘플/1024스텝 및 수송 추가 세분 시 (2.145\times10^{-5})로 감소한다. 동일 접속 컨벤션을 재사용한 별도 광선적분이다. 편광의 독립 end-to-end 비교는 추가 분석에 속한다. |

```bash
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
.venv/bin/python -m pytest -q -p no:cacheprovider tests/obsstat/test_r98_bianchi_history.py
.venv/bin/python -m scripts.r98.bianchi_history --output "$HOME/Downloads/BIANCHI_R98_history_replay.json"
```

재실행 비교에서는 `families`의 수치와 `inputs_sha256`를 대조한다. 시간과 peak RSS는 실측 메타데이터다. C9 독립 검토와 C10 통합 release는 상위 연구 사이클의 공통 기록을 따른다.
