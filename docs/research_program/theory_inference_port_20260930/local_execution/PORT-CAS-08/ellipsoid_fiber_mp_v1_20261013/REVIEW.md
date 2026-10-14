# P08-A — independent review (ellipsoid fibre, Moore–Penrose)

Reviewer: a fresh-context, read-only subagent. Requested runtime was gpt-6-astra/ultra (unavailable); observed runtime was claude-opus-5-5. The reviewer is not the author.

**Verdict: PASS_WITH_NOTES. There is no blocking finding.**

## Results per target

| Target | Result |
|---|---|
| `compatible_iff` | Exact range test A(Xb) = b, with no tolerance. |
| `z0_in_rowspace` | Genuine witness w = (XᵀX)b, using X = Aᵀ(XᵀX), which is derived from the Penrose conditions. |
| `solution_decomposition` | Both directions are proved under compatibility. |
| `pythagoras_fiber` | Proved; `min_norm` is proved with rigidity stated as an iff. |
| `fiber_branches` (η>1, η=1) | Literal fibre `{z | Az = b ∧ z·z ≤ 1}`. η>1 gives ∅. η=1 gives {z0}, proved directly from rigidity rather than from the interior formula. |
| `fiber_branches` (η<1) | The kernel ball with squared radius 1−η. `fiber_eq_kernel_ball` holds for every η. |
| `incompatible_empty` | A genuinely separate emptiness cause: it needs neither X nor η. |
| Rank branches | `rank_zero` holds for every MP X. Full column rank gives ker A = 0 and a unique solution. |
| Mixed-rank witness | A₀ = diag(1,0) separates the two emptiness causes. With b = (0,1), η = 0, yet the fibre is empty because b is incompatible. |

## Other checks

- **No circularity.** Every hypothesis is necessary, and none restates its conclusion.
- **Receipts.**
  - Source sha256 is `a69fb0ad3f476a0ece48dd77d9eca10930c8f8ee989c44f2f1e3bc5ff906c8ab`.
  - compile_01 exited 1; the failed attempt is kept.
  - compile_02 and compile_03 exited 0.
  - The G08A import hashes are unchanged.
- **Axioms.** All 22 declarations use only propext, Classical.choice and Quot.sound. There is no float or tolerance cutoff.
- **Independent rebuild.** The olean `e66a6182…` is bit-identical to the author's, and the audit stdout is identical. The reviewer's extra probes also pass:
  - `Fib` is definitionally the literal fibre set (`rfl`).
  - An MP matrix exists for any A, and z0 does not depend on which one is chosen.
  - A concrete η = 1 singleton.
  - A non-degenerate η < 1 ball.
  - rank A₀ = 1.

## Notes (optional)

- **N1:** rank A₀ = 1 is not stated in the candidate.
- **N2:** There are no fibre-set corollaries for the concrete witnesses, and no concrete η = 1 witness.
- **N3:** The radius is stated in squared form only, so prose should say "squared radius".
- **N4:** The full-row-rank branch is not stated here; G08-A provides `full_row_rank_branch`.

## Not proved

- The image factor sqrt(1−η)·P L N, i.e. the ellipsoid quotient image.
- Any link to numerical SVD. PORT_MAP F4 stands: the Python EMPTY_SET is a floating-point conclusion.
- The concrete substitution A = BL, b = y − Bc.
- Physical units.
- The full-row-rank branch.
- Full PORT-CAS-08.
- Historical four-axis acceptance.
- Scientific admission (HOLD).
