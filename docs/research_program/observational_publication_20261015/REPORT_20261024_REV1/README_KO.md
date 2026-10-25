# 영문 REVTeX 연구 보고서

완성된 보고서는 [main.pdf](main.pdf), 원고와 인용문헌 및 사용된 그림을 담은 재빌드 묶음은 [source_bundle.zip](source_bundle.zip)입니다.

보고서는 Cosmicflows-4, Pantheon+, Gaia–Quaia, Planck 자료와 조건부 수학·통계 실험의 기존 결과를 정리합니다. 관측량과 물리적 해석을 구분하며, 자료·선택·공분산·응답 모형에 남은 제한을 본문과 각 그림 설명에 기록합니다.

그림 전체 조사, 제외 사유와 원본 경로는 [FIGURE_INVENTORY.json](FIGURE_INVENTORY.json)에 있습니다. 원본 그림과 과거 후보는 보존하며, 출판용 그림의 용어만 바꾸거나 제목·각주를 문서 배치로 제외한 경우 그 절차와 해시를 `figure_audit/`에 기록했습니다. 새로운 적합, 모의 자료 생성 또는 물리적 승인 절차를 수행하지 않았습니다.

LaTeX 재빌드에는 REVTeX 4.2, pdfLaTeX, BibTeX 및 latexmk가 필요합니다. 소스 묶음을 푼 뒤 `latexmk -pdf -outdir=/원하는/빌드/경로 main.tex`를 실행하십시오. 패키지에는 본문이 참조하는 그림이 포함되며 원자료 카탈로그와 내부 실행 기록은 포함하지 않습니다.

실제 빌드 명령, 페이지·그림 수, 인용 및 참조 검사, 경고와 파일 해시는 [BUILD_REPORT.md](BUILD_REPORT.md)와 [BUILD_REPORT.json](BUILD_REPORT.json)에 기록됩니다.
