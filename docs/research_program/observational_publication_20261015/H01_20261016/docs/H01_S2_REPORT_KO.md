# P3/H01: 실제 CF4 그룹 window 추정량과 6개 논문 DAG 연결

2026-10-16 KST. 연구 프로그램 authority: `research/htt-observation-publication-dag-20261015@58bb3fa00093e36b5915c8ba87f03d7b14568bd8`의 6 paper / 42 nodes. H01의 좁은 진척만 판정한다. 이전 PR #539의 C8 작업은 별도 history이며 여기서 묵시적으로 합치거나 L01 완료로 전이하지 않는다.

## 검증한 실제 데이터 경로

- 원본 2026-10-15 Loop6 Cosmicflows4 source-cohort NPZ, SHA-256 `86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c`, 1,235,181 bytes.
- 추출된 서로 다른 실제 그룹 35,970개, `z_CMB`, `dmzp`, `e_dmzp`, ICRS `n_J2000`, method family, group ID. **실제 자료는 관측 그룹/방향/거리모듈러스이지** 아래 `H_W` likelihood의 물리적 선택/공분산을 인증한 자료가 아니다.
- Redshift Gaussian centres `z_c`=0.025,0.04,0.06,0.08, width=0.012, angular tilt `alpha=0` 또는 `alpha=0.6` about ICRS north. 고정 `cz`/distance-modulus working law, velocity-proxy diagonal sigma=(250 km/s, propagated H_ref=70 DM error) only.

## 소스 조건부 관측 summary

| radial z centre | H_W with alpha=0 (km/s/Mpc) | H_W with alpha=.6 | FP share of H denominator | effective 1/bulk-distance (Mpc) | strongest dipole-vs-bulk principal cosine |
|---:|---:|---:|---:|---:|---:|
| 0.025 | 74.629348 | 74.315905 | 0.3037 | 97.50 | 0.92687 |
| 0.040 | 74.343818 | 74.040630 | 0.5349 | 141.19 | 0.93167 |
| 0.060 | 72.516333 | 72.382225 | 0.8024 | 236.50 | 0.95232 |
| 0.080 | 70.810223 | 70.828381 | 0.9019 | 322.30 | 0.97350 |

Do **not** treat different windows as independent galaxies, independent velocity volumes or independent expansion measurements. These are 8 transformations of the same released 35,970-group cohort. The changing FP fraction shows radial and method selection is intertwined. A source window's `H_W` radial trend is **not** a measurement of physical `H(z)` or of a Bianchi anisotropic expansion.

Conditional diagonal-velocity working-law correlation among alpha=0 neighbouring centers: `corr(0.025,0.04)=0.713032`, `corr(0.04,0.06)=0.472458`, `corr(0.06,0.08)=0.531873`. Same radial center with north modulation has correlations `0.9700..0.9904` across the two processing windows, not independent.

For a source with equal distances, the angular `d*n` response to a putative expansion dipole and `n` response to peculiar bulk are **exactly collinear**, even with full 3D sky sampling. In the actual selected source the three singular cosines are typically >0.9, but not exactly one. The geometry is therefore highly conditioned on the chosen distance/sky/method weights; it cannot by itself certify physical velocity-vs-H anisotropy discrimination.

**Synthetic injection** `H0=70`, `D=(2,-1,.5)` km/s/Mpc, `B=(240,-120,60)` km/s, `Q=diag(.5,-.25,-.25)` km/s/Mpc: fixed source windows agree with the independently contracted moment response to numerical precision. No such physical coefficients have been measured.

**Noise check:** under the declared *diagonal working* `sigma_i`, 3,000 shared-source Gaussian finite simulations verify the analytic 8×8 covariance at Frobenius relative difference `0.03460018` (synthetic MC sampling fluctuations). This is **not** observed error-bar coverage or a qualified physical null. Method offsets, cross-group peculiar velocity covariance and survey radial selection are not supplied; full `C_W` still UNKNOWN.

## Statistical and publication meaning

- `H_W=sum w*d*c z/sum w*d²` has a declared redshift/angular window and dimension-correct response. `m_W`, `b_W`, STF `Q_W` give the exact leakage of specific synthetic angular/velocity modes. `H_W` may be called a selected **apparent Hubble working-law proxy**, NOT physical `H=Theta/3` without an optical forward map.
- For one fixed weight matrix and a global DM shift `Delta_mu`, `H_W` scales as `10^(-Delta_mu/5)` (derived, Wolfram and numerical test). This is source zero-point sensitivity, not a measured calibration correction.
- Prior publications already estimate expansion-fluctuation multipoles and radial variation from CF3/CF4/Pantheon. In particular Kalbouneh, Marinoni & Bel, *Multipole expansion of the local expansion rate*, Phys Rev D 107, 023507 (2023), doi:10.1103/PhysRevD.107.023507, and Kalbouneh et al., *Anisotropic expansion rate ... covariant cosmographic interpretation*, JCAP 03(2026)084, doi:10.1088/1475-7516/2026/03/084, **directly compete with H01/H03's simpler observational estimand**. Existing original 2026-10-15 six-paper novelty matrix omitted these. Boubel (JCAP03 2025 066), Stiskalek et al. (MNRAS546 2026), and Salzano et al. (PDU 2026) also compare dipoles/flows. This computation does NOT qualify P3 novelty or X02 yet.
- X01 source overlap still pending full audit; X02 novelty source equations/nulls pending; X03 prospective threshold selection pending; H02 empirical calibration/selection law external blocked; H03 can be structurally READY after H01 but should preregister statistic/holdout before observed finding and address 2023/2026 priors.
- P1, P2, P4, P5, P6 publication paths unchanged, none submit-ready. Existing 245-card canonical PR backlog unchanged. No owner dirty checkout mutation, no original six-paper branch mutation, no main merge or manuscript submission.

## Actual numeric and symbolic validation

11 scoped pytest tests pass (full-sky antipodal cancellation, anisotropic mask leakage, exact synthetic monopole/dipole/bulk/STF response, window covariance positive-semidefinite, source hash strict gate, same-row covariance unity, radial degenerate equality, global modulus scaling). Wolfram verified STF trace identity and fixed-weight `lambda` ratio. Source runner exit 0 and output JSON exact byte replay when supplied the unchanged frozen NPZ. Sample Monte Carlo is deliberately not survey-calibrated. `native_subagent: NOT_RUN`, independent fresh context reviewer NOT_RUN.

### DAG transition

H01: `pending` → `completed_scoped` ONLY after SHA, tests, source window outputs and fixed method constraints. H03: waiting → READY. H02: still missing empirical selection+covariance and X01 (not ready). All 41 other authoritative nodes preserve their input `state` values. 6 manuscript submission flags remain `NOT_READY_TO_SUBMIT`. Exact tests of complete JSON and dependency graph required before accepting the derived queue.
