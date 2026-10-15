"""C8-OBS-MES-EPS: source-locked low-ell processing diagnostics, no EGS admission.

Standalone read-only analyzer for the exact 2026-10-15 HTT archived Planck
same-sky and FFP10 same-simulation-pair coefficients. The measured scalar
sqrt(C_ell)/T0 is NOT an EGS covariant epsilon_ell derivative envelope.

No unqualified Bianchi identification, mask/beam deconvolution, sky-independent
product stacking, or physical null p-values are computed here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np

T0_MICROK = 2.72548e6
# Exact Dropbox-synced input bytes materialized in this run, not aliases to newer data.
INPUT_SHA256: dict[str, str] = {
    "loop5/result.json": "abbc49075634899499f1ba615c5f2ba0192e4f949d3d6cc8bfe2171bf862312a",
    "loop5/retained_common_support_coefficients.npz": "900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459",
    "loop6/result.json": "486b92e558296aab2a465fe01292ec2e3ad5aa4077bf8c80c09e3ebcf459509d",
    "loop7/result.json": "124f9e5dabbf513461365d2cd8afc2d97f2b52b0a8697bc0cee2a941f937c542",
    "ffp_pilot/pilot_features_coefficients.npz": "41dc0b9396540d0d4d6488500f5e37f86167e28ecf88b299d7ae9fa8db180594",
    "ffp_pilot/declaration.json": "e2e79a0fd9a6e7b9de59327924b2c0c1d17b0b018ec92b9083c564eaf2a25e1e",
    "ffp_response/processing_coefficients.npz": "0c104e41b2cbd979bbb92b61a43744fb0e17376d26dd8a534cc90ab79ca23b08",
    "ffp_response/response.json": "e6c17c9704265fb535ed149ffc17acd2280f52cf581ef6b6324998157bcd56f8",
    "loop2/result.json": "35d2e33e0ce38970d4f24b19ac05d11f07efea06b63cd9c857d4e285d33b08c2",
}
# Real harmonics l2..5, each with 2l+1 orthonormal real coefficients.
SLICES = {2: (0, 5), 3: (5, 12), 4: (12, 21), 5: (21, 32)}
SAME_SKY_NINE = (
    "SMICA_HM1", "SMICA_HM2", "SMICA_OE1", "SMICA_OE2", "NILC_HM1",
    "NILC_HM2", "SMICA_FULL", "SMICA_noSZ_FULL", "NILC_FULL",
)


class MesEpsAuditError(ValueError):
    pass


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fp:
        for block in iter(lambda: fp.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_sources(root: Path) -> dict[str, str]:
    sha = {}
    for rel, expected in INPUT_SHA256.items():
        p = root / rel
        if not p.is_file():
            raise MesEpsAuditError(f"Missing source: {rel}")
        sha[rel] = file_sha256(p)
        if sha[rel] != expected:
            raise MesEpsAuditError(f"Source byte identity mismatch {rel}: {sha[rel]} != {expected}")
    return sha


def power_and_epsilon(a: np.ndarray, ell: int, t0_microk: float = T0_MICROK) -> tuple[np.ndarray, np.ndarray]:
    """Real-orthonormal multipole C_l, sqrt(C_l)/T0 along the last axis."""
    raw = np.asarray(a)
    v = np.asarray(a, dtype=np.float64) if np.issubdtype(raw.dtype, np.number) and not np.iscomplexobj(raw) else raw
    if ell not in SLICES or v.ndim < 1 or v.shape[-1] != 32:
        raise MesEpsAuditError("expected real harmonic ell2..5 last dimension 32")
    if not np.issubdtype(v.dtype, np.number) or np.iscomplexobj(v) or not np.isfinite(v).all():
        raise MesEpsAuditError("real finite harmonic coefficients required")
    if not np.isfinite(t0_microk) or t0_microk <= 0:
        raise MesEpsAuditError("positive finite thermodynamic temperature required")
    lo, hi = SLICES[ell]
    with np.errstate(over="raise", invalid="raise"):
        try:
            cl = np.sum(v[..., lo:hi] ** 2, axis=-1) / (2 * ell + 1)
        except FloatingPointError as exc:
            raise MesEpsAuditError("harmonic power exceeds finite numerical domain") from exc
    if not np.isfinite(cl).all():
        raise MesEpsAuditError("nonfinite harmonic power")
    return cl, np.sqrt(cl) / t0_microk


def registered_geodesic_proxy_anchors(e1: float, e2: float, e3: float) -> dict[str, float | bool]:
    """PR124 geodesic conditional algebra, NOT an observational MES anchor."""
    if not all(np.isfinite(x) and x >= 0 for x in (e1, e2, e3)):
        raise MesEpsAuditError("nonnegative finite epsilon proxies required")
    bs = (5 / 3) * e1 + 3 * e2 + (3 / 7) * e3
    bw = (10 / 3) * e1 + (2 / 15) * e2
    e1crit = (43 / 25) * e2 + (9 / 35) * e3
    # The registered strict domain is rational. Float evaluation of B_sigma-B_omega
    # can turn an exact decimal boundary into a false positive.
    f1, f2, f3 = (Fraction(str(x)) for x in (e1, e2, e3))
    exact_bs = Fraction(5, 3) * f1 + 3 * f2 + Fraction(3, 7) * f3
    exact_bw = Fraction(10, 3) * f1 + Fraction(2, 15) * f2
    strict = exact_bs > exact_bw > 0
    return {
        "B_sigma": float(bs),
        "B_omega": float(bw),
        "e1crit_strict_hierarchy": float(e1crit),
        "strict_hierarchy": bool(strict),
        "Sigma2_geodesic_algebraic_ceil": float(1.5 * bs * bs),
        "W2_geodesic_algebraic_ceil": float(1.5 * bw * bw),
    }


def finite_shell_bound_per_microK(operator_norm: float, ell: int) -> float:
    """Lipschitz bound per 1 microK omitted-shell Euclidean norm.

    ||delta a_l|| <= ||K||_2 E_H within an EXACT, fixed finite-shell
    masking/OLS basis. Does not cover any unbounded upstream modes.
    """
    if ell not in SLICES or not np.isfinite(operator_norm) or operator_norm < 0:
        raise MesEpsAuditError("invalid shell norm or multipole")
    return float(operator_norm / (np.sqrt(2 * ell + 1) * T0_MICROK))


def paired_spread(obs: np.ndarray, simulations: np.ndarray, ell: int, train_rows: int = 60) -> dict[str, Any]:
    """Retrospective source-processing spread per paired latent-sky realization.

    Each simulation sky, NOT each processing choice, is the unit. The statistic
    was not preregistered; no cosmological p-value or CI is returned.
    """
    a = np.asarray(obs, float)
    x = np.asarray(simulations, float)
    if (a.ndim != 2 or a.shape[1] != 32 or x.ndim != 3 or x.shape[0] != a.shape[0]
        or x.shape[2] != 32 or a.shape[0] < 2 or train_rows < 0
        or x.shape[1] <= train_rows or not np.isfinite(a).all() or not np.isfinite(x).all()):
        raise MesEpsAuditError("matched processing branches with paired sky IDs required")
    _, eps_obs = power_and_epsilon(a, ell)
    _, eps_pair = power_and_epsilon(x, ell)
    span_obs = float(np.ptp(eps_obs))
    spans = np.ptp(eps_pair, axis=0)
    heldout_spans = spans[train_rows:]
    exceeded = int(np.count_nonzero(heldout_spans >= span_obs))
    return {
        "ell": int(ell),
        "n_processing_options_one_observed_sky": int(a.shape[0]),
        "n_paired_simulation_skies": int(x.shape[1]),
        "training_pairs_not_used_for_comparison": int(train_rows),
        "heldout_pairs_conditional": int(heldout_spans.size),
        "observed_eps_each_processing": [float(u) for u in eps_obs],
        "observed_eps_spread": span_obs,
        "observed_eps_spread_over_mean": float(span_obs / np.mean(eps_obs)) if np.mean(eps_obs) > 0 else None,
        "paired_heldout_spread_q05_q50_q95_q99": [float(q) for q in np.quantile(heldout_spans, [0.05, 0.5, 0.95, 0.99])],
        "paired_heldout_spread_max": float(heldout_spans.max()),
        "paired_heldout_spread_exceedances": exceeded,
        "exploratory_rank_fraction": float((1 + exceeded) / (1 + heldout_spans.size)),
        "rank_interpretation": "RETROSPECTIVE_CONDITIONAL_SIMULATION_COMPARISON_NOT_PHYSICAL_P_VALUE",
        "independence_unit": "ONE_LATENT_SKY_AND_ITS_SIX_PROCESSING_IMAGES",
    }


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_result(inputs: Path) -> dict:
    sha = validate_sources(inputs)
    loop5 = _read_json(inputs / "loop5/result.json")
    loop6 = _read_json(inputs / "loop6/result.json")
    loop7 = _read_json(inputs / "loop7/result.json")
    ffp_response = _read_json(inputs / "ffp_response/response.json")
    ffp_decl = _read_json(inputs / "ffp_pilot/declaration.json")
    loop2 = _read_json(inputs / "loop2/result.json")
    with np.load(inputs / "loop5/retained_common_support_coefficients.npz", allow_pickle=False) as obj:
        names = tuple(obj["names_T"].tolist()); coeff = obj["coeff_T"].copy()
    if names != SAME_SKY_NINE or coeff.shape != (9, 32):
        raise MesEpsAuditError("wrong nine same-sky source processing names/order/shape")
    if loop5["common_T_nside64_pixel_count"] != 26846 or loop5["nside64_pixels_total"] != 49152:
        raise MesEpsAuditError("source-matched Loop5 mask is not the pinned one")
    registry = loop7["active_PR124_geodesic_algebraic_e1_zero_scenarios"]
    power_ref = loop6["actual_same_sky_planck_map_multipole_scalar_conventions"]
    if set(registry) != set(names) or set(power_ref) != set(names):
        raise MesEpsAuditError("missing loop6/loop7 source partner")
    nine = {}
    for idx, name in enumerate(names):
        c2, e2 = (float(x) for x in power_and_epsilon(coeff[idx], 2))
        c3, e3 = (float(x) for x in power_and_epsilon(coeff[idx], 3))
        for ell, c, eps in [(2, c2, e2), (3, c3, e3)]:
            if not np.isclose(c, power_ref[name][f"C{ell}"], rtol=1e-12, atol=1e-10):
                raise MesEpsAuditError("Loop5 harmonic power does not reconstruct Loop6 source")
            if not np.isclose(eps, registry[name][f"eps{ell}_sqrtCl_over_T0_proxy"], rtol=1e-12, atol=1e-18):
                raise MesEpsAuditError("Loop7 input epsilon not matched to Loop5")
        anchor = registered_geodesic_proxy_anchors(0, e2, e3)
        for k, bound in [("registered_geodesic_sigma_sector_anchor", anchor["Sigma2_geodesic_algebraic_ceil"]),
                         ("registered_geodesic_omega_sector_anchor", anchor["W2_geodesic_algebraic_ceil"])]:
            if not np.isclose(bound, registry[name][k], rtol=2e-12, atol=1e-24):
                raise MesEpsAuditError("PR124 registered anchor mismatch")
        for status in ("geodesic_acceleration_sector_anchor_status", "anisotropic_curvature_anchor_status"):
            if registry[name][status] != "NO_MES_ANCHOR":
                raise MesEpsAuditError("unexpected physical sector promotion")
        if registry[name]["CF4_apparent_shear_proxy_to_geodesic_MES_stress_status"] != "CHANNEL_MISMATCH":
            raise MesEpsAuditError("typed source mismatch not preserved")
        nine[name] = {"C2_microK2":c2,"C3_microK2":c3,"eps2_proxy":e2,"eps3_proxy":e3,
                      "e1residual_assumed":0,"e1crit_for_strict_geodesic_hierarchy":anchor["e1crit_strict_hierarchy"],
                      "Sigma2_geodesic_algebraic_ceil_e1_0":anchor["Sigma2_geodesic_algebraic_ceil"],
                      "W2_geodesic_algebraic_ceil_e1_0":anchor["W2_geodesic_algebraic_ceil"]}
    same_sky_ranges={}
    for ell in [2,3]:
        e = np.array([nine[n][f"eps{ell}_proxy"] for n in names])
        same_sky_ranges[f"ell{ell}"]={"min":float(e.min()),"max":float(e.max()),
          "spread":float(np.ptp(e)),"spread_over_SMICA_FULL":float(np.ptp(e)/nine['SMICA_FULL'][f'eps{ell}_proxy'])}

    with np.load(inputs / "ffp_response/processing_coefficients.npz", allow_pickle=False) as obj:
        obs = obj["observed"].copy(); sky_pairs = obj["paired"].copy()
    with np.load(inputs / "ffp_pilot/pilot_features_coefficients.npz", allow_pickle=False) as obj:
        pilot_obs = obj["observed_retained_coefficients"]
        pilot_pair = obj["paired_retained_coefficients"]
        sky_ids = tuple(obj["cmb_ids"].tolist()); noise_ids = tuple(obj["noise_ids"].tolist())
    if (obs.shape != (6,32) or sky_pairs.shape != (6,300,32)
        or not np.array_equal(obs[0],pilot_obs) or not np.array_equal(sky_pairs[0],pilot_pair)):
        raise MesEpsAuditError("FFP first response lane and original pilot misbound")
    if (len(set(sky_ids)) != 300 or len(set(noise_ids)) != 300
        or len(sky_ids) != 300 or len(noise_ids) != 300
        or ffp_decl["independence_unit"] != "latent_sky_realization"
        or len(ffp_decl["training_realization_ids"]) != 60
        or len(ffp_decl["null_realization_ids"]) != 240
        or loop2["registered_hyperparameters"]["train_rows"] != 60
        or loop2["registered_hyperparameters"]["calibration_rows"] != 240):
        # Only source-id and original declared pairing are needed; no actual proof of iid sky.
        raise MesEpsAuditError("FFP latent sky pairing provenance contract changed")
    specs = ffp_response["response"]
    if len(specs)!=6:
        raise MesEpsAuditError("FFP response operator count changed")
    six = {}
    for i,r in enumerate(specs):
        label = f"mask_{r['mask_threshold']}_lmax_{r['fit_lmax']}"
        c2,e2=(float(x) for x in power_and_epsilon(obs[i],2))
        c3,e3=(float(x) for x in power_and_epsilon(obs[i],3))
        if not np.isclose(c2,r['observed_C2_microK2'],rtol=1e-12,atol=1e-11):
            raise MesEpsAuditError("FFP response C2 mismatch")
        anchor = registered_geodesic_proxy_anchors(0,e2,e3)
        op=float(r['shell_response_spectral_norm'])
        six[label] = {
            "mask_threshold":float(r["mask_threshold"]),"fit_lmax":int(r["fit_lmax"]),
            "selected_pixels":int(r["selected_pixels"]),"fit_design_condition":float(r["fit_condition"]),
            "C2_microK2":c2,"C3_microK2":c3,"eps2_proxy":e2,"eps3_proxy":e3,
            "Sigma2_algebraic_proxy_e1_0":anchor["Sigma2_geodesic_algebraic_ceil"],
            "W2_algebraic_proxy_e1_0":anchor["W2_geodesic_algebraic_ceil"],
            "e1crit_for_strict_geodesic_hierarchy":anchor["e1crit_strict_hierarchy"],
            "finite_l6_to16_shell_K_spectral_norm":op,
            "finite_l6_to16_shell_eps2_bound_per_1_microK_l2":finite_shell_bound_per_microK(op,2),
            "finite_l6_to16_shell_eps3_bound_per_1_microK_l3":finite_shell_bound_per_microK(op,3),
            "truncated_shell_validity": "ONLY_UNDER_DECLARED_NSIDE64_MASK_OLS_FINITE_L6_TO16_BASIS_NOT_UNBOUNDED_UPSTREAM_RESPONSE",
        }
    ranks={f"ell{ell}":paired_spread(obs,sky_pairs,ell) for ell in [2,3]}
    beam=ffp_response["released_transfer"]["ell0_to16"]
    if len(beam)<4 or beam[0]!=0 or beam[1]!=0:
        raise MesEpsAuditError("released INT_BEAM monopole/dipole gate changed")
    return {
      "schema":"htt.C8_OBS_MES_EPS_diagnostic/1", "source_version":"2026-10-15 materialized Dropbox bytes",
      "source_sha256":sha, "reproduction_base_commit":"13d8d85fa470d645d008986e8f77d8d0f70fdf54",
      "claim_tier":"SOURCE_CONDITIONAL_PROCESSING_SENSITIVITY_NOT_COVARIANT_EGS_EPS",
      "harmonic_contract":{"T0_microK":T0_MICROK,"real_basis":"full-sky orthonormal real l2..5, 2l+1 components each", "source_coefficients":"masked simultaneous OLS; no upstream physical deconvolution", "eps_proxy":"sqrt(sum(real_a_lm**2)/(2l+1))/T0"},
      "loop5_nine_same_sky_same_mask":{"temperature_pixels":26846,"rows":nine,"ranges":same_sky_ranges,"joint_sky_independence":"ONE_SKY_NINE_PROCESSING_IMAGES"},
      "ffp10_six_pipeline_one_sky":{"observed_and_300_matched_skies":True,
         "pipelines":six,"paired_calibration":ranks,
         "independence_status":"CONDITIONAL_DELIVERED_SIMULATIONS_UNVERIFIED_EXCHANGEABILITY",
         "comparison_to_loop5":"FORBIDDEN_DIFFERENT_MASK_PIPELINES"},
      "released_smica_full_INT_BEAM":{"l0":beam[0],"l1":beam[1],"l2":beam[2],"l3":beam[3],
           "naive_l2_fractional_inverse_minus_one":float(abs(1/beam[2]-1)),
           "not_a_full_response_correction":True},
      "mes_theory":{"geodesic_coefficients":{"B_sigma":["5/3","3","3/7"],"B_omega":["10/3","2/15","0"]},
           "strict_e1_condition":"0<=eps1<(43/25)eps2+(9/35)eps3, provided eps2>0; each epsilon must be covariantly qualified",
           "actual_residual_cosmological_e1":"UNIDENTIFIED_NOT_ZERO",
           "acceleration":"NO_MES_ANCHOR", "anisotropic_curvature":"NO_MES_ANCHOR",
           "derivative_copernican_C1_C2":"UNIDENTIFIED_NOT_ZERO",
           "physical_sigma_or_omega_ceil":"NOT_ADMITTED"},
      "validation_gate":{"Loop5_to_Loop6_C2_C3":"CHECKED","Loop5_to_Loop7_EGS_proxy_and_registered_anchors":"CHECKED",
           "FFP_lane0_pilot_parity":"CHECKED","FFP_6x300_exact_pairing":"CHECKED",
           "native_bianchi_or_observer_response":"NOT_ATTEMPTED","physical_EGS_qualifications":"HOLD"},
    }


def cli(argv: list[str] | None = None) -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inputs",type=Path,required=True)
    ap.add_argument("--output",type=Path)
    ap.add_argument("--verify-only",action="store_true")
    args=ap.parse_args(argv)
    result=build_result(args.inputs)
    if args.verify_only:
        print(json.dumps({"status":"VALIDATED_SOURCE_AND_ALGEBRA","n_sources":len(result['loop5_nine_same_sky_same_mask']['rows'])}))
        return 0
    if args.output is None:
        ap.error("--output required unless --verify-only")
    args.output.mkdir(parents=True,exist_ok=True)
    dest=args.output/"C8_OBS_MES_EPS_RESULT.json"
    if dest.exists():
        raise MesEpsAuditError(f"create-only output already exists: {dest}")
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":"SOURCE_CONDITIONAL_NUMERIC_RESULT","path":str(dest),
     "observed_eps2_processing_spread":result['ffp10_six_pipeline_one_sky']['paired_calibration']['ell2']['observed_eps_spread'],
     "observed_eps3_processing_spread":result['ffp10_six_pipeline_one_sky']['paired_calibration']['ell3']['observed_eps_spread']}))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
