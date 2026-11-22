# R98 과거 물리·통계 코드의 재사용 판정

기준은 R97-REM `52fee3f277d715cdb982dfbe751fefac10513060`과 R98 실행에서 읽은 파일의 SHA-256이다. 해당 commit의 로컬 Git tree는 tracked file 34,190개를 전부 반환했다. R96 원격 recursive tree 결과 32,291개는 truncation이 표시된 당시 조회값이다. 두 수의 차이로 누락된 코드의 수나 과학적 의미를 추정할 수 없다. 별도 7개 자료 루트의 내용 색인에서는 byte duplicate class 776개, Python AST 구조 duplicate class 277개를 확인했다. 후자는 외부 데이터·부호·단위·실행환경·호출자의 의미를 보존하는지 검사하지 않는다. 원본 경로와 분석 가능한 일부 구성요소에 대해 아래와 같이 판정했다.

## 원래 목적에서 이번 계산으로

| 원래 과학적 목적 | 재사용한 부분과 필요한 교정 | R98에서 실제 확인한 것 | 남은 의무 |
|---|---|---|---|
| PR13AG의 낮은 다중극 온도·편광 수송 복원 | `transport_couplings`와 유한 L 수렴 비교의 구조를 보존했다. `synthetic_gamma_history`, `synthetic_shear_source`는 소스 모형 실험이었다. R95–97의 STF/Thomson/각방향 위계를 이어받아 R98에서 종단점 재정규화와 경험적 전단 감쇠를 실제 R49 시간열로 교체했다. | 모든 m의 L12 signed T/E/B를 다섯 IVP에서 계산했다. VII_h에서는 L16 대조의 저다중극 상대차가 5.50e−15 미만, 같은 전단과 opacity에서 기하만 종단값으로 고정한 B 차이는 5.10e−9였다. | regular primordial mode, 광자–중입자 운동량 교환, 고차모멘트의 Einstein 역반응 |
| 가려진 CMB 하늘에서 L=2 통계적 비등방성 측정 | 원본 `estimate_biposh_L2`는 다섯 출력 중 중앙 슬롯에만 마스킹한 맵의 각 m 파워를 더한다. 다른 네 슬롯에 필요한 모드쌍의 위상과 결합계수가 없다. `biposh_variance`의 1/f_sky와 likelihood 생성자의 추가 1/f_sky 보정도 별도 검토 대상이다. R98은 전천 라벨 대신 실제 support와 signed harmonic feature, Gaunt 수축을 채택했다. | grouped 999 pair/300 noise ID에서 native–NumPy Gaunt 최대차 1.44e−15, 잡음군을 넘나드는 학습·검증 중복 0. 맵에 대한 OLS 재구성 최대차 1.85e−13 μK. | 동일 mask·beam·channel·split별 end-to-end null과 누설 covariance. 원본 중앙 슬롯의 값에 일반 BiPoSH의 해석을 붙일 수 없다. |
| 저다중극 pixel Gaussian likelihood | `PixelLikelihood`의 Legendre signal covariance, 관측 pixel 선택, Cholesky quadratic form과 log determinant는 명시한 Gaussian 모형에 쓸 수 있다. 원본 N은 scalar white RMS의 대각행렬이며 입력은 T map이다. | R98이 검증한 Gaussian 계산은 feature 좌표의 held-out density와 비정규화 없는 두 좌표계 대조다. Unshrunk shear 변환 전후 q와 NLL의 최대차 7.11e−14. 원본 pixel likelihood를 Planck 공식 likelihood로 실행·교차검증한 결과는 없다. | 실제 픽셀 단위 correlated noise, smoothing/beam, 기기·성분별 잔여물, signed polarization과 matched mocks |
| BASS의 물질 momentum hierarchy·Thomson collision·frame transport | PSTF/모멘트 정의, basis-free polarization screen 및 rank-9 collision eigenspace, transported triad를 규약 대조에 사용했다. 고유값 검사는 T–E 비대각 원소의 부호를 분간하지 못한다. R97-REM에서 signed angular projection으로 현 sky convention의 +√6/10을 복구했다. R98은 정상계 광자 진행방향 p=−n과 관측 도래방향 n을 명시했다. | R98는 교정된 연산자를 매 시각 평가했다. VII_h 충돌 없는 T와 별도 4D ray 적분의 상대차는 세분 후 2.15e−5. 다섯 signed 하늘의 양의 광자모멘트에서 Cov(n)의 최소 고유값은 모두 0.333044 이상이었다. | 유한 tilt에서 독립적인 편광 end-to-end 대조. 조건부 test photon 모멘트에서 실제 정상계 총 flux로 가는 관측법칙 |
| R49의 일반 Class A/B tilted Einstein–Euler IVP | 실제 tetrad, 정상계 에너지·flux, Jacobi/Hamiltonian/Codazzi 방정식을 그대로 적분. 약한 tilt에서 기존 보상속도의 이차식이 뺄셈 소실을 일으켜 R98 초기화에서 양의 근을 유리화했다. Type V의 n=0에서 잔차를 두 벡터의 끼인각으로 정규화하면 잡음 방향이 남아 대수 norm 및 H² 단위도 기록했다. | 부피 redshift 1600에서 0까지 FLRW, I, V, VII_h, VI_h를 적분. analytic FLRW H 상대차 <4.69e−9, 전체 최대 Hamiltonian/(3H²) <9.37e−9, 정상계 flux 규모 대비 Codazzi <4.29e−8. | 특정 초기값을 실제 우주의 초기조건으로 인식하기 위한 물리·관측 모형 |
| rec_bianchi의 배경궤적·각도별 선 복사, rei_bianchi의 원자율·광학깊이 | REC의 axisymmetric I와 characteristic solver는 제한된 IBVP의 검산 자원이다. 원 HyRec virtual-line source/escape와 Thomson 산란 opacity는 서로 다른 과정이다. REC native clock의 무외삽 비교와 REI 독립 Peebles/정상계 광학깊이율을 사용했다. 후자의 상수 팽창률과 밀도는 실제 R49 H(N) 및 fixture의 n_H0로 바꿨다. | 동일 수소 화학으로 1200→1000을 풀어 VI_h 대비 FLRW의 x_H 차 +5.64e−9, 구간 τ 차 −3.77e−7을 얻었다. τ tolerance 차는 2.70e−12. 전천 T/E/B의 opacity에는 별도의 HyRec-2+tanh 이력을 사용했다. | helium·다준위 선 수송·재이온화를 같은 비등방 배경과 연결하고 원소별 정확도를 검사 |
| CF4 group bulk flow와 Doppler catalog likelihood | LR-06D의 VizieR Table 4 계보, 공간창, frame과 bulk-flow 방향 해석을 보존했다. synthetic Doppler catalog는 벡터 방향/응답 실험에 쓸 수 있다. R98은 원거리모듈러스와 보정속도, Table 3 method genealogy를 원파일에서 재조립해 log-distance 적합과 shared-shift 판정을 계산했다. 과거 mock coverage를 새로운 selection에 이식하지 않았다. | 35,970개 선택 그룹의 4개 실제 창에서 STF 5열 생략에 따른 로그 쌍극자 이동 norm 0.00379–0.02035. 직접 재적합 항등식 오차 <2.8e−16. R98 P1은 serialized binary inputs의 tangent/root 경계를 exact fallback으로 복구했다. | 사전 등록 calibration의 upstream covariance, 거리선택과 특이속도 공동법칙 |
| R90의 Codazzi 가족/방향 사상 | 동일 STF chart에서 R90 `codazzi_stf(n,a)`와 R49의 −div σ를 직접 비교했다. VER2 n을 R90에 −n으로 넘기면 양의 정상계 운동량 부호와 일치한다. Rank 결과와 oriented witness의 재사용 조건을 구분한다. | VI_h의 세 지점에서 같은 n의 최대 원소차 0.00212132. 변환 후 5.43e−20 이내. h=−1/9 양옆에서 rank 3→2→3. 실제 초기 종별 flux를 합한 제약 잔차 2.27e−22. | 독립적인 총 flux와 joint covariance. 과거 특정 orientation 제약을 재사용하려면 실제 tetrad chart로 변환 후 재검사 |

외부 AniLoS/AniCLASS는 원 저자들이 제시한 nearly-isotropic homogeneous 계열의 전방 비교 대상으로 둔다. 동일 regular mode, tilt, 배경과 sky convention을 맞춘 native-vs-external 수치 일치 여부는 위 표의 검산 항목에 들어 있지 않다. [Vicente, Pereira & Pitrou 원 논문](https://arxiv.org/abs/2506.07786).

## 파일 지문

아래 SHA-256은 파일 바이트를 식별한다. 내용을 확인한 외부 compatibility component와 실제 R98 계산에 사용한 모듈의 역할은 위 표에 기재했다.

| 파일 | SHA-256 |
|---|---|
| `legacy/bass_htt_mio_github_ready_current/src/bass/PR13AG_projected_multipole_solver_restoration.py` | `2d2678fe868138e7f06dce4df9cffa1ade10519bcf26331582d7505d05e64680` |
| `legacy/bianchi_departure_v091_github/htt/likelihood/biposh_masked.py` | `3a2cfb6d86f3ba1b9e55cb2e3db132600c41c433d99ec84f36853514692deba2` |
| `legacy/bianchi_departure_v091_github/htt/likelihood/pixel_lowl.py` | `ae10077aab73ac987e7d2423e77519d1f984cbc6ef7a5c47e6bade7e563194ec` |
| `legacy/cf4_p0/scripts/make_cf4_bulkflow_likelihood.py` | `d60ecccabdcf287fd248c8713c5e8b2706dff345a784b04ee15741d83192c0e0` |
| `legacy/code_package/catalog_likelihood.py` | `17d14d7441b67c7c77c147a370880f0ac5e8afc209b3861023e8164aad683960` |
| `/home/cosmosapjw/bass/bianchi/matter/hierarchy.py` | `27f81acd681acc34537ad59ad2bec923d95c0adb7ac6d52413c4e3b2e0980aa6` |
| `/home/cosmosapjw/bass/bianchi/q/polarization.py` | `44a2eb306d8870e70d6cb46c8f481bb30e58f64ffee4b9a055a0157a23e79e95` |
| `/home/cosmosapjw/bass/bianchi/matter/grid_boltzmann.py` | `7eaaeee0bb3d55a459941b2d17af439da0bd414c2e50893230c8ba4b0f9a482e` |
| `/home/cosmosapjw/bass/bianchi/physical/frame_transport.py` | `349fff14014ae515a1ca122e601ebaf53d4f9b3a6a180204a974199dbce10ba7` |
| `../rec_bianchi/src/full_bianchi_hyrec/trajectory/characteristic_angular.py` | `1fa89cdf0b2d0568f395444dc8212d325926572057950e55a52f8a0a469dcc53` |
| `../rec_bianchi/src/full_bianchi_hyrec/background/axisymmetric_bianchi_i.py` | `5296880dbf2d1b00e2810c969e6a0406b46f10acff04c794e8f718aff5813955` |
| `../rei_bianchi/docs/science/current_OPERATOR_SPEC.md` | `1d686aa0f4915b0a059dabab59625dfe1d8d3341739586b8077bb8f66fefd183` |
| `../rei_bianchi/research/flrw_pair_observable_20261016/results/THOMSON_PAIR_RESULT.json` | `4c7001b2e0e009393a5c1ade6bb55fdfbfdd9c853c5aa04b5e17404834678754` |
| `htt/bass/background/general_tilted_evolution.py` | `9679d7651a0f29adae712afc8fff9a67731f88970925ce1ef9bdb5f42d207ddd` |
| `htt/bass/background/tilted_bianchi_state.py` | `e36dd616f4d0e2998e48e1a50ae9b67e1cd48842ef5b52ee2b1e4b94b888fe04` |
| `htt/bass/transport/general_bianchi_transfer.py` | `9bcb541d35cabc05b8c325a58bbef57f253627203ff1ac1c354e4bd789f60410` |
| `scripts/r90/sf_attribution.py` | `3a62eb5dae9f1739e3fbe4451eef95ae21c0e5d66b4e81c72242adba2542dffc` |
| `../rec_bianchi/src/full_bianchi_hyrec/trajectory/hyrec_source_adapter.py` | `453e4cbb1f20a12bb0fd2e0b2e67f5dbaaf18639e525afe2b91def95969e4369` |
| `../rec_bianchi/research/rec_history_clock_r6_20261014/code/clock_compare.py` | `b7025bf924ab3bba6c151efe87ee45906156c405eae29ac0e107ecf9ed7eb6fc` |
| `../rei_bianchi/docs/research_sync/REI-REC-BASS-SYNC02-20261005/loop2/research/independent_history_check.py` | `d0a3b0b3a8ef718093c9ab0bef0a5a7d97193cb2c7ebc821007970b1a131efc3` |

## Git 계보와 과학 판정

R98 감사 시점에 직접 조회한 선별 PR 33개의 상태는 OPEN 23, MERGED 4, CLOSED 6였다. 아래 상태와 merge OID는 해당 조회 영수증에 따른다. 계보는 방법의 위치를 찾는 근거이고 과학적 수용은 각 입력과 독립 검사의 범위에 따른다.

| PR | 조회 상태 | 원래 작업 | merge commit |
|---|---|---|---|
| [#576](https://github.com/cosmosapjw-quantum/htt_base/pull/576) | OPEN | R50: repair invalid null calibration and benchmark owned Gaia tensor information | — |
| [#575](https://github.com/cosmosapjw-quantum/htt_base/pull/575) | OPEN | R49: general tilted-Bianchi programme and observational convergence (draft) | — |
| [#553](https://github.com/cosmosapjw-quantum/htt_base/pull/553) | OPEN | HTT six-paper L01/S02 [DRAFT]: real R8 T-mask spin2 pilot and source-coherent CF4 transfer bounds | — |
| [#550](https://github.com/cosmosapjw-quantum/htt_base/pull/550) | OPEN | HTT CF4 post-recovery H02/L01 [DRAFT]: full-source local auditor, 35,970 method-sky evidence and six PR3 mask gate | — |
| [#426](https://github.com/cosmosapjw-quantum/htt_base/pull/426) | OPEN | PMG-WU-005: preserve the paired-300 low-ell harmonic carrier | — |
| [#415](https://github.com/cosmosapjw-quantum/htt_base/pull/415) | OPEN | EXPLORATORY PR-315: implement joint cut-sky low-ell estimator | — |
| [#396](https://github.com/cosmosapjw-quantum/htt_base/pull/396) | MERGED | PR-313: close CF4 status provenance | fddfb7305a02efde9d6930a173f66742d1b01d64 |
| [#395](https://github.com/cosmosapjw-quantum/htt_base/pull/395) | CLOSED | PR-307: close CF4 current-stack operator | — |
| [#394](https://github.com/cosmosapjw-quantum/htt_base/pull/394) | MERGED | PR-306: close and profile the Planck PR3 low-ell operator | f69a33759869acdff78a627192c3d834d1fd67b8 |
| [#365](https://github.com/cosmosapjw-quantum/htt_base/pull/365) | MERGED | PR-257: add matched low-ell morphology benchmark | d62d63de6fdae1fbaf595ccce52b3abf532899e5 |
| [#101](https://github.com/cosmosapjw-quantum/htt_base/pull/101) | CLOSED | PR-075: constrain BiPoSH ell ranges | — |
| [#93](https://github.com/cosmosapjw-quantum/htt_base/pull/93) | CLOSED | PR-091: verify BiPoSH entry hashes | — |

계보·파일색인의 원기록은 LEGACY_CONTENT_AUDIT.json, 수송·잔차는 BIANCHI_HISTORY_RESULTS.json, 교차 부호 및 자료 응답은 CROSS_PHY_RESULTS.json, Planck grouped 검산은 CMB_GROUPED_FULL_CACHE.json, CF4는 CF4_P1_RESULTS.json에 있다.
