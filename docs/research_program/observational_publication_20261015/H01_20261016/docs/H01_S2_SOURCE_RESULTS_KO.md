# Six-paper P3/H01 실제 CF4 source-window 연구 결과

2026-10-16 KST. Authority: `research/htt-observation-publication-dag-20261015@58bb3fa00093e36b5915c8ba87f03d7b14568bd8`, six papers and 42 research nodes. This scoped result changes only the P3 H01 methodology state, not the P3 submission gate or the 245-PR canonical backlog.

## 실제 CF4 35,970 그룹, 원본 locked

Loop6 source NPZ SHA-256 `86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c`; published group redshifts `z_CMB`, shifted `DMzp`, reported modulus errors, unit ICRS J2000 directions and method-family memberships. This is not the released selection and shared-method covariance. Source module `src/hubble_window.py` and create-only runner `src/run_h01_published.py` verify exactly this SHA.

Estimator: `d_i=10^((DMzp_i-25)/5) Mpc`, `u_i=c z_i`, `H_W=sum_i(w_i d_i u_i)/sum_i(w_i d_i²)` in km/s/Mpc. Weight: exp[-(z_i-z_c)²/(2·0.012²)]·(1+α n_{iz})/σ_i², with α=0 or 0.6 and **explicitly assumed working** σ_i²=250²+[70(ln10/5)d_i e_{DM,i}]² (km/s)². Physical H(z,n), peculiar-flow likelihood, redshift errors and survey selection are **not** calibrated.

| z center | H_W with α=0 | H_W with α=0.6 | FP denominator share α=0 | effective distance [Mpc] | top dipole/bulk subspace cosine |
|---|---:|---:|---:|---:|---:|
| 0.025 | 74.629348 | 74.315905 | 0.3037 | 97.50 | 0.92687 |
| 0.040 | 74.343818 | 74.040630 | 0.5349 | 141.19 | 0.93167 |
| 0.060 | 72.516333 | 72.382225 | 0.8024 | 236.50 | 0.95232 |
| 0.080 | 70.810223 | 70.828381 | 0.9019 | 322.30 | 0.97350 |

Eight windows of ONE group sample, not independent cosmological measurements. Changing source-method mixture and sky selection precludes interpreting the radial trend as the physical expansion history. The working diagonal-model correlations are corr(z=.025,.04)=.713032, corr(.04,.06)=.472458, corr(.06,.08)=.531873; the two angular weights at the same z center correlate .9700–.9904.

Exact source-template response: `u_i=H0d_i+d_i D·n_i+B·n_i+d_i n_i^T Q n_i` with STF Q gives `H_W=H0+D·m_W+B·b_W+Q:Q_W`. Antipodal full sky has m,b,Q_W zero; angular weighting breaks cancellation. At one fixed d, D and B angular columns are identical up to constant, so separate physical response is necessary. Under fixed weights only, a global modulus shift Δμ rescales H_W by `10^(-Δμ/5)`.

## Verification, claim and six-paper research DAG

11 scoped sandbox pytest tests PASS including real-source hash, exact injected monopole/dipole/bulk/STF response, antipodal zero, angular-window leakage, duplicate-source window covariance, one-depth degeneracy, strict invalid-input gate, zero-point effect. The full richer local runner S2 JSON `0e7f10007de1b7fa2e5db7c0329437d9feedba96e16be6aa30182603dc1e1a06` replayed byte-exactly with the source. GitHub's create-only compact runner replayed ALL eight H_W and all covariance entries **exactly (max difference 0)** relative to the source richer result. Under a deliberately diagonal working sigma law, 3000 manufactured Gaussian draws give Frobenius covariance discrepancy .03460018; not survey coverage.

**H01 pending → completed_scoped** only as a typed **SOURCE_CONDITIONED_WORKING_WINDOW_ESTIMATOR_ONLY**. H03 structurally becomes READY, but H02 remains blocked by full CF4 source selection/calibration covariance and velocity likelihood, and X01/X02/X03 common checks remain pending. Other 41 node states, six paper submit gates and all unrelated PRs preserve their prior authority.

**Novelty threat to P3:** Kalbouneh, Marinoni & Bel 2023 PRD107 023507 doi:10.1103/PhysRevD.107.023507 and Kalbouneh et al 2026 JCAP03(2026)084 doi:10.1088/1475-7516/2026/03/084 **already** construct expansion fluctuation multipoles and measure redshift-dependent CF4/Pantheon+ trends. They are direct estimand competitors absent from the six-paper baseline novelty matrix. Boubel 2025 JCAP03 066, Stiskalek/Desmond/Lavaux 2026 MNRAS546 (staf2048), and Salzano et al 2026 PDU 102382 add competing velocity/anisotropy treatments. X02/H05 must compare actual model equations, covariance and nulls; methodological restatement of H_W **has no admitted novelty**.

Physical H, H0 discrepancy, covariant shear/ω/A/tilt, optical transport and any physical Bianchi result remain `HOLD`. Independent native reviewer NOT_RUN, no main merge, no journal submission.