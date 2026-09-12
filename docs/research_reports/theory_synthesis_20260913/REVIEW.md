# 문서·출처 검토

범위는 기존 연구 갈래의 이론 종합이며 과학적 수용이나 새 증명의 감사가 아니다. 최신 formulation을 분기별로 선택하고 R8, VT foundation, WU009, companion 연구와 카탈로그의 버전을 구별했다. 작성 중 원본 dirty checkout과 SQLite는 편집하지 않았다.

## 독립 검토와 수정

한 번의 독립 source/claim 검토 후 하나의 수정 묶음을 적용했다.

| 발견 | 조치 | 남은 상태 |
|---|---|---|
| Doppler source와 dimensionless velocity의 단위 불일치 | 11.2절에서 해당 항을 S_Doppler로 두고 정규화 미해결을 명시; 무조건적인 1/k 금지 주장 제거 | 원문·생산 코드는 보존; physical closure 의무 남음 |
| 관측 full-MV 복원에 T2 cyclic 실행을 잘못 귀속 | 28절에서 실행·해석·조건부 적용을 구분; 실제 null-cone 복원만 실행 기록으로 명시 | 관측 T2 domain/실행은 미확인 |
| 최신 contraction-fibre/Hausdorff 연구 누락 | 9.3절과 S54/S55에 고정 q, 단위 norm, 빈/한점/S3 섬유 및 경계 민감도 추가 | direct derivation, noncanonical; 새 CAS 승격 없음 |

부모 작성자가 수정 문장을 해당 고정 원문과 다시 대조했다. 리뷰 결과를 증명 status 변경으로 사용하지 않았다. 최초 검토의 findings와 수정 매핑은 [review_findings.json](review_findings.json)에 있다.

추가로 실제 depth_path는 교차 공분산 항을 자동 반영하지 않음을 13.2절에 명시했다. 보고서는 일반 공동법칙과 현재 구현을 구별하며 해당 코드를 고치거나 연구 계산을 실행하지 않았다.

## Academic Writing Toolkit

요청한 플러그인의 paragraph-logic review, citation audit, BibTeX verification을 실제 사용했다. 이는 결정론적 문장/서지 검사이며 수학적 검증이 아니다.

- 문단 검사: 초기 전체 초안에서 짧은 문단 경고 102개. 수식·anchor·표·메타데이터·서지 단락이 섞인 입력에 대한 길이 휴리스틱이므로 의미상 결함이나 102개의 논리 오류로 해석하지 않았다.
- 인용 connector: 최초 입력의 Source 콜론 누락과 단일 notes 파일/복수 번호 인용 제한으로 경고 2개. 원결과를 보존했다. Toolkit의 같은 로컬 검사기를 6개의 별도 Source notes에 적용하여 [1]–[6]의 누락·미사용·번호 간격·개수 불일치가 모두 0임을 확인했다. 중립적인 author/year 서지가 엄격한 IEEE Source 패턴과 다르다는 형식 경고 6개는 유지했다.
- BibTeX: 인용한 6개 항목에서 오류 0. 온라인 전문 검증은 수행하지 않았으며, 원문 제공처의 서지·초록 대조와 내부 식 출처를 별도로 기록했다.
- 내부 S01–S55는 고정 Git 원문 내용과 독립적인 source/index checker로 연결을 확인한다. AWT의 숫자 인용 검사를 내부 source 내용 검증으로 표현하지 않는다.

상세 도구 결과: [writing_toolkit_review.json](writing_toolkit_review.json). 독립 과학 검토 후 고친 식을 플러그인이 재증명했다고 주장하지 않는다.

## PDF·파일 검사

진입점은 REPORT.md → build_report.py → report.tex → report.pdf다. 별도 그림이나 관측 plot은 없고 표·수식은 본문에서 생성한다. XeLaTeX/latexmk로 빌드하며 check_report.py는 Markdown 절, source 키, 466행 원본 기록, 172개 제안의 JSON/CSV 일치, 내부 링크, 결정론적 TeX 생성과 전체 PDF 텍스트를 검사한다. 고정 원문의 Git 내용 확인은 --verify-git로 별도 수행한다.

렌더된 모든 페이지를 contact sheet로 열고 depth, tensorized formalism, 데이터–정리 대응 등 핵심 페이지를 확대 확인했다. 한글 띄어쓰기를 보존하도록 xeCJK의 CJKspace 옵션을 켰다. 최종 페이지 수·내용 hash·빌드 경고는 [validation.json](validation.json)에 기록한다. PDF packaging 메타데이터의 byte 재현은 과학적 동등성이나 새 검증 상태가 아니다.

## 운영 훅의 한계

subagent 결과는 카탈로그 작업 트리의 THEORY-REPORT-20260913에 작성되었다. 종료 훅이 원본 checkout의 무관한 EXTERNAL-FUSION-FOLLOWUP-20260829를 검사해 전달 메타데이터에 OPERATIONAL_NONPASS가 발생했다. 해당 run에 결과를 복사하거나 원본 pointer를 바꾸지 않았다. 실제 source 검토 결과와 운영 훅 상태를 구별하며 HOST_CODEX가 보고서 수정·최종 파일 검수를 수행했다.

작업 트리에서의 normal close도 초기 검토 입력이 수정 후 달라진 점과 result-envelope schema/필드 불일치로 통과하지 않았다. 초기 검토 봉인을 사후 수정하지 않고 실패를 보존했으며, 해당 작업 트리의 pointer만 abandon으로 해제했다. 최종 수정 파일은 check_report.py와 부모 source 대조로 검수했으나, 이 상태를 하네스 전체 PASS라고 부르지 않는다.

## 원격 게시 확인

산출물 커밋 `7e33771c300e4fdacb6c3606beff0cbe8ef3bcd0`을 일반 push한 뒤 별도 원격 checkout에서22개 보고서 파일의 byte 일치와 보고서 checker PASS를 확인했다. 고정 source55개를 원격 원문에서 직접 읽어 모두 SHA-256이 일치했다(본문 전송1,494,071 bytes). [remote_verification.json](remote_verification.json)은 확인한 산출물 커밋을 가리키며 이 기록 자체의 커밋 hash를 자기 참조하지 않는다. 원본74개 dirty/untracked 상태는 작업 전후 같았다.
