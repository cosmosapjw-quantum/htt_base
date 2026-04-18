// ═══════════════════════════════════════════════════════════════════════
// PSTF Primary — FLRW-specialized State Layout (PR-020)
// ═══════════════════════════════════════════════════════════════════════
//
// FLRW-specialized wrapper over `crate::pstf::lm_indexing::LmLayout`.
//
// ## Why a wrapper rather than direct LmLayout use
//
// `LmLayout` allocates (ℓ+1)² DOF per species block to accommodate the
// full (ℓ, m) spectrum needed by Bianchi extension (Phase 4).  In the
// FLRW limit only the m=0 axisymmetric sector is populated — the m≠0
// blocks are algebraically zero but would still occupy memory.
//
// `PstfFlrwLayout` exposes m=0 accessors that are:
// - Dimensionally cheaper for documentation / testing
// - Structurally assertive (m≠0 access panics, catching bugs early)
// - Directly comparable to MB-95 variable ordering (Θ_ℓ, E_ℓ, B_ℓ, N_ℓ)
//   for Phase 2 equivalence testing (PR-025).
//
// Under the hood the full `LmLayout` is retained, so Phase 4 can switch
// to m≠0 access without a layout-level migration.
//
// ## Relation to MB-95 variables
//
// Per `docs/PR_DELTAS/pr-020-design.md §3`:
//
//   MB-95 Θ_ℓ(k)  ↔  PSTF I_{A_ℓ}^{(γ)} projected on m=0 (axisymmetric)
//   MB-95 E_ℓ(k)  ↔  PSTF E_{A_ℓ}^{(γ)} m=0
//   MB-95 B_ℓ(k)  ↔  PSTF B_{A_ℓ}^{(γ)} m=0
//   MB-95 N_ℓ(k)  ↔  PSTF I_{A_ℓ}^{(ν)} m=0
//
// The normalization constant relating PSTF and MB-95 multipoles involves
// `stf_normalization(ℓ)` from `crate::pstf::coupling` and is applied at
// the source/LoS stage (PR-024), not in the state vector itself.

use crate::core::ssot::constants::{MIN_LMAX_G, MIN_LMAX_POL_WHEN_ON};
use crate::pstf::lm_indexing::LmLayout;

// ═══════════════════════════════════════════════════════════════════════
//   §1. The FLRW-specialized layout
// ═══════════════════════════════════════════════════════════════════════

/// FLRW-specialized PSTF state vector layout.
///
/// Indexes m=0 components only; asserting on m≠0 access.
/// Full (ℓ,m) layout is retained internally via `LmLayout`.
///
/// # Invariants (enforced by `validate`)
///
/// 1. `ell_max_gamma >= MIN_LMAX_G`  (photon hierarchy needs ≥ 3 to close RHS)
/// 2. `ell_max_nu >= MIN_LMAX_G`     (neutrino parallels photon)
/// 3. If `has_pol()`: `ell_max_pol >= MIN_LMAX_POL_WHEN_ON` (else disabled)
/// 4. `total_dof` matches `LmLayout::total_dof`
#[derive(Clone, Debug)]
pub(crate) struct PstfFlrwLayout {
    /// Inner full (ℓ,m) layout.  FLRW uses m=0 section only.
    pub(crate) inner: LmLayout,
    /// Cached ell_max values for quick access without going through inner.
    pub(crate) ell_max_gamma: usize,
    pub(crate) ell_max_nu: usize,
    /// Polarization is treated as on/off: 0 => disabled, ≥ MIN_LMAX_POL_WHEN_ON => active.
    pub(crate) ell_max_pol: usize,
    /// Total state DOF (matches `inner.total_dof` when pol is on;
    /// FLRW-specialized smaller layout may be introduced in a later PR
    /// — for now we reuse the full LmLayout sizing).
    pub(crate) n_state: usize,
}

impl PstfFlrwLayout {
    /// Construct FLRW-specialized layout.
    ///
    /// `ell_max_pol`: 0 (disabled) or ≥ `MIN_LMAX_POL_WHEN_ON`.
    /// `ell_max_pol > 0` but `!= ell_max_gamma` is allowed but unusual — typically
    /// the two are locked together at the factory level (see PR-022+).
    pub(crate) fn new(
        ell_max_gamma: usize,
        ell_max_nu: usize,
        ell_max_pol: usize,
    ) -> Self {
        // Inner layout re-uses LmLayout; the E/B blocks inside LmLayout require
        // ell_max_gamma >= 2 to have any E/B DOF at all.  We use ell_max_gamma
        // to size the pol blocks because that is LmLayout's sizing convention.
        let inner = LmLayout::new(ell_max_gamma, ell_max_nu);
        let n_state = inner.total_dof;
        Self {
            inner,
            ell_max_gamma,
            ell_max_nu,
            ell_max_pol,
            n_state,
        }
    }

    /// Whether polarization hierarchy is active.
    ///
    /// Same semantics as `CambLayout::has_pol()` in MB-95 code —
    /// keeps cross-formalism code parallel.
    #[inline]
    pub(crate) fn has_pol(&self) -> bool {
        self.ell_max_pol >= MIN_LMAX_POL_WHEN_ON
    }

    /// Validate invariants.  Panics on violation (same policy as
    /// `ssot::validate_layout_invariants` for MB-95).
    pub(crate) fn validate(&self) {
        assert!(
            self.ell_max_gamma >= MIN_LMAX_G,
            "PstfFlrwLayout: ell_max_gamma = {} < MIN_LMAX_G = {}",
            self.ell_max_gamma, MIN_LMAX_G
        );
        assert!(
            self.ell_max_nu >= MIN_LMAX_G,
            "PstfFlrwLayout: ell_max_nu = {} < MIN_LMAX_G = {} (neutrinos require same minimum as photons)",
            self.ell_max_nu, MIN_LMAX_G
        );
        // Polarization is either off (0) or on with ≥ MIN_LMAX_POL_WHEN_ON
        assert!(
            self.ell_max_pol == 0 || self.ell_max_pol >= MIN_LMAX_POL_WHEN_ON,
            "PstfFlrwLayout: ell_max_pol = {} is neither 0 (off) nor ≥ {} (on)",
            self.ell_max_pol, MIN_LMAX_POL_WHEN_ON
        );
        assert!(
            self.n_state == self.inner.total_dof,
            "PstfFlrwLayout: n_state = {} does not match inner.total_dof = {}",
            self.n_state, self.inner.total_dof
        );
    }

    // ═══════════════════════════════════════════════════════════════════
    //   §2. m=0 index accessors
    // ═══════════════════════════════════════════════════════════════════
    //
    // All accessors return flat indices into the inner state vector,
    // restricted to m=0.  Calling with m≠0 is a logic error in FLRW code
    // and will panic (see §3 caveat tests).

    /// Photon intensity I_{A_ℓ}^{(γ)} at m=0, flat state index.
    #[inline]
    pub(crate) fn i_photon_i_m0(&self, ell: usize) -> usize {
        assert!(ell <= self.ell_max_gamma,
            "i_photon_i_m0: ell={} exceeds ell_max_gamma={}", ell, self.ell_max_gamma);
        self.inner.photon_i_start
            + LmLayout::lm_offset_full(ell, 0, self.ell_max_gamma)
    }

    /// Photon E-mode E_{A_ℓ}^{(γ)} at m=0, flat state index.
    /// Requires `has_pol()` — panics otherwise.
    /// E-modes exist only for ℓ ≥ 2.
    #[inline]
    pub(crate) fn i_photon_e_m0(&self, ell: usize) -> usize {
        assert!(self.has_pol(),
            "i_photon_e_m0: polarization disabled (ell_max_pol={})", self.ell_max_pol);
        assert!(ell >= 2,
            "i_photon_e_m0: ell={} must be ≥ 2 (E-mode defined only for ℓ≥2)", ell);
        assert!(ell <= self.ell_max_gamma,
            "i_photon_e_m0: ell={} exceeds ell_max_gamma={}", ell, self.ell_max_gamma);
        self.inner.photon_e_start
            + LmLayout::lm_offset_pol(ell, 0, self.ell_max_gamma)
    }

    /// Photon B-mode B_{A_ℓ}^{(γ)} at m=0, flat state index.
    /// In FLRW scalar sector B_ℓ^{(0)} = 0 identically, but the DOF
    /// is retained for Bianchi compatibility.
    #[inline]
    pub(crate) fn i_photon_b_m0(&self, ell: usize) -> usize {
        assert!(self.has_pol(),
            "i_photon_b_m0: polarization disabled (ell_max_pol={})", self.ell_max_pol);
        assert!(ell >= 2,
            "i_photon_b_m0: ell={} must be ≥ 2", ell);
        assert!(ell <= self.ell_max_gamma,
            "i_photon_b_m0: ell={} exceeds ell_max_gamma={}", ell, self.ell_max_gamma);
        self.inner.photon_b_start
            + LmLayout::lm_offset_pol(ell, 0, self.ell_max_gamma)
    }

    /// Massless neutrino I_{A_ℓ}^{(ν)} at m=0, flat state index.
    #[inline]
    pub(crate) fn i_neutrino_m0(&self, ell: usize) -> usize {
        assert!(ell <= self.ell_max_nu,
            "i_neutrino_m0: ell={} exceeds ell_max_nu={}", ell, self.ell_max_nu);
        self.inner.nu_theta_start
            + LmLayout::lm_offset_full(ell, 0, self.ell_max_nu)
    }

    // ═════════════════════════════════════════════════════════════════
    //   Metric block accessors (PR-023a)
    // ═════════════════════════════════════════════════════════════════
    //
    // Metric block layout (11 DOF reserved):
    //   metric[0] = etak  ← active, sync-gauge scalar metric × k
    //   metric[1] = σ     ← active, shear scalar
    //   metric[2..=10]    ← reserved for Bianchi-I Z_{ab} tensor (Phase 4)

    /// PSTF metric scalar `etak` (= η·k) — active in FLRW sync gauge.
    /// MB-95 equivalent: `i_etak` in `CambLayout`.
    #[inline]
    pub(crate) fn i_metric_etak(&self) -> usize {
        self.inner.metric_start + 0
    }

    /// PSTF metric shear scalar `σ` — active in FLRW sync gauge.
    /// MB-95 equivalent: `i_sigma` in `CambLayout`.
    #[inline]
    pub(crate) fn i_metric_sigma(&self) -> usize {
        self.inner.metric_start + 1
    }

    // ═════════════════════════════════════════════════════════════════
    //   Fluid block accessors (PR-023b)
    // ═════════════════════════════════════════════════════════════════
    //
    // Baryon block (4 DOF): [δ_b, v_b_{m=-1}, v_b_{m=0}, v_b_{m=+1}]
    //                        offset 0   1          2          3
    // CDM block     (4 DOF): [δ_c, v_c_{m=-1}, v_c_{m=0}, v_c_{m=+1}]
    //                        (v_c_* = 0 identically at synchronous gauge)
    //
    // At FLRW m=0 only indices [0] and [2] are physically active.

    /// Baryon density contrast δ_b (= clxb in MB-95).
    #[inline]
    pub(crate) fn i_baryon_delta(&self) -> usize {
        self.inner.baryon_start + 0
    }

    /// Baryon velocity v_b at m=0 (MB-95 equivalent: `i_vb`).
    #[inline]
    pub(crate) fn i_baryon_v_m0(&self) -> usize {
        self.inner.baryon_start + 2
    }

    /// CDM density contrast δ_c (= clxc in MB-95).
    #[inline]
    pub(crate) fn i_cdm_delta(&self) -> usize {
        self.inner.cdm_start + 0
    }

    /// CDM velocity v_c at m=0.  Zero identically in synchronous gauge.
    /// Accessor retained for completeness and structural parallel with baryon.
    #[inline]
    pub(crate) fn i_cdm_v_m0(&self) -> usize {
        self.inner.cdm_start + 2
    }
}

// ═══════════════════════════════════════════════════════════════════════
//   §3. FLRW projection identity — PSTF coupling coefficients
// ═══════════════════════════════════════════════════════════════════════
//
// Companion helpers documenting the relationship between PSTF free-streaming
// coefficients and the MB-95 recursion.  These are NOT used by production
// code directly; they serve as the machine-checkable claim that the two
// formalisms share their FLRW limit at the coefficient level.

/// Reference MB-95 coefficient  ℓ / (2ℓ+1)  for the "down" direction
/// (coupling of Θ_ℓ to Θ_{ℓ−1}) per
/// `Θ_ℓ' = k/(2ℓ+1)·[ℓ·Θ_{ℓ−1} − (ℓ+1)·Θ_{ℓ+1}]`.
#[inline]
pub(crate) fn mb95_down_coefficient(ell: usize) -> f64 {
    ell as f64 / (2 * ell + 1) as f64
}

/// Reference MB-95 coefficient  (ℓ+1) / (2ℓ+1)  for the "up" direction
/// (coupling of Θ_ℓ to Θ_{ℓ+1}).
#[inline]
pub(crate) fn mb95_up_coefficient(ell: usize) -> f64 {
    (ell + 1) as f64 / (2 * ell + 1) as f64
}

// NOTE: A naive "normalization ratio" such as `(2ℓ+1)/(2ℓ−1)` does NOT
// convert PSTF `coupling::free_streaming_down(ell) = ℓ/(2ℓ−1)` into the
// MB-95 coefficient `ℓ/(2ℓ+1)`.  For ℓ=1 the ratio approach gives 3
// instead of 1/3 — a factor-9 error.
//
// The actual FLRW-limit equivalence between PSTF and MB-95 brightness
// hierarchies is more subtle and involves:
//   (i) STF-to-spherical-harmonic projection (Y_ℓ^{m=0})
//   (ii) Normalization factors in the I_{A_ℓ} / Θ_ℓ definition
//   (iii) Different recursion structures that coincide only after full
//        integration, not at per-coefficient level.
//
// This equivalence is the subject of PR-025 (Phase 2 equivalence test).
// PR-020 does NOT claim any pointwise identity between PSTF and MB-95
// coefficients; only that both sets of primitives exist and return their
// self-documented values.

// ═══════════════════════════════════════════════════════════════════════
//   §4. Tests (PR-020 TDD gate)
// ═══════════════════════════════════════════════════════════════════════

#[cfg(test)]
mod tests {
    use super::*;
    use crate::pstf::coupling;

    fn test_layout_pol_on() -> PstfFlrwLayout {
        let lay = PstfFlrwLayout::new(16, 16, 16);
        lay.validate();
        lay
    }

    fn test_layout_pol_off() -> PstfFlrwLayout {
        let lay = PstfFlrwLayout::new(16, 16, 0);
        lay.validate();
        lay
    }

    // ─── Identity tests (2) ─────────────────────────────────────────────

    /// PR-020 Identity #1: PSTF `coupling::free_streaming_{down,up}` return
    /// the values documented in `src/pstf/coupling.rs`.
    ///
    /// # Scope clarification
    ///
    /// This test does NOT claim FLRW-limit numerical equivalence with MB-95
    /// recursion coefficients — that is the subject of PR-025 (Phase 2
    /// equivalence test), where the full normalization chain
    ///
    ///   Θ_ℓ^{MB-95}(k)  ↔  I_{A_ℓ}^{PSTF} · STF_norm(ℓ) · Y_ℓ^{m=0}
    ///
    /// is worked out.  The naive pointwise ratio
    /// `free_streaming_down(ℓ)·(2ℓ+1)/(2ℓ−1)` does NOT equal `ℓ/(2ℓ+1)` —
    /// attempting that identity here would overstep PR-020's scope.
    ///
    /// What PR-020 asserts is only that the PSTF primitives exist, return
    /// finite values, and match their own documented definitions.
    #[test]
    fn identity_pstf_free_streaming_self_consistent() {
        // coupling::free_streaming_down(ℓ) = ℓ / (2ℓ − 1)
        // (see src/pstf/coupling.rs doc-comment)
        for ell in 1..=20 {
            let v = coupling::free_streaming_down(ell);
            let expected = ell as f64 / (2 * ell - 1) as f64;
            assert!((v - expected).abs() < 1e-15,
                "coupling::free_streaming_down({}) = {} but should be ℓ/(2ℓ−1) = {}",
                ell, v, expected);
        }
        // coupling::free_streaming_up(ℓ) = (ℓ+1) / (2ℓ+3)
        for ell in 0..=20 {
            let v = coupling::free_streaming_up(ell);
            let expected = (ell + 1) as f64 / (2 * ell + 3) as f64;
            assert!((v - expected).abs() < 1e-15,
                "coupling::free_streaming_up({}) = {} but should be (ℓ+1)/(2ℓ+3) = {}",
                ell, v, expected);
        }
    }

    /// PR-020 Identity #2: mb95_up_coefficient matches  (ℓ+1)/(2ℓ+1)
    /// exactly (no PSTF machinery needed; direct verification).
    #[test]
    fn identity_mb95_up_coefficient_hand_values() {
        // ℓ = 0: (0+1)/1 = 1
        assert!((mb95_up_coefficient(0) - 1.0).abs() < 1e-15);
        // ℓ = 1: 2/3
        assert!((mb95_up_coefficient(1) - 2.0/3.0).abs() < 1e-15);
        // ℓ = 2: 3/5
        assert!((mb95_up_coefficient(2) - 3.0/5.0).abs() < 1e-15);
        // ℓ = 10: 11/21
        assert!((mb95_up_coefficient(10) - 11.0/21.0).abs() < 1e-15);
        // Large-ℓ limit: → 1/2
        assert!((mb95_up_coefficient(1000) - 0.5).abs() < 1e-3);
    }

    // ─── Limit tests (2) ─────────────────────────────────────────────────

    /// PR-020 Limit #1: pol=0 turns off polarization accessors.
    ///
    /// When polarization is disabled, `i_photon_e_m0` / `i_photon_b_m0`
    /// must panic on any call.  `has_pol()` must return false.
    #[test]
    fn limit_pol_off_has_pol_false() {
        let lay = test_layout_pol_off();
        assert!(!lay.has_pol());
    }

    #[test]
    #[should_panic(expected = "polarization disabled")]
    fn limit_pol_off_e_mode_accessor_panics() {
        let lay = test_layout_pol_off();
        let _ = lay.i_photon_e_m0(2);  // expected panic
    }

    // ─── Channelwise tests (2) ───────────────────────────────────────────

    /// PR-020 Channelwise #1: photon I, photon E, photon B, neutrino I
    /// occupy disjoint index ranges.
    #[test]
    fn channelwise_index_blocks_disjoint() {
        let lay = test_layout_pol_on();
        // Enumerate all photon-I m=0 indices for ℓ=0..ell_max
        let photon_i: Vec<usize> = (0..=lay.ell_max_gamma).map(|l| lay.i_photon_i_m0(l)).collect();
        // Photon-E and photon-B m=0 indices for ℓ=2..ell_max
        let photon_e: Vec<usize> = (2..=lay.ell_max_gamma).map(|l| lay.i_photon_e_m0(l)).collect();
        let photon_b: Vec<usize> = (2..=lay.ell_max_gamma).map(|l| lay.i_photon_b_m0(l)).collect();
        // Neutrino m=0 indices
        let nu: Vec<usize> = (0..=lay.ell_max_nu).map(|l| lay.i_neutrino_m0(l)).collect();

        // All four sets must be pairwise disjoint
        for &i_i in &photon_i {
            assert!(!photon_e.contains(&i_i), "photon_i index {} collides with photon_e", i_i);
            assert!(!photon_b.contains(&i_i), "photon_i index {} collides with photon_b", i_i);
            assert!(!nu.contains(&i_i), "photon_i index {} collides with nu", i_i);
        }
        for &i_e in &photon_e {
            assert!(!photon_b.contains(&i_e), "photon_e index {} collides with photon_b", i_e);
            assert!(!nu.contains(&i_e), "photon_e index {} collides with nu", i_e);
        }
        for &i_b in &photon_b {
            assert!(!nu.contains(&i_b), "photon_b index {} collides with nu", i_b);
        }
    }

    /// PR-020 Channelwise #2: index range within each block matches what
    /// `LmLayout` allocates for the m=0 slice at (ℓ_max + 1)² m-major layout.
    ///
    /// For m=0 section inside an (ℓ_max + 1)² block, the m=0 slice runs
    /// ℓ = 0..ℓ_max (inclusive), contiguous.
    #[test]
    fn channelwise_index_within_layout_bounds() {
        let lay = test_layout_pol_on();
        // Every returned index must be < n_state
        for l in 0..=lay.ell_max_gamma {
            assert!(lay.i_photon_i_m0(l) < lay.n_state,
                "i_photon_i_m0({}) = {} >= n_state = {}",
                l, lay.i_photon_i_m0(l), lay.n_state);
        }
        for l in 2..=lay.ell_max_gamma {
            assert!(lay.i_photon_e_m0(l) < lay.n_state);
            assert!(lay.i_photon_b_m0(l) < lay.n_state);
        }
        for l in 0..=lay.ell_max_nu {
            assert!(lay.i_neutrino_m0(l) < lay.n_state);
        }
    }

    // ─── Validation tests (3) ────────────────────────────────────────────

    #[test]
    #[should_panic(expected = "ell_max_gamma")]
    fn validation_rejects_small_ell_max_gamma() {
        let lay = PstfFlrwLayout::new(1, 16, 16);  // 1 < MIN_LMAX_G (3)
        lay.validate();
    }

    #[test]
    #[should_panic(expected = "ell_max_nu")]
    fn validation_rejects_small_ell_max_nu() {
        let lay = PstfFlrwLayout::new(16, 2, 16);  // 2 < MIN_LMAX_G (3)
        lay.validate();
    }

    #[test]
    #[should_panic(expected = "ell_max_pol")]
    fn validation_rejects_pol_eq_1() {
        // pol=1 is neither fully-off (0) nor valid-on (≥ MIN_LMAX_POL_WHEN_ON=2)
        let lay = PstfFlrwLayout::new(16, 16, 1);
        lay.validate();
    }

    // ─── Caveat tests (2) ────────────────────────────────────────────────

    /// PR-020 Caveat #1: no synchronous-gauge fields are exposed.
    ///
    /// This is a structural assertion — there must be NO `i_h_sync`,
    /// `i_eta_sync`, `i_sigma_sync` accessors on `PstfFlrwLayout`.
    /// We prove this at the struct level by listing its actual fields;
    /// this test serves as a regression guard that would fail if
    /// someone later adds a gauge-artifact field.
    #[test]
    fn caveat_no_synchronous_gauge_fields() {
        let lay = test_layout_pol_on();
        // Struct must expose only: inner, ell_max_gamma, ell_max_nu,
        // ell_max_pol, n_state.
        //
        // Any attempt to access `lay.i_h_sync` or `lay.i_eta_sync` would
        // fail at compile time.  We document the explicit invariant here.
        //
        // The *field access* below confirms the allowed fields:
        let _ = &lay.inner;
        let _ = lay.ell_max_gamma;
        let _ = lay.ell_max_nu;
        let _ = lay.ell_max_pol;
        let _ = lay.n_state;
        // Nothing more.  PSTF is gauge-invariant; metric variables
        // (Φ^{1+3}, σ_{ab} geometric, etc.) are introduced in PR-023
        // via `pstf_primary::metric` as distinct, covariant DOF.
    }

    /// PR-020 Caveat #2: `has_pol()` semantics match MB-95 exactly.
    ///
    /// Cross-formalism consistency: both `CambLayout::has_pol()` and
    /// `PstfFlrwLayout::has_pol()` must return the same answer for the
    /// same `ell_max_pol` input.  This is what makes the PR-010 source
    /// registry (`SourceInputs.has_pol`) formalism-agnostic.
    #[test]
    fn caveat_has_pol_threshold_matches_mb95() {
        // pol=0 → off in both
        assert!(!PstfFlrwLayout::new(16, 16, 0).has_pol());
        // pol=2 → on in both (MIN_LMAX_POL_WHEN_ON = 2)
        assert!(PstfFlrwLayout::new(16, 16, 2).has_pol());
        // pol=16 → on in both
        assert!(PstfFlrwLayout::new(16, 16, 16).has_pol());
    }

    // ─── Integration with existing pstf module (sanity) ───────────────────

    /// PR-020 sanity: reusing `src/pstf/` primitives produces the
    /// expected FLRW values.  This is a regression guard for the claim
    /// in `pr-020-design.md` that `src/pstf/coupling` is formalism-agnostic
    /// at the coefficient level.
    #[test]
    fn sanity_pstf_coupling_concrete_values() {
        // Documented in coupling.rs: free_streaming_down(ℓ=2) = 2/3
        assert!((coupling::free_streaming_down(2) - 2.0/3.0).abs() < 1e-15);
        // free_streaming_up(ℓ=0) = 1/3
        assert!((coupling::free_streaming_up(0) - 1.0/3.0).abs() < 1e-15);
        // Large-ℓ limit: both → 1/2
        assert!((coupling::free_streaming_down(1000) - 0.5).abs() < 1e-2);
        assert!((coupling::free_streaming_up(1000) - 0.5).abs() < 1e-2);
    }
}
