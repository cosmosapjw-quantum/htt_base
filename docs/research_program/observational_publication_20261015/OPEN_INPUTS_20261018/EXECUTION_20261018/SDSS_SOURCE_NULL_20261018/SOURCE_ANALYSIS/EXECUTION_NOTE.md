# Actual-source execution facts, 2026-10-19

Owner: obsstat. Scope: released SDSS v1.1.0, frozen numerically lowest 64
distinct source boxes (0–63), observer Y0, source angular mask and all galaxy
types, with the contracted redshift selection. Claim tier C0;
NON_CLAIM_BEARING_SOURCE_DIAGNOSTIC; transfer source none. Allowed use is the
declared estimator diagnostic on this frozen source sample. Separate-box
independence remains NOT_CERTIFIED. Covariance is DIAGONAL_WORKING plus finite
source empirical covariance, with shared-window terms retained. Physical/H02
coverage, CF4 joint-law substitution, native/family identification and original
42-task completion are forbidden uses. Scientific admission remains HOLD.

The unchanged one-shot command was executed once from the existing checkout:

```sh
.venv/bin/python -B docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/SDSS_SOURCE_NULL_20261018/run_source_analysis.py
```

Observed branch: `research/htt-open-input-theory-20261018`; HEAD:
`2840975012db67f7a5cb0ef3b7148e262fb634d7`. Requested executor:
`gpt-6.1-sol/high`; independently observed runtime identity: UNKNOWN.
Monitor session 73042, controller PID 1512145, science worker PID 1531040;
both processes terminated. Science run ID: `1792336547886924695`.

Approval, selection, header, archive and prepared code hashes matched before
launch. `INPUT_BINDINGS.json` preserves the exact identities; source archive
SHA256 is `eaac95f323e6dcb6c3626122793d734790f8b27cb0b231f31e60cdd6255b0536`.
The driver revalidated the whole archive and extracted selected members before
starting the science clock. Its worker ran under the declared single-thread
environment. No code, mathematical convention, selection, control, tolerance or
scientific limit was changed; no passing fixture or campaign was rerun.

`RETURN.json` records exit 0, `EXECUTED_AWAITING_INDEPENDENT_REVIEW`, elapsed
science time 38.42006481997669 s and cumulative time 40.71262605697848/600 s.
The shared ledger has the matching START/END pair; the prior cumulative charge
was 2.2925612370017916 s. Raw stdout reaches `COMPLETED 64/64 box=63`.
All six controls on the designated first actual-source mock completed with
`PASS_FINITE_CONTROLS_ON_DESIGNATED_FIRST_SOURCE_MOCK`, using the unchanged
1e-10 mag absolute and 1e-8 relative tolerances. This control status is not an
independent review or broader scientific admission.

Recorded descriptive results from `SUMMARY.json`:

- K/64 = 4/64 = 0.0625 at threshold 2.955166847497834, with exceedances in
  source boxes 19, 32, 34 and 62. This is not calibrated physical/H02 coverage.
- Raw uncentered T spans 0.7003313765567362–4.111576860299339.
- Empirical/mean-working diagonal variance ratios span
  0.9667173102163353–1.4611966237667524.
- Same-basis empirical cross-window correlations span
  0.7209600812411991–0.8594910967509404. The shared windows remain correlated.

The output contains 64 per-mock JSON files, all vectors and working covariances
in `SUMMARY.json`, `CONTROLS.json`, `INPUT_BINDINGS.json`, `REPORT.md`, raw
stdout/stderr, `RETURN.json`, and PNG/PDF pairs for coefficients/variance,
empirical correlation and raw descriptive T. The coefficients/variance PNG
was visually inspected for readable axes and provenance footer; the generated
report has no production-forbidden affirmative claim phrases. Fresh read-only
independent review is pending. No publication was performed.
