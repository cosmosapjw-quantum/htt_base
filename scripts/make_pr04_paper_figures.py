#!/usr/bin/env python3
"""LR-06B/LR-06C synthetic figure suite for PAPER-A / PAPER-B.

Figures are generated from the actual PR04 overlay modules (no mocks):
  A1  response rank-gain ladder (identifiability).
  A2  non-collinear boost: composed speed vs Euclidean rapidity sum (Wigner).
  B1  scalar non-sufficiency: equal Omega_tilt, different ||Pi||.
  B2  dust-FLRW integrator error + shear memory (sigma with/without Pi).

All four are diagnostic-only program-theorem figures: not observed data, not a
native solver result, not a family-identification claim. Each ships a
source.json and a gated manifest; --check compares the deterministic sidecars.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
for p in (REPO_ROOT / "htt", REPO_ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
FIG_DIR = REPO_ROOT / "figures" / "current"

from bass.background.bi_continuation import (  # noqa: E402
    SpeciesPrimitive, tilt_moments, BIState, integrate, dust_flrw_exact,
)
from bass.observer.congruence_ssot import compose_rapidity_vectors  # noqa: E402
from htt.departure.multicomponent_response import rank_gain_ladder  # noqa: E402


def _git_state() -> str:
    try:
        c = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, text=True).strip()
        d = subprocess.run(["git", "status", "--short"], cwd=REPO_ROOT, text=True, capture_output=True).stdout.strip()
        return f"{c}+dirty" if d else c
    except Exception:
        return "unknown"


def _config_hash(payload: dict) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _manifest(stem: str, fig_id: str, title: str, source: dict) -> dict:
    w = _git_state()
    return {
        "artifact_id": f"bass.pr04_paper_figure.{stem}",
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
        "figure_id": fig_id,
        "title": title,
        "source_json_path": f"figures/current/{stem}.source.json",
        "generating_command": "python scripts/make_pr04_paper_figures.py",
        "config_hash": _config_hash(source),
        "created_by": "scripts/make_pr04_paper_figures.py",
        "git_commit": w.split("+")[0],
        "git_commit_or_worktree_state": w,
        "code_version": w,
        "schema_version": "bass.pr04_paper_figure.v1",
        "caption_policy": [
            "must_state_diagnostic_only",
            "must_not_use_for_family_identification_or_family_selection",
            "must_state_no_native_solver_output",
        ],
        "caveats": [
            "Synthetic figure from the PR04 overlay modules; not observed data.",
            "Program-theorem illustration; not a detection.",
            "No native solver output or Bianchi family-ID is claimed.",
        ],
        "promotion_blockers": [
            "native_solver_validation_absent",
            "native_morphology_atlas_absent",
            "family_identification_blocked_pre_native_atlas",
        ],
        "title_full": title,
        "source": source,
    }


def _write_sidecars(stem, fig_id, title, source) -> None:
    (FIG_DIR / f"{stem}.source.json").write_text(json.dumps(source, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (FIG_DIR / f"{stem}.manifest.json").write_text(json.dumps(_manifest(stem, fig_id, title, source), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sources() -> dict:
    rng = np.random.default_rng(11)
    # A1 rank-gain ladder.
    blocks = {"bulk": rng.normal(size=(80, 3)), "shear": rng.normal(size=(80, 5)),
              "curl": rng.normal(size=(80, 3)), "dup": None}
    blocks["dup"] = blocks["bulk"]
    ladder = rank_gain_ladder({k: v for k, v in blocks.items()}, np.eye(80))
    a1 = {"figure_id": "A1", "added": [x["added"] for x in ladder],
          "rank": [x["rank"] for x in ladder], "dimension": [x["dimension"] for x in ladder]}
    # A2 Wigner non-additivity: fix b1 along x, sweep b2 along y.
    b1 = 0.4
    b2s = np.linspace(0.0, 0.8, 33)
    composed, euclid = [], []
    for b2 in b2s:
        out = compose_rapidity_vectors(np.array([b1, 0, 0]), np.array([0, b2, 0]))
        composed.append(float(np.linalg.norm(out["rapidity_vector"])))
        euclid.append(float(np.hypot(b1, b2)))
    a2 = {"figure_id": "A2", "b1": b1, "b2": b2s.tolist(),
          "composed_speed": composed, "euclidean_sum": euclid}
    # B1 scalar non-sufficiency.
    v = np.sqrt(0.04)
    pair = (SpeciesPrimitive(0.3, 0, np.array([v, 0, 0])), SpeciesPrimitive(0.3, 0, np.array([-v, 0, 0])))
    six = []
    for e in np.eye(3):
        six += [SpeciesPrimitive(0.1, 0, v * e), SpeciesPrimitive(0.1, 0, -v * e)]
    m1, m2 = tilt_moments(pair, 1.0), tilt_moments(tuple(six), 1.0)
    b1f = {"figure_id": "B1", "labels": ["colinear pair", "isotropic six-stream"],
           "Omega_tilt": [float(m1.Omega_tilt), float(m2.Omega_tilt)],
           "Pi_norm": [float(np.linalg.norm(m1.Pi)), float(np.linalg.norm(m2.Pi))]}
    # B2 dust-FLRW error + shear memory.
    H0 = 0.8
    state = BIState(1.0, H0, np.zeros((3, 3)), (SpeciesPrimitive(3 * H0 * H0, 0.0, np.zeros(3)),))
    t = np.linspace(0, 0.4, 201)
    hist = integrate(state, t)
    a_ex, _ = dust_flrw_exact(t, H0)
    a_err = [abs(s.a - ae) for s, ae in zip(hist, a_ex)]
    pair2 = (SpeciesPrimitive(0.6, 0, np.array([0.18, 0, 0])), SpeciesPrimitive(0.6, 0, np.array([-0.18, 0, 0])))
    p = tilt_moments(pair2, 1.0).total_projection
    Hs = float(np.sqrt(p.mu / 3.0))
    ts = np.linspace(0, 0.08, 81)
    st2 = BIState(1.0, Hs, np.zeros((3, 3)), pair2)
    full = integrate(st2, ts, include_anisotropic_stress=True)
    abl = integrate(st2, ts, include_anisotropic_stress=False)
    sig_full = [float(np.linalg.norm(s.sigma)) for s in full]
    sig_abl = [float(np.linalg.norm(s.sigma)) for s in abl]
    b2f = {"figure_id": "B2", "t_dust": t.tolist(), "a_error": a_err,
           "t_shear": ts.tolist(), "sigma_with_Pi": sig_full, "sigma_no_Pi": sig_abl}
    return {"a1": a1, "a2": a2, "b1": b1f, "b2": b2f}


def _render(s: dict) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    a1 = s["a1"]
    fig, ax = plt.subplots(figsize=(5.4, 4.0))
    ax.step(range(len(a1["added"])), a1["rank"], where="mid", color="#2563eb", lw=2)
    ax.scatter(range(len(a1["added"])), a1["rank"], color="#2563eb")
    ax.axhline(a1["dimension"][-1], ls="--", color="#888", lw=1)
    ax.set_xticks(range(len(a1["added"]))); ax.set_xticklabels(a1["added"])
    ax.annotate("duplicate block adds 0 rank", (len(a1["added"]) - 1, a1["rank"][-1]),
                textcoords="offset points", xytext=(-10, 8), fontsize=8, ha="right", color="#dc2626")
    ax.set_ylabel("identifiable rank"); ax.set_xlabel("response block added")
    ax.set_title("A1: response rank-gain ladder (identifiability)")
    fig.tight_layout(); fig.savefig(FIG_DIR / "fig_pr04_a1_rank_ladder.png", dpi=140); plt.close(fig)

    a2 = s["a2"]
    fig, ax = plt.subplots(figsize=(5.4, 4.0))
    ax.plot(a2["b2"], a2["euclidean_sum"], "--", color="#888", label="Euclidean sum |(b1,b2)|")
    ax.plot(a2["b2"], a2["composed_speed"], color="#2563eb", lw=2, label="relativistic composed speed")
    ax.set_xlabel("transverse boost b2 (b1=0.4)"); ax.set_ylabel("speed")
    ax.set_title("A2: non-collinear boost composition (Wigner)"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG_DIR / "fig_pr04_a2_wigner.png", dpi=140); plt.close(fig)

    b1 = s["b1"]
    fig, axs = plt.subplots(1, 2, figsize=(6.0, 3.6))
    axs[0].bar(b1["labels"], b1["Omega_tilt"], color="#16a34a"); axs[0].set_title("Omega_tilt (scalar)")
    axs[0].tick_params(axis="x", labelrotation=12)
    axs[1].bar(b1["labels"], b1["Pi_norm"], color="#ea580c"); axs[1].set_title("||Pi|| (STF moment)")
    axs[1].tick_params(axis="x", labelrotation=12)
    fig.suptitle("B1: scalar non-sufficiency (equal Omega_tilt, different Pi)")
    fig.tight_layout(); fig.savefig(FIG_DIR / "fig_pr04_b1_nonsufficiency.png", dpi=140); plt.close(fig)

    b2 = s["b2"]
    fig, axs = plt.subplots(1, 2, figsize=(6.4, 3.6))
    axs[0].semilogy(b2["t_dust"], np.maximum(b2["a_error"], 1e-16), color="#2563eb")
    axs[0].set_title("B2a: dust-FLRW |a_int - a_exact|"); axs[0].set_xlabel("t"); axs[0].set_ylabel("abs error")
    axs[1].plot(b2["t_shear"], b2["sigma_with_Pi"], color="#ea580c", lw=2, label="with Pi")
    axs[1].plot(b2["t_shear"], b2["sigma_no_Pi"], "--", color="#2563eb", lw=2, label="Pi ablated")
    axs[1].set_title("B2b: shear memory ||sigma||"); axs[1].set_xlabel("t"); axs[1].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG_DIR / "fig_pr04_b2_dust_shear.png", dpi=140); plt.close(fig)


SPECS = [
    ("fig_pr04_a1_rank_ladder", "A1", "Response rank-gain ladder", "a1"),
    ("fig_pr04_a2_wigner", "A2", "Non-collinear boost composition", "a2"),
    ("fig_pr04_b1_nonsufficiency", "B1", "Scalar non-sufficiency of Omega_tilt", "b1"),
    ("fig_pr04_b2_dust_shear", "B2", "Dust-FLRW oracle error and shear memory", "b2"),
]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    sources = _sources()
    if args.check:
        stale = []
        for stem, fig_id, title, key in SPECS:
            exp_src = json.dumps(sources[key], indent=2, sort_keys=True) + "\n"
            exp_man = json.dumps(_manifest(stem, fig_id, title, sources[key]), indent=2, sort_keys=True) + "\n"
            for path, content in ((FIG_DIR / f"{stem}.source.json", exp_src), (FIG_DIR / f"{stem}.manifest.json", exp_man)):
                if (path.read_text(encoding="utf-8") if path.exists() else None) != content:
                    stale.append(path.relative_to(REPO_ROOT).as_posix())
        if stale:
            print("stale PR04 figure sidecars:", *stale, sep="\n  - ")
            return 1
        print("PR04 paper figure sidecars up to date")
        return 0
    _render(sources)
    for stem, fig_id, title, key in SPECS:
        _write_sidecars(stem, fig_id, title, sources[key])
        print(f"wrote figures/current/{stem}.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
