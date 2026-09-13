# Sage/Singular bounded axis detail

Profile observed: `SageMath 10.9` at `/usr/local/bin/sage` and
`Singular 4.3.2` at the required case-sensitive path `/usr/bin/Singular`.
The runner invokes both engines for every proposition. It is an exact algebra
attempt, and is not an authenticated launch or an admission decision.

| Proposition | Exact computation performed | Full-contract status |
|---|---|---|
| D1 | Sage expands `[-k,1] C [-k,1]^T` for symbolic scalar blocks and compares it with the stated cross-block formula; Singular is invoked on the exact zero normal form. | `INCONCLUSIVE`: no arbitrary block-dimension pullback proof and no finite-second-moment probability-space proof. |
| D3 | Sage checks a two-step scalar recursion in both directions and the determinant of its triangular transform; Singular is invoked on an exact zero normal form. | `INCONCLUSIVE`: no arbitrary finite block recursion, kernel/surjectivity proof, or transformed full-law/support proof. |
| D2 | Sage checks the symbolic rank-one diagonal score identity `lambda*(z1^2/lambda)=z1^2`; Singular is invoked on an exact zero normal form. | `INCONCLUSIVE`: this does not establish Gaussian pushforward, support, chi-square distribution, rank-zero, or off-support assertions in general. |
| D4 | Sage checks the scalar nonsingular Schur-complement identity after clearing the denominator; Singular is invoked on an exact zero normal form. | `INCONCLUSIVE`: no pseudoinverse range proof, singular conditioning proof, conditional Gaussian law, independence proof, or successive-innovation proof. |

Every runner check is therefore `false`. This records absent full obligations,
not a counterexample to any D1--D4 statement. The empty
`domain_assumption_diff` means the runner does not substitute a narrowed theorem
for the contract; its separate detail identifies the unproved scope.

The command for parent-owned `run-adjudicate` integration is:

```text
/usr/local/bin/sage -python .agent-harness/runs/R9-THEORY-20260914/artifacts/depth_sage_singular/depth_sage_singular_runner.py D1
```

Replace `D1` with `D3`, `D2`, or `D4` for the matching contract. Use the
repository worktree as cwd and the contract limit of 180 seconds.
