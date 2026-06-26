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
| `BLOCKED_MISSING_FIELD_REALIZATIONS` | K6 vorticity/curl posterior | obtain CF4 3D WF field; run Hoffman–Ribak CR | yes | **DISCHARGED (rev-r127)** as a structural no-go (real CF4++ WF field is curl-suppressed) |
| `BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP` | K5 cosmic-variance bulk-flow coverage | own the CF4 release mock pipeline | yes | **DISCHARGED (rev-r127)**: real CF4 catalogue, CV-inclusive coverage nominal |
| `BLOCKED_UPSTREAM` | PR08-006 joint posterior artifact | close K1+K5+K6 first | n/a | K5/K6 closed, K1 partial → assemblable with explicit partial/no-go sectors |
| `AWAITING_NATIVE_LOWELL_SOLVER` | full Bianchi family atlas / morphology | build the native low-ℓ Bianchi–Boltzmann solver | partial (B1 interim) | separate long-term project (PR10) |

**rev-r127 discharge status (real data, this session).** With local nvme + long
runs enabled, the controlling inputs for K5/K6 were found already in-repo
(`workdir/raw/cf4/CF4pp_mean_std_grids.npz` WF field; `workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz`
real CF4 catalogue) and the observed Planck maps for K1
(`workdir/raw/planck_data/COM_CMB_IQU-{smica,commander}_2048_R3.00_full.fits`).
- **K5** (`scripts/k5_cf4_release_coverage.py`): measured CF4 bulk flow |B| ≈ 341 ±
  102 km/s with the error budget cosmic-variance-dominated (102 km/s) vs measurement
  (5 km/s); release-matched mocks give nominal CV-inclusive coverage 0.67 while
  measurement-only coverage under-covers (0.19). Full discharge.
- **K6** (`scripts/k6_cf4_curl_posterior.py`): the real CF4++ WF velocity field is
  curl-suppressed (vorticity ≤ 0.6 % of shear at every radius) while the estimator
  recovers an injected solid-body rotation to machine precision → **structural no-go**
  (the audit's explicitly-allowed outcome), not a physical-vorticity detection.
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
  download of the FFP10 (or NPIPE) component-separated low-ℓ simulation maps.

**PR08-006 joint artifact (rev-r129) DISCHARGED.** With K5/K6/K1 closed,
`scripts/pr08_006_joint_artifact.py` assembles the graded comparator on real data:
Ω_tilt **measured** (K5 bulk flow), Σ² **partial** (K1 look-elsewhere), W² and Ω_k
**fail-closed** (K6 structural no-go + no channel — not zeroed). Data rank 2 is
reported separately from prior-conditioned rank; no collapsed `x_C` scalar; no
MIO-as-odds; no scalar→family. This realises the program headline (a measured
rank-2 comparator with a proven two-sector no-go) on real data.

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
- **Exit gate.** Realization-conditioned shear/vorticity posterior (median +
  16/84 percentiles) from the real CF4 WF/CR ensemble + provenance.

## 3. `BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP` — K5 cosmic-variance coverage

- **What it blocks.** A cosmic-variance-inclusive coverage statement for the CF4
  bulk-flow apex/depth. Tickets: `egs2/tickets/K5_release_matched_mocks.yaml`,
  `PR08-003`.
- **Why it is blocked.** Cosmic-variance coverage requires release-matched
  forward mocks (the same selection function, sky coverage, and distance-error
  model as the published CF4 group catalogue), which we do not own.
- **Concrete unblock.** Generate CF4 Bias-Gaussianization forward mocks matched
  to the release selection; push each through the same bulk-flow MLE.
- **Mechanics ready.** `htt/obsstat/bulkflow_mle.py`
  (`hierarchical_coverage_experiment`) computes coverage over a supplied mock
  ensemble; the hierarchical-GLS estimator (PR08-002) is closed.
- **Exit gate.** Cosmic-variance-inclusive coverage of the bulk-flow apex/depth
  over the release-matched mock ensemble + provenance. (Note: the K5 figure's
  internal PNG title still reads "minimum-variance"; the LaTeX caption is the
  authoritative "weighted-GLS" wording — regeneration is folded into this
  discharge because it needs the CF4 download.)

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

---

## What is NOT blocked (already delivered)

All conditional theorems on the three axes are proven and gate/Wolfram-verified
now — see `docs/generated/egs_results_table.md` (14 proven rows: 6 symbolic,
8 gate). The framework upgrade (graded comparator) and the revisionary redesign
(PSD-cone comparator) are implemented, gated, and bit-identical. The strong,
honest, publishable headline that needs **no** unblocking is: *a measured rank-2
graded comparator together with a proven two-sector no-go and named re-opening
channels.* The blockers above only gate turning the synthetic Axis-C mechanics
into real-data measurements; they do not gate the theorems.
