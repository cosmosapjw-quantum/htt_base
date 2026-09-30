# C04 후속 준비물의 저장소 게시와 로컬 실행 인계

이 폴더는 `GRSTAT-CAS-CORR-20260930-1420KST` 반환에 대한 정정 검토와 C04 보완 소스를 보존한다. 원 연구 게시 커밋은 `11602167b64e4f0c50c1f57c37fe9df2292f9725`다. 이 문서를 추가한 Git 커밋이 이번 게시 identity이며, 실행 결과의 identity와 구분한다.

## 읽기 및 실행 순서

1. 저장소 `AGENTS.md`, `docs/harness/CURRENT_CODEX_RUNTIME.md`, 현재 선택된 로컬 global authority를 읽고 기존 task IDs·비용 기록·dirty/untracked 파일을 보존한다.
2. [검토 보고서](FOLLOWUP_REPORT_KO.md), [현재 과학 상태](FOLLOWUP_STATUS.json), [일반 증명](C04_CERTIFICATE_THEOREM.md), [소스 검토](NEW_C04_SOURCE_REVIEW.md)를 읽는다.
3. [로컬 실행 프롬프트](NEXT_LOCAL_PROMPT_KO.md)를 적용한다. 새 실행 소스는 최상단의 [SymPy](c04_sympy_certificate.py)와 [Sage/Singular](c04_sage_certificate.py)다. 각 SCOPE 문서에 실행법과 신뢰 경계가 있다.
4. 계약은 [보존 사본](intake/contracts/CAS13-C04-RELATIVE-MINIMAX.json)과 로컬 원 run의 계약을 대조한다. SHA-256은 `0002809c73fd5de362deded39735fe884183bb953029f671552a525f74086f63`다. 원 계약이 참조하는 환경·허용 입력·runner provenance도 별도로 확인한다. 그 입력이 없으면 준비 사본만으로 실행 적격성을 선언하지 않는다.
5. `C04` 한 건만 새 run으로 실행한다. 먼저 두 새 소스의 자체 변조 거절 검사를 실행하고, 명제 정렬 후 네 축의 실제 실행을 기록한다. Lean은 원 반환에서 관측된 저장소 고정 toolchain과 formal_mathlib 위치를 현재 로컬 파일로 확인한다. 옛 로그를 새 실행 결과로 복사하지 않는다.
6. 새 RUN_ID, 소스·계약 hash, 실제 argv/cwd/exit/version, 네 축의 정확한 aggregate, reviewer admission, 원시 근거 manifest를 반환한다. 등록 reviewer의 비용 범위 차단은 지원된 routing으로만 해결하며 이 대화의 검토를 그 등록 완료로 대체하지 않는다.

## 원본과 이번 게시의 구별

- 원 묶음의 66개 파일을 바이트 그대로 보존했고 ZIP 자체도 함께 제공한다. [원 묶음 manifest](ARTIFACT_MANIFEST.json)는 자신을 제외한 65개 파일을 대상으로 한다. 이번 두 게시 안내 문서는 원 manifest의 대상이 아니다.
- 원 README와 FOLLOWUP_STATUS의 `commit/push=false`는 인계 작성 당시의 역사적 상태다. 이후 게시 여부는 이 폴더를 추가한 원격 Git commit/ref로 판별한다. 과거 기록을 소급 변경하지 않는다.
- `intake/`는 선택적으로 조회한 반환 원문·소스·로그이며 원 run의 466개 전체 백업이 아니다. 그 안의 PASS와 CAS_CONFLICT는 과거 실행 기록이다.
- 새 수학 엔진 실행은 미수행이다. 현재 C04 aggregate는 CAS_CONFLICT이고 scientific conditional/HOLD는 유지한다. 원 계약 closure, 관측 fit, novelty·Bianchi 분류 승격은 없다.
- 이 게시로 production 패키지, 기존 계약, DAG의 완료 상태, 사용자의 로컬 변경을 수정하지 않는다. 이번 산출물의 목적은 로컬 C04 보편 인증 실행 준비다.

## 게시 검증과 복구

게시 전: 원 manifest 65/65, ZIP 66멤버의 원문 동일성, 두 새 소스의 기존 구문·실패경로 검사 6개 및 범위가 제한된 소스 검토를 확인했다. 별도 패키지 검토는 credential·전송URL·임시 다운로드 메타데이터가 없음을 확인했다. 이 검사는 수학 엔진 PASS가 아니다. 등록 로컬 독립 reviewer admission은 미완료다.

게시 방법: 원격 main의 현재 tree 위에 이 폴더와 상위의 읽기 포인터만 추가하는 단일 커밋을 만들고 non-force fast-forward로 반영한다. 원격 ref/commit/tree를 확인하는 R1을 사용한다. 전체 저장소 clone/worktree, 강제 push, reset, 재다운로드 검증을 하지 않는다. CI 통과를 이 문서가 미리 선언하지 않는다.

복구가 필요하면 이 폴더를 추가한 커밋을 통상적인 revert로 되돌린다. 이후 다른 변경이 있으면 그 변경은 보존한다. 로컬 과학 결과나 원 run을 삭제하지 않는다.
