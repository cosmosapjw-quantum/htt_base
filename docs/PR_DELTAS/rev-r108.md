# REV-R108 - LR-06A: PREP-06 canonical integration + baseline freeze (PR04 multicomponent)

owner: COMMON
implementation_scope: common + bass_py
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_applicable_method_integration
null_mock_status: not_applicable_method_integration
generating_command: `PREP-06 handoff: install_handoff.py --apply-overlay --install-scaffold + verify_local_integration.py`
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Execute the PREP-06 local-repository handoff (external research-audit terminal
artifact built on the REV-R106 code-capability disclosure). LR-06A is the only
entry gate: freeze the baseline, merge the PR04 multicomponent/congruence/
Bianchi-I/pushforward bridge, install the research scaffold, and pass the
external theorem gates plus the canonical regression.

## Baseline freeze

- Branch `research/pr04-multicomponent` off `main` `348e8ac` (branch used per the
  PREP-06 runbook; deliberate, scoped deviation from the usual additive-on-`main`
  rule).
- Python 3.12.3, NumPy 2.4.2. `Cargo.lock` sha `f1023b1b…`, `htt/pyproject.toml`
  sha `f5b11526…`.
- Baseline `python -m compileall -q htt`: PASS. Baseline collection:
  `7654/7713 tests collected` (59 deselected), clean.
- Recorded dirty-state waiver: pre-existing `.claude/settings.json`,
  `.codex/rules/default.rules` (unrelated session state; never touched).

## Integration (overlay + scaffold, 0 conflicts)

Preflight `overlay_conflicts: []`, `overlay_missing_payloads: []` (status FAIL is
only the dirty-tree advisory, covered by the waiver). Installed via
`install_handoff.py`; merged one PR at a time in the required dependency order
(representation/conventions -> GR first jet -> statistics -> Bianchi-I -> theorem
tests -> legacy pushforward), one commit each:

| PR | Files | Review focus |
| --- | --- | --- |
| PR04-002 | `htt/htt/htt/common/{stf_canonical,multicomponent_blocks}.py` | canonical STF + multicomponent block schema |
| PR04-003 | `htt/bass/observer/congruence_ssot.py` | covariant congruence first jet + exact rapidity composition |
| PR04-004 | `htt/htt/htt/departure/multicomponent_response.py` | response rank / no-go / sufficiency audit |
| PR04-005 | `htt/bass/background/bi_continuation/{__init__,moments,dynamics}.py` | restricted Bianchi-I multifluid moments + dynamics + shear memory |
| PR04-006 | `research_gates/pr04/tests/*` + `tools/verify_forbidden_dependencies.py` | 23 external theorem/property gates |
| PR04-007 | `htt/mio/formalism/physical_pushforward.py`, `htt/htt/htt/integration/pr04_canonical_bridge.py` | fail-closed pushforward + Bianchi-I canonical bridge |

Scaffold: `docs/research_program/pr04/*` (9 docs), `.github/` (CI gate workflow,
issue form, PR template), `research_gates/pr04/local_tickets.json`.

## LR-06A PASS gate (all green)

| Check | Result |
| --- | --- |
| preflight overlay conflicts | 0 (dirty-tree waiver recorded) |
| 23 external PR04 theorem/property gates | 23/23 PASS |
| `compileall -q htt` (full tree) | PASS |
| import smoke (htt, bass, mio, congruence, response, pushforward) | IMPORT_OK |
| forbidden old-Rust dependency scan | PASS (no findings) |
| canonical collect (post-overlay) | 7654/7713, unchanged from baseline |
| `run_subset.py fast` | 6 passed |
| `run_subset.py smoke` | 6 passed |
| `pytest -m "ci and not slow"` | 11 passed |

The overlay is purely additive (9 new modules, 0 edits to existing files);
post-overlay collection is identical to baseline, so no existing test regressed.

## Claim boundary

Method/theorem integration only. No raw-data analysis, no observational estimate,
no old-Rust science output, no native-transfer validation, no family
identification. `physical_pushforward.py` is fail-closed
(`BLOCKED_UNIDENTIFIED_COMPONENTS`, `BLOCKED_ZERO_DENOMINATOR_BRANCH`); the
Bianchi-I bridge is tagged `restricted_bianchi_i_multifluid`. The standing stop
gates in `docs/research_program/pr04/CLAIM_AND_STOP_GATES.md` remain in force.

## Next

LR-06B (PAPER-A theorems) and LR-06C (PAPER-B Bianchi-I dynamics) unblock and run
in parallel (no raw data). Raw-data acquisition track (CF4 / Planck PR4-NPIPE /
velocity fields) starts in parallel to unblock LR-06D-G. Blocker codes apply
where an input cannot be satisfied.
