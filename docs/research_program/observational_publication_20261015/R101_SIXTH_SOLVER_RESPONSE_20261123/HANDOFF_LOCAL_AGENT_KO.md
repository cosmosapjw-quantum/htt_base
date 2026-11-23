# R101 이후 로컬 개발·분석 인계 프롬프트

아래 내용을 local agent의 새 작업 지시로 사용한다. 결과의 commit과 push 확인은 같은 디렉터리 `PUBLICATION_RECEIPT.json`을 읽는다. 이 파일의 `implementation_commit`이 코드·시험·연구 산출물의 정확한 출발점이다. receipt 자체를 저장하는 후속 commit은 별도로 존재할 수 있다.

---

너는 HTT/BASS 연구 프로그램의 로컬 개발·분석 담당자다. R101의 여섯 번째 이론 R1–R10·코딩 C1–C10 결과에서 이어서, SQ-CF4를 첫 실행점으로 삼고 canonical 6개 대주제·7개 교차 주제·60개 노드를 데이터 분석과 실제 native solver 개발로 진행하라. 이번 사용자는 native solver를 직접 구체적으로 개발하고 기존 legacy/BASS/REI/REC 자원을 최대한 재사용하라고 명시했다. 오래된 solver-free·외부 solver 대기 정책은 현재 지시를 막지 않는다.

## 1. 작업 위치와 권위

기존 checkout은 `/home/cosmosapjw/Dropbox/bianchi/htt_base`, 연구 branch는 `research/r69-observable-physics-bridges-20261118`이다. 기존 BASS 원 저장소는 `/home/cosmosapjw/bass`다. 새 clone·worktree·전체 복사본을 만들지 않는다. 작업 시작 시 `git status --short`, `git branch --show-current`, `git rev-parse HEAD`를 읽고 publication receipt와 비교한다. R101 시작 시 이미 320개 untracked 항목이 있었으므로 무관한 작업을 삭제·덮어쓰기·일괄 stage하지 않는다. `git add -A`, `git reset --hard`, `git clean`, force-push를 사용하지 않는다.

현재 root `AGENTS.md`, 해당 module의 `AGENTS.md`, `docs/SSOT_POLICY.md`를 따르되 R101 최상단의 owner direction이 과거의 native 금지·no-push 제약을 대체한다. 현재 연구 branch의 검증된 실질 변경은 commit/push할 수 있다. main push·merge·외부인 메시지 전송은 범위 밖이다. 모델 설정은 repo가 요구한 native delegation을 사용하되 requested setting과 provider-observed identity를 구분한다.

연구 결과 디렉터리:

`docs/research_program/observational_publication_20261015/R101_SIXTH_SOLVER_RESPONSE_20261123/`

먼저 `REPORT_KO.md`, `PUBLICATION_RECEIPT.json`, `NODE60_EXECUTION.json`, `INDEPENDENT_REVIEW.md`, `ACQUISITION_REVIEW.md`를 읽는다. 이후 현재 수행할 가지의 `CF4_THEORY_KO.md`, `SOLVER_THEORY.md`, `CHEMISTRY_THEORY_KO.md`와 실제 JSON을 읽는다. 네 선행 연구의 원문은 `prior_studies/`, 전체 legacy 카탈로그와 통합 helper는 `legacy/research_supplements_20261123/`에 있다. 동일 입력·가정·코드 identity가 유지된 근거는 재사용하고, 전체 legacy를 다시 목록화하는 작업으로 연구를 대체하지 않는다.

원 과학 SSOT는 R78 `INTEGRATED_DAG.json`이다. 60개 노드·129개 간선과 원래 42개 판정 조건을 유지한다. R101 runner의 다섯 shared job을 60개의 독립적인 과학 성공으로 집계하지 않는다. 원문 속 과거의 직접 구현 금지 stop은 current owner direction으로 대체하지만 calibrated null·source identity·물리적 admissibility 판정은 유지한다.

## 2. 이미 끝난 코드와 실제 결과를 재사용하라

`htt.infer.cf4_predictive_response`는 훈련에만 nuisance를 적합한 conditional Gaussian tangent와 shared-field selected mark likelihood를 제공한다. `scripts.r101.cf4_predictive_response --source-marks`는 실제 R100 source 자료를 읽는다. 원 8,885개 release-parent 중 고유 매칭 7,190·음의 매칭 1,695를 사용한 조건부 비교는 −11.942159→+27.341020으로 바뀌었다. 두 fitted 실험에서 zero-field log density는 −5727.256929로 같다. 이 수치는 같은 코호트·fitted selection·Gaussian 폭·다섯 radial scenario에 조건부이며 bulk-flow 발견이나 calibrated Bayes factor가 아니다.

`bass.collision.ThomsonCoherencyPropagator`와 `bass.transport.stokes_fourier.FourierStokesPropagator`는 signed I/Q/U/V를 처리한다. 기존 Mueller의 90° 선편광 부호 오류를 수정했고, rank-nine exact homogeneous/affine collision과 보존 모드를 안정화한 L-stable SDIRK2를 구현했다. FLRW Fourier streaming·collision은 공동 적분하며 zero-k/zero-opacity에 동일 이산식을 쓴다. optional Strang과 default SDIRK2의 정확도·강성 의미를 섞지 않는다.

`bass.recombination.clocked_chemistry.evolve_clocked_chemistry`는 공급한 유한 proper-time rate generator에서 점유·전자분율·광학깊이·last-scattering-bin 확률과 일곱 입력 tangent를 계산한다. `scripts.r101.chemistry_coherency`는 β=0의 공통 충돌 프레임에서 화학 응답과 exact collision을 연결한다. 이 fixture의 nonzero β 거절을 지우고 directional opacity 하나를 공통 sky depth로 쓰지 않는다.

`bass.kinetic.moving_projection`은 `V′,W′`를 포함한 exact finite linear projection blocks, memory kernel, initial hidden force를 제공한다. 복소 값을 버리던 초기 dtype을 수정했다. full auxiliary q를 유지하는 reference이며 이미 효율적인 reduced-order solver를 얻었다고 표기하지 않는다. 통계 모수 경로만 주어졌을 때 물리 generator를 발명하지 않는다.

소유자 환경의 기록은 다음과 같다.

- 조건부 five jobs 전부 exit 0, 약 8.98초.
- 범위 지정 pytest: 55 tests + 26 subtests 통과. 기존 R100 validator: 21 tests 통과/overall true. 겹치는 시험이 있으므로 합쳐 독립 시험 수로 쓰지 않는다.
- 추가 취득 도구: 최종 owner 기록 `ACQUISITION_EXECUTION_RECEIPT.json`을 따른다. default plan-only, explicit byte budget, strict HTTP framing, existing-file preservation을 검증했다.
- 실제 HYREC reference z=1150→950의 200셀: Δτ=1.7710404, Δχ=41.02159085 Mpc, k=(.03,−.015,.011)/Mpc. 시간 해상도 두 배의 최대 harmonic 변화 1.744×10⁻¹⁰. 초기 sky·원천이 지정된 조건부 수송이다.
- `RESOURCE_RECOVERY.json`: BASS/HYREC8개 파일 481,990 B가 원 SHA와 일치한다. 여섯 기준 BASS commit도 존재한다.

R100 validator는 과거 `VALIDATION.json`을 다시 쓴다. 이미 재실행 결과는 R101의 `R100_REPLAY_VALIDATION.json`에 저장하고 과거 파일을 원래 바이트로 복원했다. 동일한 전체 validator를 불필요하게 반복하지 말고 현재 수정의 위험에 맞는 시험을 수행하라.

## 3. 시작 명령과 결과를 해석하는 방법

현재 checkout에서:

```bash
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
export PYTHONPATH=.:htt:htt/src
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
.venv/bin/python -B -m scripts.r101.program science --node SQ-CF4
.venv/bin/python -B -m scripts.r101.acquire
```

첫 명령의 exit 3은 원 과학 qualification이 아직 열려 있음을 알린다. 이미 완료한 조건부 분석을 다시 계산해야 할 입력·코드 변경이 있을 때만 아래를 실행한다.

```bash
.venv/bin/python -B -m scripts.r101.program analysis --node SQ-CF4
.venv/bin/python -B -m scripts.r101.program analysis --all
```

이 runner는 R101 결과 디렉터리의 해당 JSON을 다시 쓴다. 기존 frozen 결과를 보존해야 하는 새 실험은 새 후속 결과 디렉터리와 명시적 configuration을 사용하라. 첫 분석은 현재 출판 결과와의 연결을 유지하고 변경 원인·원표·fold·모수·결과를 남긴다.

## 4. 우선 분석 A — CF4의 실제 source qualification

1. R100의 SDSS PV 원표 34,059행과 6dFGSv 원표 8,885행을 재사용한다. R101에 적힌 두 source SHA 및 matching 기준을 그대로 재현 가능한 입력으로 삼는다. 원표를 수정하여 이전 결과에 맞추지 않는다.
2. native η의 정의, comoving 거리비, catalog distance modulus, R100 bolometric template가 연결되는 식을 명시하라. fitted match probit과 과거 예시 soft cut이 서로 반대 방향으로 변하는 것을 convention 오류로 단정하지 않는다. 두 선택 사건의 모집단과 영점 계보를 분리한다.
3. 현재 fitted selection의 계수 불확실성을 joint model 또는 적절한 train/holdout scheme으로 전파하라. 그룹·calibrator·동일 simulation box는 같은 fold에 두어 leakage를 막는다. 동일 표본에서 계수를 적합하고 같은 표본의 증거로 사용하는 plug-in 효과를 정량화한다.
4. `C=N+S_PV+J_cal Σ_cal J_calᵀ+C_sel`를 source-level calibration에 연결한다. 이미 얻은 analytic m′/S′를 사용하여 covariance 변화에 의한 평균 이동과 uncertainty/volume 효과를 따로 보고한다. 독립 test에 fitted β를 다시 적합하지 않는다.
5. 전체 8,885개 매칭 패턴에서 nonunique/unmatched mark 적분을 유지하고 ambiguous matching의 별도 처리 민감도를 평가하라. 공개 6dF 내부 결과에서 CF4 전체 union selection으로 넘어가려면 방법별 parent·reject·duplication 정보를 추가로 확보해야 한다.
6. 새 결과는 독립 group holdout의 predictive density·coverage·residual과 selection/zero-point 민감도로 보고한다. source law가 아직 식별되지 않으면 식별 가능한 관측 subspace와 정확히 부족한 입력을 기록하고 다른 실행 가능 분석을 계속한다.

## 5. 우선 분석 B — 준비된 데이터 취득·다중 탐침

`DATA_ACQUISITION_PLAN.json`의 URL·크기·checksum 유무를 사용한다. existing SDSS/6dF 약20.9 MB는 다시 다운로드하지 않는다. 작은 첫 batch는 Commander noise 00000과 SDSS randoms이다. 정확한 총 product-body 예산은 887,987,911 B다.

```bash
.venv/bin/python -B -m scripts.r101.acquire \
  --ids commander_pr3_ffp10_noise_00000 sdss_randoms_v1_1 \
  --max-bytes 887987911
.venv/bin/python -B -m scripts.r101.acquire --execute \
  --ids commander_pr3_ffp10_noise_00000 sdss_randoms_v1_1 \
  --max-bytes 887987911 \
  --destination /home/cosmosapjw/Downloads/htt_r101
```

실제 실행 시 현재 디스크 여유와 기존 파일을 먼저 확인하고 stdout JSON을 새 결과 receipt로 보존한다. 프로그램은 전달받은 길이를 넘겨 읽지 않고 불명확한 HTTP framing·checksum 실패를 거절한다. checksum 없는 기존 파일의 동일 길이와 local SHA는 독립적인 provider 인증이 아니다. 충돌 파일을 자동으로 덮어쓰지 않는다.

Commander는 PR3/FFP10 signal 00000과 noise 00000의 component, unit, beam, mask, split, simulation ID를 먼저 일치시킨다. 한 쌍은 pipeline 점검이며 calibrated null ensemble은 여러 독립 쌍이 필요하다. 같은 sky의 처리 산출물을 독립 우주 realization으로 세지 않는다. PR4/NPIPE는 그 release의 관측·모의 쌍을 별도로 사용한다.

SDSS mocks 10,643,218,721 B는 box별 holdout에 사용하되 같은 box의 관측자 8개를 분리하지 않는다. 6dF reconstruction archive 17,344,070,928 B는 내부 내용이 필요한 FP/PV selection과 일치하는지 확인한 뒤 사용한다. 이것을 이미 전체 rejected-parent 자료라고 전제하지 않는다.

LoTSS 후보 tar는 355가 6,025,820,160 B, 1078이 4,507,238,400 B다. 과거 HEAD 상태를 현재 가용성으로 간주하지 않는다. 먼저 한 mosaic의 weight/RMS/내부 hole과 association을 조사하고, 외곽 support만으로 source-count likelihood를 완성하지 않는다. HTTP202는 staging 조건을 기록하고 다른 작업을 계속한다.

Gaia는 AGIS release·scan-correlated covariance와 독립 AGN photocentre control을 확보한 뒤 기존 supported rank47 subspace의 E/B 분석을 이어간다. normal-frame ρ,j,π는 독립 관측과 tetrad·단위를 확보해야 하며 constraint inversion을 독립 flux 자료로 사용하지 않는다. D01/D02/D04/D06에 확인된 URL이 없는 입력은 제공자·필요 필드·관측 사건을 명시하여 구하고, 임의 자료명·공식 checksum을 만들지 않는다.

## 6. native solver blocker — 외부 대기 대신 다음 구현을 수행하라

아래는 남은 실제 개발 순서다. 데이터 분석을 주 작업으로 진행하되 M08·M09·A03을 “external-only”로 되돌리지 않는다. 이미 있는 코드를 재사용하고 독립적인 개발 단위를 병렬화하라.

### N1. general Lie angular/screen transport

현재 `htt/bass/transport/general_bianchi_transfer.py`의 실제 `build_4d_bianchi_connection`, `integrate_polarized_geodesics`, `_spherical_screen_basis`, scalar/spin transforms와 R100 coupled background/transport builder를 읽고 사용한다. prescribed emission-map ray tracing, collisionless transfer, coupled collision evolution을 구별한다. affine source만 있는 역사적 경로를 완전한 native Boltzmann solver로 오인하지 않는다.

허용된 `(N_ab,a_a)`에 대해 Jacobi `Na=0`을 성분별로 검증하고 connection이 만드는 angular drift·screen rotation·redshift를 일관된 clock에서 이산화하라. Class B와 exceptional VI_-1/9를 처음부터 자료구조에서 허용한다. I–IX를 평탄 Fourier plane wave 한 종류로 대체하지 않는다. 특히 VIII/IX의 mode/Casimir basis와 boundary tail을 명시적으로 처리하라.

새 `stokes_fourier`의 stage inverse는 flat Fourier에서 streaming이 대각이라는 구조를 쓴다. general angular advection에서는 sparse/structured base solve와 rank-nine moment update를 구성하고 그 inverse·adjoint·conservation을 검증하라. 새로운 geometry operator가 있을 때 대각 공식을 그대로 호출하지 않는다. 정확한 행렬 크기가 작은 fixture에서 전체 dense exponential과 비교한 뒤 angular/time refinement를 하라.

수용 조건: null norm·screen orthonormality·Stokes reality, rotation/parity, homogeneous/FLRW/zero-collision limits, signed all-m의 수렴. 한 B-mode 값이 비영이라는 이유만으로 물리 chirality 또는 all-family 가능성을 주장하지 않는다.

### N2. moving electron frame과 Einstein–Boltzmann coupling

현재 rest-frame Thomson kernel에 실제 electron/baryon frame의 aberration, frequency, solid-angle/Jacobian, screen rotation을 결합하라. 단일 ray의 `(1−β·n)` 깊이를 모든 각도의 scatter-in에 적용하면 안 된다. 실제 처리하는 frequency/bolometric convention을 고정하고 zero-velocity, finite Lorentz composition, four-force exchange를 확인하라.

R100 background state와 photon/matter stress를 동일 시각에 교환하고 Hamiltonian/Codazzi 및 energy–momentum 잔차를 기록하라. frozen background의 한 step 검산과 nonlinear coupled trajectory의 검증을 구분한다. stiffness를 회피하기 위한 무근거 rate clipping이나 conservation pivot 삭제를 하지 않는다.

### N3. REC/REI/HYREC의 실제 물리 인터페이스

복구된 입력은 `data/external/r101_legacy_recovery/{bass,hyrec_atomic}`에 있다. 입력 생성 코드와 SHA는 `RESOURCE_RECOVERY.json` 및 `configs/r101/legacy_recovery.json`에서 확인한다. 원 BASS H2248은 normal-frame H이며 기존 proper-current patch는 밀도만 보정했다.

HYREC 내부에서 (i) reaction proper clock `1/(ΓH_n)`, (ii) conserved proper density, (iii) photon frequency drift/Lyα escape, (iv) matter temperature expansion과 radiation feedback을 분리하라. `H→ΓH` 전역 치환으로 끝내지 않는다. 공급된 finite positive chain의 결과를 실제 EMLA/ALI 원자율의 대체물로 부르지 않는다. legacy REC/REI를 읽어 실제 rate·Jacobian·rate history를 제공하고, FLRW FULL reference와 회복되는 극한에서 비교하라. 추가 원자/방사선 입력이 필요하면 그 필드·단위·경계조건을 명시하라.

patchy REI나 nonlinear rate가 필요하면 현재 tangent API에 total derivative를 공급하고 이벤트/셀 경계를 고정한 미분과 moving-boundary Leibniz 항을 구분하라. 양성성·수소 핵 보존·광학깊이·visibility 합 및 정상상태 극한을 함께 검사한다.

### N4. native atlas 자격 판정

실제 generator와 coupled trajectory가 준비된 family부터 mode truncation, signed all-m T/E/B/V, k/ell/time refinement와 independent FLRW/curved limits를 기록하라. legacy의 zero-Thomson/identity-streaming placeholder와 scalar Jacobi 합만 0인 시험을 통과 근거로 쓰지 않는다. 기존 VIII/IX boundary-defect와 tail-coupling 자료는 그 가정·기저가 맞을 때 재사용한다.

family별 provenance·초기조건·source normalization·clock·frame·error budget을 묶고, 같은 observed map/mask/beam 및 matched-null에 forward fold한 후 family confusion을 평가한다. emulator·surrogate가 필요하면 실제 native outputs에서 훈련하고 별도 native holdout을 유지한다. 아직 생성하지 않은 native 해를 학습했다고 표시하지 않는다.

## 7. 연구·구현의 출력 계약

각 변경에서 definition → derivation → computational form → implementation → validation 연결을 유지한다. 다음 구분을 산출물에 사용한다: established / literature-supported / derived / numerically checked / implementation-verified / conjectural / unresolved / blocked. 물리/수학 오류, 수치해석 오류, 구현 오류, runtime/접근, 입력 부족을 분리하라.

다음 결과는 후속 연구 디렉터리에 저장한다.

- 입력 identity와 현재 commit, 실제 source/output path, 실행 command·exit code·환경.
- 분석의 fitted/heldout 분리·group/box fold·source genealogy·covariance/null 가정.
- native 변경의 실제 equations, signed harmonics, constraint and conservation residuals, time/angular refinement.
- 과학 판정 조건이 닫힌 node와 여전히 열린 node; source qualification을 software PASS와 분리.
- 새로 받은 자료의 provider checksum 유무, 계산한 local digest, 정확 bytes, 재개 가능한 다음 명령.

검토에서 재현 가능한 결함이 나오면 고친 뒤 해당 위험의 시험으로 닫는다. 동일 전체 감사·빈 문서·반복 승인 절차로 시간을 쓰지 않는다. 변경은 명시된 파일만 stage하고 기존 연구 branch에 정상 commit/push한다. remote SHA와 핵심 결과·미해결 입력·다음 실행점을 보고하라. 사용자에게는 관측 분석이 무엇을 바꿨는지, solver가 실제로 어느 방정식까지 계산하게 됐는지를 먼저 설명하라.

---

최초 작업의 목표는 **SQ-CF4의 selection·calibration·holdout 분석을 진전시키고, 준비된 Commander/SDSS 자료를 분석 가능 상태로 만들며, native geometry 또는 actual REC interface의 다음 실질 구현 하나를 닫는 것**이다. 전체60 과학 노드를 완료했다는 선언을 목표로 삼지 않는다.
