# HTT 관측논문 6트랙 출판 중심 DAG

2026-10-15 KST. 기준 commit 398dc461c849235581260d3c6d510599350abd59.
이 디렉터리는 기존의 245개 canonical PR backlog나 PR533/RB/SF 계획을 덮어쓰지 않는 **publication programme overlay**다. 원본 미커밋 htt_base 작업은 읽기만 했으며 변경하지 않았다.

## 읽는 순서

1. [DEVELOPMENT_DAG_KO.md](DEVELOPMENT_DAG_KO.md): 여섯 연구주제의 우선순위, 논문별 핵심 claim·자료·그림·선행연구·DAG의 의미.
2. [SCIENTIFIC_SCOPE_KO.md](SCIENTIFIC_SCOPE_KO.md): x,F,Pi,Q,G_F의 개별 정의역 및 자료·물리적 판정 계약, Planck low-ell, H(z,n), boost/tilt, Bianchi, kinematic estimates의 식·한계.
3. [PUBLICATION_DAG.json](PUBLICATION_DAG.json): authoritative 6-paper/42-node 실행형 DAG. 노드 의존성, 실제 blocker, 목표 입력/출력, acceptance 및 제출 gate 포함.
4. [READY_QUEUE.json](READY_QUEUE.json): 위 JSON으로 재생성한 deterministic snapshot. 이 파일은 자동 스케줄러나 시행/완료 영수증이 아니다.
5. [SOURCE_CROSSWALK_AT_DESIGN.json](SOURCE_CROSSWALK_AT_DESIGN.json): 기존 Git commit에 들어 있는 연구·관측 결과 및 원본 미커밋 파일을 분리해 실제 SHA256로 읽고 보존한 9개 소스 경로.
6. [NOVELTY_MATRIX.md](NOVELTY_MATRIX.md): 주요 원전 및 경쟁 분석의 예비 comparator. 진짜 신규성 입증(X02)은 여전히 미완료.
7. [docs/plans/2026-10-15-htt-observational-six-papers.md](../../plans/2026-10-15-htt-observational-six-papers.md): 코드·논문작성 실행 계획.

각 논문 트랙은 원래 동기를 독립적으로 보존한다.

| ID | 관측논문 주제 | 우선순위 | 현재 상태 |
|---|---|---:|---|
| P1 | Signed defect 및 x,F,Pi,Q,G_F 통계·부분식별 | 3 | 데이터법칙/physical anchor 미완 |
| P2 | Planck low-ell tensor morphology와 anomaly 재평가 | 1 | qualified null 미완 |
| P3 | CF4 redshift- and direction-dependent effective Hubble | 2 | selection/shared covariance 미완 |
| P4 | Local observer boost vs global material tilt 식별성 | 4 | history response 미완 |
| P5 | Bianchi mode/family observational identification | 6 | physical all-m T/E/B atlas 미완 |
| P6 | Beyond-FLRW sigma_ab,omega_a,A_a,beta_a 실제 관측 | 5 | optical/nonradial response 미완 |

논문의 게재 가능성은 속도·우선순위와 달리 원본 source/관측 법칙·재현 결과·통계 교정·동종연구 비교로만 판정한다. 현재 6개 모두 NOT_READY_TO_SUBMIT다. 유의한 deviation이 나오지 않는 음성결과도 엄밀하고 새로운 관측 분석이면 출판 후보로 남긴다.

## CLI

Repo root에서:

    python3 scripts/htt_publication_dag.py --validate
    python3 scripts/htt_publication_dag.py --ready
    python3 scripts/htt_publication_dag.py --blocked
    python3 scripts/htt_publication_dag.py --paper P3
    python3 scripts/htt_publication_dag.py --task H01
    python3 scripts/htt_publication_dag.py --export

--ready는 기존 결과만을 근거로 실행 가능한 첫 단위 9개를 돌려준다. --task는 해당 논문의 최종 목표, 선행 결과, 테스트·출력 및 physical-claim 한계를 묶은 하나의 실행 패킷을 인쇄한다. --export는 READY_QUEUE.json을 만들 뿐 연구·실행 상태를 변경하거나 예약 작업을 생성하지 않는다. --task로 작업을 선택해도 실제 source·코드 수정과 테스트는 별도 명시적으로 수행해야 한다.

초기 가장 유용한 실천 순서는 병렬 준비 가능한 P2/L01, P3/H01, P1/S01을 시작하고 X01/X02/X03에서 실제 source ownership과 비교논문·pre/post-hoc status를 동시에 확인하는 것이다. P4/V01, P6/K01, P5/B01은 각기 다른 physics scope의 첫 식별성/atlas 점검이다. 없음/불가능을 단정하지 말고 정확한 source-needed response로 연결한다.

원래 개발 source:
/home/cosmosapjw/Dropbox/bianchi/htt_base @ 13d8d85f, 57개 미커밋 경로, read-only preservation.
이번 독립 트리:
/home/cosmosapjw/worktrees/htt-six-paper-publication-dag-20261015.
Native subagent 실행 NOT_RUN (host dispatch 없음), 외부 local Codex 사용 없음.

이 파일/PR 게시는 학술지 제출이나 main merge를 의미하지 않는다.


## 2026-10-15 current research execution

The initial 9-node ready list above was the **design-time** state at
commit 58bb3fa0. The actual continuation has now executed the
mathematical S01 and source-conditioned H01/H03 deliverables with tests,
not physical cosmological measurements. L01 actual temperature high-mode
response and K01 radial source-operator rank have useful **partial**
evidence but remain pending in full Planck beam/polarization and full
curved-spacetime kinematic physics respectively. Current READY_QUEUE.json
is regenerated from the updated DAG and returns 8 ready tasks.

- THEORY_CODING_LOOP_20261015_KO.md: full equations, actual source numbers,
  scope boundaries, extra rec_bianchi/rei_bianchi local source reuse.
- results/H01_actual_cf4_v1: CF4 35,970 group redshift windows.
- results/L01_actual_planck_v1: Planck temperature lmax5–12 same-sky response.
- results/S01_finite_mathematical_oracle_v1: synthetic signed x/F/Pi/Q/G_F checks.
- results/K01_actual_cf4_radial_oracle_v1: real CF4 sky angular rank/omega nullspace
  of a model jet, not a physical measurement.
- REPLAY_VALIDATION.json: identical scientific outcomes of the H01/L01 replays.


## 2026-10-15 next results: P3 H02, P2 raw spin2, P1 S02

The multi-lane source-conditioned continuation is in
PUBLICATION_LOOP_NEXT_20261015_KO.md. It directly reprocessed 35,970 real
CF4 groups, the 8 actual Planck same-sky polarization coefficient
products, and one original 2GB Planck SMICA_FULL native Q/U FITS.
Source result artifacts are in results/H02_cf4_method_calibration_v2,
results/L01_planck_spin2_pol_v1,
results/L01_raw_SMICA_spin2_v1 and
results/S02_real_planck_typed_partial_v1.
H02 v1 is a superseded numerical intermediate; the stable
rank-one covariance calculation is v2. No physical H(z) detection,
primordial B significance, or signed x posterior was established.
H02 remains external-input blocked, L01 and S02 remain pending.


## FFP10 native polarized cohort, 2026-10-15

New scope-specific evidence is in FFP10_POLAR_SOURCE_LOOP_KO.md and
results/L01_FFP10_QU_12pair_hashed/. This is a real 12 CMB + 12 noise
full-source-hashed Q/U pilot on the same 30,021 Planck polarization
mask pixels, not 999/300 calibrated Planck null, nor an observation
of cosmological anisotropy. Raw FFP10 POLCCONV/COORDSYS are absent.
The L01 publication task therefore remains PENDING with partial
evidence, and L03 physical simulation adequacy remains input-blocked.

## 2026-10-15 P3 source-matched FLRW correction

P3_FLRW_METHOD_DECOMPOSITION_20261015_KO.md and results/H02_flrw_method_decomposition_v2/ quantify the true flat-LCDM luminosity-distance redshift effect already present in c z/dL, separate actual CF4 source method composition and within-method changes, and compare hypothetical calibration box sensitivities. This corrects the physical reading of older H01 apparent depth trends without replacing original data. H02 remains pending its empirical selection/peculiar velocity covariance law.

## Legacy theory × modern STF × real Planck/CF4 integration (2026-10-15)

A new source-controlled integration bundle lives in
[legacy_modern_obs_integration_20261015](legacy_modern_obs_integration_20261015/),
with its principal Korean report
[INTEGRATED_THEORY_CODING_OBSERVATIONS_KO.md](legacy_modern_obs_integration_20261015/INTEGRATED_THEORY_CODING_OBSERVATIONS_KO.md).
It preserves SHA-256-identical original legacy `ch02/ch03/ch05` TeX and
two distinct historical code lineages, reuses actual Planck PR3
nine same-sky processing maps and FFP10 999 CMB/300 noise, and merges
independent actual 35,970-group CF4 flat-LCDM/method-composition
research. The legacy `Teff` exact fourth moment was extended
from `l=2` to `l=2+3` and its power-dominated vs amplitude-normalized
shape components were measured on real source-conditioned data.
Archived vorticity-MES and the current geodesic MES coefficients
are demonstrably non-identical; do not silently merge their bounds.

These are partial scientific evidence for L02/S02/H02. All three
physical-likelihood/matched-null paper gates remain PENDING;
no journal submission or completed detection is implied.


## 2026-10-15 fixed-C2-C3 phase-conditioned P2 morphology

P2 L02 gained one fully executed and independently replayed,
retrospective source-conditioned mathematical result, **not** physical
Planck anomaly calibration. The original legacy exact Teff invariant
is evaluated via modern real STF temperature harmonics from one
Planck SMICA_FULL physical sky and 999 source-registered FFP10
CMB-only simulations. The 16,384 independent ideal Gaussian phase
draws condition on the observed C2 and C3; the 999 FFP source
harmonic directions are independently rescaled to the same two
observed per-ell norms. The output separates power from normalized
angular morphology and distinguishes the ideal full-sky Gaussian
conditional theory from actual masked Planck source processing.

- Scientific report: legacy_modern_obs_integration_20261015/PHASE_CONDITIONED_MORPHOLOGY_KO.md
- Actual scientific JSON and plot: legacy_modern_obs_integration_20261015/results/planck_fixed_C2C3_phase_v1
- Numerical replay and exact file identity: legacy_modern_obs_integration_20261015/PHASE_NULL_REPLAY_RECEIPT.json
- Six-paper historical/statistical selection history: CLAIM_SELECTION_LEDGER.json.
  This deliberately does NOT create a new prospective confirmatory
  registration and never upgrades prior historical p=.039.
- New evidence-based whole-DAG progress: DAG_PROGRESS_20261015_phase_null.json.
  Re-run python3 scripts/htt_publication_progress.py for current progress.

X03 historical selection documentation is completed_scoped. L02
remains PENDING with partial P2 evidence until the physical source
beam/foreground/selection and statistical null requirements close.
Publication readiness remains 0/6.


## P4 finite observer/radiation/matter Lorentz frames, 2026-10-15

The next physical-scientific research unit implements exact finite local
Lorentz boosts for the observer O, matter M and radiation R with explicit
velocity-frame conventions (beta_AB is A as seen in B). Legacy exact
Teff fourth moment of an isotropic radiation monopole under a local
observer boost was derived and verified with Wolfram and source quadrature.
The finite source-injection path uses the SAME actual Planck PR3
temperature low ell sky products and selected native 26,846 temperature
pixels, plus a separate *counterfactual* CF4 source-window response after
proper Galactic to ICRS transformation. The source CF4 CMB-frame
redshift has already had observer motion corrected and must NEVER receive
a second physical subtraction.

Report: P4_FINITE_BOOST_FRAME_LOOP_KO.md
Canonical: results/V01_planck_cf4_finite_boost_v3/result.json
Reproducibility: P4_V01_REPLAY_RECEIPT.json
Current progress: DAG_PROGRESS_20261015_finite_boost.json
Code: htt/obsstat/finite_boost_observer_frame.py and
scripts/run_htt_real_planck_finite_observer_boost.py.

V01 is completed_scoped for event-local finite Lorentz and observer
radiation/matter source frame typing, NOT global tilt physical
identification. V02 has L01 source transfer prerequisite unfulfilled,
V03 still requires independent global matter/radiation source history,
P4/P1-P6 paper submission gates remain unready. Current total
9/42 (21.4%) scoped nodes complete, six ready, seven externally missing,
20 waiting; submission 0/6.

## 2026-10-15 P2 full FFP10 high-l nuisance Schur source run

P2 L01 now includes a genuine actual selected-pixel source-matched
temperature harmonic fit with ell0..5,8,10,12, one real Planck
SMICA observed map, 999 FFP10 CMB-only source realizations, 300
noise-only realizations, and first300 exactly same-ID paired signal+noise.
The finite masked block identity restricted-minus-joint=K*high
and an independent profiled Schur solve are verified. Legacy F4 l2/l3
s3,k4 morphology is propagated; actual SMICA s3 moves from -0.101525
to +0.412741 across ellmax5 to ellmax12, with substantial simulation
source-conditionally corresponding variability. This is a model-scope
effect and NOT a calibrated Planck anomaly detection.

Files: P2_SCHUR_HIGH_ELL_FFP10_FULL_KO.md, primary
results/L01_schur_999cmb_300noise_v2/result.json and compressed NPZ,
htt/obsstat/masked_schur_highl_temperature.py and its unit/source tests.
The 5 arcmin beam x NSIDE64 pixel transfer is a DECLARED NOMINAL
isotropic scenario and cannot represent the full Planck 2018 SMICA
effective beam/filter or source foreground/systematic covariance.
L01 remains pending and V02 waits on L01; all 6 paper submission
gates remain unpassed. Completed-scoped DAG nodes remain 9/42.

## P6 K01: 2026-10-15 exact one-event 1+3 photon-energy and CF4 sky study

P6 K01 is completed_scoped for mathematical/physical **local one-event**
null-ray redshift and one-congruence H, acceleration, STF shear, vorticity
radial cancellation/units/source-frame contract. The physical observable
rate -dln(E)/dt_u=H-A dot LOOK+sigma:LOOK LOOK was derived, CAS-verified,
implemented and tested under metric -+++ and epsilon123=+1.

Real source geometry: 35,970 grouped CF4 J2000 LOOK directions and
9 same-sky Planck processing l2 tensor alternatives transformed to
the Galactic harmonic chart. CF4 source angular H+A3+STF5 rank9,
omega3 null rank0; sky selection significantly changes across depth
windows. All synthetic injected one-event H/A/sigma/omega numeric
amplitudes are NOT cosmological inference. No source optical-history,
redshift selection/velocity physical CF4 likelihood or nonradial
vorticity, acceleration or tilt posterior is supplied.

See P6_K01_COVARIANT_OPTICAL_AND_CF4_KO.md,
K01_COVARIANT_OPTICAL_REPLAY_RECEIPT.json,
results/K01_covariant_optical_CF4_Planck_v1/ and
DAG_PROGRESS_20261015_k01_optical.json.
K02 is next READY P6 work item; K03 is externally blocked.
Total 10/42 completed_scoped, 6 READY, 7 externally blocked, 19
dependency-waiting, 0/6 manuscript submission gates.

## 2026-10-15 P6 K02: actual CF4 apparent STF vs unknown physical optical transfer

This cycle joins the original legacy beyond-FLRW x,F,Pi,Q,G_F objectives
with the one-congruence covariant photon energy law verified in K01 and
the independently studied 35,970 CF4 group nuisance-profiled apparent
STF. Under four explicit *not-physical* redshift response kernels,
conditional 5D STF estimates are genuinely source-fitted (real
distance modulus, redshift, J2000 directions and four method families).
The original g=1 source coefficients reproduce the earlier CF4 Schur
result. Unknown physical radial-transfer amplitude lambda makes fitted
amplitude and conditional covariance change as 1/lambda and 1/lambda².
Allowing hypothetical unconstrained method-specific angular STF
calibration eliminates the identifiable global STF five directions
exactly, with source projection residual ~3e-16. This is a constructive
counterexample and NOT measured actual CF4 direction-dependent
calibration or physical GR shear detection.

K02 is now completed_scoped with mathematical/working-model source
evidence. K03 real nonradial vorticity/A/beta and K04 actual physical
survey/source likelihood remain input-blocked. Overall DAG is
11/42 (26.2%) scoped tasks, 5 ready, 7 external and 19 waiting,
with 0/6 scientific manuscripts ready to submit.

Report: P6_K02_CF4_TRANSFER_IDENTIFICATION_KO.md
Actual numerical evidence: results/K02_cf4_transfer_uncertain_v1/
Original/independent replay: K02_CF4_TRANSFER_REPLAY_RECEIPT.json
Progress snapshot: DAG_PROGRESS_20261015_k02_transfer.json

## 2026-10-15 P1 S02 full FFP10 empirical conditional functional pushforward

P1 S02 now has actual masked-source FFP10 999 unique CMB simulation
IDs (and 300 original same-ID signal+noise), not fake independent
Planck observations. Under hypothetical Copernican C1/C2
geodesic and eps1=0, sector ceilings give source-specific boxes
Q in [-Uomega/Usigma,1] ONLY if flat+untilted and independent
box completions are assumed. Strict Pi(t) endpoint envelopes
were computed on the original 999 empirical source weights, with
no posterior p or processing map pseudo-replication. The original
typed HTT functional engine preserves physical missing mass 100%
for signed x, Q, F, and no genuine depth G_F is identifiable.
Scope is mathematical/source-conditional, not a physical
cosmological shear or Bianchi observational detection.

Parallel external physics preparation: seven external-input-blocked
nodes have 21 real checked candidate source artifacts, with zero
physical source contracts newly qualified. K03 additionally has
a hypothetical Euclidean tangential proper-motion 5+3 design
recovery on the actual CF4 35970 SKY DIRECTIONS, but NO
observed proper motions or full 1+3 transfer. Seven external
DAG states remain unchanged.

Research report: P1_S02_FFP999_AND_EXTERNAL_READINESS_KO.md
Actual source science: results/S02_ffp999_empirical_partial_v1/
Independent mathematical-source replay and evidence receipt:
S02_AND_EXTERNAL_PREP_REPLAY_RECEIPT.json
External seven-node contracts: results/EXTERNAL_BLOCKED_PREFLIGHT_20261015_v2/
K03 preflight: results/K03_CF4_NONRADIAL_PREP_v1/
Current complete progress: DAG_PROGRESS_20261015_s02_ffp999.json,
12/42 scoped scientific tasks, 4 ready, 7 externally blocked,
19 dependencies awaiting, 0/6 manuscripts ready.

## 2026-10-15 X01 tensorized source identity and observational irrep anchor

This loop deliberately prioritizes later PR254/255/256/257/258/262/264
typefree tensor/response/orbit methods over the original scalar
x_C, Q, F, Pi, G_F formulation. The tensor source statistical objects are
STF2 rank2 (5 real Planck T modes) and STF3 rank3 (7 real modes).
With 999 FFP10 registered signal realizations, masked source
empirical covariance bodies and actual one-sky source irrep tensors
were measured. Q_anchor is a descriptive covariance gauge;
F_phi a signed directional support utilization; Pi_phi a finite
source empirical exceedance surface; and paired ellmax5/12
G_F-like paths are MASK/FIT source functions, NOT physical
redshift-depth orbit. Physical sigma, omega, A, beta remain
typed MISSING with retained undefined mass 1.

Six-paper X01 now has a verified SOURCE_BINDINGS.json with
11 SHA-bound source classes, 9 overlap edges and 7 original
later-PR commit identities. Planck 9 temperature products are
one sky, and CF4 35970 vs 24 SN subset correlation remains
unqualified. The seven external physics tasks each have a new
tensor-space source contract, but none gained qualified external
physics input. X01 completed_scoped; P1 S03 now READY.
13/42 scoped nodes complete (30.95%); 4 ready, 7 external,
18 dependencies waiting; 0/6 manuscripts ready.

Report: TENSOR_X01_LEGACY_MODERN_OBSERVATIONS_KO.md.
Tensor data: results/X01_tensorized_stf_planck_ffp999_v2/
Source graph and blockers: results/X01_tensorized_source_bindings_v3/
Scientific replay: X01_TENSOR_SOURCE_REPLAY_RECEIPT.json.
Current DAG: DAG_PROGRESS_20261015_tensor_X01.json.
