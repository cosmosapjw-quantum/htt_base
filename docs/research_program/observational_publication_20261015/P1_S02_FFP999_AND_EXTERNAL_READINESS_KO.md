# HTT S02 연구 루프: legacy signed defect × FFP10 999개 × 외부물리 입력 준비

2026-10-15 KST. 연구 기준 commit aeb303e5c166b8c22f18abf6f76def96418aeb23. 원본 legacy (x,F,Pi,Q,G_F), 업그레이드된 1+3/PSTF/MES 및 실제 Planck/CF4 관측을 구분하여 재사용한다. 본 루프의 실질 산출물은 source-simulation empirical measure 위의 정확한 *부분식별* pushforward이지 cosmological posterior 또는 anomaly p-value가 아니다.

## 1. 정의, 원본 물리학과 source 경계

Original signed Gauss defect: x_C=Sigma²-W²+Omega_tilt+DeltaOmega_k; Q=x_C/U_sigma. Sigma=|sigma|/H, |sigma|=sqrt(sigma_ab sigma^ab/2), metric (-,+,+,+). MES photon PSTF epsilon2/3는 실제 sigma, W, matter/radiation tilt나 signed curvature의 관측값이 아니다. 또한 legacy sector fraction F는 directional temperature bolometric F4와 전혀 다른 함수다.

UNVERIFIED all-observer geodesic C1/C2 + hypothetical intrinsic eps1=0 조건 아래에서만
U_sigma=3/2(3 eps2 +3 eps3/7)^2,
U_omega=3/2(2 eps2/15)^2,
U_omega/U_sigma=196 eps2^2/[2025(7 eps2+eps3)^2].
Wolfram으로 마지막 수식을 대수적으로 확인했다. 해당 상한을 물리적 posterior로 전환하지 않는다.

실제 Planck PR3의 9 처리 결과는 하나의 cosmological sky이고 SHA는 900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459. 모의실현 source는 독립 등록된 FFP10 CMB 999개와 같은 ID noise 300개를 원래 Planck 온도 마스크(NSIDE64 RING 26,846 pixels)에 projection한 eps2/3. 원본 489 MB K1 cache SHA 86b792c821b3e641c76c83d96523148c65e9d30a439d7c850acc808c1bc5fadb를 실제 스트리밍으로 검증했다. 임의 posterior 표본은 생성하지 않았다.

## 2. 수학적으로 sharp한 box Pi_Q와 full 물리량의 미식별성

추가로 flat/untilted Omega_tilt=DeltaOmega_k=0, 0<=Sigma²<=U_sigma, 0<=W²<=U_omega라는 counterfactual box를 가정하면 각 simulation j에서 Q_j in [-r_j,1], r_j=U_omega,j/U_sigma,j이다. 서로 독립적으로 선택 가능한 수학적 product box와 1/999 empirical source weights에서 strict event Q>t의 lower/upper는

L(t)=sum_j w_j 1_{-r_j>t},
U(t)=sum_j w_j 1_{1>t}.

각각 box lower/upper endpoint witness로 실제 source 모든 threshold에서 검증했다. 이는 실제 Planck 관측 posterior가 아니며 cosmological null PTE도 아니다. 실제 full x_C에는 미측정 signed curvature와 tilt sector가 남아 Q가 임의의 실수가 될 수 있으므로 모든 유한 t에서 physical Pi_Q(t) outer=[0,1]만 가능하다.

FFP10 masked-source 999개에서 U_sigma 중앙값 7.5624717801e-9, U_omega 중앙값 1.0666289754e-11, Q box lower 중앙값 -0.00139777898036. Q lower source empirical 5/16/50/84/95% 분위수는 [-0.00166304,-0.00157022,-0.00139778,-0.00115923,-0.00100422]. Same 999 masked vs full source Qlower RMS=9.43372e-5, 300 same-ID CMB+noise vs CMB Qlower RMS=2.73009e-6. 이는 보정/processing/source 민감도다.

원래 legacy-modern finite_functional_image 엔진에 이 *같은* 999 simulation ID를 물리적으로 미관측 Gauss sector와 F/depth를 None으로 넣어 explicit missing mass {x_C:1, Q:1, F:1}를 얻었고 Pi_Q(t)=[0,1]을 유지했다. 선언적 G_F floor=.05 하의 순수 추상 범위 [.05,20]은 실제 두 깊이의 측정치가 전혀 없기에 observed G_F가 아니라 generic support일 뿐이다. F4와 F의 동일시, 처리 하늘 9개의 독립 posterior화, CF4 apparent STF를 physical sigma로 옮기는 작업은 수행하지 않았다.

## 3. 외부 입력 차단노드 7개 병렬 준비

최신 PUBLICATION_DAG.json의 일곱 external_missing ID를 직접 검사하고 21개 실제 local candidate file의 존재를 확인했다. REC/REI local source 존재는 물리적으로 qualified cosmological atlas/tilt history를 뜻하지 않는다. 충족된 외부 물리관측 데이터 계약은 **0개**, 블로커 상태 변경 **0개**.

S04: full x_C common-congruence physical joint law 또는 valid narrower identified source interval 부재.
L03: Planck foreground/beam/effective-filter noise full end-to-end null/exchangeability 부재.
H02: 진짜 CF4 group method calibration, selection and angular-depth peculiar flow covariance 부재.
V03: recombination one-event screen만 있고 global physical radiation/matter tilt source history T/E/B 수송 부재.
B02: rec_bianchi frame/screen 및 Planck spin2 source 코드는 있으나 all-family verified full Einstein–Boltzmann polarized atlas/IC 부재.
K03: radial CF4 외에 nonradial curl/proper motion/acceleration/tilt 관측자료와 covariance 부재.
K04: K01/K02 수학적 source는 있으나 H04 true selection/cosmological light-cone physical law 부재.
기계판독 상세 필수 입력/파일·HEAD/다음 가능한 검증: results/EXTERNAL_BLOCKED_PREFLIGHT_20261015_v2/result.json.

## 4. 실제 CF4 look-angle를 이용한 K03 기하 준비

로컬 Euclidean first-velocity-jet 한계에서 v_i(r n)=r G_ij n_j, G=H I+S+W이면 radial nGn=H+nSn, nWn=0이지만 hypothetical transverse proper-motion rate는 (I-nn)G n이다. 이 식은 완전한 GR Bianchi optical ray history가 아니고 실제 proper-motion 측정도 아니다.

실제 CF4 35,970개 J2000 하늘 방향만 사용하여 tangent shear 5 + omega 3의 angular design rank8, shear nuisance profile 뒤 omega rank3을 얻었다. omega 상대 정보 고유값 [0.5282989023,0.7223403252,0.9306794734]. 제조한 gradient coefficients [1,-2,3,.5,-1,5,-7,9] km/s/Mpc의 source injection/recovery 최대오차는 1.19904e-14 km/s/Mpc였다. 실제 CF4 그룹에는 proper-motion 자료가 제공되지 않으므로 K03은 입력 차단을 유지한다. 결과: results/K03_CF4_NONRADIAL_PREP_v1 및 Python angular code/tests.

## 5. 연구 DAG·재현·다음 행동

이번 S02는 999 unique source simulations + original finite mathematical functional image and explicit unknown probability mass를 실제로 실행했을 때만 completed_scoped로 승격한다. S03은 X01 physical source identity/overlap graph를 먼저 요구하고 S04는 여전히 외부 입력 차단이다. 7 external tasks는 실제 자료 준비만 진행하고 완료로 바꾸지 않는다. 그 검증이 통과하면 전체 완료 12/42=28.57%, ready4, external7, waiting19, paper gates 0/6이 된다.

실행 경로:
- htt/obsstat/s02_ffp_source_partial_pushforward.py
- scripts/run_htt_s02_ffp999_partial_image.py
- tests/obsstat/test_s02_ffp_source_partial_pushforward.py
- scripts/run_htt_external_physics_preflight.py
- htt/obsstat/k03_nonradial_proper_motion_preflight.py
- scripts/run_htt_k03_nonradial_preflight.py
- tests/obsstat/test_htt_external_preflight_and_nonradial.py
- results/S02_ffp999_empirical_partial_v1/와 독립 재실행, 외부 입력 v2 및 K03 준비 결과.

문헌: Stoeger–Araujo–Gebbie astro-ph/9904346, MES astro-ph/9501016, Saadeh et al. PRL117 131302 (2016), Beresteanu–Molinari의 random-set partial identification 연구, Tully/Courtois CF4 source, Planck 2018 IV and VII. Native host subagent spawn 기능 부재, NOT_RUN. Local Codex 사용 안 함. 원본 user owner checkout 57개의 미커밋 경로 보존.
