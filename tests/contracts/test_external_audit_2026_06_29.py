"""Contract: the 2026-06-29 external-audit revision holds.

Two permanent gates folded in from the external audit packs
(`htt_research_evaluation_review` MINOR, `pr08_reassessment_audit_pack` MAJOR):

  1. the research-content SURFACES (final report + results table + blocker
     dossier) are free of the forbidden over-promotions the audits flagged
     (`scripts/claim_lint_research_surfaces.py` -> 0 hits);
  2. the audit's independent re-checks still pass
     (`research_gates/external_audit_2026_06_29/reviewer_verification.py` -> 5/5),
     including the Omega_k genuine-zero-vs-degeneracy demonstration.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_research_surface_claim_lint_is_clean():
    lint = _load("claim_lint_research_surfaces", "scripts/claim_lint_research_surfaces.py")
    hits = lint.scan(REPO_ROOT)
    assert hits == [], hits


def test_reviewer_verification_all_checks_pass():
    rv = _load("reviewer_verification",
               "research_gates/external_audit_2026_06_29/reviewer_verification.py")
    assert rv.main() == 0
