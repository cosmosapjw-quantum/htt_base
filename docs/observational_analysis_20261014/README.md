# 관측 분석 실행 결과와 다음 과학 단계

감사 #530 (`6365e36d0ccc6acddb7f6909aacea8d766c0fc4a`) 위에서 R1/R2 이식을 검토하고, 현재 보유 자료를 실제 결과·그림·보고서로 잇는 세 실행기를 추가했다. 감사 스냅샷은 99개 PR의 병합이나 과학적 승인으로 취급하지 않았다.

## 바로 읽을 결과

- [현재 종합 보고서](results/report/report.md): DESI 요약량, CF4 표본·조건부 감도, CMB 같은 하늘의 제품 차이.
- [DESI 공개 요약자료 결과](results/desi/analysis.md): z_eff=0.295234695에서 D_V/r_d=7.924712 ± 0.150734 (1 sigma), 배포된 고정 Gaussian 요약량 조건부. 새로운 우주론 적합이나 독립 관측 추가가 아니다.
- [CF4 coverage](results/report/cf4_coverage.png), [CF4 sensitivity](results/report/cf4_sensitivity.png), [CMB contrast](results/report/cmb_same_sky.png), [DESI likelihood](results/desi/desi_bao_summary.png). 같은 basename의 PDF도 제공한다.
- [실행 준비 결과](results/preparation/PREPARATION_REPORT.md): 이번 실행의 두 Python 환경과 현재 입력/runner 접근 확인.

DESI 원자료 reader/likelihood를 실제 실행했다. CF4/CMB 수치는 수용된 R2-02/R2-03 JSON에서 재사용했으며, SVD·원본 지도 reduction·합성 injection을 반복하지 않았다. 원자료·모의 자료·파생 요약량을 새 독립 likelihood로 세지 않았다. `report.json`과 `figure_data.json`에 현재 source-report hash, 재사용 상태, 그림 생성식/단위, 출력 hash가 들어 있다.

## 다음 작업

[CODEX_HANDOFF_KO.md](CODEX_HANDOFF_KO.md)를 복사하여 기존 checkout에서 이어간다. [NEXT_TASK.json](NEXT_TASK.json)은 작은 시작 packet이며 [ANALYSIS_PLAN.json](ANALYSIS_PLAN.json)에 OA00–OA11 의존성과 수용 조건이 있다. 이번 게시로 OA00–OA04의 중간 결과 경로가 실행됐다. 다음 과학 작업은 OA05 CF4 관측법칙/실제 적합이며 OA06 CMB 및 OA07 DESI physical response와 병렬 조사할 수 있다. 공동 posterior, posterior용 legacy adapter, 최종 물리 결과 보고서는 OA08–OA11에서 이어간다.

실제 남은 구현은 [repo 검토](REPO_REVIEW_KO.md)에 정리했다. R1의 네 sibling PR는 현재 tree에 없으므로 필요할 때 source별로 재사용한다. DESI summary conditioning adapter와 현재 POSTERIOR를 거부하는 legacy adapter의 확장은 별도 과학적·구현 작업이다. 상위 증명 유효 전제는 채택하되 관측법칙 적격성·물리 입력을 대신하지 않는다.

## 검증

- targeted pytest: 49 passed, exit 0 (`evidence/combined_0.log`). 기존 Gaussian/intake 회귀 포함. 두 warning은 Matplotlib PDF backend의 Pillow deprecated mode 인자이며 결과 생성은 성공했다.
- 실제 DESI 실행: exit 0 (`evidence/initial_1.json`).
- preparation 및 최종 report 실행: 모두 exit 0 (`evidence/delivery_0.json`, `evidence/delivery_1.json`).
- 4종 그림 실제 렌더 검토. 초기 보고서의 colorbar margin/legend 위치를 수정하여 최종 `results/report`에 생성했다.
- canonical DAG strict 검사 통과 (`evidence/dag_validation.json`). 새로운 작업의 extension 등록 누락은 policy 목록에 추가하여 해결했고 검사기는 수정하지 않았다.
- 독립 검토 판정과 최종 candidate binding은 `review/`를 따른다. 원격 게시와 merge는 별개의 상태다.

완료된 동일 입력 결과는 재사용한다. 명령의 새 output directory는 재현 또는 변경된 입력의 실행을 위한 것이며 완료된 결과를 다시 만들라는 요구가 아니다. 이 문서의 경량 분석 산출물이 실제 공동 posterior나 native Bianchi 검출을 뜻하지 않는다.
