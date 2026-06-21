# REV-R104 - EGS-Type Low-ell Diagnostic Theorems (NT-A1, NT-A3, NT-B3)

owner: BASS
implementation_scope: bass_py
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: synthetic_only
generating_command: `Codex REV-R104 prove EGS-type low-ell theorems and update the report`
git_commit_or_worktree_state: pending_rev_r104_commit

## Evidence Read

- `egs_theorem_program.zip` (`04_THEOREM_CANDIDATES.md`, `05_AXIS_A`, `06_AXIS_B`,
  `code/egs_boltzmann_core.py`, `nt1/nt3/nt4`) and
  `htt_beyond_mes_egs_theorem_program_2026-06-19.zip`.
- `docs/generated/theorem_extension_registry.json` (existing B4/G2/G5/S1/S3/S4/S5;
  no NT-* present), `docs/manuscript/ch01`/`ch02` (EGS sections),
  `docs/manuscript/appendices.tex`.
- `htt/obsstat/scalar_lowell.py`, `morphology.py` definitions; ETM coefficient
  4/21 and MES constants from the zip's Boltzmann core.

## New-Result Rationale

The zip proposes EGS-type theorem candidates (NT-A1..A3, NT-B1..B4) carrying the
EGS chain onto the report's diagnostic variables; none are in the research
report. Three are rigorously provable as conditional analytic theorems and are
proven here with the Wolfram Engine (via `wolframclient`), with new figures and
a manuscript appendix subsection. NT-B1/B2 (near-trivial algebra) and
NT-A2/NT-B4 (methodology/loophole, not clean theorems) are not promoted.

## Theorems Proven (symbolically, Wolfram-verified, QED x3)

- NT-A1 quadrupole-filling EGS identity: `F_shear = a2^2/(kappa^2 x_max)` ∝ `D2`,
  EGS limit `F_shear -> 0` as `D2 -> 0`, tilt-independence; sphere average
  `<n_a n_b> = (1/3) delta_ab` verified.
- NT-A3 cosmic-variance Cramer-Rao floor: `sigma(F_shear)/F_shear >=
  sqrt(2/(2l+1))`, `= sqrt(2/5) ~ 0.632` at l=2 (branch-free squared identity).
- NT-B3 depth-transport EGS limit: depth-steady shear -> `G_F(z) ≡ 1`; a
  depth-evolving tilt imprints `dG_F/dz != 0`.

All conditional on explicit hypotheses (free-streaming linear ell=2 closure;
single-sky chi-square quadrupole variance; additive shear+tilt filling). Not
detections; no native solver output, HTT/MIO evidence, or family-ID.

## Role Split

- Physics/statistics auditor steelman: state every hypothesis; the floor must
  use the chi-square single-sky variance and the squared identity (no sqrt
  branch ambiguity); the closure coefficient kappa is the ETM input, theorems
  hold for any kappa>0.
- Code cartographer steelman: reuse the report's diagnostic-variable definitions;
  put the proofs in a Wolfram-driven script + a deterministic figure script.
- Claim-gate reviewer steelman: keep figures/manifests diagnostic-only with
  family-ID and native-solver use blocked; manuscript prose must avoid bare
  "family identification" (uses family-ID) and any detection language.

## Changes

- `scripts/prove_egs_lowell_theorems.py`: Wolfram symbolic proofs ->
  `docs/generated/egs_lowell_theorem_proofs.{json,md}` (QED per theorem).
- `scripts/make_egs_lowell_theorem_figures.py`: 3 analytic figures +
  `source.json` + gated manifests in `figures/current/`.
- `docs/manuscript/appendices.tex`: new subsection
  (Sec.~\ref{sec:egs-lowell-theorems}) with the three theorem environments,
  proofs, and figures; PDF rebuilt.
- Regenerated `docs/generated/manuscript_figure_inventory.md`,
  `missing_figure_references.md`, `pdf_claim_lint_report.md`,
  `manuscript_pdf/htt_base_research_report.{pdf,manifest.json}`, and the
  research-only audit package (now bundling the three theorem figures).
- Test: `tests/bass/test_egs_lowell_theorems.py` (pure-python re-derivation +
  proof-record contract + Wolfram re-proof).

## Artifact Metadata

- owner: BASS
- implementation_scope: bass_py
- claim_tier: diagnostic_only
- config_hash:
  - `scripts/prove_egs_lowell_theorems.py:sha256:b1ef7e9d822924579b429c57fc7e61178577d218536b6b718a23031cf781ef4d`
  - `scripts/make_egs_lowell_theorem_figures.py:sha256:7c7aeef3859453e494525f22bdc0bb89bddbb2bdbaef351ebb26175d1e79f5b4`
- input_hashes:
  - `docs/generated/egs_lowell_theorem_proofs.json:sha256:95df9dbb7587446200a7141f021e39405c525bb47051b3fed4fe58844a8da169`
  - `tests/bass/test_egs_lowell_theorems.py:sha256:f633df490797ca126f7c10e9487ba62dbdec518d62a749534a46d5781dc134f4`
  - `docs/manuscript/appendices.tex:sha256:b646a97ed3a502a9b65f4908851d4b899c44c16b943a7f973d241ab87a86e12f`
  - `docs/generated/manuscript_pdf/htt_base_research_report.pdf:sha256:88e52ac4a13464e027555069d5bec9fde30422bd4dedb1ff19ee9b812a516b15`
  - `figures/current/fig_theorem_nt_a1_quadrupole_filling.png:sha256:bb22a004554888fc154a9526bc6dea5d12a691238da0959fd92c10ba88e5ec50`
- caveats:
  - conditional theorems; structural/limit statements, not detections;
  - kappa = 4/21 is the ETM closure value (cited); theorems hold for any kappa>0;
  - no native low-ell solver output, HTT/MIO evidence, or Bianchi family-ID.

## TDD Red

- `venv/bin/python -B scripts/prove_egs_lowell_theorems.py` initially reported
  `NT-A3 QED=False` until the floor identity was checked branch-free (squared
  form) rather than via the symbolic sqrt equality.

## Validation

| Command | Status | Notes |
| --- | --- | --- |
| `venv/bin/python -B scripts/prove_egs_lowell_theorems.py` | PASS | NT-A1/A3/B3 QED=True (Wolfram $Version recorded). |
| `venv/bin/python -B scripts/make_egs_lowell_theorem_figures.py --check` | PASS | Sidecars up to date. |
| `latexmk ... main.tex` (from docs/manuscript) | PASS | PDF rebuilt; no undefined references. |
| `venv/bin/python -B scripts/pdf_claim_lint.py --check` | PASS | `Failed findings: 0`. |
| `venv/bin/python -B scripts/audit_manuscript_figures.py --dry-run` | PASS | resolved=126, quarantined=0, manual findings 0. |
| `venv/bin/python -B scripts/build_research_only_audit_package.py --check` | PASS | Package bundles the three theorem figures; no PDFs. |
| `pytest -q tests/bass/test_egs_lowell_theorems.py tests/contracts/test_current_manuscript_figures.py tests/contracts/test_research_only_audit_package.py tests/contracts/test_audit_ver2_claim_firewall.py` | PASS | `24 passed`. |
