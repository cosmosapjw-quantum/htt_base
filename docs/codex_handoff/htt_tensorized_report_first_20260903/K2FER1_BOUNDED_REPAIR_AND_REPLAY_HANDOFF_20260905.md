# HTT Report A — K2FER1 bounded repair and actual replay

@GitHub @Superpowers

## 0. Execute a repair, not another runtime-only probe

The owner returned an actual K2FE failure run under CPython 3.12.13:
syntax exit 0; existing regressions 15 passed / 3 failed; strict regressions
11 passed / 4 failed; total 26 passed / 7 failed. No skips, collection errors,
xfail or xpass were reported. The production strict CLI was correctly not run.
The production bundle was not created and structural_findings was null.

The next task is one bounded source/test repair followed by the existing
K2FE execution. Do not redesign MES, invent another compiler, repeat the PDF
build, or finish with only a readiness report when execution is available.

This handoff is a repair specification, not an applied patch or a passing
execution receipt. In the parent pass that wrote it, both container and
independent Python calls failed before observable execution. The attached ZIP
could not be opened or hashed there. Do not turn those limitations into a
claim that the work runtime is unavailable: the owner's returned test run
already demonstrates a separate executing environment.

## 1. Scope and preserved artifacts

Repository: `cosmosapjw-quantum/htt_base`; report PR: `449`.

Known live head before this document was added:
`a8d5417b3beae46e345392b5c2576c15be83a514`.

Original failed execution snapshot:
`a0784f2a1ce1f4a3fe14195a5f169e4959bd8391`.
Original execution tree:
`036bc001d333cbc61427179edea2bf77fba3ff0a`.
PR base at parent read:
`687234128d7c12d04e68aad0f303c21d2d470393`.

Freshly read PR #449, its current head/tree/base and any relevant changes.
Document-only head movement does not change the frozen executable surface.
An actual change to that surface requires comparison, not silently resetting
expected hashes. If another session already applied this repair, reuse its
verified result rather than duplicating the patch.

The old handoff remains immutable historical evidence:
`K2FE_WORK_THREAD_EXECUTION_HANDOFF_20260905.md`, blob
`e7efaa12815e4d700c5a5b9fbf82d37068a629f0`, available at
`a8d5417b3beae46e345392b5c2576c15be83a514` under this directory.
Read it for the original input/config closure and execution rules. Its
no-source-edit restriction is superseded ONLY for the four paths explicitly
allowed below. Its scientific, canonical and publication restrictions remain.

The 24-page K5 review PDF remains delivered. Its reported digest is
`9f70061a593c58024a406c643a22004b0535bf60c6f5961d7bcd06ea85d3c97c`.
The revised scientific manuscript blob is
`99a3f75c67ece3cfb00179bfd61787f47cb7e7ac`.
Do not regenerate that PDF or edit its scientific source/theorem packs.
Canonical remains T9 v4 / 30 claims; the report candidate has 40 claims.
No Planck/FFP10, BASS/REC/REI, CAS evaluation, scientific claim promotion,
publication approval or merge belongs to this task.

## 2. Failure package intake before source edits

Locate the attached actual file, not the other thread's sandbox URL:
`HTT_REPORT_A_K2FE_FAILURE_PACKAGE_20260905.zip`.
The parent upload was mounted at `/mnt/data/` but the new runtime may mount it
elsewhere; find the attachment rather than guessing that the old absolute
scratch path is portable.

Expected owner-reported ZIP SHA-256:
`77329d5082a7c41c1977f7547fdefb1b6c2e57dde8de907aada560f95bfb112a`.

Compute that digest, inspect archive member paths, reject path escapes or
symlink extraction, and extract into a fresh directory. Verify the packaged
SHA256SUMS and source_manifest. Read K2FE_RESULT.yaml,
K2FE_EXECUTION_RECEIPT.json, K2FE_REVIEW.md, the actual JUnit files and command
stdout/stderr. Recover all seven actual failed node IDs and their tracebacks.
The parent did not read those members; do not invent their detailed contents.

Keep the original archive and extracted source read-only. Keep the original
failure classification and logs even if the repair succeeds. Report exactly
which source identities the manifest covers; it reportedly contains 27 files,
not a certified full-repository checkout.

If the attachment is unavailable, continue with verified Git source and a
fresh unmodified baseline, but say FAILURE_PACKAGE_NOT_AVAILABLE and do not
claim archive hash/JUnit verification. A digest mismatch is instead a hard
PACKAGE_INTEGRITY_FAILED stop for using that archive as evidence.

## 3. Runtime and baseline

Use the available work runtime. Shell/Python smoke may be tried once each if
needed; do not repeat identical failing probes. Prefer existing CPython 3.12.
A bounded installation using the environment's supported mechanism is allowed
if 3.12 is absent. Do not bypass the production CLI's interpreter check.

Use the versions from the existing K2 workflow:

```text
CPython 3.12 (record exact patch version)
pytest 8.3.5
PyYAML 6.0.2
pybtex 0.26.1
Linux with the existing renameat2 no-replacement publisher
```

Lean, Wolfram, Sage and PDF toolchains are not dependencies of this repair.
Their availability must not gate Python-only execution.

Read AGENTS.md and the relevant repository-local harness/validation/claim/
handoff skills. Prefer a full isolated checkout. A hash-verified minimal mirror
is allowed under the original handoff's config/conftest/import-closure rules.
Do not create a fake .git or remove conftest/configuration to obtain a pass.

Before edits, preserve a baseline manifest and recover observed failures from
the verified archive. In a changed runtime, rerun the original two test groups
once on the unchanged source to establish the baseline. Do not run the
production compiler after those failing predecessors. If the baseline differs
from 26/7, record the actual result and cause; do not force expected counts.

## 4. Four-path implementation allowlist

Use a second isolated copy/worktree for repairs. The only pre-existing files
allowed to change are:

| Path | Original Git blob | Allowed delta |
|---|---|---|
| `docs/codex_handoff/htt_tensorized_report_first_20260903/REPORT_A_CITATION_PROVENANCE_MATRIX_V2.yaml` | `3fbaa2f97522cca6d0ad60e0c96655d293ca0d74` | quotes around exactly three existing title values |
| `scripts/compile_report_a_k2f_authority.py` | `d22e439211b0058596c27028d382554657b9f532` | only EXPECTED_INPUT_GIT_BLOBS['base_citation_matrix'] |
| `scripts/compile_report_a_k2fr0_authority.py` | `d89ac38f47e221597fbc2b152b4a6c591c673d81` | only LEGACY_BLOB, to the actually changed helper |
| `tests/contracts/test_report_a_k1r_kinematical_mes_repairs.py` | `bed6f72f9498631f3b945b1d44c0820a4e13a5d9` | two failing documentary checks, their small helpers, and focused positive/negative regression cases |

Put the added focused tests in that same test file so the existing workflow
collects them without a workflow change. Retain its six existing test node
names and all nonaffected machine-readable checks. Other original test files,
input ledgers, bibliography files, science prose, claims, numerical thresholds,
parser implementations and publisher implementations remain byte-identical.
Execution artifacts, patch and review notes go outside the source root.

This task permits the isolated edits and local validation above. Return the
repair patch and exact post-repair source set. Do not commit/push, mutate PR
metadata, merge or change canonical authorities during this execution. The
parent can review and publish the verified repair as a separate decision.
Do not stop for another approval of these four isolated file changes.

## 5. Citation quoting: precise repair and preservation check

Repair all three values, not just the first parser error:

```yaml
# RANDOMIZATION_2024
title: "Randomization Inference: Theory and Applications"
# ROLDAN_NOTARI_QUARTIN_2016
title: "Interpreting the CMB aberration and Doppler measurements: boost or intrinsic dipole?"
# LI_1999
title: "Relative perturbation theory: II. Eigenspace and singular subspace variations"
```

Maintain the original indentation and every title character. Change no author,
year, role, identifier, claim row or key. Do not round-trip the whole file
through safe_dump, which would introduce unrelated byte changes.

Require exactly one occurrence of each original unquoted title line and check
that the entire new file is precisely the old bytes with those three quote
pairs inserted. The old file does not parse, so do NOT assert equality of its
old and new parsed objects. Instead verify the bounded textual delta, then
parse the corrected whole file and check the three decoded titles and retained
17-source/30-row registry against its actual keys.

Add a whole-file parse regression. Also test each of the three original
unquoted forms in isolation by reverting that one title in an otherwise
corrected in-memory copy and requiring a YAML parsing failure. Do not mutate
the source file to run a negative test. Keep the parser and exception policy
unchanged. The applicable external reference is YAML 1.2.2 section 7.3.3:
plain scalars cannot contain colon followed by a space.
https://yaml.org/spec/1.2.2/#733-plain-style

## 6. Documentary contract: formatting tolerance without semantic weakening

The parent's direct source read established three distinct problems:

- line wrapping splits the shared-data non-independence sentence and several
  scope exclusions;
- the test spells HEALPIX while the source spells HEALPix;
- the demanded literal sentence 'feasible response-kernel fibre contains no
  other admissible state' is absent, although the exact equivalence and its
  argument are present.

Use separate test helpers for prose and mathematics. A minimal normalisation
pattern is:

```python
def _prose(text: str) -> str:
    return " ".join(text.split()).casefold()

def _math(text: str) -> str:
    return "".join(text.split())  # preserve mathematical letter case
```

These are a suggested implementation shape, not an executed fixture. Limit
prose normalisation to the actual relevant prose/section. Do not lowercase
mathematical expressions, remove negations, test only unrelated keywords, or
accept a forbidden statement merely because it appears in a historical quote.

In test_k1r_joint_identification_and_shared_data_firewall, replace the absent
literal singleton sentence with checks on the existing exact-response premise,
actual affine-fibre equation and singleton equivalence. Use the source's
case-sensitive mathematical notation, for example:

```text
\Theta(y;\eta)=F_y\cap(X_0+\ker\mathcal R_\eta)

\Theta(y;\eta)=\{X_0\}
\quad\Longleftrightarrow\quad
\{h\in\ker\mathcal R_\eta:X_0+h\in F_y\}=\{0\}
```

Verify the original sentence, after prose whitespace normalisation:
'Their appearance as separate set factors does not make them independent evidence'.
Also retain explicit checks that the complete analysis includes MES ceiling
construction and anchor conditioning, that the response is exact and linear,
and that full column rank is sufficient but not necessary. Retain the existing
YAML evidence-row forbidden-extension checks. Do not renumber ledger result
IDs to resemble Markdown theorem headings; the two source naming schemes are
already related by their content, not numeric string equality.

For test_k1r_scientific_firewalls_remain_closed, check the existing prologue
and integrated-spine prohibitions with wrapping/case tolerance for prose.
Retain the native-BASS, no-observation/no-physical-estimate exclusions,
non-generative-anchor statement, response prerequisite and NO_CLAIM_PROMOTION.
Retain all machine-readable scope_firewall assertions.

Add focused tests using the SAME checking helpers as the repaired tests:

Positive variants must pass:
- harmless prose rewrapping or repeated whitespace;
- HEALPix/HEALPIX casing variation in prose.

Negative variants must fail, one mutation at a time:
- delete or reverse 'does not make them independent evidence';
- delete MES ceiling construction from the complete-analysis sentence;
- remove the exact/linear response qualification;
- change the singleton equivalence symbol or its zero-kernel right-hand side;
- reverse the non-generative-anchor statement;
- permit an observable-to-physical map without a declared response;
- remove the relevant no-observation or native-BASS prohibition.

Each mutation must assert that its target was present and was actually changed.
Do not let a fixture that made zero replacements produce a false negative-test
PASS. Restrict checks to the relevant section/statement so duplicate historical
text elsewhere cannot conceal removal of the active assertion. These tests
exercise documentary guards; they do not prove the mathematical theorem.

## 7. Intentional hash-chain migration, not a bypass

The source dependency is:

```text
corrected citation YAML bytes
        ↓ new Git blob
legacy helper EXPECTED_INPUT_GIT_BLOBS['base_citation_matrix']
        ↓ changed helper bytes and new Git blob
strict compiler LEGACY_BLOB
        ↓ changed strict compiler bytes and its execution SHA-256
new execution manifest / original-to-repaired identity map
```

Calculate every new digest from actual local bytes:

```python
def git_blob(raw: bytes) -> str:
    import hashlib
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()
```

Update only the named expected input entry in the helper; then calculate that
helper's new blob and update only LEGACY_BLOB in the strict compiler. Verify
the two compiler diffs contain no executable logic change. The remaining
seven compiler input digests must remain unchanged. Do not blanket-replace old
hashes throughout the repository. Old handoffs, failure receipts and frozen
contracts retain historical values. Do not mutate a loaded module's constants
or pass enforce_registered_input_blobs=False.

Run tests and compiler in NEW processes after this migration, avoiding stale
imports. Record base snapshot plus full patch and every post-repair file blob;
without an actual new Git commit this is REPAIRED_HASH_VERIFIED_SOURCE_SET,
not BYTE_EXACT_ORIGINAL_HEAD or a fictitious new commit. Test-generated
fixtures are not the production bundle.

If another active consumer blocks the requested execution on one of these
changed identities, report its exact path and role. A direct frozen historical
contract is not automatically authorised for migration. Do not convert this
four-file repair into repository-wide hash churn.

## 8. Replay the registered tests and only then the strict CLI

Preserve each command's cwd, interpreter, argv, stdout, stderr and exit code
without a pipeline hiding the return code. Use separate original/repaired
logs. Preserve source bytes before and after execution; caches belong outside
the source tree where the existing configuration permits it.

```bash
cd "$REPO"
"$PY" -m py_compile \
  scripts/compile_report_a_k2f_authority.py \
  scripts/compile_report_a_k2fr0_authority.py \
  tests/contracts/test_report_a_k1r_kinematical_mes_repairs.py \
  tests/contracts/test_report_a_k2fr0_hardening.py

"$PY" -m pytest -q \
  tests/contracts/test_report_a_k1r_kinematical_mes_repairs.py \
  tests/contracts/test_report_a_k2_kinematical_claim_recompile.py \
  tests/contracts/test_report_a_k2f_compiler.py \
  --junitxml="$RUN/receipts/k2fer1-existing-and-focused.xml"

"$PY" -m pytest -q \
  tests/contracts/test_report_a_k2fr0_hardening.py \
  --junitxml="$RUN/receipts/k2fer1-strict.xml"
```

The repaired first group has the original node names plus added regression
cases. Report actual counts; do not force a target total. Skip, xfail, zero
collection, assertion errors or changed exclusions do not satisfy acceptance.
All four original test files must execute. Do not use --noconftest, a substitute
configuration, deselection, or monkeypatched production hashes.

After all required syntax/tests pass, run the production CLI once:

```bash
"$PY" scripts/compile_report_a_k2fr0_authority.py \
  --repository-root "$REPO" \
  --output-root "$RUN/authority-bundle"
```

The RUN parent must exist and authority-bundle must NOT already exist. Preserve
renameat2/no-replacement behaviour. A new implementation is not an allowed
fallback. If a predecessor fails, do not run the production CLI: return the
actual unresolved failure and minimal next repair, not another general plan.

One bounded repair-and-replay pass is requested. An unrelated new failure
must remain a failure, not trigger broader refactoring or silent weakening.

## 9. Read back the actual six-file production bundle

Expected files, only after production success:

```text
T9_INTEGRATED_CLAIM_EVIDENCE_LEDGER_V5.yaml
REPORT_A_CITATION_PROVENANCE_MATRIX_V3.yaml
REPORT_SECTION_CLAIM_MAP_V3.csv
REPORT_A_ORGANIC_INTEGRATION_MATRIX_V3.yaml
HTT_REPORT_A_REFERENCES_V2.bib
K2F_COMPILATION_RECEIPT.json
```

Use a separate reader to verify the four 40-ID bijections, twenty parsed
bibliography keys, preserved base notation/survivor/repair/vocabulary/history,
30 historical plus 10 candidate claims, four registered statement revisions,
status translations, and non-inheritance of donor execution. Recompute the
sorted-ID SHA-256 from the ACTUAL output IDs. Check all output digests against
the actual receipt; record the receipt's own digest externally.

Check strict source-binding fields and report the ACTUAL structural_findings
and coverage booleans. A successful materialisation with nonempty findings is
not rejected as 'not executed', but is not scientific/canonical acceptance.
Do not invent missing assumptions. If no production execution completed,
structural_findings is null, never an empty successful finding set.

The compiler/source-candidate receipt must continue to have false values for
scientific_verification_performed, compiled_bundle_is_canonical,
claim_promotion, publication_authority and merge_authorized.

## 10. Return durable evidence and a parent summary

Return the immutable original failure reference; verified package digest;
original/repaired source manifests; a four-file unified patch and post-repair
source files; command logs and JUnit; negative-test results; old-to-new identity
map; source invariance checks; and the production six-file bundle if generated.
Use a fresh output archive with SHA256SUMS. Do not claim a sandbox file exists
unless the executing environment created or verified its actual path.

Write K2FER1_EXECUTION_RECEIPT.json and K2FER1_REVIEW.md in the run output,
not as new canonical science ledgers. Include this parent summary:

```yaml
k2fer1_result:
  observed_live_head: null
  repair_base_snapshot: a8d5417b3beae46e345392b5c2576c15be83a514
  original_failed_execution_snapshot: a0784f2a1ce1f4a3fe14195a5f169e4959bd8391
  original_failure_zip_sha256: 77329d5082a7c41c1977f7547fdefb1b6c2e57dde8de907aada560f95bfb112a
  original_failure_zip_verified: null
  source_method: null
  baseline_junit_verified: null
  baseline_rerun: null
  python_version: null
  package_versions: null
  modified_source_paths: []
  patch_sha256: null
  old_to_new_identities: []
  syntax_exit: null
  original_test_nodes_retained: null
  existing_and_focused_tests: null
  strict_tests: null
  negative_mutation_results: null
  required_skips: null
  strict_cli_executed: false
  strict_cli_exit: null
  six_file_bundle_created: false
  four_surface_id_counts: null
  bibliography_keys: null
  canonical_sorted_id_sha256: null
  structural_findings: null
  coverage: null
  source_unchanged_during_replay: null
  scientific_manuscript_changed: false
  theorem_pack_changed: false
  bibliography_bib_changed: false
  remote_repository_mutated: false
  k5_pdf_regenerated: false
  canonical_claims: 30
  candidate_claims: 40
  cas_executed: false
  publication_authorized: false
  overall: null
```

Choose the terminal from actual observations:
REPAIRED_AND_MATERIALISED_WITH_STRUCTURAL_FINDINGS,
REPAIRED_AND_MATERIALISED_NO_STRUCTURAL_FINDINGS,
REPAIR_TEST_FAILED, COMPILER_EXECUTION_FAILED, SOURCE_DRIFT,
PACKAGE_INTEGRITY_FAILED, SOURCE_ACQUISITION_BLOCKED or RUNTIME_UNAVAILABLE.
A clean materialisation is still a source candidate, not a claim release.

## 11. Parent provenance for this handoff

The parent freshly read PR #449 at a8d5417b..., the current citation lines,
the entire K1R test file, the legacy input pins and strict helper pin. It did
not extract the owner's failure ZIP or run tests. Its shell and independent
Python attempts both returned ClientError before execution. It made no new
GitHub Actions rerun or CAS evaluation. Three paragraphs explaining the repair
and evidence boundaries received zero issues in Academic Writing Toolkit's
paragraph-logic check; that check did not validate code or mathematics.

No operational source repair is applied by adding this handoff. The consuming
decision is the next work execution of the known failed K2FE path. Preserve
the original failure and K5 completion rather than scheduling either as an
unperformed historical task.
