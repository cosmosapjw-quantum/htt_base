# R2-01 independent review

Reviewer requested: `gpt-6-astra/ultra`; observed runtime: `UNKNOWN`. The reviewer was read-only and did not author the candidate.

Final candidate identities: `structured_inference.py` SHA256 `2e807f47e6cab377f1389beaca4d4e15b2b4386f4f7a53ea64343f19e12e4145`; `bulkflow_covariance.py` `5c517e494b75569bccc33a2664a92d15c460b47d5e0e273e7eec9a34960b763c`; `test_structured_inference.py` `fd3810997893545eaacb36fb6b19b0ca103818b564893c79809ece7fc14a0b0a`.

Verdict: **scoped PASS** for the guarded fixed-design Gaussian implementation. The initial reviewer found two blockers: a low-rank whitening mode lost to floating-point cancellation and nonfinite computed statistics accepted as finite-input likelihoods. The first repair still failed after a row permutation. The final candidate rejects unresolved extreme `D^-1/2 U` regimes before inference, independent of row ordering, and raises `ArithmeticError` on computed overflow. Raw first failures and repair logs are retained in `raw/`.

Independent closeout: 12 extreme cases in both row orders and whitening directions raised `ArithmeticError`; original overflow cases raised `ArithmeticError`; 120 tests passed. Across 27 accepted boundary cases and nine rejected cases, the largest reported whitening/precision/adjoint error was `7.46e-9`, and coefficient-covariance error was below `9e-16`. The guard restricts the accepted numerical domain but does not certify uniform forward accuracy. `1e-10` dense parity applies to the tested moderate-scale cases only.

The 38,053-row synthetic benchmark is an operator/memory check, not a CF4 fit. Actual product inference, source-specific selection, and broader scientific admission remain `HOLD`. The common suite's 22 missing-`MES_R7_SOURCE` setup errors are recorded in `raw/common_tests.log`; they are outside the R2-01 module tests.
