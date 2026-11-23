# 로컬 에이전트 인계 프롬프트

아래 지시를 기존 htt_base 연구 체크아웃에서 수행하라. R103은 R102 `664845022a9600ad925d6c1332143395aac5ed90`의 후속이다. 우선순위는 실제 자료 분석이며, 독립적으로 드러난 solver 오류는 재현하고 식과 코드 양쪽에서 고쳐라.

## 출발점

```bash
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
branch=research/r69-observable-physics-bridges-20261118
git fetch origin "$branch"
git status --short --branch
git rev-parse HEAD FETCH_HEAD
export PYTHONPATH=.:htt:htt/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1
run_dir=$(mktemp -d "$HOME/Downloads/htt-r103-analysis-XXXXXXXX")
report_dir=docs/research_program/observational_publication_20261015/R103_SOLVER_SOURCE_CONTINUATION_20261123
.venv/bin/python -B -m scripts.r103.program --node SQ-CF4
```

기존 연구 브랜치에서 출발하라. 로컬 HEAD가 뒤처진 경우 작업 중인 파일을 보존하면서 fast-forward 가능한 커밋만 반영하라. 기준은 R78의 60노드·129간선과 42개 원래 수용 조건이다. `NODE60_EXECUTION.json`의 각 행에서 상위 의존성과 실제 근거·다음 행동을 확인한다.

### 1. SQ-CF4와 독립 속도장 후보

```bash
.venv/bin/python -B -m scripts.r103.cf4_shared_field_holdout --output "$run_dir/cf4.json"
.venv/bin/python -B -m scripts.r103.p1_joint_patterns --output "$run_dir/p1.json"
.venv/bin/python -B -m scripts.r103.manticore_cf4_pv geometry
```

6dFGSv 8,885행의 PGC·PGC1 연결, 다섯 홀드아웃의 개별 점수, 군 적색편이 대체에서 결론이 유지되는지 보고하라. 첫 실행의 R102 재현값과 표본 해시를 비교한다. Manticore-Local의 2M++ 제약 z=0 속도장을 이용하려면 `PV_FIELD_PLAN.json`의 패키지 버전·릴리스·객체 목록부터 확인하라. 2개의 실제 필드를 다음처럼 축약할 수 있다. 전송 불가 시 공급자 응답을 기록하고 Gaia/Commander로 진행하라.

```bash
field_dir="$HOME/Downloads/htt_r103/manticore"
.venv/bin/python -B -m scripts.r103.manticore_cf4_pv fetch --indices 0 1 --directory "$field_dir" --max-bytes 800000000
for frame in simulation relative-to-grid-observer; do
  .venv/bin/python -B -m scripts.r103.manticore_cf4_pv reduce --files "$field_dir"/manticore_local_00[01].h5 --frame "$frame" --output "$run_dir/pilot_$frame.npz"
done
```

파일럿 2개로 얻는 36차원 표본공분산의 최대 rank는 1이다. 각 실현·frame·격자 원점 규약(0, −0.5)과 공통 압축행렬을 고정한 뒤, 공급자 목록의 고유 실현을 늘려 공분산 고유값과 유효 표본수를 비교하라. 2M++–CF4 추적자 중복, CF4 선정 실패 표본, 독립 영점 및 같은 창의 상관 PV를 각각 조사하라. Hartlap 보정 등 정밀도 행렬의 보정은 표본 독립성과 분포 가정부터 확인한다. 예상값·필드 불확실성과 무조건부 PV 분산을 단순 합산하면 같은 물리를 두 번 셀 수 있다.

### 2. Commander PR3 실자료

```bash
.venv/bin/python -B -m scripts.r103.commander_ensemble plan --plan-json "$run_dir/commander_plan.json"
export OMP_NUM_THREADS=4
.venv/bin/python -B -m scripts.r103.commander_ensemble reduce --start 0 --stop 1 --lmax 64 --output-dir "$run_dir/commander"
.venv/bin/python -B -m scripts.r103.compare_commander "$run_dir/commander/commander_pr3_00000.json" --output "$run_dir/commander_replay.json"
.venv/bin/python -B -m scripts.r103.commander_ensemble reduce --start 1 --stop 2 --lmax 64 --scratch "$run_dir/tmp" --output-dir "$run_dir/commander" --max-download-bytes 603987840
export OMP_NUM_THREADS=1
```

위 바이트 예산은 기존 신호 00001을 재사용하고 noise 1개를 받는 경우다. 그 뒤 실제 `plan`을 보고 연속 구간과 전송 상한을 정하라. 원본은 읽기 전용으로 재사용하고, 새 스트리밍 파일은 쌍별 축약 후 임시 경로에서 해제된다. 입력·마스크 SHA와 모든 서명 있는 TT/EE/BB/TE/EB/TB를 저장한다. 이미 계산한 `output-dir`으로 재개할 수 있다. 300개의 독립된 noise 실현과 corresponding CMB 실현이 필요하다. 동일한 쌍의 재조합은 독립 실현 수를 늘리지 않는다.

관측 통계량의 calibration 전에 release-specific 유효 빔·픽셀창, intensity/polarization mask, foreground 처리와 통계량의 관측자 프레임을 동결하라. 관측 맵에만 beam HDU가 있다는 사실만으로 raw MC가 무빔이라는 결론을 낼 수 없다. 공식 릴리스에서 유효 응답을 확인한 후 공통 전달함수 처리와 holdout/injection coverage를 실행한다. PR4 Commander는 해당 릴리스의 별도 자료·전달함수에서 처리한다.

### 3. Gaia, NVSS와 교차 관측량

```bash
.venv/bin/python -B -m scripts.r103.gaia_frame_curvature --output "$run_dir/gaia.json"
.venv/bin/python -B -m scripts.r103.radio_selection --output "$run_dir/radio.json"
```

Gaia에서 48개 동일 하늘 패치의 delete-one과 모든 1,128개 delete-two 결과, E/B별 잔차, 가장 영향 큰 패치를 보고하라. 634,233개 소스의 해시가 고정된 정상방정식을 사용했다. 적색편이에 affine인 공통 프레임은 제거되지만 비선형 AGN·스캔 성분은 남는다. NVSS에서는 peak/integrated 선택을 같은 소스와 flux에서 재현하고 completeness·형태 및 LSS를 포함한 추가 공분산을 실제 자료와 대조하라. 나머지 PHY-01…07의 구체적 물리량과 입력은 `CROSS_ROUTE_BOUNDS_KO.md`와 노드별 조치를 따른다.

### 4. Solver의 다음 분석과 개발

```bash
.venv/bin/python -B -m scripts.r103.native_moving_check --workers 3 --cells 48 --ell 6 --picard 3 --output "$run_dir/native.json"
.venv/bin/python -B -m scripts.r103.massless_neutrino_check --workers 3 --cells 48 --N-eff 3.044 --output "$run_dir/neutrino.json"
.venv/bin/python -B -m scripts.r103.rec_rei_result --out "$run_dir/rec.json"
ref_dir=/home/cosmosapjw/workdir/htt_external_physics_20261015/reference_code
.venv/bin/python -B -m scripts.r103.signed_reference --anilos-root "$ref_dir/AniLoS" --aniclass-root "$ref_dir/AniCLASS" --output "$run_dir/reference.json"
.venv/bin/python -B -m scripts.r103.closed_tensor_history --aniclass-root "$ref_dir/AniCLASS" --output "$run_dir/closed_tensor.json"
.venv/bin/python -B -m scripts.r103.high_tilt_quadrature --output "$run_dir/tilt_angles.json"
rei_repo=/home/cosmosapjw/Dropbox/bianchi/rei_bianchi
rei_ref=56dc609ea9b801c88d3364aed3eee140b3a20d46
rei_path=research/rei_igm_sync_20261116/approximation_validity/incremental_fifth/results_five
git -C "$rei_repo" show "$rei_ref:$rei_path/five_case_abundances.csv.gz" > "$run_dir/five_case.csv.gz"
.venv/bin/python -B -m scripts.r103.rei_five_case_optical "$run_dir/five_case.csv.gz" --output "$run_dir/rei.json"
```

- **격자와 물리 closure.** 같은 VIIh·VI₋₁/₉·IX 초기조건에서 시간 간격, `ell_max`, Gauss–Legendre 각격자와 Picard 반복을 한 축씩 세분하라. `GeneralLieStokesOperator(L,n_gl_theta=...)`를 결합 solver의 `lie_op` 인자로 전달할 수 있다. `q/E`를 유체 방정식 및 sky dipole 양쪽에서 직접 계산하고, 종별 `π/E`, 광자–바리온 힘의 합, Hamiltonian·Codazzi와 함께 저장하라. 고속 $|\beta|=0.90554$ 고정 하늘에서는 32링이 처음으로 상대오차 $10^{-8}$에 도달했다. 다른 분포·속도에서는 각격자 세분화로 필요한 해상도를 측정하라. 제약식 잔차만으로 각운동량 수렴을 판정하면 flux 오류를 놓친다.
- **독립 해.** AniLoS/AniCLASS와 공통의 곡률 부호·handedness, 등각 거리, 초기 regular mode와 진폭, 각기저와 B 부호, `Ωγ, Ων, Tγ` 정규화 및 opacity/source 이력을 맞춰라. 소스 시계열과 복소 `a_lm`을 먼저 비교하고, 차이가 남으면 최초로 어긋난 방정식/시각 및 최소 재현 입력을 남긴 뒤 그 경로를 수정하라. 동일한 결정론적 초기조건의 외부 해를 구현 비교의 기준으로 사용하라.
- **재이온화.** REI 출력의 관측자는 평균 적색편이 4이다. `20→4` 구간의 결과를 오늘까지 연장하려면 `4→0`에서 연결되는 물질 이력과 경계값이 필요하다. 공통 단위·He 분율·광학깊이 누적 방향을 확인하고 유한 셀 전송 확률을 합산하라. Sobolev 기울기가 0을 지나는 모델은 다중 공명 수송을 별도 구현해 대조하라.
- **귀속.** 공통 beam·마스크, 소스 매칭, held-out 잡음 calibration과 주입 회수까지 갖춘 경우에만 family confusion과 물리적 초과확률을 산출한다. 현재 원자료에 없는 `physical_Pi`, `physical_GF`, 계열 귀속은 미정이다.

회신에는 실행 커밋, 명령, 최초 실패 입력, 실제 반환 코드, 중요 원자료 SHA, 코드·환경, 실행 시간과 메모리, 관측 통계·수치 잔차의 단위를 포함하라. 완료된 분석과 원자료가 추가로 필요한 노드를 `NODE60_EXECUTION.json`의 ID에 연결하고 새 검증물만 같은 연구 브랜치에 푸시하라.
