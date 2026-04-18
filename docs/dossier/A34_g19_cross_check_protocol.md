# A34 · G19 cross-check protocol

**Appendix**: A34 (§11.14.6 of `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3)
**Version**: 2026-04-19 draft (landed with CONTRACTS-02 Week 7 Day 6).
**Code anchor**: [`bass_py/tsc/integration/htt_bridge.py`](../../bass_py/tsc/integration/htt_bridge.py)
**Related contracts**: [`bass_py/workspace/contracts/`](../../bass_py/workspace/contracts/)
— sibling `MioCertificate`, `HttForwardOutput`, `AtlasEntry`.
**Governing rules**: v3 §4.5.4 (G19 hard separation) + §10.2bis
(enforcement matrix); INDEPENDENT_TRACKS_PLAN v1.1 §14.3 (TSC-06 v3
sidenote); v3 §10.2 (HTT ↔ MIO contract table).

---

## A34.1 Purpose

A34 documents the **cross-check protocol** connecting the three
independent epistemic domains — HTT posteriors, TSC diagnostics, and
MIO certificates — under the G19 "Hard separation" rule. The protocol
specifies:

1. *what a cross-check is* (§A34.2);
2. *which channels are cross-checks vs. merges* (§A34.3);
3. *how the `is_cross_check=True` contract is expressed in code*
   (§A34.4);
4. *which failure modes the protocol is designed to catch* (§A34.5);
5. *the architectural failure modes that would be introduced if the
   cross-check channel were relaxed into a merge* (§A34.6).

The protocol is deliberately narrow: the only legitimate cross-check
currently wired through the repo is TSC-06
(`tsc.integration.htt_bridge`), which compares the HTT
filling-fraction posterior mean against the TSC filling-fraction
diagnostic. Additional cross-checks (e.g. HJ-04 evidence-anatomy
↔ HTT ln B decomposition) will be added when their parent MIO
modules land, and must follow the exact protocol documented here.

## A34.2 Definition — "cross-check"

Under G19, an object is a **cross-check** iff it satisfies all five
of the following structural properties:

| # | Property | Enforcement |
|---|----------|-------------|
| 1 | Produces two numerically-comparable scalars from two **independently implemented** code paths. | Code-path review; per-call `rel_difference` is recorded in the report. |
| 2 | Does **NOT** combine the two scalars into a single merged, summed, or averaged estimator. | Type-level: no `F_Bayes_merged` / `combined` / `unified` field on the report dataclass. Test-level: [`test_tsc_htt_ff_cross_check_not_merged`](../../bass_py/tsc/integration/test_htt_bridge.py). |
| 3 | Carries a frozen `is_cross_check: bool = True` tag that cannot be set to `False` at construction. | `FFCrossCheckReport.__post_init__` raises `ValueError` on attempted negation. |
| 4 | Exposes a loud-fail guard (`assert_cross_check_consistent`) that refuses to return normally on numerical mismatch or band violation. | `CrossCheckMismatch` subclass of `AssertionError`. |
| 5 | Is consumed downstream only for agreement / disagreement reporting — never for likelihood multiplication, posterior update, or evidence integration. | Documentation + test suite; the report type has no `to_likelihood()` / `as_posterior_bundle()` entry point. |

Any object satisfying properties 1–5 is G19-compliant. Any object
missing one of them is **not** a cross-check; if it exposes a merged
estimator it is a G19 violation.

## A34.3 Channel catalogue

| Channel | Owner | Counterparty | Report type | Status (2026-04-19) |
|---|---|---|---|---|
| TSC-06 filling fraction | `tsc.integration.htt_bridge.ff_htt_mc_cross_check` | `htt.core.analysis_extended.FillingFraction.mc_posterior` | `FFCrossCheckReport` | **landed (Week 7 Day 5)** |
| HJ-04 evidence anatomy | `mio.decomposition.evidence_anatomy` (planned) | `htt.core.analysis_extended.EvidenceComparison.run_all` | `MioCertificate(report_type="evidence_anatomy")` | deferred — dependencies in Week 10+ |
| PR13AM ↔ COMMON-A spherical-mean regression | `htt.PR13AH_observables_reintegration` | `common.sky_geometry.spherical_mean` | `ChannelSummary` diff | landed (W4 R1 anchor) |
| MIO HJ-02a ↔ HTT dipole consistency | `mio.coherence.directional.to_mio_certificate` | (HTT dipole likelihood, advisory only) | `MioCertificate(report_type="directional_coherence")` | landed (Week 6), advisory not a numerical cross-check |

Only TSC-06 currently exposes a numerical `is_cross_check=True`
contract. The other rows are either advisory (where no matched
numerical pair exists) or deferred to future weeks.

## A34.4 Contract expression in code

The TSC-06 channel implements the full protocol. The salient
architectural commitments:

```python
@dataclass(frozen=True)
class FFCrossCheckReport:
    F_Bayes_tsc: float                # Path A — tsc diagnostic
    F_Bayes_htt_mean: float           # Path B — htt mc_posterior
    F_Bayes_htt_median: float
    abs_difference: float
    rel_difference: float
    within_published_band: bool
    is_cross_check: bool = True       # FROZEN (G19)
    scenario: str = "gaussian"
    n_samples: int = 0
    config: Mapping[str, Any] = ...

    def __post_init__(self) -> None:
        if self.is_cross_check is not True:
            raise ValueError("... G19 architectural stance ...")
```

`ff_htt_mc_cross_check` draws from `numpy.random.default_rng(seed)`
twice with identical parameters — once inside
`htt.FillingFraction.mc_posterior` and once inside the tsc-side
helper `_tsc_filling_fraction_from_stream`. The tsc-side helper
restates the MES literal coefficients (5/3, 3, 3/7, 2.69) rather
than importing them from htt; any silent drift on either side fires
`assert_cross_check_consistent` at the caller's chosen `rtol`.

The guard function signature encodes the two failure axes directly:

```python
def assert_cross_check_consistent(
    report: FFCrossCheckReport,
    *,
    rtol: float = 5.0e-2,
    require_within_band: bool = True,
) -> None:
    """Raises CrossCheckMismatch on numerical drift *or* band violation."""
```

A caller that wants only the numerical check (e.g. during an isolated
refactor of `FillingFraction.x_V`) passes `require_within_band=False`;
a caller downstream of a production pipeline step asserts both.

## A34.5 Failure modes the protocol catches

1. **Coefficient drift on either side.** If a future patch changes the
   MES `(5/3, 3, 3/7)` literal on the tsc side but not htt, or vice
   versa, the tsc and htt F_Bayes diverge. `rel_difference` crosses
   rtol and `CrossCheckMismatch` surfaces at the TSC-06 hero test
   `test_S3_tsc_htt_numerical_agreement` (rtol 1e-6).
2. **Frame-correction regression.** If `eta_udot` or the `2.69 eps1`
   frame correction changes on only one side, Path A and Path B
   disagree at ~10 % → band violation.
3. **Scenario-table drift.** If `SCENARIOS["S3"]["eps1"]` changes on
   the htt side but not in a tsc-side consumer, the recomputed
   x_V samples disagree and the cross-check fails.
4. **RNG stream non-determinism.** The protocol pins
   `numpy.random.default_rng(seed)`; any upgrade that changes the
   default bit-generator would emit a band violation first (not a
   silent numerical drift), and the flagged rtol mismatch points
   reviewers at the stream, not the physics.
5. **Accidental merge.** The `test_tsc_htt_ff_cross_check_not_merged`
   suite scans `tsc.integration.htt_bridge.__all__` for substrings
   `merge`, `combine`, `sum_score`, `unified`, and checks that the
   report dataclass does not expose any `F_Bayes_merged`-style field.
   A PR that would introduce a merge is blocked at review time.

## A34.6 Failure modes a merge would introduce

If A34.2 property 2 were relaxed — i.e. if the repo ever exported a
single merged `F_Bayes_combined`-style score — the following
architectural regressions would surface:

- **Collapse of the two independent epistemic domains.** tsc and htt
  stop being witnesses of each other; a bug that corrupts both sides
  identically becomes undetectable. G19's purpose — to preserve
  independent-check-ability — is lost.
- **Miscounting of evidence.** Averaging F_Bayes_tsc and F_Bayes_htt
  into a single score double-counts shared uncertainty. The merged
  variance is NOT `(sigma_tsc² + sigma_htt²) / 4` because the two
  estimators share the eps1 / eps2 / eps3 draw.
- **Silent loss of cross-check power.** Once merged, any residual
  disagreement is absorbed into the merged score's scatter. The
  regression anchor that `rel_difference` must stay below 1e-6
  disappears; coefficient drift can accumulate silently for multiple
  PRs before anyone notices.
- **Regression of the MIO boundary.** A merged tsc ⊕ htt score
  contaminates the architectural separation v3 §4.5.4 was designed to
  preserve: MIO reports what the data says without a model, HTT
  reports posteriors under a model, and TSC reports physical
  realisability. A merged score would cross two of these boundaries
  at once.
- **Violation of the `is_cross_check=True` invariant.** Any downstream
  code relying on the frozen tag to skip likelihood ingestion would
  behave incorrectly on the new merged score, opening a path for the
  merged value to leak back into HTT as a likelihood input — a
  direct G19 violation.

The protocol in §A34.2 is therefore **not** a style choice; it is the
load-bearing invariant that preserves the G19 separation in the
presence of future refactors.

## A34.7 Extending the protocol (for future MIO channels)

When HJ-04 evidence anatomy lands (parent plan v3 §4.5.3.4, Week 10+),
the MIO module must:

1. Instantiate a dedicated report type that inherits the five
   properties of A34.2.
2. Expose a top-level helper analogous to
   `ff_htt_mc_cross_check(...)` that takes the counterparty (HTT
   `EvidenceComparison.run_all` result) and returns the new report.
3. Expose a loud-fail guard of the shape
   `assert_<channel>_consistent(report, *, rtol, ...)`.
4. Add a test file under `bass_py/mio/decomposition/` or
   `bass_py/tsc/integration/` that asserts (a) the new report's
   `is_cross_check` tag is frozen `True`; (b) the hero anchor
   numerical agreement at rtol; (c) no merge-style field leaks into
   the dataclass; (d) a deliberately mismatched report raises the
   loud-fail guard.
5. Update §A34.3 to list the new channel with its status.

Any extension that omits one of (1)–(5) is not G19-compliant and
must not merge.

## A34.8 Appendix — related tests

- [`bass_py/tsc/integration/test_htt_bridge.py`](../../bass_py/tsc/integration/test_htt_bridge.py)
  — 32 tests; class `TestTscHttFfCrossCheckNotMerged` is the
  merge-prohibition regression anchor.
- [`bass_py/workspace/contracts/tests/test_g19_enforcement.py`](../../bass_py/workspace/contracts/tests/test_g19_enforcement.py)
  — repo-wide G19 enforcement battery (MioCertificate /
  HttForwardOutput / AtlasEntry).
- [`bass_py/tsc/admissibility/test_three_bound_hierarchy.py`](../../bass_py/tsc/admissibility/test_three_bound_hierarchy.py)
  — TSC-03 cross-check anchor against `htt.core.bounds` (rtol 1e-10,
  a sibling cross-check channel outside the filling-fraction axis).
- [`bass_py/tsc/charts/test_michaelis_menten_export.py`](../../bass_py/tsc/charts/test_michaelis_menten_export.py)
  — TSC-05 zero-drift regression between the tsc and bass MM SSOT
  mirrors (another sibling channel).

These three test files collectively cover the TSC-side cross-check
surface exposed as of 2026-04-19.
