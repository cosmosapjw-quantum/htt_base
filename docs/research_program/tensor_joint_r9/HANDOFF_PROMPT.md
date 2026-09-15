# R9 revision 2 handoff — depth obligations and moving-q stability

저장소 `cosmosapjw-quantum/htt_base`, 브랜치
`implementation/project-catalog-20260912`를 이어서 작업하라.
기존 intake/adapter 구현은 `9e9539edcdbd7bbf66e458cdce685c7a112f8a04`에서 시작했고,
실제 다중 깊이 실행은 `c532862651235ed0586a0677b61a43b2e09b3c85`에서,
이번 선택·보정 입력 continuation은 사용자가 확인한
`51ed1e913ac358f9a2569fce8ccb5dc3c1650305`에서 시작했다.
이번 고정 ambient STF 수치 비교는 `af5fe14a60658ff7926e58ea512bd3014aeba2ba`를 이어서 수행했다.
이 인계 파일을 포함하는 전달 커밋을 다음 immutable starting point로 고정하라.
R9 revision 2를 계속하며 R10 또는 새로운 과학 프로그램으로 초기화하지 마라.

## 현재 mathlib continuation — 2026-09-15

사용자의 Continue에 따라 동일 work unit R9-DEPTH-MATHLIB-20260914를 이어간다.
현재 설치된 공용 mathlib fabf563a7c95a166b8d7b6efca11c8b4dc9d911f와
Lean v4.31.0 캐시 연결이 실제로 성공했다. 기존 core 전용 manifest는 유지한다.
`revision2/depth_formal/mathlib/README.md`와 `COMPONENT_STATUS.json`을 먼저 읽어라.

`formal/R9Depth/Recursion.lean`에서 이종 블록 역방향 합성, 양방향 동치와 임의
직사각 실수 행렬 specialization이 컴파일됐다. `Covariance.lean`에서는 D1의 실제
기댓값·전체 HCHᵀ·실수 PSD 및 네 교차 블록 항을 일반 차원에서 컴파일했다.
이는 기존 정리의 형식화이며 새 수학 정리로 세지 않는다. 독립 검수 판정은
COMPONENT_STATUS와 검수 원문에서 확인하라.

FORMAL_DEPTH는 아직 BLOCKED다. **다음 단일 의무는 D3의 flattened block-linear
map과 determinant/kernel/full-law bridge**다. 그 뒤 D2의 특이 지지집합·의사역행렬
χ² 법칙과 D4의 전체 과거 조건부 Gaussian·innovation 독립성을 형식화해야 한다.
확률 라이브러리가 전부 없다는 이전 설명은 현재 상태가 아니다. 설치된 Gaussian
map/independence 정리는 사용 가능하지만 전체 필요한 연결 증명은 아직 없다.
사용자는 FORMAL_DEPTH 해제 뒤에 16개 연구 묶음을 진행하도록 지시했다.
기존 MQ1/MQ2를 다시 실행하거나 새 발견으로 세지 말고, 이 선행 조건을 생략하지 마라.

이전 child continuation hook 거부는 보존했고 Host가 현재 증명을 작성했다.
새 독립 검수 depth_mathlib_review는 launch cl_617136dbc88895e44bec01b87c3a18fd로
등록·요청했으나 `GLOBAL_HOOK_IDENTITY_OR_STATE_UNVERIFIED:CHILD_BINDING_MISSING`으로
최종 중단 응답을 반환했다. 종료 시 검수 보고서와 성공한 재컴파일 2건도 발견됐다.
Host가 소스/hash/trace를 확인했으나 result의 launch_id는 null이고 실행 근거는
self_declared다. 양쪽 기록을 보존하며 독립 검수 수용은
BLOCKED_AUTHENTICATION_UNVERIFIED로 둔다. 보고서의 fail은 D3/D2/D4 전체 의무가
미완료라는 뜻이며 통과한 보조정리의 반례가 아니다.
동일 작업의 검수 1회 예산을 소진했고 우회·새 이름 재시도는 하지 않았다.
다음 실행은 현재 client binding/lifecycle을 복구한 뒤 정확한 증명 검수를
재개하는 것이다. 그 뒤 위 D3 잔여 의무를 진행하라. 현재 실행 신원과 네 축 수용은 별도 상태다.
관측 입력 확보 보류, 기존 모든 HOLD와 예산, 원본 실행 증거를 유지한다.

## 2026-09-14 우선 적용 continuation

이번 작업은 기준 bc5e028d16c10a8a60080a59f5cd6adaf7595238와 동일한 HEAD에서
시작했다. 이후 변경을 보존하고 R9 revision 2를 유지한다. 사용자 지시에 따라
**추가 관측자료 확보·요청·기존 확보 시도 반복은 보류**한다. 아래의 외부 입력
목록은 남은 의무 기록이며 이번 세션의 실행 지시가 아니다.

R9-02.depth의 D1/D3/D2/D4를 명제별 현재 계약으로 연결하고 각 네 축을 실제
`run-adjudicate`로 실행했다. 원시 판정은 네 명제 모두 CAS_FAIL이고, 일반 증명
의무가 남아 FORMAL_DEPTH는 BLOCKED다. 반례 발견을 뜻하지 않는다.
`revision2/depth_formal/OBLIGATIONS.md`, `ADJUDICATION.md/json`과 원시 실행을 읽어라.
Lean core에서 이종 블록의 residual-after-reconstruction 한쪽 합성이 컴파일됐지만
반대 합성, 실수 covariance/PSD와 전체 Gaussian 법칙은 남았다. 현재 Mathlib
import는 실패한다. Wolfram/Sage 결과 요약의 등록 스키마 오류도 보존했다.
엔진 실제 실행, 유효한 result envelope, authenticated lifecycle을 구분하라.
현재 연구 run은 NON_PASS다. 두 result 스키마 오류로 normal close가 거절됐고,
원본·오류를 보존한 채 정확한 local active pointer만 정리했다.
`.agent-harness/runs/R9-THEORY-20260914/CLOSEOUT.md`가 범위별 판정을 연결한다.

같은 ambient 좌표계의 uncertain-q fibre에 대해 MQ1/MQ2를 직접 유도했다.
두 fibre가 모두 비어 있지 않을 때, A=3√(2/5), ε=||q−q′||F+||v−v′||2로 두면
전역적으로 dH≤2Aε+√(2A)√ε다. 두 η≤1−δ인 내부에는
Cδ=A[2+√((1−δ)/δ)]의 Lipschitz 상계가 성립한다. 중심·사영·반지름의 변화를
분리하며 전역 kernel 기저는 가정하지 않는다. η<1/η=1/η>1, 원시 Q의 양의
진폭 하한과 Q=0 분기를 구분한다. 기존 fixed-q 경계 예로 지수 1/2의 sharpness와
δ^(−1/2) 차수를 확인했으며 이를 새 반례로 세지 않았다.

`revision2/moving_q/RESEARCH_NOTE.md`, `REVIEW.md`, `PR_DELTA.md`를 읽어라.
새 합성 360쌍 검사와 독립 derivation/diff 검수는 scoped PASS다. 유한 방향 표본은
거리의 lower witness이며 해석적 증명이 전체 상계를 준다. 네 축 admission,
관측 coverage 또는 물리 응답으로 승격하지 마라. 원문 끝의 pending-review 표기는
검수 당시 고정된 문구이며 별도 REVIEW.md가 현재 판정을 기록한다.

다음 단일 작업은 pinned Lean core에서 **이종 블록 역방향 재구성 합성**을 증명하는
것이다. 기존 `DepthCore.lean`과 실패 로그에서 이어가라. 이 보조정리만 통과해도
D3 전체·FORMAL_DEPTH는 미수용이며 실수 행렬/전체 법칙과 D1/D2/D4 의무가 남는다.
완료된 DESI/SDSS/CF3/fixed-ambient 실행은 변경 없이 재실행하지 마라.

## 먼저 읽을 현재 상태

1. `AGENTS.md`와 관련 repo skills, canonical `docs/codex_handoff/pr_backlog.yaml` 및 `pr_status.yaml`.
2. 이 디렉터리의 `RESEARCH_STATE.json`, 고정 `REVISION_SPEC.md`, `campaign_dag.json`.
3. `revision2/harness_activation/STATE.md`, `CODING_CONTRACT.md`와 `revision2/implementation/CONTRACT.md`.
4. `revision2/selected_law/README.md`, `input_inventory.json`, `final/result.json`, 실행·검수 기록.
   이어서 `revision2/multidepth/README.md`, `analysis.json`과 이전 실행·검수 기록.
5. 이전 `revision2/implementation/REVIEW.md`, `reference_comparison.json`, `desi_product_final.json`.
6. `revision2/ambient_fibre/README.md`, `comparison.json`, `PR_DELTA.md`와 독립 수치 검수.
7. `revision2/THEORY_EXTENSION.md` D1–D4/F1–F3와 `MODEL_TO_DATA.md`의 제품 조건.

## 원본 하네스

GPT-6 Astra v4.0.0의 두 원본 ZIP을 이번 구현에서도 등록 SHA256과 모든
vendor member bytes로 재검증한 c532 evidence를 유지한다. 이번 continuation에서도
51ed 단계의 두 ZIP 등록 SHA256 검증과 관련 core/phase 적용 증거를 유지한다.

- 연구: `harness/archives/physmath-research-harness-gpt6-astra-v4.0.0-20260908.zip`
  SHA256 `dae76c90f2e5d691bcdd595dadbe470bacacba3bb2a036ff9788ffe7d3bfabb7`.
- 코딩: `harness/archives/physmath-coding-harness-gpt6-astra-v4.0.0-20260908.zip`
  SHA256 `dc99e7ab2f9629dcce3ec0758d97e19acc5b645f86e208d1b338bb6430ff8d7a`.

각 vendored `START_HERE.md`와 연구 `PROJECT_INSTRUCTIONS.md`, 코딩 `AGENTS.md`를
읽어라. 패키지 state는 NOT_RUN 템플릿이다. 원본/과학 기준/기존 evidence를
템플릿으로 덮어쓰지 마라. 원본이 없거나 hash가 다르면 하네스 적용은 BLOCKED다.
패키지 선택은 runtime 모델 신원이나 성능, authenticated hook/profile 증거가 아니다.

## 현재 실제 구현과 실행

- `common.depth_path.DepthRepresentation`, `common.r9_product`가 고정 feature 순서,
  전체 covariance, 공통 state incidence와 제품 processing identity를 보존한다.
- `htt.infer.r9_depth_law`는 현재 브랜치의 R7 `JointObservationLaw`에 직접 연결된다.
  r=HY, V=H C Hᵀ의 교차 단계 항을 유지한다. HTT 법칙은 Y 또는 (Y0,HY)만
  허용하며 평균/Jacobian/전체 covariance도 같이 변환한다. MIO 차분은 진단이고
  독립 likelihood가 아니다. 임의 block 크기, 누락 covariance, fitted law,
  완전 중복/지지집합, 공통 모드, 실제 공유 nuisance와 full-past conditioning을 검증했다.
- `htt.infer.r9_confidence_image`는 공통 state–jet–anchor coverage 사건을 요구한다.
  실제 region, covered variables, coverage target/procedure/evidence와 prospective
  allocation이 없으면 물리 신뢰집합 사상은 unavailable이다. 별도 95% 영역을 붙이지
  마라. point coverage로 full identified-set coverage를 주장하지 마라.
- `common.tensor_functionals.fixed_contraction_support`는 고정된 3×7 contraction의
  수치 support/witness helper다. uncertain q는 joint inverse image를 요구한다.
  오차 범위 내 eta=1 경계는 unresolved이며 certified physical bound가 아니다.
- 준비된 DESI DR1 BGS syst qiso HDF5 하나를 새 runner로 읽고 alpha=1/80의
  조건부 신뢰구간과 100000 Gaussian-summary mocks를 실행했다. 원 자료는 한 scalar
  block이므로 `NO_DEPTH_CONTRASTS`다. 실제 multi-depth covariance를 만들지 않았다.

재현 명령 (출력은 반드시 새 경로):

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=htt/src:htt:htt/htt python3 -m pytest -q tests/r9 htt/src/common/test_r9_depth_path.py htt/src/common/test_r9_tensor_functionals.py
/mnt/sn850x2t/htt_base_e2e/workdir/external_fusion_round3_20260722_envs/lowell/bin/python scripts/observed_runs/run_tensor_joint_r9_product.py --input /mnt/sn850x2t/htt_base_e2e/workdir/raw/desi_dr1_fullshape_bgs_bright_v1.2/likelihood/likelihood_bao-recon_syst_BGS_BRIGHT-21.5_GCcomb_z0.1-0.4.h5 --output /tmp/r9-desi-fresh.json
```

원본 `revision2/run_checks.py`는 고정 evidence 경로를 덮어쓴다. 이번에는 원 소스의
별도 디렉터리에서 그대로 실행했고 raw stdout/stderr/exit을 `implementation/baseline*`에
보존했다. 재실행도 복사본을 사용하라. 기각 횟수와 원래 assertion은 재현되지만
SVD 기준벡터의 자유도로 random-coordinate fibre support 값은 환경 간 동일하지 않았다.
허용오차를 변경하지 않았으며 이를 exact fibre-target replay PASS로 부르지 마라.

## 실제 SDSS PV 다중 깊이 경로

전체 2,048개 mock / 256개 box 실행과 관련 테스트 25개가 통과했고, 같은 독립
검수자가 최종 저장 벡터의 수치 재계산 및 영점 퇴화 수정 검수를 완료했다.
현재 수용 범위는 release feature diagnostic이다. 실제 선택 관측법칙과 물리
state–jet–anchor coverage는 unavailable이며 과학적 HOLD를 승격하지 않는다.


`revision2/multidepth/README.md`와 실행기가 읽는 `analysis.json`이 이번 제품과
추출 절차를 정의한다. 공식 v1.1.0 release의 `logdist`를 네 누적 redshift 창에서
9개 angular feature로 추출한다. 같은 전체 mock 카탈로그에서 36성분 Y와 각 창의
응답을 함께 다시 적합하고, simulation box 단위로 학습·평가를 분리한다.
전체 sample Cjk, mean/response, HCHᵀ와 초기 Y0를 포함한 변환을 저장한다.
최종 실행 상태와 수치는 `revision2/multidepth/final/result.json`을 소비하라.

공개 mock의 반복 ID는 서로 다른 행을 가리킬 수 있다. source ID와 행 번호를
보존하며 ID 중복만으로 행을 버리지 마라. 공통 additive eta 영점은 36개 shell
계수와 함께 37차원 state에 들어가며, 36차원 관측 응답의 정확한 퇴화를 유지한다.
계수는 dex 단위의 현상론적 log-distance feature다. 물리 velocity/shear/Q/O 또는
local boost/global tilt 응답으로 바꾸어 읽지 마라.

이 경로가 추정하는 것은 release feature의 전체 covariance다. 원시 은하 covariance,
확정 Gaussian 법칙 또는 survey coverage가 아니다. `logdist_corr`의 group-richness
보정, CF3 영점 보정, 관측 자료로 조정한 선택·FP·오차 생성기의 전체 반복이 없다.
이 입력들을 확보하기 전에는 `ESTIMATED_REQUIRES_CALIBRATION`을 유지하고,
HTT Gaussian inversion이나 p-value를 생성하지 마라. 현재 alpha 소비는 0이다.

## 공개 선택·보정 입력 continuation

`htt.infer.sdss_cf3_calibration`과 `run_sdss_cf3_calibration.py`가 공개 CF3 table3의
PGC를 실제 SDSS 행에 연결한다. 공통 296행에서 공개 TF tracer H/I 규칙으로
PGC 39712, 59838을 제외한 294행의 진단 영점을 계산했다.
flat Ωm=0.31, H0=75와 명시된 luminosity-distance 변환/개별 폭 가중에서
delta=+0.00043862234757611747 dex다. 이는 표준오차·신뢰구간·공식 그룹 보정의
재현 결과가 아니다. 원저자의 변환·가중 코드와의 수치 일치도 미확인이다.

보정과 깊이 관측이 같은 SDSS 행을 사용하는 의존성을
`G=[M,0]+(M1)lᵀ`로 보존한다. 전체 입력 covariance가 주어지면 `G C_joint Gᵀ`를
사용해야 하며 교차 항을 지우지 마라. 현재 C_joint는 unavailable이다.
공통 영점은 H contrast에서 소거되고 초기 Y0에 남는다. 관측값을 직접 다시 적합한
결과와 operator 경로를 비교했다. 기존 SDSS feature 결과와 DESI 실험은 그대로 유지한다.

Tempel 2017의 공개 584,449행에서 objID로 SDSS 33,641행을 연결했고 그룹 ID·richness는
모두 일치했다. 미연결 418행과 CF3 전체 보정 은하에 대한 group crosswalk는 남아 있다.
정확한 대응 없이 sky 근접이나 같은 halo mass를 그룹 identity로 사용하지 마라.
공개 mock의 FP 참값·관측값·오차도 최종 선택된 행에만 있으며 선택 전 모집단은 아니다.

관련 구현 테스트 35개와 실제 공개 자료 연결 실행이 통과했고 독립 검수에서 차단 결함이 없었다. 검수 상태는
`RESEARCH_STATE.json`의 `selected_law_connection.review_status`를 소비하라.
selected law, 전체 upstream refit, 물리 응답과 공통 coverage는 계속 unavailable이다.

## 보존된 관측 입력 의무와 HOLD — 이번 세션 확보 보류

R9-03/05와 R9-24/25의 **scoped implementation**이 실자료/형식적 capability를
승격하지 않는다. R9-24 `FORMAL_DEPTH`와 R9-25 적격 CF4/JWST/CMB의 실제 전체 깊이
법칙이 여전히 필요하다. 다음 핵심은 SDSS PV의 선택 전 parent population과
FP 생성·적합 코드, group-richness correction 및 CF3 group-level calibration을
확보해, 자료로 추정하는 단계들을 같은 전체 모의자료 안에서 반복하는 것이다.
이번 공개 CF3 개별 연결로도 공식 292-group 보정, richness-bin FP refit, 원시 선택법칙은
완성되지 않았다. `input_inventory.json`의 남은 입력부터 확보하라. 원 논문이 요청 자료로
명시한 exact SQL/supersets, 생성·적합 코드, 수정된 창과 fitted spline, CF3 그룹 대응·공유
anchor law가 필요하다. 준비된 stage를 같은 전체 모의자료에서 반복하라.
현재 release feature replay의 mean/C/창 응답은 그 입력 확보를 대체하지 않는다.
기존 R9-03/05 adapter 구현을 다시 시작하거나 DESI scalar를 반복 실행하지 마라.
물리 image는 동일한 calibrated state–jet–anchor 사건이 갖춰져야 한다.

Fibre 비교는 동일한 **ambient STF 방향** a와 q,v를 먼저 고정해 실행했다.
두 기존 Python/NumPy 환경과 35개 기저 표현에서 support=0.9745422070448619가
일치했다. Cartesian reference와의 최대 support 오차는 4.45e-16 미만,
ambient witness 오차는 7.90e-16 미만이며 허용오차 1e-10을 유지했다.
`revision2/ambient_fibre/comparison.json`과 독립 검수 결과를 소비하라.
이것은 새 고정 target의 유한 수치 비교다. 원래 난수 ambient target은 복구하지
않았고, 이전 두 서로 다른 target의 결과와 원본 evidence는 그대로 보존했다.
임의 기저에 대한 증명, 불확실 q, 경계 인증, 네 축 CAS나 물리 coverage가 아니다.
같은 SVD-coordinate 난수 seed만으로 같은 target을 정의했다고 보지 마라.

이전 bc5e028d 시점에는 R9-02의 명제별 CAS 계약과 네 축 실행이 미완료였다.
현재는 위의 depth_formal 실행·판정이 그 readiness 상태를 갱신한다. 아래 기록은 이전 상태다.
이번 readiness map은 pinned Lean 4.31 core와 SymPy 실행을 확인했고,
mathlib는 현재 formal 프로젝트에 설정되지 않았다. Sage-to-Singular probe는
30초 안에 끝나지 않아 NOT_MEASURED다. 별도 실행 파일은 대소문자를 구분하는
`/usr/bin/Singular`에 있으므로 소문자 `singular` 검색 실패를 미설치로 읽지 마라.
계약/도구 준비 자체는 formal admission이 아니다. 과거 R8 계약을 대입하지 마라.

기존 R8 STOP_INVALID, 25 unresolved pools, CF4 quarantine, PR4 skip,
production/empirical/novelty/four-axis HOLD와 R9-REV2-20260912의
NOT_A_WHOLE_CURRENT_RUN_PASS를 그대로 보존한다. 이전 증거를 재실행으로 덮지 마라.
CF4 quarantine 수치 재사용 금지; JWST 위치 match는 물리 identity가 아니다.
DESI는 같은 release 조건부 law, Union3는 approximate scenario다.

Family alpha=1/20, CMB/CF4/distance-calibration/DESI 각각 1/80,
CMB 내부 두 항 각각 1/160이다. 빠진 제품의 alpha를 재배분하지 마라.
새 depth 점수는 기본 진단이다. co-primary 변경은 제품 예산 안의 사전 분할과
전체 scan calibration을 요구한다. 같은 하늘/좌표변환/깊이 점수를 중복 곱하지 마라.
관측 Q/O, beta_RO, global matter tilt와 physical sigma/omega를 구분하라.
Native Boltzmann solver를 구현/시뮬레이션하거나 Bianchi family를 주장하지 마라.

Subagent 시작 전에 실제 worktree의 context pack과 등록 assignment를 사용하라.
이번 독립 수치 검수와 입력 map의 launch authentication은 미확인이다. 등록 result의
직접 검증과 scoped review를 authenticated lifecycle 또는 네 축 CAS로 승격하지 마라.
사용자가 local 검증 후 push 전후 별도 worktree/clone 재검증을 생략하도록 지시했다.
현재 worktree에서 필요한 검증을 마치고 단계별 commit/push 후 원격 ref를 확인하라.

전역 Codex runtime authority는 현재 `3379cc219ed6b5e44a2b50d7224324a89fdf77ab`다.
80df의 opaque spawn-message 거부 후 3379의 exact-task-name fallback을 적용했고,
이전에 거부된 동일 등록 작업의 native 실행을 재개했다. 공식 installer 재적용은
GLOBAL_POLICY_UNCHANGED였으며 hook 5개의 현재 hash 신뢰/활성 설정을 공식
app-server config API로 저장했다. 사용자에게 /hooks 승인과 reload 권한을 받았다.
`reloadUserConfig=true`는 임시 app-server에 요청됐지만 현재 데스크톱 스레드의
reload와 새 authenticated lifecycle event는 확인되지 않았다. 승인 저장, 실행 재개,
실행 중 클라이언트 reload 상태를 구분하라. 이 단계 local model dispatch는 0회다.
기존 0f4/0b6022/80df receipts와 거부 기록, frozen budgets는 유지한다.
전역 runtime 적용은 과학 하네스 ZIP 적용이나 과학적 admission과 별도다.
