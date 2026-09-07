# HTT Report A — K2FER1 bounded repair and K2FE replay

REPAIRED_AND_MATERIALISED_WITH_STRUCTURAL_FINDINGS

CPython 3.12.13/Linux에서 syntax exit 0, 기존·focused 회귀 40 PASS, strict 회귀 15 PASS를 확인했다. 기존 33개 node를 유지했고 skip/xfail/xpass/deselect는 모두 0이다. 생산 strict CLI를 한 번 실행하여 exit 0으로 여섯 파일을 생성했다.

독립 reader가 네 surface의 40개 unique ID 집합 일치, bibliography 20개, 원 30개+신규 10개, 예정된 statement revision 4개, authority memory/history, 상태 변환과 donor execution 비상속, 실제 input/output hash를 대조했다.

조건부 scope가 명시되지 않은 claim은 RA-ORBIT-004, RA-STAT-002, RA-STAT-003, RA-PROC-001, RA-ERR-004이다. 원 structural_findings 객체를 그대로 보존한다.

~~~json
{
  "conditional_scope_not_explicit": [
    "RA-ORBIT-004",
    "RA-STAT-002",
    "RA-STAT-003",
    "RA-PROC-001",
    "RA-ERR-004"
  ],
  "interpretation": "Findings remain visible; this compiler does not silently invent missing assumptions or certify theorems.",
  "numerical_execution_grade_missing": [],
  "source_only_execution_promotions": []
}
~~~

검증한 원 실패 ZIP SHA-256: 77329d5082a7c41c1977f7547fdefb1b6c2e57dde8de907aada560f95bfb112a. 내부 SHA256SUMS 83개, source manifest 27개와 두 원 JUnit 및 stdout/stderr를 대조했다. 원 archive와 추출본은 읽기 전용이며 원 26 PASS/7 FAIL, 생산 CLI 미실행, structural_findings=null 기록을 보존했다.

원 K2FE_RESULT.yaml은 ZIP 내부에 없었다. 같은 workspace의 별도 원 deliverable을 찾아 archive receipt와 값이 일치함을 검증하고 original_K2FE_RESULT.yaml로 보존했다. 실행 환경과 package 버전이 원 실행과 동일하여 unmodified baseline을 다시 실행하지 않았다. 새 whole-file citation 회귀의 RED 실행은 같은 YAML ScannerError를 실제 재현했으며 별도 로그/JUnit에 남겼다.

GitHub fresh read: head 9f44eb10b5c66d6d5132bedf15285fa09de58edb, tree 83d27c6c935d784ba68d071febca09be18b712aa, base 687234128d7c12d04e68aad0f303c21d2d470393. 원 실패 snapshot 이후 변경은 두 handoff 문서 추가뿐이었다. 수리 base는 a8d5417b3beae46e345392b5c2576c15be83a514이다.

수리는 27개 파일의 REPAIRED_HASH_VERIFIED_SOURCE_SET에서 수행했다. 전체 checkout이나 새 Git commit으로 표시하지 않는다. 원 source와 repaired source는 byte-identical하지 않으며 다음 네 파일만 바뀌었다. 나머지 23개 및 replay 전후의 27개 source bytes가 일치한다.

| Source | Old Git blob | New Git blob |
| --- | --- | --- |
| scripts/compile_report_a_k2fr0_authority.py | d89ac38f47e221597fbc2b152b4a6c591c673d81 | 3d90beb90646f0fe5a7d0212a5adaef7a77e4994 |
| scripts/compile_report_a_k2f_authority.py | d22e439211b0058596c27028d382554657b9f532 | 50aca195e6a5a433ee8c4370a38ee52b35e2f0e2 |
| tests/contracts/test_report_a_k1r_kinematical_mes_repairs.py | bed6f72f9498631f3b945b1d44c0820a4e13a5d9 | 90726a5a3fd58b8e8521994c151bb86609266ea5 |
| docs/codex_handoff/htt_tensorized_report_first_20260903/REPORT_A_CITATION_PROVENANCE_MATRIX_V2.yaml | 3fbaa2f97522cca6d0ad60e0c96655d293ca0d74 | 5087d39edf094f3adf7d72eed3061521ecf0b78d |

Citation YAML은 세 title 값에 quote 여섯 문자만 삽입했다. Legacy helper는 해당 citation pin 한 항목, strict compiler는 LEGACY_BLOB 한 항목만 변경했다. 두 compiler의 나머지 bytes는 동일하며 parser/publisher 로직과 나머지 일곱 input pin을 유지했다.

K1R 문서 guard는 해당 section의 active prose와 case-sensitive 수식을 확인한다. 두 원 test의 machine-readable assertion과 나머지 네 원 test는 유지했다. 새 22개 case는 whole-file parse 1개, 단일 unquote 3개, harmless formatting 2개, semantic mutation 14개, historical quote 2개다. 실제 내용 변경을 확인한 negative fixture 19개가 모두 기대한 오류로 거부됐다. 이 검사는 문서 계약을 검사하며 수학적 정리를 증명하지 않는다.

생산 receipt SHA-256: 0510b3ea21bdca35113d88a9797fb37f86bf645556a84621ec3b50be5838c81e. Sorted claim-ID SHA-256: f4f727da892a0d2cdc7d785aede3028ca0c57a7978518a662029fd5b2a6388db. 실행 argv/cwd/interpreter/exit와 분리된 stdout/stderr는 logs/, JUnit과 negative 상세 및 독립 readback은 receipts/에 있다.

Pre-edit intake helper의 첫 시도는 이전 세션 store 값 유실로 잘못 구성된 로컬 경로에서 AssertionError를 냈다. 경로 바인딩을 바로잡은 후 실제 ZIP 검증을 완료했다. 최초 오류와 복구 정보는 보존했다. 이것은 원 archive의 부재 또는 무결성 실패로 분류하지 않는다.

Canonical은 T9 v4 / 30 claims이고 산출물은 40-claim source candidate다. K5의 기존 24쪽 PDF는 재생성하지 않았다. 과학 원문·theorem pack·.bib를 수정하지 않았고 CAS, 관측 실행, BASS/REC/REI, finite-HEALPix rank 해결, claim 승격, commit/push/PR mutation/merge를 수행하지 않았다. Scientific acceptance와 publication authority는 부여하지 않았다.

재개 시 RESUME.md와 source_manifest.json을 사용한다. 기존 생산 output/receipt를 덮지 않고 새 RUN에서 같은 strict entrypoint와 등록된 회귀를 실행한다.
