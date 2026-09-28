# htt_base

HTT/Bianchi 연구를 위한 관측 feature, 조건부 기하, 통계 추론 및 재현성 도구를 모은 저장소입니다. 관측 입력에서 계산할 수 있는 결과와, 외부 전달함수·물리적 가정·추가 검증이 필요한 결과를 구분합니다.

이 저장소는 외부 native low-ell Bianchi Boltzmann solver를 구현하지 않습니다. 현재의 관측 요약량이나 조건부 계산만으로 Bianchi 계열 또는 우주 기하의 검출을 주장하지 않습니다.

## 현재 제공하는 기능

| 영역 | 역할 | 경계 |
|---|---|---|
| `common` | 입력·단위·공동 상태 계약, anchor/response geometry, 조건부 support 계산 | 관측 proxy를 물리량으로 자동 승격하지 않음 |
| `obsstat` | 관측 feature 추출과 frozen-release adapter | likelihood·posterior·인증서 생성은 다른 계층의 책임 |
| `htt` | 모델에 의존하는 통계법칙과 추론 | 실제 sampling law와 필요한 입력이 있을 때 사용 |
| `mio` | 모델 계열에 독립적인 진단과 방향·깊이 coherence | 진단은 posterior나 truth certificate가 아님 |
| `bass_py` 및 외부 adapter | 전달함수 출처와 향후 native solver 입력 계약 | external/conditional 결과는 native 결과가 아님 |
| `formal`, `tests`, `.agent-harness` | 범위가 고정된 증명·회귀 검사·검수 기록 | 도구 실행 성공과 과학적 수락을 구분 |

## MES R7 조건부 source image

MES R7 모듈은 제공된 frozen fixture의 **525행, 418 literal CID, 4변수 box → 5개 STF feature** 계산을 지원합니다. 반복 CID 행을 임의로 제거하지 않으며, signed feature operator와 좌표·단위 convention을 유지합니다.

하나의 공통 latent vector `xi`에 대해 다음 비선형 image를 계산합니다.

```text
Phi(xi) = -L log1p(-A xi),  xi ∈ [-1, 1]^4
```

각 support 방향에는 실제 feasible witness, 전체 5개 feature, outward upper bound와 남은 gap이 함께 반환됩니다. 서로 다른 방향의 witness를 하나의 물리적 realization으로 합치지 않습니다. 상계는 저장된 수치 입력과 지정된 box에 조건부이며, optimizer 성공을 exact global maximum으로 부르지 않습니다.

- 실행 지원: 저장된 4변수 box, 전체 로그·redshift 정의역 검사, zero-width와 입력 불일치 처리.
- 미지원: generic 차원의 optimizer와 ellipsoid 수치 solver.
- 결과 상태: `CONDITIONAL_SCENARIO`.
- `beta_flow`는 reconstruction calibration parameter이며 congruence tilt가 아닙니다.
- q-proxy는 physical shear가 아니며 source image는 새로운 MES anchor가 아닙니다.
- empirical MES D·physical shear·joint confidence 요청에는 근거 부족을 명시적으로 반환합니다.

원 frozen replay와 수치 비교는 통과했습니다. 독립 구현 검수도 결함 없이 지정 검사 33개를 통과했지만, **과거 child의 종료 수락은 runtime continuation 예약 문제로 보류**되어 있습니다. `main` 게시와 이 검수의 정식 수락은 별개입니다. 자세한 방법·허용오차·실패 이력은 [MES R7 실행 문서](docs/research_program/mes_r7/README.md)를 확인하세요.

## 로컬에서 실행하기

현재 배포 경로는 아래 `PYTHONPATH`를 사용하는 저장소 실행입니다. NumPy, SciPy, pytest가 준비된 Python 환경을 사용합니다. 저장된 실행 환경은 Python 3.12.3, NumPy 2.4.2, SciPy 1.17.0, pytest 9.1.1입니다. 선택적 연구·CAS 도구는 해당 작업 문서의 별도 조건을 따릅니다.

MES 원본 bundle은 별도로 제공된 입력입니다. 이 README가 해당 관측 입력을 다운로드하거나 생성하지 않습니다. `MES_R7_SOURCE`는 압축 해제한 원본 `mes_r7` 디렉터리를 가리켜야 합니다. 소스·fixture의 SHA256은 adapter가 검사합니다.

```bash
cd /path/to/htt_base
export PYTHONPATH=htt/src:htt:htt/htt
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MES_R7_SOURCE=/path/to/mes_r7

# 제한된 모듈 및 영향받는 기존 인터페이스 검사
python3 -B -m pytest -q -p no:cacheprovider \
  htt/src/common/test_conditional_source_image.py \
  tests/r9/test_intake_depth.py \
  tests/r9/test_law_support_runner.py

# 계산 결과는 반드시 존재하지 않는 새 디렉터리에 기록
python3 -B -m obsstat.mes_r7_source_image \
  --source "$MES_R7_SOURCE" \
  --out /path/to/new_mes_r7_output \
  --cover-depth 6
```

이미 존재하는 출력 디렉터리·파일·dangling symlink는 거부합니다. 원 frozen replay의 완료된 출력 경로를 재사용하지 마세요. 테스트 통과는 외부 데이터 적합, 물리량 식별 또는 native solver 검증을 의미하지 않습니다.

## 연구 상태와 HOLD

HTT/MES I1·I2의 원문 702개와 독립 검토·검증 근거는 [검증된 체크포인트 읽기 안내](docs/research_program/mes_verified_checkpoints_20260928/README_KO.md)에서 시작합니다. 원본 전체 ZIP의 [보존·복원 검증](docs/research_program/mes_full_handoff_20260928/VALIDATION_KO.md)과 이미 진행한 [I3 Gaia-CRF3 screening](docs/research_program/mes_i3_gaia_screening_20260928/REPORT_KO.md)은 별도 기록입니다. I2는 `DEFENDED_CONDITIONAL`, I3 입력은 `HOLD_INPUT_INCOMPLETE`이며 실측이나 일반 finite tilt 검증으로 승격되지 않았습니다.

| 항목 | 현재 경계 |
|---|---|
| MES R7 | 조건부 box 계산·adapter·frozen replay, 독립 검수 내용 PASS; 과거 runtime 수락 보류 |
| R9 | 제한된 D3 law/support/moment 컴파일 근거 보존; 다음 단일 과제 D2 singular-Gaussian support |
| D4 및 `FORMAL_DEPTH` | 기존 미완료 의무와 BLOCKED 상태 보존 |
| Physical source closure, target/source full response | `HOLD` |
| Reference `U_R` / optical bridge | `HOLD` |
| Empirical MES D | `HOLD_NOT_COMPUTED` |

누락된 mean·correlation·transfer를 zero, identity 또는 independent Gaussian으로 채우지 않습니다. 기존 directional `F`와 수학적 squared gauge는 같은 이름으로 취급하지 않습니다.

세부 상태의 기준은 [canonical DAG](docs/codex_handoff/pr_backlog.yaml), [PR 상태](docs/codex_handoff/pr_status.yaml), [R9 연구 상태](docs/research_program/tensor_joint_r9/RESEARCH_STATE.json), [R9 인계 문서](docs/research_program/tensor_joint_r9/HANDOFF_PROMPT.md)입니다. `machine_readable/`의 DAG·상태는 호환용 mirror입니다.

## 작업 방식

`main`은 게시 브랜치입니다. 앞으로는 **기존 원 저장소 checkout에서 작업하며 새 worktree나 전체 clone을 자동으로 만들지 않습니다.** 소유자의 로컬 경로는 `/home/cosmosapjw/Dropbox/bianchi/htt_base`입니다.

사용자 변경을 보존하고, production 파일은 한 작업자가 수정합니다. 새 worktree가 꼭 필요한 경우에만 별도 명시적 지시를 받습니다. 기존 worktree·증거·실패 기록은 이 정책만으로 삭제하거나 다른 등록에 재결합하지 않습니다.

정책은 [AGENTS.md](AGENTS.md)와 [shared-context harness](.agent-harness/README.md)에 있으며, [공유 결정](.agent-harness/context/FROZEN_DECISIONS.md)을 통해 이후 에이전트에 전달됩니다. 일반 Git 게시에는 성공 응답과 remote ref/SHA 확인을 사용하고, 복구·감사·출처 충돌 등에서는 정해진 강화 검증을 적용합니다.

```bash
python3 -B scripts/codex_harness/validate_pr_dag.py \
  docs/codex_handoff/pr_backlog.yaml
python3 -B .agent-harness/scripts/build_context_pack.py
```

과거 assignment의 context/version은 새 정책에 맞추어 소급 수정하지 않습니다. 원격 게시, 결과 재현, 독립 검수, 물리적 수락은 각각의 근거로 판단합니다.
