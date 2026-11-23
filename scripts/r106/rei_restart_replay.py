"""R106 D1: replay the actual REI z=4 restart checkpoints of the five shear cases.

Inputs are the native AXBI_CHECKPOINT_V2 restart files of the original REI runs
(rei_bianchi commit 56dc609e manifests; checkpoint files on the workstation).
Nothing in rei_bianchi or the recovery bundle is modified: the frozen Rust crate is
copied into the output directory, its compiled source identity is re-hashed, and a
read-only replay example is added there.  The physics, tolerances, clock and step
rule are those of the copied crate; only resource caps (which gate termination, not
a step result) are set to the values the original continuation wrappers applied.

Stages
  build    copy + identity-verify the two source epochs, compile the replay example
  record   (no compilation) record script/environment/toolchain identity and full
           src/ tree hashes of the two epochs into BUILD.json
  replay   per case: restart from checkpoint 312120, replay to 312180 and 312237
           (continuous), restart from the original 312180 checkpoint to 312237,
           re-read the terminal restart, probe the z<4 domain
  analyze  restart inventory (charge bookkeeping, temperature, proper time, photons),
           replay residuals over the stated window, clock/H consistency and quadrature
           error of the native rows on z in [4,20], FLRW+tanh foreground sensitivity
           at z<4 (outside the locked domain, sensitivity only)

Regenerate from the cached native outputs without rebuilding or rerunning native code:
  python -B scripts/r106/rei_restart_replay.py --stages record,analyze

Claim classes (see the result's claim_classes): the replay is a numerical
reproducibility statement of the frozen solver; the clock integrals are a clock/H
consistency and quadrature check; restart-state values and the native Thomson depth
are conditional model outputs of the locked, non-admitted scenario; nothing here is
a physical attribution.
"""
from __future__ import annotations

import argparse
import concurrent.futures as futures
import hashlib
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

import numpy as np

SCRIPT = Path(__file__).resolve()
HTT_BASE = SCRIPT.parents[2]
REI_REPO = Path("/home/cosmosapjw/Dropbox/bianchi/rei_bianchi")
REI_COMMIT = "56dc609ea9b801c88d3364aed3eee140b3a20d46"
PLUS = Path("/home/cosmosapjw/Dropbox/bianchi/rei_ax08_plus_recovery_20261115")
RUNS = REI_REPO / "research/axbi_goal_20261014/runs"
DEFAULT_OUT = Path.home() / "Downloads/htt_r106_analysis/rei"
SYNC = "research/rei_igm_sync_20261116"
FIVE_CASE_PATH = SYNC + "/approximation_validity/incremental_fifth/results_five/five_case_abundances.csv.gz"
FIVE_CASE_SHA = "f4bc0046d79faf2cd13ae7ed78135503306c7d76c11580e4601a757c407bc83d"
ID_PLUS = "d7676b9309ac9b084499bbf599e803baecd661c80765489be45839ef5a7cf185"
ID_PAIRED = "4de69c1e68ebd395fe2d0b5580d901b9a82bde86cadbd11bdd07e5ad2042b4a1"
IDENTITY_FILES = [
    "src/axbi_driver.rs", "src/axbi_background.rs", "src/axbi_sources.rs", "src/axbi_rates.rs",
    "src/igm_rates.rs", "src/igm_thermal.rs", "src/igm_state.rs", "src/igm_background.rs",
    "src/atomic_provider.rs", "src/bianchi_i.rs", "src/hhe_events.rs", "examples/axbi_reionization.rs",
    "src/lib.rs", "Cargo.toml",
    "../../docs/fastest_track_chat/REI-AXBI-GOAL-20261014/OUTPUT_CONTRACT.json",
    "../../research/axbi_goal_20261014/scenario/SCENARIO_LOCK.json",
    "../../research/axbi_goal_20261014/scenario/AX05_NUMERICAL_CONTRACT.md",
]
BOUNDARY = "\nAXBI_SOURCE_BOUNDARY\n"
CASES: dict[str, dict[str, Any]] = {
    "ZERO": dict(q_ref=0.0, segment=RUNS / "flrw/32d11e733155/ZERO_continuation_001",
                 composed=RUNS / "flrw/32d11e733155/ZERO_composed_001", identity=ID_PLUS),
    "SHEAR_HALF_PLUS": dict(q_ref=0.005, segment=RUNS / "paired/32d11e733155/SHEAR_HALF_PLUS_continuation_001",
                            composed=RUNS / "paired/32d11e733155/SHEAR_HALF_PLUS_composed_002", identity=ID_PAIRED),
    "SHEAR_HALF_MINUS": dict(q_ref=-0.005, segment=RUNS / "paired/32d11e733155/SHEAR_HALF_MINUS_continuation_001",
                             composed=RUNS / "paired/32d11e733155/SHEAR_HALF_MINUS_composed_001", identity=ID_PAIRED),
    "SHEAR_PLUS": dict(q_ref=0.01, segment=PLUS / "SHEAR_PLUS_continuation_002", composed=None, identity=ID_PLUS),
    "SHEAR_MINUS": dict(q_ref=-0.01, segment=RUNS / "paired/32d11e733155/SHEAR_MINUS_continuation_001",
                        composed=RUNS / "paired/32d11e733155/SHEAR_MINUS_composed_001", identity=ID_PAIRED),
}
START, MIDDLE, TERMINAL = 312120, 312180, 312237
# Physical constants exactly as in the copied crate (hhe_events.rs, axbi_driver.rs) and htt REC (SI).
KB_ERG_K, EV_ERG = 1.380649e-16, 1.602176634e-12
F_HE = 0.2454 / (4.0 * (1.0 - 0.2454))
H0 = 67.4e5 / 3.0856775814913673e24
OM, OR = 0.315, 9.2e-5
OL = 1.0 - OM - OR
A_REF = 1.0 / 21.0
C_SI, SIGMA_T_SI = 299792458.0, 6.6524587321e-29
LEDGER_NAMES = ["source_N_per_H", "source_U_eV_per_H", "absorbed_N_per_H", "escape_U_eV_per_H",
                "boundary_N_per_H", "boundary_U_eV_per_H", "thermal_work_eV_per_H", "photon_work_eV_per_H",
                "signed_CMB_input_eV_per_H", "DR_events_per_H", "CE_cap_eV_per_H", "excluded_DR_eV_per_H"] + [
    f"{k}_events_{i}_per_H" for k in ("RR", "CI", "photo", "CI_floor") for i in range(3)]
UNITS = {"a": "1", "time_s": "s (proper, elapsed since mean z=20)", "b": "1", "H_per_s": "s^-1",
         "s_per_s": "s^-1", "H_flrw_per_s": "s^-1", "x_HII": "1 (per H)", "x_HeII": "1 (per He)",
         "x_HeIII": "1 (per He)", "w_erg_per_H": "erg per H", "nH_proper_cm3": "cm^-3",
         "nHe_proper_cm3": "cm^-3", "ne_proper_cm3": "cm^-3", "temperature_K": "K",
         "photon_n_per_H": "photons per H", "photon_u_eV_per_H": "eV per H", "moments_eV_per_H": "eV per H",
         "photon_count_residual_per_H": "photons per H", "energy_residual_eV_per_H": "eV per H",
         "next_dln_a": "1", "last_error": "1", "max_newton_residual": "1",
         "ledgers": "per H (counts) or eV per H, by ledger name", "photons": "photons per H per (angle, energy) node"}
COUNTS = ["accepted", "attempts", "rejects", "consecutive_rejects", "rhs_evaluations", "comparisons"]
LOCK_REL = "research/axbi_goal_20261014/scenario/SCENARIO_LOCK.json"
# RETURN.txt key -> checkpoint counter index (AXBI_CHECKPOINT_V2 line 3 order is COUNTS).
RETURN_COUNT_FIELDS = (("accepted", 0), ("attempts", 1), ("rejections", 2), ("rhs_evaluations", 4), ("comparisons", 5))
# RETURN.txt key -> parsed checkpoint field.
RETURN_FLOAT_FIELDS = (("a", "a"), ("wall_s", "wall_elapsed_s"), ("max_newton_residual", "max_newton_residual"),
                       ("last_error", "last_error"))
ANCHOR_BLOB_LIMIT_BYTES = 1 << 20
CONSTANT_STEP_REL_TOL = 1e-9
REVIEW_CORRECTIONS = [
    {"id": "REI-R106-01", "change": (
        "Removed the per-case cosmic_age_at_mean_z20_s_from_locked_background and cosmic_age_at_restart_s fields and "
        "the a=1e-12..a_ref quadrature of the sheared H law that produced them (outside the locked domain; "
        "SCENARIO_LOCK clock.absolute_cosmic_age_s=null). Added one top-level q=0 FLRW age at zbar=20, labelled "
        "EXTERNAL_CONVENTION_OUTSIDE_LOCKED_DOMAIN and identical for all cases. No q-dependent extrapolated age is "
        "reported. The z<4 foreground H model is now labelled as an extension beyond a_end (sensitivity only).")},
    {"id": "REI-R106-02", "change": (
        "Provenance is described as RECEIPT_LINKED_PLUS_CONTENT_BOUND for the four composed cases and "
        "GIT_MANIFEST_HASH_BOUND_PLUS_CONTENT_BOUND for SHEAR_PLUS. COMPOSITION_RECEIPT.json, composed RETURN.txt and "
        "composed checkpoint.txt are hashed into input_sha256. chain_ok now also requires equality of every RETURN "
        "counter/clock/error field with the checkpoint and of both RETURN residuals with the natively recomputed "
        "residuals. The git refs whose tips actually contain each checkpoint sha256 are found by a scan of the "
        "rei_bianchi object store run now, and the REI_COMMIT ancestry is recorded.")},
    {"id": "REI-R106-03", "change": (
        "The dt-form versus dN-form agreement is reported as a clock/H consistency check (dt/dN=1/H) plus a "
        "quadrature-error estimate (native rows versus Richardson and versus a cubic spline). It is stated not to "
        "validate tau(4..20), because both forms share n_e, sigma_T and H.")},
    {"id": "REI-R106-04", "change": (
        "Renamed ne_vs_native_eos_cm3, ne_vs_history_last_row_cm3 and abundance_rows_charge_neutrality_cm3 to "
        "electron_formula_*_consistency fields, and stated that charge neutrality is imposed by the EOS "
        "(n_e = n_H x_HII + n_He (x_HeII + 2 x_HeIII)); these are bookkeeping identities, not tests.")},
    {"id": "REI-R106-05", "change": (
        "The z<4 list is now a top-level z_below_4_continuation with three independent blockers (1 scenario-lock "
        "scope, 2 DriverConfig::validate 4<=end_zbar<20, 3 source redshift guard plus no admitted z<4 source model), "
        "each with the source line found now in both compiled epochs, and with background domain, absolute age and "
        "stored H/s marked DERIVED or NON_BLOCKING. Each case records the positive control from the cached native "
        "replay: the config.cfg end_zbar passed DriverConfig::read and Driver::new (both call validate).")},
    {"id": "REI-R106-06", "change": (
        "Each case states the replay window next to the residual: accepted-step count, zbar range, "
        "rejections in window, attempts per step and the per-step dln a regime (constant step, endpoint-clipped "
        "final step). The headline residual covers every compared field including ledgers, photons and the energy "
        "residual. The reject and step-size-change branches are listed as not exercised. No new native window run.")},
    {"id": "REI-R106-07", "change": (
        "BUILD.json and the result record the script sha256, htt_base HEAD and dirty flag, script git tracking "
        "status, python/numpy/scipy/pandas versions, platform, current rustc/cargo versions, the rustc that built "
        "the cached binaries (target/.rustc_info.json), the full src/ tree hash per epoch, the compiled src files "
        "not covered by the 17-file identity hash, and a recomputed binary sha256. Done without recompiling.")},
]

RUST_REPLAY = r'''//! R106 replay of frozen REI AXBI restart checkpoints. Reads AXBI_CHECKPOINT_V2 with the
//! frozen driver; no model, tolerance, clock or step-rule change. Resource caps are set to the
//! values the original continuation wrapper applied; they gate termination only.
use rei_microphysics::axbi_driver::{Driver, DriverConfig, DriverState};
use rei_microphysics::ForwardError;
use std::{fs, path::{Path, PathBuf}, time::Instant};

fn fail(s: &'static str) -> ForwardError { ForwardError::InvalidInput(s) }
fn io(_: std::io::Error) -> ForwardError { fail("R106_REPLAY_IO") }
fn num(x: f64) -> String { if x.is_finite() { format!("{x:?}") } else { "null".to_string() } }
fn arr(v: &[f64]) -> String { format!("[{}]", v.iter().map(|x| num(*x)).collect::<Vec<_>>().join(",")) }
fn quote(s: &str) -> String { format!("\"{}\"", s.replace('\\', "\\\\").replace('"', "\\\"")) }
fn outcome<T>(r: Result<T, ForwardError>) -> String {
    match r { Ok(_) => quote("OK"), Err(e) => quote(&format!("{e:?}")) }
}
fn ledgers(s: &DriverState) -> Vec<f64> {
    let l = &s.ledgers;
    let mut v = vec![l.source_n, l.source_u, l.absorbed_n, l.escaped_u, l.boundary_n, l.boundary_u,
        l.thermal_work, l.photon_work, l.cmb_input, l.dr_events, l.ce_cap_ev, l.excluded_dr_ev];
    for a in [l.rr_events, l.ci_events, l.photo_events, l.ci_floor_events] { v.extend(a); }
    v
}
fn state_json(d: &Driver, s: &DriverState) -> Result<String, ForwardError> {
    let p = d.background.point_at_scale(s.a)?;
    let nh = d.n_h0_cm3 / s.a.powi(3);
    let nhe = d.n_he0_cm3 / s.a.powi(3);
    let eos = s.gas.eos(nh, nhe)?;
    let (n, u) = d.photon_inventory(s);
    let m = d.moments(s)?;
    let (rn, ru) = d.residuals(s)?;
    let f = s.gas.fractions;
    Ok(format!(concat!("{{\"accepted\":{},\"attempts\":{},\"rejects\":{},\"consecutive_rejects\":{},",
        "\"rhs_evaluations\":{},\"comparisons\":{},\"a\":{},\"time_s\":{},\"b\":{},\"H_per_s\":{},",
        "\"s_per_s\":{},\"H_flrw_per_s\":{},\"x_HII\":{},\"x_HeII\":{},\"x_HeIII\":{},\"w_erg_per_H\":{},",
        "\"nH_proper_cm3\":{},\"nHe_proper_cm3\":{},\"ne_proper_cm3\":{},\"temperature_K\":{},",
        "\"photon_n_per_H\":{},\"photon_u_eV_per_H\":{},\"moments_eV_per_H\":{},",
        "\"photon_count_residual_per_H\":{},\"energy_residual_eV_per_H\":{},\"next_dln_a\":{},",
        "\"last_error\":{},\"max_newton_residual\":{},\"wall_elapsed_s\":{},\"ledgers\":{},\"photons\":{}}}"),
        s.accepted, s.attempts, s.rejects, s.consecutive_rejects, s.rhs_evaluations, s.comparisons,
        num(s.a), num(p.time_s), num(p.b), num(p.h_per_s), num(p.s_per_s), num(p.h_flrw_per_s),
        num(f[0]), num(f[1]), num(f[2]), num(s.gas.w_erg_per_h), num(nh), num(nhe),
        num(eos.electron_density_cm3), num(eos.temperature_k), num(n), num(u), arr(&m), num(rn), num(ru),
        num(s.next_dln_a), num(s.last_error), num(s.max_newton_residual), num(s.wall_elapsed_s),
        arr(&ledgers(s)), arr(&s.photons)))
}
#[derive(Default)]
struct Rows { history: Vec<u8>, abundances: Vec<u8>, spectra: Vec<u8>, ledgers: Vec<u8>, feedback: Vec<u8> }
impl Rows {
    fn emit(&mut self, d: &Driver, s: &DriverState, case: &str, spectrum: bool) -> Result<(), ForwardError> {
        let mut p: Vec<u8> = Vec::new();
        d.output_row(s, case, &mut self.history, &mut self.abundances, &mut p, &mut self.ledgers, &mut self.feedback)?;
        if spectrum { self.spectra.extend_from_slice(&p); }
        Ok(())
    }
    fn write(&self, dir: &Path, prefix: &str) -> Result<(), ForwardError> {
        for (name, bytes) in [("history", &self.history), ("abundances", &self.abundances),
                              ("spectra", &self.spectra), ("ledgers", &self.ledgers), ("feedback", &self.feedback)] {
            fs::write(dir.join(format!("{prefix}_{name}.csv")), bytes).map_err(io)?;
        }
        Ok(())
    }
}
// Same acceptance/reject continuation rule as the original continuation loop.
fn advance(d: &Driver, s: &mut DriverState, target: usize, case: &str, rows: &mut Rows,
           log: &mut Vec<String>) -> Result<(), ForwardError> {
    let end = 1.0 / (1.0 + d.config.end_zbar);
    while s.accepted < target {
        if s.a == end { return Err(fail("R106_ENDPOINT_BEFORE_TARGET")); }
        match d.adaptive_step(s) {
            Ok(true) => {
                let due = s.accepted % d.config.spectra_every_accepted == 0 || s.a == end;
                rows.emit(d, s, case, due)?;
            }
            Ok(false) => {
                log.push(format!("reject attempts={} a={:?} next_dln_a={:?} metric={:?}",
                                 s.attempts, s.a, s.next_dln_a, s.last_error));
                if s.consecutive_rejects >= 30 || s.next_dln_a < 1e-10 { return Err(fail("R106_REJECT_CAP")); }
            }
            Err(e) => {
                log.push(format!("step_error attempts={} a={:?} next_dln_a={:?} error={e:?}",
                                 s.attempts, s.a, s.next_dln_a));
                if s.consecutive_rejects >= 30 || s.next_dln_a < 1e-10 || s.rhs_evaluations >= d.config.max_rhs {
                    return Err(e);
                }
            }
        }
    }
    if s.accepted != target { return Err(fail("R106_TARGET_OVERSHOOT")); }
    Ok(())
}
fn main() {
    if let Err(e) = cli() { eprintln!("{e:?}"); std::process::exit(1); }
}
fn cli() -> Result<(), ForwardError> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.len() % 2 != 0 { return Err(fail("R106_USAGE")); }
    let mut m = std::collections::BTreeMap::new();
    for p in args.chunks_exact(2) {
        if m.insert(p[0].clone(), p[1].clone()).is_some() { return Err(fail("R106_USAGE")); }
    }
    let get = |k: &str| m.get(k).cloned().ok_or(fail("R106_USAGE"));
    let config_path = PathBuf::from(get("--config")?);
    let case = get("--case")?;
    let start_path = PathBuf::from(get("--start")?);
    let refs: Vec<PathBuf> = get("--references")?.split(',').map(PathBuf::from).collect();
    let terminal_path = PathBuf::from(get("--terminal")?);
    let caps: Vec<f64> = get("--caps")?.split(',')
        .map(|s| s.parse::<f64>().map_err(|_| fail("R106_CAPS"))).collect::<Result<_, _>>()?;
    let out = PathBuf::from(get("--out")?);
    if caps.len() != 4 { return Err(fail("R106_CAPS")); }
    let text = fs::read_to_string(&config_path).map_err(io)?;
    let mut cfg = DriverConfig::read(&text)?;
    cfg.max_steps = caps[0] as usize;
    cfg.max_attempts = caps[1] as usize;
    cfg.max_rhs = caps[2] as usize;
    cfg.max_wall_s = caps[3];
    let (d, _) = Driver::new(cfg.clone())?;
    fs::create_dir_all(&out).map_err(io)?;
    let start = d.read_checkpoint(&start_path)?;
    let references = refs.iter().map(|p| d.read_checkpoint(p)).collect::<Result<Vec<_>, _>>()?;
    let terminal = d.read_checkpoint(&terminal_path)?;
    let mut log = Vec::new();
    let mut rows = Rows::default();
    let mut s = start.clone();
    rows.emit(&d, &s, &case, true)?;
    let mut continuous = Vec::new();
    let t0 = Instant::now();
    for r in &references {
        advance(&d, &mut s, r.accepted, &case, &mut rows, &mut log)?;
        let mut saved = s.clone();
        saved.wall_elapsed_s = r.wall_elapsed_s;
        d.save_checkpoint(&out.join(format!("continuous_{:08}.txt", s.accepted)), &saved)?;
        continuous.push(state_json(&d, &s)?);
    }
    let continuous_wall = t0.elapsed().as_secs_f64();
    rows.write(&out, "continuous")?;
    let mut restart = Vec::new();
    let t1 = Instant::now();
    for w in references.windows(2) {
        let mut rows2 = Rows::default();
        let mut s2 = w[0].clone();
        rows2.emit(&d, &s2, &case, true)?;
        advance(&d, &mut s2, w[1].accepted, &case, &mut rows2, &mut log)?;
        let mut saved = s2.clone();
        saved.wall_elapsed_s = w[1].wall_elapsed_s;
        d.save_checkpoint(&out.join(format!("restart_{:08}_from_{:08}.txt", s2.accepted, w[0].accepted)), &saved)?;
        rows2.write(&out, &format!("restart_from_{:08}", w[0].accepted))?;
        restart.push(state_json(&d, &s2)?);
    }
    let restart_wall = t1.elapsed().as_secs_f64();
    let mut trows = Rows::default();
    trows.emit(&d, &terminal, &case, true)?;
    trows.write(&out, "terminal")?;
    let set_end = |z: &str| text.lines()
        .map(|l| if l.starts_with("end_zbar=") { format!("end_zbar={z}") } else { l.to_string() })
        .collect::<Vec<_>>().join("\n");
    let mut low = cfg.clone();
    low.end_zbar = 0.0;
    let probes = vec![
        ("DriverConfig::read(config.cfg with end_zbar=0.0)", outcome(DriverConfig::read(&set_end("0.0")))),
        ("DriverConfig::read(config.cfg with end_zbar=3.999)", outcome(DriverConfig::read(&set_end("3.999")))),
        ("Driver::new(DriverConfig{end_zbar:0.0,..})", outcome(Driver::new(low))),
        ("AxbiSource::at_redshift(4.0)", outcome(d.source.at_redshift(4.0))),
        ("AxbiSource::at_redshift(3.999)", outcome(d.source.at_redshift(3.999))),
        ("AxbiSource::at_redshift(0.0)", outcome(d.source.at_redshift(0.0))),
        ("AxbiBackground::point_at_scale(0.2)", outcome(d.background.point_at_scale(0.2))),
        ("AxbiBackground::point_at_scale(0.25)", outcome(d.background.point_at_scale(0.25))),
    ];
    let probes = probes.iter().map(|(k, v)| format!("{}:{}", quote(k), v)).collect::<Vec<_>>().join(",");
    let mus = d.source.angular_cells.iter().map(|c| c.mu).collect::<Vec<_>>();
    let wts = d.source.angular_cells.iter().map(|c| c.count_fraction).collect::<Vec<_>>();
    let json = format!(concat!("{{\"schema\":\"htt.r106.rei_native_replay/1\",\"case\":{},\"q_ref\":{},",
        "\"config_end_zbar\":{},\"caps\":{},\"n_h0_cm3\":{},\"n_he0_cm3\":{},\"energies_eV\":{},",
        "\"angular_mu\":{},\"angular_count_fraction\":{},\"start\":{},\"references\":[{}],\"terminal\":{},",
        "\"continuous\":[{}],\"restart\":[{}],\"continuous_wall_s\":{},\"restart_wall_s\":{},",
        "\"probes\":{{{}}},\"log\":[{}]}}\n"),
        quote(&case), num(cfg.q_ref), num(cfg.end_zbar), arr(&caps), num(d.n_h0_cm3), num(d.n_he0_cm3),
        arr(&d.energies), arr(&mus), arr(&wts), state_json(&d, &start)?,
        references.iter().map(|r| state_json(&d, r)).collect::<Result<Vec<_>, _>>()?.join(","),
        state_json(&d, &terminal)?, continuous.join(","), restart.join(","), num(continuous_wall),
        num(restart_wall), probes, log.iter().map(|l| quote(l)).collect::<Vec<_>>().join(","));
    fs::write(out.join("replay.json"), json).map_err(io)?;
    Ok(())
}
'''


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Recorder:
    """Exact command, return code, wall time and peak RSS of every subprocess."""
    def __init__(self, out: Path):
        self.path = out / "COMMANDS.jsonl"
        self.logs = out / "logs"
        self.logs.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()

    def append(self, record: dict) -> None:
        with self.lock, open(self.path, "a") as f:
            f.write(json.dumps(record) + "\n")

    def records(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text().splitlines() if line.strip()]

    def drop(self, prefixes: tuple[str, ...]) -> None:
        """Forget earlier records of the stages being rerun, so COMMANDS.jsonl describes the outputs."""
        keep = [r for r in self.records() if not r["tag"].startswith(prefixes)]
        self.path.write_text("".join(json.dumps(r) + "\n" for r in keep))

    def capture(self, argv, tag, cwd=None, ok=(0,), stdin: bytes | None = None) -> subprocess.CompletedProcess:
        """Run a short read-only command, keep its stdout in memory and record it."""
        argv = [str(a) for a in argv]
        t0 = time.perf_counter()
        r = subprocess.run(argv, cwd=cwd, capture_output=True, input=stdin)
        self.append({"tag": tag, "command": " ".join(argv), "cwd": str(cwd or os.getcwd()),
                     "return_code": r.returncode, "wall_s": round(time.perf_counter() - t0, 3), "maxrss_kB": None,
                     "stdout_sha256": sha256_bytes(r.stdout), "stderr_tail": r.stderr.decode(errors="replace")[-2000:]})
        if r.returncode not in ok:
            raise RuntimeError(f"{tag}: {' '.join(argv)} returned {r.returncode}: {r.stderr[-500:]!r}")
        return r

    def run(self, argv, tag, env=None, cwd=None):
        timing = self.logs / f"{tag}.time"
        stdout, stderr = self.logs / f"{tag}.stdout", self.logs / f"{tag}.stderr"
        full = ["/usr/bin/time", "-f", "%e s %M kB", "-o", str(timing)] + [str(a) for a in argv]
        with open(stdout, "wb") as o, open(stderr, "wb") as e:
            rc = subprocess.run(full, env=env, cwd=cwd, stdout=o, stderr=e).returncode
        wall, rss = None, None
        text = timing.read_text().strip().splitlines() if timing.exists() else []
        if text:
            parts = text[-1].split()
            wall, rss = float(parts[0]), int(parts[2])
        record = {"tag": tag, "command": " ".join(str(a) for a in argv), "cwd": str(cwd or os.getcwd()),
                  "return_code": rc, "wall_s": wall, "maxrss_kB": rss,
                  "stderr_tail": stderr.read_text(errors="replace")[-2000:]}
        self.append(record)
        return record


def git_show(rec: Recorder, relpath: str, tag: str) -> bytes:
    return rec.capture(["git", "-C", REI_REPO, "show", f"{REI_COMMIT}:{relpath}"], tag).stdout


def identity_text(root: Path) -> str:
    return BOUNDARY.join((root / f).read_text() for f in IDENTITY_FILES)


# ----------------------------------------------------------------------------------------------
# Pure helpers (unit-tested in tests/obsstat/test_r106_rei_restart_replay.py)
# ----------------------------------------------------------------------------------------------
def tree_digest(root: Path) -> dict:
    """Hash of every file below root: sha256 of the sorted sha256sum-format manifest."""
    files = {p.relative_to(root).as_posix(): sha256(p) for p in sorted(root.rglob("*")) if p.is_file()}
    manifest = "".join(f"{digest}  {name}\n" for name, digest in sorted(files.items()))
    return {"root": str(root), "n_files": len(files), "sha256": sha256_bytes(manifest.encode()),
            "definition": "sha256 of the sorted '<sha256>  <relative path>\\n' manifest of all files", "files": files}


def find_line(path: Path, needle: str) -> dict | None:
    """First line of a text file that contains needle (1-based), or None."""
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if needle in line:
            return {"file": str(path), "line": number, "text": line.strip()}
    return None


def crate_imports(text: str) -> set[str]:
    """Top-level crate modules a Rust source names through crate::x or crate::{x, y::z}."""
    import re
    names = set(re.findall(r"crate::([A-Za-z_][A-Za-z0-9_]*)", text))
    for group in re.findall(r"crate::\{([^{}]*)\}", text):
        names.update(item.strip().split("::")[0] for item in group.split(",") if item.strip())
    return names


def parse_kv(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def parse_residual_pair(text: str) -> tuple[float, float]:
    first, second = (float(x) for x in text.strip().strip("()").split(","))
    return first, second


def content_binding(ret: dict[str, str], ck: dict, native_residuals: tuple[float, float]) -> dict:
    """Exact equality of the RETURN record with the checkpoint counters/fields and the natively recomputed residuals."""
    fields = {key: int(ret[key]) == ck["counts"][index] for key, index in RETURN_COUNT_FIELDS}
    fields.update({key: float(ret[key]) == ck[ck_key] for key, ck_key in RETURN_FLOAT_FIELDS})
    count_res, energy_res = parse_residual_pair(ret["residuals"])
    fields["residual_count_equals_native_recomputed"] = count_res == native_residuals[0]
    fields["residual_energy_equals_native_recomputed"] = energy_res == native_residuals[1]
    return {"fields_equal": fields, "all_equal": all(fields.values())}


def flrw_q0_age(a_hi: float, a_lo: float = 1e-12, h0: float | None = None, om: float | None = None,
                or_: float | None = None, ol: float | None = None) -> float:
    """Proper time int_{a_lo}^{a_hi} dln a / H_FLRW for an isotropic FLRW law (no shear term)."""
    from scipy.integrate import quad
    h0, om, or_, ol = (H0 if h0 is None else h0, OM if om is None else om, OR if or_ is None else or_,
                       OL if ol is None else ol)

    def inv_h(lna):
        a = math.exp(lna)
        return 1.0 / (h0 * math.sqrt(om / a**3 + or_ / a**4 + ol))
    return quad(inv_h, math.log(a_lo), math.log(a_hi), epsabs=0.0, epsrel=1e-13, limit=800)[0]


def replay_window(start: dict, references: list[dict], a_rows, total_accepted: int, log: list[str]) -> dict:
    """Step regime of the replayed window from the native states and the replayed history rows."""
    end = references[-1]
    a_rows = np.asarray(a_rows, float)
    dln = np.diff(np.log(a_rows))
    steps = end["accepted"] - start["accepted"]
    if dln.size != steps:
        raise ValueError(f"replayed history has {dln.size} steps, counters say {steps}")
    nominal = start["next_dln_a"]
    requested = [start["next_dln_a"]] + [r["next_dln_a"] for r in references]
    body = dln[:-1]
    body_dev = float(np.max(np.abs(body / nominal - 1.0))) if body.size else 0.0
    rejections = end["rejects"] - start["rejects"]
    constant = (rejections == 0 and not log and all(x == nominal for x in requested)
                and body_dev <= CONSTANT_STEP_REL_TOL and dln[-1] <= nominal * (1 + CONSTANT_STEP_REL_TOL))
    return {
        "accepted_start": start["accepted"], "accepted_end": end["accepted"], "accepted_steps_replayed": steps,
        "zbar_start": float(1 / a_rows[0] - 1), "zbar_end": float(1 / a_rows[-1] - 1),
        "fraction_of_run_accepted_steps": steps / total_accepted,
        "rejections_in_window": rejections, "solver_log_entries": len(log),
        "attempts_in_window": end["attempts"] - start["attempts"],
        "attempts_per_accepted_step": (end["attempts"] - start["attempts"]) / steps,
        "comparisons_in_window": end["comparisons"] - start["comparisons"],
        "rhs_evaluations_in_window": end["rhs_evaluations"] - start["rhs_evaluations"],
        "next_dln_a_at_start_middle_end": requested,
        "dln_a_steps_except_final_max_relative_deviation_from_next_dln_a": body_dev,
        "dln_a_final_step": float(dln[-1]), "final_step_over_next_dln_a": float(dln[-1] / nominal),
        "regime": ("CONSTANT_STEP_NO_REJECTION_ENDPOINT_CLIPPED_FINAL_STEP" if constant
                   else "NOT_CONSTANT_STEP_OR_HAS_REJECTIONS"),
        "constant_step_relative_tolerance": CONSTANT_STEP_REL_TOL,
        "branches_not_exercised": (["adaptive reject branch", "step-size change branch"] if constant else []),
    }


def headline_residual(reports: dict[str, dict]) -> dict:
    """Largest difference over every compared field of the diff_report() outputs (zero means bitwise identical)."""
    worst, fields, unequal = 0.0, set(), []
    for label, report in reports.items():
        for key, d in report.items():
            fields.add(key)
            if "difference" in d:
                value, same = abs(d["difference"]), d["difference"] == 0
            elif "max_abs" in d:
                value, same = d["max_abs"], d["n_bitwise_unequal"] == 0
            else:
                value, same = d["abs"], d["bitwise_equal"]
            worst = max(worst, float(value))
            if not same:
                unequal.append(f"{label}:{key}")
    return {"comparisons": sorted(reports), "fields_compared": sorted(fields), "n_fields": len(fields),
            "max_abs_difference_any_field": worst, "all_bitwise_equal": not unequal, "unequal_fields": unequal,
            "includes_ledgers_photons_energy_residual": {"ledgers", "photons", "energy_residual_eV_per_H"} <= fields,
            "note": "max over fields of mixed units; read only as zero versus non-zero"}


def build(out: Path, rec: Recorder) -> dict:
    """Copy the frozen crate into two source epochs, verify identity hashes, compile replay."""
    src_crate = PLUS / "rust/rei_microphysics"
    report = {}
    paired_identity = (CASES["SHEAR_MINUS"]["segment"] / "source_identity.txt").read_text()
    for tag, identity in (("d7676", ID_PLUS), ("4de69", ID_PAIRED)):
        tree = out / "native" / f"tree_{tag}"
        crate = tree / "rust/rei_microphysics"
        if tree.exists():
            shutil.rmtree(tree)
        crate.mkdir(parents=True)
        for name in ("Cargo.toml", "Cargo.lock"):
            shutil.copy2(src_crate / name, crate / name)
        for name in ("src", "examples"):
            shutil.copytree(src_crate / name, crate / name)
        for f in IDENTITY_FILES[-3:]:
            target = (crate / f).resolve()
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2((src_crate / f).resolve(), target)
        replaced = []
        if tag == "4de69":
            parts = paired_identity.split(BOUNDARY)
            if len(parts) != len(IDENTITY_FILES):
                raise ValueError("paired identity record does not split into the 17 identity files")
            for f, text in zip(IDENTITY_FILES, parts):
                if (crate / f).read_text() != text:
                    (crate / f).write_text(text)
                    replaced.append(f)
        got = hashlib.sha256(identity_text(crate).encode()).hexdigest()
        if got != identity:
            raise ValueError(f"source identity mismatch for {tag}: {got}")
        (crate / "examples/rei_restart_replay.rs").write_text(RUST_REPLAY)
        env = dict(os.environ, CARGO_TARGET_DIR=str(out / "native" / f"target_{tag}"))
        r = rec.run(["cargo", "build", "--release", "--offline", "--locked", "-j", "3",
                     "--manifest-path", crate / "Cargo.toml", "--example", "rei_restart_replay"],
                    f"build_{tag}", env=env)
        if r["return_code"] != 0:
            raise RuntimeError(f"cargo build failed for {tag}: {r['stderr_tail']}")
        binary = out / "native" / f"target_{tag}" / "release/examples/rei_restart_replay"
        report[tag] = {"compiled_source_identity_sha256": got, "files_replaced_from_identity_record": replaced,
                       "copied_from": str(src_crate), "replay_example_sha256":
                       hashlib.sha256(RUST_REPLAY.encode()).hexdigest(), "binary": str(binary),
                       "binary_sha256": sha256(binary), "build": r}
    (out / "BUILD.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


EPOCHS = (("d7676", ID_PLUS), ("4de69", ID_PAIRED))


def rustc_of_cached_build(target: Path) -> str | None:
    """rustc -vV text cargo stored in the target directory when it compiled the cached binary."""
    info = target / ".rustc_info.json"
    if not info.exists():
        return None
    for item in json.loads(info.read_text()).get("outputs", {}).values():
        text = item.get("stdout", "")
        if text.startswith("rustc "):
            return text.strip()
    return None


def environment(rec: Recorder) -> dict:
    import pandas
    import scipy
    head = rec.capture(["git", "-C", HTT_BASE, "rev-parse", "HEAD"], "record_htt_base_head").stdout.decode().strip()
    status = rec.capture(["git", "-C", HTT_BASE, "status", "--porcelain", "--untracked-files=no"],
                         "record_htt_base_status").stdout.decode().splitlines()
    rel = SCRIPT.relative_to(HTT_BASE).as_posix()
    tracked = rec.capture(["git", "-C", HTT_BASE, "ls-files", "--error-unmatch", rel], "record_script_tracked",
                          ok=(0, 1)).returncode == 0
    rei_head = rec.capture(["git", "-C", REI_REPO, "rev-parse", "HEAD"], "record_rei_head").stdout.decode().strip()
    rustc = rec.capture(["rustc", "-vV"], "record_rustc_vV").stdout.decode().strip()
    cargo = rec.capture(["cargo", "-V"], "record_cargo_V").stdout.decode().strip()
    return {
        "script": {"path": str(SCRIPT), "sha256": sha256(SCRIPT), "git_tracked_in_htt_base": tracked},
        "htt_base": {"path": str(HTT_BASE), "head": head, "dirty_tracked_files": bool(status),
                     "n_modified_tracked_paths": len(status)},
        "rei_bianchi": {"path": str(REI_REPO), "head": rei_head},
        "python": {"version": sys.version, "executable": sys.executable,
                   "implementation": platform.python_implementation()},
        "libraries": {"numpy": np.__version__, "scipy": scipy.__version__, "pandas": pandas.__version__},
        "platform": platform.platform(),
        "toolchain_now": {"rustc_vV": rustc, "cargo_V": cargo},
        "env": {k: os.environ.get(k) for k in ("PYTHONPATH", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS",
                                               "MKL_NUM_THREADS", "PYTHONDONTWRITEBYTECODE")},
    }


def record_build(out: Path, rec: Recorder) -> dict:
    """Add script/environment/toolchain identity and full src/ tree hashes to BUILD.json.

    Reads the cached epoch trees, binaries and target/.rustc_info.json; nothing is copied or compiled.
    Fails closed if a cached tree, example or binary no longer matches the build record.
    """
    path = out / "BUILD.json"
    report = json.loads(path.read_text())
    src_crate = PLUS / "rust/rei_microphysics"
    origin_src = tree_digest(src_crate / "src")
    replay_sha = sha256_bytes(RUST_REPLAY.encode())
    covered = {f for f in IDENTITY_FILES if f.startswith("src/")}
    trees = {}
    for tag, identity in EPOCHS:
        entry = report[tag]
        crate = out / "native" / f"tree_{tag}" / "rust/rei_microphysics"
        src = tree_digest(crate / "src")
        identity_now = sha256_bytes(identity_text(crate).encode())
        binary_now = sha256(Path(entry["binary"]))
        checks = {
            "identity_hash_recomputed_equals_record": identity_now == identity == entry["compiled_source_identity_sha256"],
            "binary_sha256_recomputed_equals_record": binary_now == entry["binary_sha256"],
            "replay_example_in_tree_equals_this_script":
                sha256(crate / "examples/rei_restart_replay.rs") == replay_sha == entry["replay_example_sha256"],
        }
        if not all(checks.values()):
            raise ValueError(f"{tag}: cached build no longer matches its record: {checks}")
        trees[tag] = src["files"]
        entry["post_build_record"] = {
            "src_tree": src, "examples_tree": tree_digest(crate / "examples"),
            "cargo_toml_sha256": sha256(crate / "Cargo.toml"), "cargo_lock_sha256": sha256(crate / "Cargo.lock"),
            "identity_hash_recomputed": identity_now, "binary_sha256_recomputed": binary_now, "checks": checks,
            "compiled_src_files_not_in_identity_hash":
                sorted(f"src/{n}" for n in src["files"] if f"src/{n}" not in covered),
            "src_files_differing_from_copy_origin_now":
                sorted(n for n in set(src["files"]) | set(origin_src["files"])
                       if src["files"].get(n) != origin_src["files"].get(n)),
            "rustc_that_built_cached_binary": rustc_of_cached_build(out / "native" / f"target_{tag}"),
            "identity_files_importing_uncovered_modules": {
                f: sorted(m for m in crate_imports((crate / f).read_text())
                          if f"{m}.rs" in src["files"] and f"src/{m}.rs" not in covered)
                for f in sorted(covered)
                if any(f"{m}.rs" in src["files"] and f"src/{m}.rs" not in covered
                       for m in crate_imports((crate / f).read_text()))},
            "construction": (
                "copy of the copy-origin crate with files_replaced_from_identity_record grafted in; src files outside "
                "IDENTITY_FILES come from the copy origin and no record binds them to the source compiled by the "
                "original runs; agreement of the replay with the original checkpoints is functional evidence over "
                "the replayed window, not a hash binding"),
        }
    a, b = trees["d7676"], trees["4de69"]
    paired_record = CASES["SHEAR_MINUS"]["segment"] / "source_identity.txt"
    report.update({
        "schema": "htt.r106.rei_build/2",
        "script_sha256": sha256(SCRIPT),
        "mode": ("record stage: no copy and no compilation; the epoch trees, binaries and target/.rustc_info.json "
                 "are the cached outputs of the build stage"),
        "environment": environment(rec),
        "src_files_differing_between_epochs": sorted(n for n in set(a) | set(b) if a.get(n) != b.get(n)),
        "identity_hash_scope": {
            "n_identity_files": len(IDENTITY_FILES), "n_src_files_covered": len(covered),
            "n_compiled_src_files": {tag: len(trees[tag]) for tag, _ in EPOCHS},
            "note": ("The source identity hash covers only the listed IDENTITY_FILES; the compiled crate contains "
                     "more src/ files (per epoch: post_build_record.compiled_src_files_not_in_identity_hash). "
                     "post_build_record.src_tree.sha256 hashes the full compiled src/ tree.")},
        "input_sha256": {f"tree:{src_crate / 'src'}": origin_src["sha256"],
                         str(src_crate / "Cargo.toml"): sha256(src_crate / "Cargo.toml"),
                         str(src_crate / "Cargo.lock"): sha256(src_crate / "Cargo.lock"),
                         str(paired_record): sha256(paired_record)},
        "review_corrections": REVIEW_CORRECTIONS,
    })
    report["commands"] = [r for r in rec.records() if r["tag"].startswith(("build_", "record_"))]
    path.write_text(json.dumps(report, indent=2) + "\n")
    return report


def caps_for(case: str) -> list[float]:
    seg = CASES[case]["segment"]
    cfg = dict(line.split("=", 1) for line in (seg / "config.cfg").read_text().split() if "=" in line)
    caps = [float(cfg["max_steps"]), float(cfg["max_attempts"]), float(cfg["max_rhs"]), float(cfg["max_wall_s"])]
    over = json.loads((seg / "effective_resource_overrides.json").read_text())
    for i, key in enumerate(("max_steps", "max_attempts", "max_rhs", "max_wall_s")):
        if key in over:
            caps[i] = float(over[key])
    return caps


def replay_case(case: str, out: Path, rec: Recorder, build_report: dict) -> dict:
    seg = CASES[case]["segment"]
    tag = "d7676" if CASES[case]["identity"] == ID_PLUS else "4de69"
    if (seg / "source_identity.txt").exists() and sha256(seg / "source_identity.txt") != CASES[case]["identity"]:
        raise ValueError(f"{case}: segment source identity differs from the selected build")
    target = out / "replay" / case
    if target.exists():
        shutil.rmtree(target)
    argv = [build_report[tag]["binary"], "--config", seg / "config.cfg", "--case", case,
            "--start", seg / f"checkpoints/{START:08d}.txt",
            "--references", f"{seg / f'checkpoints/{MIDDLE:08d}.txt'},{seg / f'checkpoints/{TERMINAL:08d}.txt'}",
            "--terminal", seg / "checkpoint.txt", "--caps", ",".join(repr(c) for c in caps_for(case)),
            "--out", target]
    return rec.run(argv, f"replay_{case}")


def tail_lines(path: Path, count: int) -> list[str]:
    with open(path, "rb") as f:
        f.seek(0, 2)
        end = f.tell()
        size, data = 1 << 16, b""
        while True:
            start = max(0, end - size)
            f.seek(start)
            data = f.read(end - start)
            if data.count(b"\n") > count or start == 0:
                break
            size *= 2
    lines = data.decode().splitlines()
    return lines[-count:]


def parse_checkpoint(path: Path) -> dict:
    lines = path.read_text().splitlines()
    if len(lines) != 6 or lines[0] != "AXBI_CHECKPOINT_V2":
        raise ValueError(f"{path}: not AXBI_CHECKPOINT_V2")
    v = [float(x) for x in lines[1].split()]
    return {"a": v[0], "time_s": v[1], "b": v[2], "x_HII": v[3], "x_HeII": v[4], "x_HeIII": v[5],
            "w_erg_per_H": v[6], "next_dln_a": v[7], "max_newton_residual": v[8], "last_error": v[9],
            "wall_elapsed_s": v[10], "counts": [int(x) for x in lines[2].split()],
            "ledgers": [float(x) for x in lines[3].split()], "photons": np.array([float(x) for x in lines[4].split()]),
            "initial_energy_eV_per_H": float(lines[5])}


def hubble(a, q_ref):
    hf = H0 * np.sqrt(OM / a**3 + OR / a**4 + OL)
    href = H0 * math.sqrt(OM / A_REF**3 + OR / A_REF**4 + OL)
    s = q_ref * href * (A_REF / a) ** 3
    return np.hypot(hf, s), s, hf


def diff_report(replay: dict, ref: dict) -> dict:
    out = {}
    for key, value in ref.items():
        if key == "wall_elapsed_s":
            continue
        r = replay[key]
        if key in COUNTS:
            out[key] = {"difference": r - value, "unit": "count"}
        elif isinstance(value, list):
            d = np.abs(np.asarray(r, float) - np.asarray(value, float))
            scale = np.maximum(np.abs(np.asarray(value, float)), 1e-300)
            out[key] = {"max_abs": float(d.max()), "max_rel": float((d / scale).max()),
                        "n_bitwise_unequal": int(np.sum(np.asarray(r, float) != np.asarray(value, float))),
                        "unit": UNITS.get(key, "")}
        else:
            out[key] = {"abs": abs(r - value), "rel": abs(r - value) / max(abs(value), 1e-300),
                        "bitwise_equal": r == value, "unit": UNITS.get(key, "")}
    return out


def rows_compare(replay_file: Path, original: Path, per_state: int) -> dict:
    new = replay_file.read_text().splitlines()
    old = tail_lines(original, len(new))
    unequal = [i for i, (x, y) in enumerate(zip(new, old)) if x != y]
    report = {"rows": len(new), "rows_bytewise_identical": len(new) - len(unequal),
              "states": len(new) // per_state, "original_tail_of": str(original)}
    if unequal:
        worst = 0.0
        for i in unequal:
            for x, y in zip(new[i].split(","), old[i].split(",")):
                try:
                    worst = max(worst, abs(float(x) - float(y)))
                except ValueError:
                    pass
        report["max_abs_numeric_difference_in_unequal_rows"] = worst
    return report


def spectra_compare(replay_file: Path, original: Path, nodes: int) -> dict:
    new = replay_file.read_text().splitlines()
    times = sorted({line.split(",")[3] for line in new})
    old = tail_lines(original, nodes * 8)
    report = {}
    for t in times:
        a = [x for x in new if x.split(",")[3] == t]
        b = [x for x in old if x.split(",")[3] == t]
        report[t] = {"replay_rows": len(a), "original_rows_found": len(b),
                     "bytewise_identical": a == b[-len(a):] if b else None}
    return report


def history_columns(path: Path, cols):
    import pandas as pd
    return pd.read_csv(path, usecols=cols, float_precision="round_trip")


def native_history(case: str, plus_manifest: dict):
    """Full native rows z=20..4. SHEAR_PLUS is composed from its three admitted segments."""
    cols = ["a", "time_s", "H_per_s", "ne_proper_cm3", "x_HII", "x_HeII", "x_HeIII", "temperature_K"]
    meta = {}
    if CASES[case]["composed"] is not None:
        path = CASES[case]["composed"] / "history.csv"
        meta["files"] = {str(path): sha256(path)}
        frame = history_columns(path, cols)
    else:
        import pandas as pd
        manifest = plus_manifest
        parts = []
        meta["files"] = {}
        for k, item in enumerate(manifest["inputs"]):
            path = Path(item["source_remote_path"])
            digest = sha256(path)
            if digest != item["sha256"]:
                raise ValueError(f"SHEAR_PLUS segment hash mismatch {path}")
            meta["files"][str(path)] = digest
            full = pd.read_csv(path, float_precision="round_trip")
            if k:
                if not full.iloc[0].equals(parts[-1][1].iloc[-1]):
                    raise ValueError("SHEAR_PLUS segment boundary row differs")
                full = full.iloc[1:item["added_rows"] + 1]
            if len(full) != item["added_rows"]:
                raise ValueError("SHEAR_PLUS added-row count differs")
            parts.append((k, full))
        frame = pd.concat([p[1] for p in parts], ignore_index=True)[cols]
    if len(frame) != 312238:
        raise ValueError(f"{case}: native history row count {len(frame)}")
    return frame, meta


def trapezoid(y, x):
    return float(np.sum(0.5 * (y[1:] + y[:-1]) * np.diff(x)))


def cubic_spline_integral(y, x) -> float | None:
    """Integral of the not-a-knot cubic spline through (x, y); None if x is not strictly increasing."""
    from scipy.interpolate import CubicSpline
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.size < 4 or not np.all(np.diff(x) > 0):
        return None
    return float(CubicSpline(x, y).integrate(x[0], x[-1]))


def clock_h_consistency(frame) -> dict:
    """Clock/H consistency (dt/dN = 1/H) and quadrature-error estimate on stored native rows.

    c sigma_T int n_e dt (stored time column) and c sigma_T int n_e/H dN (stored H column) share n_e,
    sigma_T and H, so their agreement tests only that the stored clock integrates dN/H, plus the
    trapezoid discretisation. It cannot detect an error in n_e, sigma_T or H and is not a validation
    of the Thomson depth itself.
    """
    a = np.asarray(frame["a"], float)
    t = np.asarray(frame["time_s"], float)
    H = np.asarray(frame["H_per_s"], float)
    ne = np.asarray(frame["ne_proper_cm3"], float) * 1e6
    N = np.log(a)
    k = C_SI * SIGMA_T_SI
    idx2 = np.r_[np.arange(0, len(a), 2), [len(a) - 1]] if (len(a) - 1) % 2 else np.arange(0, len(a), 2)
    it, it2 = k * trapezoid(ne, t), k * trapezoid(ne[idx2], t[idx2])
    iN, iN2 = k * trapezoid(ne / H, N), k * trapezoid((ne / H)[idx2], N[idx2])
    rt, rN = it + (it - it2) / 3, iN + (iN - iN2) / 3
    st, sN = cubic_spline_integral(k * ne, t), cubic_spline_integral(k * ne / H, N)

    def rel(x, ref):
        return None if x is None or ref is None else (x - ref) / ref
    return {
        "rows": len(a), "zbar_interval": [float(1 / a[0] - 1), float(1 / a[-1] - 1)],
        "unit": "dimensionless (c sigma_T int n_e dt)",
        "c_sigmaT_int_ne_dt": {"native_rows": it, "every_second_row": it2, "richardson": rt, "cubic_spline": st},
        "int_c_sigmaT_ne_over_H_dN": {"native_rows": iN, "every_second_row": iN2, "richardson": rN,
                                      "cubic_spline": sN},
        "clock_H_consistency": {
            "dt_form_minus_dN_form_native_rows": it - iN, "relative_native_rows": (it - iN) / iN,
            "dt_form_minus_dN_form_richardson": rt - rN, "relative_richardson": (rt - rN) / rN,
            "tests": "stored time column t(N) integrates dN/H of the stored H column (dt/dN = 1/H)",
            "does_not_test": "n_e, sigma_T or H themselves (shared by both forms); not a validation of tau"},
        "quadrature_error_estimate": {
            "dt_form_native_rows_minus_richardson_relative": rel(it, rt),
            "dN_form_native_rows_minus_richardson_relative": rel(iN, rN),
            "dt_form_native_rows_minus_cubic_spline_relative": rel(it, st),
            "dN_form_native_rows_minus_cubic_spline_relative": rel(iN, sN),
            "dN_form_richardson_minus_cubic_spline_relative": rel(rN, sN),
            "note": "native-row trapezoid error scale; the dt-vs-dN agreement above is of the same order"},
    }


def tanh_foreground(case: str, xe_restart: float, nh0_cm3: float) -> dict:
    from scipy.integrate import quad
    from bass.recombination.reionization import ReionizationParameters, tanh_reionization_xe
    q = CASES[case]["q_ref"]
    out = {}
    k = C_SI * SIGMA_T_SI * nh0_cm3 * 1e6
    for name, params in (("H_and_first_He", ReionizationParameters(include_HeII=False)),
                         ("with_HeII_to_HeIII", ReionizationParameters())):
        def xe(z):
            return float(tanh_reionization_xe(z, params, F_HE))

        def integrand(z):
            return (1 + z) ** 2 * xe(z) / float(hubble(1 / (1 + z), q)[0])
        tau_quad = k * quad(integrand, 0.0, 4.0, epsabs=0.0, epsrel=1e-13, limit=400)[0]
        z = np.linspace(0, 4, 2049)
        y = np.array([integrand(v) for v in z])
        tau_trap = k * trapezoid(y, z)
        # Proper-time form on the same foreground: tau = c sigma_T int n_e dt along increasing
        # time from the z=4 junction to z=0; t(N) is the trapezoid of 1/H on the same N grid.
        def forms(points):
            Nf = np.linspace(-math.log(5.0), 0.0, points)
            af = np.exp(Nf)
            zf = 1 / af - 1
            Hf = hubble(af, q)[0]
            tf = np.concatenate([[0.0], np.cumsum(0.5 * (1 / Hf[1:] + 1 / Hf[:-1]) * np.diff(Nf))])
            nef = nh0_cm3 * 1e6 * (1 + zf) ** 3 * np.array([xe(v) for v in zf])
            return C_SI * SIGMA_T_SI * trapezoid(nef, tf), C_SI * SIGMA_T_SI * trapezoid(nef / Hf, Nf)
        (tau_t, tau_N), (tau_t2, tau_N2) = forms(16385), forms(8193)
        rt, rN = tau_t + (tau_t - tau_t2) / 3, tau_N + (tau_N - tau_N2) / 3
        x4 = xe(4.0)
        out[name] = {"tau_0_to_4_adaptive": tau_quad, "tau_0_to_4_trapezoid_2049": tau_trap,
                     "transmission_exp_minus_tau": math.exp(-tau_quad),
                     "c_sigmaT_int_ne_dt": {"N_points_16385": tau_t, "N_points_8193": tau_t2, "richardson": rt},
                     "int_c_sigmaT_ne_over_H_dN": {"N_points_16385": tau_N, "N_points_8193": tau_N2, "richardson": rN},
                     "proper_time_vs_N_form_relative_16385": (tau_t - tau_N) / tau_N,
                     "proper_time_vs_N_form_relative_richardson": (rt - rN) / rN,
                     "richardson_N_form_minus_adaptive": rN - tau_quad,
                     "xe_tanh_at_z4": x4, "xe_restart_at_z4": xe_restart,
                     "junction_charge_mismatch_restart_minus_tanh": xe_restart - x4,
                     "junction_relative_mismatch": (xe_restart - x4) / x4}
    out["role"] = "sensitivity only: common isotropic FLRW+tanh foreground, not a native continuation"
    out["claim_class"] = "CONDITIONAL_SENSITIVITY (external tanh convention; not a model prediction)"
    out["H_model"] = ("hypot(H_FLRW, q_ref H_FLRW(a_ref)(a_ref/a)^3) evaluated at a > a_end = 0.2: an extension of the "
                      "locked background formula outside its locked domain [a_ref, a_end], used for this sensitivity only")
    out["form_comparison_note"] = ("proper_time_vs_N_form_* compares two quadratures of one integrand (t is built "
                                   "from 1/H on the same grid); it is a quadrature check, not a tau validation")
    return out


def restart_inventory(case: str, rep: dict, out: Path) -> dict:
    """Independent Python reconstruction of the restart state against the native outputs."""
    from scipy.integrate import quad
    seg = CASES[case]["segment"]
    ck = parse_checkpoint(seg / "checkpoint.txt")
    term = rep["terminal"]
    for key in ("a", "time_s", "b", "x_HII", "x_HeII", "x_HeIII", "w_erg_per_H"):
        if ck[key] != term[key]:
            raise ValueError(f"{case}: python/rust checkpoint parse differs at {key}")
    if not np.array_equal(ck["photons"], np.asarray(term["photons"])):
        raise ValueError(f"{case}: photon stock parse differs")
    a, q = ck["a"], CASES[case]["q_ref"]
    nh = rep["n_h0_cm3"] / a**3
    nhe = rep["n_he0_cm3"] / a**3
    xe = ck["x_HII"] + F_HE * (ck["x_HeII"] + 2 * ck["x_HeIII"])
    ne = nh * ck["x_HII"] + nhe * (ck["x_HeII"] + 2 * ck["x_HeIII"])
    temp = 2 * ck["w_erg_per_H"] * nh / (3 * KB_ERG_K * (nh + nhe + ne))
    header = "case_id,q_ref,Sigma,time_s,a,zbar,b,H_per_s,s_per_s,x_HII,x_HeII,x_HeIII,nH_proper_cm3,ne_proper_cm3,temperature_K,Gamma_HI_per_s,Gamma_HeI_per_s,Gamma_HeII_per_s,photon_n_per_H,photon_u_eV_per_H,J0_photon_u_eV_per_H,J1_photon_u_eV_per_H,J2_photon_u_eV_per_H,x_HI,x_HeI".split(",")
    last = dict(zip(header, tail_lines(seg / "history.csv", 1)[0].split(",")))
    hist = {k: float(v) for k, v in last.items() if k != "case_id"}
    abund = [line.split(",") for line in tail_lines(seg / "abundances.csv", 6)]
    dens = {row[5]: float(row[9]) for row in abund}
    energies = np.asarray(rep["energies_eV"])
    ph = ck["photons"].reshape(len(rep["angular_mu"]), len(energies))
    n_ph, u_ph = float(ph.sum()), float((ph * energies).sum())
    L = dict(zip(LEDGER_NAMES, ck["ledgers"]))
    x_hii_ledger = 2e-4 + L["photo_events_0_per_H"] + L["CI_events_0_per_H"] - L["RR_events_0_per_H"]
    net2 = L["photo_events_2_per_H"] + L["CI_events_2_per_H"] - L["RR_events_2_per_H"]
    net1 = L["photo_events_1_per_H"] + L["CI_events_1_per_H"] - L["RR_events_1_per_H"] - L["DR_events_per_H"]
    H, s, hf = hubble(a, q)

    def inv_h(lna):
        return 1.0 / float(hubble(math.exp(lna), q)[0])

    def s_over_h(lna):
        h, sv, _ = hubble(math.exp(lna), q)
        return float(sv / h)
    t_quad = quad(inv_h, math.log(A_REF), math.log(a), epsabs=0.0, epsrel=5e-14, limit=400)[0]
    b_quad = quad(s_over_h, math.log(A_REF), math.log(a), epsabs=0.0, epsrel=5e-14, limit=400)[0]
    bands = {"13.6-24.59 eV": (energies >= 13.6) & (energies < 24.59),
             "24.59-54.42 eV": (energies >= 24.59) & (energies < 54.42),
             "54.42-100 eV": energies >= 54.42}
    return {
        "restart_file": str(seg / "checkpoint.txt"), "restart_sha256": sha256(seg / "checkpoint.txt"),
        "native_read_checkpoint": "PASS (frozen reader: exact background clock/b identity, ledgers within 1e-8)",
        "a": a, "zbar": 1 / a - 1, "accepted_steps": ck["counts"][0],
        "charge": {
            "x_HII": ck["x_HII"], "x_HeII": ck["x_HeII"], "x_HeIII": ck["x_HeIII"],
            "xe_per_H": xe, "ne_proper_cm3": ne, "nH_proper_cm3": nh, "nHe_proper_cm3": nhe,
            "charge_neutrality": ("IMPOSED_BY_EOS: n_e = n_H x_HII + n_He (x_HeII + 2 x_HeIII); the model has no "
                                  "independent electron variable, so the electron_formula_* fields below are "
                                  "bookkeeping identities that cannot fail, not neutrality tests"),
            "electron_formula_python_minus_native_eos_cm3": ne - term["ne_proper_cm3"],
            "electron_formula_python_minus_history_last_row_cm3": ne - hist["ne_proper_cm3"],
            "history_row_time_equals_restart": hist["time_s"] == ck["time_s"],
            "electron_row_formula_consistency_cm3":
                dens["electron"] - (dens["H_II"] + dens["He_II"] + 2 * dens["He_III"]),
            "ledger_closures_note": ("ledger_closure_* compare the state fractions with separately accumulated "
                                     "event ledgers (initial value + photo + CI - RR [- DR]); these are "
                                     "numerical bookkeeping checks"),
            "ledger_closure_x_HII_minus_events": ck["x_HII"] - x_hii_ledger,
            "ledger_closure_fHe_x_HeIII_minus_events_per_H": F_HE * ck["x_HeIII"] - net2,
            "ledger_closure_fHe_x_HeII_minus_events_per_H": F_HE * ck["x_HeII"] - (net1 - net2),
            "absorbed_minus_sum_photo_events_per_H": L["absorbed_N_per_H"] - sum(L[f"photo_events_{i}_per_H"] for i in range(3)),
            "units": "fractions per H or per He; densities cm^-3 proper; ledger closures per H"},
        "temperature": {
            "w_erg_per_H": ck["w_erg_per_H"], "T_K_python_eos": temp, "T_K_native_eos": term["temperature_K"],
            "T_K_history_last_row": hist["temperature_K"], "python_minus_native_K": temp - term["temperature_K"],
            "history_minus_native_K": hist["temperature_K"] - term["temperature_K"]},
        "proper_time": {
            "time_s_restart": ck["time_s"], "time_s_independent_quad": t_quad,
            "restart_minus_quad_s": ck["time_s"] - t_quad, "relative": (ck["time_s"] - t_quad) / t_quad,
            "b_restart": ck["b"], "b_independent_quad": b_quad, "b_restart_minus_quad": ck["b"] - b_quad,
            "clock_definition": ("checkpoint stores elapsed proper seconds since mean z=20 (SCENARIO_LOCK "
                                 "clock.origin); no absolute age is stored or reported per case "
                                 "(SCENARIO_LOCK clock.absolute_cosmic_age_s = null)")},
        "expansion": {"H_per_s_python": float(H), "H_per_s_native": term["H_per_s"],
                      "H_per_s_history": hist["H_per_s"], "s_per_s_python": float(s),
                      "s_per_s_native": term["s_per_s"], "s_per_s_history": hist["s_per_s"],
                      "H_python_minus_native_relative": float(H / term["H_per_s"] - 1),
                      "stored_in_checkpoint": False,
                      "note": "H and s are not checkpoint fields; the frozen background recomputes them from a and q_ref"},
        "photons": {
            "nodes": int(ck["photons"].size), "angles": len(rep["angular_mu"]), "energy_nodes": len(energies),
            "photon_n_per_H": n_ph, "photon_u_eV_per_H": u_ph,
            "n_minus_history_per_H": n_ph - hist["photon_n_per_H"], "u_minus_history_eV_per_H": u_ph - hist["photon_u_eV_per_H"],
            "n_minus_native_per_H": n_ph - term["photon_n_per_H"], "u_minus_native_eV_per_H": u_ph - term["photon_u_eV_per_H"],
            "moments_J0_J1_J2_eV_per_H": term["moments_eV_per_H"],
            "count_ledger_residual_per_H": term["photon_count_residual_per_H"],
            "augmented_energy_residual_eV_per_H": term["energy_residual_eV_per_H"],
            "initial_energy_reference_eV_per_H": ck["initial_energy_eV_per_H"],
            "photon_n_per_H_by_band": {k: float(ph[:, m].sum()) for k, m in bands.items()},
            "photon_n_per_H_by_angle_mu": dict(zip([repr(x) for x in rep["angular_mu"]], ph.sum(axis=1).tolist())),
            "source_N_per_H": L["source_N_per_H"], "absorbed_N_per_H": L["absorbed_N_per_H"],
            "boundary_N_per_H": L["boundary_N_per_H"]},
        "claim_class": ("CONDITIONAL_MODEL_OUTPUT (restart-state values of the locked, non-admitted scenario); "
                        "python-vs-native and quad-vs-stored differences are numerical consistency checks"),
    }


def git_hash_anchors(rec: Recorder, shas: dict[str, str]) -> dict:
    """Blobs, paths and ref tips of rei_bianchi that contain each checkpoint sha256 (object-store scan, read-only)."""
    t0 = time.perf_counter()
    oids = []
    inventory = rec.capture(["git", "-C", REI_REPO, "cat-file", "--batch-all-objects",
                             "--batch-check=%(objectname) %(objecttype) %(objectsize)"], "analyze_git_blob_inventory")
    for line in inventory.stdout.decode().splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[1] == "blob" and int(parts[2]) < ANCHOR_BLOB_LIMIT_BYTES:
            oids.append(parts[0])
    patterns = {case: sha.encode() for case, sha in shas.items()}
    hits: dict[str, list[str]] = {case: [] for case in shas}
    argv = ["git", "-C", str(REI_REPO), "cat-file", "--batch"]
    proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def feed():
        proc.stdin.write(("\n".join(oids) + "\n").encode())
        proc.stdin.close()
    feeder = threading.Thread(target=feed, daemon=True)
    feeder.start()
    scanned = 0
    for oid in oids:
        header = proc.stdout.readline().split()
        if len(header) != 3 or header[0].decode() != oid:
            proc.kill()
            raise RuntimeError(f"git cat-file --batch out of step at {oid}: {header!r}")
        data = proc.stdout.read(int(header[2]))
        proc.stdout.read(1)
        scanned += len(data)
        for case, pattern in patterns.items():
            if pattern in data:
                hits[case].append(oid)
    feeder.join()
    rc = proc.wait()
    rec.append({"tag": "analyze_git_blob_scan", "command": " ".join(argv) + f" <stdin: {len(oids)} blob ids>",
                "cwd": os.getcwd(), "return_code": rc, "wall_s": round(time.perf_counter() - t0, 3),
                "maxrss_kB": None, "stderr_tail": ""})
    if rc != 0:
        raise RuntimeError("git cat-file --batch failed")
    names: dict[str, str] = {}
    for line in rec.capture(["git", "-C", REI_REPO, "rev-list", "--all", "--objects"],
                            "analyze_git_object_paths").stdout.decode().splitlines():
        oid, _, path = line.partition(" ")
        if path:
            names.setdefault(oid, path)
    all_refs = [line.split() for line in rec.capture(
        ["git", "-C", REI_REPO, "for-each-ref", "--format=%(refname) %(objectname)"],
        "analyze_git_refs").stdout.decode().splitlines() if line.strip()]
    peeled = rec.capture(["git", "-C", REI_REPO, "cat-file", "--batch-check=%(objectname)"], "analyze_git_ref_trees",
                         stdin="".join(f"{ref}^{{tree}}\n" for ref, _ in all_refs).encode()).stdout.decode().splitlines()
    if len(peeled) != len(all_refs):
        raise RuntimeError("git cat-file --batch-check answer count differs from ref count")
    refs = [(ref, target, tree) for (ref, target), tree in zip(all_refs, peeled) if len(tree) == 40]
    rei_tree = rec.capture(["git", "-C", REI_REPO, "rev-parse", f"{REI_COMMIT}^{{tree}}"],
                           "analyze_git_rei_commit_tree").stdout.decode().strip()
    wanted = {oid for found in hits.values() for oid in found}
    trees = sorted({tree for _, _, tree in refs} | {rei_tree})
    t1, failures = time.perf_counter(), 0
    located: dict[str, list[tuple[str, str]]] = {}
    for tree in trees:
        r = subprocess.run(["git", "-C", str(REI_REPO), "ls-tree", "-r", "--full-tree", tree], capture_output=True)
        failures += r.returncode != 0
        located[tree] = []
        for line in r.stdout.decode(errors="replace").splitlines():
            meta, _, path = line.partition("\t")
            parts = meta.split()
            if len(parts) == 3 and parts[1] == "blob" and parts[2] in wanted:
                located[tree].append((parts[2], path))
    rec.append({"tag": "analyze_git_ls_tree_ref_tips",
                "command": f"git -C {REI_REPO} ls-tree -r --full-tree <tree>  (for {len(trees)} unique ref-tip trees "
                           "of all refs and REI_COMMIT)",
                "cwd": os.getcwd(), "return_code": int(failures > 0), "wall_s": round(time.perf_counter() - t1, 3),
                "maxrss_kB": None, "stderr_tail": ""})
    if failures:
        raise RuntimeError(f"git ls-tree failed for {failures} trees")
    per_case = {}
    for case, found in hits.items():
        found_set = set(found)
        tips: dict[tuple[str, str], list[tuple[str, str]]] = {}
        for ref, commit, tree in refs:
            for oid, path in located[tree]:
                if oid in found_set:
                    tips.setdefault((path, oid), []).append((ref, commit))
        at_rei = sorted(path for oid, path in located[rei_tree] if oid in found_set)
        anchors = [{"path": path, "blob": oid, "n_ref_tips": len(v),
                    "ref_tips_by_namespace": {ns: sum(1 for r, _ in v if r.split("/")[1] == ns)
                                              for ns in sorted({r.split("/")[1] for r, _ in v})},
                    "ref_tips_first5": [{"ref": r, "target": c} for r, c in sorted(v)[:5]]}
                   for (path, oid), v in sorted(tips.items())]
        per_case[case] = {"checkpoint_sha256": shas[case], "n_blobs_containing_sha256": len(found),
                          "blobs": [{"blob": oid, "first_seen_path": names.get(oid)} for oid in sorted(found)],
                          "git_anchored_at_REI_COMMIT": bool(at_rei), "REI_COMMIT_paths": at_rei,
                          "anchored_at_some_ref_tip": bool(anchors),
                          "anchored_at_branch_tip_heads_or_remotes": any(
                              ns in ("heads", "remotes") for x in anchors for ns in x["ref_tips_by_namespace"]),
                          "ref_namespaces_with_anchor": sorted({ns for x in anchors for ns in x["ref_tips_by_namespace"]}),
                          "ref_tip_anchors": anchors}
    return {"search": {"scope": (f"every blob object smaller than {ANCHOR_BLOB_LIMIT_BYTES} bytes in the rei_bianchi "
                                 "object store, then every path holding a matching blob in the tip trees of all "
                                 "refs (heads, remotes, tags, archive, codex) and REI_COMMIT"),
                       "n_blobs_scanned": len(oids), "bytes_scanned": scanned, "n_refs": len(all_refs),
                       "n_refs_with_tree": len(refs),
                       "n_unique_tip_trees": len(trees), "wall_s": round(time.perf_counter() - t0, 3)},
            "cases": per_case}


def rei_commit_ancestry(rec: Recorder) -> dict:
    head = rec.capture(["git", "-C", REI_REPO, "rev-parse", "HEAD"], "analyze_rei_head").stdout.decode().strip()
    ancestor = rec.capture(["git", "-C", REI_REPO, "merge-base", "--is-ancestor", REI_COMMIT, "HEAD"],
                           "analyze_rei_commit_is_ancestor", ok=(0, 1)).returncode == 0
    refs = rec.capture(["git", "-C", REI_REPO, "branch", "-a", "--contains", REI_COMMIT, "--format=%(refname)"],
                       "analyze_rei_commit_containing_refs").stdout.decode().split()
    return {"rei_commit": REI_COMMIT, "rei_bianchi_head": head, "rei_commit_is_ancestor_of_head": ancestor,
            "refs_containing_rei_commit": sorted(refs)}


def tracked_at(rec: Recorder, path: Path, tag: str) -> dict:
    rel = path.relative_to(REI_REPO).as_posix()
    index = rec.capture(["git", "-C", REI_REPO, "ls-files", "--error-unmatch", rel], tag + "_index", ok=(0, 1))
    commit = rec.capture(["git", "-C", REI_REPO, "cat-file", "-e", f"{REI_COMMIT}:{rel}"], tag + "_rei_commit",
                         ok=(0, 128))
    return {"tracked_in_rei_bianchi_index": index.returncode == 0, "present_at_REI_COMMIT": commit.returncode == 0}


def z_below_4_blockers(out: Path, rec: Recorder) -> dict:
    """Independent blockers of a native z<4 continuation, with source lines found now in both compiled epochs."""
    needles = {
        "axbi_driver.rs": {"validate_end_zbar_domain": "!(4.0..20.0).contains(&self.end_zbar)",
                           "config_read_calls_validate": "c.validate()?",
                           "driver_new_calls_validate": "config.validate()?",
                           "a_end_derived_from_config": "let a_end = 1.0 / (1.0 + config.end_zbar)"},
        "axbi_sources.rs": {"source_id": "pub const SOURCE_ID",
                            "source_redshift_support": "pub const REDSHIFT_SUPPORT",
                            "source_at_redshift_guard": "!(4.0..=20.0).contains(&zbar)"},
        "axbi_background.rs": {"background_scale_domain_guard": "if a < self.a_ref || a > self.a_end"},
    }
    lines = {}
    for tag, _ in EPOCHS:
        crate = out / "native" / f"tree_{tag}" / "rust/rei_microphysics"
        lines[tag] = {}
        for fname, items in needles.items():
            for key, needle in items.items():
                hit = find_line(crate / "src" / fname, needle)
                if hit is None:
                    raise ValueError(f"{tag}: {needle!r} not found in {fname}")
                lines[tag][key] = hit

    def pick(*keys):
        return {tag: {k: lines[tag][k] for k in keys} for tag, _ in EPOCHS}
    lock_path = out / "native" / "tree_d7676" / LOCK_REL
    lock = json.loads(lock_path.read_text())
    lock_git_sha = sha256_bytes(git_show(rec, LOCK_REL, "analyze_git_show_scenario_lock"))
    scope = find_line(lock_path, "No continuation to recombination or today is claimed")
    if scope is None:
        raise ValueError("scenario-lock scope statement not found")
    return {
        "extendable_with_frozen_model": False,
        "scenario_lock": {"path": str(lock_path), "sha256": sha256(lock_path),
                          "equals_git_REI_COMMIT_copy": lock_git_sha == sha256(lock_path),
                          "equals_other_epoch_copy": sha256(out / "native" / "tree_4de69" / LOCK_REL) == sha256(lock_path),
                          "scientific_admission": lock["scientific_admission"], "interval": lock["interval"]},
        "independent_blockers": [
            {"rank": 1, "kind": "SCIENTIFIC_SCOPE", "blocker": "scenario-lock scope",
             "evidence": {"lock_line": scope["line"], "background.scope": lock["background"]["scope"]},
             "consequence": ("the locked scenario admits no model content below zbar=4; relaxing the native "
                             "validator alone would not make a z<4 run part of the locked scenario")},
            {"rank": 2, "kind": "NATIVE_CONFIG_VALIDATOR",
             "blocker": "DriverConfig::validate requires 4 <= end_zbar < 20; DriverConfig::read and Driver::new call it",
             "evidence": pick("validate_end_zbar_domain", "config_read_calls_validate", "driver_new_calls_validate"),
             "native_probes": "per case: z_below_4_extension.probes (failing inputs) and .positive_control"},
            {"rank": 3, "kind": "SOURCE_MODEL",
             "blocker": ("AxbiSource::at_redshift accepts only zbar in [4,20], and the lock defines no z<4 "
                         "source model"),
             "evidence": pick("source_id", "source_redshift_support", "source_at_redshift_guard"),
             "lock_source_sfr_density": lock["source"]["sfr_density"],
             "lock_source_high_z_support": lock["source"]["high_z_support"],
             "note": ("the guard bounds an analytic emissivity law (SFRD x ionizing yield x f_esc), not a missing "
                      "table; lifting it needs a newly admitted z<4 source model")}],
        "derived_or_non_blocking": [
            {"item": "background domain [a_ref, a_end]", "status": "DERIVED_FROM_BLOCKER_2",
             "evidence": pick("a_end_derived_from_config", "background_scale_domain_guard"),
             "reason": "a_end = 1/(1+end_zbar) is computed in Driver::new from the validated config"},
            {"item": "absolute cosmic age", "status": "NON_BLOCKING",
             "lock_clock_origin": lock["clock"]["origin"],
             "lock_clock_absolute_cosmic_age_s": lock["clock"]["absolute_cosmic_age_s"],
             "reason": "the native clock is elapsed proper time since zbar=20; a continuation needs no absolute age"},
            {"item": "H and s are not checkpoint fields", "status": "NON_BLOCKING",
             "reason": "the frozen background recomputes them from a and q_ref (see restart_inventory.expansion)"}],
    }


def provenance_for_case(case: str, spec: dict, shas: dict, rep: dict, expected: dict, plus_manifest: dict,
                        anchors: dict, rec: Recorder) -> dict:
    seg = spec["segment"]
    restart_sha = shas[str(seg / "checkpoint.txt")]
    ck = parse_checkpoint(seg / "checkpoint.txt")
    native_res = (rep["terminal"]["photon_count_residual_per_H"], rep["terminal"]["energy_residual_eV_per_H"])
    if spec["composed"] is not None:
        comp = spec["composed"]
        for name in ("COMPOSITION_RECEIPT.json", "RETURN.txt", "checkpoint.txt"):
            shas[str(comp / name)] = sha256(comp / name)
        receipt = json.loads((comp / "COMPOSITION_RECEIPT.json").read_text())
        ret = parse_kv((comp / "RETURN.txt").read_text())
        binding = content_binding(ret, ck, native_res)
        checks = {
            "git_manifest_binds_composed_RETURN_sha256":
                shas[str(comp / "RETURN.txt")] == expected[case]["terminal_sha256"],
            "receipt_output_checkpoint_sha256_equals_restart": receipt["output_sha256"]["checkpoint.txt"] == restart_sha,
            "composed_checkpoint_sha256_equals_restart": shas[str(comp / "checkpoint.txt")] == restart_sha,
            "RETURN_fields_and_residuals_equal_checkpoint_and_native": binding["all_equal"]}
        prov = {
            "chain_kind": "RECEIPT_LINKED_PLUS_CONTENT_BOUND",
            "statement": ("REI_COMMIT binds the composed RETURN.txt and history.csv by sha256 but holds no hash of "
                          "this checkpoint. The checkpoint is linked through COMPOSITION_RECEIPT.json (sha256 "
                          "recorded here) and bound by content: every RETURN counter/clock/error field and both "
                          "residuals equal the checkpoint and the natively recomputed values. Not a git-anchored "
                          "hash chain at REI_COMMIT; ref tips that do hold the checkpoint sha256 are in git_anchors."),
            "manifest_terminal_RETURN_sha256": expected[case]["terminal_sha256"],
            "composed_RETURN_sha256": shas[str(comp / "RETURN.txt")],
            "composition_receipt_sha256": shas[str(comp / "COMPOSITION_RECEIPT.json")],
            "composition_receipt_git_status": tracked_at(rec, comp / "COMPOSITION_RECEIPT.json",
                                                         f"analyze_receipt_{case}"),
            "composition_receipt_checkpoint_sha256": receipt["output_sha256"]["checkpoint.txt"],
            "manifest_composed_history_sha256": expected[case]["sha256"]}
    else:
        ret_path = seg / "RETURN.txt"
        shas[str(ret_path)] = sha256(ret_path)
        evidence = plus_manifest["native_evidence"]
        ret = parse_kv(ret_path.read_text())
        binding = content_binding(ret, ck, native_res)
        checks = {
            "git_manifest_checkpoint_sha256_equals_restart": evidence["checkpoint_sha256"] == restart_sha,
            "git_manifest_return_sha256_equals_RETURN": evidence["return_sha256"] == shas[str(ret_path)],
            "RETURN_last_durable_checkpoint_sha256_equals_restart": ret["last_durable_checkpoint_sha256"] == restart_sha,
            "RETURN_fields_and_residuals_equal_checkpoint_and_native": binding["all_equal"]}
        prov = {
            "chain_kind": "GIT_MANIFEST_HASH_BOUND_PLUS_CONTENT_BOUND",
            "statement": ("REI_COMMIT PLUS_COMPLETE_COMPOSITION_MANIFEST.json native_evidence binds this checkpoint "
                          "and RETURN.txt by sha256; content binding as for the other cases. Whether REI_COMMIT is "
                          "an ancestor of the rei_bianchi checkout is in rei_commit_ancestry."),
            "manifest_native_checkpoint_sha256": evidence["checkpoint_sha256"],
            "manifest_native_return_sha256": evidence["return_sha256"]}
    prov.update({"restart_checkpoint_sha256": restart_sha, "checks": checks, "content_binding": binding,
                 "git_anchors": anchors["cases"][case], "chain_ok": all(checks.values())})
    if not prov["chain_ok"]:
        raise ValueError(f"{case}: restart provenance chain broken: {checks}")
    return prov


def analyze(out: Path, rec: Recorder, stages: list[str]) -> dict:
    sys.path[:0] = [str(HTT_BASE), str(HTT_BASE / "htt"), str(HTT_BASE / "htt/src")]
    import pandas as pd
    from bass.recombination.rei_material_history import ReiMaterialHistory
    build_report = json.loads((out / "BUILD.json").read_text())
    if build_report.get("script_sha256") != sha256(SCRIPT):
        raise RuntimeError("BUILD.json was not recorded by this script version; run --stages record first")
    inputs = out / "inputs"
    inputs.mkdir(exist_ok=True)
    five = inputs / "five_case_abundances.csv.gz"
    five.write_bytes(git_show(rec, FIVE_CASE_PATH, "analyze_git_show_five_case"))
    if sha256(five) != FIVE_CASE_SHA:
        raise ValueError("five-case sample hash mismatch")
    manifest4 = json.loads(git_show(rec, SYNC + "/approximation_validity/INPUT_MANIFEST_ORIGINAL_FOUR.json",
                                    "analyze_git_show_manifest_four"))
    plus_manifest = json.loads(git_show(rec, SYNC + "/plus_recovery/PLUS_COMPLETE_COMPOSITION_MANIFEST.json",
                                        "analyze_git_show_plus_manifest"))
    expected = {c["id"]: c for c in manifest4["cases"]}
    native_records = {r["tag"]: r for r in rec.records() if r["tag"].startswith(("build_", "replay_"))}
    lock = json.loads((out / "native" / "tree_d7676" / LOCK_REL).read_text())
    if lock["clock"]["absolute_cosmic_age_s"] is not None:
        raise ValueError("SCENARIO_LOCK now stores an absolute age; revisit the external age convention")
    age_lo = 1e-12
    result = {
        "schema": "htt.r106.rei_restart_replay/2", "rei_commit": REI_COMMIT,
        "script": {"path": str(SCRIPT), "sha256": sha256(SCRIPT)},
        "environment": build_report["environment"],
        "native_outputs": {
            "mode": ("NATIVE_RUN_IN_THIS_INVOCATION" if {"build", "replay"} & set(stages) else
                     "REGENERATED_FROM_CACHED_NATIVE_OUTPUTS (no rebuild, no native rerun)"),
            "replay_dir": str(out / "replay"), "native_dir": str(out / "native"),
            "native_command_records": native_records},
        "rei_commit_ancestry": rei_commit_ancestry(rec),
        "restart_mean_redshift": 4.0, "replayed_accepted_steps": [START, MIDDLE, TERMINAL],
        "external_flrw_q0_age_at_mean_z20_s": {
            "value_s": flrw_q0_age(A_REF, age_lo), "label": "EXTERNAL_CONVENTION_OUTSIDE_LOCKED_DOMAIN",
            "definition": ("int dln a / H_FLRW from a=1e-12 to a_ref=1/21, H_FLRW^2 = H0^2 (Om a^-3 + Or a^-4 + OL), "
                           "q=0, with the lock's rounded H0, Om, Or, OL"),
            "lower_limit_truncation_estimate_s": age_lo**2 / (2 * H0 * math.sqrt(OR)),
            "applies_to": "all five cases identically (no shear term)",
            "not_a_model_output": ("the locked background is defined only on [a_ref, a_end]; SCENARIO_LOCK sets "
                                   "clock.absolute_cosmic_age_s = null; no q-dependent extrapolated age is reported"),
            "lock_clock_absolute_cosmic_age_s": lock["clock"]["absolute_cosmic_age_s"],
            "locked_domain_a": [lock["interval"]["a_ref"], lock["interval"]["a_end"]]},
        "z_below_4_continuation": z_below_4_blockers(out, rec),
        "claim_classes": {
            "numerical_reproducibility": ("cases.*.replay: bitwise restart determinism of the frozen solver over the "
                                          "stated window only (cases.*.replay.window)"),
            "numerical_consistency_and_quadrature": [
                "cases.*.clock_H_consistency_and_quadrature (dt/dN = 1/H and trapezoid error scale)",
                "cases.*.restart_inventory.proper_time (independent quad vs stored clock)",
                "cases.*.restart_inventory python-vs-native and ledger_closure_* differences"],
            "bookkeeping_identities_not_tests": ["cases.*.restart_inventory.charge.electron_*formula*"],
            "conditional_prediction": [
                "cases.*.restart_inventory state values (x_HII, x_HeII, x_HeIII, T, photon stock)",
                "cases.*.clock_H_consistency_and_quadrature Thomson depth values on zbar 20..4"],
            "conditional_sensitivity": ["cases.*.foreground_sensitivity_z_0_to_4 (external tanh convention)"],
            "external_convention": ["external_flrw_q0_age_at_mean_z20_s"],
            "physical_attribution": ("NONE: q_ref differences are conditional responses of a prescribed background "
                                     f"family; SCENARIO_LOCK scientific_admission = {lock['scientific_admission']}")},
        "review_corrections": REVIEW_CORRECTIONS,
        "input_sha256": {}, "cases": {}}
    shas = result["input_sha256"]
    shas[f"git:{REI_COMMIT}:{FIVE_CASE_PATH}"] = FIVE_CASE_SHA
    shas[str(out / "BUILD.json")] = sha256(out / "BUILD.json")
    restart_shas = {case: sha256(spec["segment"] / "checkpoint.txt") for case, spec in CASES.items()}
    anchors = git_hash_anchors(rec, restart_shas)
    result["git_anchor_search"] = anchors["search"]
    for case, spec in CASES.items():
        seg = spec["segment"]
        replay_dir = out / "replay" / case
        for path in sorted(replay_dir.iterdir()):
            shas[str(path)] = sha256(path)
        rep = json.loads((replay_dir / "replay.json").read_text())
        files = {"config": seg / "config.cfg", "restart": seg / "checkpoint.txt",
                 "start": seg / f"checkpoints/{START:08d}.txt", "middle": seg / f"checkpoints/{MIDDLE:08d}.txt",
                 "terminal_checkpoint_copy": seg / f"checkpoints/{TERMINAL:08d}.txt",
                 "resource_overrides": seg / "effective_resource_overrides.json",
                 "segment_history": seg / "history.csv"}
        if (seg / "source_identity.txt").exists():
            files["source_identity"] = seg / "source_identity.txt"
        for path in files.values():
            shas[str(path)] = sha256(path)
        provenance = provenance_for_case(case, spec, shas, rep, expected, plus_manifest, anchors, rec)
        refs = rep["references"]
        continuous = [diff_report(x, r) for x, r in zip(rep["continuous"], refs)]
        restart = diff_report(rep["restart"][0], refs[1])
        byte_ck = {
            f"continuous_{MIDDLE:08d}": (replay_dir / f"continuous_{MIDDLE:08d}.txt").read_bytes() == files["middle"].read_bytes(),
            f"continuous_{TERMINAL:08d}": (replay_dir / f"continuous_{TERMINAL:08d}.txt").read_bytes() == files["terminal_checkpoint_copy"].read_bytes(),
            f"restart_{TERMINAL:08d}_from_{MIDDLE:08d}": (replay_dir / f"restart_{TERMINAL:08d}_from_{MIDDLE:08d}.txt").read_bytes() == files["terminal_checkpoint_copy"].read_bytes()}
        rows = {}
        for prefix in ("continuous", f"restart_from_{MIDDLE:08d}"):
            rows[prefix] = {name: rows_compare(replay_dir / f"{prefix}_{name}.csv", seg / f"{name}.csv", per)
                            for name, per in (("history", 1), ("abundances", 6), ("ledgers", 27), ("feedback", 1))}
            rows[prefix]["spectra"] = spectra_compare(replay_dir / f"{prefix}_spectra.csv", seg / "spectra.csv",
                                                      len(rep["energies_eV"]) * len(rep["angular_mu"]))
        rows["terminal_restart_reread"] = {
            name: (replay_dir / f"terminal_{name}.csv").read_text().splitlines() == tail_lines(seg / f"{name}.csv", per)
            for name, per in (("history", 1), ("abundances", 6), ("ledgers", 27), ("feedback", 1))}
        replay_rows = (replay_dir / "continuous_history.csv").read_text().splitlines()
        hdr = ["time_s", "a", "H_per_s", "ne_proper_cm3"]
        idx = [3, 4, 7, 13]
        mat = np.array([[float(r.split(",")[i]) for i in idx] for r in replay_rows])
        frame_replay = pd.DataFrame(mat, columns=hdr)
        window = replay_window(rep["start"], refs, frame_replay["a"].to_numpy(), rep["terminal"]["accepted"],
                               rep["log"])
        headline = headline_residual({f"continuous_{MIDDLE}": continuous[0], f"continuous_{TERMINAL}": continuous[1],
                                      f"restart_from_{MIDDLE}_to_{TERMINAL}": restart})
        headline["window"] = (f"{window['accepted_steps_replayed']} accepted steps, zbar "
                              f"{window['zbar_start']!r} -> {window['zbar_end']!r}, regime {window['regime']}, "
                              f"rejections in window {window['rejections_in_window']}")
        interval_integrals = clock_h_consistency(frame_replay)
        frame, meta = native_history(case, plus_manifest)
        for p, d in meta["files"].items():
            shas[p] = d
        if spec["composed"] is not None and meta["files"][str(spec["composed"] / "history.csv")] != expected[case]["sha256"]:
            raise ValueError(f"{case}: composed history hash differs from manifest")
        native_last = frame.iloc[-1]
        term = rep["terminal"]
        if not (native_last["a"] == term["a"] and native_last["time_s"] == term["time_s"]
                and native_last["ne_proper_cm3"] == term["ne_proper_cm3"]):
            raise ValueError(f"{case}: full history does not end at the restart state")
        full_integrals = clock_h_consistency(frame)
        rN = full_integrals["int_c_sigmaT_ne_over_H_dN"]["richardson"]
        mat_hist = ReiMaterialHistory(five, case)
        tau_sample = float(mat_hist.cells(np.array([mat_hist.N[0], mat_hist.N[-1]])).tau_to_observer[0])
        inventory = restart_inventory(case, rep, out)
        replay_record = native_records.get(f"replay_{case}")
        if replay_record is None:
            raise ValueError(f"{case}: no native replay command record in COMMANDS.jsonl")
        probes = rep["probes"]
        result["cases"][case] = {
            "q_ref": spec["q_ref"], "segment": str(seg), "source_identity_build": spec["identity"],
            "provenance": provenance, "restart_inventory": inventory,
            "replay": {
                "claim_class": "NUMERICAL_REPRODUCIBILITY (frozen solver restart determinism over the window below)",
                "window": window, "headline_residual": headline,
                "replay_wall_s": {"continuous_312120_to_312237": rep["continuous_wall_s"],
                                  "restart_312180_to_312237": rep["restart_wall_s"]},
                "caps_from_original_wrapper": rep["caps"], "solver_log": rep["log"],
                "continuous_vs_original": {f"{MIDDLE}": continuous[0], f"{TERMINAL}": continuous[1]},
                "restart_from_original_312180_vs_original_312237": restart,
                "checkpoint_text_bytewise_identical_with_original_wall_field": byte_ck,
                "output_rows": rows},
            "clock_H_consistency_and_quadrature": {
                "role": ("clock/H consistency (dt/dN = 1/H) and quadrature-error estimate; NOT a validation of the "
                         "Thomson depth (both forms share n_e, sigma_T and H)"),
                "native_rows_mean_z_20_to_4": full_integrals,
                "replayed_rows_312120_to_312237": interval_integrals,
                "conditional_thomson_depth_mean_z_20_to_4": {
                    "value_richardson_dN_form": rN,
                    "claim_class": ("CONDITIONAL_PREDICTION of the locked, non-admitted scenario; its n_e is "
                                    "not checked by the clock/H consistency above")},
                "r105_1001_sample_vs_native": {
                    "r105_1001_sample_tau_mean_z_20_to_4": tau_sample,
                    "minus_native_richardson": tau_sample - rN, "relative": tau_sample / rN - 1,
                    "tests": "sampling/interpolation of the R105 1001-node material history against native rows"}},
            "z_below_4_extension": {
                "extendable_with_frozen_model": False,
                "blockers": "top-level z_below_4_continuation",
                "probes": probes,
                "first_failing_input": ("config.cfg end_zbar=0.0 -> DriverConfig::read -> "
                                        + probes["DriverConfig::read(config.cfg with end_zbar=0.0)"]),
                "positive_control": {
                    "config_end_zbar": rep["config_end_zbar"],
                    "DriverConfig::read_and_Driver::new_on_config.cfg": "OK" if replay_record["return_code"] == 0 else "FAILED",
                    "evidence": ("the cached native replay parsed config.cfg with DriverConfig::read and built "
                                 "Driver::new (both call DriverConfig::validate) before stepping; see "
                                 "native_outputs.native_command_records"),
                    "replay_command_return_code": replay_record["return_code"],
                    "AxbiSource::at_redshift(4.0)": probes["AxbiSource::at_redshift(4.0)"],
                    "AxbiBackground::point_at_scale(0.2)": probes["AxbiBackground::point_at_scale(0.2)"]},
                "native_tau_4_to_0": None},
            "foreground_sensitivity_z_0_to_4": tanh_foreground(case, inventory["charge"]["xe_per_H"], rep["n_h0_cm3"]),
        }
        print(f"[analyze] {case} done", flush=True)
    result["build"] = build_report
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--stages", default="build,record,replay,analyze")
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    stages = args.stages.split(",")
    unknown = set(stages) - {"build", "record", "replay", "analyze"}
    if unknown:
        parser.error(f"unknown stages {sorted(unknown)}")
    workers = max(1, min(args.workers, 3))
    args.out.mkdir(parents=True, exist_ok=True)
    rec = Recorder(args.out)
    t0 = time.time()
    if "build" in stages:
        rec.drop(("build_", "record_"))
        build(args.out, rec)
    if "record" in stages:
        rec.drop(("record_",))
        record_build(args.out, rec)
    build_report = json.loads((args.out / "BUILD.json").read_text())
    if "replay" in stages:
        rec.drop(("replay_",))
        with futures.ThreadPoolExecutor(max_workers=workers) as pool:
            records = list(pool.map(lambda c: replay_case(c, args.out, rec, build_report), CASES))
        bad = [r for r in records if r["return_code"] != 0]
        if bad:
            raise RuntimeError("replay failed: " + "; ".join(f"{r['tag']}: {r['stderr_tail']}" for r in bad))
    if "analyze" in stages:
        rec.drop(("analyze_",))
        result = analyze(args.out, rec, stages)
        result["invocation"] = {"argv": list(sys.orig_argv), "python_executable": sys.executable, "cwd": os.getcwd(),
                                "stages": stages}
        result["commands"] = rec.records()
        result["analysis_wall_s"] = time.time() - t0
        (args.out / "REI_RESTART_REPLAY.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
        print(f"wrote {args.out / 'REI_RESTART_REPLAY.json'}")


if __name__ == "__main__":
    main()
