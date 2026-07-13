# Blocker dossier — what stands between the current programme and a published measurement

_Last updated: rev-r126 (2026-06-26). Single source of truth for every standing
blocker across the EGS / EGS2 / EGS3 / PR07 / PR08 / PR10 programmes._

The programme deliberately separates **proven** content (conditional theorems,
gate- and Wolfram-verified) from **measured** content (real-data runs). Every
real-data run that is not yet possible terminates with a **registered blocker
code** and emits no substitute estimate beyond a clearly labelled synthetic
stand-in. This file enumerates each code, exactly what unblocks it, what is
already built (`mechanics_ready`), and the exit gate that closes it.

There is no claim-envelope change hidden in any discharge: closing a blocker
turns a synthetic stand-in into a calibrated measurement; it never authorises a
Bianchi-family, anisotropic-geometry, or native-solver claim.

---

## Summary

| Code | Blocks | Unblock action (owner) | Mechanics ready? | State |
| --- | --- | --- | --- | --- |
| `BLOCKED_MISSING_PR4_E2E_ACCESS` | K1 global low-ℓ p-value | E2E-systematics null needs PLA-portal/NERSC-auth sims | yes | **PARTIAL (rev-r127)**: look-elsewhere global p discharged on the real map under a ΛCDM null; E2E-systematics null still open |
| `BLOCKED_MISSING_FIELD_REALIZATIONS` | K6 vorticity/curl distribution | own the full CF4 WF residual covariance (operator) for a true Hoffman–Ribak CR | yes | **PARTIAL (rev-r127; rev-r198)**: rev-r198 QUANTIFIED the WF mean-field curl suppression on the REAL 3-D CF4++ field (`cf4pp_vorticity_posterior.py`: RMS\|curl\|/RMS\|div\| = 0.009, potential flow) and built a CORRELATED-residual CR (a principled upgrade over the per-cell-independent toy). The CR vorticity distribution is residual-dominated + correlation-length-dependent (RMS\|curl\| 14–48 (km/s)/Mpc across R=7.8–30 Mpc), so a DEFINITIVE ensemble still needs the full WF residual covariance / operator |
| `BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP` | K5 bulk-flow amplitude significance (definitive, mock-calibrated) | own the full nonlinear COLA/L-PICOLA release-matched mock suite | yes | **PARTIAL — in-house physical mock DELIVERED (rev-r197)**: `scripts/cf4_mock_calibrated_significance.py` replaces the request-only CF4TF release mocks with an in-house **physical forward-mock ensemble** (linear GRF velocity field + super-sample mode + real per-object noise at the fixed CF4 geometry, `htt/obsstat/pv_forward_mocks.py`). It reproduces the analytic linear bulk-flow covariance (mock/analytic ratio ≈1) → the estimator/geometry/noise do NOT inflate the significance; the gap to the literature ~2–3σ is localised to nonlinear velocity power. Residual: the full nonlinear COLA/L-PICOLA suite (Qin+2021 CF4TF is request-only) — **downgraded, no longer the sole gate** |
| `BLOCKED_MISSING_CROSS_RECONSTRUCTION` | K5 external cross-reconstruction | ~~bind the Nusser 2026 2MRS reconstruction~~ | yes | **DISCHARGED_BY_SUBSTITUTION (rev-r197)**: the private Nusser 2026 2MRS reconstruction (no public release) is substituted by **two public 2MRS reconstructions** — the Lilow–Ganeshaiah-Veena–Nusser 2024 neural network (arXiv:2404.02278) and CORAS (Lilow–Nusser 2021, arXiv:2102.07291) — both downloaded + connected as reconstruction methods (7-method spread now); Nusser 2026 stays a provenance note |
| `BLOCKED_UPSTREAM` | PR08-006 joint posterior artifact | close K1+K5+K6 first | n/a | K5 measured (conditional coverage), K6 WF mean-field no-go, K1 partial → assemblable with explicit measured/partial/fail-closed sectors |
| `AWAITING_NATIVE_LOWELL_SOLVER` | full Bianchi family atlas / morphology | build the native low-ℓ Bianchi–Boltzmann solver | partial (B1 interim) | separate long-term project (PR10) |
| `BLOCKED_MISSING_DESI_RANDOMS` | DESI number-count dipole (Ω_tilt cross-check) | ~~download the DESI DR1 BGS random catalogues~~ | yes | **DISCHARGED (rev-r192/r193)**: randoms downloaded (`fetch.py --desi-randoms`); window-corrected overdensity dipole MEASURED D=9.49×10⁻³ on NGC+SGC (224× below the raw footprint). rev-r198 MOCK-CALIBRATED the significance (`desi_dipole_mock_significance.py`, an in-house LambdaCDM clustering mock): D is CLUSTERING-dominated (13.5σ above the shot-noise floor) and CONSISTENT with ΛCDM clustering cosmic variance (p=0.90) — not an excess. Residual: clustering/kinematic separation (BGS low-z) |
| `BLOCKED_MISSING_ACT_LENSING_SIMS` | ACT DR6 low-ℓ κ isotropy | ~~download the ACT DR6 lensing simulation ensemble~~ | yes | **DISCHARGED (rev-r192/r194)**: 400 baseline sims downloaded (`fetch.py --act-sims`); mean field subtracted; ℓ=2..10 debiased band power **p=0.35, CONSISTENT** with the isotropic ΛCDM sims (dipole ℓ=1 not measurable). Residual: a true realization-dependent N0 (RDN0) debias needs the quadratic-estimator pipeline / raw CMB maps — only the reconstructed κ a_lm are on disk, so this is blocked-on-QE (NOT runnable with κ alone; the sim-null already includes N0+N1 correctly for the isotropy test) |

**rev-r127 discharge status (real data, this session).** With local nvme + long
runs enabled, the controlling inputs for K5/K6 were found already in-repo
(`workdir/raw/cf4/CF4pp_mean_std_grids.npz` WF field; `workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz`
real CF4 catalogue) and the observed Planck maps for K1
(`workdir/raw/planck_data/COM_CMB_IQU-{smica,commander}_2048_R3.00_full.fits`).
- **K5** (`scripts/k5_cf4_release_coverage.py`): measured CF4 bulk flow |B| ≈ 341 ±
  102 km/s (consistent with the ΛCDM ~150–250 km/s expectation at this depth — high
  but not anomalous) with the error budget cosmic-variance-dominated (102 km/s) vs
  measurement (5 km/s). The CV-inclusive coverage 0.67 (vs measurement-only 0.19) is
  computed with geometry-and-error matched Gaussian bulk-flow mocks and is
  **conditional on a fixed ΛCDM σ_cv=150 km/s/comp prior** (a non-ΛCDM CV prior would
  change it; residual selection enters only through the distance-error term). The bulk
  flow is a measurement; the full release-matched mocks remain a gate (reworded rev-r134).
- **K6** (`scripts/k6_cf4_curl_posterior.py`): the real CF4++ WF velocity field is
  curl-suppressed (vorticity ≤ 0.6 % of shear at every radius) while the estimator
  recovers an injected **solid-body** rotation to machine precision (estimator
  curl-sensitivity demonstrated for that mode; the suppression is the WF prior's,
  across modes) → **WF mean-field structural no-go**, not a physical-vorticity
  detection. A true Hoffman–Ribak CR vorticity posterior remains blocked until a CR
  ensemble is owned (the present field uses independent per-cell draws, not the full
  cell–cell covariance) (reworded rev-r134).
- **K1** (`scripts/k1_global_maxscan.py`): global look-elsewhere-corrected morphology
  p on the real SMICA map = 0.097 (Commander 0.121) under an isotropic ΛCDM null.
  This discharges the *look-elsewhere correction*; the full E2E-systematics null is
  still blocked because the matched FFP10/NPIPE component-separated sim ensemble is
  served only via the PLA interactive query portal / NERSC-authenticated paths, not a
  plain-URL download (confirmed by probing PLA + IRSA + NERSC this session).
  **cobaya checked (this session) and does not unblock it:** `cobaya-install
  planck_2018_lowl.TT` installs the Blackwell-Rao **C_ℓ-level** low-ℓ TT likelihood
  (`cov.txt` 249×249, `mu.txt`, `cl2x_*.txt`), not a map/a_lm ensemble. The K1
  morphology statistics (parity/planarity/alignment) depend on a_lm phases, which a
  C_ℓ-only product cannot generate, so cobaya provides likelihood data, not sim maps.
  The only remaining route to the E2E null is a manual PLA-portal / NERSC-authenticated
  download of the FFP10 (or NPIPE) component-separated low-ℓ simulation maps — the full
  step-by-step acquisition + run procedure is `docs/research_program/K1_E2E_DOWNLOAD_GUIDE.md`
  (everything downstream of the download is already implemented and waits for the maps).

**PR08-006 joint artifact (rev-r129) ASSEMBLED.** With K5 measured (conditional
coverage), K6 a WF mean-field no-go, and K1 partial,
`scripts/pr08_006_joint_artifact.py` assembles the graded comparator on real data:
Ω_tilt **measured** (K5 bulk flow), Σ² **partial** (K1 look-elsewhere), W² and Ω_k
**fail-closed** (K6 structural no-go + no channel — not zeroed). Data rank 2 is
reported separately from prior-conditioned rank; no collapsed `x_C` scalar; no
MIO-as-odds; no scalar→family. This realises the program headline (a rank-2 graded
comparator: one measured kinematic sector Ω_tilt + one partial CMB sector Σ² + two
fail-closed sectors, with a proven two-sector no-go) on real data — the rank-2 count
is one full plus one partial, not two fully measured sectors (reworded rev-r134).

### Hygiene-pass finding (audit F2/F5): the residual contract failures are structural

The audit's remaining stale-generated-artifact contract failures are **not** fixable
by regeneration: 6 of the 7 (`cf4pp_lnb_provenance`, `code_capability` manifest,
`current_manuscript_figures` generator-check, `external_research_input_inventory`,
`semantic_firewall_fuzz`, and the `current_science_plot_payload`-fed chain) embed a
`git_commit_or_worktree_state: <HEAD>+dirty` field in the generated file itself.
Because that field references the working state at generation time, any commit
changes HEAD and immediately re-stales the file — so these contracts can only pass
in the exact uncommitted state they were generated in, never after a commit. The
durable fix is a generator refactor that drops `git_commit_or_worktree_state` from
the emitted artifacts (keeping only content-addressed `config_hash`/`input_hashes`),
mirroring the content-addressed manifests added for the EGS/discharge figures. The
7th (`manuscript_audit_repair_matrix`) reflects the manuscript PDF carrying 2 genuine
`pdf_claim_lint` findings under the current linter (the committed report is blessed at
0); it needs a manuscript-text fix or a hash-bound exemption, not a regeneration.
The one genuinely field-based failure (figure claim-lane policy) was durably fixed in
rev-r128. These items are a separate refactor PR, deliberately not churned here.

---

## 1. `BLOCKED_MISSING_PR4_E2E_ACCESS` — K1 global low-ℓ p-value

- **What it blocks.** Promoting the K1 low-ℓ morphology score from a *local*
  (single-sky) p-value to a *global* p-value calibrated against an end-to-end
  simulation ensemble. Tickets: `egs3/tickets/k1_ffp10_npipe.yaml`, `PR08-001`.
- **Why it is blocked.** The global rank requires a full E2E ensemble
  (instrument + component-separation + masking) that is not in-tree. We refuse
  to quote a global p from an internal toy null.
- **Concrete unblock.** Download the public Planck Legacy Archive products:
  - FFP10: `dx12_v3_{method}_{cmb,noise}_mc_*` — 999 CMB + 300 noise MC per
    component-separation method (Commander / NILC / SEVEM / SMICA);
  - NPIPE (PR4): ~300 A/B end-to-end realizations.
  Downgrade each to `NSIDE=16`, `FWHM≈40'`, apply the matched low-ℓ mask.
- **Mechanics ready.** `htt/obsstat/lowell_global_calibration.py`
  (`e2e_maxscan_from_summaries`) consumes per-sim summary statistics, computes
  the 6 K1 statistics, tail-scores each, runs the frozen max-scan, and returns
  the +1 global rank p-value. A synthetic stand-in is exercised in
  `egs2_experiments.json:BLOCK_K1_e2e_maxscan` (labelled, `global_p` from a
  toy null) purely to prove the pipeline runs.
- **Exit gate.** Global rank p-value + matched-pipeline config hash + ensemble
  provenance manifest (map IDs, mask, beam, NSIDE). On exit, the K1 row in
  `docs/generated/egs_results_table.json` flips `blocked -> measured`.

## 2. `BLOCKED_MISSING_FIELD_REALIZATIONS` — K6 vorticity/curl posterior

- **What it blocks.** A realization-conditioned posterior on the velocity-shear
  curl (vorticity) sector from CF4. Tickets: `egs3/tickets/cf4_wfcr.yaml`,
  `PR08-004`.
- **Why it is blocked.** The curl posterior needs an ensemble of constrained 3D
  velocity-field realizations consistent with the CF4 data; the Wiener-filter
  point estimate alone gives no posterior width.
- **Concrete unblock.** Run Hoffman–Ribak constrained realizations on the CF4
  3D Wiener-filter field (Hoffman et al. 2024, arXiv:2311.01340): draw an
  unconstrained realization, add the WF residual of (data − constraint), repeat
  for the ensemble.
- **Mechanics ready.** `htt/obsstat/constrained_realizations.py`
  (`curl_posterior`) builds the curl posterior from a CR ensemble; a toy 1D
  curl sector is exercised in `egs2_experiments.json:BLOCK_K6_hoffman_ribak`
  (labelled synthetic). The vorticity re-opening theorem (NT2-B3/EGS3-B3) that
  the posterior would test is already proven.
- **rev-r198 partial.** `scripts/cf4pp_vorticity_posterior.py` +
  `htt/obsstat/velocity_field_curl.py` QUANTIFIED the WF mean-field curl
  suppression on the REAL 3-D CF4++ field (RMS|curl|/RMS|div| = 0.009 within the
  reliable radius — potential flow, the no-go confirmed) and built a
  CORRELATED-residual CR (a GRF residual scaled to the per-cell WF std) — a
  principled upgrade over the per-cell-independent toy. The CR vorticity
  distribution is residual-dominated + correlation-length-dependent (RMS|curl|
  14–48 (km/s)/Mpc across R=7.8–30 Mpc), because the residual correlations are
  NOT fixed by (v_mean, v_std) alone. This does NOT discharge the blocker: a
  definitive CR needs the full WF residual covariance / operator.
- **Exit gate.** Realization-conditioned shear/vorticity posterior (median +
  16/84 percentiles) from the real CF4 WF/CR ensemble + provenance.

## 3. `BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP` — K5 cosmic-variance coverage

- **What it blocks.** A cosmic-variance-inclusive coverage statement for the CF4
  bulk-flow apex/depth. Tickets: `egs2/tickets/K5_release_matched_mocks.yaml`,
  `PR08-003`.
- **Why it is blocked.** Full cosmic-variance coverage requires
  selection/Malmquist/grouping-matched forward mocks (the same selection function,
  sky coverage, and distance-error model as the published CF4 group catalogue),
  which we do not own. The rev-r127 coverage is a CONDITIONAL stand-in: a fixed
  ΛCDM σ_cv=150 km/s/comp Gaussian bulk-flow prior on the real geometry + errors.
- **rev-r195 partial.** `scripts/cf4_bulkflow_lcdm_variance.py` replaced that
  hand-set prior with the real **linear estimator-matched** cosmic variance
  (mode-function window integral of a fiducial EH98 σ₈-normalised P(k), validated:
  single-group σ_v recovers the closed form to 1.2%, grids converged to 0.4%).
  The result (σ_cv≈35 km/s along **B**) is a **lower bound** — the noise-weighted
  GLS estimator aliases nonlinear small-scale velocity power linear theory omits —
  so the LambdaCDM amplitude **significance is WITHHELD** (a naive χ² reads a
  spurious ~9σ). The measurement (|B|, apex, Ω_tilt) is real; the significance is
  not. This does NOT discharge the blocker.
- **rev-r197 in-house physical mock (DELIVERED).**
  `scripts/cf4_mock_calibrated_significance.py` replaces the request-only CF4TF
  release mocks with an in-house **physical forward-mock ensemble**
  (`htt/obsstat/pv_forward_mocks.py`): a linear Gaussian-random-field
  peculiar-velocity grid (EH98 σ₈-normalised P(k), 2 h⁻¹Gpc box) + the
  super-sample (>box) uniform bulk mode + real per-object N(0, σ_tot) noise,
  sampled at the fixed CF4 group positions and run through the identical MV
  weights (250 boxes × 8 octant observers = 2000 survey-matched mocks). The mock
  bulk-flow covariance reproduces the analytic linear-theory covariance to the
  grid resolution (mock/analytic ratio ≈1), so the estimator + geometry + noise
  do NOT inflate the significance; the reduction to the literature ~2–3σ is
  localised to nonlinear velocity power beyond this linear model. This
  **discharges the "no mock at all" state** — only the full nonlinear refinement
  remains.
- **Concrete unblock (residual).** The full nonlinear COLA/L-PICOLA
  survey-matched mock suite (the Qin+2021 CF4TF suite is request-only; L-PICOLA
  is roll-your-own) to fold in nonlinear velocity power + selection mode-coupling.
- **Mechanics ready.** `htt/obsstat/pv_forward_mocks.py` (the in-house linear
  forward model) + `htt/obsstat/bulkflow_mle.py`
  (`hierarchical_coverage_experiment`) computes coverage over any supplied mock
  ensemble; the hierarchical-GLS estimator (PR08-002) is closed.
- **Exit gate.** Nonlinear COLA/L-PICOLA survey-matched mocks folded into the
  same estimator to pin the definitive significance; the in-house linear forward
  mock already calibrates the estimator and localises that residual.

## 4. `BLOCKED_UPSTREAM` — PR08-006 joint posterior artifact

- **What it blocks.** The single joint posterior artifact + legacy scalar
  pushforward that combines K1/K4/K5/K6. Ticket: `PR08-006`.
- **Why it is blocked.** It is a pure downstream join: it cannot be assembled
  until K1, K5, and K6 are themselves discharged.
- **Exit gate.** All of §1–§3 closed, then the graded-comparator joint
  pushforward (EGS3 Axis-C C3) reports the rank-2 reachable sectors (Σ², Ω_tilt)
  *with values* and the two fail-closed blind sectors (W², Ω_k) — the honest
  publishable joint result (a measured comparator **with** the proven no-go).

## 5. `AWAITING_NATIVE_LOWELL_SOLVER` — full Bianchi family atlas

- **What it blocks.** Any Bianchi-family identification / anisotropic-geometry
  detection / morphology-atlas claim. This is the hard claim ceiling.
  Ticket: `PR08/tickets/PR10-solver.yaml` (PR10-001..006), a **separate
  long-term project**, not part of this programme's deliverables.
- **Partial discharge.** EGS3-B1 (`htt/bass/transfer/shear_quadrupole_seminative.py`)
  gives an interim **semi-native** shear→low-ℓ transfer: a single shear-sourced
  mode projected through a real recombination visibility, exact-FLRW-anchored.
  It derives NT2-A1's toy response and bounds NT2-A2's tail — but it is **one
  mode**, not the family atlas, and it makes no family/geometry claim.
- **Exit gate (out of scope here).** A validated native low-ℓ Bianchi–Boltzmann
  solver + morphology atlas + covariance + matched masks + nulls + PPC/LOOCV +
  equivalence-class gates. Only then may any family-ID language be used.
- **rev-r142 (EGS3 Axis-D) — theory-g CMB joint likelihood is mechanics-ready +
  fail-closed.** The BASS-Extended joint likelihood's CMB *theory* sector — the
  mode-coupled `C_{ℓm,ℓ'm'}(g)` / `A^{LM}_{ℓℓ'}(g)` prediction for a proposed Bianchi
  `g` — needs this solver. It is FAIL-CLOSED: `joint_pv_cmb_forecast.anisotropic_cmb_covariance`
  / `anisotropic_cmb_loglike` raise `OutOfScopeError` and never fabricate a covariance;
  the drop-in point is `bass.spectrum.cl_assembly.off_diagonal_biposh`. The solver-free
  substitute is the **data-side** BipoSH SI measurement on the real SMICA map (EGS3-D3,
  `scripts/k1_biposh_smica.py`), which needs no solver. The PV sector (EGS3-D1) and the
  coupled-Fisher degeneracy break (EGS3-D2) are fully in scope now.
- **BipoSH E2E-null upgrade** is pending under `BLOCKED_MISSING_PR4_E2E_ACCESS`: the SMICA
  BipoSH global `p` is calibrated against a matched isotropic GRF null now; the FFP10/NPIPE
  E2E simulation ensemble replaces it when downloaded (same script, frozen statistic set).

---

## What is NOT blocked (already delivered)

All conditional theorems on the three axes are proven and gate/Wolfram-verified
now — see `docs/generated/egs_results_table.md` (14 proven rows: 6 symbolic,
8 gate). The framework upgrade (graded comparator) and the revisionary redesign
(PSD-cone comparator) are implemented, gated, and bit-identical. The honest,
publishable headline that needs **no** unblocking is: *a rank-2 graded comparator
(one measured kinematic sector Ω_tilt + one partial CMB sector Σ²) together with a
proven two-sector no-go and named re-opening channels.* The blockers above only
gate turning the synthetic Axis-C mechanics into real-data measurements, and
turning the conditional/partial K-row coverage into full release-matched
measurements; they do not gate the theorems.
