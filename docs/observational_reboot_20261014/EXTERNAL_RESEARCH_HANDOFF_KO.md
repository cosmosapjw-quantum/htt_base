# 관측 분석 blocker 해소를 위한 외부 연구 인계

기준: `obs/legacy-reboot-20261014`의 `e9728c88b2ccf0192e0594d0045128e67ed52aaf` (tree `19a755879ae93607f8ef105d9a65e85909ca3cf3`), [PR #532](https://github.com/cosmosapjw-quantum/htt_base/pull/532). 이 문서는 **연구 의뢰**다. 아래 입력은 아직 수용되지 않았으며 기존 과학 판정은 `HOLD`다. 최신 상태는 [RETURN](RETURN.md), [BLOCKERS](BLOCKERS.json), [REBOOT_PLAN](REBOOT_PLAN.json)을 따른다. 저장소의 기존 계산은 [13쪽 과학 보고서](results/scientific_report/scientific_report.pdf)와 [source inventory](results/scientific_report/report.json)에 있다. `report(1).pdf` 같은 별도 첨부와 로컬 원자료는 Git에 없을 수 있다. 외부 연구자는 Git 파일만으로 접근 가능하다고 가정하지 말고 필요한 원제품의 공개 release/DOI·버전·접근 경로를 명시해야 한다.

## 우선 위임 과제

| 과제 | 해소할 질문과 필요한 산출물 | 재사용할 계산 / 완료 판정 |
|---|---|---|
| **E1 — 물리 response, RB08→RB09** | 한 congruence와 frame에서 local boost, global tilt/shear history, source motion, intrinsic CMB dipole의 *서로 다른* 관측 미분을 제시한다. CF4 거리·적색편이와 CMB 처리 연산자를 거친 계수, 단위, 적분 구간, boundary convention, covariance 및 공통 nuisance를 제공한다. 수치 response에는 오차 진단과 대체 모델 범위를 붙인다. | [endpoint dipole](results/physical_dipole_v2/report.md), [CF4 selected law](results/cf4/selected_v2/report.md), [response laboratory](results/response_laboratory/report.md), `python scripts/reboot_task_packet.py --task RB09`. 동일 endpoint 열만 다시 제출하면 실제 global 식별성은 열린다. |
| **E2 — 공동 관측법칙, RB10→RB12** | CF4/SDSS의 표본선택 함수와 정규화, method/group별 거리·속도 오차, 공유 zero point·절대척도 공분산, 관측 객체 overlap을 제품 근거와 함께 제공한다. Union3·DESI·CMB와의 공유 latent/중복 여부를 명시하고, 같은 draw에서 shear/vorticity/tilt/curvature와 양의 MES 분모·ceiling·remainder를 계산할 수 있는 물리 입력 계약을 제시한다. | [CF4 latent/posterior](results/cf4/latent_v1/report.md), [조건부 Union3–DESI posterior](results/posterior/report.md), [SDSS box control](results/cache_sdss_v1/report.md). 조건부 posterior는 완전한 물리 likelihood나 H0–rd 분해가 아니다. `python scripts/reboot_task_packet.py --task RB10`. |
| **E3 — Planck/CLASS/FFP source bridge, RB04/RB19** | 실제 사용한 Planck SMICA 및 FFP10 원제품의 frame, `POLCCONV`, beam/pixel window, mask, downgrade, component separation, dipole 및 quadrupole 처리 순서를 파일명·release·header/문서 위치로 연결한다. 실제 sky의 공동 split/null law와 CLASS map/noise pairing 및 transfer 적용 범위를 검증한다. | [SMICA response](results/smica_response_scan_v2/report.md), [CLASS noise](results/class_noise_v1/report.md), [FFP formal operator](results/spectra_ffp10_first_pair_v1/report.md), [기존 primary-source 조사](research/PRIMARY_SOURCES.json). 기존 rank나 `p=.039`를 새 증거로 합산하지 않는다. `python scripts/reboot_task_packet.py --task RB19`. |
| **E4 — ACT raw QE, AO19** | 실제 raw map splits, beam/mask/filter/noise covariance, normalization response, mean field, disconnected bias와 재사용 시뮬레이션 ID를 동정한다. 원자료가 없는 경우 제품 접근 제한과 필요한 최소 필드를 정확히 적는다. | [파생 lensing summary](results/cache_lensing_v1/report.md)와 [feature rank](results/cache_feature_ranks_v1/report.md)는 raw QE가 아니다. `python scripts/reboot_task_packet.py --task RB22`는 기존 scoped task 설명용이며 AO19 자체는 `BLOCKERS.json`을 따른다. |
| **E5 — CAS07 물리 remainder** | 실제 ray/source 정규화, curvature·도함수 envelope, 거리 interval/domain, 단위와 표본선택 조건을 제공해 finite-distance Jacobi remainder를 묶는 전제를 만든다. 수치 envelope에는 어느 데이터·기하에서 유효한지와 검산 벡터를 포함한다. | [Gaia bias sensitivity](results/gaia_bias_sensitivity_v1/report.md)는 별도 선형 추정량의 가정된 `rho`/좌표 box 진단이다. CAS07 upper bound가 아니다. 새 coverage wrapper는 Lean `UNVERIFIED`. `python scripts/reboot_task_packet.py --task RB26`. |
| **E6 — 외부 native atlas, RB13→RB16** | 외부 low-ell Bianchi solver/atlas가 생긴 경우에만 all-`m` T/E/B morphology, transfer source·convention, sky mask, covariance/null, family equivalence, 버전·검증 기록을 제공한다. 이 저장소 안에서 solver를 새로 구현하지 않는다. | [native task packet](../../scripts/reboot_task_packet.py)에서 `--task RB13` 조회. 외부 atlas와 E1 물리 response가 없으면 family 경쟁·식별은 보류한다. |

E2의 JWST/CF3 확장에는 개별 SN/host의 방법·선택·공유 보정과 FP/source-motion 법칙이 별도로 필요하다. [JWST host control](results/cache_jwst_v1/report.md), [CF4 실제 24개 그룹](results/cf4/selected_v2/report.md), [SDSS join coverage](results/cache_join_coverage_v1/report.md)는 그 법칙을 추정한 결과가 아니다. 새 연구자는 원본 제품을 확보했는지, 공개 요약만 사용했는지 구별해 반환한다.

## 외부 연구자의 반환 형식

각 E 과제별로 아래를 한 파일 또는 PR에 묶어 반환한다.

1. **Source identity:** DOI/release/제품명·파일명·버전·접근 URL과 실제 읽은 범위. immutable 입력은 가능한 hash/size를 기록한다. 문헌의 가정을 실제 제품 설정에 대응시킨다.
2. **물리·통계 계약:** 좌표계/frame, 단위, population/selection, latent/nuisance, 공분산 블록과 동일 객체·하늘·noise의 중복, prior/likelihood, 유효 domain, 선택한 depth/axis의 동시추론 보정을 명시한다. 미관측 물리량은 0으로 채우지 않는다.
3. **재현 가능한 산출물:** 최소 계산 코드·명령·환경, raw log, 작은 독립 대조 또는 injected recovery, 결과와 수치 오차, 그림의 source/coverage. 대용량 원자료는 업로드 대신 공개 획득 절차와 checksum/manifest를 적을 수 있다.
4. **판정:** 제공한 입력이 어느 RB/AO 의무를 닫는지, 남은 `UNKNOWN`/`HOLD`, `statistic`과 물리적 bias/coverage를 분리해 기술한다. 합성·조건부 진단을 관측 검출, native solver 결과, 물리 MES bound로 승격하지 않는다.

수용 전 이 저장소의 production writer가 관련 task packet으로 연결·검산하고 별도 독립 reviewer가 최종 수식·코드·그림을 확인한다. 범위별 판정과 원본 실패는 보존한다. 위 여섯 과제의 자료 조달이나 공동 연구 자체는 이 commit의 완료 범위에 들어가지 않는다.
