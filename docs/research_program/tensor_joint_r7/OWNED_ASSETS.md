# 보유 관측자료·외부 코드의 실행 연결

이 표는 사용자가 제공한 2026-09-07 자산 목록과 선택한 첨부 소스의 정적 검토를 연결한다. 관측자료의 현장 존재·헤더·우도 적합성은 아직 검증하지 않았다. `W=/home/cosmosapjw/Dropbox/bianchi/htt_base/workdir`, `E=/mnt/sn850x2t/htt_base_e2e`; 기존 `W/asset_inventory_20260907` 및 `E/inventories/EXTERNAL_ASSETS_20260907T071735Z`를 먼저 소비한다. 전체 저장장치를 다시 스캔하거나 모든 데이터를 다시 해시하지 않는다.

## 관측자료별 역할

26개 DAG 노드는 제품별 하위 작업을 가진다. 예를 들어 `R7-06.wmap`은 새 DAG 노드가 아니라 R7-06의 독립 제품 결과다. 주제품의 부재가 다른 제품의 처리를 막지 않는다. 모든 아래 행은 R7-00에서 자산 상태를 정하고 R7-21/25에서 실제 사용·비사용 이유를 결산한다.

| 보유 자산 / 목록의 위치 | 실제 소비할 관측량·역할 | 필요한 연결과 결측 시 대안 | DAG |
|---|---|---|---|
| PR3 SMICA, `W/raw/planck_data` | 주 온도 Q/O, 상위 관측모드, 공분산을 포함한 형태·조건부 MES | 단위·frame·beam/pixel·mask·dipole/KQ 처리 확인. 실제 uncertainty law가 없으면 기술적 tensor 결과와 합성 응답 검증까지 수행 | 04/06→10→11/12/13→18/19 |
| PR3 component controls, `W/raw/planck_pr3_component_controls` | 같은 처리 기준의 tensor 차이, foreground 및 component 의존성 | 동일 sky와 원관측을 공유. 차이 공분산이 있으면 검정; 없으면 기술적 차이·감도. 독립 지도 우도로 곱하지 않음 | 06→21; qualified law→10 |
| FFP10, `W/raw/planck_ffp10` | 제품 대응 null·noise·processing bank | signal/noise ID와 보정·제품 일치, calibration/evaluation membership 구분. `.fits.partial`·전송 sidecar 제외. 파일 수를 독립 N으로 사용하지 않음 | 06→18/19 |
| PR4/NPIPE 관련 모든 위치 | 사용자 제외 범위의 비수치 상태 기록 | 획득·intake·분석·비교를 실행하지 않음. 이전 문서의 upgrade-candidate 문구보다 이 제외가 우선 | 00만 |
| WMAP9 지도 / WMAP7 simulation | 다른 기기의 commonized Q/O·polarization controls | 7년 simulation은 9년 제품의 end-to-end null이 아님. 기존 release-matched law가 없으면 9년 지도는 descriptive common-sky control | 06.wmap→21; qualified law→10/18 |
| BeyondPlanck v2 | 지도·foreground 모형 민감도, 제공된 조건부 posterior uncertainty | posterior draw는 독립 null sky가 아님. 관측·prior 중복을 유지한 tensor 이동/불확실성 비교 | 06.beyondplanck→21 |
| Cosmoglobe DR1 | 추가 map-making/foreground 비교 | WMAP/Planck 원자료 중복을 기록. posterior draw를 FFP10 null과 한 ensemble로 합치지 않음 | 06.cosmoglobe→21 |
| ACT DR6 lensing / simulations | 배포된 kappa-space 통계, 모델이 정해진 projected-matter 보조량 | kappa는 온도·속도가 아님. mask·reconstruction response·noise/bias와 simulation law 적용. 기존 PR177을 쓸 경우 그 support/statistic 유지; raw QE 자료 없이는 raw-QE 재분석을 주장하지 않음 | 06.act_kappa→21; qualified kernel→10 |
| CF4 full 원객체·그룹, `W/raw/cf4_full` | 원 distance/redshift 및 group/calibration 우도; bulk·symmetric affine·depth | 기존 catalogue adapter와 P의 full-covariance design 재사용. raw selection 부재 시 명시된 conditional velocity-space law 또는 scenario | 07→10→14→18/19 |
| CF4 compact grid / WF / CR | 재구성 조건부 비교, 원관측 예측의 민감도 | 원 catalogue·prior 공유. 독립 grid-cell 우도 추가 금지. potential-flow prior의 CR은 curl 관측을 만들어내지 않음 | 07.recon→21 |
| CF4++, 2M++/Carrick, CORAS, Lilow/2MRS flow | 동일 객체 위치에서 competitor velocity·거리 예측 및 residual | 단위·frame·grid·보간 정의역·원자료 중복 확인. 지원 밖은 missing prediction; 영속도로 대체하지 않음 | 07/09.field_controls→21; qualified law→10/17 |
| DESI raw catalogue / random / mock | cap·깊이별 count vector, selection response, nuisance refit | P의 BGS BRIGHT sample을 정확히 적용. 좌표·weight·completeness·mock law 고정. PR151 무효 수치는 재사용 불가 | 08→10→14→18/19 |
| DESI compressed full-shape/BAO BGS-bright v1.2 | 배경 우주론·공유 nuisance의 공개 compressed-likelihood 비교 | 위치가 없으면 각도 dipole을 복원하지 않음. raw DESI와는 대체 실행 또는 올바른 공유 법칙으로 사용 | 08.compressed→21; qualified law→10/17 |
| Union3 | distance-redshift·배경·보정 비교 | binned product는 해당 compression만 지원. 개별 방향 분석은 좌표·redshift·원오차·보정/중복 정보가 있는 경우만 | 09.union3→21; qualified rows→10/14 |
| JWST CCHP/SH0ES host 자료 | host-method contrast로 보정 제약; absolute row는 거리/깊이 | 같은 host의 geometry 평균은 contrast에서 소거. 표본 단위·공유 calibration·CF4 중복을 인증. 위치만으로 같은 측정이라 판정하지 않음 | 09.jwst→10→13/14/17 |
| HSC / KiDS / COSMOS/Web | footprint 내 lensing·selection·systematics 비교; matched kernel 아래 projected matter | lensing shear와 MES congruence shear는 별개. 작은 footprint를 all-sky dipole 자료로 만들지 않음. kernel/photo-z/shape law가 없으면 control/scenario | 09.small_area/10.projected_controls→21 |
| QUIJOTE MFI | 주파수별 foreground·온도/polarization systematics | 실제 band/bandpass·단위·calibration·mask 적용. 공유 sky-derived template의 uncertainty를 유지 | 06.quijote→21; qualified foreground law→04/10 |
| CLASS **관측소** 제품 | polarization·주파수 systematics control | 실제 기기 map/transfer/noise를 확인. CLASS Boltzmann 코드와 구분 | 06.class_observatory→21 |
| 기존 obs_bundle·compact carrier·derived cards | 빠른 locator, 안전한 I/O, 원열·tensor의 재사용 | 원자료 변환이 확인된 carrier만 소비. 과거 scalar-MES rank·무효화된 amplitude/significance는 새 데이터가 아님 | 00/02→06–09; 역사 비교→21 |

WMAP·foreground·lensing control은 그 제품 타입을 유지한다. 예를 들어 kappa를 `TensorRecord`의 온도 Q/O 필드에 넣지 않는다. 제공되지 않은 sky/noise/selection law를 Local Codex가 추정 선택하도록 요구하지 않는다.

## 제품 하위 작업과 중복 처리

`AssetUseRecord`는 `product_key`, 기존 inventory locator, release/component, observable type, frame/units, processing/window, row/realization ID, raw-data ancestry, response/control role, uncertainty law, law scope, disposition, fallback, DAG consumers를 가진다. 관측값을 보고 사용 여부를 고르는 용도가 아니다.

사용 상태는 `QUALIFIED_LIKELIHOOD`, `QUALIFIED_CONDITIONAL_LAW`, `LAW_FACTORY`, `CONTROL_ONLY`, `SCENARIO_ONLY`, `UNAVAILABLE_PRODUCT_OR_LAW`, `SKIPPED_BY_USER_SCOPE`로 구분한다. 실제 normalized law만 R7-10의 admitted experiment가 된다. `LAW_FACTORY`는 물리 예측 결합 뒤 검증해야 한다. control/scenario는 R7-21에서 해석하며, 유효한 다른 제품의 추론을 지연시키지 않는다. 제외·결측 상태는 결과의 생략과 다르다.

서로 다른 자료에 대해 공통 모수 theta의 유효한 marginal confidence region `C_j`가 이미 있고 교차 의존성만 모르면, 고정한 오류 예산 `sum(alpha_j)<=alpha`로 `intersection_j C_j`를 사용할 수 있다. 실패 사건의 합집합 확률이 각 marginal 실패 확률의 합 이하이기 때문이다. 이것은 **의존성에 강건한 공동 confidence set**이며 product likelihood나 posterior가 아니다. 공통 estimand·물리 모형·각 marginal coverage를 먼저 확인한다. 서로 대안인 nuisance/물리 모형의 region에는 T7/T8의 **union** 규칙을 사용한다.

기본은 분석 전 고정한 J개 자료 scope에 `alpha_j=.05/J`; 모든 marginal을 동시에 덮는 하나의 공유 nuisance coverage event에 gamma=.01을 별도로 쓸 때 관측 몫은 `.04/J`다. 서로 다른 nuisance confidence event를 쓰면 그 실패 예산의 합이 .01 이하가 되도록 별도로 나눈다. 결측 또는 coverage 미검증 제품의 region은 공통 전체 parameter domain으로 놓아 정보 기여를 0으로 기록하고 사후 재배분하지 않는다. 영역의 수치 근사는 certified outer approximation이어야 한다. 공통 대상의 정식화도 없으면 단순한 자료별 비교만 수행한다.

## 첨부 코드: 새로 작성하지 말고 연결할 부분

아래는 선택한 실제 archive member의 텍스트를 읽은 결과다. 소스 존재를 확인했으며 import·build·수치 검증은 하지 않았다. 파일을 이식할 때 원 archive/member와 license를 기록하고 기존 tests를 해당 consumer에 붙인다.

| 원 첨부 / 정확한 member | 재사용 내용 | 연결·수정 조건 |
|---|---|---|
| `bianchireview87.tar(1).gz`: `./bianchi/matter/freestream.py` | `f_bose_einstein`, `moments`, `emt_conservation_residual`: collisionless photon quadrature | 기본 Fermi–Dirac 대신 이미 있는 Bose–Einstein 입력을 선택; R3 photon 온도·정규화·단위와 연결. R7-02/15 |
| 같은 archive: `./bianchi/matter/kinetic_einstein.py` | `matter_from_quadrature`, `matter_from_hierarchy`, `geometry_rhs`, `integrate_reference`, `integrate_coupled`, `K3_residual`, `einstein_residual` | quadrature/hierarchy 및 stress-source 비교를 재사용. 실제 dust+photon+Lambda 합성은 별도 provider에서 수행 |
| 같은 archive: `./bianchi/matter/hierarchy.py` | `J_moment`, `J_grid`, `emt_from_J`, `hierarchy_rhs`, `integrate_hierarchy` | angular/radial truncation과 PSTF normalization 범위를 유지 |
| 같은 archive: `./bianchi/matter/grid_boltzmann.py` | `initial_grid`, `moments_from_grid`, `thomson_step`, `multipole_amplitudes` | isotropic collision gate의 oracle. 동일 quadrature와의 비교만으로 quadrature 자체가 독립 검증된 것은 아님 |
| 같은 archive: `./bianchi/rays/optical.py` | `screen_basis`, full-four-vector screen/Jacobi mechanics, `trace_optical_diag_bianchi` | wrapper의 `sigma_dot=-3H sigma` 및 perfect-fluid density 진화를 R3 실제 background/history derivatives로 교체. endpoint helper만으로 reverse-ray reciprocity 검증을 주장하지 않음 |
| 같은 archive: `./bianchi/rays/weyl.py`, `./bianchi/rays/frame.py` | `riemann_up/low`, `tidal_matrix`, `tidal_batch`, `frame_connection` | symbolic cache의 생성 소스·단위 확인. 알려진 curvature fixture로 검증한 기하 contraction을 사용 |
| `bianchirustcoreRDAGcomplete.tar.gz`: `_rustcore/src/rays/geodesic.rs` | `photon_rhs`, `trace_ray_diag`, `trace_rays_batch_final_z` | optional acceleration. 기존 tracer는 parity를 위해 forward Euler를 유지하므로 일치 자체는 고차 정확도의 증거가 아님 |
| 같은 archive: `_rustcore/src/rays/optical.rs` | `screen_basis`, `trace_optical_diag`, `trace_optical_batch` | Python과 같은 background/derivative adapter를 적용한 뒤 독립 수렴 검증 |
| review87: `./_rustcore/src/kinetic/collide_exact.rs`, `pol_collide.rs` | exact collision exponential, angular projector/eigenvalue·polarization oracle | stationary-electron collision scope와 screen/Stokes 규약을 유지. 완전한 Bianchi transfer로 승격하지 않음 |
| `BASS_v1_BACKGROUND_HIGHL_HARNESS_PROJECT_SOURCE_BUNDLE_20260803(1).zip` | background/high-l `contracts`의 conventions·scope·acceptance·external-oracle 요구 | 이 bundle은 **solver code를 포함하지 않는 pre-code harness**다. 이미 구현된 physical provider로 계산하지 않음 |
| `lowell_bianchi_codex_automation_kit.zip`: `README.md`, `KIT_MANIFEST.md`, `scripts/codex_patch_loop.py` | 실제 solver patch source가 있을 때 packaging/build automation | kit 자체는 solver가 아님. 해당 Local 작업이 생길 때만 재사용 |
| `xAct_1.3.0.tgz`: `xAct/xTensor/xTensor.m`, `xAct/xCoba/xCoba.m`, `xAct/xPert/xPert.m` | abstract tensor·component·perturbation 검증 | headers: xTensor1.3.0, xCoba0.8.6, xPert1.0.6; GPL notices 유지. 실제 Wolfram 환경에서만 R7-01 CAS 수행 |

선택한 review87 test donor는 `./tests/test_k1_kinetic_einstein.py`, `./tests/test_g1_grid_boltzmann.py`, `./tests/test_rustcore_differential.py`다. R3에서는 kinetic conservation·source normalization과 screen/Jacobi를 먼저 연결하고, optional Rust acceleration은 CPU reference의 결과가 정해진 뒤 수행한다. 기존 repo의 올바른 dust `bi_continuation`은 이 archive의 제한된 background wrapper보다 우선한다.

중요 member SHA-256: review87 `freestream.py` = `b03aeed2cfcdaa5baf45fdab626941905674e2385bc06d1173a4b8c39ebf8bb4`; `kinetic_einstein.py` = `59f1c49539d35061d17490944ace63c48addce0e44e3d1a0f39f8f40b363d93b`; `optical.py` = `c6b83f73e0c65fe21c31291bdefdcc25c4c1ed6e497be85785075b5e137a1026`. 이 값들은 선택 소스의 식별자이며 실행 인증이 아니다.

## 기존 라이브러리의 작업 분담

| 기존 환경·라이브러리 | 이번에 소비할 기능 / 절약할 작업 |
|---|---|
| NumPy/SciPy | CPU tensor·GLS·최적화·quadrature reference; 자체 선형대수 재작성 방지 |
| Astropy/FITS | 실제 헤더/column admission과 ICRS/Galactic 변환; 수작업 방향 변환 방지 |
| healpy / ducc0 | 기존 구면변환·pixel 중심·beam/pixel 처리; 규약을 맞춘 독립 구현 비교. `map2alm`을 masked simultaneous fit의 자동 대체물로 삼지 않음 |
| CAMB / CLASS Boltzmann | 지원되는 등방 배경, CMB/matter spectra, transfer·거리의 기준 모델. Bianchi나 CLASS 관측소 데이터와 구분 |
| SymPy / xAct 및 사용 가능한 독립 CAS | T1/T3/T5와 기존 rational certificate의 명명된 검증. 설치만으로 CAS pass를 만들지 않음 |
| 기존 sampling/optimization 도구 | 고정된 law와 domain의 계산; likelihood를 새로 정의하는 역할은 없음 |
| JAX/diffrax/equinox | 선택된 review87 donor가 실제로 요구할 때만 기존 backend 사용; 모든 stack의 재설치 불필요 |
| Rust/PyO3/nalgebra/Rayon/diffsol | 검증된 donor의 선택적 가속. Rust installer/env/bootstrap은 환경 자산으로 유지 |

공식 기능 범위는 [CAMB 문서](https://camb.readthedocs.io/en/latest/), [healpy 문서](https://healpy.readthedocs.io/en/latest/), [xTensor 문서](https://www.xact.es/xTensor/)와 대조했다. 웹의 latest 버전이 현재 워크스테이션의 버전이라는 뜻은 아니다. Local Codex는 이미 작동하는 호환 환경 하나를 먼저 사용하고, 실제 소비한 모듈만 버전·smoke check를 기록한다.

새 구현의 최소 범위는 기존 source를 잇는 typed adapter, 필요한 좁은 결함 수정, 아직 없는 normalized joint-law/outer-confidence consumer다. 자료를 다시 내려받거나 올바른 quadrature·optics·통계 kernel을 처음부터 작성하는 것은 기본 경로가 아니다.
