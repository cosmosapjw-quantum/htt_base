# A22 실행 재개 — 2026-10-23

기존 소유자 checkout, branch `research/htt-open-input-theory-20261018`.
시작 local/remote/PR #561 HEAD는 `a8fd176305fb475947a46f9dacb651805d323741`이다.
초기 working tree는 깨끗했다. 수정 V03 기준 18/42와 원래 외부 산출물 기준
17/42를 각각 추적한다. 논문 6개는 모두 NOT_READY_TO_SUBMIT이다.

| 작업 | 새 입력·모형·통계량 | 실제 산출물과 실패 기준 | 다음 소비자 |
|---|---|---|---|
| A22-03 | Quaia G<20 catalogue와 기존 Gaia CRF3의 exact source_id 연결 | 세 payload 검증, 중복·손실·cohort 표, PM covariance; ID/단위/유한성 실패 시 중단 | A22-05 |
| A22-04 | 같은 spectral source의 유한 observer 변환과 source-template fit; 공개 보정 근사 | paired finite test와 magnitude/redshift defect; fit/관측식 불일치·허용오차 초과는 보존 | V04/V05, H04 |
| A22-06 | HI 선택 cohort의 marked generative law와 별도 6dFGSv cohort | 정규화 분모·누락질량·실제 membership 민감도; parent확률 추측·중복 PV는 허용하지 않음 | H02/S02/S04/K04 |
| A22-07 | donor phase/orientation/parity algebra와 새로운 morphology control | blob 동등성, 동일 sky linkage, 새 통계 사전명세; 현실조건·power·rotation/parity 불일치 시 실패 | A22-08, L03/L04 |
| A22-05 | A22-03의 적색편이별 PM와 E/B 고차·선택 nuisance | Gaussian 저랭크 적분과 직접행렬 대조, whole-field mock 및 조건부 robust set | K03/K04/K05 |

실제 mount는 `/dev/sda2`→`/mnt/extdrive` rw, 여유 약2.3T다. 다운로드 상한은
없으며 `--budget-gib`를 사용하지 않는다. 기본2GiB reserve와 streaming 공간
검사를 유지한다. raw/행별 산출물은 Git 밖에 저장한다.

부모 요청 `gpt-6.1-sol/high`; 두 이론 계약 요청 `gpt-6-astra/xhigh`, read-only.
backend 관측은 UNKNOWN이다. 부모만 production 파일을 쓰고 publish한다.
동시 부모 포함 최대4, nested 없음; 별도 fresh read-only reviewer가 각 결과를 검토한다.
기존 Gaia/LP/projection/Planck split 캠페인은 재사용한다.

A22-03 완료: 755850행 전체에 PM covariance가 연결됐다. 기존692154행을 재사용하고
나머지63696개 ID만 anonymous TAP으로 보완했다. 새 raw 입력은 세 Quaia payload와
1640346-byte subset VOT이며 모두 Git 밖에 있다. [보고서](quaia_join/REPORT.md),
[독립 검토](quaia_join/INDEPENDENT_REVIEW.md), [그림](quaia_join/JOIN.png).
A22-05는 이 검토된 cache를 소비한다. 작업 중 별도 GR/CAS 디렉터리의 사용자
untracked 파일이 생겼으며 이 작업에서는 읽거나 수정·stage하지 않았다.
