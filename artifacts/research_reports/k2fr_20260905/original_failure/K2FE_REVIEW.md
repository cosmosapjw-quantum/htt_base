# HTT Report A K2FE 실행 검토

결과: **K2FE_TEST_FAILED**. 분류는 **SOURCE_TEST_FAILURE**다. 원본 syntax 검사와 네 테스트 파일의 실제 실행을 완료했다. 필수 회귀 검사가 실패하여 생산 strict CLI는 실행하지 않았다. authority-bundle과 생산 K2F_COMPILATION_RECEIPT.json은 생성되지 않았다.

검토 방식: EXECUTOR_FAILURE_READBACK. 별도 독립 심사 또는 과학 명제 검증으로 주장하지 않는다.

## Source와 실행 환경

| 항목 | 실제 관측 |
|---|---|
| PR | cosmosapjw-quantum/htt_base #449 |
| Live head | a8d5417b3beae46e345392b5c2576c15be83a514 |
| Live tree | 6c45d9134b8d0a30a599e1194e5062957d510e53 |
| Live base | 687234128d7c12d04e68aad0f303c21d2d470393 |
| 실행 snapshot | a0784f2a1ce1f4a3fe14195a5f169e4959bd8391 |
| 실행 tree | 036bc001d333cbc61427179edea2bf77fba3ff0a |
| Live diff | K2FE handoff 한 파일 추가; 실행 표면 변경 없음 |
| Handoff blob | e7efaa12815e4d700c5a5b9fbf82d37068a629f0 |
| 생산 compiler blob | d89ac38f47e221597fbc2b152b4a6c591c673d81 |
| Helper blob | d22e439211b0058596c27028d382554657b9f532 |
| Workflow blob | d7d18171f8a91d13c2a10ddb316481bbe7fdacfd |
| Source method | HASH_VERIFIED_SOURCE_SET, 27개 파일 |
| Python | CPython 3.12.13; Clang 22.1.3 |
| Platform | Linux-6.18.35-x86_64-with-glibc2.39 |
| 고정 의존성 | pytest 8.3.5 / PyYAML 6.0.2 / pybtex 0.26.1 |
| 전이 의존성 | iniconfig 2.3.0 / packaging 26.3 / pluggy 1.6.0 / latexcodec 3.0.1 |
| pip | 25.0.1 |
| 원 source byte identity | 실행 전후 27/27 일치 |

전체 checkout은 아니다. 직접 clone은 인증 경로 부재로 exit 128이었다. 허용된 connector 원본 payload 경로로 전환했고, 27개 파일 모두 snapshot tree의 Git blob 및 byte length와 대조했다. Handoff의 명시적 15 pins도 일치했다. 원본 pytest.ini를 사용했고, 적용 대상 conftest 및 package initializer의 부재는 잘리지 않은 동일 snapshot tree로 확인했다. source mirror에 가짜 .git, 대체 initializer, 대체 config를 만들지 않았다.

실제 scripts namespace와 compiler/helper import는 이 mirror 아래에서만 해소됐다. PYTHONPATH와 PYTEST_ADDOPTS는 unset이었다. Bytecode 및 테스트 임시는 RUN 아래에 저장됐고, source 아래 추가 파일은 pytest cache뿐이다. 전체 repo의 모든 blob을 검증했다고 주장하지 않는다.

## 실제 실행

| 단계 | collected | passed | failed | errors | skipped | exit |
|---|---:|---:|---:|---:|---:|---:|
| Syntax: 지정된 py_compile 3개 대상 | 해당 없음 | 해당 없음 | 해당 없음 | 해당 없음 | 해당 없음 | 0 |
| 기존 K1R/K2/helper 회귀, 3개 파일 | 18 | 15 | 3 | 0 | 0 | 1 |
| Strict hardening 회귀, 1개 파일 | 15 | 11 | 4 | 0 | 0 | 1 |
| 합계 | 33 | 26 | 7 | 0 | 0 | 해당 없음 |
| 생산 strict CLI | 실행 안 함 | 해당 없음 | 해당 없음 | 해당 없음 | 해당 없음 | null |

xfail=0, xpass=0. 실제 JUnit testcase, pytest 요약 및 원본 test marks를 근거로 기록했다. 두 그룹은 각각 한 번 실행했고 수리·재실행하지 않았다. 두 번째 그룹은 handoff가 허용한 독립 결과 수집이다. 첫 그룹의 실패를 무시한 acceptance가 아니다.

Command argv/cwd/UTC 시작·종료 시각/exit는 logs/*.json, 원 stdout/stderr는 동일 stem의 .stdout/.stderr, JUnit은 receipts/k2-existing-tests.xml과 receipts/k2fr0-tests.xml에 있다. JUnit이 기록한 -04:00 timestamp는 원문 그대로 유지했다.

## 최초 실패와 원인 구분

최초 실패는 tests/contracts/test_report_a_k1r_kinematical_mes_repairs.py:65의 test_k1r_joint_identification_and_shared_data_firewall이었다.

```text
AssertionError: required substring absent:
Their appearance as separate set factors does not make them independent evidence
```

원 theorem pack에서는 이 문장이 “Their” 다음에서 줄바꿈돼 있다. 별도 문자열 진단에서는 공백 정규화 후 해당 첫 문장이 발견됐다. 이 진단은 실패한 원 test를 PASS로 바꾸지 않는다. 같은 test가 뒤이어 요구하는 “feasible response-kernel fibre contains no other admissible state”는 공백·대소문자 정규화 후에도 그대로 존재하지 않는다. Theorem K1R-T9에는 singleton/kernel의 수식 기준이 있으나, 이것을 자동으로 해당 문장과 동등한 scientific entailment 증거로 채택하지 않았다.

두 번째 원 assertion failure는 같은 test 파일 133행의 test_k1r_scientific_firewalls_remain_closed다. 첫 불일치는 “no physical shear, vorticity or acceleration estimate”의 줄바꿈이다. 이후 요구된 finite-HEALPIX 표현에는 HEALPix 대소문자 불일치가 있고, observable-to-physical 문장도 줄바꿈돼 있다. 전체 진단은 receipts/documentary_failure_diagnosis.json에 있다.

세 번째 실패 및 strict 그룹의 네 실패는 모두 아래 **동일한 고정 source YAML 오류**다.

경로: docs/codex_handoff/htt_tensorized_report_first_20260903/REPORT_A_CITATION_PROVENANCE_MATRIX_V2.yaml  
Git blob: 3fbaa2f97522cca6d0ad60e0c96655d293ca0d74  
필드: source_registry.RANDOMIZATION_2024.title

```text
yaml.scanner.ScannerError: mapping values are not allowed here
  in "<unicode string>", line 42, column 35:
        title: Randomization Inference: Theory and Applications
                                      ^
```

인용부호 없는 scalar 안의 colon-space가 원인이다. 원본 PyYAML 6.0.2가 실제로 반환한 오류이며, Git blob은 handoff와 일치한다. 다운로드 손상, Python 부재, dependency 부재, source binding failure로 분류하지 않는다.

| 실패 test | 관측 원인 |
|---|---|
| test_k1r_joint_identification_and_shared_data_firewall | exact-substring AssertionError |
| test_k1r_scientific_firewalls_remain_closed | exact-substring AssertionError |
| test_exact_repository_inputs_compile_to_one_forty_claim_authority_bundle | 위 YAML ScannerError |
| test_mid_write_failure_leaves_no_published_bundle | 위 YAML ScannerError |
| test_corrupt_staged_write_is_detected_before_publication | 위 YAML ScannerError |
| test_destination_race_does_not_replace_even_an_empty_directory | 위 YAML ScannerError |
| test_strict_six_file_bundle_is_deterministic_and_preserves_all_bijections | 위 YAML ScannerError |

네 strict 실패는 citation parse에서 발생했으므로 staged write·corruption check·destination race·renameat2 publication을 실제로 검증한 결과가 아니다. **FILESYSTEM_PUBLICATION_FAILURE는 관측되지 않았고 해당 경로는 NOT_REACHED**다. Backend prestart 및 interpreter/dependency failure도 관측되지 않았다. Python exception이 test call 도중 발생하여 JUnit은 이를 failure로 분류했으며, JUnit errors는 0이다.

## 생성되지 않은 결과

- 생산 CLI attempts=0, exit=null. RUN 부모는 존재하고 authority-bundle은 존재하지 않는다.
- 여섯 파일 bundle 및 원본 생산 K2F_COMPILATION_RECEIPT.json은 생성되지 않았다.
- 구조 findings, coverage booleans, 40-ID 출력 bijections, 출력 bibliography 20개, 출력 ID digest와 payload hash readback은 모두 NOT_EXECUTED/null이다. 빈 findings 배열로 대신하지 않는다.
- authority-memory 관련 lower-level 회귀 test가 통과한 사실은 production bundle readback을 대체하지 않는다.
- 원본 “existing receipt” 회귀 test가 17-byte 문자열 “previous receipt\n”을 K2F_COMPILATION_RECEIPT.json이라는 임시 파일에 썼다. 이것은 의도적인 test sentinel이며 생산 compiler receipt가 아니다. Package에는 이를 compiler output으로 넣지 않았고 별도 inventory로만 기록했다.

Canonical T9 v4/30을 유지한다. Candidate 40은 요청된 source target이지 생성 성공 count가 아니다. CAS, scientific verification, claim/canonical/publication promotion, PDF 재생성, 관측 데이터 사용, commit/push/merge/PR metadata mutation은 수행하지 않았다. K5의 이미 전달된 24쪽 PDF 상태와 사용자 제공 digest 기록은 유지하되, 이 실행에서 PDF binary hash를 다시 계산한 것으로 표현하지 않는다.

## 복구한 source 취득 단계 오류

Git clone의 인증 실패는 logs/01_git_clone.*에 보존했다. 또한 실행자가 작성한 최초 materialiser가 모든 regular file mode를 100644로 가정해 AssertionError로 종료했다(logs/02_materialise_source.*). 원본에는 executable mode 100755 파일이 있었다. 별도 v2 materialiser에서 두 원본 mode를 허용하고 기존 bytes를 먼저 비교한 후 미확보 파일만 만들었다. logs/03_materialise_source_modes.*에 성공 및 27개 byte 검증을 기록했다. 이는 source 취득 보조 도구의 오류로, repository compiler/helper/tests/input을 수정한 것이 아니다. 원 helper와 그 오류 로그도 package에 남겼다.

## 후속 최소 수정 제안 — 이 실행에서는 미적용

1. Owner가 새 source revision에서 위 title을 적법한 quoted YAML scalar로 고친 뒤, 영향받는 입력 pins와 handoff를 새 identity로 명시적으로 재발행해야 한다. 기존 snapshot의 hash를 조용히 새 파일에 맞추면 안 된다.
2. K1R 문서와 두 exact-substring contract를 대조하여 줄바꿈·대소문자와 실제로 없는 fibre prose 요구를 각각 처리해야 한다. 공백 정규화 하나로 전부 해결된다고 주장하지 않는다.
3. 승인된 새 snapshot에서 원 syntax 및 네 test 파일을 다시 통과시킨 뒤에만 strict CLI를 실행하고 여섯 파일을 readback한다. 이번 실패 snapshot에서 CLI를 강제 실행하거나 source를 패치하지 않는다.

이 제안은 repair implementation 또는 새로운 과학 가정이 아니다. 최초 실패와 후속 미실행 단계를 유지한 실행 closeout이다.

