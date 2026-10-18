# S02: 실제 CF4 공동 표본의 거리 보정 식별 한계

2026-10-18. HTT, C0/CONDITIONAL/empirical_proxy. 기존 checkout의 `research/htt-sixpaper-goals-robustness-20261018`, 시작 HEAD `1e095a2749cce9b28e45aac043a82218c21f84e5`.
요청 executor `gpt-6.1-sol/high`, 관찰된 runtime identity `UNKNOWN`. 독립 검토와 canonical 상태 결정은 부모 담당이며 이 산출물은 스스로 S02를 승인하지 않는다.

**원래 S02 목표인 물리 sector 사상은 미완료다.** 현재 입력에는 finite-window apparent field를 공통 congruence의 물리 shear로 연결하는 source-qualified 응답이 없다. 본 실행은 이름을 바꿔 그 입력을 대신하지 않는다. 실제 관측 요약치에서 거리 보정 때문에 무엇이 식별되지 않는지를 새로 정량화한, 한 번의 bounded preparation 결과다. 추가 assurance 반복으로 노드를 완료시키지 않는다.

## 실제 입력과 보존한 measure

`../P1/results/paired_functional_arrays.npz` SHA256 `cd38f438a0bf07385b07478c7b5c122df5af1e9bb48a5575fe1cad40ef261f27`의 **기존 2048개 공동 표본을 그대로 읽었다.** 새 표본 생성·seed 변경·분모 재정규화가 없다. `CF4_WORKING_JOINT_00000`부터 `02047`까지 각 ID에 네 겹치는 창이 포함되고, 각 ID의 원 가중치 `1/2048`의 합은 정확히 1이다. 네 창을 독립 관측으로 세지 않았다. original draws, signed STF/H, q_app, physical NaN 열을 새 NPZ에서 분리 보존했다.

원 출처는 CF4 35,970 그룹의 H03 `H03_SOURCE_TOMOGRAPHY.json`, SHA256 `5d31e2ab4fea682c538c31c15181ae7b07e11efba98b36c66aff6feca88f8326`, upstream selected-source NPZ SHA256 `86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c`다. 이 NPZ는 선택된 관측 행 추출물이며 원 CDS raw table의 SHA가 아니다. H03는 `cz=d[H+D·n+nᵀSn]`를 fit하며 스스로 `not physical expansion H(z,n)`이라고 선언한다. 36×36 joint covariance는 같은 그룹에서 전파한 **diagonal velocity-noise working law**다. 이번 실행은 raw catalogue 재fit, 실제 selection law 추정, physical likelihood 구축을 하지 않았다.

## 1. 한 창을 등방화하는 최소 거리 보정

선택한 sector는 H03 **fitted even angular field**

`h_j(n)=[h_full,j(n)+h_full,j(-n)]/2=H_app,j+nᵀS_app,j n=nᵀM_j n`, `M_j=H_app,j I+S_app,j`, `||n||=1`.

S는 원래 H03 Frobenius-orthonormal STF 기저를 쓴다. H와 S의 단위는 km/s/Mpc, 아래 log 비율은 무차원이고 magnitude 보정은 mag다. dipole는 이 정의에서 parity로 제외했다. 상관·selection·mask 독립성을 가정한 것이 아니다.

거리 보정 부호를 `d_corrected=d_app 10^(Delta_mu/5)`로 두면 `h_corrected=h_app 10^(-Delta_mu/5)`다. 양의 M의 고유값 극값은 전 구면의 h 극값이다. 상수 H*>0로 등방화하려면 `Delta_mu(n)=5log10[h(n)/H*]`이며,

`rho*=inf_(H*>0) sup_n |Delta_mu(n)|=2.5log10(lambda_max(M)/lambda_min(M))`,

`H*=sqrt(lambda_max lambda_min)`.

이는 log h의 최소·최대 사이 midpoint를 선택한 elementary minimax다. 두 고유벡터에서 ±rho*를 달성하고, 작은 sup bound로는 두 끝을 동시에 덮을 수 없다. 따라서 이 fitted-field ambiguity class에서는 **필요충분한 sharp erasure radius**다. 양의 h 조건이 깨지면 계산을 거부하며 clipping하지 않는다.

| z 중심 | 실제 point-fit rho* [mag] | working 5/50/95% 분위 [mag] |
|---|---:|---|
| .025 | .04421371 | .03513694 / .04556907 / .05643241 |
| .040 | .06363935 | .05352913 / .06447596 / .07570800 |
| .060 | .07731767 | .06606335 / .07853863 / .09121694 |
| .080 | .04017529 | .03092264 / .04659453 / .06571510 |

예컨대 z=.060의 모든 저장 표본은 .05 mag보다 큰 erasure radius를 요구한다. 이는 **현재 working measure의 조건부 질량**이며 관측 보정이 .05 mag 이하임을 측정했다는 뜻도, physical anisotropy 유의성도 아니다. 보정 크기를 허용하면 shear가 0인 등방적 field도 동일한 apparent even field와 양립한다는 구성적 obstruction이다. 실제 congruence는 여전히 미식별이다.

## 2. 네 깊이에 공통인 방향 보정: 정확한 공동 minimax

깊이별 independent calibration을 허용하면 각 rho*로 끝난다. 더 유용한 질문은 **하나의 arbitrary common angular calibration** g(n), 각 창의 자유 monopole c_j와 bounded differential residual e_j로 네 field를 설명할 수 있는가이다:

`E_j(n)=5log10 h_j(n)=g(n)+c_j+e_j(n)`, `|e_j(n)|<=eta`.

g의 크기에는 외부 bound를 넣지 않았다. calibration이 모든 깊이에 같다는 것은 **분석상의 가정**이며 method/window 혼합이 실제로 이를 만족한다는 측정은 없다. 이 함수 g는 pure quadrupole에 제한되지 않는다.

각 방향에서 네 허용 g 구간이 공통 교집합을 가지려면 모든 ordered pair에 대해

`c_j-c_k >= D_jk-2eta`, `D_jk=sup_n[E_j(n)-E_k(n)]`.

`h_j/h_k`는 양의 quadratic forms의 generalized Rayleigh quotient라서 `D_jk=5log10 lambda_max(M_j,M_k)`다. 방향 grid·pixel approximation 없이 극값을 얻는다. 유한 difference constraints의 feasible 조건은 모든 directed cycle의 총 weight가 0 이하인 것이다. 따라서

`eta*=max_directed_simple_cycle C {sum_((j,k)in C) D_jk / (2 |C|)}`.

Cycle 합을 취하면 c가 상쇄돼 필요조건이 된다. 반대로 nonpositive cycle 조건 아래 longest-path potentials c가 모든 부등식을 만족한다. 각 n에서 `g=(max_j(E_j-c_j)+min_j(E_j-c_j))/2`로 놓으면 |e_j|<=eta를 달성한다. 이것으로 충분조건과 sharpness를 얻는다. 2-cycle만 쓰면 `max_(j,k)(D_jk+D_kj)/4`인 pair lower bound다. 3/4-cycle은 추가 consistency 정보를 쓴다.

실제 point fit의 `eta*=.02479898849 mag`다. 2048개 원 공동 표본에서 5/50/95% 분위는 **.02352775896 / .03011962061 / .03872817414 mag**다. 135/2048 표본에서는 3-cycle이 가장 큰 pair bound보다 강하고, 개선 최대값은 **.00431213369 mag**다. 2-cycle active 1913개, 3-cycle active 135개, 4-cycle active 0개다. 모든 표본의 c witness에 대한 최대 부등식 초과는 5.55e-17 mag다.

| 선언한 differential residual eta [mag] | eta* > eta인 strict working mass |
|---|---:|
| .020 | 2036/2048 = .994140625 |
| .025 | 1817/2048 = .88720703125 |
| .030 | 1045/2048 = .51025390625 |
| .040 | 59/2048 = .02880859375 |
| .050 | 0 |

이 질량은 미리 주어진 finite working measure의 함수다. 실제 보정 residual radius의 추정이나 calibrated p/coverage가 아니다. 공통 g를 허용해도 서로 다른 깊이의 방향 field를 완전히 등방화할 수 없는 정도를 보여주며, 외부 calibration 자료가 제공해야 할 **측정 target과 scale**을 준다.

## 3. signed x를 추론할 수 없는 추가 이유

S01의 signature는 (-,+,+,+), H=Theta/3이며,

`x_C=(sigma_ab sigma^ab-omega_ab omega^ab)/(6H²)+Omega_tilt+DeltaOmega_k`.

설령 별도의 실제 source가 `S_app=sigma`, `H_app=Theta/3`를 보증하고 tilt와 curvature를 0으로 제한하더라도, radial affine relation은 antisymmetric Omega에 대해 `nᵀOmega n=0`이다. 따라서 동일 radial data에서

`x_kin=(||S||_F²-||Omega||_F²)/(6H²)`

는 **조건부 algebraic set** `(-infinity, ||S||_F²/(6H²)]`를 가진다. 테스트는 같은 radial field에 positive/negative x witness가 공존함을 보인다. 이 코드는 선행 source에 없는 bridge를 승인하지 않으므로 위 상한 열도 `conditional_x_kin_upper`로 분리했고 physical x_C에는 넣지 않았다. 미측정 tilt/curvature까지 자유롭게 허용하면 전체 x에 유한 구간을 주장할 수 없다. 실제 unknown x를 0으로 치환하거나 음수를 clip하지 않았다.

physical x_C/Q/F/G_F unknown mass는 각각 **1**이고 기존 physical NaN 열은 그대로다. physical Pi의 generic outer는 [0,1]을 유지한다. positive sector ceiling과 common-congruence/depth 규약이 없으므로 certified F와 G_F는 domain-uncertified다.

## 엄밀한 범위, 원전 및 다음 실행

이것은 raw data에 distance correction을 적용하고 동일 weight/design으로 다시 fit해도 결과가 같다는 주장이 아니다. 실제 correction은 d와 error weighting, selection을 바꾸므로 catalogue likelihood를 따로 다시 구성해야 한다. 구면 전체의 극값은 fitted quadratic field를 연장한 값이며 모든 방향에 같은 관측 지원이 있다는 증거도 아니다. Gaussian working covariance의 물리적 정합성이나 calibration field의 매끈함/방법별 구조도 추가 정보다.

[Boubel et al. §3, Eqs.(3.3–3.7)](https://arxiv.org/html/2412.14607)는 directional zeropoint와 expansion의 연결 및 calibration 가정을 설명한다. 본 결과는 그 논문의 likelihood 또는 유의성을 재현한 것이 아니다. [Maartens et al. §§3–4](https://arxiv.org/html/2312.09875v3)는 matter-frame expansion과 boosted observer의 optical relation을 구별한다. 이 원전을 현 turn에서 확인했으며, 이미 있는 optical theory가 H03 finite-window coefficient에 필요한 응답/보정/remainder 데이터를 제공하는 것은 아니다. Elementary minimax와 difference-constraint 방법 자체의 신규성을 주장하지 않는다.

S02의 정확한 missing input은 (1) 동일 source/congruence/frame에 연결된 optical→kinematic 응답, (2) finite-z evolution/remainder와 peculiar-flow controls, (3) 방향·방법·깊이별 calibration 및 selected covariance/likelihood다. total x에는 vorticity/tilt/curvature, Q/F/G_F에는 admissible positive ceiling과 depth 규약이 추가로 필요하다. 현재 파일만으로 source-supported 물리 sector를 하나라도 승인할 수 없다. **S02는 physical mapping 대기이며, 이 때문에 S03의 physical sensitivity application도 미완료다.**

다음 runnable goal은 H02가 실제 method별 source-matched centers/covariance 또는 calibration bound를 확보하면, 같은 2048 IDs와 위 eta functional을 그 자료의 admissible calibration class에 연결하는 것이다. raw CF4 rows를 다시 선택/fit할 때는 d와 noise/selection 변화까지 반영한다. 그 입력이 없으면 이 lane의 과학 진전을 막는 입력을 부모에게 반환하고 다른 ready lane으로 이동한다. 기존 성공 계산을 다시 실행하는 assurance loop는 다음 goal이 아니다.

## 재현 명령과 검증

저장소 root에서:

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python docs/research_program/observational_publication_20261015/CONTINUATION_20261018/S02_EXECUTION_20261018/calibration_obstruction.py
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python docs/research_program/observational_publication_20261015/CONTINUATION_20261018/S02_EXECUTION_20261018/test_calibration_obstruction.py
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python docs/research_program/observational_publication_20261015/CONTINUATION_20261018/S02_EXECUTION_20261018/plot_calibration_obstruction.py
```

12 targeted tests: exact source/ID/weight preservation, source tamper rejection, isotropic/axisymmetric limits, erasure witness, orthogonal/scale invariance, generalized eigenvector endpoint witness, shared-shape cancellation, **40 independent linear-program comparisons** (20 actual joint draws +20 positive matrix examples), strict ties, invalid domains, signed-vorticity witness, generated arrays/all 2048 joint constraints. First executed 11-test suite passed; the generated-output regression was added before the final 12-test suite. No scientific failure was hidden or validator relaxed. Full repository CI, raw catalogue refit, physical transfer, solver/ODE: NOT_RUN.

산출물은 `results/S02_CALIBRATION_OBSTRUCTION.json`, `results/calibration_obstruction_arrays.npz`, `results/calibration_obstruction.png`와 PDF다. 그림을 생성하고 육안 확인했다. Source SHA는 immutable input identity 검증이며 numerical output의 scientific admission을 뜻하지 않는다. 독립 검토: PENDING_PARENT_INDEPENDENT_REVIEW.

## Claim audit

| Claim | Owner/status | Evidence/limit |
|---|---|---|
| 위 rho와 eta 식은 선언된 fitted-field calibration class의 sharp minimax다 | htt / CONDITIONAL / C0 / empirical_proxy | 유도, endpoint witness, 별도 LP 비교; physical map 아님 |
| 위 숫자는 기존 CF4 summary-conditioned 공동 finite measure의 실제 재실행이다 | htt / DIAGNOSTIC_ONLY / C0 / empirical_proxy | 원 NPZ와 source seal, 보존된 IDs/weights; calibrated posterior 아님 |
| physical sector mapping 및 physical x/Q/F/G_F | htt / UNMEASURED 또는 domain-uncertified | 공급되지 않은 response/calibration/ceiling; unknown mass 1 |

스킬 적용은 signed x와 sector F의 분리, source/working-law/physical claim 경계, 원 질량 보존, 좁은 falsifier와 raw execution 기록에 반영했다. Canonical DAG/status/shared 파일은 수정하지 않았다.
