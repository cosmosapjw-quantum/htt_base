"""R108 lane s8 step 3: feasibility of lifting the rei_bianchi z >= 4 guard to z = 0 with physics.

Purpose
  Machine-checked feasibility record for S8 (handoff LOCAL_AGENT_HANDOFF.md S8, THEORY_FOUNDATIONS.md TF8).
  Every code location is found now in the frozen source of rei_bianchi commit 56dc609e (read-only
  `git show`); every on-disk input is hashed now; literature identifiers are verified now against the
  arXiv API (metadata only).  The verdict is BLOCKED unless every required physics input is present and
  admitted; no data are invented and nothing in rei_bianchi is modified.

Inputs: rei_bianchi git object store (56dc609e), the R8 radiation directory of rei_bianchi (untracked,
  on disk), the s8 replay rerun (REI_RESTART_REPLAY.json), S8_LOWZ_TAU.json, S8_UVB_VO_PROBE.json,
  S8_REPLAY_COMPARISON.json and the lane command log (replay wall time only).
Outputs: REI/S8_LOWZ_FEASIBILITY.json; REI/S8_LOWZ_FEASIBILITY.md, rendered from the JSON files by
  ``render_markdown`` (R108 review S8-1/S8-2: the page states only what the fields carry; derived ranges and
  maxima are stored in the JSON under ``derived_for_markdown``); receipts in ~/Downloads/htt_r108/s8/RECEIPTS.jsonl
  (the arXiv API response, saved under ~/Downloads/htt_r108/s8/arxiv_api/, and pre-existing inputs).
No randomness.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import re
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HTT_BASE = Path(__file__).resolve().parents[2]
REI_REPO = Path("/home/cosmosapjw/Dropbox/bianchi/rei_bianchi")
REI_COMMIT = "56dc609ea9b801c88d3364aed3eee140b3a20d46"
CRATE = "rust/rei_microphysics"
LOCK_REL = "research/axbi_goal_20261014/scenario/SCENARIO_LOCK.json"
R8 = REI_REPO / "research/microphysics_r9_20261015/vendor_r8/reionization_R8_20261014/radiation"
RESULTS = HTT_BASE / "docs/research_program/observational_publication_20261015/R108_LOS_ATLAS_DATA_20261124/REI"
DEFAULT_RERUN = Path.home() / "Downloads/htt_r108/s8/replay_rerun"
S8_DL = Path.home() / "Downloads/htt_r108/s8"
CMDLOG = Path.home() / "Downloads/htt_r108/logs/s8_COMMANDS.jsonl"

# (file at 56dc609e, needle, role)
CODE_SITES = [
    (f"{CRATE}/src/axbi_driver.rs", "!(4.0..20.0).contains(&self.end_zbar)",
     "DriverConfig::validate: 4 <= end_zbar < 20 (the guard of the handoff)"),
    (f"{CRATE}/src/axbi_driver.rs", "c.validate()?;", "DriverConfig::read calls validate"),
    (f"{CRATE}/src/axbi_driver.rs", "config.validate()?;", "Driver::new calls validate"),
    (f"{CRATE}/src/axbi_driver.rs", "let a_end = 1.0 / (1.0 + config.end_zbar);", "background end derived from end_zbar"),
    (f"{CRATE}/src/axbi_driver.rs", "ln_a_max: a_end.ln(),", "FlatFlrwBackground domain end"),
    (f"{CRATE}/src/axbi_driver.rs", "let mut energies = vec![13.6];", "photon energy grid = source cell edges (13.6..100 eV)"),
    (f"{CRATE}/src/axbi_driver.rs", "return Err(err(\"AXBI_ABOVE_SUPPORT\"));",
     "deposit(): photons above 100 eV rejected (quasar SED above 100 eV cannot be stored)"),
    (f"{CRATE}/src/axbi_driver.rs", "fn inject(&self, s: &mut DriverState, dt: f64)",
     "single source owner (AxbiSource); a quasar population needs a second owner"),
    (f"{CRATE}/src/axbi_driver.rs", "let rate = self.source.at_redshift(1.0 / s.a - 1.0)?.per_h_s;",
     "source call that hits the [4, 20] source guard below z = 4"),
    (f"{CRATE}/src/axbi_driver.rs", "let opacity = (0..3)",
     "homogeneous absorption only (n_absorber sigma); no Lyman-limit-system / clumpy-IGM opacity"),
    (f"{CRATE}/src/axbi_driver.rs", "|| photons.len() != self.energies.len() * self.source.angular_cells.len()",
     "read_checkpoint: photon vector length fixed by the energy grid (z = 4 cohorts need a remap if the grid grows)"),
    (f"{CRATE}/src/axbi_driver.rs", "pub fn run(config_text: &str, out: &Path, case: &str, resume: bool)",
     "run loop (end = 1/(1+end_zbar))"),
    (f"{CRATE}/src/axbi_sources.rs", "pub const ENERGY_SUPPORT_EV: [f64; 2] = [13.6, 100.0];", "source energy support"),
    (f"{CRATE}/src/axbi_sources.rs", "pub const REDSHIFT_SUPPORT: [f64; 2] = [4.0, 20.0];", "source redshift support"),
    (f"{CRATE}/src/axbi_sources.rs", "let edges = [13.6_f64, 24.59, 54.42, 100.0];", "spectral cell edges"),
    (f"{CRATE}/src/axbi_sources.rs", "if !zbar.is_finite() || !(4.0..=20.0).contains(&zbar) {",
     "AxbiSource::at_redshift guard [4, 20]"),
    (f"{CRATE}/src/axbi_sources.rs", "let sfr = 0.015 * zp.powf(2.7) / (1.0 + (zp / 2.9).powf(5.6));",
     "MD14 SFRD law (stellar emissivity = fesc x yield x SFRD; no AGN term)"),
    (f"{CRATE}/src/axbi_background.rs", "if a < self.a_ref || a > self.a_end {", "background scale-domain guard"),
    (LOCK_REL, "No continuation to recombination or today is claimed", "scenario scope (scientific blocker)"),
    (LOCK_REL, "\"clumping_factor\": 1.0,", "homogeneous IGM"),
    (LOCK_REL, "\"AGN_source\": \"OFF\"", "no quasar source in the locked scenario"),
    (LOCK_REL, "\"closure\": \"HOMOGENEOUS_PRIMARY_ONLY_CASE_A_ESCAPE\",", "primary-only closure"),
    (LOCK_REL, "\"observer_tail\": null", "no observer tail in the lock"),
]
# Rust tests at 56dc609e that pin guards of the z >= 4 domain (they must stay; a lift adds a new code path with
# new tests).  R108 review S8-1: each role below was checked against the test body.
TEST_PINS = [
    (f"{CRATE}/tests/axbi_sources.rs", "for z in [3.9, 20.1, f64::NAN, f64::INFINITY] {",
     "source redshift guard: AxbiSource::at_redshift(3.9) and at_redshift(20.1) must fail"),
    (f"{CRATE}/tests/axbi_driver.rs", "assert!(d.deposit(&mut v.photons, 0, 101.0, 1.0).is_err());",
     "energy-support guard: a deposit at 101 eV must fail (AXBI_ABOVE_SUPPORT)"),
    (f"{CRATE}/tests/axbi_background.rs", ".point_at_scale(0.3)",
     "background scale-domain guard: point_at_scale(0.3) on the toy background with a_end = 1/5 must fail "
     "(a > a_end, axbi_background.rs AxbiScaleDomain; the test asserts is_err, not the error kind)"),
    (f"{CRATE}/tests/axbi_background.rs", "        1.0 / 5.0,", "the toy background's a_end = 1/5 (context of that test)"),
]
# Cited as a guard pin before the review; it pins a different guard (R108 review S8-1).
NOT_Z_DOMAIN_TESTS = [
    (f"{CRATE}/tests/axbi_driver.rs", "fn geometry_map_rejects_cold_endpoint_outside_provider_domain()",
     "temperature-provider guard, not the z >= 4 domain: a 1.0001 K gas mapped to a = 1/20.8 must fail after "
     "adiabatic cooling (AxbiProvider.rates)"),
    (f"{CRATE}/tests/axbi_driver.rs", "1.0001,", "the 1.0001 K gas temperature of that test"),
    (f"{CRATE}/tests/axbi_driver.rs", "assert!(d.geometry_map(&mut s, 1.0 / 20.8).is_err());", "its assertion"),
]
R8_FILES = ["puchwein_v1_rates_fiducial.txt", "puchwein_v1_rates_eq-eq.txt", "puchwein_v1_readme.txt",
            "PUBLIC_DATA_RECEIPT.json", "PUBLIC_UVB_RESULTS.json", "uvb_table_adapter.py", "qlf_v3_e912_18_2.npz",
            "QLF_DATA_RECEIPT.json", "QLF_CACHE_AUDIT.json", "SOURCE_CONTRACT.json", "SOURCE_CANDIDATES.md"]
# Literature identifiers to verify against the arXiv API (metadata only).
ARXIV = {
    "HM12 UV/X-ray background synthesis (Haardt & Madau)": "1105.2039",
    "FG20 UV/X-ray background update (Faucher-Giguere)": "1903.08657",
    "P19 UVB and IGM thermal history (Puchwein et al.)": "1801.04931",
    "KS19 UVB / EBL synthesis (Khaire & Srianand)": "1801.09693",
    "AGN UV luminosity function (Kulkarni, Worseck & Hennawi)": "1807.09774",
    "Bolometric quasar luminosity function (Shen et al.)": "2001.02696",
    "Quasar EUV stacked spectrum (Lusso et al.)": "1503.02075",
    "Cosmic star formation history (Madau & Dickinson)": "1403.0007",
    "Ionizing mean free path at 5 < z < 6 (Becker et al.)": "2103.16610",
    "HeII reionization from HeII Lyman-alpha absorption (Worseck et al.)": "1405.7405",
    "Reformatted UVB tables (Taira et al.)": "2505.23544",
}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(REI_REPO), *args], capture_output=True)


def find_sites(sites) -> list[dict]:
    out = []
    cache: dict[str, list[str]] = {}
    for rel, needle, role in sites:
        if rel not in cache:
            r = git("show", f"{REI_COMMIT}:{rel}")
            if r.returncode != 0:
                raise RuntimeError(f"git show {rel} failed")
            cache[rel] = r.stdout.decode().splitlines()
        hits = [i + 1 for i, line in enumerate(cache[rel]) if needle in line]
        if not hits:
            raise ValueError(f"needle not found at {REI_COMMIT[:8]}:{rel}: {needle!r}")
        out.append({"file": f"{REI_COMMIT[:8]}:{rel}", "lines": hits, "needle": needle, "role": role})
    return out


def r8_inventory() -> dict:
    files = {}
    for name in R8_FILES:
        p = R8 / name
        entry: dict = {"present": p.exists()}
        if p.exists():
            entry["sha256"] = sha256_bytes(p.read_bytes())
            rel = p.relative_to(REI_REPO).as_posix()
            entry["in_any_rei_bianchi_commit"] = bool(git("log", "--all", "--format=%H", "-1", "--", rel).stdout.strip())
        files[name] = entry
    receipts = json.loads((R8 / "PUBLIC_DATA_RECEIPT.json").read_text()) + json.loads(
        (R8 / "QLF_DATA_RECEIPT.json").read_text())
    for r in receipts:
        f = files.get(r["local_name"])
        if f and f["present"]:
            f["receipt_url"] = r["url"]
            f["sha256_equals_receipt"] = f["sha256"] == r["sha256"]
    contract = json.loads((R8 / "SOURCE_CONTRACT.json").read_text())
    audit = json.loads((R8 / "QLF_CACHE_AUDIT.json").read_text())
    p19 = (R8 / "puchwein_v1_rates_fiducial.txt").read_text().splitlines()
    zs = [float(line.split()[0]) for line in p19 if line.strip() and not line.startswith("#")]
    return {"directory": str(R8), "files": files,
            "source_contract": {k: contract.get(k) for k in ("modes", "mode_exclusivity", "production_integration",
                                                             "AGN_provider", "stellar_ssp_provider",
                                                             "public_benchmark_status")},
            "qlf_cache_audit": audit,
            "p19_fiducial_table": {"n_nodes": len(zs), "z_min": min(zs), "z_max": max(zs),
                                   "columns": "z, Gamma/heating HI, HeI, HeII, Compton (readme: units 1/s and eV/s)"}}


def guard_test_scan() -> dict:
    """Mechanical search of the crate tests at REI_COMMIT for tests of the end_zbar and scale-domain guards.

    The end_zbar guard (DriverConfig::validate, 4 <= end_zbar < 20) is pinned only if some test supplies a literal
    end_zbar outside [4, 20); the scale-domain guard only if some test asserts is_err on a point_at_scale call.
    """
    names = git("ls-tree", "-r", "--name-only", REI_COMMIT, f"{CRATE}/tests").stdout.decode().split()
    literal, computed, scale_err = [], [], []
    lit_re = re.compile(r"end_zbar\s*=\s*(-?\d+(?:\.\d+)?)\s*(?:;|\\n)")
    for rel in [n for n in names if n.endswith(".rs")]:
        lines = git("show", f"{REI_COMMIT}:{rel}").stdout.decode().splitlines()
        for i, ln in enumerate(lines):
            loc = f"{REI_COMMIT[:8]}:{rel}:{i + 1}"
            if "end_zbar" in ln:
                m = lit_re.search(ln)
                if m:
                    literal.append({"at": loc, "value": float(m.group(1)), "text": ln.strip()})
                elif re.search(r"end_zbar\s*=[^=]", ln):
                    computed.append({"at": loc, "text": ln.strip()})
            if "point_at_scale(" in ln and any(".is_err()" in x for x in lines[i:i + 3]):
                scale_err.append({"at": loc, "text": ln.strip()})
    outside = [x for x in literal if not 4.0 <= x["value"] < 20.0]
    return {"commit": REI_COMMIT, "test_files_scanned": len([n for n in names if n.endswith(".rs")]),
            "end_zbar_literals": literal, "end_zbar_computed_assignments": computed,
            "end_zbar_literals_outside_4_20": outside, "end_zbar_guard_pinned_by_a_test": bool(outside),
            "point_at_scale_is_err_assertions": scale_err, "scale_domain_guard_pinned_by_a_test": bool(scale_err),
            "rule": ("end_zbar guard pinned iff a test supplies a literal end_zbar outside [4, 20) (necessary "
                     "condition); scale guard pinned iff a test asserts is_err within 3 lines of a point_at_scale "
                     "call; computed assignments set the struct field directly and do not call validate()")}


def append_receipts(lines: list[dict]) -> list[dict]:
    """Append receipt lines to ~/Downloads/htt_r108/s8/RECEIPTS.jsonl, skipping (path, sha256) pairs already there."""
    path = S8_DL / "RECEIPTS.jsonl"
    have = set()
    if path.exists():
        for line in path.read_text().splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            have.add((r.get("path"), r.get("sha256")))
    new = [r for r in lines if (r.get("path"), r.get("sha256")) not in have]
    if new:
        S8_DL.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as fh:
            for r in new:
                fh.write(json.dumps(r) + "\n")
    return new


def preexisting_receipts(inv: dict, tau: dict, replay: dict) -> list[dict]:
    """'Pre-existing input' receipt lines (review RCPT-1, lane s8 part) for the raw inputs this lane reads."""
    out = []
    for name, f in inv["files"].items():
        if not f["present"]:
            continue
        p = R8 / name
        out.append({"id": f"S8-PRE-R8-{name}", "name": name, "path": str(p), "sha256": f["sha256"],
                    "bytes": p.stat().st_size, "status": "PRE_EXISTING_INPUT",
                    "route": ("rei_bianchi R8 radiation directory (on disk, untracked); "
                              + (f"download receipt in R8 PUBLIC_DATA_RECEIPT/QLF_DATA_RECEIPT: {f['receipt_url']} "
                                 f"(sha256 equal: {f['sha256_equals_receipt']})" if "receipt_url" in f else
                                 "no download receipt (author/derived file of the R8 round)"))})
    for case, c in tau["cases"].items():
        p = Path(c["checkpoint"])
        sha = sha256_bytes(p.read_bytes())
        out.append({"id": f"S8-PRE-CKPT-{case}", "name": p.name, "path": str(p), "sha256": sha,
                    "bytes": p.stat().st_size, "status": "PRE_EXISTING_INPUT",
                    "route": (f"rei_bianchi AXBI z = 4 restart checkpoint ({case}); sha256 equal to S8_LOWZ_TAU.json: "
                              f"{sha == c['checkpoint_sha256']}")})
    r106 = Path(replay["inputs"]["r106_result"])
    out.append({"id": "S8-PRE-R106-RESULT", "name": r106.name, "path": str(r106),
                "sha256": sha256_bytes(r106.read_bytes()), "bytes": r106.stat().st_size,
                "status": "PRE_EXISTING_INPUT", "route": "committed R106 result (htt_base docs); reference of the replay"})
    return out


def arxiv_verify(timeout: float) -> dict:
    ids = ",".join(ARXIV.values())
    url = f"https://export.arxiv.org/api/query?id_list={ids}&max_results={len(ARXIV)}"
    t0 = time.time()
    fetched_at = dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            raw = resp.read()
            final_url, status = resp.geturl(), resp.status
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "url": url}
    sha = sha256_bytes(raw)
    save = S8_DL / "arxiv_api" / f"arxiv_api_{sha[:16]}.xml"
    save.parent.mkdir(parents=True, exist_ok=True)
    save.write_bytes(raw)
    receipt = {"id": "S8-ARXIV-API", "name": save.name, "path": str(save), "url": url, "final_url": final_url,
               "http_status": status, "bytes": len(raw), "sha256": sha, "fetched_at_utc": fetched_at,
               "status": "FETCHED", "route": "export.arxiv.org API (metadata only)"}
    append_receipts([receipt])
    ns = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    root = ET.fromstring(raw)
    found = {}
    for e in root.findall("a:entry", ns):
        def text(path: str) -> str:
            node = e.find(path, ns)
            return "" if node is None or node.text is None else node.text
        eid = text("a:id").rsplit("/abs/", 1)[-1]
        found[eid.split("v")[0]] = {"id": eid, "title": " ".join(text("a:title").split()),
                                    "first_author": text("a:author/a:name"), "published": text("a:published"),
                                    "journal_ref": text("arxiv:journal_ref") or None, "doi": text("arxiv:doi") or None}
    entries = {label: found.get(aid, {"id": aid, "missing": True}) for label, aid in ARXIV.items()}
    return {"ok": True, "url": url, "response_sha256": sha, "wall_s": round(time.time() - t0, 3),
            "response_file": str(save), "receipt": receipt, "entries": entries,
            "doi_summary": {"n_entries": len(entries),
                            "n_missing": sum(bool(e.get("missing")) for e in entries.values()),
                            "with_doi": [k for k, e in entries.items() if e.get("doi")],
                            "without_doi": [k for k, e in entries.items() if not e.get("doi")]}}


def _sci(x: float, n: int = 3) -> str:
    """Compact %g formatting: 1.29e+05 -> 1.29e5, 2.2e-16 stays."""
    t = f"{x:.{n}g}"
    m = re.match(r"^(-?[\d.]+)e([+-])0*(\d+)$", t)
    return f"{m.group(1)}e{'-' if m.group(2) == '-' else ''}{m.group(3)}" if m else t


def _cap(t: str) -> str:
    return t[:1].upper() + t[1:]


def _cmdlog_last_success(pattern: str) -> dict | None:
    if not CMDLOG.exists():
        return None
    rows = [json.loads(line) for line in CMDLOG.read_text().splitlines() if line.strip()]
    hits = [r for r in rows if pattern in r["cmd"] and r.get("rc") == 0]
    if not hits:
        return None
    r = hits[-1]
    return {"file": str(CMDLOG), "cmd": r["cmd"], "wall_s": r["wall_s"], "started_utc": r.get("started_utc")}


def derive(tau: dict, replay: dict, res: dict) -> dict:
    """Ranges and maxima quoted by the markdown page, computed from JSON fields (review S8-2a)."""
    cases = tau["cases"]
    zhs = sorted(tau["donor_band_recomputed"]["by_z_HeII"], key=float)
    blocks = [(c, zh, cases[c]["by_z_HeII"][zh]) for c in cases for zh in zhs]
    dec = [b["decomposition"] for _, _, b in blocks]
    shear: dict[str, list] = {}
    for c, zh, b in blocks:
        shear.setdefault(f"{abs(cases[c]['q_ref']):g}", []).append(b["shear_term_sensitivity"]["relative"])
    rc = replay["cases"]
    windows = {c["window"] for c in rc.values()}
    uc = tau["units_check"]
    return {
        "sources": ("fields of S8_LOWZ_TAU.json, S8_REPLAY_COMPARISON.json and this file; replay wall time from the "
                    "lane command log"),
        "replay_wall_time_from_command_log": _cmdlog_last_success("scripts/r106/rei_restart_replay.py"),
        "replay_n_cases": len(rc),
        "replay_window_all_cases": windows.pop() if len(windows) == 1 else sorted(windows),
        "replay_checkpoints_bytewise_identical_all": all(all(c["checkpoint_text_bytewise_identical"].values())
                                                         for c in rc.values()),
        "replay_output_rows_bytewise_identical_all": all(c["output_rows_all_bytewise_identical"] for c in rc.values()),
        "replay_last_two_intervals_zero_difference_all": all(all(v["all_zero"] for v in c[
            "last_two_output_intervals"].values()) for c in rc.values()),
        "restart_inventory_identical_to_r106_all": all(all(v["identical"] for v in c[
            "restart_inventory_vs_r106_exact"].values()) for c in rc.values()),
        "restart_inventory_groups": sorted(next(iter(rc.values()))["restart_inventory_vs_r106_exact"]),
        "native_files_identical_to_r106_cache_all": all(c["native_replay_files_vs_r106_cache"]["all_identical"]
                                                        for c in rc.values()),
        "n_case_depths": len(blocks),
        "n_case_depths_inside_band": sum(b["inside_donor_band"] for _, _, b in blocks),
        "z_HeII_with_depths_outside_band": sorted({zh for _, zh, b in blocks if not b["inside_donor_band"]}, key=float),
        "above_band_max_by_range": [min(b["above_band_max_by"] for _, _, b in blocks if not b["inside_donor_band"]),
                                    max(b["above_band_max_by"] for _, _, b in blocks if not b["inside_donor_band"])]
        if any(not b["inside_donor_band"] for _, _, b in blocks) else None,
        "x_e4_checkpoint_range": [min(c["x_e4_from_checkpoint"] for c in cases.values()),
                                  max(c["x_e4_from_checkpoint"] for c in cases.values())],
        "x_e4_minus_tf8_donor_range": [min(c["x_e4_minus_tf8_donor"] for c in cases.values()),
                                       max(c["x_e4_minus_tf8_donor"] for c in cases.values())],
        "max_abs_affine_prediction_minus_exact_x_e4_term": max(
            abs(d["x_e4_term_affine_prediction"] - d["x_e4_term_exact"]) for d in dec),
        "n_H0_and_f_He_terms_all_exactly_zero": all(d["n_H0_term"] == 0.0 and d["f_He_and_background_term"] == 0.0
                                                    for d in dec),
        "n_h0_and_f_he_equal_r107_constants_all": all(c["n_h0_minus_r107_constant"] == 0.0
                                                      and c["f_he_minus_r107_constant"] == 0.0 for c in cases.values()),
        "shear_term_relative_range_by_abs_q_ref": {q: [min(v), max(v)] for q, v in sorted(shear.items())},
        "units_relative_quad_minus_module": [u["relative_astropy_quad_minus_module"] for u in uc.values()],
        "units_max_abs_relative_gauss_legendre_minus_module": max(
            abs(u["relative_astropy_gauss_legendre_minus_module"]) for u in uc.values()),
        "units_codata2022_sigma_T_tau_shift": next(iter(uc.values()))["relative_tau_shift_if_codata2022_sigma_T"],
        "units_astropy_version": next(iter(uc.values()))["astropy_version"],
        "arxiv_entries_without_doi": res["literature_arxiv_verification"].get("doi_summary", {}).get("without_doi"),
    }


def render_markdown(res: dict, tau: dict, replay: dict, json_path: Path) -> str:
    """S8_LOWZ_FEASIBILITY.md from the JSON files (every number is a field or a ``derived_for_markdown`` entry)."""
    d = res["derived_for_markdown"]
    sites = {(x["file"].split("/")[-1], x["needle"]): x["lines"] for x in res["code_sites_at_56dc609e"]}

    def ln(fname: str, needle_part: str) -> str:
        hits = [v for (f, n), v in sites.items() if f == fname and needle_part in n]
        return ", ".join(str(i) for i in hits[0])

    lock = "SCENARIO_LOCK.json"
    inv = res["r8_inventory"]
    p19 = inv["p19_fiducial_table"]
    p19_rec = all(inv["files"][n].get("sha256_equals_receipt") for n in inv["files"] if n.startswith("puchwein_v1_rates"))
    cost = res["runtime_extrapolation_frozen_physics"]["ZERO"]
    arx = res["literature_arxiv_verification"]
    vo = res["vo_probe_summary"] or {}
    reach = vo.get("vizier_server_reachable", {})
    found = vo.get("named_catalogue_ids_found", {})
    rel = vo.get("relevant_vizier_catalogues", {})
    band = tau["donor_band_recomputed"]
    cosmo = tau["cosmology_from_solver_configuration"]["checks"]
    scan = res["guard_test_scan"]
    L = []
    w = L.append
    w("# S8: REI below z = 4\n")
    w(f"This page is generated by `scripts/r108/s8_lowz_feasibility.py` (sha256 {res['script']['sha256'][:12]}...). "
      "Every number on it is a field of `S8_REPLAY_COMPARISON.json`, `S8_LOWZ_TAU.json`, "
      "`S8_LOWZ_FEASIBILITY.json` or `S8_UVB_VO_PROBE.json` in this directory; ranges and maxima are computed by "
      "that script and stored in `S8_LOWZ_FEASIBILITY.json` under `derived_for_markdown`. The one exception is the "
      "replay wall time, which comes from the lane command log `~/Downloads/htt_r108/logs/s8_COMMANDS.jsonl`. "
      "Each JSON file records the script that wrote it and that script's sha256.")
    w("These results are numerical evidence only. They make no family attribution, use no likelihood and give no "
      "calibrated p.\n")
    w("## Verdict\n")
    v = res["verdict"]
    w(f"**S8 physics lift: {v['s8_physics_lift']}.** The rei_bianchi branch `r108-lowz-feasibility` was "
      f"{'**not** ' if not v['branch_r108_lowz_feasibility_created'] else ''}created, and nothing in rei_bianchi was "
      "modified.\n")
    w(f"The lift needs {len(res['missing_inputs'])} inputs ({res['missing_inputs'][0]['id']} to "
      f"{res['missing_inputs'][-1]['id']} in `S8_LOWZ_FEASIBILITY.json`), and none of them is both present and "
      "admitted:\n")
    w(f"- **M1. Scope.** An owner-issued scenario lock for 0 <= zbar < 4. The current lock states:")
    w(f"  - \"No continuation ... today\" ({lock}:{ln(lock, 'No continuation')});")
    w(f"  - `AGN_source` is OFF (:{ln(lock, 'AGN_source')});")
    w(f"  - clumping is 1 (:{ln(lock, 'clumping_factor')});")
    w(f"  - the closure is `HOMOGENEOUS_PRIMARY_ONLY_CASE_A_ESCAPE` (:{ln(lock, 'closure')});")
    w(f"  - `observer_tail` is null (:{ln(lock, 'observer_tail')}).")
    w(f"- **M2. Quasar source.** {_cap(res['missing_inputs'][1]['missing'])}. "
      f"The only on-disk candidate is the Kulkarni QLF v3.0 cache `{inv['qlf_cache_audit']['file']}` in the R8 "
      f"radiation directory, and it is {inv['qlf_cache_audit']['status']} (`QLF_CACHE_AUDIT.json`: "
      f"{inv['qlf_cache_audit']['reason'].rstrip('.')}).")
    w(f"- **M3. Stellar source.** {_cap(res['missing_inputs'][2]['missing'])}.")
    w(f"- **M4. IGM opacity.** {_cap(res['missing_inputs'][3]['missing'])} "
      f"(axbi_driver.rs:{ln('axbi_driver.rs', 'opacity')}).")
    w("- **M5. UV background tables valid to z = 0.**")
    w(f"  - {_cap(res['missing_inputs'][4]['missing'])}.")
    w(f"  - The P19 v1 ancillary rates on disk: {p19['n_nodes']} nodes, z from {p19['z_min']:g} to {p19['z_max']:g}; "
      f"receipt hashes {'match' if p19_rec else 'DO NOT match'}; production integration "
      f"{inv['source_contract']['production_integration']}.")
    w(f"- **M6. Grid.** {_cap(res['missing_inputs'][5]['missing'])} "
      f"(axbi_driver.rs:{ln('axbi_driver.rs', 'photons.len()')}).\n")
    w(f"Code locations at {res['rei_commit'][:8]}, each found again in this run:\n")
    w("- **Driver guard and domain** (`axbi_driver.rs`):")
    w(f"  - guard: {ln('axbi_driver.rs', 'contains(&self.end_zbar)')};")
    w(f"  - validate is called from {ln('axbi_driver.rs', 'c.validate()')} and {ln('axbi_driver.rs', 'config.validate()')};")
    w(f"  - `a_end` is derived at {ln('axbi_driver.rs', 'let a_end')} and {ln('axbi_driver.rs', 'ln_a_max')};")
    w(f"  - energy grid: {ln('axbi_driver.rs', 'energies = vec')};")
    w(f"  - `AXBI_ABOVE_SUPPORT`: {ln('axbi_driver.rs', 'AXBI_ABOVE_SUPPORT')}.")
    w("- **Driver sources, absorption and run loop** (`axbi_driver.rs`):")
    w(f"  - `inject`: {ln('axbi_driver.rs', 'fn inject')};")
    w(f"  - source call: {ln('axbi_driver.rs', 'at_redshift')};")
    w(f"  - homogeneous opacity: {ln('axbi_driver.rs', 'opacity')};")
    w(f"  - checkpoint length check: {ln('axbi_driver.rs', 'photons.len()')};")
    w(f"  - `run`: {ln('axbi_driver.rs', 'pub fn run')}.")
    w("- **Sources** (`axbi_sources.rs`):")
    w(f"  - energy support: {ln('axbi_sources.rs', 'ENERGY_SUPPORT_EV')};")
    w(f"  - redshift support: {ln('axbi_sources.rs', 'REDSHIFT_SUPPORT')};")
    w(f"  - cell edges: {ln('axbi_sources.rs', 'let edges')};")
    w(f"  - `at_redshift` guard: {ln('axbi_sources.rs', 'zbar.is_finite()')};")
    w(f"  - SFRD law: {ln('axbi_sources.rs', 'let sfr')}.")
    w(f"- **Background** (`axbi_background.rs`): domain guard at {ln('axbi_background.rs', 'a < self.a_ref')}.\n")
    pins = res["rust_tests_pinning_the_guards"]
    w(f"Rust tests at {res['rei_commit'][:8]} that pin guards of the z >= 4 domain and must stay unchanged:\n")
    for t in pins:
        if "context" in t["role"]:
            continue
        w(f"- `tests/{t['file'].split('/')[-1]}:{', '.join(map(str, t['lines']))}`: {t['role']}.")
    w("")
    nz = res["rust_test_cited_before_review_not_a_z_domain_guard"][0]
    w(f"Not a z-domain guard: `tests/{nz['file'].split('/')[-1]}:{', '.join(map(str, nz['lines']))}` "
      f"(`{nz['needle'].replace('fn ', '').replace('()', '')}`) is a {nz['role']}.\n")
    lits = sorted({x["value"] for x in scan["end_zbar_literals"]})
    w(f"**Unpinned guard.** No test at {res['rei_commit'][:8]} checks that `DriverConfig::validate` rejects an end_zbar "
      f"outside [4, 20) (axbi_driver.rs:{ln('axbi_driver.rs', 'contains(&self.end_zbar)')}): the "
      f"{scan['test_files_scanned']} test files contain end_zbar literals {', '.join(f'{x:g}' for x in lits)} only, and "
      f"{len(scan['end_zbar_computed_assignments'])} computed assignments that set the struct field without "
      f"calling validate. A relaxed end_zbar guard would therefore pass every existing test; acceptance test T0 adds "
      f"the missing tests. The scale-domain guard is pinned "
      f"({'; '.join('`' + x['at'].split('/')[-1] + '`' for x in scan['point_at_scale_is_err_assertions'])}).\n")
    w(f"The JSON lists a change plan and acceptance tests "
      f"{res['acceptance_tests_if_unblocked'][0].split()[0]} to {res['acceptance_tests_if_unblocked'][-1].split()[0]} "
      "for when the blockers are lifted. The plan uses a separate low-z driver configuration and source owner rather "
      "than relaxing the locked validator.\n")
    w(f"At the z = 4 step size (dln a = {_sci(cost['next_dln_a_at_z4_checkpoint'])}) and the measured "
      f"{cost['wall_s_per_accepted_step']:.2g} s per accepted step (ZERO case), the frozen physics would need about "
      f"{_sci(cost['accepted_steps_z4_to_z0_at_that_step'])} steps, or about "
      f"{cost['wall_h_z4_to_z0_at_that_rate']:.2g} h per case, to reach z = 0. This is an arithmetic extrapolation "
      "only: new physics changes both the step size and the cost per step.\n")
    if arx.get("ok"):
        ds = arx["doi_summary"]
        names = [k.split("(")[-1].rstrip(")") if "(" in k else k for k in arx["entries"]]
        w(f"{ds['n_entries'] - ds['n_missing']} of {ds['n_entries']} literature identifiers were found by the arXiv "
          f"API in this run: {'; '.join(names).rstrip('.')}. The DOI was recorded where arXiv lists one "
          f"(none for {'; '.join(k.split('(')[-1].rstrip(')') for k in ds['without_doi']) or 'no entry'}).\n")
    else:
        w(f"The arXiv API query failed in this run: {arx.get('error')}.\n")
    vers = vo.get("versions") or {}
    w(f"The VO search used astroquery {vers.get('astroquery')} and pyvo {vers.get('pyvo')}:\n")
    w(f"- CDS VizieR: {'reachable' if reach.get('vizier.cds.unistra.fr') else 'unreachable'} "
      f"(`{vo.get('cds_connectivity_error')}`); TAPVizieR: "
      f"{'answered' if vo.get('tapvizier_ok') else 'timed out or failed'}.")
    cfa = [f"{cid} ({x['description']})" for cid, x in rel.items()
           if any(k in x["description"] for k in ("photoionization", "Kulkarni", "Worseck"))]
    w(f"- The CfA VizieR mirror {'answered' if reach.get('vizier.cfa.harvard.edu') else 'did not answer'}. "
      f"Of the named catalogues it lists {'; '.join(k for k, f in found.items() if f) or 'none'}"
      + (f"; relevant entries include {'; '.join(cfa)}" if cfa else "") + ".")
    w(f"- Not found on the CfA VizieR mirror (CDS unreachable, so not a statement about VizieR as a whole): "
      f"{'; '.join(k for k, f in found.items() if not f)}.\n")
    rr = replay["rerun"]
    wall = d["replay_wall_time_from_command_log"]
    w(f"## Step 1: restart replay ({'PASS' if replay['verdict']['all_cases_identical_to_original_and_r106'] else 'FAIL'})\n")
    w(f"The R106 replay script was run {'unchanged' if rr['replay_script_unchanged'] else 'CHANGED'} "
      f"(sha256 {rr['replay_script_sha256'][:8]}...) with stages {', '.join(rr['invocation']['stages'])}. It wrote to "
      f"`{rr['invocation']['argv'][4].replace(str(Path.home()), '~')}`"
      + (f" and took {wall['wall_s']:.3g} s (command log, started {wall['started_utc']})." if wall else ".") + "\n")
    b = replay["build"]
    w(f"- **Build.** For both source epochs ({', '.join(b)}), the compiled source identity, the full src tree hash and "
      f"the binary sha256 {'equal' if all(x['identity_equal_r106'] and x['src_tree_equal_r106'] and x['binary_equal_r106'] for x in b.values()) else 'DO NOT all equal'} the R106 build.")
    win = d["replay_window_all_cases"]
    w(f"- **Window.** For all {d['replay_n_cases']} cases: {win}." if isinstance(win, str) else
      f"- **Window.** The cases differ: {win}.")
    w("- **Agreement with the original run:**")
    w(f"  - checkpoint text bytewise identical (both checkpoints and the restart), all cases: "
      f"{d['replay_checkpoints_bytewise_identical_all']};")
    w(f"  - every replayed output row bytewise identical: {d['replay_output_rows_bytewise_identical_all']};")
    w(f"  - every field of the last two output intervals has zero difference: "
      f"{d['replay_last_two_intervals_zero_difference_all']}.")
    w(f"- **Agreement with the committed R106 result:** every leaf of the restart inventory "
      f"({', '.join(d['restart_inventory_groups'])}) exactly equal: {d['restart_inventory_identical_to_r106_all']}.")
    w(f"- **Agreement with the R106 cache:** every native replay output file byte-identical (replay.json apart from "
      f"its wall-clock fields): {d['native_files_identical_to_r106_cache_all']}.\n")
    w("## Step 2: tau(0 -> 4)\n")
    bgm = tau["cosmology_from_solver_configuration"]["module_background"]
    w(f"**Cosmology.** The module accepts the solver cosmology: H0 = {bgm['h0_km_s_mpc']:g}, Omega_m = "
      f"{bgm['omega_m']:g} and Omega_r = {_sci(bgm['omega_r'], 2)} from SCENARIO_LOCK.json at "
      f"{res['rei_commit'][:8]}.\n")
    w(f"- Omega_Lambda equal to the lock formula: {cosmo['module_omega_l_equals_lock_formula']}; Mpc constant equal: "
      f"{cosmo['module_Mpc_equals_lock_mpc_cm']}.")
    w(f"- H0 in s^-1 differs by {_sci(cosmo['module_H0_per_s_relative_minus_lock_formula'], 2)} relative "
      f"({cosmo['module_H0_per_s_formula']}).")
    w(f"- The native n_H0 and f_He equal the R107 constants exactly in every case: "
      f"{d['n_h0_and_f_he_equal_r107_constants_all']}.\n")
    sr = d["shear_term_relative_range_by_abs_q_ref"]
    w("**The shear term is not supported.** The locked H law is hypot(H_FLRW, s), and `FlrwBackground` has no shear "
      "term. An independent integrand gives a relative shift of "
      + "; ".join(f"{_sci(v[0])} to {_sci(v[1])} for |q| = {q}" if v[0] != v[1] else f"{_sci(v[0])} for |q| = {q}"
                  for q, v in sr.items())
      + " (over z_HeII and the sign of q). This uses the lock law outside its domain, so it is a sensitivity only.\n")
    w(f"**Donor band, recomputed.** All values round to the TF8 quoted values: {band['all_round_to_tf8_quoted']}.\n")
    w("| z_HeII | tau(0 -> 4) |")
    w("|---|---|")
    for zh in sorted(band["by_z_HeII"], key=float):
        w(f"| {zh} | {band['by_z_HeII'][zh]['tau_0_to_4']:.12f} |")
    s_ = tau["summary"]
    w("")
    w(f"**Case depths.** The {len(tau['cases'])} cases differ from each other by at most "
      f"{_sci(s_['max_case_to_case_spread_same_z_HeII'], 2)} at fixed z_HeII, and from the donor by at most "
      f"{_sci(s_['max_abs_case_minus_donor_same_z_HeII'])}.\n")
    w(f"- {d['n_case_depths_inside_band']} of the {d['n_case_depths']} case depths lie inside the band.")
    if d["above_band_max_by_range"]:
        w(f"- The other {d['n_case_depths'] - d['n_case_depths_inside_band']} (z_HeII = "
          f"{', '.join(d['z_HeII_with_depths_outside_band'])}) lie above the band maximum by "
          f"{_sci(d['above_band_max_by_range'][0])} to {_sci(d['above_band_max_by_range'][1])}.")
    w("")
    zmax = max(band["dtau_dxe4_by_z_HeII"], key=float)
    w(f"**Why they lie above.** Each case has x_e(4) = {d['x_e4_checkpoint_range'][0]:.11g} to "
      f"{d['x_e4_checkpoint_range'][1]:.11g} from its checkpoint, which is {_sci(d['x_e4_minus_tf8_donor_range'][0])} to "
      f"{_sci(d['x_e4_minus_tf8_donor_range'][1])} above the TF8 donor value {tau['inputs']['tf8_donor_x_e4']!r}. tau is "
      f"affine in x_e(4) with dtau/dx_e(4) = {band['dtau_dxe4_by_z_HeII'][zmax]:.4g} at z_HeII = {zmax}. The affine "
      f"prediction matches the exact difference to {_sci(d['max_abs_affine_prediction_minus_exact_x_e4_term'], 1)} "
      f"(max over cases and z_HeII), and the n_H0 and f_He terms are exactly 0: "
      f"{d['n_H0_and_f_He_terms_all_exactly_zero']}."
      + (" **The offset is therefore the rounding of the TF8 donor value, not a physics difference.**"
         if d["n_H0_and_f_He_terms_all_exactly_zero"] else "") + "\n")
    w("**Units check.** The test is `tests/obsstat/test_r108_s8_lowz_tau.py`. It uses astropy CODATA-2018 constants "
      "with a hand-written integrand.\n")
    w(f"- Against the module, the relative difference is "
      f"{' and '.join(_sci(x, 2) for x in d['units_relative_quad_minus_module'])} with scipy quad, and at most "
      f"{_sci(d['units_max_abs_relative_gauss_legendre_minus_module'], 2)} with a 400-node Gauss-Legendre rule.")
    w(f"- The module's constants are CODATA 2018. The .venv astropy {d['units_astropy_version']} defaults to CODATA "
      f"2022, whose sigma_T would shift tau by {_sci(d['units_codata2022_sigma_T_tau_shift'])} relative.")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rerun", type=Path, default=DEFAULT_RERUN)
    ap.add_argument("--out", type=Path, default=RESULTS / "S8_LOWZ_FEASIBILITY.json")
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--md", type=Path, default=RESULTS / "S8_LOWZ_FEASIBILITY.md")
    args = ap.parse_args(argv)
    t0 = time.time()
    sites = find_sites(CODE_SITES)
    pins = find_sites(TEST_PINS)
    not_z = find_sites(NOT_Z_DOMAIN_TESTS)
    scan = guard_test_scan()
    inv = r8_inventory()
    rerun = json.loads((args.rerun / "REI_RESTART_REPLAY.json").read_text())
    cost = {}
    for case, c in rerun["cases"].items():
        w = c["replay"]["window"]
        wall = c["replay"]["replay_wall_s"]["continuous_312120_to_312237"]
        ck = (Path(c["restart_inventory"]["restart_file"])).read_text().splitlines()[1].split()
        next_dln_a = float(ck[7])
        steps_to_z0 = __import__("math").log(5.0) / next_dln_a
        cost[case] = {"replayed_steps": w["accepted_steps_replayed"], "continuous_wall_s": wall,
                      "wall_s_per_accepted_step": wall / w["accepted_steps_replayed"],
                      "next_dln_a_at_z4_checkpoint": next_dln_a,
                      "accepted_steps_z4_to_z0_at_that_step": steps_to_z0,
                      "wall_h_z4_to_z0_at_that_rate": steps_to_z0 * wall / w["accepted_steps_replayed"] / 3600.0,
                      "note": ("arithmetic extrapolation of the frozen z>=4 physics at the z=4 step size; new z<4 "
                               "physics changes both the step size and the per-step cost")}
    tau = json.loads((RESULTS / "S8_LOWZ_TAU.json").read_text())
    vo_path = RESULTS / "S8_UVB_VO_PROBE.json"
    vo = None
    if vo_path.exists():
        probe = json.loads(vo_path.read_text())
        vo = dict(probe["summary"], file=str(vo_path), sha256=sha256_bytes(vo_path.read_bytes()))
        relevant = {}
        for server, blk in probe["vizier"].items():
            for group in ("find_catalogs", "catalog_ids"):
                for q in blk[group].values():
                    res = q.get("result") if q.get("ok") else None
                    for cid, desc in (res or {}).items():
                        if desc and any(k in desc for k in ("UV background", "photoionization", "luminosity function",
                                                            "Kulkarni", "Worseck")):
                            relevant[cid] = {"description": desc, "server": server}
        vo["relevant_vizier_catalogues"] = relevant
        vo["note"] = ("'null' in vizier_catalogue_ids_returned is astroquery's placeholder for an empty match; "
                      "the CDS server's legacy votable endpoint returned HTTP 404, the CfA mirror answered")
        vo["cds_connectivity_error"] = probe["vizier"]["vizier.cds.unistra.fr"]["connectivity_get_catalogs_II_246"].get(
            "error")
        vo["tapvizier_error"] = (probe.get("tapvizier", {}).get("tables_of_named_catalogues", {}).get("error") or "")[:160]
        vo["catalogue_search_scope"] = ("named catalogue ids and keyword searches answered by the CfA VizieR mirror "
                                        "only (CDS VizieR unreachable, TAPVizieR timed out); absence means 'not found "
                                        "on the CfA mirror', not 'absent from VizieR'")
        vo["versions"] = probe.get("versions")
    arx = arxiv_verify(args.timeout)
    missing = [
        {"id": "M1", "kind": "SCIENTIFIC_SCOPE",
         "missing": "an owner-issued scenario lock for 0 <= zbar < 4 (interval, AGN on, post-overlap IGM closure)",
         "evidence": "code_sites: SCENARIO_LOCK scope / AGN_source / closure / observer_tail lines"},
        {"id": "M2", "kind": "SOURCE_MODEL_QUASAR",
         "missing": ("an admitted quasar ionizing emissivity eps(z) for 0 <= z <= 4 with an EUV SED reaching above "
                     "54.4 eV (HeII edge) and beyond the 100 eV grid end"),
         "on_disk_candidate": "R8 qlf_v3_e912_18_2.npz (Kulkarni QLF v3.0 cache)",
         "candidate_status": "NOT_ADMITTED per QLF_CACHE_AUDIT.json (quantile labels/generator unresolved)"},
        {"id": "M3", "kind": "SOURCE_MODEL_STELLAR",
         "missing": ("an admitted stellar escaped emissivity below z = 4: the lock's MD14 x yield x fesc law is "
                     "admitted only on [4, 20] (fesc = 0.2 fixed); an fesc(z < 4) or SSP-based escaped spectrum is "
                     "not selected (SOURCE_CONTRACT stellar_ssp_provider = CANDIDATE_SELECTED_NOT_DOWNLOADED)")},
        {"id": "M4", "kind": "IGM_OPACITY",
         "missing": ("an absorber (Lyman-limit-system) opacity or mean-free-path model lambda_mfp(z) for the "
                     "post-overlap IGM; the driver absorbs only on homogeneous gas (clumping 1) and has no recombination "
                     "re-emission (excluded in the lock provider list)")},
        {"id": "M5", "kind": "UVB_TABLE",
         "missing": ("for an H/He UV background valid to z = 0: FG20 and HM12 tables are not on disk; P19 v1 ancillary "
                     "rates (z 0..15.1) are on disk with receipts and a Python adapter, but production integration is "
                     "PENDING and the prescribed-rate mode is exclusive with endogenous photon cohorts for the same "
                     "population (SOURCE_CONTRACT mode_exclusivity), so it cannot both continue the z = 4 cohorts and "
                     "supply the background without a declared handover rule"),
         "on_disk": "R8 puchwein_v1_rates_fiducial.txt / _eq-eq.txt (hashes in r8_inventory)"},
        {"id": "M6", "kind": "NUMERICS_GRID",
         "missing": ("an energy grid above 100 eV and a conservative remap of the 392-node z = 4 photon stock "
                     "(8 angles x 49 energies) onto it; read_checkpoint fixes the vector length")},
    ]
    result = {
        "schema": "htt.r108.s8.lowz_feasibility/1",
        "script": {"path": str(Path(__file__).resolve()), "sha256": sha256_bytes(Path(__file__).read_bytes())},
        "rei_commit": REI_COMMIT,
        "rei_bianchi_head_now": git("rev-parse", "HEAD").stdout.decode().strip(),
        "verdict": {
            "s8_physics_lift": "BLOCKED",
            "branch_r108_lowz_feasibility_created": False,
            "reason": ("the z < 4 physics inputs M1-M6 are not all present and admitted; implementing the lift now "
                       "would require choosing a quasar emissivity/SED, an fesc(z), an absorber opacity model and a "
                       "source-mode handover that no admitted input fixes (invented model content)"),
            "what_remains_valid": ("DonorMatchedContinuation depths (S8_LOWZ_TAU.json) as a declared-sensitivity "
                                   "closure below z = 4; the z >= 4 native history is reproducible (S8_REPLAY_COMPARISON.json)")},
        "missing_inputs": missing,
        "code_sites_at_56dc609e": sites,
        "rust_tests_pinning_the_guards": pins,
        "rust_test_cited_before_review_not_a_z_domain_guard": not_z,
        "guard_test_scan": scan,
        "unpinned_guards": [
            {"guard": "DriverConfig::validate: 4 <= end_zbar < 20",
             "site": next(x for x in sites if "end_zbar" in x["needle"] and "contains" in x["needle"]),
             "pinned_by_a_test": scan["end_zbar_guard_pinned_by_a_test"],
             "evidence": "guard_test_scan.end_zbar_literals (all literal values) and end_zbar_literals_outside_4_20"}],
        "pinned_guards_from_scan": [
            {"guard": "AxbiBackground::point_at_scale scale domain (a_ref <= a <= a_end)",
             "pinned_by_a_test": scan["scale_domain_guard_pinned_by_a_test"],
             "evidence": "guard_test_scan.point_at_scale_is_err_assertions"}],
        "change_plan_if_unblocked": [
            "add a separate low-z driver configuration (0 <= end_zbar < 4, start from an AXBI_CHECKPOINT_V2 at zbar = 4) "
            "instead of relaxing DriverConfig::validate, so the locked-scenario guard and its tests stay unchanged",
            "add a LowZSource owner next to AxbiSource (quasar eps(z) x SED cells; stellar escaped emissivity below z = 4), "
            "each with its own redshift/energy support constants and unit tests; AxbiSource::at_redshift keeps [4, 20]",
            "extend the energy grid above 100 eV for the low-z driver only; remap the z = 4 stock by zero padding "
            "(exact in N and U) and accept the remapped checkpoint through a versioned reader",
            "add an absorber opacity term (lambda_mfp(z) or f(N_HI, z)) to evaluate() for the low-z driver only, with a "
            "photon-ledger owner for absorbed-by-absorber photons",
            "keep the prescribed-rate (P19) branch as an exclusive regression mode, never added to endogenous cohorts"],
        "acceptance_tests_if_unblocked": [
            "T0 (first, before any low-z code) add Rust tests that DriverConfig::read(\"end_zbar=3.9\\n\") and "
            "DriverConfig::read(\"end_zbar=20.0\\n\") fail: the end_zbar guard of DriverConfig::validate has no test at "
            "56dc609e (unpinned_guards); the scale-domain test (pinned_guards_from_scan) stays unchanged",
            "T1 restart identity: the z = 4 checkpoints round-trip through the low-z reader (remap identity on the "
            "first 392 nodes) and the R106 117-step window replay is still bitwise identical (S8_REPLAY_COMPARISON.json)",
            "T2 photon count and augmented energy ledgers closed to the lock tolerance 1e-8 over zbar 4 -> 0",
            "T3 remap conserves photon number and energy exactly",
            "T4 quasar/stellar source cell moments versus direct quadrature (<= 1e-7, as AxbiSource normalization)",
            "T5 prescribed-rate regression branch versus the P19 table nodes (as PUBLIC_UVB_RESULTS.json, 181 checks)",
            "T6 native tau(0 -> 4) versus the DonorMatchedContinuation band of S8_LOWZ_TAU.json (difference reported)",
            "T7 the guard tests listed in rust_tests_pinning_the_guards and the T0 tests still pass unchanged"],
        "r8_inventory": inv,
        "runtime_extrapolation_frozen_physics": cost,
        "donor_band_from_s8_lowz_tau": {"band_min": tau["donor_band_recomputed"]["band_min"],
                                        "band_max": tau["donor_band_recomputed"]["band_max"],
                                        "all_case_depths_inside": tau["summary"]["all_case_depths_inside_donor_band"]},
        "vo_probe_summary": vo,
        "literature_arxiv_verification": arx,
        "claim_class": "FEASIBILITY_RECORD (code locations, input inventory); no physics result",
        "wall_s": None}
    replay = json.loads((RESULTS / "S8_REPLAY_COMPARISON.json").read_text())
    result["inputs_sha256"] = {n: sha256_bytes((RESULTS / n).read_bytes()) for n in (
        "S8_LOWZ_TAU.json", "S8_REPLAY_COMPARISON.json", "S8_UVB_VO_PROBE.json")}
    result["derived_for_markdown"] = derive(tau, replay, result)
    result["receipts_written_this_run"] = [r["id"] for r in append_receipts(preexisting_receipts(inv, tau, replay))]
    result["wall_s"] = time.time() - t0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    args.md.write_text(render_markdown(result, tau, replay, args.out))
    print(json.dumps(result["verdict"], indent=1))
    print(json.dumps({k: (v.get("title"), v.get("missing")) for k, v in arx.get("entries", {}).items()}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
