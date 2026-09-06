# T2 code and test review

Verdict: PASS_WITHIN_TWO_FILE_REPAIR_SCOPE.
Reviewer: WORK_THREAD. This is the second sequential review, after provenance/claim review, by the same result-informed work reviewer. LOCAL_CODEX remains the sole source author/native executor. No blind or two-reviewer independence is claimed.

The exact submitted patch was replayed in memory against the returned originals with LF-only splitting. Both reconstructed outputs match the returned repaired bytes and declared Git/SHA-256 identities. The T2 diff consists solely of the three approved token replacements. The test diff is confined to the existing test file: standard-library re and pytest imports, private assertion helpers, preservation of the three original test names, and the directly relevant parametrized cases.

The complete original Cayley-Hamilton and moment string requirements are retained in _T2_FORMULAS. The truncated newline-rac{ check remains and follows a raw-character guard. Cholesky layout tolerance uses only ASCII space/TAB/LF/CR, after rejecting C0 except TAB/LF/CR and DEL. The unique upper-triangular/positive-diagonal wording remains required. Matrix transpose/order, determinant, signed diagonal, B=S_chi B_+, orthogonality and nonunique-choice exclusion remain meaningful; the full signed diagonal relation is additionally required.

The finite-scope helper accepts only HEALPix and HEALPIX in the existing negative clause. It retains the exact three machine-readable boundary strings and native-BASS denial. It does not fold mathematical case. Original helpers and reader behavior were not replaced by a general parser or sanitizer.

The 40 added nodes comprise:
- 5 allowed Cholesky wrapping variants and 2 permitted proper-name variants.
- 3 separately reintroduced form-feed sites, 1 actually truncated token, and 3 altered coefficient/moment-index cases.
- 6 canonical-section mutations covering uniqueness, positive diagonal, orientation sign, factor order, transpose and the excluded nonunique choice.
- 5 scope mutations covering removed/reversed denial, unapproved spelling, unresolved constant and native-BASS denial.
- 15 control cases: five forbidden characters across the three original helpers.

All 33 negative nodes construct an effective mutation before entering pytest.raises. _mutate_once additionally requires exactly one existing target. Only AssertionError satisfies the rejection check; import/runtime exceptions do not count. Formula, truncated-token and control cases match the intended assertion message. For the remaining eleven canonical/scope cases, the unchanged source is covered by the original positive tests, and inspection confirms the unique intended changed predicate; no unrelated exception is being credited. Expected caught messages are not separate raw logs, and are not represented as such.

The original collection has 40 unique IDs. The new collection and actual full JUnit have 80 unique IDs, with every original executed and passing. The focused JUnit has 43 passing IDs (the three original source tests plus all 40 added cases), a subset of the full 80. These are not 123 distinct tests. No node was removed, skipped, xfailed, deselected or accepted as zero collection.

The actual native record is CPython 3.12.3, pytest 8.4.2, PyYAML 6.0.3. Source freeze precedes all five captured commands; its digest and the two source identities match each command record. Syntax, diff-check, focused, collection and full-suite commands each have one recorded invocation and exit 0. Raw stdout, stderr, exits and JUnit agree; no timeout is recorded. The complete eight-file argv matches the approved suite. Source manifests retain the frozen repaired bytes afterward.

The command recorder invokes the declared commands through fresh subprocesses, captures stdout/stderr without rewriting, removes external override variables, checks the frozen source before each invocation and preserves the actual return code. It is task evidence, not a new permanent validator. WORK did not import/run the submitted tests or rerun either successful suite. The new WORK artifact reader's own command/stdout/stderr/exit are recorded separately.

Blocking findings: none. No in-scope correction is requested.
Limits: these are bounded documentary assertions and declared mutations, not a general natural-language semantics parser or formal mathematical validation. The local runtime result is not a hosted CI PASS for the future publication commit.
Evidence: exact two-file-repair.patch and source bytes, verified_node_inventory.json, RETURN_VERIFICATION.json, raw command records, source freeze, focused/full JUnit and local self-review.

