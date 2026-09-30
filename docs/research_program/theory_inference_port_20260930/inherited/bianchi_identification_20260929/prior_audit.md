# 선행 방법론 감사 — Bianchi 식별 재탐색에 사용할 정확한 범위

2026-09-29. 기존 보존 문서의 읽기 감사다. 최신 원격 저장소 감사, 과학 계산 재실행, 기존 판정 승격은 수행하지 않았다. 경로는 `/workspace/scratch/83eeacddad29` 기준이다.

## 1. 가장 중요한 정정: 기존 판정은 보편적인 Bianchi 불가능 정리가 아니었다

`report_20260929/sources/repo/docs/research_reports/final_candidate_20260907/HTT_REPORT_A_EVIDENCE_INTEGRATED_R3.md` §1, line 37은 해당 보고서에 Bianchi-family identification이 포함되지 않으며 family label에는 별도의 forward model과 identification argument가 필요하다고 명시한다. 동일 문서 lines 15–21, 33과 §6 lines 499–547은 observable tensor representation, physical state, joint response set과 population identification을 구별한다. 따라서 이번 연구가 유한 jet·Lie 대수·물리 제약의 새 response 및 식별 논증을 제시한다면, 기존 정리를 번복하지 않고 정당하게 연구 범위를 넓힌다.

`report_20260929/sources/repo/docs/research_reports/theory_synthesis_20260913/REPORT.md` §14 lines 495–514는 순간 선형 response의 scalar-curvature 열 0과 곡률의 동역학적 효과를 이미 구별한다. 제한된 LRS Bianchi III/Kantowski–Sachs 가지의 FLRW 근방 particular mode는 Σ≈−2K/(5+3w)이나, transient·remainder·branch 존재 조건이 필요하며 전체 유형 식별로 승격하지 않는다. 이는 이번 재탐색의 직접적인 선행 근거다.

해석: 이전 ceiling은 주로 **현재 입력/response의 미완성**, **snapshot의 derivative 결손**, **명시된 nuisance 아래의 동등법칙**, **좁은 처리 연산자 영역**이다. 이 모두를 ‘어떠한 solver-free 관측으로도 Bianchi를 분류할 수 없다’로 합쳐서는 안 된다.

## 2. 계승할 상태와 통계 객체

권위 문서: `report_20260929/sources/docs/research_program/typefree_loop2_20260928/source/RESEARCH_ARCHITECTURE_KO.md`, §§1–4 (특히 lines 7–26, 28–95).

공동 상태 ξ는 metric, 선택 congruence U, 기준 congruence N, radiation, 필요한 spacetime jet, source/boundary, observation operator, nuisance, reference/body를 함께 포함한다. K(일반 운동학), O(광학), E(Einstein), L(미분류 Lie 대수), M(MES), S(joint statistics)는 별개 가지다. 같은 ξ와 같은 congruence에서 양립함을 확인하고 합성한다. 총 응력 energy eigenframe, 물질 성분 frame, dust frame, observer frame은 자동으로 같지 않다.

| 객체 | 계승된 의미 | Bianchi 연구에서의 쓰임과 한계 |
|---|---|---|
| x | φ_j(ξ_i)의 sample-by-functional 배열; tensor/vector 원자료 보존 | type별 허용 상태상의 공통 함수족 평가 |
| Q | anchor gauge γ_B, margin 1−γ_B, joint interval | premise 만족/위반; 유형 posterior가 아님 |
| F | 같은 상태별 방향 support 이용률 | 각 type의 관측 가능 형상 및 허용 방향 비교 |
| Π | 명시한 joint law와 scalarization의 exceedance/envelope | law가 공급된 뒤에만 확률 의미 부여 |
| G_F | depth/mask/feature의 signed transport와 coherence 경로 | 추가 depth의 실제 응답 차이를 검사; z bin을 time derivative로 대체하지 않음 |

동일 의미 표: `.../theory_synthesis_20260913/REPORT.md` §23.1–23.2, lines 761–805. 기존 scalar 이름을 새 tensor 의미로 단순 alias하지 않는다. `code_upgrade_20260929/analysis/formalism_map.md` lines 37–47의 PR142 F/Pi/GF는 successor 정의와 다른 진단들이므로 별도 유지한다.

MES normalization은 같은 ξ에서 `100[1−γ_Bχ(ξ)(φ(ξ)−φ_ref(ξ))]`다. 음의 margin을 0으로 자르지 않는다. 같은 관측조건의 premise-relative 사용률은 비교 가능하지만 covariance/rank/selection이 다르면 검출력까지 같지 않다. 정규화는 이미 존재하는 data-law ambiguity를 제거하지 않는다.

## 3. 명제별 유지 영역과 분류에 대한 귀결

### 3.1 임의 관측자 1-jet와 stress-selected congruence

근거: `report_20260929/notes/theory_sources.md` lines 32–89; 원 결정 `.../typefree_loop2_20260928/source/ADJUDICATED_AMENDMENTS_KO.md` TF-P1/P2/P3.

고정 metric과 U(p) 아래에도 임의 정규화 observer의 ∇U(p)는 12개 성분 θ(1)+σ(5)+ω(3)+A(3)를 자유롭게 가진다. 유한 β(p)는 derivative bound가 아니다. 이 명제는 arbitrary observer에 대한 것이며 물질/균질 invariant congruence에 추가 제약을 부과하는 것을 금지하지 않는다.

T의 단순 timelike eigenbranch로 U를 선택하고 rest stress gap δ>0일 때 `∇_Eμ U=−c L⁻¹D_μ`, `θ²/3+||σ||²+2|ω|²+|A|²/c² ≤ c²Σμ|D_μ|²/δ²`. 이는 같은 상태의 stress derivative budget을 입력으로 요구한다. 기존 MES/dust 상계와 자동 동일하지 않다.

Einstein total stress와 위 선택 규칙에서 metric 3-jet는 U(p),∇U(p)를 정한다. metric 2-jet가 일반적으로 부족하다는 conformal 반례가 존재한다. 그러나 이 정리는 **선택된 congruence의 pointwise first derivative**의 충분 차수이며, spacetime germ/Killing algebra/공간균질성/전역 Bianchi label의 충분 차수 정리가 아니다. 관측 cosmographic jet가 metric 3-jet 전부를 제공한다는 결론도 없다.

분류 귀결: Lie 대수/곡률을 복원할 새 명제의 입력을 ‘공간균질 symmetry-adapted frame의 기하 jet’와 ‘관측 reconstructed jet’로 분리한다. 물질 congruence의 ω≠0에서 그 rest projector를 homogeneous hypersurface의 intrinsic metric이라고 부르지 않는다.

### 3.2 Same-state support/gauge와 quotient

근거: `.../ADJUDICATED_AMENDMENTS_KO.md` TF-S1–S3, 특히 lines 85–98; 보강 설명 `notes/theory_sources.md` lines 91–149.

유한차원 compact convex body B에 0이 interior이고 p:E→V=p(E)가 고정 선형이면 `γ_pB(v)=min_{py=v}γ_B(y)` 및 `h_pB(u)=h_B(p*u)`다. v=0에서 최소 lift는 0이다. V={0}이면 gauge=0이지만 profile은 NO_DIRECTIONS다. quotient gauge≤1은 허용 body 내부 lift 하나가 있다는 뜻이며 실제 hidden norm 또는 physical state가 결정되었다는 뜻이 아니다. 최소화는 고정 B의 unrestricted algebraic fiber이고, type별 Einstein/matter 물리집합 K의 fiber는 별도로 교차해야 한다.

분류 귀결: type별 admissible set K_b와 joint C를 정의하고 실제 목표 `label(K_b∩response⁻¹(data))`를 계산해야 한다. 공통 outer body 안에 들어온다는 이유로 유형을 승인하지 않는다. 반대로 해당 type의 **검증된 outer image**와 관측 compatibility set이 불교차이면 조건부 배제는 가능하다. 이 마지막 항은 이번 연구에 제안하는 사용 방식이며 기존 저장 명제를 새로운 type 판정 결과로 가장하지 않는다.

### 3.3 동일 full data law no-go와 rank의 정확한 위치

근거: `.../ADJUDICATED_AMENDMENTS_KO.md` TF-S4 lines 101 이후; `notes/theory_sources.md` lines 150–168, 194–205.

`D=μ₀+Rk+Nη+ε`에서 ε의 전체 law가 고정이고 Rh=Nc이며 (k,η),(k+h,η−c)가 둘 다 물리적으로 허용되면 full data law가 같다. 목표 f는 실제 equivalence fiber마다 상수일 때 quotient로 내려간다. f₀≠f₁인 두 동등법칙 상태에서 양쪽 coverage≥1−α인 confidence set은 `P{diam Aα≥d(f₀,f₁)}≥max(0,1−2α)`를 만족한다. 같은 mean/Jacobian만으로는 부족하다. Parameter-dependent covariance이면 Gaussian Fisher에 covariance derivative trace term이 남는다.

분류 귀결: 서로 다른 Bianchi labels의 허용 상태가 같은 실험의 full law를 내면 unique classification은 불가하다. 하지만 다른 redshift/optical 실험이 law를 다르게 만들 수 있으며, 기존 null column만으로 그 가능성을 닫지 않는다. 모든 depth에서 같은 kernel인 경우에만 stacking이 개선하지 못한다. 정확한 metric 자체가 여러 transitive group labels를 허용하는 경우에는 관측 정밀도 증가로도 label ambiguity가 사라지지 않으므로 대상 label의 정의를 먼저 고정해야 한다.

정오표: `report_20260929/sources/docs/research_program/typefree_loop2_closeout_20260928/ERRATA_F1_W1_KO.md`, 전체. `||Pv||≤C||Bv|| ⇔ ker B⊆ker P`는 유한차원 unrestricted linear variation, affine에서는 허용 variation에 적용한다. 일반 bounded/curved K에는 필요조건이 아니다. B=0,P=id,K=[−1,1]이면 kernel inclusion 없이 image가 유계다. 따라서 finite residual bound, boundedness, singleton identification, confidence calibration을 구별한다. Type별 nonlinear constraint가 response fiber를 단일점 또는 단일 label로 좁힐 가능성은 이 정오표와 양립한다.

### 3.4 CMB morphology·local boost와 물리 유형

근거: final_candidate R3 lines 17, 37, §§6,8–10; theory_synthesis §12 lines 410–446.

실수 harmonic carrier와 STF Q/O 사이의 정확 변환은 morphology 표현을 복원한다. Quadrupole와 physical shear가 같은 STF2 표현이라는 사실은 인과 response가 아니다. Full-sky local-observer temperature response는 radiation–observer lane이고 global matter tilt/shear/vorticity 전달함수가 아니다. intrinsic octupole를 자유롭게 허용하면 well-conditioned B_Q 역산도 실제 β의 유일 추정이 아니다.

Cut-sky에서는 high-source nuisance image로 quotient한다. 등록된 continuum wide-mask L=12 axial 예의 rank32는 exact algebraic evidence이나 finite HEALPix matched-control rank는 unresolved다. 이를 모든 관측 파이프라인의 불가능 정리로 확장하지 않는다.

분류 귀결: CMB-only에 arbitrary intrinsic radiation을 허용한 채 morphology를 직접 family likelihood로 바꾸지 않는다. Solver-free route를 local geometry/optics에 기반시키고 CMB는 실제로 제공된 response와 source assumptions 아래에서만 결합한다.

## 4. I1/I2/I3의 보호된 결과

근거: `notes/theory_sources.md` lines 285–289; 원문 `report_20260929/sources/docs/research_program/mes_verified_checkpoints_20260928/I2/integration_i2/PHYSICAL_RESIDUAL_AND_IDENTIFIED_SET_KO.md`, §§1–7; `report_20260929/sources/docs/research_program/mes_i3_gaia_screening_20260928/REPORT_KO.md`, §§1–4.

- I1의 residual-known target은 `Z=σ−STF(p aᵀ)`이고 p≠0에서 quadrupole residual만 주고 acceleration이 자유로우면 rank3 ambiguity, 2D transverse STF quotient만 남는다. 임의 Einstein/matter constraints 뒤에도 유지되는 보편 no-go가 아니다.
- I2는 Λ=0, geodesic normal Bianchi I, massless Einstein–Vlasov의 정확 local counterfamily다. 같은 instantaneous isotropic radiation과 임의 절대 shear를 갖지만 H도 변한다. `||S||/H→√6`이므로 normalized shear는 무한하지 않다. 같은 상태 H,ρ를 고정하면 `||S||²=6H²−2κ_rateρ`, κ_rate=8πG/c²인 STF sphere다. 음수면 empty, 0 singleton, 양수 nonconvex sphere이며 all-direction expansion에는 HI+S≻0을 더한다. 상태는 DEFENDED_CONDITIONAL; 실제 관측 CMB bound/모든 Bianchi가 아니다.
- I3의 이상적인 같은 emitter–observer congruence/Fermi frame local vertex는 `κ₀(n)=P_nσn+ω×n`, `Hcal(n)=H−a·n+σ:nn`이다. Free frame spin이면 ω−Ω_frame만 측정하며, arbitrary source transverse field는 임의 shear 변화도 흡수한다. Gaia proper motion은 유한 시간 fit이고 local vertex 자체가 아니다. Distance/local remainder, source velocity law, 독립 spin/acceleration calibration, cross-source covariance와 selection이 미확보다. 따라서 HOLD_INPUT_INCOMPLETE를 유지한다.

광학 용어에 주의: I2 다음 단계의 ‘optical shear input’은 후속 I3에서 congruence shear를 optical/cosmographic response로 추정하려는 뜻으로 구체화된다. Sachs screen shear를 physical fluid σ로 직접 동일시하는 문장은 이 감사에서 발견되지 않았다. 둘을 같은 기호로 처리해서는 안 된다. 별도 registry `.../I1/recovery/latest_loops/htt_paper_a_reloptics_source_seal_loop_20260916/htt_paper_a_reloptics_source_seal_loop_20260916/RELATIVISTIC_OPTICS_TYPE_REGISTRY.md`는 Jacobi screen map, u-relative σ, endpoint redshift와 directional cosmography를 별개의 유형으로 기록한다.

## 5. 기존 형식검증과 코드 준비도의 한계

`.../typefree_loop2_closeout_20260928/ERRATA_F3_LEAN_SCOPE_KO.md` 전체: Lean gap_column3는 세 성분의 **단일 column** estimate이고 3개 column 전체의 theorem이 아니다. 3×3 Frobenius decomposition은 별도 명제다. TF-S2/S4 Lean 범위는 event inclusion, measure monotonicity, diameter event, union-bound 구성요소이며 full law/measurability/calibration 전체가 형식화되었다고 부르지 않는다.

`code_upgrade_20260929/handoff/AUTHORITY.json`은 source commit 3aeecb100d9b938bfffdade093ae8938d84efcfd, source tree 8fc6852e8bdda17db4c2208771e0362d35defb82를 기록한다. 당시 I2 DEFENDED_CONDITIONAL, I3 HOLD_INPUT_INCOMPLETE이며 source checks를 native family identification이나 universal MES/likelihood admission으로 승격하지 않는다. 이는 당시 pinned preparation 근거이고 현재 main head 검증이 아니다.

`code_upgrade_20260929/analysis/formalism_map.md`는 60개 파일 23,930행의 read-only 조사였다. 기존 body/gauge, supported covariance quotient, rank, Schur morphology, finite-vertex/rational-polytope support, depth transforms를 재사용할 수 있다. 그러나 general physical fiber contraction, all-sector finite anchors, physical line-of-sight kernel, finite-tilt full response가 완성되었다고 할 수 없다. Exact/numeric narrow identified_set engines를 임의 nonlinear Bianchi domain solver로 대체해서는 안 된다.

## 6. 이번 연구루프에 대한 구체적인 결론

1. 연구 목표는 ‘유일 Bianchi type’ 하나로 시작하지 말고, (a) 국소 기하/kinematic 특성, (b) 선언된 homogeneous action에 관한 Lie algebra class, (c) 관측 law 아래 남는 label 집합을 별도로 정의한다.
2. Solver-free classification의 긍정 경로는 Lie algebra의 대수적 제약 + 선택된 homogeneous hypersurface의 curvature/constraint + 제한된 cosmographic/optical jet의 공동 허용집합이다. 필요한 input이 실제 관측에서 제공되는지는 별도의 재구성 문제다.
3. 동일 metric의 여러 transitive group action 반례, 동일 full law 반례, boundary contraction/near-degeneracy를 각각 제시하면 왜 unique label이 안 되는지 더 정확히 말할 수 있다. 이것은 ‘현재 구현 없음’과 구별해야 한다.
4. Outer prediction set과 calibrated joint observation set의 불교차는 조건부 배제의 안전한 대상이다. 비어 있지 않은 교차는 해당 label의 검증/우주 식별을 뜻하지 않는다. Unique surviving label도 가정집합과 type universe가 exhaustive할 때만 그 안에서의 조건부 주장이다.
5. MES gauge/Q/F/Π/G_F는 후보별 전제 예산 및 morphology/depth 통계의 공통 언어다. 이 정규화 자체는 type information을 생성하지 않는다. Covariance/law 변화, type별 물리 constraints와 독립 optical information이 실제로 label 집합을 좁히는지 계산해야 한다.
6. 위 제안은 기존 보호 상태를 자동 승격하지 않는다. 새 exact algebraic identity/반례와 기존 결과의 계승, 향후 observational application의 미완성을 문서에서 명확히 나눈다.

