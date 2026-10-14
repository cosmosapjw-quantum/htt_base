# HTT 관측 분석 RETURN

## 게시 상태

- 기존 checkout: `/home/cosmosapjw/Dropbox/bianchi/htt_base`
- branch: `obs/legacy-reboot-20261014`, [PR #532](https://github.com/cosmosapjw-quantum/htt_base/pull/532)
- 검토 시작 HEAD: `7e94477124b60a6c755017acd6b8eb3f7b67dc54`
- 이 closeout 직전 게시 checkpoint: `a6a59d7ce25c1b55e3d5d84d6e4f919ce0a7d2ce` / tree `cb66f27d4f1c3bf084e244f3e33764a61dfc84f2`

최종 인계 commit은 live branch head다. 문서 자체의 commit hash를 자기 안에 넣지는 않는다.

## 실제 과학 결과

| 분석 | 결과 | 해석 범위 |
|---|---|---|
| Union3 22개 압축 node + DESI BGS | rho=0: Ωm=.357456±.027084, H0rd=9974.625±204.181 km/s; PPC=.285645 | 다섯 cross-covariance 가정, proper 공통 offset, 동일 262144 node ID/weight. H0와 rd는 따로 측정하지 않음 |
| CF4 실제 24개 SNIa-only 그룹 | MLE endpoint H=73.012199; 2048 posterior draw ESS=1120.827; 반복측정 PPC=.678020; 32개 조건부 주입 모두 해결 | 공유 preselection law. 실제 CF4 완전성·coverage나 cosmological H0 아님 |
| SMICA STF/processing | tensor family 17/241, 48개 선택 공동 scan 63/241 | 같은 하늘·300개 paired simulation 재사용. 절차 내부 60/240 split만 분리; 두 결과는 독립 증거가 아님 |
| 물리 dipole/boost | kinematic Gaussian proxy 369.816042±.108896 km/s, endpoint 식별성 계산 | intrinsic dipole/global history/source motion 가정 미완료 |
| ACT+Planck/Planck PR3 | joint A=.977071±.019956; 해당 Planck marginal .971649±.024399; PR3 reference 1.009562±.026253 | 공유 정보 유지. PR3 fixed-CMB .995252±.024119는 같은 자료 민감도이며 독립 곱셈 금지 |
| BK18/CLASS/FFP | BK18 고정 fiducial QHL=545.104273; CLASS joint rank 1/161; FFP 첫 쌍 6개 full-resolution spin-2 변환 | BK18 PTE/r/evidence 아님. CLASS 독립 split-noise 근사, FFP source bridge HOLD |
| Gaia/COSMOS/기타 | Gaia 4756개 source와 rho/raw-box operator, COSMOS 784016행/79 batch, CCHP 183543 photometry행, KiDS 5N(z), Union3/SDSS/JWST controls | 표본 선택·상관·측정법 조건 유지. empirical completeness나 순간 physical shear 아님 |

## 그림·보고서·검증

[한국어 과학 보고서](results/scientific_report/SCIENTIFIC_REPORT_KO.md), [13쪽 PDF](results/scientific_report/scientific_report.pdf), [34개 source identity](results/scientific_report/report.json), [11개 그림 identity](results/scientific_report/figure_inventory.json). 각 lane의 report/result/receipt에 source, 고정 가정, 단위, statistic-vs-bias, coverage scope가 있다.

별도 독립 read-only reviewer를 requested Astra/xhigh로 실행했고 observed runtime은 UNKNOWN으로 기록했다. 최근 joint/CMB 묶음은 43개 대상 테스트, RB26은 9개 대상 테스트를 통과했다. DAG/mirror/PDF build도 검증했다. 원본 실패와 결과를 보존하고, 변경하지 않은 큰 계산은 재실행하지 않았다. 요청 설정·transport capacity 실패·관찰값은 DELIVERY에서 분리한다.

## 종료 범위와 재개

27개 이름 붙인 task 중 18개가 scoped 완료, 9개 full physical/native task는 입력 차단이다. 현재 finite available queue에 pending/in-progress 작업이 없다. 전체 physical science가 완료됐다는 뜻은 아니다. 원래 RB10/11/12/15 dependency gate는 보존했고, 조건부 RB23/24/25를 별도 target으로 수행했다.

[BLOCKERS.json](BLOCKERS.json)에 goal/task별 정확한 부족 입력, 시도, 가능한 조건부 결과와 재개 명령을 기록했다. 남은 global-history/congruence response, empirical selection/shared calibration/object overlap, physical MES ceiling/remainder, raw QE filter/mean-field/bias, external native atlas가 필요하다. FFP source variant/convention과 CLASS physical split law도 남는다. Physical MES unknown mass는 1, 새 Lean coverage wrapper는 UNVERIFIED다. CAS07 upper bound나 native Bianchi family를 인증하지 않았다. 과거 HOLD/UNKNOWN은 승격하지 않았다.

외부 연구자에게는 [blocker별 입력·산출물 인계](EXTERNAL_RESEARCH_HANDOFF_KO.md)를 전달한다. 이 문서는 연구 의뢰이며 기존 task의 과학 판정을 변경하지 않는다.

관측 계산 process/batch는 모두 종료됐다. seed·batch·실행 시간과 source는 각 receipt에 보존했고 자동 재개 기능을 주장하지 않는다.

다음 한 명령: `python scripts/reboot_task_packet.py --task RB09`.
해당 packet의 부족한 global response를 공급한 뒤 작업을 연다. 다른 차단 goal의 별도 재개 행동은 BLOCKERS.json을 따른다.
