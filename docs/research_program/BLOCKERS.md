# Blocker dossier — what stands between the current programme and a published measurement

_Last updated: PR-120 (2026-07-15). Single source of truth for every standing
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
| `BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP` | K5 CF4 amplitude/significance/global-tilt chain | close the registered P0 lineage and own an estimator-appropriate nonlinear release-matched mock suite | yes, method substrate only | **OPEN / QUARANTINED (PR-120)**: `C1-K5-MV-F1` and `N-DATA-CF4-DOWNSTREAM` remain OPEN. Existing analytic and in-house mock mechanics do not authorize an amplitude, significance, or global-tilt result and supply no replacement value. |
| `BLOCKED_MISSING_CROSS_RECONSTRUCTION` | K5 external cross-reconstruction | ~~bind the Nusser 2026 2MRS reconstruction~~ | yes | **DISCHARGED_BY_SUBSTITUTION (rev-r197)**: the private Nusser 2026 2MRS reconstruction (no public release) is substituted by **two public 2MRS reconstructions** — the Lilow–Ganeshaiah-Veena–Nusser 2024 neural network (arXiv:2404.02278) and CORAS (Lilow–Nusser 2021, arXiv:2102.07291) — both downloaded + connected as reconstruction methods (7-method spread now); Nusser 2026 stays a provenance note |
| `BLOCKED_UPSTREAM` | PR08-006 joint artifact | close the CF4 P0 lineage plus its matched-null and authority gates | n/a | **QUARANTINED (PR-120)**: the active path is a canonical blocked-source record; the numerical historical join is legacy-reproduction-only and non-public. |
| `AWAITING_NATIVE_LOWELL_SOLVER` | full Bianchi family atlas / morphology | build the native low-ℓ Bianchi–Boltzmann solver | partial (B1 interim) | separate long-term project (PR10) |
| `BLOCKED_MISSING_DESI_RANDOMS` | DESI number-count dipole (Ω_tilt cross-check) | ~~download the DESI DR1 BGS random catalogues~~ | yes | **DISCHARGED (rev-r192/r193)**: randoms downloaded (`fetch.py --desi-randoms`); window-corrected overdensity dipole MEASURED D=9.49×10⁻³ on NGC+SGC (224× below the raw footprint). rev-r198 MOCK-CALIBRATED the significance (`desi_dipole_mock_significance.py`, an in-house LambdaCDM clustering mock): D is CLUSTERING-dominated (13.5σ above the shot-noise floor) and CONSISTENT with ΛCDM clustering cosmic variance (p=0.90) — not an excess. Residual: clustering/kinematic separation (BGS low-z) |
| `BLOCKED_MISSING_ACT_LENSING_SIMS` | ACT DR6 low-ℓ κ isotropy | ~~download the ACT DR6 lensing simulation ensemble~~ | yes | **DISCHARGED (rev-r192/r194)**: 400 baseline sims downloaded (`fetch.py --act-sims`); mean field subtracted; ℓ=2..10 debiased band power **p=0.35, CONSISTENT** with the isotropic ΛCDM sims (dipole ℓ=1 not measurable). Residual: a true realization-dependent N0 (RDN0) debias needs the quadratic-estimator pipeline / raw CMB maps — only the reconstructed κ a_lm are on disk, so this is blocked-on-QE (NOT runnable with κ alone; the sim-null already includes N0+N1 correctly for the isotropy test) |

**rev-r127 discharge status (real data, this session).** With local nvme + long
runs enabled, the controlling inputs for K5/K6 were found already in-repo
(`workdir/raw/cf4/CF4pp_mean_std_grids.npz` WF field; `workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz`
real CF4 catalogue) and the observed Planck maps for K1
(`workdir/raw/planck_data/COM_CMB_IQU-{smica,commander}_2048_R3.00_full.fits`).
- **K5**: PR-120 replaces every active amplitude, significance, coverage, and
  global-tilt consumer with the canonical CF4 P0 blocked-source record. The
  historical producer chain is preserved byte-for-byte below `legacy/cf4_p0/`
  for explicit reproduction only; `public_use` is false. Existing estimator,
  covariance, and mock code remains method substrate, not an observational
  result. No audit sensitivity or alternative number is a replacement truth.
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
  This discharges the *look-elsewhere correction*. The user confirms the PR3
  E2E download is complete; its authenticated manifest and estimator run are
  deferred to the roadmap's PR-150 gate. PR4/NPIPE data are not downloaded, and
  every PR4 download, reduction, and analysis action is explicitly skipped in
  the active long-horizon run.
  **cobaya checked (this session) and does not unblock it:** `cobaya-install
  planck_2018_lowl.TT` installs the Blackwell-Rao **C_ℓ-level** low-ℓ TT likelihood
  (`cov.txt` 249×249, `mu.txt`, `cl2x_*.txt`), not a map/a_lm ensemble. The K1
  morphology statistics (parity/planarity/alignment) depend on a_lm phases, which a
  C_ℓ-only product cannot generate, so cobaya provides likelihood data, not sim maps.
  The registered procedure remains in
  `docs/research_program/K1_E2E_DOWNLOAD_GUIDE.md`; PR-150 may consume the
  already-downloaded PR3 ensemble only. It must not infer PR4 readiness from
  that fact.

**PR08-006 joint artifact (PR-120 status: QUARANTINED).** Its historical
numerical join consumed the OPEN K5 chain. The active producer now emits only the
canonical blocked-source record; no measured Ω_tilt sector, joint rank count,
scalar pushforward, posterior, or evidence statement is authorized. Independent
K1/K6 mechanics remain separately classified, but they cannot rehabilitate the
blocked K5 input. Exact historical bytes are retained below `legacy/cf4_p0/`.

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
- **Why it is blocked.** A downloaded ensemble is not yet an authenticated,
  estimator-matched receipt. PR3 files are available but have not passed the
  PR-150 lineage/null gate; PR4 inputs are absent.
- **Concrete unblock.** For PR3 only, bind the existing E2E files to a manifest,
  map IDs, mask, beam, resolution, and exact estimator run at PR-150. PR4/NPIPE
  remains an unexecuted future branch and is not downloaded or analysed here.
- **Mechanics ready.** `htt/obsstat/lowell_global_calibration.py`
  (`e2e_maxscan_from_summaries`) consumes per-sim summary statistics, computes
  the 6 K1 statistics, tail-scores each, runs the frozen max-scan, and returns
  the +1 global rank p-value. A synthetic stand-in is exercised in
  `egs2_experiments.json:BLOCK_K1_e2e_maxscan` (labelled, `global_p` from a
  toy null) purely to prove the pipeline runs.
- **Exit gate.** Global rank p-value + matched-pipeline config hash + ensemble
  provenance manifest (map IDs, mask, beam, NSIDE). PR-150 may update the
  active v9 successor row from the authenticated PR3 ensemble; the legacy v7/v8
  tables remain byte-frozen and PR4 remains unexecuted.

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

## 3. `BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP` — K5 CF4 P0 chain

- **What it blocks.** Every active CF4 amplitude, significance, coverage,
  global-tilt, and joint-comparator interpretation rooted in
  `C1-K5-MV-F1`; it also blocks the transitive finding
  `N-DATA-CF4-DOWNSTREAM`.
- **Why it is blocked.** The hostile audit found an estimator/lineage defect and
  an inadequate observational-systematics null. Analytic covariance and
  positions-conditional linear mocks test code mechanics only; they cannot
  adjudicate the affected observational estimand or authorize a replacement.
- **PR-120 containment.** Active producers, cards, tables, figures, manuscript
  surfaces, and packages consume a content-addressed no-number block record.
  Exact historical code and artifacts are available only through explicit
  `legacy_reproduction_only` mode below `legacy/cf4_p0/`, with public use false.
- **Mechanics retained.** Linear-window integration, GLS/MV operators, and
  forward-mock infrastructure remain reusable method substrate. Their
  self-consistency or injection recovery is not validation of the quarantined
  CF4 result.
- **Exit gate.** Authenticated input and estimator lineage; an
  estimator-appropriate nonlinear selection/Malmquist/grouping/reconstruction
  mock ensemble; nuisance-orthogonal end-to-end coverage; all-consumer
  regeneration; and independent non-author adjudication. Until every gate is
  satisfied, the scientific status remains OPEN and no numerical substitute is
  allowed.

## 4. `BLOCKED_UPSTREAM` — PR08-006 joint artifact

- **What it blocks.** Any numerical multi-sector join, scalar pushforward, or
  posterior/evidence interpretation that consumes the quarantined K5 path.
- **Why it is blocked.** A downstream join cannot be more authoritative than
  its OPEN source. Independent K1/K6 diagnostics do not turn the missing K5
  authority into a measured Ω_tilt sector.
- **Current active surface.** `scripts/pr08_006_joint_artifact.py` emits the
  canonical blocked-source record. The historical artifact is exact-hash-bound,
  legacy-reproduction-only, and non-public.
- **Exit gate.** Close §3 with independent adjudication, then regenerate every
  sector and consumer from authenticated sources while retaining blind sectors
  as fail-closed rather than zero-filled.

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

## What is NOT blocked (method substrate only)

Registered symbolic identities, synthetic mechanics, and independent K1/K6
diagnostics keep their own claim tiers when they do not consume the quarantined
CF4 chain. The graded/PSD comparator remains implemented as a formal framework.
None of that authorizes a measured Ω_tilt sector, a numerical joint comparator,
posterior odds, family identification, or a native-solver claim. The active
result table must represent every affected K5 row as blocked until §3 closes.
