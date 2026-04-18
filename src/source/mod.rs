// ═══════════════════════════════════════════════════════════════════════
// BASS Source Registry — top-level module
// ═══════════════════════════════════════════════════════════════════════
//
// Per `docs/PR_CONSTITUTION.md §3` PR-010 (FLRW source/radial channel
// split cleanup) and PR-023 (linear/quadratic source registry).
//
// This crate sub-tree owns the canonical split of FLRW scalar source
// channels:
//
//   - `registry` — per-channel pure functions (SW / ISW / Doppler /
//                  Polter-quad / E-mode) with SSOT conformance.
//
// Future additions (PR-023+):
//
//   - `bridge`   — ForwardBridge-wrapped source exports for HTT/MIO
//   - `quadratic` — quadratic source library (second-order sources)

#![allow(dead_code)]

pub(crate) mod registry;
