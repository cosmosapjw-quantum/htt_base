# Legacy v2 통합 결정

23개 첨부의 5,038개 재귀 원본 위치를 4,073개 SHA-256 content object로 합쳤다. 정확히 같은 바이트의 중복 occurrence 965개를 제거했다. 원본 archive와 작업 중인 저장소는 변경하지 않았다. 모든 원본 위치는 FILE_OCCURRENCES.tsv / INSTANCES.json에서 단일 canonical object를 가리킨다.

## 합친 단위

| 단위 | 통합 결과 | 의미 보존 조건 |
|---|---|---|
| 동일 파일 바이트 | 한 canonical 파일 + 전체 aliases | 같은 hash만 하나로 저장 |
| 이전 source evidence | 992개 code body의 기존 정독 장부 재사용 | 동일 SHA, 기존 domain·failure 설명 보존 |
| 새 source evidence | 362개 code body의 전문 또는 전문기준본+완전 diff 검토 | 읽기 방식·파일 identity를 각각 기록 |
| Python AST 동일·바이트 다름 | 7개 그룹을 연결하고 모두 보존 | comments/import path/runtime authority를 자동동일시하지 않음 |
| 같은 basename의 다른 구현 | 179개 variant family | macro·units·STF packing·상태정의 차이를 보존 |
| 공통 수학 연산 | canonical/research_primitives.py와 response_primitives.py | 아래 typed component contracts로 통합 |
| exact duplicate helper | canonical/legacy_exact_helpers.py | 앞선4 helper의 추출 provenance 보존 |
| source generator와 실제 결과 | 별도 역할로 색인 | JSON/PDF/CAS transcript 생성기가 계산 producer를 대신하지 않음 |
| symbolic link | 5개 target 문자열, 110개 원위치 | 링크 대상을 읽거나 복구한 것으로 세지 않음 |

## 공통 수학 구성요소와 연결

| 통합 계층 | 재사용 source | canonical 입구 | 유지할 경계 |
|---|---|---|---|
| streaming/Schur | 기존 Legendre/Rust LU, 새 HyRec static block, Scholarly memory | partition_generator, memory_kernel, schur_resolvent, schur_memory_coefficients | HyRec의 static virtual-state matrix는 kinetic capacity 없이 time generator로 승격하지 않음 |
| cascade reward/delay | microphysics_check.py, microphysics.tex | phase_type_moments, phase_type_bin, moment_direction | fixed transient generator·line reward·initial layer·clock |
| normalized law/score | 기존 Fisher/entropy 코드, LOOP4→5 Bose correction | normalized_tilt, score_projection, stimulated_axis_law/response | rate와 conditional mark의 가중치, same-parent law를 일치 |
| positive moment/detector | hh_extension_checks.py, hh.tex, polarized transport | positive_matrix_moments, spectral_response | physical prepared coherence가 없으면 scalar rate로 임의 off-diagonal을 구성하지 않음 |
| passive Gram/screen | LOOP10 nonorthogonal algebra, FA02 Jet/detector | gram_connection | square full frame와 rectangular moving subspace leakage 분리 |
| geometry/PSTF | geometry_checks.py, full-m layout, current Bianchi constraint | stf_orthonormal_basis, lie_jacobi_vector | PSTF5는 연구5뷰와 다르며 Na는 벡터 |
| opacity/clock | native density driver, R100 opacity, visibility | opacity_per_clock, optical_depth_to_endpoint | chemical proper clock와 radiation drift를 다른 입력으로 전달 |
| finite-bin/event | synthesis/nonthermal, optical tangent | fold_bin_mass; 기존 joint_fractional_interval | turning point의 약한/bin response, moving endpoint, support를 명시 |
| VIII tail | SU(1,1) ladder kit | analysis/bass_viii_runs/verify_projected_casimir.py | projected operator defect와 actual state/observable tail convergence 구분 |
| statistical outputs | 기존 joint rank/covariance/bin information | exchangeable_global_rank, gaussian_covariance_score, conditional_bin_information | qualified law·exchangeability·selection을 실제 입력으로 유지 |

새 response_primitives.py는 원본 소스를 덮어쓴 파일이 아니라, 공통 정의와 보완된 계산을 한 인터페이스로 묶은 연구용 구현이다. 재현 가능한 검산은 research/response_discriminators.py에 있다. 원 source가 필요하면 catalogue의 SHA로 찾거나 tools/materialize_archive.py로 지정 archive/중첩 chain의 파일을 새 경로에 복구한다. 실제 source의 import layout를 단일 디렉터리에 평탄화하면 의미가 달라지므로 canonical 원본 파일을 무작위로 함께 import하는 사용법은 지원하지 않는다.

## 실제로 분리해야 하는 버전

- HYRec FULL/SWIFT compile macro와 runtime mode는 다른 선택축이다. 서로 다른 history.h/history.c를 동일 이름으로 덮어쓰지 않는다.
- LOOP4의 자극방출 조건부-law 오류는 LOOP5 이후 수정되어 있다. 수정 전 반례와 수정된 positive law를 한 쌍의 provenance로 보존한다.
- Lowell ell-only24와 full-m188 layout은 별도 schema다. mapping을 명시하기 전에는 함수명 유사성으로 통합하지 않는다.
- zero collision/identity mode fixture와 실제 physical kernel은 카탈로그에서 분리한다.
- numerical packet count, physical integer photon count, electron fraction x_e, signed scientific carrier x는 서로 다른 타입이다.
- 17-species 및 내부 atomic basis의 차원과 연구의5뷰(x,Q,Pi,F,G_F)는 동일 상태공간이 아니다.

이 통합은 불필요한 바이트와 공통 연산 중복을 줄이면서, 다르게 정의된 물리 모델은 이름·단위·provenance가 남도록 구성했다.
