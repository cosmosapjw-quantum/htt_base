# Phase-boundary audit — Independent Tracks Week 17

**Phase tag**: `IND_TRACKS_W17`
**Date**: 2026-04-19
**Plan**: INDEPENDENT_TRACKS_PLAN.md v1.3 §21 (Week 12+ continuation
routine); day-by-day guidance from
`docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` §2 Week 17 (W16 F2 A44.3
runtime-gate microtest + W16 F3 A36a YAML range-reduction hedge +
one A4x dossier).
Execution: W17D1 `MioCertificate.git_commit` at-instantiation
microtest (D1), W17D3 `sigma_lit_range_deg` bracketing sibling
test (D3), W17D5 DOS-A45 MIO cache-replay drift protocol (D5),
this audit + NEXT_SESSION rotation (D7).
**Pre-commit audit** per memory rule `feedback_phase_boundary_audit.md`.
**Parent-plan references**:
v3 §4.5.4 (G19 hard separation — A45 is content-hash companion to
A44's execution-order companion to A34);
v3 §10.2 (HTT ↔ MIO contract table — A45.2 specifies the replay-
path hash chain the table's provenance columns presuppose);
v3 §11.14.6 (dossier convention — A45 added under the A4x family;
first A4x added since A44 in W16);
v3 §16.2 FM2 (σ_cone placeholders — W17D3's range-bracketing hedge
extends the W16D3 YAML sidecar gate to the optional range field);
[W6 FM6](AUDIT_PHASE_IND_TRACKS_W6_2026-04-19.md) +
[W11 F5](AUDIT_PHASE_IND_TRACKS_W11_2026-04-19.md) +
[A44.3](../dossier/A44_mio_htt_handshake_sequence.md) (git_commit
at-instantiation invariant — W17D1 is the runtime gate);
[W7 FM3](AUDIT_PHASE_IND_TRACKS_W7_2026-04-19.md) +
[A43](../dossier/A43_schema_hash_digest.md) (schema-hash digest —
A45.5 escape-hatch upgrades cleanly on A43 landing);
[W12 F1](AUDIT_PHASE_IND_TRACKS_W12_2026-04-19.md) +
[W14 F1](AUDIT_PHASE_IND_TRACKS_W14_2026-04-19.md) (cross-lane
contamination mitigations — W13D1 status-gate + W15D1 scoped-
pathspec rule; §6 below records the W17 recurrence check);
[W16 F1](AUDIT_PHASE_IND_TRACKS_W16_2026-04-19.md#post-write-addendum-2026-04-19-15-min-after-w16d7-audit-landed)
(first adversarial stress-test of the scoped-pathspec rule — W17D3
is the second).

**Baseline head**: `e9afa8e` (`AUDIT(W16 §6): W15D1 scoped-pathspec
passes first adversarial test`). **Zero intervening cross-lane
commits on `main` this phase** — the three W17 landings
(`151fbc4`, `3137cc0`, `a4dc670`) sit consecutively atop `e9afa8e`
with no other-lane commit between them. The bass lane was quiet
on `main` during the W17 window; however the bass lane staged
working-tree modifications to `bass_py/bass/hierarchy/*.py`
between W17D1 and W17D3 — the W17D3 `git status --short` observed
four bass-lane files in the unstaged index, and the W15D1 scoped-
`git commit -- <paths>` rule excluded them by construction
(§6 W17 check #1 below). Pre-commit `git status --short` gate
applied before each W17 commit per W13D1; scoped `git commit
-- <paths>` pathspec applied per W15D1.

**Commits this phase**:

- `W17D1` — `151fbc4` `W17D1: MIO git_commit capture-time runtime
  gate (W16 F2)`. One-file commit (+37 L) appending
  `test_git_commit_is_capture_time_not_lazy` to
  `bass_py/workspace/contracts/tests/test_mio_certificate.py`. The
  microtest constructs a `MioCertificate` with a concrete
  `git_commit`, monkeypatches `subprocess.run` to raise if called
  and (defensively) `_resolve_git_commit` on the MIO interface
  module to return a sentinel, reads `cert.git_commit` via both
  attribute access and `dataclasses.asdict`, asserts equality with
  the originally-passed value, and asserts no class-level
  descriptor / property sits on `git_commit` (a lazy re-resolver
  would fail that check). Closes W16 F2 — A44.3's at-instantiation
  invariant is now runtime-enforced at the workspace-layer. Touched
  surface 1077 → 1078.
- `W17D3` — `3137cc0` `W17D3: DOS-A36a YAML range-bracketing hedge
  (W16 F3)`. One-file commit (+47 L) appending
  `test_a36a_yaml_range_brackets_midpoint` as a sibling test to
  `bass_py/mio/tests/test_sigma_cone_provenance.py`. Iterates every
  YAML row carrying the optional `sigma_lit_range_deg: [min, max]`
  field and asserts `range[0] <= sigma_lit_deg <= range[1]`. All
  three current range-carrying rows satisfy this by construction
  (Radio 10-14 midpoint 12; CF4pp 10-12 midpoint 11; BiPoSH 15-25
  midpoint 20); the hedge is future-edit insurance against a
  ranged-σ addition to a currently-scalar probe or a range/midpoint
  typo that drifts `sigma_lit_deg` outside its declared range.
  Closes W16 F3. Touched surface 1078 → 1079; MIO contribution
  107 → 108 (`test_sigma_cone_provenance.py` 11 → 12 tests).
- `W17D5` — `a4dc670` `W17D5: DOS-A45 MIO cache-replay drift
  protocol`. One-file commit (+269 L) creating
  `docs/dossier/A45_mio_cache_replay_drift.md`. Content-hash
  companion to A44's execution-order companion to A34. §A45.2
  specifies the `verify_cache_replay(mio_cert, htt_input_bundle,
  allow_unsigned_config=False)` pseudocode — recompute
  `config_hash` from the re-parsed payload tuple, set-equality-
  check `input_data_hashes` against the live HTT input bundle,
  raise `CacheReplayDriftError` on either drift. §A45.3 declares
  landing deferred to the first harness that crosses a persistence
  boundary (HJ-03 per A42.5 + A44.7). §A45.5 specifies the
  `allow_unsigned_config=True` escape-hatch semantics and its
  clean upgrade path once A43's schema-hash digest lands (W15 F3
  / A43.3 trigger). §A45.6 ships a paste-ready five-test
  acceptance block for the HJ-03 PR; test (5) mirrors W17D1 at
  the MIO harness surface. §A45.7 resolves cross-refs into A32 /
  A34 / A41 / A42 / A43 / A44. No code change.
- `W17D7` (= this audit) — pending commit: this log + NEXT_SESSION
  rotation.

**Touched-surface test count**: `bass_py/htt/tests/ bass_py/src/
bass_py/tsc/admissibility/ bass_py/tsc/diagnostics/
bass_py/tsc/charts/ bass_py/tsc/integration/ bass_py/workspace/
bass_py/mio/` → **1079 passed, 0 failed, 4 skipped**. Week 17
delta vs Week 16 (1077 / 0 / 4): **+2 tests (W17D1 +1, W17D3 +1),
0 skip change, 0 regressions**.

**TSC-standalone test count**: `bass_py/tsc/` → 602 passed
(unchanged from W13–W16 — no TSC code change this week).

**MIO contribution**: 108 tests (+1 vs W16's 107; gate ≥ 47 met
with 61 to spare). Composition: `test_sigma_cone_provenance.py`
11 → 12 tests (W17D3 adds the range-bracketing sibling); W17D1
lives at the workspace-contract surface, so MIO count excludes
it. Cross-check: `pytest bass_py/mio/ --collect-only -q | tail -1`
= `108 tests collected`.

**Smoke-test skip composition** (touched surface, 4 skips):
unchanged from W10 end-of-phase — 2 × mio.core/reporting
(W6 SKIP-02b-v3-LEGACY), 1 × `fig_certification_matrix` family
(W9), 1 × `test_bulkflow_likelihood.py:303` dynesty contract guard
(W10D1).

---

## 1. Audit target reconstruction

Three landings, three distinct audit targets — workspace-layer
runtime-gate conversion of a documented invariant (W17D1),
convention-drift hedge on the A36a YAML sidecar (W17D3), and
design-layer cache-replay drift protocol (W17D5). No new production
code surface; all three landings either add a test or add dossier
prose.

### W17D1 — `MioCertificate.git_commit` at-instantiation runtime gate (closes W16 F2)

- **Core claim**: A44.3 and prior audit notes (W6 FM6 / W11 F5)
  state that `MioCertificate.git_commit` captures HEAD at
  construction time, not at artefact-emission or read time. The
  invariant was documented-only: a future refactor that made
  `git_commit` a property / descriptor re-resolving HEAD on access
  would silently invalidate A44's sequence diagram.
- **Algorithm**: directly instantiate a `MioCertificate` with a
  concrete string `git_commit="a1b2c3d4..."`, monkeypatch
  `subprocess.run` to raise `AssertionError` on any call, and
  (defensively) `mio.interface.mio_certificate._resolve_git_commit`
  on the generator module to return a sentinel `"FFFFFF..."` —
  neither will be called by the contract-layer schema as written
  today, and the monkeypatch is a hedge against a future refactor
  that routes attribute reads through either path. Then read
  `cert.git_commit` via plain attribute access and
  `dataclasses.asdict`, asserting both return the original value.
  Finally assert `type(cert).__dict__.get("git_commit", None)` is
  `None` — i.e. the schema has no class-level descriptor /
  property on the field, because a dataclass field lives only on
  the instance.
- **Output**: 1 file changed
  (`bass_py/workspace/contracts/tests/test_mio_certificate.py`,
  +37 L), +1 test, MIO contribution holds at 107 (workspace-layer
  addition). Touched surface 1077 → 1078.

### W17D3 — A36a YAML `sigma_lit_range_deg` bracketing (closes W16 F3)

- **Core claim**: the W16D3 YAML sidecar introduced
  `sigma_lit_deg` as the scalar representative (midpoint) of any
  ranged literature σ, plus an optional `sigma_lit_range_deg:
  [min, max]` preserving the full range. The W16D3 parity test
  does not consume the range field. A future editor who adds
  `sigma_lit_range_deg` to a currently-scalar probe (or flips the
  reduction convention in the header comment) could drift
  `sigma_lit_deg` outside its declared range without test failure.
- **Algorithm**: load the YAML sidecar, filter to rows carrying
  the optional range field, assert (a) the field is a
  two-element list, (b) `min <= max`, (c) `min <= sigma_lit_deg
  <= max`. Guard against accidental complete retirement of the
  range convention: assert at least one row carries the field
  (today: Radio / CF4pp / BiPoSH). Paired docstring points at
  the W16 F3 audit row and the YAML header's edit protocol.
- **Output**: 1 file changed (`bass_py/mio/tests/test_sigma_cone_
  provenance.py`, +47 L), +1 test, MIO 107 → 108. Touched surface
  1078 → 1079.

### W17D5 — DOS-A45 MIO cache-replay drift protocol (new A4x dossier)

- **Core claim**: A44.6 names a `config_hash` +
  `input_data_hashes` re-verification step the cross-check harness
  must run when consuming a persisted MIO artefact (mode A44.4.2),
  but does not specify the algorithm. A45 writes the pseudocode
  plus the escape-hatch gating plus the paste-ready acceptance
  test list, so the HJ-03 author has a mechanical recipe for the
  replay harness and the reviewer has a single paragraph to check
  against.
- **Algorithm**: dossier-only. The `verify_cache_replay(mio_cert,
  htt_input_bundle, allow_unsigned_config=False)` pseudocode
  recomputes the 16-char sha256 prefix of the payload tuple
  (`report_type`, `probe_name`, `channel`, `departure_variables`,
  `adequacy_indicators`, `consistency_metrics`) via
  `_hash_config` — the same function used at t₁ by
  `mio.interface.mio_certificate.build_mio_certificate`. The
  input-data check compares the harness's observed hash bundle
  against the certificate's `input_data_hashes` as a set (bag-
  equality) rather than as an ordered list, consistent with A32.4.
  The escape hatch is a kwarg-only opt-in for (a) pre-W6 legacy
  certificates and (b) synthetic test certificates; the flag is
  never allowed to bypass the input-data-drift check.
- **Output**: `docs/dossier/A45_mio_cache_replay_drift.md` (269 L).
  Cross-references A32 / A34 / A41 / A42 / A43 / A44. No code
  change.

---

## 2. Contract / interface audit

| Surface | Before W17 | After W17 | Δ |
|---|---|---|---|
| `MioCertificate.git_commit` capture-time invariant (A44.3) | documented-only (audit notes + A44.3); no runtime assertion | workspace-layer microtest locks attribute read to the construction-time value and bans class-level descriptors on the field (W17D1) | **+runtime gate** |
| A36a YAML sidecar `sigma_lit_range_deg` optional field | consumed by neither the W16D3 parity test nor any other consumer (metadata-only) | per-row bracketing hedge — if present, `range[0] <= sigma_lit_deg <= range[1]` + min ≤ max well-formedness + "at-least-one-row" convention guard (W17D3) | **+convention gate** |
| Cross-process MIO → HTT replay hash chain | A44.6 declares the check exists; A32.5 enforcement table assumes `config_hash` / `input_data_hashes` are consumed at replay time; algorithm unspecified | A45 specifies the `verify_cache_replay` pseudocode + escape-hatch semantics + A43 upgrade path + paste-ready five-test acceptance block for the HJ-03 landing PR (W17D5) | **+docs (landing deferred to HJ-03 trigger)** |
| `MioCertificate` schema-hash digest mechanism (A43) | specified W15D3; test deferred to first extension | unchanged (test still deferred per §A43.3) | 0 |
| §0 first-order rules (commit hygiene) | status-gate (W13D1) + scoped pathspec (W15D1) | unchanged | 0 |
| All other surfaces (probe registry, A37 grammar, A36/A42/A44 dossier text, MIO producers, TSC bridges, workspace contracts) | as-of W16 | unchanged | 0 |

All extensions are additive. No schema-hash rotation, no field
retype, no field removal, no producer-side runtime change. The
two new assertions (W17D1 runtime gate on `git_commit`, W17D3
YAML range-bracketing) exercise existing state under stricter
gates; A45 is documentation-only.

---

## 3. Phys-math audit

No physics or numerical-method change landed this phase. All three
landings are runtime-contract / dossier-surface additions.

- **W17D1**: string-equality and identity assertions on a frozen
  dataclass attribute. The `monkeypatch.setattr(_subprocess,
  "run", ...)` path is defensive: `workspace.contracts.mio_
  certificate` imports nothing from `subprocess`, so the
  monkeypatch never fires on current code. The value locked is
  that this remains true — a future refactor that imports
  `subprocess` into the contract module to re-resolve HEAD at
  attribute read would trip the assertion.
- **W17D3**: arithmetic bracketing on YAML-provided float
  triples. Three current triples satisfy the bracket by
  construction at midpoint convention (12 ∈ [10, 14], 11 ∈ [10, 12],
  20 ∈ [15, 25]). No physics claim is asserted.
- **W17D5**: A45 is specification-only. The `_hash_config` 16-char
  sha256 prefix is an existing MIO-interface helper; §A45.2
  references it by signature without introducing a new reduction.

---

## 4. Code path audit

- **W17D1**: pure-Python test addition at the workspace-contract
  layer. Uses the module's existing `_certificate(**overrides)`
  helper. Imports `subprocess` and `workspace.contracts.
  mio_certificate` (the module under test) with a `hasattr`
  guard on `_resolve_git_commit` — the contract module does not
  define it today, so the second monkeypatch is skipped; the
  test still passes because the attribute read never touches
  subprocess either.
- **W17D3**: pure-Python test addition to MIO's provenance-tests
  module. Reads the YAML sidecar via the existing
  `A36A_YAML_PATH` module-level path + `yaml.safe_load`. Iterates
  only rows containing the optional range key; the "at least one
  row present" assertion guards against a silent full retirement
  of the range convention.
- **W17D5**: documentation-only (`docs/dossier/A45_*.md`). No
  Python file touched; no test added. The dossier references
  existing code anchors
  (`bass_py/workspace/contracts/mio_certificate.py`,
  `bass_py/mio/interface/mio_certificate.py`,
  `bass_py/tsc/integration/htt_bridge.py`) but adds no
  production-time wiring.
- No `bass_py/bass/*` file touched (lane discipline); no
  `plots/physics_gallery/` file touched (gallery-lane discipline);
  no `project/*` file touched (W8 FM1 /
  `feedback_project_local_only`). `git status --short` during
  W17D3 showed unstaged bass-lane edits to
  `bass_py/bass/hierarchy/{__init__,nabla_dispatch,test_nabla_
  dispatch,test_nabla_dispatch_fb22}.py`; the W15D1 scoped-
  pathspec rule excluded all four from our commit by construction
  (see §6 check #1).

---

## 5. Numerical / pipeline audit

| Item | Assessment |
|---|---|
| Solver suitability | n/a (no numerics landed this phase). |
| Tolerance sensitivity | **W17D3** — assertions are integer / small-float bracket tests; no tolerance knob exposed. **W17D1** — string equality and `None`-identity tests; no tolerance. |
| Underflow / overflow | n/a. |
| Conditioning | n/a. |
| Cache / state leakage | `monkeypatch` is function-scoped by pytest; both monkeypatched targets are restored on test exit. `A36A_YAML_PATH` is resolved per-test-call. |
| Seed / reproducibility | n/a (deterministic pure functions + file-read). |
| Baseline reproduction | `pytest bass_py/mio/` = 108/108 green in ~1.6 s; `pytest bass_py/workspace/contracts/tests/test_mio_certificate.py` = 5/5 green in 0.08 s; touched-surface 1079/0/4 (+2). Two independent pytest invocations during W17 landings returned identical counts. |
| OOD / misspecification | A45 names two off-happy-path failure modes the replay guard will catch once HJ-03 lands (hand-edited certificate, drifted input bundle); these are design-layer failure modes, not current runtime diagnostics. The TSC-06 in-memory harness (A44.4.1) does not exercise them because it has no cache edge. |

---

## 6. Ranked failure modes (P0–P3)

Per the NEXT_SESSION §2 Week 17 Day 7 directive this section MUST
include a §6 W12 F1 / W14 F1 cross-lane-contamination recurrence
check verifying the W15D1 scoped-commit rule was followed on every
W17 sha via `git show --stat`, with an adversarial-stress-test
narrative if the bass_py lane commits during the W17 window.

| # | Severity | Type | Symptom | Root cause | Cheapest discriminator | Misinterpretation risk |
|---|---|---|---|---|---|---|
| W17 check #1 | **PASSED** | process (W12 F1 / W14 F1 recurrence) | `git show --stat 151fbc4 3137cc0 a4dc670` returns (1 file: `bass_py/workspace/contracts/tests/test_mio_certificate.py`) + (1 file: `bass_py/mio/tests/test_sigma_cone_provenance.py`) + (1 file: `docs/dossier/A45_mio_cache_replay_drift.md`). Every file is on this lane's owned surface; no `bass_py/bass/*`, no `plots/physics_gallery/*`, no `project/*`, no unrelated dossier paths. **Zero cross-lane commits on `main`** landed between `e9afa8e` (W16 §6 addendum) and the three W17 shas — the three landings sit consecutively. **Working-tree adversarial exercise on W17D3**: `git status --short` before W17D3 showed four unstaged bass-lane files under `bass_py/bass/hierarchy/` (`__init__.py`, `nabla_dispatch.py`, `test_nabla_dispatch.py`, `test_nabla_dispatch_fb22.py`). The W17D3 `git commit -m ... -- bass_py/mio/tests/test_sigma_cone_provenance.py` invocation excluded all four by construction — `git show --stat 3137cc0` returns exactly one file. | Both the W13D1 status-gate (observed the drift) and the W15D1 scoped-pathspec rule (excluded the drift) held. This is a distinct adversarial scenario from W16D7's cross-lane-commit-between-landings — the bass-lane edits sat in the unstaged working tree rather than a separate commit. Either mitigation alone would have kept the gate green; the scoped-pathspec rule did so without requiring the status-gate to trigger a manual reset. | n/a — positive finding. | a working-tree-drift exercise is narrower than a concurrent-commit exercise; the W15D1 rule's coverage of concurrent commits remains certified by W16D7's addendum and by this phase's observation (no concurrent commit appeared, so that scenario was not retested this week). |
| F1 | **P3** | docs (A45 freshness window) | A45.2's `verify_cache_replay` pseudocode names `_hash_config` as the re-hashing helper. If a future MIO-layer refactor changes the signature of `_hash_config` (e.g. reorders its positional args or swaps the 16-char prefix length), A45.2's pseudocode becomes stale and the HJ-03 author will either paste-copy the wrong version or silently diverge. | the pseudocode is a leaf-reference on a helper that lives in a single module; no dossier-test exists to catch rename / resize. | optional W18+ follow-up: add a one-line acceptance assertion to `test_mio_certificate_generator.py` that `_hash_config.__name__ == "_hash_config"` and the hash output is 16 chars — a docs-↔-code anchor that fails if the helper moves. | a reader assumes A45.2 is a faithful sketch; the helper moves; the HJ-03 PR paste-copies a broken pseudocode. |
| F2 | **P3** | docs (A45 test-list paste-readiness) | §A45.6's five-test block is paste-ready only if HJ-03's harness signature accepts `mio_cert` as input and exposes a `htt_input_bundle` descriptor shape. If HJ-03 lands with a different signature, the tests need per-item translation before landing. | signature not yet fixed; A45.6 assumes the A44.4.2 pseudocode shape. | optional W18+ follow-up when HJ-03 lane opens: cross-link A45.6 ↔ A41.6 (HJ-03 extension checklist) to ensure the harness signature freeze happens at the same time as the acceptance-test land. | HJ-03 author paste-copies the test block, discovers a signature mismatch, and either hand-translates (risk) or lands a looser guard than A45 spec. |
| F3 | **P3** | process (rate-of-check confidence) | The W17 §6 check passed on a different adversarial scenario (working-tree drift) than W16 §6 (concurrent commit in audit window). The W15D1 scoped-pathspec rule has now been stress-tested under two distinct scenarios across two consecutive phases; it has not been stress-tested under a three-way race (this lane + bass lane + gallery lane committing into the same audit window). | the three-lane scenario has not occurred in the repo's history; cannot certify rule coverage without observation. | no repair; continue §6 checks every phase. Flag the first phase where three lanes commit into the same window. | two distinct passes under two distinct adversarial scenarios is stronger evidence than two repeats of the same scenario, but still does not certify three-lane coverage. |

**No P0 / P1 items found.** The W12 F1 / W14 F1 process pattern
did not recur this phase (W17 check #1 PASSED under a different
adversarial scenario than W16's check #1). The three residual P3
items are soft surfaces — F1 / F2 are dossier freshness hedges,
F3 is a statistical point about confidence in the process rule.
None block W18 execution.

---

## 7. Verifier results

**A. Physics verifier**
- **known-limit recovery**: **n/a** — no numerical claim landed.
- **dimensional consistency**: **n/a** — string / float / docs
  surface.
- **sign / normalization**: **n/a**.
- **positivity / admissibility**: **passed** — `PROMOTED_SIGMA_
  CONE_PROBES` frozenset membership unchanged from W14D5/D6; no σ
  value modified by W17.

**B. Code verifier**
- **contract satisfaction**: **passed** — `MioCertificate`
  signature unchanged; the W17D1 microtest exercises the existing
  `__init__` via `_certificate(**overrides)`. `STANDARD_PROBES`
  read-only access; the W17D3 sibling test reads the same YAML
  path the W16D3 parity test does. A45 introduces no signature.
- **actual code-path usage**: **passed** — W17D1 exercises
  `MioCertificate.__init__` with a concrete `git_commit` kwarg
  and `dataclasses.asdict(cert)` on the result; W17D3 exercises
  `yaml.safe_load` on the existing sidecar and iterates the
  `probes` list.
- **regression risk**: **low** — touched-surface 1077 → 1079
  (+2), 0 failures, 0 skip-change. Full `bass_py/mio/` 108/108
  in ~1.6 s. Full touched-surface pytest 1079/0/4 in ~34 s.
- **reproducibility**: **passed** — `monkeypatch` scope restored
  per test; `yaml.safe_load` deterministic on a repo-tracked file.

**C. Numerical verifier**
- **tolerance robustness**: **passed** — W17D1 uses plain string
  equality + `None`-identity; W17D3 bracket uses exact `<=`
  (integer-boundary cases all pass by construction).
- **convergence / stability**: **n/a**.
- **baseline reproducibility**: **passed** — two independent
  pytest runs during W17 landings returned identical test counts.
- **uncertainty / misspecification**: **n/a**.

**D. Dossier verifier**
- **A45 cross-references resolve**: **passed** — relative markdown
  links to `A32_mio_certificate_schema.md`,
  `A34_g19_cross_check_protocol.md`,
  `A41_mio_report_type_extension_protocol.md`,
  `A42_evidence_anatomy.md`,
  `A43_schema_hash_digest.md`,
  `A44_mio_htt_handshake_sequence.md` all resolve at the same
  directory level; code anchors
  (`bass_py/workspace/contracts/mio_certificate.py`,
  `bass_py/mio/interface/mio_certificate.py`,
  `bass_py/tsc/integration/htt_bridge.py`) exist at the linked
  relative paths.
- **A45 anchor links**: **passed** — internal anchors `#a451-
  purpose` through `#a458-no-code-landing-in-this-appendix`
  follow the GitHub markdown slug rule.
- **A45 escape-hatch upgrade path**: **passed** — §A45.5
  explicitly names the W15 F3 / A43.3 digest trigger as the
  mechanism that narrows the `allow_unsigned_config=True` window;
  the step-2 `""` check is described as transitioning to a
  `digest_version < A43_INTRODUCED_VERSION` check without
  rewriting the algorithm. No dangling "future work" without a
  named trigger.
- **W16 F2 / F3 carry-forward closure**: **passed** — the two
  W16 P3 residuals are fully closed by W17D1 + W17D3. The §3
  carry-forward table rows collapse to `RESOLVED W17D1: see
  test_git_commit_is_capture_time_not_lazy` and
  `RESOLVED W17D3: see test_a36a_yaml_range_brackets_midpoint`.
  Handled in W17D7 NEXT_SESSION rotation.

---

## 8. Minimal repair plan

No P0 / P1 repair needed. Three opportunistic patches for W18+:

| # | Patch | Load-bearing? | Failure mode avoided | New test | Baseline impact |
|---|---|---|---|---|---|
| R1 | Add a one-line assertion in `test_mio_certificate_generator.py` (or sibling) that `mio.interface.mio_certificate._hash_config` returns a 16-char lowercase-hex string on the frozen payload tuple. Anchors A45.2's pseudocode to the helper's observable shape. | no (P3 docs-↔-code anchor). | F1 — stale A45.2 pseudocode if `_hash_config` is silently renamed / resized. | +1 assertion (or +1 test). | additive. |
| R2 | Cross-link A45.6 ↔ A41.6 (HJ-03 extension checklist) so the harness signature freeze lands alongside the acceptance-test block. Prose-only edit to both dossiers. | no (P3 coordination). | F2 — HJ-03 author discovers signature-mismatch after paste-copying §A45.6. | 0. | additive prose. |
| R3 | A43 digest test landing at first actual schema extension (HJ-03 / HJ-04 / TSC-05 v2). **Unchanged from W15 R3 / W16 R3 — still gated on trigger arrival.** | no (P3 timing, blocked on external trigger). | W7 FM3 code-side closure. | +2 (one per contract). | additive (+2). |

All three are deferrable; none block W18 execution.

---

## 9. Minimal test set (landed or referenced)

- **Baseline reproduction**: `pytest bass_py/mio/` → 108/108
  green in ~1.6 s; `pytest bass_py/workspace/contracts/tests/
  test_mio_certificate.py` → 5/5 in 0.08 s; touched-surface
  1079/0/4 (+2 over W16 baseline).
- **Edge / adversarial**:
  `test_git_commit_is_capture_time_not_lazy` (W17D1 —
  monkeypatches `subprocess.run` *and* the MIO-interface
  `_resolve_git_commit` defensively; asserts both direct
  attribute access and `dataclasses.asdict` return the
  construction-time value; asserts no class-level descriptor
  on the field);
  `test_a36a_yaml_range_brackets_midpoint` (W17D3 — per-row
  bracket check on ranged-σ probes; well-formedness min ≤ max
  guard; "at least one row carries the range field" convention
  guard).
- **Physics sanity**: n/a — no numerical claim landed; the tests
  are runtime-contract + convention-drift gates.
- **Regression**: full touched-surface `1079 / 0 / 4` (+2 over
  W16 baseline); MIO contribution 107 → 108; tsc standalone 602
  unchanged.

---

## 10. 최종 판정

- **통과** — 치명적 오류 없음. W17 세 landings (W16 F2 A44.3
  runtime-gate microtest + W16 F3 YAML range-bracketing + A45
  cache-replay drift dossier) 모두 contract ↔ code ↔ test 일관.
  MIO contribution 107 → 108. **W12 F1 / W14 F1 재발 없음**
  — §6 W17 check #1 PASSED; 세 W17 commits 각각 단일 lane-
  owned path만 포함. **W17D3은 scoped-pathspec 규칙의 두 번째
  adversarial stress test** (W16D7의 concurrent-commit 시나리오와
  다른 working-tree-drift 시나리오로, 네 개의 bass-lane 파일이
  unstaged index에 있었음에도 pathspec이 구성적으로 제외).
  세 residual P3 (F1 A45.2 docs-freshness, F2 A45.6 paste-
  readiness, F3 three-lane race stress-test) 모두 deferrable.
- **지금 당장 구현/수정할 1개**: 없음. W17 gate 다섯 항목 전부
  green; W18 active priorities 는 §8 R1–R3 중 하나 (또는 W17
  F1/F2/F3 중 하나를 닫거나 신규 A4x dossier) 로 caller 판단.
- **지금 손대면 안 되는 1개**: A43 digest 테스트의 즉시 착지
  (W15 R3 / W16 R3 반복 — trigger 가 아직 미도착; 현재 schema에
  freeze 하면 첫 확장 PR이 paste-replace 를 강요받을 뿐 추가
  catch 는 없음). HJ-03 production wiring 또한 bass_py W10-02
  K_ℓ atlas 착지 전까지 금지 (governing plan §17.3 의존 대기
  목록; 현재 주 BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md v3 §17.3
  유지).

---

## Week-17 final gate (per NEXT_SESSION §2 Week 17)

- [x] W16 F2 `MioCertificate.git_commit` runtime-gate microtest
      landed (W17D1 `151fbc4`; +1 test; workspace-layer).
- [x] W16 F3 A36a YAML range-bracketing hedge landed (W17D3
      `3137cc0`; +1 test; MIO 107 → 108).
- [x] One of A45 dossier / MANU-CH03 extension landed — **A45
      picked** (W17D5 `a4dc670`; new dossier, 269 L; committed
      per policy since A45 sits under `docs/dossier/` rather than
      `/project/`).
- [x] Phase-boundary audit log written (this file); §6 W12 F1 /
      W14 F1 recurrence check returns **PASSED** (`git show
      --stat` on the three W17 commits shows only this lane's
      owned paths; **zero cross-lane commits on `main` in the W17
      window**; W17D3 uniquely exercised the scoped-pathspec rule
      against working-tree bass-lane drift — four unstaged files
      excluded by construction).
- [x] No touched-surface regressions (1079 passed; +2 over W16;
      0 failed; 4 skipped unchanged).

All five gate items green. Phase `IND_TRACKS_W17` closes with
zero new P0/P1/P2 findings; three documented P3 residuals
(F1/F2/F3) deferred to W18+.
