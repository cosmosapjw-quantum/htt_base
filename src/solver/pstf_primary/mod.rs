// ═══════════════════════════════════════════════════════════════════════
// BASS PSTF Primary Solver (Production Target)
// ═══════════════════════════════════════════════════════════════════════
//
// Per `docs/SSOT_POLICY.md §17` and `docs/ROADMAP_PHASE_I_TO_L.md` v2.0
// Phase 1 (PR-020..PR-024).
//
// **Role**: This module tree is the **production target** solver based on
// the 1+3 covariant PSTF (Projected Symmetric Trace-Free) formalism
// (Challinor & Lasenby 2000 I/II; Tsagas, Challinor & Maartens 2008 review).
// The MB-95 synchronous-gauge implementation in `src/solver/sync_gauge_camb.rs`
// is being reclassified as a **verified FLRW oracle**, to be retired into
// `#[cfg(test)]` scope after PR-026 (Phase 3 backend switch).
//
// **PR schedule**:
// - PR-020 (this commit): state layout + hierarchy primitives (thin wrapper
//   over `src/pstf/` 130-test-passing base).
// - PR-021: adiabatic IC
// - PR-022: RHS (photon/ν/Thomson) + Jacobian (Rodas5P-compatible)
// - PR-023: metric sector (1+3 covariant)
// - PR-024: LoS source + `solve_pstf_spectrum()`
// - PR-025: FLRW equivalence test MB-95 ↔ PSTF (≤0.5% at ℓ ∈ [2, 300])
// - PR-026: production backend switch
//
// **Reuse map** (from `docs/PR_DELTAS/pr-020-design.md §2`):
// - `crate::pstf::coupling`       — ✅ STF primitives (free_streaming, CG kappa, STF norm)
// - `crate::pstf::tensor`         — ✅ STF projection / Frobenius
// - `crate::pstf::lm_indexing`    — ✅ (ℓ,m) layout (Bianchi-ready, FLRW uses m=0 only)
// - `crate::pstf::hierarchy_matrix` — ✅ coupling matrix assembly
// - `crate::pstf::tca_lm`         — ✅ TCA closure
// - `crate::pstf::hierarchy`      — 🟡 struct reused, step replaced by Rodas5P
// - `crate::pstf::collision_lm`   — 🔍 re-derivation required for electron-frame ζ̃
// - `crate::pstf::m_decomposition`, `streaming_lm` — ⏸️ deferred to Phase 4
//
// **PR-020 scope** (this commit):
// - `layout::PstfFlrwLayout` — thin wrapper over `LmLayout`, FLRW-specialized
//   (m=0 section only; assert on m≠0 access).
// - Unit tests (identity / limit / channelwise / regression / caveat).
// - Production path UNCHANGED — D_2 = 1002.086744 μK² bit-identical preserved.

#![allow(dead_code)]

pub(crate) mod layout;
pub(crate) mod ic;
pub(crate) mod rhs_free;
pub(crate) mod collision;
pub(crate) mod jacobian;
pub(crate) mod metric;
pub(crate) mod fluid;
pub(crate) mod full_rhs;
pub(crate) mod source;
pub(crate) mod matrix;
pub(crate) mod integrate;
