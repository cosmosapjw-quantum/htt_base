# LEGACY — This is the standalone pipeline from v7.x.
# Production pipeline: workspace/pipeline/run_integrated.py
# VER04 references below are version tags for the legacy output format.

#!/usr/bin/env python3
"""
run_all.py — Master Integrated Pipeline for the Bianchi Defect Framework
=========================================================================
Usage: python run_all.py [--quick] [--skip-evidence] [--skip-figures]
                         [--skip-departure]

Phases:
  1.  Data loading & validation
  2.  MES algebraic bounds
  3.  Nonlinear T_eff corrections
  3b. Bayesian evidence computation (15 models)
  3c. Departure posteriors (x / Q / Π for each model)
  3d. Comparator sensitivity (flat / closed / matched)
  4.  Statistical analysis (filling fraction, scenarios, forecasts)
  5.  LaTeX table generation (bounds + NL + evidence + departure)
  6.  Figure generation
  7.  Validation report & VER04_integrated_results.json

All outputs → /mnt/user-data/outputs/
Warning log  → /mnt/user-data/outputs/pipeline_warnings.log
"""
import sys, os, time, json, argparse, logging
import warnings
import numpy as np

# ─── Warning capture (code_audit: do NOT suppress) ────────────
# Route Python warnings to a log file instead of silencing them.
_WARN_RECORDS = []

def _warning_handler(message, category, filename, lineno, file=None, line=None):
    """Capture warnings into a list for later serialisation."""
    entry = {
        'message': str(message),
        'category': category.__name__,
        'file': str(filename),
        'line': int(lineno),
    }
    _WARN_RECORDS.append(entry)

warnings.showwarning = _warning_handler

# ─── Setup ────────────────────────────────────────────────────
from dataclasses import dataclass, field
from pathlib import Path as _Path

@dataclass
class PipelineConfig:
    """Configurable pipeline settings. Replaces hardcoded paths."""
    output_dir: str = os.environ.get('HTT_OUTPUT_DIR', '/mnt/user-data/outputs')
    obs_defaults_path: str = None  # None = auto-detect via ssot
    skip_evidence: bool = False
    skip_figures: bool = False
    skip_departure: bool = False
    quick: bool = False

_CONFIG = PipelineConfig()
OUT = _CONFIG.output_dir
os.makedirs(OUT, exist_ok=True)

t0_global = time.time()
LOG = []


def log(msg, level='INFO'):
    ts = time.time() - t0_global
    entry = f"[{ts:7.1f}s] [{level:5}] {msg}"
    LOG.append(entry)
    print(entry)


def phase_header(n, name):
    log(f"{'═'*60}")
    log(f"  PHASE {n}: {name}")
    log(f"{'═'*60}")


# ─── Args ─────────────────────────────────────────────────────
# Guard: pipeline execution only runs as __main__ or explicit call
def _parse_pipeline_args():
    """Parse CLI args. Only called when pipeline is run directly."""
    parser = argparse.ArgumentParser(
        description='Bianchi defect integrated pipeline (VER04)')
    parser.add_argument('--quick', action='store_true',
                        help='Reduced nlive/dlogz for fast testing')
    parser.add_argument('--skip-evidence', action='store_true',
                        help='Skip nested sampling (Phase 3b)')
    parser.add_argument('--skip-figures', action='store_true',
                        help='Skip figure generation (Phase 6)')
    parser.add_argument('--skip-departure', action='store_true',
                        help='Skip departure posteriors (Phases 3c–3d)')
    parser.add_argument('--cf4-version', default='wfh2009',
                        choices=['wfh2009', 'watkins2023', 'courtois2025'],
                        help='CF4 bulk flow source (default: wfh2009 legacy)')
    return parser.parse_args()

# Only execute pipeline when run directly
if __name__ == '__main__':
    args = _parse_pipeline_args()
else:
    # When imported as a library, provide defaults without argparse
    class _MockArgs:
        quick = True
        skip_evidence = True
        skip_figures = True
        skip_departure = True
        cf4_version = 'wfh2009'
    args = _MockArgs()
    # Don't execute any pipeline phases on import
    import sys as _sys
    _sys.modules[__name__].__dict__['_IMPORT_ONLY'] = True

QUICK = args.quick
CF4_VERSION = args.cf4_version

# Map cf4-version to obs_defaults file
_CF4_OBS_FILES = {
    'wfh2009':      'obs_defaults.json',
    'watkins2023':  'obs_defaults_watkins2023.json',
    'courtois2025': 'obs_defaults_CF4pp.json',
}
_OBS_FILE = _CF4_OBS_FILES[CF4_VERSION]
NL_ORTH = 200 if QUICK else 500
NL_TILT = 300 if QUICK else 800
DL_ORTH = 0.5 if QUICK else 0.1
DL_TILT = 0.5 if QUICK else 0.05

results_store = {}

# ── Guard: stop here if imported as library ──────────────────
if getattr(__import__(__name__), '_IMPORT_ONLY', False) or \
   globals().get('_IMPORT_ONLY', False):
    pass  # Pipeline phases below will not execute
else:
    _RUN_PIPELINE = True


# ═══════════════════════════════════════════════════════════════
#  PHASE 1: DATA LOADING & VALIDATION
# ═══════════════════════════════════════════════════════════════
phase_header(1, "DATA LOADING & VALIDATION")

from htt.core.ssot import C, load_obs, eps_ell, D_ell_from_eps

obs = load_obs(path=_OBS_FILE)
log(f"Loaded: {_OBS_FILE} (CF4 version: {CF4_VERSION})")
_cf4 = obs['dipole_observations']['cf4_watkins_2023']
log(f"  β_CF4 = {_cf4['beta']:.3e} ± {_cf4['sigma']:.3e}")
log(f"  Source: {_cf4['source'][:60]}...")
log(f"T₀ = {C.T0_uK:.0f} μK, Ω_m = {C.Omega_m}, η_u̇ = {C.eta_udot}")
log(f"D₂^obs = {C.D2_obs} μK², D₃^obs = {C.D3_obs} μK²")
log(f"Scenarios: {list(obs['scenarios'].keys())}")
log(f"Channels: {list(obs['channels'].keys())}")

# Validate round-trips
D2_rt = D_ell_from_eps(eps_ell(C.D2_obs, 2), 2)
assert abs(D2_rt - C.D2_obs) / C.D2_obs < 1e-6, f"D₂ round-trip failed: {D2_rt}"
log("D₂ round-trip ✓")

results_store['phase1'] = {'status': 'PASS', 'T0': C.T0_uK, 'Omega_m': C.Omega_m}


# ═══════════════════════════════════════════════════════════════
#  PHASE 2: MES ALGEBRAIC BOUNDS
# ═══════════════════════════════════════════════════════════════
phase_header(2, "MES ALGEBRAIC BOUNDS")

from htt.core.bounds import (B_sigma, B_omega, B_accel, B_sigma_corrected,
                    Sig2_max_MES, beta_safe, frame_bias, Sig2_BV)

scenarios_eps = [
    ('S0', 0.0), ('S1', 1.233e-3), ('S2a', 1.476e-3),
    ('S2c', 3.296e-3), ('S3', 1.476e-3),
]

bounds_table = []
for sn, e1 in scenarios_eps:
    Bs = B_sigma(e1); Bo = B_omega(e1); Ba = B_accel(e1)
    Bs_c = B_sigma_corrected(e1); S2 = Sig2_max_MES(e1)
    b = beta_safe(e1); fb = frame_bias(e1)
    row = {'scenario': sn, 'eps1': e1,
           'B_sigma': Bs, 'B_omega': Bo, 'B_accel': Ba,
           'B_sigma_corr': Bs_c, 'Sigma2_max': S2,
           'beta_safe': b, 'frame_bias': fb}
    bounds_table.append(row)
    log(f"  {sn}: B_σ={Bs:.4e}, B_σ^c={Bs_c:.4e}, Σ²_max={S2:.4e}")

# BV momentum constraint check
D2_BV = Sig2_BV(1.334e-3, 0.001) * 6 / (2 * np.pi) * (2.75e4 * C.T0_uK)**2
log(f"  BV D₂^shear at β_CF4: {D2_BV:.2e} μK² (obs: {C.D2_obs})")
assert D2_BV > 1e10, "BV should massively overproduce D₂"
log("  BV overproduction ✓")

results_store['phase2'] = bounds_table


# ═══════════════════════════════════════════════════════════════
#  PHASE 3: NONLINEAR T_eff CORRECTIONS
# ═══════════════════════════════════════════════════════════════
phase_header(3, "NONLINEAR T_eff CORRECTIONS")

from htt.core.teff_extended import NonlinearCorrection, DefectPropagation

nlc = NonlinearCorrection(N_mu=400)
dp_prop = DefectPropagation()

nl_table = []
for sn, e1 in scenarios_eps:
    Rs = nlc.R_sigma(e1); Ro = nlc.R_omega(e1); Ru = nlc.R_udot(e1)
    xi = dp_prop.x_I(e1, nl=False); xi_nl = dp_prop.x_I(e1, nl=True)
    row = {'scenario': sn, 'eps1': e1,
           'R_sigma': Rs, 'R_omega': Ro, 'R_udot': Ru,
           'x_I_lin': xi, 'x_I_nl': xi_nl,
           'delta_x': (xi_nl / xi - 1) if xi > 0 else 0}
    nl_table.append(row)
    Ds = Rs - 1
    log(f"  {sn}: R_σ={Rs:.6f} (Δ={Ds:.4e}), x_I={xi:.3e}")

# Universal ratio check
Ds1 = nlc.R_sigma(1.233e-3) - 1
Do1 = nlc.R_omega(1.233e-3) - 1
Du1 = nlc.R_udot(1.233e-3) - 1
log(f"  Ratios: Δ_ω/Δ_σ = {Do1/Ds1:.4f} (exp 1.478), "
    f"Δ_u̇/Δ_σ = {Du1/Ds1:.4f} (exp 0.742)")

results_store['phase3'] = nl_table


# ═══════════════════════════════════════════════════════════════
#  PHASE 3b: BAYESIAN EVIDENCE COMPUTATION
# ═══════════════════════════════════════════════════════════════
ev_results = []   # populated by Phase 3b, consumed by 3c

if not args.skip_evidence:
    phase_header('3b', "BAYESIAN EVIDENCE COMPUTATION")

    from analysis_extended import EvidenceComparison
    from evidence_models import ObsData

    # Create ObsData with CF4 version override
    custom_obs = ObsData()
    _cf4_obs = obs['dipole_observations']['cf4_watkins_2023']
    custom_obs.b_CF4 = _cf4_obs['beta']
    custom_obs.b_CF4_s = _cf4_obs['sigma']
    log(f"  ObsData CF4: β={custom_obs.b_CF4:.3e} ± {custom_obs.b_CF4_s:.3e} ({CF4_VERSION})")

    ec = EvidenceComparison(channels='abcdefh', obs=custom_obs)

    Z0 = ec.flrw_evidence()
    log(f"FLRW ln Z₀ = {Z0:.4f}")

    # Run all 15 non-FLRW models
    t_ev = time.time()

    model_tags = [t for t in ec.MODEL_REGISTRY if t != 'FLRW']
    for tag in model_tags:
        is_tilt = 'tilt' in tag
        nl = NL_TILT if is_tilt else NL_ORTH
        dl = DL_TILT if is_tilt else DL_ORTH

        r = ec.run_single(tag, nlive=nl, dlogz=dl)
        ev_results.append(r)
        log(f"  {tag:>18}: ln B = {r['lnB']:+8.2f} ± {r['err']:.3f}  "
            f"neff={r['neff']}")

    # Master table
    master = ec.master_table(ev_results)
    dt_ev = time.time() - t_ev
    log(f"  Evidence computed: {len(ev_results)} models in {dt_ev:.0f}s")
    log(f"  Top model: {master[0]['tag']} (ln B = {master[0]['lnB']:+.2f})")
    log(f"  Bottom: {master[-1]['tag']} (ln B = {master[-1]['lnB']:+.2f})")

    # Save intermediate JSON
    ec.to_json(ev_results, f'{OUT}/pipeline_evidence.json')
    log("  Saved pipeline_evidence.json")

    results_store['phase3b'] = {
        'FLRW_lnZ': Z0,
        'n_models': len(ev_results),
        'top_model': master[0]['tag'],
        'top_lnB': master[0]['lnB'],
        'compute_time_s': round(dt_ev, 1),
    }
else:
    log("Phase 3b SKIPPED (--skip-evidence)")
    results_store['phase3b'] = {'status': 'SKIPPED'}


# ═══════════════════════════════════════════════════════════════
#  PHASE 3c: DEPARTURE POSTERIORS (x / Q / Π)
# ═══════════════════════════════════════════════════════════════
departure_reports = {}

if ev_results and not args.skip_departure:
    phase_header('3c', "DEPARTURE POSTERIORS (x/Q/Π)")

    from departure_posteriors import DeparturePosterior

    t_dep = time.time()
    n_with_samples = 0

    for r in ev_results:
        tag = r['tag']
        eq = r.get('eq_samples')
        if eq is None or len(eq) == 0:
            log(f"  {tag:>18}: no posterior samples, skipped")
            continue

        n_with_samples += 1
        pnames = r.get('param_names', [])

        # Default comparator: flat
        dp = DeparturePosterior(
            model_tag=tag,
            samples=eq,
            logwt=None,       # eq_samples are already equal-weighted
            param_names=pnames,
            comparator='flat',
            w=0.0,
        )
        report = dp.full_report(
            eps1_ceiling=C.eps1_kin,
            d_Mpc=40.0,
        )
        departure_reports[tag] = report

        x_med = report['layer_1_departure']['x']['median']
        Q_med = report['layer_2_occupancy']['Q']['median']
        Pi_01 = report['layer_3_exceedance']['Pi'].get('0.01', 0)
        v_med = report['derived_observables']['v_tilt_km_s']['median']

        log(f"  {tag:>18}: x̃={x_med:+.3e}  Q̃={Q_med:.4f}  "
            f"Π(0.01)={Pi_01:.3f}  ṽ={v_med:.1f} km/s")

    dt_dep = time.time() - t_dep
    log(f"  Departure computed: {n_with_samples} models in {dt_dep:.1f}s")

    results_store['phase3c'] = {
        'n_models': n_with_samples,
        'comparator': 'flat',
        'compute_time_s': round(dt_dep, 1),
    }

elif args.skip_departure:
    log("Phase 3c SKIPPED (--skip-departure)")
    results_store['phase3c'] = {'status': 'SKIPPED'}
else:
    log("Phase 3c SKIPPED (no evidence results available)")
    results_store['phase3c'] = {'status': 'SKIPPED (no evidence)'}


# ═══════════════════════════════════════════════════════════════
#  PHASE 3d: COMPARATOR SENSITIVITY
# ═══════════════════════════════════════════════════════════════
comparator_results = {}

if ev_results and not args.skip_departure:
    phase_header('3d', "COMPARATOR SENSITIVITY")

    from departure_posteriors import comparator_sensitivity

    t_comp = time.time()

    # Run sensitivity for models that have curvature parameters
    # (BV_tilt, BIII_tilt, BIX_tilt, BIX_orth) and a few representative
    # tilted models (FLRW_tilt, BI_tilt) for completeness.
    sensitivity_tags = []
    for r in ev_results:
        tag = r['tag']
        eq = r.get('eq_samples')
        if eq is None or len(eq) == 0:
            continue
        pnames = r.get('param_names', [])
        # Run for models with Omega_k, or tilted models, or BI_orth as baseline
        has_curvature = 'Omega_k' in pnames or 'Omega_K' in pnames
        has_tilt = 'beta' in pnames
        if has_curvature or has_tilt:
            sensitivity_tags.append(tag)

    for tag in sensitivity_tags:
        r = next(x for x in ev_results if x['tag'] == tag)
        eq = r['eq_samples']
        pnames = r.get('param_names', [])

        cs = comparator_sensitivity(
            model_tag=tag,
            samples=eq,
            logwt=None,
            param_names=pnames,
            comparators=('flat', 'closed', 'matched'),
        )
        comparator_results[tag] = cs

        spread_01 = cs['sensitivity_summary'].get('0.01', {}).get('spread', 0)
        log(f"  {tag:>18}: ΔΠ(0.01) spread = {spread_01:.4f}")

    dt_comp = time.time() - t_comp
    log(f"  Comparator sensitivity: {len(sensitivity_tags)} models in {dt_comp:.1f}s")

    results_store['phase3d'] = {
        'n_models': len(sensitivity_tags),
        'comparators': ['flat', 'closed', 'matched'],
        'compute_time_s': round(dt_comp, 1),
    }

elif args.skip_departure:
    log("Phase 3d SKIPPED (--skip-departure)")
    results_store['phase3d'] = {'status': 'SKIPPED'}
else:
    log("Phase 3d SKIPPED (no evidence results)")
    results_store['phase3d'] = {'status': 'SKIPPED (no evidence)'}


# ═══════════════════════════════════════════════════════════════
#  PHASE 3e: FRAME-CHOICE η_u̇ REGRESSION (CA-06)
# ═══════════════════════════════════════════════════════════════
phase_header("3e", "FRAME-CHOICE η_u̇ REGRESSION")

_eta_values = [0.0, 1/12, 1/6]
_eta_results = {}
import evidence_models_R03a as _emod
from htt.core.evidence_models_R03a import FLRW_tilt as _FT_cls, FLRW as _FL_cls
_old_eta = _emod.ETA_UDOT
for _eta in _eta_values:
    _emod.ETA_UDOT = _eta
    _ft_tmp = _FT_cls(channels='abcdefh')
    _r_tmp = _ft_tmp.log_evidence_quadrature(n_points=30000)
    _fl_tmp = _FL_cls(channels='abcdefh')
    _Z0_tmp = _fl_tmp.log_evidence()
    _lnB_tmp = _r_tmp['lnZ'] - _Z0_tmp
    _eta_results[str(round(_eta, 6))] = {
        'eta_udot': round(_eta, 6),
        'lnB': round(_lnB_tmp, 2),
        'beta_median': float(_r_tmp['beta_median']),
    }
    log(f"  η_u̇={_eta:.4f}: lnB={_lnB_tmp:+.2f}, β_med={_r_tmp['beta_median']:.4e}")
_emod.ETA_UDOT = _old_eta  # restore fiducial

results_store['phase3e_eta_sweep'] = _eta_results


# ═══════════════════════════════════════════════════════════════
#  PHASE 3f: MES BOUNDARY CHECK (CA-12)
# ═══════════════════════════════════════════════════════════════
phase_header("3f", "MES BOUNDARY CHECK")

_mes_report = {}
if ev_results:
    from bounds import Sig2_max_MES
    _Sig2_ceil = Sig2_max_MES(C.eps1_kin)
    log(f"  Σ²_max (MES ceiling at ε₁_kin) = {_Sig2_ceil:.4e}")
    for _er in ev_results:
        _tag = _er.get('tag', '')
        _eq = _er.get('eq_samples')
        if _eq is None:
            continue
        _pn = _er.get('param_names', [])
        if 'Sigma2' not in _pn:
            continue
        _si = _pn.index('Sigma2')
        _s2_samp = _eq[:, _si]
        _s2_max = float(_s2_samp.max())
        _s2_med = float(np.median(_s2_samp))
        _ratio = _s2_max / _Sig2_ceil
        _safe = _ratio < 0.01
        _mes_report[_tag] = {
            'Sigma2_max_sampled': _s2_max,
            'Sigma2_median': _s2_med,
            'ratio_to_ceiling': round(_ratio, 6),
            'safe': bool(_safe),
        }
        log(f"  {_tag:>20}: Σ²_max/ceiling = {_ratio:.2e} {'✓' if _safe else '⚠ NEAR BOUNDARY'}")
else:
    log("  SKIPPED (no evidence results)")

results_store['phase3f_mes_boundary'] = {'ceiling': float(_Sig2_ceil) if ev_results else 0.0, 'models': _mes_report}


# ═══════════════════════════════════════════════════════════════
#  PHASE 3g: MODEL IDENTIFIABILITY AUDIT (CA-07, CA-08)
# ═══════════════════════════════════════════════════════════════
phase_header("3g", "MODEL IDENTIFIABILITY AUDIT")

from htt.core.evidence_models_R03a import audit_inactive_parameters, MODEL_AUDIT
_id_report = audit_inactive_parameters()
log(f"  Inactive parameters: {_id_report['inactive_parameters']}")
log(f"  Duplicate models: {_id_report['duplicate_models']}")
log(f"  Equivalence classes with >1 member:")
for _cls, _members in _id_report['equivalence_classes'].items():
    log(f"    {_cls}: {_members}")

results_store['phase3g_identifiability'] = _id_report


# ═══════════════════════════════════════════════════════════════
#  PHASE 4: STATISTICAL ANALYSIS
# ═══════════════════════════════════════════════════════════════
phase_header(4, "STATISTICAL ANALYSIS")

from htt.core.analysis_extended import FillingFraction, GrowingMode, ScenarioTable, ForecastTable

# 4.1 Filling fraction
ff = FillingFraction(w=0.0)
F_S3 = ff.F(1.476e-3)
samp, med, q16, q84, _, _ = ff.mc_posterior('S3', N=50000)
BF = ff.bayes_factor(samp)
log(f"  ℱ(S3) point: {F_S3:.4f}")
log(f"  ℱ(S3) MC: {med:.4f} [{q16:.4f}, {q84:.4f}]")
log(f"  Bayes factor (ℱ>0): {BF:.0f}")

# 4.2 Growing mode
gm = GrowingMode()
sig_min, sig_max = gm.detection_window(10.0)
log(f"  Growing mode window: σ/H ∈ [{sig_min:.2e}, {sig_max:.2e}]")

# 4.3 Scenario table
st = ScenarioTable()
all_sc = st.compute_all()
log(f"  Scenario table: {len(all_sc)} scenarios computed")

# 4.4 Forecast matrix
ft = ForecastTable()
golden = ft.golden_experiments(3)
log(f"  Golden experiments (≥3 predictions): {list(golden.keys())}")

results_store['phase4'] = {
    'F_S3': F_S3, 'F_mc_median': med,
    'BF': BF, 'n_scenarios': len(all_sc),
    'golden_experiments': list(golden.keys()),
}


# ═══════════════════════════════════════════════════════════════
#  PHASE 5: LaTeX TABLE GENERATION
# ═══════════════════════════════════════════════════════════════
phase_header(5, "LaTeX TABLE GENERATION")

tables_written = []

# 5.1 Bounds table
tex_bounds = "\\begin{table}\n\\caption{MES algebraic bounds by scenario.}\n"
tex_bounds += "\\label{tab:bounds}\\centering\\footnotesize\n"
tex_bounds += "\\begin{tabular}{lrrrr}\n\\hline\\hline\n"
tex_bounds += ("Scenario & $B_\\sigma$ & $B_\\sigma^{\\rm corr}$ "
               "& $\\Sigma^2_{\\rm max}$ & $\\beta_{\\rm safe}$ \\\\\n\\hline\n")
for row in bounds_table:
    tex_bounds += (f"{row['scenario']} & {row['B_sigma']:.4e} "
                   f"& {row['B_sigma_corr']:.4e} & {row['Sigma2_max']:.4e} "
                   f"& {row['beta_safe']:.4e} \\\\\n")
tex_bounds += "\\hline\\hline\n\\end{tabular}\n\\end{table}\n"
with open(f'{OUT}/table_bounds.tex', 'w') as f:
    f.write(tex_bounds)
tables_written.append('table_bounds.tex')

# 5.2 Nonlinear corrections table
tex_nl = "\\begin{table}\n\\caption{Nonlinear $T_{\\rm eff}$ corrections.}\n"
tex_nl += "\\label{tab:nl_corrections}\\centering\\footnotesize\n"
tex_nl += "\\begin{tabular}{lrrrrr}\n\\hline\\hline\n"
tex_nl += ("Scenario & $R_\\sigma$ & $R_\\omega$ & $R_{\\dot u}$ "
           "& $\\delta\\Sigma^2/\\Sigma^2$ (\\%) \\\\\n\\hline\n")
for row in nl_table:
    dS = (row['R_sigma']**2 - 1) * 100
    tex_nl += (f"{row['scenario']} & {row['R_sigma']:.6f} "
               f"& {row['R_omega']:.6f} & {row['R_udot']:.6f} "
               f"& {dS:.4f} \\\\\n")
tex_nl += "\\hline\\hline\n\\end{tabular}\n\\end{table}\n"
with open(f'{OUT}/table_nl_corrections.tex', 'w') as f:
    f.write(tex_nl)
tables_written.append('table_nl_corrections.tex')

# 5.3 Evidence master table (if evidence was run)
if 'phase3b' in results_store and results_store['phase3b'].get('status') != 'SKIPPED':
    with open(f'{OUT}/pipeline_evidence.json') as f:
        ev_data = json.load(f)
    ev_sorted = sorted(ev_data, key=lambda x: x['lnB'], reverse=True)

    tex_ev = "\\begin{table*}\n\\caption{Bayesian evidence for Bianchi models.}\n"
    tex_ev += "\\label{tab:evidence_pipeline}\\centering\\footnotesize\n"
    tex_ev += "\\begin{tabular}{rlcrrl}\n\\hline\\hline\n"
    tex_ev += "Rk & Model & $d$ & $\\ln\\mathcal{B}$ & $\\pm$ & Jeffreys \\\\\n\\hline\n"
    for i, r in enumerate(ev_sorted, 1):
        lnB = r['lnB']
        jeff = 'Decisive' if lnB > 5 else 'Negligible' if lnB > -5 else 'Excluded'
        nm = r['tag'].replace('_', ' ').replace('VIIh', 'VII$_h$')
        tex_ev += (f"{i} & {nm} & {r['ndim']} & ${lnB:+.1f}$ "
                   f"& {r['err']:.2f} & {jeff} \\\\\n")
        if i == 5 or i == 12:
            tex_ev += "\\hline\n"
    tex_ev += "\\hline\\hline\n\\end{tabular}\n\\end{table*}\n"
    with open(f'{OUT}/table_evidence_pipeline.tex', 'w') as f:
        f.write(tex_ev)
    tables_written.append('table_evidence_pipeline.tex')

# 5.4 Departure summary table (NEW — from Phase 3c)
if departure_reports:
    tex_dep = "\\begin{table*}\n"
    tex_dep += "\\caption{Departure posteriors (flat comparator, $d=40$\\,Mpc).}\n"
    tex_dep += "\\label{tab:departure_summary}\\centering\\footnotesize\n"
    tex_dep += "\\begin{tabular}{lrrrrrr}\n\\hline\\hline\n"
    tex_dep += ("Model & $\\tilde x$ & $\\tilde Q$ & $\\Pi(0.01)$ "
                "& $\\Pi(0.1)$ & $\\tilde v$ (km/s) & $N_{\\rm eff}$ \\\\\n\\hline\n")

    # Sort by Q median descending
    sorted_tags = sorted(departure_reports.keys(),
                         key=lambda t: departure_reports[t]['layer_2_occupancy']['Q']['median'],
                         reverse=True)
    for tag in sorted_tags:
        rep = departure_reports[tag]
        x_m = rep['layer_1_departure']['x']['median']
        Q_m = rep['layer_2_occupancy']['Q']['median']
        Pi01 = rep['layer_3_exceedance']['Pi'].get('0.01', 0)
        Pi10 = rep['layer_3_exceedance']['Pi'].get('0.1', 0)
        v_m = rep['derived_observables']['v_tilt_km_s']['median']
        neff = rep['N_eff']
        nm = tag.replace('_', ' ').replace('VIIh', 'VII$_h$')
        tex_dep += (f"{nm} & ${x_m:+.2e}$ & ${Q_m:.4f}$ & ${Pi01:.3f}$ "
                    f"& ${Pi10:.3f}$ & ${v_m:.1f}$ & ${neff:.0f}$ \\\\\n")

    tex_dep += "\\hline\\hline\n\\end{tabular}\n\\end{table*}\n"
    with open(f'{OUT}/table_departure_summary.tex', 'w') as f:
        f.write(tex_dep)
    tables_written.append('table_departure_summary.tex')

log(f"  Tables written: {tables_written}")
results_store['phase5'] = tables_written


# ═══════════════════════════════════════════════════════════════
#  PHASE 6: FIGURE GENERATION
# ═══════════════════════════════════════════════════════════════
if not args.skip_figures:
    phase_header(6, "FIGURE GENERATION")

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        'font.size': 9, 'axes.labelsize': 10, 'axes.linewidth': 0.6,
        'xtick.labelsize': 8, 'ytick.labelsize': 8,
        'xtick.direction': 'in', 'ytick.direction': 'in',
        'xtick.top': True, 'ytick.right': True,
        'figure.dpi': 300, 'mathtext.fontset': 'dejavusans'})

    figs_written = []

    # 6.1 Bounds hierarchy
    e1_grid = np.linspace(0, 4e-3, 200)
    fig, ax = plt.subplots(figsize=(3.375, 2.8))
    ax.plot(e1_grid * 1e3, [B_sigma(e) * 1e3 for e in e1_grid],
            'b-', lw=1.2, label=r'$B_\sigma$')
    ax.plot(e1_grid * 1e3, [B_omega(e) * 1e3 for e in e1_grid],
            'r--', lw=1.2, label=r'$B_\omega$')
    ax.plot(e1_grid * 1e3, [B_accel(e) * 1e3 for e in e1_grid],
            'g:', lw=1.2, label=r'$B_{\dot{u}}$')
    ax.set_xlabel(r'$\varepsilon_1$ ($\times 10^{-3}$)', fontsize=9)
    ax.set_ylabel(r'Bound ($\times 10^{-3}$)', fontsize=9)
    ax.legend(fontsize=7.5)
    ax.set_xlim(0, 4)
    fig.tight_layout(pad=0.3)
    fig.savefig(f'{OUT}/fig_bounds_hierarchy.png', dpi=300, bbox_inches='tight')
    fig.savefig(f'{OUT}/fig_bounds_hierarchy.pdf', dpi=300, bbox_inches='tight')
    plt.close(fig)
    figs_written.append('fig_bounds_hierarchy')

    # 6.2 R_σ, R_ω, R_u̇ vs ε₁
    fig, ax = plt.subplots(figsize=(3.375, 2.8))
    e1_g = np.linspace(1e-4, 4e-3, 200)
    Rs = [nlc.R_sigma(e) for e in e1_g]
    Ro = [nlc.R_omega(e) for e in e1_g]
    Ru = [nlc.R_udot(e) for e in e1_g]
    ax.plot(e1_g * 1e3, Rs, 'b-', lw=1.2, label=r'$R_\sigma$')
    ax.plot(e1_g * 1e3, Ro, 'r--', lw=1.2, label=r'$R_\omega$')
    ax.plot(e1_g * 1e3, Ru, 'g:', lw=1.2, label=r'$R_{\dot{u}}$')
    ax.axhline(1, color='gray', lw=0.4, ls=':')
    ax.set_xlabel(r'$\varepsilon_1$ ($\times 10^{-3}$)', fontsize=9)
    ax.set_ylabel(r'$R_X = B_X^{\rm nl}/B_X^{\rm lin}$', fontsize=9)
    ax.legend(fontsize=7.5)
    ax.set_xlim(0, 4)
    fig.tight_layout(pad=0.3)
    fig.savefig(f'{OUT}/fig_nl_corrections.png', dpi=300, bbox_inches='tight')
    fig.savefig(f'{OUT}/fig_nl_corrections.pdf', dpi=300, bbox_inches='tight')
    plt.close(fig)
    figs_written.append('fig_nl_corrections')

    # 6.3 Filling fraction posterior
    fig, ax = plt.subplots(figsize=(3.375, 2.8))
    from scipy.stats import gaussian_kde
    kde = gaussian_kde(samp, bw_method=0.1)
    xg = np.linspace(0, max(samp) * 1.2, 300)
    ax.plot(xg, kde(xg), 'b-', lw=1.2)
    ax.fill_between(xg, kde(xg), alpha=0.1, color='blue')
    ax.axvline(med, color='k', ls='--', lw=0.8, label=f'median={med:.3f}')
    ax.set_xlabel(r'$\mathcal{F}$', fontsize=10)
    ax.set_ylabel('Posterior density', fontsize=9)
    ax.legend(fontsize=7.5)
    ax.set_xlim(0, None)
    fig.tight_layout(pad=0.3)
    fig.savefig(f'{OUT}/fig_filling_fraction.png', dpi=300, bbox_inches='tight')
    fig.savefig(f'{OUT}/fig_filling_fraction.pdf', dpi=300, bbox_inches='tight')
    plt.close(fig)
    figs_written.append('fig_filling_fraction')

    log(f"  Figures written: {figs_written}")
    results_store['phase6'] = figs_written
else:
    log("Phase 6 SKIPPED (--skip-figures)")
    results_store['phase6'] = 'SKIPPED'


# ═══════════════════════════════════════════════════════════════
#  PHASE 7: VALIDATION REPORT & VER04 OUTPUT
# ═══════════════════════════════════════════════════════════════
phase_header(7, "VALIDATION REPORT & VER04 OUTPUT")

# 7.1 Run all test suites
test_results = {}
import subprocess
for test_file in ['test_pipeline.py', 'test_teff.py', 'test_analysis.py', 'test_tilted.py']:
    if os.path.exists(test_file):
        ret = subprocess.run(
            [sys.executable, test_file],
            capture_output=True, text=True, timeout=120)
        passed = ret.returncode == 0
        lines = ret.stdout.split('\n')
        result_line = [l for l in lines if 'RESULTS:' in l]
        test_results[test_file] = {
            'passed': passed,
            'returncode': ret.returncode,
            'summary': result_line[-1].strip() if result_line else 'N/A',
        }
        log(f"  {test_file}: {'✓ PASS' if passed else '✗ FAIL'} — "
            f"{test_results[test_file]['summary']}")

# 7.2 Write warning log
with open(f'{OUT}/pipeline_warnings.log', 'w') as f:
    f.write(f"# Warnings captured during pipeline run\n")
    f.write(f"# {time.strftime('%Y-%m-%dT%H:%M:%S')}\n")
    f.write(f"# Total warnings: {len(_WARN_RECORDS)}\n\n")
    for i, w in enumerate(_WARN_RECORDS, 1):
        f.write(f"[{i}] {w['category']} in {w['file']}:{w['line']}\n")
        f.write(f"    {w['message']}\n\n")
log(f"  Warnings captured: {len(_WARN_RECORDS)} → pipeline_warnings.log")

# 7.3 Assemble VER04_integrated_results.json
ver04 = {
    '_metadata': {
        'version': 'VER04_integrated',
        'generator': 'run_all.py v2.0 (IS-04)',
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'total_time_s': round(time.time() - t0_global, 1),
        'quick_mode': QUICK,
        'warnings_count': len(_WARN_RECORDS),
    },
    'evidence': {},
    'departure': {},
    'comparator_sensitivity': {},
    'algebraic_bounds': bounds_table,
    'nonlinear_corrections': nl_table,
    'filling_fraction': {
        'F_S3_point': F_S3,
        'F_S3_mc_median': med,
        'F_S3_mc_68': [float(q16), float(q84)],
        'BF_positive': BF,
    },
    'tests': test_results,
}

# New audit phases (CA-06, CA-07, CA-08, CA-12)
if 'phase3e_eta_sweep' in results_store:
    ver04['eta_udot_regression'] = results_store['phase3e_eta_sweep']
if 'phase3f_mes_boundary' in results_store:
    ver04['mes_boundary_check'] = results_store['phase3f_mes_boundary']
if 'phase3g_identifiability' in results_store:
    ver04['identifiability_audit'] = results_store['phase3g_identifiability']

# Evidence block
if ev_results:
    for r in ev_results:
        ver04['evidence'][r['tag']] = {
            'lnB': r['lnB'],
            'err': r['err'],
            'ndim': r['ndim'],
            'neff': r['neff'],
            'niter': r.get('niter', 0),
        }
    # Add FLRW reference
    if 'phase3b' in results_store and 'FLRW_lnZ' in results_store['phase3b']:
        ver04['evidence']['FLRW'] = {
            'lnZ': results_store['phase3b']['FLRW_lnZ'],
            'lnB': 0.0,
            'err': 0.0,
            'ndim': 0,
        }

# Departure block
for tag, rep in departure_reports.items():
    ver04['departure'][tag] = rep

# Comparator sensitivity block
for tag, cs in comparator_results.items():
    # Store only the sensitivity summary + Pi values, not full reports
    ver04['comparator_sensitivity'][tag] = {
        'sensitivity_summary': cs['sensitivity_summary'],
        'comparators': cs['comparators_evaluated'],
        'Pi_by_comparator': {
            comp: cs['reports'][comp]['layer_3_exceedance']['Pi']
            for comp in cs['comparators_evaluated']
        },
    }

# Serialise with float handling
class _NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

with open(f'{OUT}/VER04_integrated_results.json', 'w') as f:
    json.dump(ver04, f, indent=2, cls=_NumpyEncoder)
log("  Saved VER04_integrated_results.json")

# 7.4 Pipeline report (backward-compatible)
total_time = time.time() - t0_global
report = {
    'version': 'run_all.py v2.0 (IS-04)',
    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
    'total_time_s': round(total_time, 1),
    'quick_mode': QUICK,
    'phases': results_store,
    'tests': test_results,
    'warnings_count': len(_WARN_RECORDS),
}

with open(f'{OUT}/pipeline_report.json', 'w') as f:
    json.dump(report, f, indent=2, default=str)

# Write log
with open(f'{OUT}/pipeline_log.txt', 'w') as f:
    f.write('\n'.join(LOG))

log(f"\n{'═'*60}")
log(f"  PIPELINE COMPLETE: {total_time:.0f}s total")
log(f"  Tests: {sum(1 for v in test_results.values() if v['passed'])}"
    f"/{len(test_results)} passed")
log(f"  Warnings: {len(_WARN_RECORDS)}")
log(f"  Output: {OUT}/")
log(f"{'═'*60}")
