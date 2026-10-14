# Loop 2 게시·이론·PR 종료 감사

감사 기준일: 2026-09-28. 대상 저장소: `cosmosapjw-quantum/htt_base`.

**판정: 게시된 근거와 역사적 DB의 보존은 통과했다. 이론 문구 2곳과 DB 재실행 안전장치를 고쳐야 하며, 기존 PR 전체의 일괄 병합은 적절하지 않다.** 이번 감사는 GitHub의 PR/issue 상태를 변경하지 않았다. 실제 수정·검증·병합·종료는 동봉한 local Codex 프롬프트의 작업 범위다.

## 1. 직접 확인한 증거

| 항목 | 이번 감사 결과 |
|---|---|
| 게시 commit | `de3ab20219c46c2b14f1d2ec6bb87508c331634d` |
| 게시 tree | `8bb24302707ec57d2766c53937a08b0380eeac5e` |
| parent | `96c0b2cb59765c36860da2049021c25a240d0c9b` |
| 변경 파일 | 원격에서 내려받은 40/40 파일의 Git blob 일치 |
| Loop 1 ZIP | 292,194,128 bytes; SHA-256 `0f896823faa03ed82b8cf484cfc893a56ea913e259dc16d59c50d5f97e68670c` |
| ZIP manifest | 101/101 항목 크기·SHA 일치, 전체 102 members; 중복/경로 이탈/symlink 없음 |
| 선택된 원문 | 게시 source의 6개 파일이 원본 ZIP의 대응 파일과 바이트 동일 |
| 엔진 ledger | script/raw 10/10 SHA와 공통 contract SHA 일치 |
| DB gzip | 중간·최종 두 gzip 모두 전체 CRC/크기/압축 및 해제 SHA 일치 |
| SQLite | 원본·중간·최종 모두 `integrity_check=ok` |
| 역사적 DB 보존 | 원본의 **20개 테이블 전체와 schema objects**, 원본→중간→최종의 실제 행 내용 동일 |
| append 보존 | 중간 evidence 6행 + lineage 7행 그대로 유지; 최종에서 5행 + 1행만 추가 |
| 최종 출처 연결 | evidence 11 + lineage 8 = **19/19** 파일 SHA 일치 |
| 상대 링크 | README·RETURN_HANDOFF·RESULTS의 이번 검사 범위 40/40 존재. 사용자 측 41개 검사와 검사 모집단이 같다고 주장하지 않음 |
| GitHub PR/issue | 열린 PR 57개(51 draft), 일반 issue 2개; 전체 목록 확인 |
| 저장소 tree | 11,148 entries, API `truncated=false`; 코드 DB를 내려받은 것이 아닌 경로/blob metadata |
| PR 비교 | 57개 모두 ancestry 확인; 분기된 49개 PR의 변경 3,931 path occurrences 전부 비교·페이지 순회 |

원본 ZIP이 이 작업 공간에 보존되어 있었으므로, 이번 감사는 게시자가 제시한 ZIP 검사 결과를 단순 인용한 것이 아니다. 다만 원격 `main` 일치는 조회 시점의 사실이며 후속 작업 전에 다시 확인해야 한다.

## 2. 수정해야 할 사항

### F1 — TF-W1 kernel 조건의 적용 영역 누락 (medium)

`TF_W1_INPUT_KO.md` 마지막 절은 실제 coupled feasible set을 언급하면서 `ker(B) ⊆ ker(P)`인 target만 유계 가능하다고 쓴다. 이 필요조건은 **제약 없는 선형 공간**, 또는 명시된 **affine variation space**에 대한 진술이다. 일반적인 bounded/curved 물리적 feasible set에는 필요조건이 아니다.

반례: `B=0`, `P=id`, `K=[−1,1]`이면 kernel inclusion은 실패하지만 `Pk`는 유계다. 따라서 한 창의 관측만으로 얻는 무제약 상계와, 별도로 채택한 물리 제약으로 얻는 상계를 구분해야 한다.

수정할 명제: 유한차원 `V`와 고정 선형 `B:V→Y`, `P:V→Z`에 대해 모든 `v∈V`에서 `||Pv|| ≤ C||Bv||`인 유한 C가 존재할 필요충분조건은 `ker B ⊆ ker P`이다. affine domain `k0+V`에서는 `ker B ∩ V ⊆ ker P`를 사용한다. 실제 제한 영역 K에서는 fiber `P(K ∩ B⁻¹{y})` 또는 오차까지 포함한 joint feasible image의 유계성/직경을 직접 평가한다.

증명: 상계가 있으면 `Bv=0 ⇒ Pv=0`. 역으로 `L(Bv)=Pv`가 잘 정의되고 유한차원 `im(B)`에서 연속이므로 `P=L∘B`, `C=||L||`을 택한다. 이 보정은 W1의 적분 항등식이나 관측 입력 부족 판정을 바꾸지 않는다.

### F2 — DB 원본 경로 보호가 실제 계약보다 약함 (medium)

`db/apply_append.py`는 `ROOT/THEORY_INHERITANCE.sqlite`라는 한 경로만 거부한다. 원본이 다른 디렉터리에 있으면 정확히 동일한 BASE_SHA와 행 수를 갖기 때문에 `--db-copy`로 잘못 넘겨도 쓰기 연결까지 진행한다. 현재 원본이 손상됐다는 뜻은 아니다. 실제 세 DB의 역사 내용은 이번 감사에서 동일함을 확인했다.

추가 문제는 압축 출력 경로의 존재 검사를 DB commit **뒤에** 한다는 점이다. 출력 충돌을 이미 알 수 있어도 먼저 입력 DB가 변경될 수 있다. 기존 2개 실행 스크립트를 역사 자료로 보존하고, 새 안전한 migration entrypoint를 만들 것을 권한다.

새 도구는 `--source`를 읽기 전용으로 열고, 별도 `--output`을 exclusive create하며, 원본과 동일 path/inode 및 symlink/hardlink alias를 거부해야 한다. 기존 출력 충돌을 쓰기 전에 확인하고, 임시 새 복사본에서 transaction·검증을 완료한 뒤 새 결과와 영수증을 게시한다. 입력 원본은 성공·실패 모두에서 불변이어야 한다.

### F3 — Lean 증명 범위의 작은 과장 (low)

`gap_column3`는 **3개 성분을 가진 열 하나**의 diagonal gap estimate를 증명한다. 3개 열 전체를 한 번에 증명한 명제가 아니다. 별도 정리는 명시적 3×3 trace/STF/antisymmetric Frobenius identity다.

`RESULTS_KO.md`, `ENGINE_RUNS.json`, `INDEPENDENT_DECISION_LOOP2.json`의 self-review, `db/append_final_evidence.py`, 최종 DB TF-P2/lean_mathlib caveat에 있는 “3열/3-column” 표현을 새 정오표에서 바로잡아야 한다. 기존 Lean 소스 자체는 이 좁은 주장과 일치한다. 기존 DB 행·raw·receipt를 덮어쓰지 말고 correction/supersession을 새로 추가한다.

### F4 — PR #469의 실제 CI 실패 원인 (merge blocker)

PR head `ef47cf3a4359c0876f4cd8002cd5f33a569ed3d3`, run `35051091315`, job `104651420491`을 확인하고 전체 job log를 읽었다.

- runner가 배정됐고 checkout·설치·여러 계약 검사는 실행됐다.
- `tests/contracts/test_human_execution_authorization.py::test_ci_coverage_001_runs_every_pr304_policy_command_on_pull_requests`가 line 1445에서 실패했다: **1 failed, 63 passed**.
- 이 테스트는 이전 한 줄 설치 문자열 `numpy>=1.26,<3`를 workflow에서 찾는다. PR #469는 여러 줄의 설치와 `numpy==2.5.2` 등으로 pin을 바꿨다.
- 뒤의 `Validate PR-315 portable projection byte determinism`은 **skipped**다.

따라서 이번 실패를 runner 미배정이나 PR-315 재현성 실패로 부르면 안 된다. PR-304의 명령 실행·설치 순서 계약을 보존하면서 테스트를 실제 pin/설치 구조에 맞게 고쳐야 한다. 옛 문자열을 주석에 넣거나 테스트를 삭제해 통과시키면 안 된다. 이 수정 후 같은 새 head에서 독립 CI 실행 두 번과 완전한 preimage/환경 영수증이 있어야 #445의 종료 조건을 검토할 수 있다.

## 3. 이론 검토의 결론과 한계

후보 작성자가 아닌 별도 검토자 두 명이 등록된 할당으로 수학·DB를 검토했다. 결과 JSON의 strict v2 payload validation은 각각 오류 0개다. 두 결과의 `status=fail`은 위 보정 사항이 남아 있다는 뜻이며, 게시 바이트나 P2/P3 중심 식이 실패했다는 뜻이 아니다.

| 대상 | 이번 독립 수기/소스 검토 |
|---|---|
| TF-P2 | energy-eigenvector 미분식, positive observer norm, gap δ>0 아래 결합 상계를 지지. 일반 spectral/미분기하 bridge는 수기 |
| TF-P3 | conformal 2-jet, `G(0)=diag(6b,0,0,0)`, `∂₀G₁₀=−2λ`, `A¹=c²λ/(3b)` 및 P2 포화를 지지. 총 Einstein source의 국소 명제 |
| TF-S2/S4 | Lean 소스가 말하는 event inclusion/measure monotonicity/diameter/실수 union-bound 구성요소와 일치. 전체 통계 정리의 형식화는 아님 |
| TF-C1 | 미분류 Jacobi와 실수 image 예시의 범위를 지지. 일반 real feasibility 결과가 아님 |
| TF-W1 | 원본 R2 §4의 4/1/2 계수와 와도 0, window 적분 및 오차식 일치. kernel 조건에 F1 보정 필요 |

이번에는 과학 엔진을 재실행하지 않았다. 소스·raw 바이트 대조와 독립 수기 검토를 새 observed execution 또는 blinded four-axis CAS PASS로 승격하지 않는다. I2 `DEFENDED_CONDITIONAL`, I3 `HOLD_INPUT_INCOMPLETE`, 관측 likelihood·joint anchor·source/time law의 부족은 유지한다.

별도 한계: 이 환경의 선택적 소스 staging은 `.git`이 있는 실제 checkout이 아니며, 이전 준비 run의 결과 형식은 현재 strict harness 규격과 맞지 않았다. 오류 기록·원 결과·run summary를 보존한 뒤 지원되는 invalid-state recovery로 staging의 포인터만 해제했다. 새 감사는 별도 게시 감사 work-unit으로 등록했다. 이 절차는 사용자의 local R9 run을 변경하지 않았고, 그 예산을 초기화하지 않았다. 새 결과의 `launch_evidence=unverified`, `execution_evidence=self_declared`를 그대로 유지한다. 따라서 local의 operational admission은 해당 하네스의 실제 실행·예산·관찰 요건을 충족한 별도 판정이 필요하다. DB의 Lean 문구 확인은 독립 DB 내용 검사가 끝난 후 root가 요청한 교차 확인임을 결과에 공개했다.

## 4. 기존 PR을 처리할 순서

**57개 전체의 목록·ancestry와 49개 분기 PR의 경로/blob 차이를 조사했다. 57개 모든 PR의 코드와 과학 내용을 깊이 검토했다는 뜻은 아니다.** 전체 표는 `PR_DISPOSITION_MATRIX.csv/json`, 상세 경로는 `remote/PR_FILE_OVERLAP.json`이다.

| PR | 확인된 상태 | 처리 방향 |
|---|---|---|
| #440, #449, #460, #461, #463, #465, #466, #467 | 8개 head가 게시 main의 조상 | 최종 head를 다시 확인하고 이미 통합됐다는 근거로 정리. 다시 merge할 변경은 없음. GitHub close와 실제 merge 표시를 구분 |
| #468 | head는 분기. 40개 delta 중 같은 경로 blob 24개 일치, 추가 10개는 다른 경로에 동일 blob 보존 | 현재 R9 후속 결과와 의미 단위 대조 후 미반영 요건만 통합하거나 superseded 판정 |
| #470 | head는 분기. 25개 delta 모두 역사 보존 경로에 동일 blob 존재; 원래 활성 경로에서 일치 0개 | 보존과 활성화를 구분. 현재 DAG에 유효한 optical 계획만 계승하고 원 PR 처리. 과거 DAG 전체를 복원하지 않음 |
| #469 → #445 | 위 실제 CI 실패; 새 checker는 main의 해당 경로에 없음 | F4 수정 → 같은 새 head의 두 CI replay → 정확한 코드 통합 → issue 종료 조건 확인 |
| #444 → #448 | 최신 해당 head의 A4 run `33718012456`, attempt 2, job `100532290372`: runner_id=0, steps=[] | 원 head에 대한 runner 실행 증거가 아직 없음. 뒤의 #469에서 runner가 동작한 사실을 함께 기록하되 같은 head의 회복 증거로 대체하지 않음 |
| #428 | delta 2,131개: 삭제 2,106, 수정 24, 추가 1 | 현재 자료를 광범위하게 삭제하는 과거 정리안. Loop2 종료에 섞어 병합하지 않음 |
| #427 | 본문은 marker 한 파일이나 실제 delta 337개: 추가 274, 수정 57, 삭제 6 | smoke 설명과 현재 base/head 차이 불일치. 재기준화·scope 검토 전 병합하지 않음 |
| 나머지 분기 PR | 원래 경로 부재/변경 및 일부 archive 보존이 혼재 | base별 증분·의존성·미해결 review를 확인해 MERGE / SUPERSEDED / HOLD / OUT_OF_SCOPE 각각 기록 |

현재 canonical DAG는 **211개 card**다. #468/#470 문서의 과거 195개 DAG로 되돌리면 안 된다. GitHub PR 번호와 저장소의 `PR-xxx` card ID는 별개다. 특히 여러 GitHub PR이 같은 `PR-248`을 가리킨다.

Issue #445/#448은 이번 감사에서 닫지 않았다. `de3ab202` 자체에는 조회 시점 Actions run/check-run이 없으므로 CI PASS를 주장하지 않는다. 필수 check 존재 여부나 merge 허용 여부는 최종 병합 대상의 실제 branch policy로 확인해야 한다.

## 5. 닫을 수 있는 범위

F1–F3의 정오표와 안전한 append 경로를 새 증거로 추가하고, 필요한 독립 후속 판정을 받으면 **범위가 명시된 유형 미지정 Loop 2 이론 패키지**를 종료할 수 있다. 모든 역사적 PR, 모든 일반 형식화, 실제 관측 입력, 미래 solver까지 완료해야 이 범위를 닫을 수 있다는 새 조건을 만들 필요는 없다.

PR 통합과 #445/#448의 운영 문제는 실제 해결/보류 사유를 남긴다. 외부 입력이 필요한 W1의 수치 Q,F,Π,G_F, MES percentage/p-value와 관측 제약은 계속 `UNAVAILABLE/HOLD`다. 이를 보존한 `CLOSED_SCOPED_WITH_EXTERNAL_BLOCKERS`는 가능한 종료 판정이며, “모든 과학 문제가 해결됨”을 뜻하지 않는다.

근거 링크: [게시 commit](https://github.com/cosmosapjw-quantum/htt_base/commit/de3ab20219c46c2b14f1d2ec6bb87508c331634d), [PR #469](https://github.com/cosmosapjw-quantum/htt_base/pull/469), [실제 CI job](https://github.com/cosmosapjw-quantum/htt_base/actions/runs/35051091315/job/104651420491), [issue #445](https://github.com/cosmosapjw-quantum/htt_base/issues/445), [issue #448](https://github.com/cosmosapjw-quantum/htt_base/issues/448), [PR #470](https://github.com/cosmosapjw-quantum/htt_base/pull/470), [PR #428](https://github.com/cosmosapjw-quantum/htt_base/pull/428), [PR #427](https://github.com/cosmosapjw-quantum/htt_base/pull/427).
