# Work 스레드 실행 프롬프트 — HTT Report A K5 review PDF

@GitHub @Superpowers @Academic Writing Toolkit

## 목표와 승인 범위

`cosmosapjw-quantum/htt_base` PR #449의 **K4 수정이 반영된 전체 원고 revision 2**를 실제 TeX/PDF로 조판하고 페이지를 검사하라. Runtime inventory나 새로운 계획서만 반환하지 말고, 실행 경로가 있으면 이 응답에서 review PDF를 산출하라.

이 작업은 비canonical review artifact 제작이다. K2 compiler 통과, T9 v5 승격, CAS 검증, 관측 분석, publication/merge 승인이 아니다. BASS/REC/REI 소스나 물리 모델을 변경하지 않는다. 수정할 수 있는 것은 격리된 출력 디렉터리의 렌더링 metadata, 로컬 adapter 및 generated TeX의 조판 요소뿐이다. 수식의 계수·부호·전제·결론이나 inherited numerical values를 바꾸지 않는다. 기존 branch/source/test/workflow/claim ledger/bibliography를 수정하거나 commit/push/merge하지 않는다. 최종 산출물을 이 스레드에 파일로 반환하라.

## 1. 고정 입력과 live state 확인

마지막 확인한 source snapshot:

```yaml
repository: cosmosapjw-quantum/htt_base
pr: 449
branch: docs/htt-tensorized-mes-response-synthesis-20260903
source_snapshot: fc229262827edb750ceefc205e3f3e7c58d03e89
tree: dbebc9debf08588dc16c3c51115ab358701b1c5b
base: 687234128d7c12d04e68aad0f303c21d2d470393
state: OPEN_DRAFT_UNMERGED
canonical_ledger: T9_V4
canonical_claims: 30
review_candidate_claims: 40
candidate_bibliography_entries: 20
```

먼저 PR #449를 fresh read하고 live head/tree/base를 기록하라. 위 snapshot은 비교·렌더링 입력 identity이며 live head라는 주장이 아니다. 이 handoff 추가 같은 문서 변경만 있고 아래 입력 blob들이 같으면 진행한다. 원고가 달라졌으면 변경을 읽고 `SOURCE_DRIFT`를 기록하라. 이전 blob을 현재 최신본이라고 부르거나 새 원고에 옛 K4 replacements를 다시 적용하지 않는다. 검토된 revision 2를 렌더링하는 경우에는 그 snapshot을 명시한다.

필수 렌더링 파일과 Git blob SHA-1:

| 경로 | Git blob |
|---|---|
| `docs/research_reports/drafts/HTT_REPORT_A_FULL_KINEMATICAL_MES_DRAFT_K3_20260905.md` | `99a3f75c67ece3cfb00179bfd61787f47cb7e7ac` |
| `docs/research_reports/HTT_REPORT_A_REFERENCES.bib` | `ba37321119725e52f1a2b0ac827050ee895e5466` |
| `docs/research_reports/report_a/K2_BIBLIOGRAPHY_SUPPLEMENT_CANDIDATE.bib` | `930457120f5def21321008f4f77cc2b9c0f5694a` |
| `docs/research_reports/report_a/structure.lua` | `afaf143126319a864b7f08790348db20963d55d2` |
| `docs/research_reports/report_a/header.tex` | `21102ea9ae0a117fc921189884916226c13d5aae` |

40-ID 비교 입력:
`docs/codex_handoff/htt_tensorized_report_first_20260903/K2_40_CLAIM_CANDIDATE_OVERLAY.yaml`
의 snapshot blob `394378a796a24410a4174a8222e40c5c59e9700a`를 확인하고 `candidate_claim_ids`를 읽는다. 이는 후보 ID 집합이지 canonical v5가 아니다.

원고 제목은 다음과 같아야 한다.

**Tensorised Low-Multipole CMB Morphology, Kinematical Isotropy Bounds and Response-Limited Identification**

원고 전체에는 본문 12절, 부록 A–D, Appendix A의 40개 후보 claim이 있다. 5.1/8.2/11.2절 K4 수정은 이미 적용돼 있다.

## 2. Runtime 시도는 제한하고, 실제 가용 경로를 사용

우선 최소 shell/Python 프로세스를 한 번 실행하고 Python, Pandoc, latexmk/LaTeX 또는 Tectonic, PDF 렌더러의 실제 버전을 기록한다. 실행 backend 자체가 실패하면 독립 fallback 한 번까지만 시도한다. 같은 `print()`를 반복하며 세션을 소모하지 않는다.

로컬 checkout이 있으면 읽고 격리 worktree나 read-only snapshot을 사용한다. 직접 GitHub 네트워크가 막혔지만 connector가 source bytes를 제공하고 로컬 파일 쓰기가 가능하면, **완전한 원본 payload**를 받고 로컬 bytes의 Git blob hash를 검증해 최소 source mirror를 만들 수 있다. 전체 git clone의 부재 자체가 review PDF 금지는 아니다. 단, 요약문·수작업 수식 재입력·불완전한 line chunk를 byte-exact source라 부르지 않는다.

Git blob identity 계산은 `SHA1(b"blob " + decimal_byte_length + b"\0" + raw_bytes)`다. SHA-256은 별도로 계산한다. Snapshot, local blob identity, git ancestry, toolchain identity를 서로 구분한다. 단순 import 성공은 PDF compilation이 아니다.

PDF task를 위한 `/home/oai/skills/pdfs/SKILL.md`가 이 실행환경에 있으면 먼저 읽고 따른다. Repo의 `AGENTS.md`, `.agents/skills/htt-latex-paper-build/SKILL.md`와 관련 claim/provenance 규약도 읽는다. 해당 파일을 읽지 못했다면 읽었다고 주장하지 않는다.

**Python 3.12나 Lean의 부재만으로 비canonical PDF 작업을 중단하지 말 것.** 사용 가능한 rendering toolchain의 버전을 기록해 review artifact를 만들 수 있다. 이는 별도 K2 production CLI의 CPython 3.12 gate나 기존 CAS acceptance를 면제하지 않는다. Hosted CI가 막혀 있어도 로컬 PDF가 가능하면 로컬로 진행한다. 과거 첨부 runtime probe는 `0ae24eed...` snapshot의 기록이며 현재 실행증거가 아니다.

## 3. 확인된 구 조판 경로를 그대로 실행하지 말 것

현재 snapshot에서 다음은 구 30-claim draft를 위한 경로다.

- `report_a/pandoc.yaml`은 `../HTT_REPORT_A_THEORY_METHODS_DRAFT_R3_20260904.md`를 input으로 사용하고 기본 bibliography 하나만 읽는다. Blob: `f669c1ebdf402a2af9a6f96748a65396f635c4a3`.
- `report_a/metadata.yaml`의 title과 `hypersetup.pdftitle`은 구 원고 제목이다. Blob: `5ab67fb4bef8f5f7255ab3b78506952aa0dcde3e`.
- `scripts/validate_report_a_generated_tex.py`는 구 title/section 문자열을 요구하고, 현재 원고에 의도적으로 있는 `CURRENT_OBSERVATIONAL_RESULT`를 금지한다. Blob: `d0d480c58ae98874cd8f3774952cccce4b2f598e`.

이는 과학 원고를 다시 수리하라는 뜻이 아니라 **렌더링 대상 버전이 다르다는 뜻**이다. 기존 config/test를 느슨하게 수정해 PASS를 만들지 말고, 격리 출력 디렉터리에 revision-2 review 전용 metadata와 최소 검사를 둔다. 이 검사는 기존 R4B0 acceptance를 통과했다는 주장으로 사용하지 않는다. `docs/manuscript/main.tex`나 구 scalar manuscript를 렌더링하지 않는다.

## 4. 격리된 조판 경로

`REPO`를 검증된 checkout 또는 minimal source mirror의 절대경로로 설정한다. `OUT`은 비어 있는 새 출력 디렉터리의 절대경로로 설정한다. 기존 output을 덮어쓰지 않는다. 최종 파일은 이 환경에서 사용자에게 실제 전달 가능한 경로로 복사하고 그 경로의 존재를 확인한다.

출력 디렉터리에 `review-metadata.yaml`을 만들되 구 metadata를 상속하지 않는다. 최소 내용은 다음과 같다.

```yaml
title: Tensorised Low-Multipole CMB Morphology, Kinematical Isotropy Bounds and Response-Limited Identification
subtitle: Review candidate — K4-corrected revision 2; not a canonical release
author:
  - Jiwon Park
date: 2026-09-05
lang: en-GB
documentclass: article
classoption: [11pt, a4paper]
geometry: [margin=25mm]
reference-section-title: References
```

기존 `structure.lua`는 pre-Abstract prologue 제거, heading level 조정 및 한 번의 appendix 전환을 담당한다. Source bytes를 보존한 채 이 structural adapter를 재사용하되 결과를 확인한다. 리뷰 상태가 제거된 prologue에만 남지 않도록 위 subtitle을 유지한다. 모든 본문과 부록의 과학·provenance 경계는 보존한다.

다음은 공식 CLI 문서와 source config에서 작성한 **실행용 recipe이며 이 handoff에서 실행된 코드는 아니다**. 실제 설치 버전의 `--help`로 옵션을 확인하고 argv·cwd·exit·stdout/stderr를 보존하라.

```bash
# REPO와 OUT은 위에서 실제 절대경로로 확정한다.
set -euo pipefail
MANUSCRIPT="$REPO/docs/research_reports/drafts/HTT_REPORT_A_FULL_KINEMATICAL_MES_DRAFT_K3_20260905.md"
BIB="$REPO/docs/research_reports/HTT_REPORT_A_REFERENCES.bib"
SUPP="$REPO/docs/research_reports/report_a/K2_BIBLIOGRAPHY_SUPPLEMENT_CANDIDATE.bib"
FILTER="$REPO/docs/research_reports/report_a/structure.lua"
HEADER="$REPO/docs/research_reports/report_a/header.tex"

pandoc "$MANUSCRIPT" \
  --from=markdown+tex_math_single_backslash+raw_tex+citations+fenced_code_blocks+pipe_tables \
  --to=latex --standalone --number-sections --top-level-division=section \
  --lua-filter="$FILTER" --citeproc \
  --bibliography="$BIB" --bibliography="$SUPP" \
  --metadata-file="$OUT/review-metadata.yaml" \
  --include-in-header="$HEADER" --wrap=preserve \
  --log="$OUT/pandoc.json" \
  --output="$OUT/HTT_REPORT_A_K4_REVIEW.tex" \
  >"$OUT/pandoc.stdout" 2>"$OUT/pandoc.stderr"
```

`-d report_a/pandoc.yaml`을 추가하지 않는다. 구 입력과 title을 재상속하지 않는다. 두 BibTeX 입력을 함께 parse하고 key 중복과 cited-key 누락을 검사한다. 기존 17개 + 보충 3개를 PDF에 렌더링하는 것은 canonical bibliography 합병과 다르다.

설치된 LaTeX toolchain으로 실제 PDF를 compile한다. Repo skill에 따라 latexmk가 사용 가능하면 우선하고, 없으면 Tectonic 등 지원되는 engine을 사용한다. Tectonic V1 CLI 예시는 다음과 같다.

```bash
tectonic --keep-logs --keep-intermediates --outdir "$OUT" \
  "$OUT/HTT_REPORT_A_K4_REVIEW.tex" \
  >"$OUT/tectonic.stdout" 2>"$OUT/tectonic.stderr"
```

공식 release/package만 사용하고 실제 버전·다운로드 identity를 기록한다. 이 handoff는 최신 버전이나 특정 binary checksum을 추정하지 않는다. Missing executable/network/font-bundle는 환경 실패, TeX syntax는 조판 실패, 수식 의미 변경 요구는 scientific source 문제로 나눈다. 부재한 engine을 사용할 수 있다고 말하지 않는다.

원본 Markdown은 바꾸지 않는다. 실제 재현된 line overflow나 package 충돌 때문에 필요하면 출력 디렉터리의 header/template 또는 generated TeX만 최대 두 번의 bounded formatting repair로 수정하고 patch를 보존한다. 수학 기호 삭제, citation 제거, 통계 경계 삭제로 compile을 통과시키지 않는다. 새로운 scientific defect가 발견되면 위치와 재현 조건을 보존하고 부모 스레드로 반환한다.

## 5. Review-candidate 검사

출력 전에 다음을 실제로 검사하라.

1. 입력 Markdown의 Appendix A에 unique candidate ID 40개가 있고, candidate overlay의 ID 집합과 일치한다. Generated TeX와 PDF에서도 40개가 보존돼야 한다. 이는 후보 대응 검증이지 canonical 40-claim 승격이 아니다.
2. Bibliography는 중복 없이 20개 입력 항목을 parse하고, 본문 인용이 모두 해결돼야 한다. 미사용 항목과 unresolved citation은 따로 보고한다. 문자열 검색만으로 DOI/논문 내용이 검증됐다고 하지 않는다.
3. 본문 12절, 부록 A–D, 현재 title·PDF metadata, References와 review-candidate 표기가 있어야 한다. 수동 numbering이 중복되지 않고 appendix 전환은 한 번이어야 한다.
4. 5.1절의 expanding/common-rate convention과 MES 3/2, 8.2절의 `B_Q^*B_Q=3M_Q`, 11.2절의 `s_m(W K_obs)>=1+delta`, `delta>0`가 실제 화면에서 읽혀야 한다. 수식은 source의 의미를 보존한다.
5. 4.4절 physical functionals, observable/physical 비동일성, 동일자료 공동조건화, 두 finite-null lane, inherited numerical tables가 유지돼야 한다. `CURRENT_OBSERVATIONAL_RESULT = NONE`, `DEFERRED_BY_OWNER`, `RANK_UNRESOLVED`는 의도된 경계이지 삭제할 오류가 아니다.
6. TeX logs에서 undefined reference/citation, missing glyph/file, duplicate label, overfull box를 검사한다. Warnings를 숨기지 말고 개별 판정한다.
7. PDF 모든 페이지를 렌더링해 실제 시각 점검한다. 문자 추출만으로 visual PASS를 주지 않는다. 표·긴 수식·40-ID 부록·bibliography의 잘림과 겹침을 특히 확인한다. PDF를 볼 도구가 없으면 `PDF_BUILT_VISUAL_PENDING`이라고 반환한다.

원고의 Appendix D는 원래 drafting pass에서 하지 않은 작업의 역사적 기록이다. 별도 build receipt에 이번 실행을 기록하되 원고를 조용히 수정해 옛 이력을 덮지 않는다.

## 6. K2/CAS와 PDF의 분리

PDF가 만들어져도 K2FR0 compiler, T9 v5, required formal axes의 PASS는 아니다. 이 작업의 우선 산출물은 review PDF다.

PDF와 필수 산출물을 먼저 보존한 뒤, exact checkout과 해당 runtime이 실제로 갖춰져 있고 기존 계약을 읽은 경우에만 K2 실행을 별도 선택적 lane으로 진행할 수 있다. 기존 `scripts/compile_report_a_k2fr0_authority.py`, 관련 regression tests와 workflow를 읽고 그대로 실행하라. 실패하면 원 실패를 보존한다. 이번 범위에서 compiler나 과학코드를 수리하지 않는다. CAS axes의 독립성·필수축·버전·source binding·promotion 규약을 임의로 바꾸지 않는다.

K2/CAS blocked 상태를 이유로 이미 가능한 review PDF를 폐기하거나 미루지 않는다. 반대로 PDF 성공을 K2/CAS 성공으로 대체하지 않는다. GitHub-hosted admission을 시험한다면 관련 job 하나만 bounded retry하고, steps=[]를 scientific test failure로 분류하지 않는다. 새 workflow나 empty commit으로 재실행을 강제하지 않는다.

## 7. 산출물과 중단 조건

성공 시 실제 존재하는 파일을 제공한다.

- `HTT_REPORT_A_K4_REVIEW.pdf`
- generated `.tex`, review metadata 및 사용한 로컬 adapter/formatting patch
- 정확한 입력 source/bibliography 묶음 또는 재취득 가능한 snapshot/blob 목록
- commands, logs, page-review note, `K5_EXECUTION_RECEIPT.json`
- 위 파일들의 SHA-256과 source package

현재 파일시스템에 없는 sandbox 링크를 만들지 않는다. 실패 시에도 수집된 로그·TeX·receipt가 있으면 먼저 보존한다. 전체 backend가 실행 전 실패해 파일조차 만들 수 없으면 최종 답변에 원 오류와 미실행 항목을 반환한다. 성공을 연기하는 약속이나 새 계획안만 남기지 않는다.

Receipt의 최소 결과 필드:

```yaml
k5_result:
  observed_live_head: null
  rendered_source_snapshot: null
  rendered_manuscript_git_blob: null
  source_bytes_verified: false
  source_method: null  # EXACT_CHECKOUT or HASH_VERIFIED_MINIMAL_MIRROR
  python_version: null
  pandoc_version: null
  tex_engine_version: null
  tex_generated: false
  pdf_generated: false
  pdf_sha256: null
  page_count: null
  pages_visually_reviewed: 0
  candidate_claims_checked: null
  bibliography_entries_parsed: null
  unresolved_citations: null
  unresolved_rendering_findings: []
  scientific_source_modified: false
  repository_mutated: false
  k2_or_cas_receipts: NOT_EXECUTED
  canonical_claims: 30
  candidate_claims: 40
  observational_data_used: false
  publication_authorized: false
  overall: null
```

`overall`은 실제 수행에 따라 `REVIEW_PDF_BUILT_AND_VISUALLY_CHECKED`,
`PDF_BUILT_VISUAL_PENDING`, `TEX_ONLY_BUILD_BLOCKED`, `SOURCE_ACQUISITION_BLOCKED`,
`LOCAL_RUNTIME_UNAVAILABLE`, `SOURCE_DRIFT`, `RENDERING_FAILED` 중 하나로 둔다.
어느 것도 과학적 publication 승인을 뜻하지 않는다.

최종 답변은 (a) 무엇을 실제 실행했는지, (b) PDF/TeX/receipt 링크, (c) 페이지·인용 검사 결과,
(d) 남은 blocker, (e) 이 부모 스레드에 붙여넣을 위 machine-readable 요약으로 끝낸다.

---

## 이 handoff를 작성한 스레드의 관측 기록

2026-09-05의 이 패스에서는 container와 독립 Python fallback이 각각
`ClientError`로 종료해 observable process 실행을 확인하지 못했다. Wolfram
context connection은 MCP/SSE HTTP 404였다. GitHub read/write 경로는 별개로
작동했다. GitHub Actions explicit rerun은 요청하지 않았으므로 현재 hosted
runtime의 새 PASS/FAIL을 주장하지 않는다.

Fresh readback으로 원고 blob `99a3f75...`, 두 bibliography, 구조 filter와
header, 그리고 위 구 조판 config/validator의 target mismatch를 확인했다.
이 파일은 그 정보를 실행 가능한 다음 단계로 전달하기 위한 handoff이며,
그 자체가 실행 receipt는 아니다. AWT는 보충 BibTeX 3개에 대해 offline
형식 issue 0을 반환했지만 online metadata verification이나 20개 전체
citation acceptance를 수행하지 않았다. SciSpace의 이번 검색은 관련성이
낮아 반환 결과를 새 근거로 채택하지 않았다. Exact named Canonical Memory
Verifier는 검색에서 확인되지 않았고, 무관한 plugin은 설치하지 않았다.

CLI reference consulted (instructions, not proof of execution):
- https://pandoc.org/MANUAL.html
- https://tectonic-typesetting.github.io/book/latest/ref/v1cli.html
