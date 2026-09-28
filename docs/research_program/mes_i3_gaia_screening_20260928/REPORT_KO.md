# HTT/MES I3 — Gaia-CRF3 방향 drift 입력의 동일 상태 적합성 판정

2026-09-28 KST. `HANDOFF_ROOT=/home/cosmosapjw/Dropbox/bianchi/htt_base`. Owner: local Host Codex. Scope: external I3 exploratory theory/source screening. Claim tier: C0, `DIAGNOSTIC_ONLY`. Transfer source: none. Generation: source reading, direct derivation, one light `WolframLanguageEvaluator` call, author self-review. Caveats: no catalog rows, empirical likelihood, independent I3 reviewer, repository CAS4 or production admission. 연구 질문은 **tensor morphology**다. Norm만의 I2 `H,ρ` 경로는 별개로 유지한다. 이 문서는 새로운 관측 상한, 실측 shear, Bianchi family 판정 또는 일반 finite-tilt Einstein–matter 검증이 아니다. 결정은 `HOLD_INPUT_INCOMPLETE`; 후보 입력은 독립 astrometry carrier이지만 아직 동일 상태의 `Z` 입력으로 채택할 수 없다.

## 1. 연결한 선행 상태와 현재 실행

- I1 `TARGET_RESPONSE_THEORY_KO.md` SHA-256 `666db799914911ba5824d6dd46e4ae01296106e67c1c4c7a433d846a2786d161`: `Z=σ−STF(p aᵀ)`, `p=β`, residual-known inverse 및 정적 brightness의 한계.
- I2 `PHYSICAL_RESIDUAL_AND_IDENTIFIED_SET_KO.md` SHA-256 `4976e5785a66616180ed73ccd5e7e3065a5e7bfb6315122649a2dffd025e1d5f`: radiation-only, Λ=0, geodesic normal Bianchi I의 `p=a=0`에서는 `Z=σ`; 동일 순간의 등방 sky만으로 절대 shear 유한 상한 없음. 독립 판정은 `DEFENDED_CONDITIONAL`이며 실측/일반 finite tilt에는 적용되지 않는다.
- R3 `MES_R3_OBSERVABLE_JET_AND_SOURCE_BOUNDS_20260927_KO.md` SHA-256 `31b55cfaf7e3f0c40907ee4386a5fc424cd7066c1d989d55019de41a956227aa`: nearby emitter/observer가 하나의 smooth congruence에 속할 때의 국소 position-drift vertex 식. R3 별도 raw/독립 판정의 확보 공백은 종전 상태다.
- I1에 포함된 GPT-6 연구 하네스 v4.0.0의 `START_HERE`, `PROJECT_INSTRUCTIONS`, `docs/MODEL_ROUTING`, integrated run 및 완료된 state를 읽고 현재 gap만 다뤘다. 이 세션의 상위 호스트 정보는 GPT-6 계열만 제공한다. Astra 변형/effort의 실제 메타데이터는 도구로 확인되지 않아 `MODEL_VARIANT_UNVERIFIED`로 둔다. `gpt6-astra` 하네스 파일을 연구 절차 참조로 사용한 것이 모델 신원 인증은 아니다. 실제 사용 가능한 shell, web, lazy Wolfram evaluator를 확인했고 Wolfram exact symbolic 한 호출만 수행했다.
- 15:05–15:11 KST 원격 `refs/heads/main`을 `git ls-remote`로 재조회: `cc162c804eecb3c588efc6edadbe057a8a67301f`; 로컬 `HEAD` 동일, tree `f14a536e7934d99bbe67489d1b81e5da0079cb09`. 기존 tracked 7개 수정과 untracked 자료는 유지했다.

## 2. 실제로 연 대표 입력

**Gaia-CRF3의 QSO-like source astrometry**를 screening 입력으로 선택했다. [Gaia DR3 `gaia_source` 공식 field schema](https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_main_source_catalogue/ssec_dm_gaia_source.html)에서 `source_id`, `ref_epoch`, `ra`, `dec`, `pmra`, `pmdec`, `pmra_error`, `pmdec_error`, `pmra_pmdec_corr`, `astrometric_params_solved`를 확인했다. 위치는 ICRS barycentric 각도, proper motion은 `mas yr⁻¹`이며 `pmra=μ_α cosδ`다. 같은 공식 표의 개별 covariance 요소는 제공된다. [Gaia-CRF3 원 논문 §2, §5, Appendix C/E](https://doi.org/10.1051/0004-6361/202243483)은 `gaiaedr3.agn_cross_id`와 `gaiaedr3.gaia_source`의 `source_id` join, `frame_rotator_source`의 spin 사용 flag, 외부 QSO 목록과 proper-motion/parallax 필터를 제시한다. DR3 기본 astrometry는 EDR3와 같다.

| 필요한 항목 | 실제 입력에서 확인한 것 | I3 판정 |
|---|---|---|
| 위치/방향/epoch | `ra`, `dec`, `ref_epoch`; ICRS, TCB epoch | 제공 |
| 각도 drift/개별 오차 | `pmra`, `pmdec`, 오차 2개와 `pmra_pmdec_corr` | 제공; 개별 측정 공분산까지만 |
| 표본 선택 | QSO 외부 목록 교차와 astrometric filtering, frame-spin 사용 flag | 방법 제공; sky/magnitude/selection response가 필요 |
| 독립 거리와 local Taylor 범위 | 이 astrometry 표에는 같은 congruence의 물리 거리 및 `L_κ`가 없음 | 결손 |
| source/observer 운동 | 동일 smooth cosmic congruence 소속, source transverse-velocity 분포, observer peculiar acceleration | 결손 |
| Fermi frame 대 ICRS | frame spin과 보정의 독립 공동 오차법칙 | 결손; QSO proper motions 자체가 frame 정의에 사용됨 |
| low-ell 공동 공분산 | source 간 상관, large-scale systematics, 마스크/선택 coupling | 이 field schema만으로 닫히지 않음 |

원 논문은 Gaia-CRF3 선택이 17개 외부 목록과 2단 astrometric filtering에 의존하고, 넓은 각도 scale의 proper-motion systematics 및 QSO subset별 spin 차이를 보고한다. 이는 개별 `pmra_error`로 전천 공분산을 대체할 수 없다는 직접 근거다. Quasar는 이 local vertex의 `D→0` 실험이 아니므로 `v/D`가 작아 보인다는 이유로 remainder를 버릴 수도 없다. 적색편이 crossmatch가 가능하더라도 `z`를 모형 독립적 물리 거리나 동일 congruence의 local Taylor 제어로 바로 바꾸지 않는다. 실제 catalog row, full covariance 또는 selection likelihood는 이번 단계에서 내려받거나 적합하지 않았다.

또한 catalog proper motion은 관측 기간에 걸친 astrometric solution의 적합 계수다. 아래 순간 vertex 값을 곧바로 catalog의 `pmra/pmdec`와 동일시하려면 시간 window와 solution response를 forward model에 포함해야 한다. 그 response도 현재 확인한 field들만으로 주어지지 않는다.

## 3. 동일 상태로 가는 최소 수학 계약

서명 `(-,+,+,+)`, source 방향 단위벡터 `n`, `P_n=I−nnᵀ`, proper-time rate `s⁻¹`를 쓴다. `1 mas yr⁻¹ = π/(648000000·31557600) s⁻¹`이다. R3의 같은 smooth emitter/observer congruence와 Fermi–Walker frame에서, caustic 없는 근거리 geometric optics의 vertex 값은

`κ₀(n)=P_n σ n+ω×n`, `Hcal(n)=H−a·n+σ:nn`.

여기서 `a=A/c`. 관측 catalog와 연결할 때는 **같은 잠재 상태** `ξ=(U,frame,source worldlines,ray,distances,selection,calibration,σ,ω,a,p)`에서 다음 forward relation과 오차법칙을 함께 줘야 한다:

`μ_i^cat = T_i[κ₀(n_i^F)+δκ(D_i,n_i^F;ξ)+v_{⊥,i}^F/D_i] − Ω_frame×n_i^cat + P_{n_i^cat}b_pec^cat + ε_i`.

`n_i^F`와 `n_i^cat`는 각각 Fermi 및 catalog frame의 같은 방향이며, `T_i`는 기준 시각의 두 tangent plane 사이 orientation 변환이다. `b_pec^cat`도 catalog frame 성분이다. `Ω_frame`은 그 orientation에 이미 포함되지 않은 잔여 시간 회전으로 정의한다. 실제 catalog 적합 계수에는 이 순간식의 시간 window와 solution response를 더 적용해야 한다. 이 식은 모델 계약이며 Gaia-CRF3가 모든 항을 제공한다는 주장이 아니다. R3의 조건부 bound는 `||δκ|| ≤ L_κ D`와 `||v_⊥|| ≤ v_*`가 **같은 유효 구간**에서 따로 입증될 때 `L_κ D+v_*/D`다. 거리 좌표와 `d_A/d_L` 변환 remainder를 명시해야 하며 finite shell이면 window를 적분한다. 원 관측 자료와 여기서 유도한 summary를 독립 likelihood로 곱하지 않는다.

이상적인 전천, 완전한 frame, source/remainder 0의 수학적 경우에는 `P_nσn=∇_{S²}(nᵀσn/2)`이므로 STF shear는 gradient형 `ℓ=2`, `ω×n`은 회전형 `ℓ=1`이다. `∫_{S²}|P_nσn|²dΩ=(4π/5)||σ||_F²`, `∫(P_nσn)·(ω×n)dΩ=0`. 이번 Wolfram의 일반 실수 STF 기호검산 출력이 세 잔차 `0`임을 `WOLFRAM_LIGHT_RAW.txt`에 보존했다. 이는 R3의 이상적 rank 성질을 좁게 재확인한 것이다. 마스크·불균일 selection·systematic 공분산 아래의 통계적 직교성이나 실측 가능성은 따라오지 않는다.

조건부로, 전천 평균 `⟨·⟩`의 tangent `L²` 공간에서 `M:S↦P_n S n`을 쓰면 `M* M=I_STF/5`다. 회전형 `ℓ=1`을 분리하고 **독립적으로 정당화된** 공동 nuisance bound `||e||_{L²}≤ε`가 있다면 `S_hat=5M*y`의 허용집합은 `||S−S_hat||_F≤√5 ε`의 외접구에 들어간다. 더 정확한 집합은 `{S∈STF₂:y−MS∈E}`로, frame·source·remainder·selection을 포함한 실제 공동 `E`를 요구한다. 여기에는 검증된 `ε`나 `E`가 없으므로 수치 반지름은 출력하지 않는다. 이는 물리적 Einstein 허용집합과의 교집합도 자동으로 보장하지 않는다.

Frame spin이 자유로우면 catalog의 회전형 성분은 `ω−Ω_frame`만 정한다. 더욱이 source/remainder tangent field가 자유로우면 임의 `Δσ`에 대해 그 field를 `−P_nΔσ n`만큼 바꾸어 같은 `μ^cat`를 만들 수 있으므로 shear tensor도 이 입력만으로 식별되지 않는다. 이 nuisance freedom이 물리적으로 유계라는 근거는 현재 없다. I2 branch에서 유효한 별도 optical `σ`가 실제로 생기면 `p=a=0`에 한해 `Z=σ`; 이것이 I2의 static-radiation 결론을 관측으로 승격하는 것은 아니다. 일반 finite tilt에서는 `Z=σ−STF(p aᵀ)`이며 proper motion으로 `σ`를 안다 해도 `p,a`의 같은 상태 공동 제약 없이는 `Z` 전부가 정해지지 않는다. I1의 `p≠0`에서 `a` 자유일 때 rank-3 ambiguity/2차원 quotient를 보존한다.

## 4. 결정과 최소 추가 자료

`HOLD_INPUT_INCOMPLETE` / `DIAGNOSTIC_ONLY` / claim tier C0. Gaia-CRF3는 정적 radiation snapshot과 관측 carrier가 독립이라는 장점이 있지만, 현재 확인한 자료·방법만으로 I3의 **같은 congruence 물리 입력**을 제공하지 않는다. 유용한 numerical interval, `D/Π/G`, likelihood, Bianchi family, general finite-tilt Einstein existence, production adapter, repository CAS4는 모두 `NOT_RUN` 또는 기존 `HOLD`다. 새 I3 후보의 분리된 independent decision review는 실행되지 않았으므로 `INDEPENDENT_REVIEW_UNAVAILABLE`; 이 보고서의 검토는 author self-review다.

다음 한 단계는 **하나의 고정 nearby-source 표본**에서 (1) source와 observer의 명시된 coarse-grained congruence, 거리/적색편이와 validity window, (2) source transverse motion과 `L_κ` 또는 공동 nuisance law, (3) Fermi–ICRS frame spin·observer acceleration의 외부 calibration, (4) 원 proper-motion covariance에 더한 cross-source systematics 및 selection/mask response를 같은 latent-state 계약으로 확보하는 것이다. `Hcal`로 `a`까지 필요한 finite-tilt `Z`를 목표로 한다면 같은 표본의 calibrated distance–redshift 입력과 remainder도 추가한다. 어느 하나를 다른 식으로 역산해 독립 prior로 재투입하지 않는다. 이 최소 입력이 실제 확보되기 전에는 식별 부분공간의 *이상적* 수학 구조만 유지한다.

## 근거

- [Gaia DR3 공식 `gaia_source` schema](https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_main_source_catalogue/ssec_dm_gaia_source.html), 조회 2026-09-28.
- [Gaia Collaboration, *Gaia-CRF3*, A&A 667 A148 (2022), DOI 10.1051/0004-6361/202243483](https://doi.org/10.1051/0004-6361/202243483), §2, §5, Appendix C/E 조회 2026-09-28.
- [Heinesen & Korzyński, *Exploring the rich geometrical information in cosmic drift signals with covariant cosmography*, arXiv:2406.06167](https://arxiv.org/pdf/2406.06167), §III/IX 및 Appendix C/E 조회 2026-09-28. 구면 multipole·source/frame·근거리 유효성의 원전이며 Gaia data 적합 판정은 이 보고서의 추론이다.
