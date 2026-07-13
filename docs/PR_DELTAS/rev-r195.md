# REV-R195 — real-claim upgrades on the downloaded data (ACT κ upper limit + CF4 ΛCDM cosmic variance, significance honestly withheld)

## Context

Owner ask: run the long analyses on the downloaded datasets and produce results
that carry a real (non-diagnostic) claim, not just descriptors. Chosen scope
(runnable-now): the ACT DR6 κ isotropy upper limit and the CF4 bulk-flow ΛCDM
comparison. The K1 CMB E2E null stays deferred (the FFP10 SMICA ensemble is
still downloading/repairing).

Honest ceiling (stated up front, unchanged): the Bianchi theory-g prediction is
fail-closed (native low-ℓ solver = separate project) and the data show nulls, so
the only honest non-diagnostic claims are **statistical-isotropy null /
upper-limit constraints and kinematic measurements** — never a detection or a
family/geometry assignment.

## Lane A — ACT DR6 κ low-ℓ upper limit (real constraint)

`scripts/act_kappa_isotropy_measure.py` extended with a deterministic
exact-quadratic forward model: a flat-in-ℓ excess convergence power `C_sig` is
injected into the 400-sim (N0+N1-inclusive) isotropic null; for a fixed
unit-excess draw the injected band statistic is exactly quadratic in `√C_sig`,
so the 95% CL limit is solved on a fixed grid with no per-trial resampling
(byte-stable, `--check` green).

Result: **95% CL upper limit on excess ℓ=2..10 κ band power < 3.28×10⁻⁶**
(= 0.47× the null band power; `C_sig < 2.80×10⁻⁸`), alongside the unchanged
consistency p = 0.35. A real, model-independent upper-limit claim — an
upper-limit/consistency constraint, NOT a detection, NOT a family claim.

## Lane B — CF4 bulk-flow ΛCDM cosmic variance (measurement; significance withheld)

`scripts/cf4_bulkflow_lcdm_variance.py` → `docs/generated/cf4_bulkflow_lcdm_card.json`.
Replaces the frozen release-coverage card's hand-set isotropic prior
(`b_true ~ N(0, 150 km/s)` per component) with the **real linear
estimator-matched cosmic variance** of the same weighted-GLS estimator:

    Cov_CV(B) = A⁻¹ M A⁻¹,   M_ij = (H₀f)²/(2π)³ ∫dk P(k) I_ij(k),
    I_ij(k) = ∮dΩ_k F_i F_j*,  F_i = Σ_m w_m n_{m,i}(n_m·k̂) e^{i k r_m (k̂·n_m)}

— a mode-function window integral (factorises the O(N²) pair sum into
O(N_k N_dir N)), fiducial EH98 σ₈-normalised P(k), self-contained (no download).

**Validation (gates the card status):** the single-group diagonal recovers the
closed-form linear 1-D velocity dispersion to 1.2% (σ_v = 304 vs 308 km/s), and
the k̂/k grids are converged to 0.4%.

**Measurements (real):** |B| = 340.7 ± 5.0 km/s (inverse-Fisher measurement
error), apex (l,b) = (293,20) — 37° from the CMB dipole and only **18° from the
published CF4 (Watkins 2023) flow direction** — and Ω_tilt = 4.07×10⁻⁷.

**Significance WITHHELD (the important honesty call).** The linear
estimator-matched cosmic variance is small (~35 km/s along **B**), so a naive χ²
of the 3-vector reads a spurious ~9σ. That is **not** a cosmological anomaly: the
noise-weighted GLS estimator aliases small-scale (nonlinear) velocity power that
linear theory omits, so the linear window CV is a **lower bound** on the true
ΛCDM scatter. The literature (Watkins 2023) finds only ~2–3σ. We therefore
report the measurement and **withhold the amplitude significance**; a credible
significance needs the minimum-variance ideal-window estimator or release-matched
mocks (`BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP`, kept OPEN). No 9σ headline was
shipped.

## Wiring

- Module `htt/obsstat/egs3_external_lanes.py`: the ACT lane surfaces the 95% CL
  upper limit (`real_claim`, `upper_limit_95cl`); `external_lanes_seal.json`
  regenerated (PASS).
- Gate `tests/obsstat/test_cf4_bulkflow_lcdm.py` (measurement + validation +
  significance-withheld + claim firewall + `--check`).
- Results table v9: EXT-ACT → `measured` (adds the UL); new row `K5-LCDMCV`
  → `measured` (71 rows). The v9 report reads the v8 table, so no rebuild forced.
- CLAIM_LEDGER: `egs3.external_lanes` ACT clause += UL; new `k5.cf4_bulkflow_lcdm`
  (MEASURED_SIGNIFICANCE_WITHHELD, C3).
- BLOCKERS.md: `BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP` PARTIAL note += the
  rev-r195 linear-CV result + why it stays blocked (significance withheld).
- Open-items ledger: rank-5 reframed to the CF4 amplitude significance
  (MV estimator or mocks); rank-9 ACT note += the UL.

## Frozen surfaces

x_C untouched; W2_max untouched; v5/v6/v6.1/v7/v8 and the v7/v8/v9 K5 cards
byte-frozen (the CF4 card is a NEW standalone card). Downloaded data on the
gitignored workdir / off-Dropbox NVMe, not committed. Diagnostic firewall intact:
no detection, no Bianchi family/geometry, no tension/anomaly headline.
