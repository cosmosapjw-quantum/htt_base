# 기능·분석 길잡이

아래 카드는 소스의 연구 질문과 입력·출력을 연결하는 탐색 안내다. 레지스트리에 남은 오래된 주장도 포함하므로 각 카드의 버전·가정을 함께 읽는다.
연구 코드·분석·증명 도구는 실행하지 않았다. 현재 실행 가능성이 확인된 분석 목록으로 사용하지 않는다.

## GUIDE-01 — 진단 변수 분리: Q·F·Pi·G_F·P_post

진단량과 HTT posterior 양을 혼동 없이 어떤 계약으로 구분하는가?

- 소유 표기: MIO/HTT/common
- 입력: Q, F, Pi, G_F, P_post 정의; 도메인 검사된 comparator 의미론
- 출력·등록 결과: 변수-역할 구분; MIO/HTT 경계용 형식화
- 실행 정보: 미기록 (등록 소스: budget_spec.py, posterior_pushforward.py)
- 상태와 한계: P2는 ACTIVE_CONDITIONAL/C1-C2로 기록되어 있으며, MIO posterior·evidence·truth certificate는 허용되지 않는다.
- 후속 확인: E3의 채널별 분모 정책, diagnostic occupancy vector, transfer 안정성 요약
- 원문: [docs/research_program/THEOREM_REGISTRY.yaml](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/research_program/THEOREM_REGISTRY.yaml), [docs/generated/research_program_experiment_registry.yaml](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/generated/research_program_experiment_registry.yaml)

관련 코드·기록 조회:

```bash
python3 -B scripts/project_catalog.py query --ref baseline --q "budget_spec" --limit 15
python3 -B scripts/project_catalog.py query --ref baseline --q "posterior_pushforward" --limit 15
```

## GUIDE-02 — 부호 있는 x_C 식별구간

부호 있는 곡률을 포함할 때 x_C의 두 가지 식별구간 분기를 어떻게 계산·해석하는가?

- 소유 표기: OBSSTAT/MIO
- 입력: product-factorized feasible set; 계수와 각 성분의 하한·상한; open/all-curvature 분기
- 출력·등록 결과: I_x endpoint decomposition; open curvature [0.11,0.17] 및 all-curvature [0.09,0.17] 등록 분기
- 실행 정보: 미기록 (등록 소스: egs3_coverage_strengthened.py)
- 상태와 한계: T1p ACTIVE는 등록 상태일 뿐 이번 조사에서 재검증하지 않았다. product-factorization 가정에 한정된다.
- 후속 확인: 가정·입력 범위가 바뀌면 별도 seal과 구간 재산출
- 원문: [docs/research_program/THEOREM_REGISTRY.yaml](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/research_program/THEOREM_REGISTRY.yaml)

관련 코드·기록 조회:

```bash
python3 -B scripts/project_catalog.py query --ref baseline --q "egs3_coverage_strengthened" --limit 15
```

## GUIDE-03 — 일반 분수계획 depth-gap 구간

joint feasible set과 product relaxation 사이의 fractional-program endpoint 차이를 어떻게 판정하는가?

- 소유 표기: MIO/OBSSTAT
- 입력: joint feasible set; 분자 N·분모 D; endpoint의 diagonal-attainment 조건
- 출력·등록 결과: I_joint subseteq I_prod; endpoint별 equality criterion; argmin/argmax corollary
- 실행 정보: 미기록 (등록 소스: egs3_fractional_program.py)
- 상태와 한계: T2G ACTIVE/C2가 P36·T2p를 대체한다. 철회된 계수 부호만의 per-endpoint iff를 사용하면 안 된다.
- 후속 확인: 새 feasible-set 모델에는 Charnes-Cooper/vertex exact-QQ 인증을 다시 연결
- 원문: [docs/research_program/THEOREM_REGISTRY.yaml](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/research_program/THEOREM_REGISTRY.yaml)

관련 코드·기록 조회:

```bash
python3 -B scripts/project_catalog.py query --ref baseline --q "egs3_fractional_program" --limit 15
```

## GUIDE-04 — 응답 rank와 넓은 depth 회복

중복 채널·단일 shell degeneracy가 있을 때 어느 관측 설계가 response rank를 회복하는가?

- 소유 표기: HTT/OBSSTAT
- 입력: 관측 채널; response 구조; single-shell 또는 broad-depth 지원
- 출력·등록 결과: duplicated-channel rank 진단; single-shell degeneracy 및 broad-depth recovery 조건
- 실행 정보: 미기록 (등록 소스: paper_a_closure.py)
- 상태와 한계: P8은 ACTIVE, P10은 ACTIVE_CONDITIONAL/C2로 기록된다. E4는 nuisance projection과 null 없이 discrimination claim을 차단한다.
- 후속 확인: nuisance-projected rank report, Fisher compression, degeneracy-direction audit
- 원문: [docs/research_program/THEOREM_REGISTRY.yaml](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/research_program/THEOREM_REGISTRY.yaml), [docs/generated/research_program_experiment_registry.yaml](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/generated/research_program_experiment_registry.yaml)

관련 코드·기록 조회:

```bash
python3 -B scripts/project_catalog.py query --ref baseline --q "paper_a_closure" --limit 15
```

## GUIDE-05 — Volterra depth-memory와 횡방향 vorticity 채널

깊이 의존 memory와 transverse 채널이 vorticity 정보를 언제 열어 주는가?

- 소유 표기: OBSSTAT/MIO
- 입력: depth kernel; H(z) 또는 any-H kernel; 횡방향 관측 채널
- 출력·등록 결과: Volterra depth-memory representation; vorticity-sector reopening 조건
- 실행 정보: 미기록 (등록 소스: egs3_volterra_memory.py, egs3_volterra_hz.py, egs3_vorticity_channels.py)
- 상태와 한계: P21·P22는 ACTIVE_CONDITIONAL/C2로 기록된다. P21의 constant-H caveat는 any-H successor로 닫혔다고 등록되었을 뿐 본 과업에서 검증하지 않았다.
- 후속 확인: 실측 depth response·sampling law와 matched null 확보
- 원문: [docs/research_program/THEOREM_REGISTRY.yaml](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/research_program/THEOREM_REGISTRY.yaml)

관련 코드·기록 조회:

```bash
python3 -B scripts/project_catalog.py query --ref baseline --q "egs3_volterra_memory" --limit 15
python3 -B scripts/project_catalog.py query --ref baseline --q "egs3_volterra_hz" --limit 15
python3 -B scripts/project_catalog.py query --ref baseline --q "egs3_vorticity_channels" --limit 15
```

## GUIDE-06 — Fisher·transfer-profile 분석

다중 ell과 transfer profile이 Fisher floor 및 식별 가능성에 어떤 추가 정보를 주는가?

- 소유 표기: OBSSTAT/BASS
- 입력: multi-ell features; transfer profile; Fisher response
- 출력·등록 결과: multi-ell Fisher floor; transfer-profile refinement
- 실행 정보: 미기록 (등록 소스: egs2_fisher.py, shear_quadrupole_seminative.py)
- 상태와 한계: P17은 ACTIVE_CONDITIONAL/C2이다. 외부/proxy transfer는 native가 아닌 transfer-conditional 경로이며, family identification은 차단된다.
- 후속 확인: native morphology atlas와 외부 null/mask/covariance/family-equivalence gates
- 원문: [docs/research_program/THEOREM_REGISTRY.yaml](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/research_program/THEOREM_REGISTRY.yaml), [docs/generated/research_program_experiment_registry.yaml](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/generated/research_program_experiment_registry.yaml)

관련 코드·기록 조회:

```bash
python3 -B scripts/project_catalog.py query --ref baseline --q "egs2_fisher" --limit 15
python3 -B scripts/project_catalog.py query --ref baseline --q "shear_quadrupole_seminative" --limit 15
```

## GUIDE-07 — e-value와 finite-cover calibration

exceedance 및 e-value를 어떤 null calibration과 finite-cover 결합 아래 해석하는가?

- 소유 표기: OBSSTAT/HTT
- 입력: null feature distributions; exceedance statistic; finite cover
- 출력·등록 결과: exceedance/e-value calibration; finite-cover e-value combination; Rao-Blackwell reachable-sector 진단
- 실행 정보: 미기록 (등록 소스: egs3_calibration.py)
- 상태와 한계: P19은 ACTIVE_CONDITIONAL, P29·P20은 ACTIVE로 기록되나 이번 카탈로그 조사에서 calibration을 실행하지 않았다.
- 후속 확인: finite-mock coverage, prior-support surface, null-threshold summary (E1)
- 원문: [docs/research_program/THEOREM_REGISTRY.yaml](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/research_program/THEOREM_REGISTRY.yaml)

관련 코드·기록 조회:

```bash
python3 -B scripts/project_catalog.py query --ref baseline --q "egs3_calibration" --limit 15
```

## GUIDE-08 — 공분산 MES와 morphology 보존

diagonal covariance 압축이 잃는 morphology와 full covariance MES가 주는 tightening을 어떻게 진단하는가?

- 소유 표기: OBSSTAT/BASS/MIO
- 입력: full covariance; low-ell morphology features; MES budget/ceiling 모델
- 출력·등록 결과: diagonal-loss diagnostic; full-covariance MES tightening; rank-failure no-result 또는 morphology information-gain 분기
- 실행 정보: 미기록 (등록 소스: budget_ceiling_optimizer.py)
- 상태와 한계: P23-P25는 모두 ACTIVE_CONDITIONAL/C2-C3이다. E7의 morphology 사용에는 해당 레지스트리의 atlas·null 조건을 확인해야 한다.
- 후속 확인: mask/noise simulation calibration, BiPoSH residual summary, covariance MES report, atlas
- 원문: [docs/research_program/THEOREM_REGISTRY.yaml](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/research_program/THEOREM_REGISTRY.yaml), [docs/generated/research_program_experiment_registry.yaml](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/generated/research_program_experiment_registry.yaml)

관련 코드·기록 조회:

```bash
python3 -B scripts/project_catalog.py query --ref baseline --q "budget_ceiling_optimizer" --limit 15
```

## GUIDE-09 — Bianchi V momentum-response 및 동역학 seal

tilted LRS Bianchi V에서 momentum-response relation과 constraint preservation을 어떤 범위에서 점검하는가?

- 소유 표기: BASS/OBSSTAT
- 입력: non-vacuum dust/radiation trajectory; Gauss·momentum residual; rapidity relation
- 출력·등록 결과: conditional momentum-response formula; trajectory residual monitor; dynamical P5 relation check
- 실행 정보: 미기록 (등록 소스: egs3_bianchi_v_constraint.py, egs3_bianchi_v_dynamics.py)
- 상태와 한계: P5는 ACTIVE_CONDITIONAL이고 BV-DYN은 ACTIVE/C2로 기록된다. BV-DYN은 King-Ellis item도 dynamical T3 endpoint realization도 아니라고 명시한다.
- 후속 확인: 별도 native low-ell solver atlas; 이 카드만으로 family/geometry admission 불가
- 원문: [docs/research_program/THEOREM_REGISTRY.yaml](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/research_program/THEOREM_REGISTRY.yaml)

관련 코드·기록 조회:

```bash
python3 -B scripts/project_catalog.py query --ref baseline --q "egs3_bianchi_v_constraint" --limit 15
python3 -B scripts/project_catalog.py query --ref baseline --q "egs3_bianchi_v_dynamics" --limit 15
```

## GUIDE-10 — constraint-surface endpoint witnesses

identified interval endpoint를 homogeneous initial-data candidate로 어느 sharpness 수준까지 실현하는가?

- 소유 표기: BASS/OBSSTAT
- 입력: Bianchi V upper-endpoint construction; transverse shear; antipodal flux cancellation; Gauss closure
- 출력·등록 결과: upper-endpoint level-2 witness; lower-endpoint W^2 sector의 limitation 기록
- 실행 정보: 미기록 (등록 소스: egs3_nonlinear_realization.py)
- 상태와 한계: T3-full은 ACTIVE_CONDITIONAL/C2, sharpness_level 2다. lower W^2 rotational mode는 constraint-unverified이고 level-3 dynamics는 미점검이다.
- 후속 확인: King-Ellis rotating-congruence rederivation 및 dynamical solution-space sharpness
- 원문: [docs/research_program/THEOREM_REGISTRY.yaml](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/research_program/THEOREM_REGISTRY.yaml)

관련 코드·기록 조회:

```bash
python3 -B scripts/project_catalog.py query --ref baseline --q "egs3_nonlinear_realization" --limit 15
```

## GUIDE-11 — estimated-covariance coverage

추정 공분산을 쓰는 residual test와 special-model endpoint coverage를 어떤 표본 가정 아래 구분하는가?

- 소유 표기: OBSSTAT
- 입력: Gaussian y; independent Wishart covariance ensemble; fixed response/nuisance projector/rank/active set
- 출력·등록 결과: Hotelling T²/F residual test; deterministic-width Imbens-Manski special-model coverage
- 실행 정보: 미기록 (등록 소스: egs3_coverage_strengthened.py)
- 상태와 한계: T4p·T5p는 ACTIVE_CONDITIONAL/C2이며, selection이 covariance mocks를 재사용하면 ensemble split이 필요하다. T5p의 exactness는 special model에 한정된다.
- 후속 확인: 실측/선택 설계가 바뀌면 독립 mock allocation과 가정 재검토
- 원문: [docs/research_program/THEOREM_REGISTRY.yaml](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/research_program/THEOREM_REGISTRY.yaml)

관련 코드·기록 조회:

```bash
python3 -B scripts/project_catalog.py query --ref baseline --q "egs3_coverage_strengthened" --limit 15
```

## GUIDE-12 — King-Ellis 회전 perfect-fluid 동역학

Omega_k>0의 rotating perfect-fluid development와 Omega_k=0 obstruction을 어떻게 분리하는가?

- 소유 표기: OBSSTAT/GR
- 입력: type-V off-diagonal 7x7 first-principles system; dust/radiation; u-frame conservation 및 Raychaudhuri identities
- 출력·등록 결과: Omega_k>0 rotating-development 기록; Omega_k=0 double-obstruction 분류
- 실행 정보: 미기록 (등록 소스: wolfram/ke_rotating_congruence.wls 및 registry source set)
- 상태와 한계: KE-DYN은 ACTIVE/C2, sharpness_level 3으로 기록되지만 본 과업은 proof engine을 실행하지 않았다.
- 후속 확인: 등록된 W² re-attribution interpretive question은 별도 과업으로 유지
- 원문: [docs/research_program/THEOREM_REGISTRY.yaml](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/research_program/THEOREM_REGISTRY.yaml), [docs/research_program/OPEN_ITEMS_LEDGER.md](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/research_program/OPEN_ITEMS_LEDGER.md)

관련 코드·기록 조회:

```bash
python3 -B scripts/project_catalog.py query --ref baseline --q "King-Ellis" --limit 15
```

## GUIDE-13 — 곡률-전단 slaving 및 finite ceiling

anisotropic Omega_k 재개방에서 curvature-shear slaving과 class-conditional ceiling을 어떻게 기록하는가?

- 소유 표기: OBSSTAT/GR
- 입력: LRS Bianchi III/Kantowski-Sachs; transient-decayed mode; q와 curvature K
- 출력·등록 결과: Sigma=kappa K, kappa=-1/(2+q) 등록 relation; finite attribution/class-conditional ceilings
- 실행 정보: 미기록 (등록 소스: axis_g_omega_k_reopening test 및 k5 ceiling card)
- 상태와 한계: OMK-REOPEN ACTIVE/C2 기록은 instantaneous null을 변경하지 않으며 아무 claim promotion도 포함하지 않는다고 명시한다.
- 후속 확인: 새 observational use에는 bound input·config identity와 claim lane 재평가
- 원문: [docs/research_program/THEOREM_REGISTRY.yaml](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/research_program/THEOREM_REGISTRY.yaml), [docs/research_program/OPEN_ITEMS_LEDGER.md](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/research_program/OPEN_ITEMS_LEDGER.md)

관련 코드·기록 조회:

```bash
python3 -B scripts/project_catalog.py query --ref baseline --q "곡률-전단" --limit 15
```

## GUIDE-14 — MES geodesic anchor와 MESb provenance

geodesic MES vorticity ceiling과 print-only MESb non-geodesic 계수를 어떻게 provenance별로 분리하는가?

- 소유 표기: OBSSTAT/GR
- 입력: MESa primary-source bounds; C1/C2 reduction; accessible-source web trace
- 출력·등록 결과: geodesic omega anchor; MESb in-house non-geodesic bounds refutation 기록; print-only internal algebra blocker
- 실행 정보: 미기록 (registry는 SymPy+Wolfram two-engine reduction을 기록)
- 상태와 한계: MES-REFREEZE·MES-MESB-TRACE의 ACTIVE는 과거 등록 상태다. MESb Eqs.30-36의 내부 유도는 print-only PDF 접근 부족으로 blocked 상태다.
- 후속 확인: 정당한 print-only PDF 접근 후 MESb 내부 대수 재유도
- 원문: [docs/research_program/THEOREM_REGISTRY.yaml](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/research_program/THEOREM_REGISTRY.yaml), [docs/research_program/OPEN_ITEMS_LEDGER.md](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/research_program/OPEN_ITEMS_LEDGER.md)

관련 코드·기록 조회:

```bash
python3 -B scripts/project_catalog.py query --ref baseline --q "MES" --limit 15
```

## GUIDE-15 — R8 orbit/representation 합성 실행

synthetic tensor orbit bounds와 full-tensor representation을 어떤 저장된 실행 결과로 탐색하는가?

- 소유 표기: HTT/obsstat/restricted BASS benchmark
- 입력: 30 saved pools; mock/observed component tensors; exact rational quaternion rotation을 포함한 orbit procedure
- 출력·등록 결과: 7,186 pair upper-bound improvements; 44/45 mock tensor reconstruction; campaign/summary.json 및 orbit_continuation/summary.json
- 실행 정보: docs/generated/tensor_joint_r8/final/EXECUTION.md에 기록됨 (정확한 명령은 지정 입력에 미포함)
- 상태와 한계: 내부 non-claim-bearing synthesis다. 25 pools unresolved, 0 reject; qualified observed CMB pool이 없고 independent CAS/scientific acceptance는 미달이다.
- 후속 확인: 독립 CAS obligations, qualified observed pool, held diagnostic 해소
- 원문: [docs/generated/tensor_joint_r8/final/REPORT.md](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/generated/tensor_joint_r8/final/REPORT.md)

관련 코드·기록 조회:

```bash
python3 -B scripts/project_catalog.py query --ref baseline --q "r8" --limit 15
```

## GUIDE-16 — R8 restricted R3 history·optics benchmark

고정 weak-anisotropy Bianchi-I history와 reverse-ray optics benchmark의 실행 범위는 무엇인가?

- 소유 표기: HTT/obsstat/restricted BASS benchmark
- 입력: LRS Bianchi-I two-antipodal dust streams; isotropic collisionless Planck photons; Lambda; six kappa/zeta cases, a=1..2
- 출력·등록 결과: 54 histories; 432 forward/reverse-ray pairs; 288 passing-history-associated eligible rays; restricted_history/results.json
- 실행 정보: docs/generated/tensor_joint_r8/final/EXECUTION.md에 기록됨 (정확한 명령은 지정 입력에 미포함)
- 상태와 한계: 36 histories pass, 18 coarse histories fail; fixed benchmark predictions에 observed likelihood가 없고 radiation derivative jet은 unavailable이다. arbitrary parameters 또는 global caustic theorem의 근거가 아니다.
- 후속 확인: observed likelihood와 radiation derivative laws; native low-ell solver atlas는 별도 blocker
- 원문: [docs/generated/tensor_joint_r8/final/REPORT.md](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/generated/tensor_joint_r8/final/REPORT.md)

관련 코드·기록 조회:

```bash
python3 -B scripts/project_catalog.py query --ref baseline --q "r8" --limit 15
```

## GUIDE-17 — 관측 자료 준비도와 proposal analysis lanes

기존 관측 인벤토리와 proposal registry는 어떤 입력과 분석 조건을 기록했는가?

- 소유 표기: COMMON / HTT / OBSSTAT
- 입력: Planck PR3 harmonic products/maps/masks; DESI raw catalogs; CF4 query products; proposal registry
- 출력·등록 결과: D0/D1/blocked readiness labels; E1-E8 proposed artifact requirements; blocked-claim 목록
- 실행 정보: manual REV-R078 registry from external research program inputs (proposal registry)
- 상태와 한계: 과거 인벤토리의 D0/D1/blocked 표기다. 현재 보유 현황은 이 카탈로그의 filesystem/asset 조회와 대조해야 하며, 과거 결손을 현재 결손으로 단정하지 않는다. 자료 존재와 statistical admission도 구분한다.
- 후속 확인: E1 finite-mock calibration, E2 bulk-flow bookkeeping, E5 CF4 PPC/heldout validation, E6 matched randoms/covariance/nulls, E7 mask-noise/atlas calibration
- 원문: [docs/generated/observational_data_inventory.json](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/generated/observational_data_inventory.json), [docs/generated/research_program_experiment_registry.yaml](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/generated/research_program_experiment_registry.yaml)

관련 코드·기록 조회:

```bash
python3 -B scripts/project_catalog.py query --ref baseline --q "관측" --limit 15
```
