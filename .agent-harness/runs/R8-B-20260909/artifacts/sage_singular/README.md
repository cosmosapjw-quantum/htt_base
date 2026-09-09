# SageMath + Singular O4 verification

Run from the worktree root:

```
/usr/local/bin/sage -python .agent-harness/runs/R8-B-20260909/artifacts/sage_singular/verify_o4.py
```

Both engines reduced 37 rank-two, 381 rank-three and 3 null-cone residuals exactly to zero. Sage uses Q(I) with I^2+1=0 and a multivariate polynomial ring; the external Singular program reconstructs unreduced formulas, rather than receiving Sage zeros. The standalone emitted `verify_o4.sing` is independently runnable with `/usr/bin/Singular -q <path>`.

Every Cartesian component and all six index/vector permutations are checked. Fixed divisions by 2,3,5,6 occur in characteristic zero; there is no variable denominator, localization, saturation, excluded amplitude or coincident-vector locus. Polynomial identity establishes the arbitrary real-vector statement by specialization; the null-cone coordinate is arbitrary complex and the dot product is bilinear without conjugation. The extension I can be mapped to either square root of -1.

The command checks current contract/source hashes and pinned engine versions. The first successful execution and a timed deterministic replay both exited zero; the second took 2.57 seconds. `execution_receipt.json` holds timestamps separately. Replay preserves checks.json, verify_o4.sing and both Singular transcript hashes. No random or floating fixtures are used.

Only the three contracted STF/null-cone identities are verified. Generic root isolation, complete MV existence/uniqueness, numerical conversion, statistical qualification and scientific admission remain outside this result. No production changes or sibling derivations/results were read. Common LLM authorship across axes is possible and does not create independent scientific admission.

Repository result schema accepts repository-relative files_read only; external policy/bootstrap files consulted are separately declared in external_files_read. No memory-derived mathematical premise or tool path was used.
