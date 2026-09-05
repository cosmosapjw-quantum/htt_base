# Work 스레드 실행 인계 — HTT Report A K2FE

@GitHub @Superpowers

## 0. 목적과 실행 범위

이 작업은 이미 구현된 strict compiler와 등록된 회귀 테스트의 실제 실행이다. 새 연구계획, 새로운 compiler 구현, PDF 재생성 또는 문헌 재감사가 아니다. 가용 runtime이 있으면 이 응답에서 기존 테스트를 실행하고 여섯 파일의 forty-claim source-candidate bundle 또는 정확한 실패 증거를 반환하라.

K5의 24쪽 review PDF는 이미 전달됐다. 입력 원고 revision 2의 Git blob은 `99a3f75c67ece3cfb00179bfd61787f47cb7e7ac`, work 스레드가 보고한 PDF SHA-256은 `9f70061a593c58024a406c643a22004b0535bf60c6f5961d7bcd06ea85d3c97c`다. 이 PDF와 그 receipt는 보존하며 재생성하지 않는다. K5에서 Python 3.12.13이 실행됐다는 기록은 다음 환경 선택에 유용하지만 현재 K2 실행 증거는 아니다.

이번에 허용된 동작은 GitHub 읽기, 격리 checkout 또는 검증된 source mirror 구성, 격리 Python 환경의 필요한 의존성 설치, 기존 tests/compiler 실행, 로컬 결과 검토와 파일 반환이다. scientific source, compiler, helper, tests, workflows, input ledgers와 bibliography를 수정하지 않는다. Commit/push/PR metadata mutation, merge, canonical/publication 승격, Planck/FFP10 관측 분석, BASS/REC/REI 변경 및 CAS 실행은 이 인계에 포함하지 않는다.

Canonical은 T9 v4의 30 claims로 유지한다. 생성되는 40-claim v5는 이름에 v5가 있더라도 아직 source candidate다. 성공적인 source compilation은 40개 과학 명제의 참, CAS 통과 또는 publication acceptance를 뜻하지 않는다.

## 1. 고정 snapshot과 live-state 확인

```yaml
repository: cosmosapjw-quantum/htt_base
pr: 449
branch: docs/htt-tensorized-mes-response-synthesis-20260903
execution_source_snapshot: a0784f2a1ce1f4a3fe14195a5f169e4959bd8391
execution_source_tree: 036bc001d333cbc61427179edea2bf77fba3ff0a
base: 687234128d7c12d04e68aad0f303c21d2d470393
canonical_ledger: T9_V4
canonical_claim_count: 30
candidate_claim_count: 40
```

먼저 PR #449를 fresh read하고 실제 live head/tree/base를 기록한다. 위 snapshot은 실행 입력의 고정 identity이지 앞으로도 live head라는 뜻이 아니다. 이 handoff 등 문서만 추가되고 아래 compiler/test/input/config blobs가 그대로면 고정 snapshot의 실행을 진행할 수 있다. 실행 표면에 실제 변화가 있으면 `SOURCE_DRIFT`를 기록하고 변경을 읽는다. 구 hash를 새 source에 맞춰 바꾸거나 옛 snapshot을 최신 상태라고 부르지 않는다. 임의로 base/default branch의 파일을 섞지 않는다.

Repo의 `AGENTS.md`, 관련 하위 AGENTS, `.agents/skills/htt-scientific-code-validation/SKILL.md`, `htt-claim-provenance-ledger`, `htt-ssot-handoff-maintainer` 규약을 읽는다. 읽지 못한 규약은 읽었다고 기록하지 않는다. 이 한정 실행을 이유로 새로운 영구 audit gate를 추가하지 않는다.

## 2. 정확한 실행 source

아래는 위 snapshot에서 부모 스레드가 실제로 읽은 Git blob identity다. 비교는 원본 raw bytes로 하며 Git 속성에 의한 줄바꿈/필터 변환을 배제한다.

| 경로 | Git blob SHA-1 |
|---|---|
| `scripts/compile_report_a_k2fr0_authority.py` | `d89ac38f47e221597fbc2b152b4a6c591c673d81` |
| `scripts/compile_report_a_k2f_authority.py` | `d22e439211b0058596c27028d382554657b9f532` |
| `tests/contracts/test_report_a_k2fr0_hardening.py` | `767b86900ab22b5ea002af77e5e8a5ab8be12835` |
| `tests/contracts/test_report_a_k2f_compiler.py` | `d90a80c8836c3340c3f50b9f3c621c84a647fa02` |
| `tests/contracts/test_report_a_k1r_kinematical_mes_repairs.py` | `bed6f72f9498631f3b945b1d44c0820a4e13a5d9` |
| `tests/contracts/test_report_a_k2_kinematical_claim_recompile.py` | `0c36ccd9fd6d18c4302256c508ba655cf7f90b58` |
| `.github/workflows/report-a-k2.yml` | `d7d18171f8a91d13c2a10ddb316481bbe7fdacfd` |

생산 entrypoint는 반드시 `compile_report_a_k2fr0_authority.py`다. 이전 `compile_report_a_k2f_authority.py`는 새 compiler가 호출하는 고정 helper와 회귀 이력이며, 그 standalone CLI output을 최종 bundle로 제출하지 않는다. 기존 helper tests가 임시로 만드는 v5 파일도 최종 strict bundle로 채택하지 않는다.

### 여덟 개 compiler 입력

아래 표에서 `BASE=docs/codex_handoff/htt_tensorized_report_first_20260903`, `REPORT=docs/research_reports`, `RA=docs/research_reports/report_a`다. 실제 mirror에는 축약명이 아니라 전체 경로를 사용한다.

| 입력 경로 | Git blob SHA-1 |
|---|---|
| `BASE/T9_INTEGRATED_CLAIM_EVIDENCE_LEDGER_V4.yaml` | `58291e9cfac6ff85ceffbdb6bdefd50315240831` |
| `BASE/K2_40_CLAIM_CANDIDATE_OVERLAY.yaml` | `394378a796a24410a4174a8222e40c5c59e9700a` |
| `BASE/REPORT_A_CITATION_PROVENANCE_MATRIX_V2.yaml` | `3fbaa2f97522cca6d0ad60e0c96655d293ca0d74` |
| `BASE/K2_CITATION_PROVENANCE_CANDIDATE_OVERLAY.yaml` | `902b698ef81506179cb0f6e3c5d6616a3f445c55` |
| `BASE/REPORT_SECTION_CLAIM_MAP_V2_CANDIDATE.csv` | `d42a666ff0eba8fdca8afc9b4e719de6e5e12a8d` |
| `RA/REPORT_A_ORGANIC_INTEGRATION_MATRIX_V2_CANDIDATE.yaml` | `28e823ce7705f0c14a4cae5edf39dc32b69d2617` |
| `REPORT/HTT_REPORT_A_REFERENCES.bib` | `ba37321119725e52f1a2b0ac827050ee895e5466` |
| `RA/K2_BIBLIOGRAPHY_SUPPLEMENT_CANDIDATE.bib` | `930457120f5def21321008f4f77cc2b9c0f5694a` |

### Tests가 추가로 읽는 문서와 import/config closure

같은 snapshot에서 다음 실제 파일을 확보하고 connector/tree가 반환한 blob과 로컬 raw-byte hash를 기록한다.

```text
docs/codex_handoff/htt_tensorized_report_first_20260903/K0_TYPED_KINEMATICAL_MES_AUTHORITY_CROSSWALK_V2.yaml
docs/codex_handoff/htt_tensorized_report_first_20260903/K1R_TYPED_KINEMATICAL_MES_EVIDENCE_LEDGER.yaml
docs/codex_handoff/htt_tensorized_report_first_20260903/K2_KINEMATICAL_CLAIM_RECOMPILE_INPUT_V2.yaml
docs/research_reports/theory_packs/K1R_TYPED_KINEMATICAL_MES_THEOREM_PACK.md
docs/research_reports/K2_REPORT_A_CLAIM_ARCHITECTURE.md
```

Full checkout을 우선하되 직접 GitHub 네트워크가 막히면 connector에서 완전한 payload를 받아 hash-verified mirror를 만들 수 있다. Mirror의 경우 적용되는 root pytest configuration, 해당 디렉터리의 conftest.py, package initialisers와 그 import closure도 같은 snapshot에서 확인한다. 파일이 없는 경우 absence를 기록한다. 임의 __init__.py, 대체 conftest, 가짜 .git을 만들지 않는다. `--noconftest`, 임의 config 교체나 test skip으로 기존 workflow와 같다고 주장하지 않는다.

문서/코드를 기억으로 다시 타이핑하거나 partial chunk를 그대로 실행 source로 쓰지 않는다. 완전한 payload가 확보됐는지는 최종 Git blob 재계산으로 판정한다.

```python
hashlib.sha1(b"blob " + str(len(raw_bytes)).encode("ascii") + b"\0" + raw_bytes).hexdigest()
```

`git hash-object --no-filters`도 사용할 수 있다. 각 입력의 SHA-256은 별도 보존한다. `HASH_VERIFIED_SOURCE_SET`은 full Git checkout이나 전체 repo tree 검증과 다르므로 정확한 실행 grade를 기록한다.

## 3. Runtime와 출력 디렉터리

최소 shell/Python process 한 번과 독립 fallback 한 번까지만 runtime admission을 시험한다. 둘 다 backend 단계에서 실패하면 원 오류를 보존하고 종료한다. 같은 print를 반복하지 않는다.

이 작업의 생산 CLI는 **CPython 3.12**를 요구한다. 실제 interpreter 경로와 full version, Linux/platform, PyYAML/pytest/pybtex와 transitive dependencies를 기록한다. K5에서 사용한 Python 3.12.13 환경을 재사용할 수 있으나 현재 버전을 재확인한다. Python 3.13 library call로 이 gate를 우회하지 않는다. Lean, Wolfram, Sage 또는 Pandoc의 부재는 이 Python-only task의 blocker가 아니다.

Atomic publisher에는 Linux `renameat2(..., RENAME_NOREPLACE)`가 필요하다. 사용할 수 없으면 platform failure를 반환하며 os.replace나 copy fallback으로 바꾸지 않는다.

`REPO`는 검증된 source root, `PY`는 격리 환경의 CPython 3.12 절대경로, `RUN`은 새 실행 출력 디렉터리로 둔다. RUN은 REPO 밖에 만들고 원 source bytes를 보존한다. `RUN/logs`, `RUN/receipts`와 임시 테스트 출력은 생성해도 된다. **`RUN/authority-bundle` 자체는 compiler 호출 전에 존재하면 안 된다.** Compiler가 여섯 파일을 한 디렉터리로 공개한다.

필요하면 source 밖의 venv에 아래 workflow-pinned dependency를 설치한다. 실제 package 다운로드/설치 실패를 기록하고 다른 버전을 조용히 사용하지 않는다.

```bash
"$PY" -m pip install --disable-pip-version-check \
  pytest==8.3.5 PyYAML==6.0.2 pybtex==0.26.1
```

이후 package versions/pip freeze, source root, 실제 import 경로, pytest rootdir/config/plugins, 관련 PYTHONPATH/PYTEST_ADDOPTS를 기록한다. 전체 환경이나 credential을 덤프하지 않는다. Source initialisers와 pytest configuration을 누락해 외부의 다른 `scripts` package를 import하지 않았는지 확인한다.

## 4. 기존 명령을 실제 실행

각 command의 cwd, argv, 시작/종료 시각, exit code, stdout/stderr를 별도 파일에 남긴다. `tee`를 사용하면 pipefail과 실제 command exit code를 보존한다. 종료코드를 무시해 PASS로 바꾸지 않는다. 아래는 등록된 workflow의 실행 순서이며 부모 스레드에서 실행됐다는 뜻이 아니다.

```bash
cd "$REPO"

"$PY" -m py_compile \
  scripts/compile_report_a_k2f_authority.py \
  scripts/compile_report_a_k2fr0_authority.py \
  tests/contracts/test_report_a_k2fr0_hardening.py

"$PY" -m pytest -q \
  tests/contracts/test_report_a_k1r_kinematical_mes_repairs.py \
  tests/contracts/test_report_a_k2_kinematical_claim_recompile.py \
  tests/contracts/test_report_a_k2f_compiler.py \
  --junitxml="$RUN/receipts/k2-existing-tests.xml"

"$PY" -m pytest -q \
  tests/contracts/test_report_a_k2fr0_hardening.py \
  --junitxml="$RUN/receipts/k2fr0-tests.xml"
```

Cache/bytecode는 generated files로 구분하고 가능하면 source 밖의 경로에 둔다. 실행 전후 registered source bytes를 다시 검사한다. 실제 collected/passed/failed/error/skipped/xfail/xpass를 반환한다. 이 prompt는 사전 고정 PASS 개수를 발명하지 않는다. Zero collection 또는 required tests의 skip을 성공으로 판정하지 않는다.

원본 tests에 failure가 생기면 실패 assertion/exception과 최초 로그를 보존한다. 별도 독립 test group의 결과를 수집할 수는 있으나 failed predecessor를 무시하고 accepted K2FE를 선언하지 않는다. 이번 실행은 자동 수리 승인이 아니다. 필요한 최소 수정 제안만 적고 source와 test를 그대로 둔다.

필수 regression과 syntax 검증이 통과한 뒤 strict CLI를 한 번 실행한다.

```bash
"$PY" scripts/compile_report_a_k2fr0_authority.py \
  --repository-root "$REPO" \
  --output-root "$RUN/authority-bundle"
```

성공 시 다음 여섯 파일이 있어야 한다.

```text
T9_INTEGRATED_CLAIM_EVIDENCE_LEDGER_V5.yaml
REPORT_A_CITATION_PROVENANCE_MATRIX_V3.yaml
REPORT_SECTION_CLAIM_MAP_V3.csv
REPORT_A_ORGANIC_INTEGRATION_MATRIX_V3.yaml
HTT_REPORT_A_REFERENCES_V2.bib
K2F_COMPILATION_RECEIPT.json
```

`--no-enforce-input-blobs`, `enforce_registered_input_blobs=False`, helper standalone CLI, 손으로 쓴 ledger, patched hash table 또는 fixture output으로 생산 bundle을 대체하지 않는다. 테스트 내부의 의도적 fault injection은 기존 regression의 일부이며 실제 scientific source 수리는 아니다.

## 5. 생성 결과 readback과 판정

원본 output을 편집하지 않고 별도 reader로 다음을 확인한다.

- 최종 claim/citation/section/integration의 ID가 각각 40개이고 중복 없이 서로 같은 집합인지.
- 기존 30개가 유지되고 신규 10개 및 예정된 기존 4개 revision이 적용됐는지.
- Full BibTeX parse의 key가 20개이며 citation source registry와 일치하는지.
- Base의 `canonical_notation_registry`, `registered_survivor_source`, `active_repairs`, `vocabulary`, prior supersession history가 보존됐는지.
- 과거 survivor projection count 30을 새 candidate count 40으로 덮지 않았는지.
- Status가 base vocabulary 안에 있고 원래 candidate labels와 donor lineage가 보존되며 donor execution을 상속하지 않았는지.
- `source_binding.enforced`, `all_registered_input_blobs_match`, `parser_uses_verified_byte_snapshot`가 true인지.
- 실제 최종 IDs에서 `SHA256(UTF8("\n".join(sorted(ids))+"\n"))`를 재계산해 receipt와 맞는지. 기대 hash를 대화의 수작업 목록에서 가져오지 않는다.
- Five payload hashes가 receipt와 맞는지. Receipt 자신의 hash는 외부 SHA256SUMS에 기록한다.
- `claim_promotion`, `compiled_bundle_is_canonical`, `scientific_verification_performed`, `publication_authority`, `merge_authorized`가 false인지.

`structural_findings`와 coverage booleans를 그대로 반환한다. **성공적으로 compile되어도 conditional scope 등의 findings가 비어 있지 않을 수 있다.** 이는 현재 compiler가 의도적으로 숨기지 않는 결과다. Missing assumptions를 상식으로 채우거나 all-true로 고치지 않는다. 그 경우 `K2FE_EXECUTED_WITH_STRUCTURAL_FINDINGS`로 기록하고 각 claim ID, 원 source field, 후속 검토 대상을 적는다. 기술적 materialisation 성공과 canonical/scientific acceptance는 서로 다른 판정이다.

현재 원고 Appendix A와의 연결은 위 manuscript blob을 별도로 확보해 ID 집합만 대조할 수 있다. 문장의 scientific entailment까지 자동 검증했다고 부르지 않는다. 기존 PDF, canonical manuscript, input ledger 및 candidate overlays는 변경하지 않는다. Compiler 입력에 남은 오래된 `remaining_before_report_freeze` 문구가 이미 완료된 K3/K5 작업을 언급해도 입력 hash를 바꾸지 말고 역사적 상태와 실제 최신 완료 상태의 차이를 별도 검토 메모에 적는다.

별도 reviewer가 실제로 수행하지 않았다면 readback은 `EXECUTOR_READBACK`으로 분류한다. 이를 blind independent review라고 부르지 않는다.

## 6. 결과 파일과 부모 스레드 반환 형식

성공/실패 어느 경우에도 가능한 범위의 durable package를 만든다.

```text
source_manifest.json
logs/                         # command별 stdout/stderr/exit
receipts/                     # 실제 JUnit 및 runtime 기록
K2FE_EXECUTION_RECEIPT.json    # 실행 관리 receipt, compiler receipt와 별개
K2FE_REVIEW.md                 # output readback 또는 정확한 blocker
authority-bundle/             # 성공했을 때만 여섯 파일
SHA256SUMS
```

재개에 필요한 exact inputs, compiler/helper/tests/config를 source subtree로 포함할 수 있다. Credential, token, font 파일, 무관한 대형 archive는 넣지 않는다. 원래 compiler receipt는 보존하고 실행환경 설명을 추가하기 위해 덮어쓰지 않는다. Package와 개별 결과 파일은 실제 생성 경로를 확인한 후 링크한다. Sandbox 간 링크가 이식 가능하다고 가정하지 않는다.

부모에게 아래 machine-readable summary를 반환하라. 실행되지 않은 값은 false/null/NOT_EXECUTED로 표시한다.

```yaml
k2fe_result:
  observed_live_head:
  execution_source_snapshot:
  execution_source_tree:
  source_method: FULL_CHECKOUT_OR_HASH_VERIFIED_SOURCE_SET
  execution_grade:
  input_blob_identity_verified:
  test_and_config_closure_verified:
  compiler_git_blob:
  helper_git_blob:
  workflow_git_blob:
  python_version:
  platform:
  pytest_version:
  pyyaml_version:
  pybtex_version:
  syntax_exit_code:
  existing_regression_exit_code:
  strict_regression_exit_code:
  tests_collected:
  tests_passed:
  tests_failed:
  tests_errors:
  tests_skipped:
  tests_xfailed:
  tests_xpassed:
  strict_cli_executed:
  strict_cli_exit_code:
  six_file_bundle_created:
  claim_count:
  citation_rows:
  section_rows:
  integration_rows:
  bibliography_entries:
  claim_id_sha256:
  authority_memory_preserved:
  structural_findings:
  output_readback_status:
  source_bytes_unchanged:
  pdf_rebuilt: false
  scientific_source_modified: false
  repository_committed_or_pushed: false
  required_cas_execution: NOT_EXECUTED
  canonical_claims: 30
  candidate_claims: 40
  canonical_promotion: false
  observational_data_used: false
  publication_authorized: false
  package_sha256:
  first_failure:
  overall:
```

Overall은 관측된 결과에 따라 다음 중 하나를 사용한다.

```text
K2FE_EXECUTED_CANDIDATE_MATERIALISED
K2FE_EXECUTED_WITH_STRUCTURAL_FINDINGS
K2FE_TEST_FAILED
K2FE_COMPILER_FAILED
K2FE_SOURCE_BINDING_FAILED
K2FE_SOURCE_ACQUISITION_BLOCKED
K2FE_RUNTIME_UNAVAILABLE
K2FE_SOURCE_DRIFT
```

Test assertion failure는 runtime unavailable이 아니다. Python 시작 전 backend 오류는 scientific failure가 아니다. Bundle 생성 성공도 CAS/claim/publication PASS가 아니다. 모든 결과에서 기존 K5 PDF 완료 상태를 유지한다.

## 7. 부모 스레드에서 확인한 출발 상태

이 handoff 준비 중 local shell/Python 요청은 모두 observable execution 전에 ClientError로 끝났다. WolframContext는 MCP/SSE HTTP 404를 반환했고 kernel calculation은 없었다. 기존 source head의 hosted K2 run `33940619037`, job `101237196566`을 새로 읽었으나 attempt 1의 기존 기록은 `runner_id=0`, `runner_name=""`, `steps=[]`, conclusion failure였다. 이 턴에서 explicit rerun을 요청한 것은 아니며 계정 billing 원인을 단정하지 않는다.

이 handoff에 적은 실행 recipe는 부모 환경에서 테스트된 스크립트가 아니다. Repo의 현재 workflow와 source를 읽어 재구성한 실행 지침이다. 정확한 Canonical Memory Verifier plugin은 discovery에서 나오지 않았으므로 그 서비스가 검증했다고 주장하지 않는다. 실제 보존 근거는 Git blobs, 원 입력, 원 실행 로그와 결과 receipt다.

마지막으로, PDF 조판 환경에서 Python 3.12가 이미 동작했던 work 스레드에서는 그것을 활용해 이 **K2FE 실행 하나를 끝내라**. 다시 PDF를 만들거나 운동학적 MES 중심안을 재설계하는 계획서로 회귀하지 않는다.
