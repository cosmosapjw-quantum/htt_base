# Prior-art 및 legacy/PR crosswalk

**기준선:** htt_base@d7d5ce2a107b25479b8276f9fd4b5d69dbf53ad9. GitHub PR listing 561건(6 pages)과 canonical backlog 273 cards를 inventory하고, 과학 관련 PR/산출물과 사용자 제공 세 PDF를 우선 조사했다. 561개 모든 PR diff를 전부 정독했다는 의미는 아니며, 관련 PR의 diff/artifact와 legacy dossiers, 대표 코드·테스트를 직접 교차 검토했다.

## 최신 R37/R36 lineage

- cab89d25: PR-R37 convergence
- 5029f20a: R37-00 baseline
- a08e630e: R37-01 radiation
- d9bd6c48: R37-02 kinematics
- 8ab3b72f: R37-03 Hubble
- 84867cd9: R37-04 classification
- a6961390: R36-06 PR4 Commander MC100
- a18c854c: R37-05 final report
- d7d5ce2a: final adversarial audit/evidence selector repair

## 기존 결과와 신규 연구의 경계

| PR / product | 이미 확보된 내용 | 반복·과장 금지 |
|---|---|---|
| #364 / #365 | local/global velocity response, matched low-\u2113 morphology benchmark | 새 dipole/morphology scalar 자체를 novelty로 선언 |
| #378, #175, #281 | orbit/type acceptance, Bianchi invariant and geometry image | local shear/Ricci만으로 real-sky Bianchi type 지정 |
| #419 및 PMG WU series | observable irrep state, low-\u2113 pole carrier, same-sky lineage | processing variants를 independent skies로 계산 |
| #180 / boost-BiPoSH | exact zero-parameter boost residual against boosted FFP10 null | residual을 geometry estimator/Bianchi evidence로 승격 |
| #179 / directional_cosmography.py | raw CF4 directional catalogue coefficient와 position-preserving null | H_cat/q_cat를 곧바로 physical H(z,n)으로 호칭 |
| #151/#178/#203 | DESI exact-selection mocks, dipole tomography, causal decomposition tasks | historical invalidated mock covariance 재사용 |
| #155/#156/#206 | cross-survey negative controls, multi-probe rank, systematics-as-hypotheses | PR task 존재를 실행/완료 증거로 취급 |
| #193/#194/#195 | covariant hierarchy, observer-boost/matter-tilt bridge, finite-volume bridge theorem | conditional derivation을 새 empirical discovery로 재명명 |
| R36-01/02 | CF4 source-window operator and correlated covariance transport | 동일 catalogue release/method를 독립 confirmation으로 중복 |
| R36-03/04 | Gaia E2/STF5 PM history; optical joint response/error budget | Gaia E1/B1 24D와 E2/STF5 혼합, apparent CF4 proxy를 matter shear로 해석 |
| R36-05 / four-goal | exact positive radiation/shear response, 23/20 carrier, polarization omission | Thomson gain과 full shear operator를 동일 estimand 취급 |
| R36-09/10/11 | family intake, finite geometry image, science synthesis | geometry witness를 sky Bianchi identification으로 취급 |
| R37-00..05 | baseline, four-goal results, final convergence report | report release를 scientific discovery/priority로 혼동 |

## Legacy TILT_BOOST_20260930

기존 독립검토는 10개 conditional theory claim을 승인하고 actual cosmic-tilt/Bianchi classification은 HOLD했다.

- Observer O/material U와 material U/homogeneous normal N은 별개의 상대운동 쌍이다. 네 조합이 모두 가능하다.
- Ideal full-angular zero-distance intercept는 smooth common source congruence와 common spectral standard 아래 endpoint observer/source velocity를 정할 수 있지만, 유한거리 catalogue가 그 intercept를 자동 구현하지 않는다.
- Geodesic source의 방향별 Hubble slope를 symmetric 4-tensor로 lift하면 조건부 timelike eigenline 복원이 가능하다. Source geodesicity, spatial eigenvalue nonzero, eigengap, finite-distance error가 필요하다. 이 slope만으로 vorticity를 복원하지 못한다.
- Homogeneous normal은 curvature clock 또는 Codazzi momentum constraint 같은 별도 geometry input이 필요하다. CMB dipole나 finite-volume bulk flow가 normal을 대신하지 않는다.
- Congruence velocity의 한 사건 값은 \(\Theta,\sigma_{ab},\omega_{ab},a_a\)를 정하지 않는다.
- Intrinsic field family가 Lorentz inverse-boost에 닫혀 있으면 endpoint-only boost와 intrinsic anisotropy는 퇴화할 수 있다.
- T6 processed boost quotient의 matched-control cut-sky numerical rank는 unresolved였다. Full-sky boost identity만으로 cut-sky identification 불가.

실제 catalogue fit, coverage, finite-distance remainder certification, local xAct/Lean/Sage replay, native Boltzmann evolution은 legacy loop에서 실행되지 않았다.

## 현재 핵심 코드와 테스트

- htt/src/common/revival_dipole_discrimination.py: toy 24-feature synthetic kinematic/global/systematics benchmark.
- htt/obsstat/number_count_dipole.py: DESI BGS clustering cosmic-variance + shot-noise mocks; low-z mixture 때문에 diagnostic-only.
- htt/obsstat/directional_cosmography.py: PR179 CF4 catalogue feature pipeline; not a physical geometry measurement by itself.
- htt/htt/htt/infer/endpoint_cosmography.py: 13-coordinate conditional endpoint estimator with strict source/frame/distance/selection/covariance/remainder tags.
- htt/obsstat/boost_biposh_residual.py: PR180 zero-parameter boost-BiPoSH consistency diagnostic.
- tests/htt/test_local_boost_nulls.py: local-boost null and response-overlap gates.
- tests/obsstat/test_spectroscopic_dipole.py: DESI feature-only contract; blocks missing selection/null/covariance/rank/local-global interpretation.

## 문헌 경계

- Maartens et al. (2024), JCAP 09 070, DOI 10.1088/1475-7516/2024/09/070: observer-dependent Hubble multipoles.
- Ferreira & Quartin (2021), PRD 104 063503, DOI 10.1103/PhysRevD.104.063503: independent Doppler/aberration/dipole estimators under beam/noise/mask.
- von Hausegger & Dalang (2025), PRD 111 123547, DOI 10.1103/PhysRevD.111.123547: redshift-tomographic matter dipole and observed-redshift migration.
- Nadolny et al. (2021), arXiv:2106.05284: peculiar velocity/large-scale anisotropy separation using redshift and angular size plus flux/position.
- Wagenveld et al. (2025), A&A 697 A112, DOI 10.1051/0004-6361/202450291: joint radio/AGN count-dipole analysis.
- Herold et al. (2025), arXiv:2509.03720; Nofi et al. (2025), arXiv:2509.03718/2509.03719: low-\u2113 mask/foreground sensitivity and near-full-sky temperature analysis.

이 목록은 집중 prior-art screen이며, 전 세계 문헌의 exhaustive novelty proof는 아니다.
