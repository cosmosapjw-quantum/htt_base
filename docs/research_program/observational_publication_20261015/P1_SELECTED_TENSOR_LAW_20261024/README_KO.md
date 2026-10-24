# 선택 표본 텐서 법칙 원고: 빌드 안내

영문 원고의 진입점은 `main.tex`이며, REVTeX 4.2 단일 단 서식을 사용한다. 저자와 소속은 소유자가 제공하기 전까지 임의로 넣지 않는다.

## 재빌드

TeX Live의 REVTeX 4.2, pdfLaTeX, BibTeX, latexmk가 필요하다. 소스 묶음을 푼 디렉터리에서 다음을 실행한다.

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error main.tex
```

`main.tex`, `sections/*.tex`, `references.bib`, 참조된 `figures/*.pdf`가 PDF 재빌드 입력이다. `source_bundle.zip`에는 원시 관측 카탈로그나 내부 실행 영수증을 포함하지 않는다. 그림 PDF는 저장된 결과의 표시 또는 검토된 보고서 자산의 복사·형식 변환이다. 재빌드 과정은 과학 계산을 다시 실행하지 않는다.

## 범위

그림의 출처와 변환은 `FIGURE_PROVENANCE.json`, 과학적 주장 범위는 저자 작성 `SCIENTIFIC_SCOPE.md`와 `CLAIM_SOURCES.json`, 최종 빌드 결과는 `BUILD_REPORT.md` 및 `BUILD_REPORT.json`에 기록한다. PDF 컴파일, 독립 과학 검토, 출판은 서로 다른 단계다. 이 묶음 자체는 과학적 승인이나 물리적 전단 검출을 뜻하지 않는다.
