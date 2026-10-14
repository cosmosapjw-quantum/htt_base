# 현재 저장소 검토와 reboot 변경 이유

기준 checkout은 깨끗한 `b2afb6e2e60695f75ed0dbae21e9fde691bf926c`였다. 이전 전달 `61448b7e` 뒤에 OA05–11 조건부 continuation이 추가되어 있었다. #530은 미추적 local remainder snapshot이고 다른99PR의 통합본이 아니다. #531에는 두 continuation commit이 있지만 README/PR 본문/NEXT_TASK의 초기 요약만 읽으면 최신 구현을 놓칠 수 있다.

| 영역 | 기준 HEAD에서 실제 확인한 상태 | 이번 사용/다음 변화 |
|---|---|---|
| DESI | `fit_desi_qiso_flatlcdm.py`, physical response, fixed released scalar law | 현재 조건부 H0*r_d profile 재사용; 새 angular Bianchi 정보로 취급하지 않음 |
| SMICA | `fit_cmb_smica_noise_modes.py`,32mode noise-scatter,300maps | 원자료 release 의미를 다시 조사하고 signal+noise를 결합한 disjoint pilot 추가 |
| 공동 법칙 | `PublishedGaussianSummaryBlock` 구현과 tests | 구현 재사용; 실제 CF4/CMB law/의존 구조가 채워질 때 물리 joint fit |
| legacy pushforward | `PosteriorDrawSource` 별도 typed path | 이미 구현된 posterior adapter를 다시 만들지 않고 실제 물리 draws를 연결 |
| rank | `common.finite_null_ranking.pooled_rank_p`/maxscan 존재 | core 재사용; 입력 선언·학습 분리·q CP interval·CLI/plot과 실제 pilot을 추가 |
| local/global | `nuisance_rank.py`와 discrimination library 존재 | 알려진 matrix rank는 재사용; 일부 library는 skeleton/heuristic이므로 physical response provider가 필요 |
| legacy 보고서 | Sept13 첨부 compendium과 더 오래된 PPC/K1/lnB 결과가 공존 | 서로 다른 관측·통계·정규화의 대응표를 만들고 source별 보존 |
| 상태 인계 | 초기 `NEXT_TASK`는 OA05시작/adapter미구현을 가리킴 | 새 CURRENT reboot entrypoint가 b2af continuation을 읽고 다음 작업을 지시 |

실제 runtime probe: `/home/cosmosapjw/venv/bin/python`에서 numpy2.2.6/scipy1.15.3/matplotlib3.10.3; `/usr/bin/python`에서 healpy1.19.0/astropy7.2.0를 import했다. 뒤 환경에는 사용하지 않는 Axes3D 경고가 있었다. 새 branch switch 시 기존 shared-Lean post-checkout helper 경로가 없다는 메시지가 있었지만 checkout/분석을 막지 않았고 hook이나 Lean 환경을 바꾸지 않았다.

이번 repair: pilot의 처음 실행은 cache digest를 gate 문서 digest와 비교한 identity-kind 오류로 데이터 계산 전에 실패했다. gate의 `cache_hash` 필드와 pinned cache digest를 비교하고 기존 provider로 실제 cache를 검증하도록 고쳤다. 원 실패와 수정 후 regression/실행은 evidence에 보존했다. 이 환경 오류를 science HOLD로 분류하지 않았다.

원래 OA 결과·과거 review·proof HOLD/UNKNOWN은 덮어쓰지 않았다. 현재 follow-up 상태는 새 DELIVERY, GOALS 및 canonical 추가 카드로 표현한다. standalone 코드와 문서가 실제 어느 repo owner의 결과인지 명시하며, MIO 진단을 HTT evidence에 중복 더하지 않는다.
