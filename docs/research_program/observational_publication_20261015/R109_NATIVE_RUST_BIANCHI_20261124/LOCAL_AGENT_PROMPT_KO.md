# R109 로컬 에이전트 추가 지시문

진행 중인 작업 트리와 원자료를 보존하면서 아래 순서로 이어간다. 이 문서는 R109의 솔버 및 관측 템플릿을 로컬 데이터 분석에 적용하기 위한 추가 지시문이다.

1. htt_base의 `research/r69-observable-physics-bridges-20261118`을 fetch하고 R108→R109 변경을 확인한다. `NATIVE_MATERIAL_PINS.json`의 세 원본 SHA는 각각 별도 체크아웃으로 고정한다. 로컬 미커밋 변경이 있으면 새 worktree를 사용한다. BASS 루트에서 `cargo test --manifest-path _rustcore/Cargo.toml --locked`, `cargo build --manifest-path _rustcore/Cargo.toml --locked --release --example homogeneous_sky --example sky_covariance`를 실행한다. 최초 fetch가 끝난 환경에서는 `--offline` 사용이 가능하다.
2. Codazzi는 정상계 물리 운동량 q_i에 대해 D_j σ^j_i + κ q_i = 0으로 통일한다. `CODAZZI_FIX_KO.md`의 VI_h 재현점에서 수정 전/후의 *부호 있는 세 성분*을 보존한다. 과거의 영이 아닌 q를 가진 IC 캐시는 초기 σ, Lie 계수와 실제 q로 잔차를 다시 계산한다. 구 규약이 확인된 IC만 같은 물질 q로 다시 투영하고, 그 IC를 사용한 후속 결과에 정정 계보를 붙인다. 저장된 관측 속도의 부호를 바꾸면 안 된다. Gauss/Codazzi/Jacobi를 따로 기록한다. 고정 H의 전단·곡률 재조정 사례는 `CODAZZI_CLOSURES_KO.md`에 따라 두 제약의 종단 잔차와 선택된 배율을 재생한다.
3. 원본 BASS의 `research/r109_native_sky/NATIVE_SOLVER.md`와 `hyrec_1100/README.md`대로 초기 실행 한 건을 재생한다. 정밀 장거리 계산은 `--feedback recoil --expansion-equation gauss-reduced`에서 기준 Raychaudhuri 해와 같은 초기조건으로 교차검증한다. 전자 host의 초기 고유 수소 밀도와 H는 SI 단위, β=v/c, η=ln(a/a_emit)이다. κq에 들어가는 q의 법선 프레임, 광자 진행방향, 하늘 도래방향을 구분한다.
4. 1차 데이터 분석은 `COMMANDER_NATIVE_COEFFICIENTS.npz`의 families, angles_rad, fullsky, masked로 시작한다. 축은 [계열, 384개 자세, T/E/B, 실수 사중극 5성분]이다. ℓ≤4로 제한된 R109 템플릿의 등가 μK를 사용한다. 12개 계열의 임의 초기진폭을 관측 진폭으로 고정하지 않는다. `R108/S6`의 동일 마스크·빔·좌표와 공개된 같은 Commander 추정량을 적용한다. 방향·진폭 적합 시 동일 탐색을 보류한 모의에도 매번 실행한다. 현재 30쌍/300쌍, HM/OE 등 사용 가능한 null 범위를 결과에 표시한다. 기존 다운로드 중단 지시와 외장 저장소 선택을 존중한다.
5. 편광 파워를 비교할 때는 `modes.tsv`의 모든 부호 m을 사용한다. 한 배경의 결정론적 a^X_lm a^{Y*}_lm, m평균 C_l, 명시적 확률법칙의 K를 구분한다. 균일 SO(3) 또는 경험 가중치가 필요한 경우에만 sky_covariance에 그 법칙을 전달한다. signed TE/TB/EB를 유지한다. 전체 전달에 필요한 높은 ℓ에 대해서는 고정 초기조건에서 시간, μ, φ, ℓ_max를 독립적으로 세분하며 B의 절대 바닥을 보고한다. VII0의 작은 B에 특히 주의한다.
6. 임의 Bianchi 기하는 `--lie-ic`로 Σ,N,A를 주고 Na=0, trΣ=0, Ω>0 및 Codazzi가 요구하는 물질 운동량의 실현 가능성을 먼저 검산한다. 전단/tilt/observer orientation을 각각 바꾸어 template 응답을 분해한다. VI_−1/9의 불가능한 flux 성분, VIII의 일반 비대각 사례, I의 서로 상쇄되는 tilt를 각각 보존한다. 특이점 또는 H=0에 접근하면 이 코드의 팽창시계가 끝나는 물리적 위치를 보고한다.
7. REC/REI 물질 이력 6개는 `MATERIAL_BRIDGE_KO.md`의 한 명령으로 재생한다. `hyrec_1100`은 재결합 잔류 전자만 공급한다. donor REI z=20→4를 z=0까지 잇고 싶으면 z=4 restart에 맞는 저적색편이 광원·SED·흡수체·UVB를 입력하고 H/He·광자 재고와 시간축을 확인한다. 독립적인 두 기하의 τ를 이어붙여 물리적 EE를 공표하지 않는다.
8. CF4는 `MANTICORE_ROUTE_KO.md`의 실제 수신 경로 및 자료 계보를 쓴다. 은하단 LOS의 같은 SampleID끼리 비교한다. CF4 군에 임의로 보간할 Manticore 3차원 posterior는 원본 field.h5를 검증한 뒤에만 세며, 다른 C15/PVHub 장은 별도 민감도 대조다. `NODE_CROSSWALK.json`의 부모/관측 입력이 갖춰진 노드별로 수치 결과·표본·SHA·잔차를 기록한다.

로컬 보고에 넣을 것은 (a) 실제 사용한 네 SHA와 입력 파일 해시, (b) 관측 창·프레임·추정량, (c) 실행한 시간·각도·ℓ 및 물질/자세 대조, (d) 실제 비교치와 불확도, (e) 잔여 물리 입력이다. 산출물과 실행 코드를 같은 연구 브랜치에 커밋하고 remote HEAD를 확인한다.
