// BASS crate root — PyO3 entry point only.
// BA-01: Restructured from flat 17-module layout to hierarchical tree.

// PERF-01: Use mimalloc as the global allocator. Default malloc serializes
// concurrent allocations under contention; with rayon par_iter over k-modes,
// each k-mode allocates ~14MB of matrix data + many history vectors, and
// contention on the global allocator was preventing scaling. mimalloc has
// per-thread heaps that eliminate this bottleneck.
#[global_allocator]
static GLOBAL: mimalloc::MiMalloc = mimalloc::MiMalloc;

pub(crate) mod core;
pub(crate) mod recombination;
pub(crate) mod solver;
pub(crate) mod hierarchy;
pub(crate) mod bianchi;
pub(crate) mod pstf;
pub(crate) mod collision;
pub(crate) mod species;
pub(crate) mod los;
pub(crate) mod observable;
pub(crate) mod teff;
pub(crate) mod forward;
pub(crate) mod inference;
pub(crate) mod source;  // PR-010 Stage B: SSOT-routed source channel registry

use pyo3::prelude::*;
use pyo3::types::PyModule;

#[pymodule]
fn bass_rs(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    // ── Recombination / thermodynamics ──
    m.add_function(wrap_pyfunction!(recombination::thermo::backend_name, m)?)?;
    m.add_function(wrap_pyfunction!(recombination::thermo::backend_ready, m)?)?;
    m.add_function(wrap_pyfunction!(recombination::thermo::ping, m)?)?;
    m.add_function(wrap_pyfunction!(recombination::thermo::hubble_si_scalar, m)?)?;
    m.add_function(wrap_pyfunction!(recombination::thermo::temperature_history, m)?)?;
    m.add_function(wrap_pyfunction!(recombination::thermo::baryon_loading_history, m)?)?;
    m.add_function(wrap_pyfunction!(recombination::thermo::background_grid, m)?)?;
    m.add_function(wrap_pyfunction!(recombination::thermo::solve_peebles_hydrogen_rodas5p, m)?)?;
    m.add_function(wrap_pyfunction!(recombination::thermo::solve_peebles_hydrogen_rodas5p_diagnostics, m)?)?;
    m.add_function(wrap_pyfunction!(recombination::thermo::calibrate_hydrogen_history, m)?)?;
    // ── Visibility (BA-02: split from thermo) ──
    m.add_function(wrap_pyfunction!(recombination::visibility::recombination_postprocess, m)?)?;
    m.add_function(wrap_pyfunction!(recombination::visibility::legacy_visibility_eta_grid, m)?)?;
    m.add_function(wrap_pyfunction!(recombination::visibility::visibility_profile, m)?)?;
    // ── Hierarchy (autonomous) ──
    m.add_function(wrap_pyfunction!(recombination::thermo::evaluate_hierarchy_autonomous, m)?)?;
    m.add_function(wrap_pyfunction!(recombination::thermo::solve_hierarchy_autonomous_rodas5p, m)?)?;
    // ── Generic linear profile solver ──
    m.add_function(wrap_pyfunction!(solver::solve_linear::solve_linear_profile_rodas5p, m)?)?;
    // ── Hierarchy solvers ──
    m.add_function(wrap_pyfunction!(hierarchy::baryon_photon::solve_baryon_photon_native_rodas5p, m)?)?;
    m.add_function(wrap_pyfunction!(hierarchy::polarised::solve_polarised_native_rodas5p, m)?)?;
    m.add_function(wrap_pyfunction!(hierarchy::neutrino::solve_neutrino_native_rodas5p, m)?)?;
    m.add_function(wrap_pyfunction!(hierarchy::multispecies::solve_multispecies_native_rodas5p, m)?)?;
    m.add_function(wrap_pyfunction!(hierarchy::stacked::solve_stacked_native_rodas5p, m)?)?;
    m.add_function(wrap_pyfunction!(hierarchy::stacked::stacked_operator_toy_profile, m)?)?;
    Ok(())
}
