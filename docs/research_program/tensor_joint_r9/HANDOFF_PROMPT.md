# R9 revision 2 handoff — implemented intake and complete covariance adapter

저장소 `cosmosapjw-quantum/htt_base`, 브랜치
`implementation/project-catalog-20260912`를 이어서 작업하라.
이번 구현은 `9e9539edcdbd7bbf66e458cdce685c7a112f8a04`에서 시작했다.
이 인계 파일을 포함하는 전달 커밋을 다음 immutable starting point로 고정하라.
R9 revision 2를 계속하며 R10 또는 새로운 과학 프로그램으로 초기화하지 마라.

## 먼저 읽을 현재 상태

1. `AGENTS.md`와 관련 repo skills, canonical `docs/codex_handoff/pr_backlog.yaml` 및 `pr_status.yaml`.
2. 이 디렉터리의 `RESEARCH_STATE.json`, 고정 `REVISION_SPEC.md`, `campaign_dag.json`.
3. `revision2/harness_activation/STATE.md`, `CODING_CONTRACT.md`와 `revision2/implementation/CONTRACT.md`.
4. `revision2/implementation/REVIEW.md`, 실행/검증 JSON, `reference_comparison.json`, `desi_product.json`.
5. `revision2/THEORY_EXTENSION.md` D1–D4/F1–F3와 `MODEL_TO_DATA.md`의 제품 조건.

## 원본 하네스

GPT-6 Astra v4.0.0의 두 원본 ZIP을 이번 구현에서도 등록 SHA256과 모든
vendor member bytes로 재검증하고 실제 core/관련 phase를 읽어 적용했다.

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

## 다음 과학 실행과 HOLD

R9-03/05와 R9-24/25의 **scoped implementation**이 실자료/형식적 capability를
승격하지 않는다. R9-24 `FORMAL_DEPTH`와 R9-25 적격 CF4/JWST/CMB의 실제 전체 깊이
법칙이 여전히 필요하다. 다음은 정확한 선택·group·calibration·mask·frame과 모든
Cjk, mean/response를 갖춘 해당 제품 하나를 연결하고, 같은 전체 raw mocks에서
selection/fit/covariance/transport를 반복하는 단계다. 준비된 DESI scalar를 그
필수 선행 조건의 대용으로 쓰지 마라. provider/jet가 없으면 해당 물리 함수만 막는다.

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
이번 default-cwd hook는 다른 과거 run을 보았으므로 authenticated launch로 기록하지
않았다. 실제 지정 worktree의 결과를 직접 검증하라. 독립 검수는 현재 구현에 한정하며
네 축 CAS를 대체하지 않는다. canonical 상태/미러/PR_DELTA, commit/push와 원격
commit/file-body readback을 끝낸 후 새 과학 입력을 기다려라.
