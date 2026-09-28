# 이론–현재 코드 대응

2026-09-28 KST. 현재 main HEAD `549d8516df3ab41278bddbbba9d8c35d87dc96a6`, tree `05374ea3d40fee24b28e4b19da3297dc5e160169`. Owner: LOCAL_CODEX_THEORY_HANDOFF_INTEGRATOR; 문서용 C0, transfer none. 기존 dirty production 변경을 보존했다. 아래는 좁은 static source inspection이며 runtime verification이 아니다. 함수명 유사성 또는 과거 report commit을 현재 구현 증거로 쓰지 않는다.

## 실제 확인한 현재 동작과 범위

- `htt/src/common/mes_theorem_authority.py`: per-branch rational/source/norm/assumption authority와 receipt verifier 구조가 있다. 검증기 실행은 하지 않았다. 이 구조가 exact R1–R5 operator 구현이라는 근거는 없다.
- `htt/tsc/admissibility/three_bound_hierarchy.py:106`: COEFFS의 shear=(5/3,3,3/7), omega=(3/4,2,2/7), accel=(3/4,1,3/14)가 현재 존재한다. accessible primary geodesic omega=(10/3,2/15,0)와 다르며 source/nongeodesic 귀속을 미확보로 보존한다. legacy owner를 active science로 되살리지 않는다.
- `htt/bass/observational/planck_mes_bounds.py:205`: 현재 `compute_mes_bounds`는 2ε2, √3ε2, max(3ε1_res,2ε2,ε3)를 계산한다. typed successor import가 존재해도 이 함수 본문의 다른 계수를 자동으로 source-certified로 볼 수 없다. 패킷 R2의 해당 파일 설명과 현재 파일의 blanket legacy marker 여부는 별도이며, 이번 통합은 현재 source의 경로별 확인만 기록한다. 교체·실행하지 않았다.
- `htt/htt/htt/infer/nuisance_rank.py`: covariance whitening과 nuisance SVD projector, diagnostic rank payload가 있다. R2의 identified-subspace 개념과 MATCH하는 부품이나 physical response와 full tensor gauge를 공급하지 않는다. 새 R1–R5 대응은 ADAPTER_NEEDED다.
- `htt/htt/htt/infer/r9_confidence_image.py`: `JointCoverageEvent`, `StateFunctional`, `physical_confidence_image`는 동일 calibrated state-jet-anchor event를 요구한다. absent event는 unavailable이고 uncertain anchor를 fixed parameter로 숨기는 것을 거부한다. R3 이론 재사용과 합치되 실제 R3/R5 관측 law는 없다.
- `htt/htt/htt/infer/r7_depth_response.py`: flat FLRW, fixed observed redshift, first-order velocity의 observer/source kernels다. R2 exact local boost 및 homogeneous finite-tilt jet에 대한 검증으로 확장할 수 없다.
- `htt/src/common/conditional_source_image.py`의 BoxSourceImage, `htt/obsstat/mes_r7_source_image.py`: 525×4→5 BOX4 q-proxy calibration scenario를 소비한다. empirical D 등 physical quantities는 INSUFFICIENT_PHYSICAL_INPUTS, ellipsoid는 unsupported다. R1–R5 joint disk와 별개 namespace이며 물리 residual/source/optical bridge는 HOLD다.
- `docs/research_program/tensor_joint_r7/THEORY.md` T3와 `tensor_joint_r9/THEORY.md` T2/T4: retained geodesic radiation signs/rates 및 nuisance-aware confidence theory의 현재 대응 문서다. R3가 인용한 historical blobs와 현재 HEAD identity를 혼동하지 않는다. R9 formal/lifecycle status를 변경하지 않는다.

## claim별 매핑

MATCH는 정의·가정·입출력·단위가 맞는 inspected component에만 적용할 수 있다. 완전 대응 미확인에는 NOT_IMPLEMENTED/UNVERIFIED를 쓴다. ADAPTER_NEEDED는 존재 부품을 그대로 동일 이론 구현으로 부르지 않는 표지다. CONFLICT는 coefficient/authority의 구체적 차이이며 과학적 타당성 전체의 실패 선언이 아니다.

| Claim ID | 대응 | 현재 경로/구성요소 | 구현/증거 gap |
|---|---|---|---|
| R1.SHEAR.LB | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | Mask/noise estimation and useful residual budget; measure-class addendum not fully covered by original decision |
| R1.SHEAR.RESIDUAL | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | 실관측 입력 및 물리 예산 미확보 |
| R1.OPTICAL.ENDPOINT | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | Unknown emission morphology; ideal inverse is not unbiased noisy estimator; K is cumulative not present shear |
| R1.STRESS.BRIDGE | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | Expansion/stress consistency with complete Einstein–matter model; P=0 not generic self-gravitating radiation |
| R1.STATS.SHEAR | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | Full signed legacy x equivalence unresolved; quadratic occupancy differs from amplitude margin |
| R2.BUNDLE.PARITY | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | 실관측 입력 및 물리 예산 미확보 |
| R2.OPTICS.RV | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | R,V are photon generators, not static CMB or source proper motions |
| R2.RADIATION.WEAK | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | No evolution hierarchy closure or measured residual; polarization source/screen separate |
| R2.RADIATION.RANK | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | Algebraic rank is not observational identification |
| R2.BOOST.FIELD | ADAPTER_NEEDED | `htt/htt/htt/infer/r7_depth_response.py` | Current depth kernel is flat-FLRW low-speed and source coefficient is not global tilt |
| R2.MES.AUTHORITY | CONFLICT | `htt/src/common/mes_theorem_authority.py`<br>`htt/tsc/admissibility/three_bound_hierarchy.py`<br>`htt/bass/observational/planck_mes_bounds.py` | Nongeodesic attribution of registered omega/A rows; current authority verifier not executed |
| R2.GAUGE.PROJECTION | ADAPTER_NEEDED | `htt/htt/htt/infer/nuisance_rank.py` | 실관측 입력 및 물리 예산 미확보 |
| R2.LIKELIHOOD.CENTER | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | V1 HOLD preserved; corrected loss 0 vs uncentered 81 is historical elementary witness |
| R2.UNCERTAINTY.JOINT | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | 실관측 입력 및 물리 예산 미확보 |
| R2.STATS.TENSOR | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | Legacy signed x,Q_gauge,F_support,G_path not replaced; positive norm does not preserve cancellation |
| R3.OBSERVABLE.LEADING | ADAPTER_NEEDED | `htt/htt/htt/infer/nuisance_rank.py` | Separate raw and independent verdict file absent; ideal rank12 vs free-spin quotient rank9 only report-supported |
| R3.RESIDUAL.DISTANCE | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | Physical L,v and actual sample law absent; report embedded output is not separate raw |
| R3.SOURCE.RETAINED | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | CAS4/4B and supplementary promotion exploratory/report-supported; nonlinear remainder and polarized source not verified |
| R3.THOMSON.LOCAL | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | Opacity/gradients, intrinsic dipole and global field derivative absent; 0/0 remains undefined |
| R3.CONFIDENCE.ADAPTER | ADAPTER_NEEDED | `docs/research_program/tensor_joint_r9/THEORY.md`<br>`htt/htt/htt/infer/r9_confidence_image.py` | Current code requires actual common state-jet-anchor coverage; source report does not supply it |
| R4.GEOMETRY.CLOSURE | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | Time jets/source remain; h->lambda²h rescales gamma lambda^-1; normal result not tilted spatial bound |
| R4.TILT.ADAPTER | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | 실관측 입력 및 물리 예산 미확보 |
| R4.SHELL.COMPENSATION | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | Actual shell windows need moments and new kernel; no free source-motion/frame-spin cancellation; actual M/covariance absent |
| R4.CAS.REPAIR | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | V1 False/unevaluated output not valid scientific checks; no tolerance change |
| R5.AFFINE.RANK9 | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | No full data rank conclusion; uncertain p needs joint union of affine images |
| R5.TIMEJET.QUOTIENT | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | Derived combinations are not relabeled physical shear; need joint response and fixed-duration physical budget |
| R5.TARGET.BOUNDED | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | Not general recession-cone criterion; empty feasible set is inconsistency, not strong bound |
| R5.RADIATION.RANK8 | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | No new constraint when jets/source free within retained algebraic domain; physical positivity/time/matter may restrict domain |
| R5.DISK.JOINT | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | Sensitivity fixture only; independent sector balls/product not same joint disk |
| R5.DISK.LAW | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | Deterministic disk alone gives no probability; law is neither data posterior nor certified physical prior |
| R5.CHRONOLOGY | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | No host model/effort identity certification inferred |
| R5.CANDIDATES.HOLD | NOT_IMPLEMENTED | 검토 범위에서 특정 production 구현 미확인 | Eq71 sign discrepancy report-supported; official erratum/whole paper not adjudicated; no blanket earlier-result HOLD |

이론 채택=`DOCUMENTED_WITH_ORIGINAL_CONDITIONS`, 이번 구현 검증=`NOT_RUN_THIS_INTEGRATION`, 실관측 admission=`HOLD_NOT_RUN`을 별도 유지한다. R1–R5 원본 checks.py/.wl은 evidence reproduction source이고 production module이 아니다. 광범위 code search에서 우연히 같은 기호가 보인 결과는 매핑 증거로 사용하지 않았다. NOT_IMPLEMENTED는 inspected scope의 판단이며 저장소 전체 부재 정리가 아니다.
