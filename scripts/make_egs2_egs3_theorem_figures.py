#!/usr/bin/env python3
"""REV-R126: figures for the EGS2 + EGS3 extension theorems and the PSD-cone
revisionary redesign, computed from the canonical repo modules.

Eight diagnostic-only program-theorem figures (synthetic / analytic illustration
of the Wolfram- and gate-verified identities; no observed data, no native
low-ell solver, no Bianchi family or geometry identification):

  egs3_a1_graded_rank      graded comparator response design + rank-2 reachable
                           (Sigma2, Omega_tilt) vs joint-null (W2, Omega_k).
  egs3_a3_evalue           Pi e-value calibration: empirical false-exceedance
                           rate stays under the Markov beta bound.
  egs2_nt2a1_fisher_floor  genuine multi-multipole Fisher-CR floor dropping
                           strictly below the single-l sqrt(2/5)=0.632.
  egs3_b1_floor_profile    the floor as a PROFILE in the shear scale k: it
                           saturates at 0.632 for super-horizon shear and drops
                           below only at finite k (sharpens NT2-A1).
  egs3_b2_volterra         depth gap as a Volterra functional of the tilt stress
                           with an exponential memory kernel exp(-3 int H).
  egs3_b3_vorticity        radial peculiar velocities are vorticity-blind
                           (n.Omega.n=0); the transverse channel re-opens it.
  egs2_nt2b1_bracket       two-sided shear/F bracket excluding zero (lower bound
                           is the strong new content).
  egs3_psd_cone            PSD-cone redesign: reachable eigen-directions (rank 2)
                           + the convex cone-shell bracket excluding the FLRW
                           vertex; x_C = tr(C M) is bit-identical.

Each figure ships a deterministic source.json (plotted values) + a gated
manifest; --check compares those sidecars byte-for-byte. Manifests are
content-addressed only (no git state) so --check is stable across commits.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = REPO_ROOT / "figures" / "current"

# canonical modules (import lazily inside _sources so --help works without deps)


def _config_hash(payload: dict) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _manifest(stem: str, theorem_id: str, title: str, source: dict) -> dict:
    return {
        "artifact_id": f"bass.theorem.{stem}",
        "artifact_path": f"figures/current/{stem}.png",
        "owner": "BASS",
        "implementation_scope": "bass_py",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "artifact_mode": "paper_appendix_conditioned",
        "allowed_use": "paper_appendix",
        "transfer_source": "none",
        "sky_support_status": "not_directional",
        "null_mock_status": "synthetic_only",
        "covariance_status": "synthetic_only",
        "family_identification": False,
        "native_solver_result": False,
        "theorem_id": theorem_id,
        "theorem_title": title,
        "source_json_path": f"figures/current/{stem}.source.json",
        "statistics_definitions": {"program": "egs2_egs3_extension", "theorem_id": theorem_id},
        "generating_command": "python scripts/make_egs2_egs3_theorem_figures.py",
        "config_hash": _config_hash(source),
        "created_by": "scripts/make_egs2_egs3_theorem_figures.py",
        "schema_version": "bass.egs2_egs3_theorem_figure.v1",
        "caption_policy": [
            "must_state_diagnostic_only",
            "must_not_use_for_family_identification_or_family_selection",
            "must_state_no_native_low_ell_solver_output",
        ],
        "caveats": [
            "Analytic/synthetic theorem illustration; not observed data.",
            "Conditional theorem; structural/limit statement, not a detection.",
            "No native low-ell solver output or morphology atlas is used.",
            "No Bianchi family-ID or geometry-detection claim is made.",
        ],
        "failed_gates": [
            "native_low_ell_solver_not_available",
            "family_morphology_atlas_not_available",
            "observational_closure_not_bound",
        ],
        "passed_gates": [
            "gate_test_present",
            "manifest_metadata_present",
            "claim_firewall_caption_review",
        ],
        "promotion_blockers": [
            "native_solver_validation_absent",
            "native_morphology_atlas_absent",
            "family_identification_blocked_pre_native_atlas",
        ],
        "publication_gates": {
            "bianchi_evidence_claim": "fail_program_theorem_only",
            "family_identification_claim": "fail_blocked_pre_native_atlas",
        },
        "required_gates": [
            "gate_test_present",
            "manifest_metadata_present",
            "claim_firewall_caption_review",
        ],
        "title": title,
        "source": source,
    }


def _sources() -> dict[str, dict]:
    from htt.obsstat.egs3_graded_comparator import (
        channel_response_design, identifiable_rank, CHANNELS, SECTORS,
    )
    from htt.obsstat.egs3_calibration import evalue_markov_calibration
    from htt.obsstat.egs2_fisher import fisher_floor, single_ell_sampling_dispersion
    from htt.bass.transfer.shear_quadrupole_seminative import (
        floor_profile_vs_k, shear_multipole_response,
    )
    from htt.obsstat.egs3_volterra_memory import volterra_shear
    from htt.obsstat.egs3_vorticity_channels import radial_response, transverse_response
    from htt.obsstat.egs2_shear_bracket import filling_bracket
    from htt.obsstat.egs3_psd_cone import (
        sector_matrix, xc_from_matrix, eigen_identifiability,
        cone_shell_membership, bracket_shell_from_a2a3,
    )
    from htt.obsstat.egs3_graded_comparator import graded_comparator

    # --- A1 graded rank --------------------------------------------------
    D = channel_response_design()
    rk = identifiable_rank()
    a1 = {
        "theorem_id": "EGS3-A1",
        "channels": list(CHANNELS),
        "sectors": list(SECTORS),
        "response_design": D.tolist(),
        "rank": rk.rank,
        "reachable_sectors": list(rk.reachable_sectors),
        "null_sectors": list(rk.null_sectors),
    }

    # --- A3 Pi e-value calibration --------------------------------------
    cal = evalue_markov_calibration(n_sims=40000, threshold=1.5, seed=71)
    a3 = {
        "theorem_id": "EGS3-A3",
        "beta_grid": list(cal.beta_grid),
        "empirical_false_rate": list(cal.empirical_false_rate),
        "null_mean_evalue": cal.null_mean_evalue,
        "markov_holds": cal.markov_holds,
        "n_sims": cal.n_sims,
    }

    # --- NT2-A1 genuine multi-multipole Fisher floor --------------------
    lmaxes = list(range(2, 41))
    floors = [fisher_floor(L, 1.0) for L in lmaxes]
    a1_floor = {
        "theorem_id": "NT2-A1",
        "lmax": lmaxes,
        "fisher_floor": floors,
        "single_ell_l2_dispersion": single_ell_sampling_dispersion(2, 1.0),
    }

    # --- B1 floor profile vs k ------------------------------------------
    kvals = np.logspace(-5.3, -3.0, 24)
    prof = floor_profile_vs_k(kvals.tolist(), lmax=40)
    kchi = [prof[k]["k_chi_star"] for k in sorted(prof)]
    floor_k = [prof[k]["floor"] for k in sorted(prof)]
    resp = shear_multipole_response(k=7.0e-5, lmax=20)
    b1 = {
        "theorem_id": "EGS3-B1",
        "k_chi_star": kchi,
        "floor": floor_k,
        "saturation_floor": single_ell_sampling_dispersion(2, 1.0),
        "r_ell_l": list(resp.ell),
        "r_ell": [resp.r_ell[l] for l in resp.ell],
    }

    # --- B2 Volterra depth memory ---------------------------------------
    z = np.linspace(0.0, 1.0, 41)
    H = 3.0
    pi_of_z = 1.0e-3 * (1.0 + 2.0 * z)        # depth-growing tilt stress
    sig = volterra_shear(lambda zz: 1.0e-3 * (1.0 + 2.0 * zz), z, H=H, sigma0=1.0e-3)
    kernel = np.exp(-3.0 * H * z)              # exponential memory kernel
    b2 = {
        "theorem_id": "EGS3-B2",
        "z": z.tolist(),
        "pi_of_z": pi_of_z.tolist(),
        "shear_volterra": sig.tolist(),
        "memory_kernel": kernel.tolist(),
        "H": H,
    }

    # --- B3 vorticity radial-blind vs transverse re-opening -------------
    rng = np.random.default_rng(91)
    n_hat = np.array([0.0, 0.0, 1.0])
    m_hat = np.array([1.0, 0.0, 0.0])         # transverse to n_hat
    omegas = rng.normal(0.0, 1.0, size=(400, 3))
    radial = [radial_response(o, n_hat) for o in omegas]
    transverse = [transverse_response(o, n_hat, m_hat) for o in omegas]
    b3 = {
        "theorem_id": "EGS3-B3",
        "radial_response": radial,
        "transverse_response": transverse,
        "radial_max_abs": float(np.max(np.abs(radial))),
        "transverse_max_abs": float(np.max(np.abs(transverse))),
    }

    # --- NT2-B1 two-sided shear/F bracket -------------------------------
    a2_grid = np.linspace(0.5, 6.0, 23)
    r_ratio = 0.5                              # a3/a2 fixed in the H3 regime
    f_lo, f_hi = [], []
    for a2 in a2_grid:
        fb = filling_bracket(float(a2), float(r_ratio * a2))
        f_lo.append(fb.F_lo)
        f_hi.append(fb.F_hi)
    nt2b1 = {
        "theorem_id": "NT2-B1",
        "a2": a2_grid.tolist(),
        "a3_over_a2": r_ratio,
        "F_lo": f_lo,
        "F_hi": f_hi,
        "excludes_zero": bool(filling_bracket(2.0, 1.0).excludes_zero),
    }

    # --- PSD-cone redesign ----------------------------------------------
    g = (2.0e-6, 1.5e-6, 8.0e-7, 3.0e-7)
    M = sector_matrix(g)
    ei = eigen_identifiability(M)
    s_lo, s_hi = bracket_shell_from_a2a3(5.0, 3.0)
    cs = cone_shell_membership(sector_matrix((4.0, 0.0, 0.0, 0.0)), s_lo, s_hi)
    psd = {
        "theorem_id": "EGS3-PSD",
        "sectors": list(SECTORS),
        "spectrum": list(g),
        "x_C_trace": xc_from_matrix(M),
        "x_C_graded": graded_comparator(*g).x_C,
        "bit_identical": bool(np.array_equal(xc_from_matrix(M), graded_comparator(*g).x_C)),
        "reachable_rank": ei.reachable_rank,
        "reachable_sectors": list(ei.reachable_sectors),
        "null_sectors": list(ei.null_sectors),
        "shell_s_lo": s_lo,
        "shell_s_hi": s_hi,
        "shell_lambda_sigma": cs.lambda_sigma,
        "shell_in": cs.in_shell,
        "excludes_vertex": cs.excludes_vertex,
    }

    return {"a1": a1, "a3": a3, "a1_floor": a1_floor, "b1": b1, "b2": b2,
            "b3": b3, "nt2b1": nt2b1, "psd": psd}


def _render(src: dict) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    blue, green, red, orange, grey = "#2563eb", "#16a34a", "#dc2626", "#ea580c", "#64748b"

    # A1 graded rank: response design heatmap + reachable/null labels
    a1 = src["a1"]
    D = np.array(a1["response_design"])
    fig, ax = plt.subplots(figsize=(5.6, 3.6))
    im = ax.imshow(D, cmap="Blues", aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(4)); ax.set_xticklabels(a1["sectors"], rotation=20, fontsize=8)
    ax.set_yticks(range(len(a1["channels"]))); ax.set_yticklabels(a1["channels"], fontsize=8)
    # colour the sector tick labels: green = reachable, red = joint null
    for tick, s in zip(ax.get_xticklabels(), a1["sectors"]):
        tick.set_color(green if s in a1["reachable_sectors"] else red)
    ax.set_title(f"EGS3-A1: graded comparator response, rank {a1['rank']}\n"
                 f"green reachable {{Σ²,Ω_tilt}}; red joint null {{W²,Ω_k}}")
    fig.colorbar(im, ax=ax, shrink=0.8, label="leading-EGS response")
    fig.tight_layout(); fig.savefig(FIG_DIR / "fig_egs3_a1_graded_rank.png", dpi=140); plt.close(fig)

    # A3 e-value calibration
    a3 = src["a3"]
    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    b = np.array(a3["beta_grid"]); r = np.array(a3["empirical_false_rate"])
    ax.plot(b, b, color=grey, ls="--", label="Markov bound  P(E≥1/β)≤β")
    ax.plot(b, r, marker="o", color=blue, label="empirical false-exceedance")
    ax.fill_between(b, r, b, where=(b >= r), color=green, alpha=0.15, label="conservative margin")
    ax.set_xlabel("β"); ax.set_ylabel("false-exceedance rate")
    ax.set_title(f"EGS3-A3: Π is a calibrated e-value\nnull mean E={a3['null_mean_evalue']:.3f}; bound holds")
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_egs3_a3_evalue_calibration.png", dpi=140); plt.close(fig)

    # NT2-A1 genuine Fisher floor
    af = src["a1_floor"]
    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    ax.plot(af["lmax"], af["fisher_floor"], marker="o", ms=3, color=blue, label="multi-ℓ Fisher–CR floor")
    ax.axhline(af["single_ell_l2_dispersion"], color=red, ls="--",
               label=f"single-ℓ √(2/5)={af['single_ell_l2_dispersion']:.3f}")
    ax.set_xlabel("ℓ_max in the estimator"); ax.set_ylabel("fractional floor σ(F)/F")
    ax.set_title("NT2-A1: genuine multi-multipole floor\nstrictly below the single-ℓ dispersion")
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_egs2_nt2a1_fisher_floor.png", dpi=140); plt.close(fig)

    # B1 floor profile vs k (+ r_ell inset)
    b1 = src["b1"]
    fig, ax = plt.subplots(figsize=(5.4, 4.0))
    ax.semilogx(b1["k_chi_star"], b1["floor"], marker="o", ms=3, color=blue)
    ax.axhline(b1["saturation_floor"], color=red, ls="--",
               label=f"super-horizon saturation √(2/5)={b1['saturation_floor']:.3f}")
    ax.set_xlabel("k·χ⋆ (shear mode scale)"); ax.set_ylabel("fractional floor σ(F)/F")
    ax.set_title("EGS3-B1: the floor is a k-PROFILE\nsaturates at 0.632; drops below only at finite k")
    ax.legend(fontsize=8)
    ins = ax.inset_axes([0.55, 0.48, 0.4, 0.4])
    ins.plot(b1["r_ell_l"], b1["r_ell"], marker=".", color=green)
    ins.set_title("r_ℓ decay (k=7e-5)", fontsize=7); ins.tick_params(labelsize=6)
    fig.tight_layout(); fig.savefig(FIG_DIR / "fig_egs3_b1_floor_profile.png", dpi=140); plt.close(fig)

    # B2 Volterra depth memory
    b2 = src["b2"]
    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    ax.plot(b2["z"], b2["shear_volterra"], color=blue, lw=2, label="shear σ(z)  (Volterra of Π)")
    ax.plot(b2["z"], b2["pi_of_z"], color=orange, lw=1.5, ls="-.", label="tilt stress Π(z)")
    ax2 = ax.twinx()
    ax2.plot(b2["z"], b2["memory_kernel"], color=grey, ls="--", label="memory kernel e^{-3∫H}")
    ax2.set_ylabel("kernel", color=grey)
    ax.set_xlabel("depth z"); ax.set_ylabel("σ(z), Π(z)")
    ax.set_title("EGS3-B2: depth gap is a Volterra memory of Π\nexponential kernel e^{-3∫H}")
    ax.legend(fontsize=7, loc="upper right"); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_egs3_b2_volterra.png", dpi=140); plt.close(fig)

    # B3 vorticity radial-blind vs transverse
    b3 = src["b3"]
    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    ax.hist(b3["radial_response"], bins=30, color=red, alpha=0.7, label="radial  n·Ω·n ≡ 0 (blind)")
    ax.hist(b3["transverse_response"], bins=30, color=green, alpha=0.5, label="transverse  n·Ω·m ≠ 0 (re-opens)")
    ax.axvline(0.0, color=grey, ls="--")
    ax.set_xlabel("vorticity channel response"); ax.set_ylabel("count")
    ax.set_title("EGS3-B3: vorticity re-opening\nradial blind; transverse channel breaks the no-go")
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_egs3_b3_vorticity.png", dpi=140); plt.close(fig)

    # NT2-B1 two-sided bracket
    nb = src["nt2b1"]
    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    # log-y: the MES upper bound is quadratic in a2 and would otherwise crush the
    # load-bearing lower bound (the strong new content) onto the axis.
    ax.fill_between(nb["a2"], nb["F_lo"], nb["F_hi"], color=blue, alpha=0.2, label="admissible F_shear band")
    ax.semilogy(nb["a2"], nb["F_lo"], color=green, lw=2, label="lower bound > 0 (excludes 0)")
    ax.semilogy(nb["a2"], nb["F_hi"], color=red, lw=2, label="upper bound (MES)")
    ax.set_xlabel("CMB quadrupole a₂"); ax.set_ylabel("F_shear (log)")
    ax.set_title("NT2-B1: two-sided shear/F bracket\nlower bound is strictly positive — zero is excluded")
    ax.legend(fontsize=8, loc="lower right"); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_egs2_nt2b1_bracket.png", dpi=140); plt.close(fig)

    # PSD-cone redesign schematic
    ps = src["psd"]
    fig, (axa, axb) = plt.subplots(1, 2, figsize=(7.2, 3.6))
    cols = [green if s in ps["reachable_sectors"] else red for s in ps["sectors"]]
    axa.bar(range(4), ps["spectrum"], color=cols)
    axa.set_xticks(range(4)); axa.set_xticklabels(ps["sectors"], rotation=20, fontsize=8)
    axa.set_ylabel("labelled eigenvalue (sector)")
    axa.set_title(f"M=diag(g)⪰0, rank {ps['reachable_rank']} reachable\n"
                  f"green=reachable, red=structural null")
    # cone-shell on the lambda_Sigma axis
    axb.axvspan(ps["shell_s_lo"], ps["shell_s_hi"], color=blue, alpha=0.18, label="cone-shell")
    axb.axvline(0.0, color=red, lw=2, label="FLRW vertex (excluded)")
    axb.axvline(ps["shell_lambda_sigma"], color=green, lw=2, label="observed λ_Σ")
    axb.axvline(ps["shell_s_lo"], color=grey, ls="--")
    axb.set_xlim(-2, ps["shell_s_hi"] * 1.1); axb.set_yticks([])
    axb.set_xlabel("shear eigenvalue λ_Σ")
    axb.set_title("convex cone-shell bracket\ns_lo>0 excludes the vertex")
    axb.legend(fontsize=7)
    fig.suptitle(f"EGS3 PSD-cone redesign: x_C=tr(C M) bit-identical = {ps['bit_identical']}", fontsize=9)
    fig.tight_layout(); fig.savefig(FIG_DIR / "fig_egs3_psd_cone.png", dpi=140); plt.close(fig)


_SPECS = [
    ("fig_egs3_a1_graded_rank", "EGS3-A1", "Graded comparator identifiability rank", "a1"),
    ("fig_egs3_a3_evalue_calibration", "EGS3-A3", "Pi e-value Markov calibration", "a3"),
    ("fig_egs2_nt2a1_fisher_floor", "NT2-A1", "Genuine multi-multipole Fisher-CR floor", "a1_floor"),
    ("fig_egs3_b1_floor_profile", "EGS3-B1", "Semi-native floor profile in the shear scale k", "b1"),
    ("fig_egs3_b2_volterra", "EGS3-B2", "Volterra depth-memory of the tilt stress", "b2"),
    ("fig_egs3_b3_vorticity", "EGS3-B3", "Vorticity re-opening: radial blind, transverse channel", "b3"),
    ("fig_egs2_nt2b1_bracket", "NT2-B1", "Two-sided shear/F bracket excluding zero", "nt2b1"),
    ("fig_egs3_psd_cone", "EGS3-PSD", "PSD-cone comparator redesign", "psd"),
]


def _sidecar_payloads(src: dict) -> dict[str, tuple[str, str]]:
    out = {}
    for stem, tid, title, key in _SPECS:
        source = src[key]
        out[stem] = (
            json.dumps(source, indent=2, sort_keys=True) + "\n",
            json.dumps(_manifest(stem, tid, title, source), indent=2, sort_keys=True) + "\n",
        )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    src = _sources()
    payloads = _sidecar_payloads(src)
    if args.check:
        stale = []
        for stem, (exp_src, exp_man) in payloads.items():
            for path, content in ((FIG_DIR / f"{stem}.source.json", exp_src),
                                  (FIG_DIR / f"{stem}.manifest.json", exp_man)):
                if (path.read_text(encoding="utf-8") if path.exists() else None) != content:
                    stale.append(path.relative_to(REPO_ROOT).as_posix())
        if stale:
            print("stale EGS2/EGS3 theorem figure sidecars:", *stale, sep="\n  - ")
            return 1
        print("EGS2/EGS3 theorem figure sidecars up to date")
        return 0
    _render(src)
    for stem, (exp_src, exp_man) in payloads.items():
        (FIG_DIR / f"{stem}.source.json").write_text(exp_src, encoding="utf-8")
        (FIG_DIR / f"{stem}.manifest.json").write_text(exp_man, encoding="utf-8")
        print(f"wrote figures/current/{stem}.png (+ source.json, manifest.json)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
