# CAS15-C03 concrete least-squares / matrix continuation

Owner htt; transfer source none; scientific admission HOLD. New strength-based successor, preserving #497 historical CAS_CONFLICT and frozen contract. Real 3×3 matrices; symmetric M,Mhat; skew W and What; arbitrary Rhat; R=[M,W]; nonnegative epsR,epsM,Wstar with Frobenius noise and W bounds, induced Euclidean operator noise bound; perturbed spectral gap deltahat>0; genuine global skew least-squares minimizer. No exact-fit assumption.

| Proof obligation | Reuse / assumptions | Author ownership / tools | Completion evidence |
|---|---|---|---|
| Concrete Frobenius Hilbert space, skew subspace, arbitrary-data LS projection/contraction and residual identity | unchanged Projection.lean; #497 diagonal components | cas15_frobenius, Frobenius.lean + frobenius_logs; Lean pinned | exact concrete norm correspondence and kernel/axiom output |
| Mixed operator/Frobenius commutator estimate | symmetric DeltaM; genuine Euclidean operator norm | cas15_mixed, Mixed.lean + mixed_logs; Lean | derive bound rather than assume it |
| Arbitrary rotated coercivity; ordered eigenvalue matching and gap consequence | real symmetric spectral decomposition; positive gap only for inverse | cas15_spectral, Spectral.lean + spectral_logs; Lean plus analytical proof as needed | distinguish DERIVED from FORMALLY_CHECKED scope |
| Final synthesis and bound epsR+2epsM Wstar over deltahat | preceding explicit lemmas, no target premises | root owns build.py and final task docs; Lean | compile affected sources and print axioms; retain first failures |
| Separate independent review | final theorem/dependency/source identities first; logs afterward | fresh read-only gpt-6-astra/ultra requested after author completion | scoped review complete, no blocking findings; two P3 record findings closed before publication |

Requested authors: gpt-6-sol/high in fresh bounded contexts; observed Frobenius and mixed settings confirmed by matching turn_context, spectral settings confirmed by matching turn_context; exact sessions/turns in RESULT.md. Authors may share interfaces, and that sharing is not independent rediscovery. Root owns task plan/build/return/result documents; authors own disjoint proof/log/notes files. Existing Projection.lean and historical raw failures stay unchanged. No four-axis validator execution or scientific admission is inferred.
