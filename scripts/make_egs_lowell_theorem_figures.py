#!/usr/bin/env python3
"""REV-R104: figures for the new EGS-type low-ell diagnostic theorems.

Three analytic theorem figures (no observed data; synthetic illustration of the
Wolfram-verified identities in `docs/generated/egs_lowell_theorem_proofs.json`):

  NT-A1  F_shear linear in the CMB quadrupole D2 with the EGS limit F_shear->0.
  NT-A3  single-sky sampling dispersion sqrt(2/(2l+1)) of the standard F_shear
         estimator, l=2 -> 0.632 (one estimator; NOT a universal floor).
  NT-B3  depth gap G_F(z): flat at 1 for depth-steady shear; rising for a
         depth-evolving tilt.

All are diagnostic-only program-theorem figures: not HTT evidence, not a MIO
certificate, not native solver output, not geometry or family identification.
Each figure ships a source.json (plotted values) and a gated manifest; --check
compares those deterministic sidecars.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = REPO_ROOT / "figures" / "current"
PROOF_RECORD = REPO_ROOT / "docs/generated/egs_lowell_theorem_proofs.json"

KAPPA = 4.0 / 21.0  # ETM free-streaming ell=2 coefficient
X_MAX_S2A = 9.25e-6  # S2a algebraic ceiling (manuscript Table)


def _git_state() -> str:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip()
        dirty = subprocess.run(
            ["git", "status", "--short"], cwd=REPO_ROOT, text=True, capture_output=True
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return f"{commit}+dirty" if dirty else commit


def _config_hash(payload: dict) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _manifest(stem: str, theorem_id: str, title: str, source: dict) -> dict:
    worktree = _git_state()
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
        "statistics_definitions": {"program": "egs_lowell_theorem", "theorem_id": theorem_id},
        "generating_command": "python scripts/make_egs_lowell_theorem_figures.py",
        "config_hash": _config_hash(source),
        "input_hashes": [
            f"docs/generated/egs_lowell_theorem_proofs.json:sha256:"
            f"{hashlib.sha256(PROOF_RECORD.read_bytes()).hexdigest()}"
        ],
        "created_by": "scripts/make_egs_lowell_theorem_figures.py",
        "git_commit": worktree.split("+")[0],
        "git_commit_or_worktree_state": worktree,
        "code_version": worktree,
        "schema_version": "bass.egs_lowell_theorem_figure.v1",
        "caption_policy": [
            "must_state_diagnostic_only",
            "must_not_use_for_family_identification_or_family_selection",
            "must_state_no_native_low_ell_solver_output",
        ],
        "caveats": [
            "Analytic theorem illustration; synthetic, not observed data.",
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
            "symbolic_proof_present",
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
            "symbolic_proof_present",
            "manifest_metadata_present",
            "claim_firewall_caption_review",
        ],
        "title": title,
        "source": source,
    }


def _write_sidecars(stem: str, theorem_id: str, title: str, source: dict) -> None:
    manifest = _manifest(stem, theorem_id, title, source)
    (FIG_DIR / f"{stem}.source.json").write_text(
        json.dumps(source, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (FIG_DIR / f"{stem}.manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _sources() -> dict[str, dict]:
    # NT-A1: F_shear linear in D2 (normalised), slope = 1/(cD kappa^2 x_max).
    d2_ratio = np.linspace(0.0, 1.5, 31)
    fshear_ratio = d2_ratio  # F_shear/F_shear_ref == D2/D2_ref (linear, through 0)
    a1 = {
        "theorem_id": "NT-A1",
        "kappa": KAPPA,
        "x_max_s2a": X_MAX_S2A,
        "slope_per_unit_D2_over_cD": 1.0 / (KAPPA**2 * X_MAX_S2A),
        "D2_over_D2ref": d2_ratio.tolist(),
        "Fshear_over_Fshearref": fshear_ratio.tolist(),
        "egs_limit": "F_shear -> 0 as D2 -> 0",
    }
    # NT-A3: single-sky sampling dispersion sqrt(2/(2l+1)) of the standard estimator.
    ells = np.arange(2, 31)
    dispersion = np.sqrt(2.0 / (2.0 * ells + 1.0))
    a3 = {
        "theorem_id": "NT-A3",
        "ell": ells.tolist(),
        "fractional_sampling_dispersion": dispersion.tolist(),
        "dispersion_at_l2": float(np.sqrt(2.0 / 5.0)),
    }
    # NT-B3: G_F(z) steady-shear (flat 1) vs depth-growing tilt.
    z = np.linspace(0.0, 1.0, 41)
    fsh, c, q, zref = 1.0, 0.5, 1.0, 1.0
    gf_steady = np.ones_like(z)
    gf_tilt = (fsh + c * z**q) / (fsh + c * zref**q)
    b3 = {
        "theorem_id": "NT-B3",
        "z": z.tolist(),
        "G_F_steady_shear": gf_steady.tolist(),
        "G_F_depth_growing_tilt": gf_tilt.tolist(),
        "params": {"Fsh": fsh, "c": c, "q": q, "zref": zref},
    }
    return {"a1": a1, "a3": a3, "b3": b3}


def _render(sources: dict) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    a1 = sources["a1"]
    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    ax.plot(a1["D2_over_D2ref"], a1["Fshear_over_Fshearref"], color="#2563eb", lw=2)
    ax.scatter([0], [0], color="#dc2626", zorder=5)
    ax.annotate("EGS limit: D2->0 => F_shear->0", (0.02, 0.05), fontsize=8, color="#dc2626")
    ax.set_xlabel("D2 / D2_ref (CMB quadrupole power)")
    ax.set_ylabel("F_shear / F_shear_ref")
    ax.set_title("NT-A1: quadrupole-filling EGS identity\nF_shear = a2^2/(kappa^2 x_max) ∝ D2")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_theorem_nt_a1_quadrupole_filling.png", dpi=140)
    plt.close(fig)

    a3 = sources["a3"]
    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    ax.plot(a3["ell"], a3["fractional_sampling_dispersion"], marker="o", color="#16a34a")
    ax.axhline(a3["dispersion_at_l2"], color="#dc2626", ls="--", lw=1)
    ax.scatter([2], [a3["dispersion_at_l2"]], color="#dc2626", zorder=5)
    ax.annotate(f"l=2: sqrt(2/5)={a3['dispersion_at_l2']:.3f}", (3, a3["dispersion_at_l2"] + 0.01), fontsize=8)
    ax.set_xlabel("multipole l")
    ax.set_ylabel("single-sky sampling dispersion  sigma(F_shear)/F_shear")
    ax.set_title("NT-A3: single-sky sampling dispersion (one estimator)\nsqrt(2/(2l+1)); not a universal floor")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_theorem_nt_a3_cosmic_variance_floor.png", dpi=140)
    plt.close(fig)

    b3 = sources["b3"]
    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    ax.plot(b3["z"], b3["G_F_steady_shear"], color="#2563eb", lw=2, label="depth-steady shear (EGS limit)")
    ax.plot(b3["z"], b3["G_F_depth_growing_tilt"], color="#ea580c", lw=2, label="depth-growing tilt")
    ax.set_xlabel("depth z (arb.)")
    ax.set_ylabel("depth gap G_F(z)")
    ax.set_title("NT-B3: depth-transport EGS limit\nsteady shear => G_F=1; tilt imprints a gap")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_theorem_nt_b3_gf_transport.png", dpi=140)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    sources = _sources()
    specs = [
        ("fig_theorem_nt_a1_quadrupole_filling", "NT-A1", "Quadrupole-filling EGS identity", sources["a1"]),
        ("fig_theorem_nt_a3_cosmic_variance_floor", "NT-A3", "Single-sky sampling dispersion of the F_shear estimator", sources["a3"]),
        ("fig_theorem_nt_b3_gf_transport", "NT-B3", "Depth-transport EGS limit", sources["b3"]),
    ]
    if args.check:
        stale = []
        for stem, theorem_id, title, source in specs:
            expected_src = json.dumps(source, indent=2, sort_keys=True) + "\n"
            expected_man = json.dumps(_manifest(stem, theorem_id, title, source), indent=2, sort_keys=True) + "\n"
            for path, content in (
                (FIG_DIR / f"{stem}.source.json", expected_src),
                (FIG_DIR / f"{stem}.manifest.json", expected_man),
            ):
                if (path.read_text(encoding="utf-8") if path.exists() else None) != content:
                    stale.append(path.relative_to(REPO_ROOT).as_posix())
        if stale:
            print("stale EGS theorem figure sidecars:", *stale, sep="\n  - ")
            return 1
        print("EGS theorem figure sidecars up to date")
        return 0
    _render(sources)
    for stem, theorem_id, title, source in specs:
        _write_sidecars(stem, theorem_id, title, source)
        print(f"wrote figures/current/{stem}.png (+ source.json, manifest.json)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
