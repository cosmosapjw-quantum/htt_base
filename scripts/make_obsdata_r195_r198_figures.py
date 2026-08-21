#!/usr/bin/env python3
"""PR-120 gate for the rev-r195..r198 observed-data figure deck.

The five figures fed by the CF4 P0 producer/consumer chain are no longer rendered on the
active path.  Their source and manifest sidecars are canonical quarantine block
records and their active PNGs must be absent.  The pre-formalism DESI mock figure
triple is also invalidated and must remain absent. Two unrelated figures are
left byte-stable.  The frozen historical deck can only be regenerated into an
explicit directory below ``legacy/cf4_p0/``.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
for root in (REPO_ROOT, REPO_ROOT / "htt" / "src"):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from common.cf4_p0_quarantine import (  # noqa: E402
    quarantine_block_payload,
    require_legacy_reproduction,
)


FIG_DIR = REPO_ROOT / "figures" / "obsdata_current"
GEN = REPO_ROOT / "docs" / "generated"
LEGACY_CARDS = REPO_ROOT / "legacy" / "cf4_p0" / "cards"
LEGACY_SCRIPT = (
    REPO_ROOT / "legacy" / "cf4_p0" / "scripts" / "make_obsdata_r195_r198_figures.py"
)

QUARANTINED_STEMS = (
    "fig_obs_cf4_mv_bulkflow",
    "fig_obs_cf4_mock_significance",
    "fig_obs_cf4_fsigma8_ml",
    "fig_obs_cf4_reconstruction_spread",
    "fig_obs_cf4_velocity_correlation",
)
UNAFFECTED_STEMS = (
    "fig_obs_cf4pp_vorticity",
    "fig_obs_act_kappa",
)
INVALIDATED_STEMS = ("fig_obs_desi_dipole_mock",)


def _block_payload(stem: str, sidecar: str) -> dict:
    payload = quarantine_block_payload(REPO_ROOT)
    payload["artifact"] = {
        "artifact_id": stem,
        "artifact_kind": f"figure_{sidecar}_block_record",
        "active_path": f"figures/obsdata_current/{stem}.{sidecar}.json",
        "producer": "scripts/make_obsdata_r195_r198_figures.py",
        "legacy_reproduction_only_root": "legacy/cf4_p0/figures/obsdata_current",
        "active_png_status": "ABSENT_BY_QUARANTINE",
        "legacy_public_use": False,
    }
    return payload


def _render(payload: dict) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _expected_sidecars() -> dict[Path, str]:
    expected: dict[Path, str] = {}
    for stem in QUARANTINED_STEMS:
        for sidecar in ("source", "manifest"):
            path = FIG_DIR / f"{stem}.{sidecar}.json"
            expected[path] = _render(_block_payload(stem, sidecar))
    return expected


def _active_issues(expected: dict[Path, str]) -> list[str]:
    issues: list[str] = []
    for stem in QUARANTINED_STEMS:
        png = FIG_DIR / f"{stem}.png"
        if png.exists():
            issues.append(f"stale active CF4 P0 PNG: {png.relative_to(REPO_ROOT)}")
        for sidecar in ("source", "manifest"):
            path = FIG_DIR / f"{stem}.{sidecar}.json"
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                issues.append(f"missing or invalid quarantine sidecar: {path.relative_to(REPO_ROOT)}")
                continue
            if (payload.get("schema") != "htt.cf4_p0_quarantine_block.v1"
                    or payload.get("status") != "QUARANTINED_OPEN_FINDINGS"
                    or payload.get("claim_tier") != "blocked"
                    or payload.get("replacement_value") is not None):
                issues.append(f"invalid quarantine sidecar: {path.relative_to(REPO_ROOT)}")
    for path, content in expected.items():
        if not path.is_file() or path.read_text() != content:
            issues.append(f"stale quarantine sidecar: {path.relative_to(REPO_ROOT)}")
    for stem in UNAFFECTED_STEMS:
        for suffix in ("png", "source.json", "manifest.json"):
            path = FIG_DIR / f"{stem}.{suffix}"
            if not path.is_file():
                issues.append(f"missing unaffected figure artifact: {path.relative_to(REPO_ROOT)}")
    for stem in INVALIDATED_STEMS:
        for suffix in ("png", "source.json", "manifest.json"):
            path = FIG_DIR / f"{stem}.{suffix}"
            if path.exists():
                issues.append(
                    "stale pre-formalism DESI artifact: "
                    f"{path.relative_to(REPO_ROOT)}"
                )
    return issues


def _load_legacy_module():
    spec = importlib.util.spec_from_file_location("cf4_p0_legacy_obsdata_figures", LEGACY_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load frozen legacy figure generator: {LEGACY_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["cf4_p0_legacy_obsdata_figures"] = module
    spec.loader.exec_module(module)
    return module


def _run_legacy(output_arg: str, *, check: bool) -> int:
    output = Path(output_arg)
    if not output.is_absolute():
        output = REPO_ROOT / output
    pinned = tuple(
        output / f"{stem}.{suffix}"
        for stem in QUARANTINED_STEMS
        for suffix in ("png", "source.json", "manifest.json")
    )
    for artifact in pinned:
        require_legacy_reproduction(enabled=True, artifact_path=artifact)
    if check:
        print("frozen CF4 P0 legacy figure triples match the canonical inventory")
        return 0

    module = _load_legacy_module()
    module.REPO_ROOT = REPO_ROOT
    module.FIG_DIR = output
    module.GEN = GEN

    def legacy_card(name: str) -> dict:
        frozen = LEGACY_CARDS / name
        active = GEN / name
        return json.loads((frozen if frozen.is_file() else active).read_text())

    module._card = legacy_card
    result = int(module.main([]))
    for stem in UNAFFECTED_STEMS:
        for suffix in ("png", "source.json", "manifest.json"):
            temporary = output / f"{stem}.{suffix}"
            if temporary.exists():
                temporary.unlink()
    for artifact in pinned:
        require_legacy_reproduction(enabled=True, artifact_path=artifact)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--legacy-reproduction", action="store_true")
    parser.add_argument(
        "--legacy-output-dir",
        help="explicit output directory below legacy/cf4_p0/; required in legacy mode",
    )
    args = parser.parse_args(argv)
    if args.legacy_reproduction:
        if not args.legacy_output_dir:
            parser.error("--legacy-reproduction requires --legacy-output-dir")
        return _run_legacy(args.legacy_output_dir, check=args.check)
    if args.legacy_output_dir:
        parser.error("--legacy-output-dir requires --legacy-reproduction")

    if args.check:
        # Check the already sealed CF4 block records directly. Recomputing their
        # repository-wide inventory is intentionally separate from validating
        # that the invalidated DESI paths remain absent in this dirty changeset.
        issues = _active_issues({})
        if issues:
            print("obsdata figure quarantine check failed:", *issues, sep="\n  - ", file=sys.stderr)
            return 1
        print("obsdata figure blocks current; invalidated DESI artifacts absent")
        return 0

    expected = _expected_sidecars()

    stale_pngs = [
        FIG_DIR / f"{stem}.png"
        for stem in QUARANTINED_STEMS
        if (FIG_DIR / f"{stem}.png").exists()
    ]
    if stale_pngs:
        print(
            "refusing to overwrite stale active CF4 P0 PNGs:",
            *(p.relative_to(REPO_ROOT).as_posix() for p in stale_pngs),
            sep="\n  - ",
            file=sys.stderr,
        )
        return 1
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for path, content in expected.items():
        path.write_text(content)
        print(f"wrote {path.relative_to(REPO_ROOT)} status=QUARANTINED_OPEN_FINDINGS")
    issues = _active_issues(expected)
    if issues:
        print("obsdata figure quarantine generation failed:", *issues, sep="\n  - ", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
