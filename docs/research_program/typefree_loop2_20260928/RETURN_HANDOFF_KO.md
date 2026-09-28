# HTT/MES 유형 미지정 Loop 2 — 외부 감사용 근거

## 현재 기준과 산출물

- 연구 시작과 게시 직전 원격 확인 기준: 기존 checkout main HEAD=origin/main
  96c0b2cb59765c36860da2049021c25a240d0c9b,
  tree=f11d29925a6ec29960ae2ec17b042b867f4f19b5.
  이 패키지 기준 commit과 차이 없음. branch reset/clone/worktree/force push 없음.
- 기존 추적 사용자 수정 7개와 미추적 자료는 보존했다. 이 문서와 아래 Loop 2
  근거 및 Lean 소스는 외부 감사용 Git commit에 포함된다. 게시 commit과 원격
  ref의 실제 동일성은 게시 기록으로 확인한다. Git 게시 자체는 과학 판정이 아니다.
- [결과·증명·반례](RESULTS_KO.md),
  [TF-W1의 실제 입력 계약](TF_W1_INPUT_KO.md),
  [공통 claim contract](CLAIM_CONTRACT.json),
  [엔진·버전·raw SHA 기록](ENGINE_RUNS.json),
  [새 독립 판정 상태](INDEPENDENT_DECISION_LOOP2.json) 및
  [연구 상태](state/RESEARCH_STATE.md)를 읽는다.
- Loop 1 원본 자료의 선택된 6개 파일은 [source](source/)에 바이트 그대로
  추출했고, ZIP 전체는 압축 해제하지 않았다. [패키지 검사](source/PACKAGE_INTEGRITY.json)는
  101/101 manifest 항목의 byte/hash 일치, 중복·경로 이탈·symlink 없음,
  ZIP CRC 통과다. 원본 ZIP·DB gzip·Release/history는 그대로다. 원본 Loop 1
  ZIP 자체는 이 Git commit에 포함하지 않는다. 선택된 원문과 복사 DB의 감사는
  가능하지만 ZIP 전체 101개 항목의 외부 독립 재검증에는 별도 원본 ZIP이 필요하다.

## DB 및 source lineage

첨부된 THEORY_INHERITANCE.sqlite.gz와 ZIP 내부 gzip은 59,025,657 byte,
SHA-256 17288a47268253aa3e0eb4b6a7f8027562dd8995febd0b917db8632772521614로
서로 같다. /tmp/htt_typefree_inheritance_loop2.sqlite라는 **새 파일명**으로 푼
원본 SQLite는 548,917,248 byte, SHA-256
6587bf88aa161ff2bd345610cdc8485c5e50095c750643359e2de4851537a4cc이고
integrity_check=ok다. [QUERY_EXAMPLES.sql](source/QUERY_EXAMPLES.sql)의
[raw 결과](source/QUERY_EXAMPLES_RAW.csv)는 stderr 0으로 실행됐다:
기존 confirmed 345/unconfirmed 39,937, Loop 1 보정 분석 13,
checkpoint inventory 702. 원문 후보 20개의 [계승표](source/INHERITANCE_MAP.json)는
원본 anchor, 역사적 status, 후속 TF-ID를 분리한다.

[append migration](db/apply_append.py)은 **새 복사본에만**
loop2_evidence 6행과 loop2_source_lineage 7행을 추가했다.
[migration receipt](db/MIGRATION_RESULT.json)에는 원래 네 역사적 테이블의
행 수가 40282/40467/13/104780으로 전후 동일하고
integrity_check=ok라고 기록됐다. 새 압축 DB는
[THEORY_INHERITANCE_LOOP2.sqlite.gz](db/THEORY_INHERITANCE_LOOP2.sqlite.gz),
59,023,959 byte, SHA-256
f628cfb059d641718f4c43531d1dc0e4d66d261fe3f35239a34a277610a5a5c7다.
이후 증명·transcript의 최종본 5행과 Lean source 1행을 같은 **복사 DB의 새
테이블에만 추가**했다. [최종 append receipt](db/MIGRATION_FINAL_RESULT.json)의
총계는 evidence 11행/source lineage 8행, integrity_check=ok, 역사적 네
테이블 전후 동일이다. 현재 완성된 복사 DB는
[THEORY_INHERITANCE_LOOP2_FINAL.sqlite.gz](db/THEORY_INHERITANCE_LOOP2_FINAL.sqlite.gz),
59,023,390 byte, SHA-256
393bdfa1a8a61a3aba54a2c64db38b93d7258e7d4802717d8b6c61fcb468c676이다.
첫 압축본은 중간 append 이력으로 보존했다. 원본 historical table/status를
수정하지 않았다.

최종 선택 검증: 새 DB gzip CRC 검사 통과; 복사 DB integrity_check=ok;
evidence+lineage 19/19개 경로의 현재 파일 SHA-256 일치; 이 인계와 루트
README의 로컬 상대 링크 41/41개 존재; Lean 최종 kernel compile exit 0;
Wolfram/Sage/SymPy 실행 exit 0; git diff --check 통과. 과학 full suite와
ODE/진화 solver는 실행하지 않았다.

## 실제 검증과 과학적 한계

| 엔진 | 실제 결과 | 범위 |
|---|---|---|
| Wolfram 15.0 + xAct xTensor 1.3.0/xCoba 0.8.6 | TF-P3 metric 2-jet의 λ 독립, G(0)=diag(6b,0,0,0), ∇₀T¹₀=−2λ/κ, A¹=c²λ/(3b), θ=σ=ω=0 exact | 총 Einstein source의 국소 점 결과 |
| Wolfram | TF-P2 열별 norm, Frobenius 직교분해 잔차 0; P3에서 bound 포화 | eigenvector 미분·spectral theorem의 기하 연결은 수기 |
| Lean 4.31.0 + mathlib fabf563a7 | TF-S2/S4 네 구성요소, TF-P2 diagonal 3열 gap 추정과 3×3 직교분해 kernel compile; sorry/admit 없음, axiom 목록 출력 | full-law/measurability, 일반 self-adjoint 대각화·기하 연결, S1/S3는 미형식화 |
| SageMath 10.9 + Singular 4.3.2 | 미분류 C의 Jacobi 3식, Singular Gröbner 5식, semialgebraic 실수 image 대조 | ideal이 positivity/real feasibility를 보증하지 않음 |
| SymPy 1.14.0 | 독립 수식 경로로 P3의 점 curvature 및 ∂₀G₁₀ 재확인 | 같은 Host 실행; blinded CAS axis가 아님 |

세 요청 엔진은 [동일한 claim contract SHA](CLAIM_CONTRACT.json)를 기록한다.
서로의 수치값을 입력으로 사용하지 않았다. 실행된 claim은 각기 다르므로
4-axis 공동 CAS PASS가 아니다. 수기 Loop 1 판정도 이번의 kernel proof 또는
관측 검증으로 재명명하지 않았다.

R2 monopole finite window의 w, A, m, s 및 endpoint error는 명시했으나
실제 time/source law, optical depth, selection, nuisance, joint anchor,
stress-gradient observational budget가 없다. 따라서 실제 식별 tensor 조합,
MES percentage, p-value는 UNAVAILABLE. 한 CMB sky를 time series로 쓰지 않았다.

## 하네스와 남은 blocker

사용자 지정 GPT-6 Astra ultra에 대해 저장소 model router는 gpt6-astra 연구
하네스 v4.0.0을 **선택**했다. 이 선택은 현재 Host 모델·effort를 바꾸거나
증명하지 않는다. 현재 API는 Host의 Astra subvariant/effort attestation을
노출하지 않아 실제 Host 세부모델은 미확인이다. 로컬 codex-cli 0.157.1,
Python 3.12.3, SQLite 3.45.1, Git 2.43.0을 확인했다. 기존
R9-D2-D4-CODEX-20260922 active work-unit/비용 예산은 재설정하지 않았다.

새 독립 과학 판정은 **HOLD_INDEPENDENT_REVIEW_UNAVAILABLE**이다.
저장소 하네스에는 현재 R9 active run이 있어 별도 등록 assignment를 열려면
그 실행을 닫거나 재결속해야 한다. 기존 연구를 보존하고 등록되지 않은
subagent를 만들지 않았다. Host 자가검토와 CAS 출력을 독립 판정으로 표시하지
않는다. TF-P2의 일반 self-adjoint spectral bridge와 기하 연결, TF-S1/S3의 정밀 domain branches,
TF-S2/S4의 결합 통계 statement, TF-C1의 일반 real feasibility,
TF-W1의 실제 source/law가 남았다. I2 DEFENDED_CONDITIONAL,
I3 HOLD_INPUT_INCOMPLETE, 기존 science HOLD는 변하지 않았다.

MLflow tracing/evaluation 지침은 검토했으나 이 작업에는 평가할 LLM agent
entrypoint가 없고 현재 Python에 MLflow가 설치되지 않아 agent 평가 실행은
없다. ODE/PDE/Boltzmann solver나 코드 DB 전체 다운로드도 없다.
