# HTT 전체 연구 갈래 종합 이론 보고서

각 연구 갈래의 최신 유지 결과를 모은 한국어 수학·물리·통계 이론서다. ‘최신’은 마지막 R8 커밋만을 뜻하지 않는다. 각 분기의 대체된 구판은 반복하지 않고, 유지된 결과·조건·미해결 의무를 연결했다.

- [보고서 PDF](report.pdf) · [본문 Markdown](REPORT.md)
- [출처·고정 커밋 지도](SOURCES.md) · [출처 CSV](sources.csv)
- [전체 연구 갈래 색인](COVERAGE_INDEX.md) · [CSV](COVERAGE_INDEX.csv) · [JSON](COVERAGE_INDEX.json)
- [조사된 연구제안 172개 구간](PROPOSAL_INDEX.md) · [CSV](PROPOSAL_INDEX.csv) · [JSON](PROPOSAL_INDEX.json)
- [검토·검수](REVIEW.md) · [기존 증명 목록](../../project_catalog/proofs/README.md)

중심 장은 [23절: 텐서 정규화와 통계 분석](REPORT.md#s23)이다. 물리 상태 → MES anchor body → 관측 response와 nuisance quotient → 함수별/집합별 통계 → 깊이 경로의 순서로 읽는다.

| 요청한 내용 | 본문 |
|---|---|
| low-ell morphology | 7–10절, 12절 |
| 단일 x/F/Q/G_F/Pi를 대체한 tensorized MES formalism | 6절, 21절, 23절 |
| CMB observable와 운동학적 양의 관계 | 11–12절, 16절, 23.3절 |
| redshift/depth local boost와 global tilt 구별 | 13절, 21절, 23절 |
| 별도 방법 간 연결 | 16–24절, 27절 |
| 보유 데이터 설명에 동원한 정리 | 28절: 실행·해석·조건부 적용 구분 |
| invariants와 observables의 관계 | 7–9절, 23.4절 |

55개 고정 source 항목을 연결했다. 색인의 466행은 현재 레지스트리 65, VT source 의무 123, VT programme 의무 28, WU009 78, 연구제안 구간 172의 합이다. 체계 간 같은 명제가 겹치며 **466개의 서로 다른 정리 또는 증명된 정리라는 뜻이 아니다**. 원문 레코드와 상태는 JSON/CSV에 보존한다. 본문 절 배정은 편집 주제 안내이며 수학적 동치 판정이 아니다.

본문의 식과 기존 결과를 정적으로 대조했다. 새로운 CAS·Lean 증명, 연구 테스트, 관측 분석·시뮬레이션을 실행하지 않았다. 연구 레지스트리와 SQLite도 바꾸지 않았다. 원격에서 이 보고서만 읽는 데 DB 복원은 필요 없다.

## 재생성과 확인

Python 표준 라이브러리와 TeX Live의 XeLaTeX/latexmk, Noto CJK 글꼴, Poppler를 사용한다. 연구 패키지를 import하지 않는다.

```bash
python3 docs/research_reports/theory_synthesis_20260913/build_report.py
python3 docs/research_reports/theory_synthesis_20260913/check_report.py
```

고정 Git 원문 객체가 있는 checkout에서는 다음 검사로 55개 source의 내용도 대조한다. 얕은 clone에서는 해당 고정 커밋의 추가 fetch가 필요할 수 있다.

```bash
python3 docs/research_reports/theory_synthesis_20260913/check_report.py --verify-git
```

PDF는 본문과 출처 지도를 포함하며 대형 명제 색인은 별도 파일로 제공한다. 본문 수정 시 Markdown을 편집하고 build 명령을 실행한다. 색인은 기존 조사 결과에서 만든 편집 스냅샷이며, 보고서 빌드가 DB나 명제의 상태를 자동 갱신하지 않는다.
