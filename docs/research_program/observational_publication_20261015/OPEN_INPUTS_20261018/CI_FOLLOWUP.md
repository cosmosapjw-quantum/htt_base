# Post-publication CI follow-up

This is a separate, narrow repair after the reviewed research package was published at `e66d7c2e4819553d83c0778387db8df4e9ab3c76` in draft PR #561. The original 48 research/review files remain byte-for-byte unchanged.

## Observed failure

[Repository integrity run 39119644613](https://github.com/cosmosapjw-quantum/htt_base/actions/runs/39119644613), job 117652436291:

- Repository/harness contracts: **145 passed, 3 skipped**. The earlier fragment synchronization repair is now confirmed by the real CI suite.
- Architecture boundary tests: **5 passed**.
- `project_runtime.py check`: **PASS**.
- Runtime tests: **5 passed, 1 failed**.
- Rust compile and Python package smoke: **SUCCESS**.

The newly reached runtime test `test_versioned_profiles_pin_current_model_and_forbid_nested_spawn` unconditionally read `data["model"]`, then restricted it to `gpt-6-sol` / `gpt-6-luna`. It failed with `KeyError: 'model'`. This failure was previously masked by the earlier repository-contract failure.

## Source evidence and scope

The existing versioned directory contains 23 TOML assets: five model-free domain guidance files, ordinary model-pinned profiles, and preserved CUH-G-era profiles including Astra and older model names. For example, `physics-stat-auditor.toml` was restored by the audit snapshot commit `6365e36d0ccc6acddb7f6909aacea8d766c0fc4a`; it was not introduced by this research PR.

Current authoritative instructions explicitly require supported model/effort selection at native dispatch and distinguish historical CUH-G material from current launch instructions:

- `AGENTS.md`, current-native-execution section.
- `docs/harness/CURRENT_CODEX_RUNTIME.md`, blob `eb1b52db86a7af6302d5bc3e45779bdd54d34423`.
- `.codex/config.toml`: `max_threads = 4`, `max_depth = 1`.
- The original runtime test blob is `fa21a544f9e609cc38a1ec9f7434a1a5f6a205a6`.

No model availability is inferred from an archived TOML. No historical model is newly authorized for dispatch. No policy, runtime implementation, hook, profile, scientific criterion or model configuration is changed.

## Targeted test repair

Replace only the stale final test; preserve the first five runtime tests:

1. Parse every tracked agent TOML and reject malformed explicit model overrides or invalid effort values. Model-free task guidance is valid.
2. Check the actual project configuration's four-thread / depth-one constraints using exact integers, rejecting booleans and floats.
3. Reject a role that explicitly enables nested agents or supplies a nested-agent table without disabling children. Any explicit role limits must be integers with depth 0–1 and threads 1–4.
4. Include negative cases for empty/non-string/leading or embedded whitespace model overrides, unsupported effort labels, nested child enablement, greater thread count/depth, negative/zero invalid role bounds and boolean/float limits.

This asset-shape test does not certify an installed model catalog or observed dispatch settings; those remain native-session obligations.

## Validation boundary

The local execution transport was unavailable for this follow-up. Source comparison confirms the first five tests are unchanged. Execution is delegated to the repository's existing GitHub Actions workflow, not reported as a local test run. The exact follow-up commit and its CI result are reported in PR #561. The original independent scientific review remains scoped to the earlier 48 files; the same reviewer assessed this concrete post-publication repair separately below.

## Scoped independent follow-up review

Same independent reviewer; requested gpt-6-astra/xhigh, observed backend settings UNKNOWN. This is static review, distinct from the original research review.

Verdict: **PASS_STATIC_PATCH_REVIEW_CI_PENDING**, exact test blob `56c83542faf29ac074118641130adcdce11e64d7`.

The reviewer read the complete candidate through GitHub and compared the 4,736-character unchanged prefix against original blob `fa21a544f9e609cc38a1ec9f7434a1a5f6a205a6`. All first five tests and setup are unchanged. The three positive cases and 22 negative cases cover the concrete stale-model assumption and newly identified boolean/float, role-cap and embedded-whitespace bypasses. No remaining blocking finding in this narrow repair. The seven-test file remains execution-pending until the new CI run passes; no local execution is claimed.
