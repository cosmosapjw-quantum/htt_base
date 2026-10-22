# Independent R6/C9 review — 2026-10-22

Verdict: **SCOPED_PASS_C0**. No unresolved blocking finding in this candidate.
Reviewer: separate native `review_loop_20261022`, requested `gpt-6-astra/xhigh`,
observed runtime `UNKNOWN`; fresh bounded context, read-only, no implementation.
This record transcribes the reviewer's returned decision. Parent alone publishes.

Scope: normalized-selection derivation/consumer/sensitivity plot, two-redshift
source interpretation, legacy reuse, new source intake and operational handoff.
The review does not promote physical Q/Pi, H02/S02, PR3 L03, PR4 null coverage,
B02 atlas, historical four-axis CAS, or any original scientific acceptance.

## Findings closed in one targeted repair episode

| Finding | Repair and independently observed closeout |
|---|---|
| P1 tiny-reference-mass LP returned a false upper optimum | Use normalized mass coordinates, dual optimality checks and the exact box vertex. Counterexample upper now `0.6666666666888889`; ill-scaled coupled case fails explicitly. |
| P1 overflow/NaN normalization returned false finite bounds | Require finite positive normalization/transform and finite returned variables, objective and each residual. Exact `float.max` counterexample now raises `ArithmeticError`. |
| P2 unnormalized joint weights confused with normalized RN ratio | State `q/p=r/Z`, preserving state-dependent selection normalization inside the target kernel. A true-RN normalization example gives `[0.15,0.6]`. |
| P2 fractional per-atom event flags accepted | Enforce binary flags, with rejection regression; aggregate event masses may remain fractional. |
| P2 restart command selected zero resources | Explicit eight IDs and external root; reviewer plan produced eight resources with null byte caps. |

First failures, including the original numerical outputs, remain in
[selection/REPORT.md](selection/REPORT.md). No tolerance was relaxed to obtain PASS.

## Final candidate evidence

- Selection code SHA-256:
  `7a4ff7f7b393f23ba5a0ee17b8f7080ce340c221f0250322003e67319b5883b3`.
- Selection tests SHA-256:
  `60e166b62941750c7c0ff0f8ca4311ad65b7ffaa3f4d7419e8320414841133b4`.
- `.venv/bin/python -m pytest -q docs/research_program/observational_publication_20261015/RESEARCH_LOOP_20261022/selection/test_selection_bounds.py`:
  **12 passed**, exit 0. Reviewer separately confirmed both P1 cases and the RN example.
- Reviewer source verifier reproduced the retained-table/row-selection counts.
- Reviewer PR4 verifier exited 0 and exactly reproduced `data/pr4/VALIDATION.json`,
  including full T/Q/U checks and exact RIMO member identity/schema.
- Reviewer viewed the plot and matched final PNG/PDF/JSON hashes to its receipt.
- Eight newly acquired payloads total **1,241,866,173 bytes**, with no byte cap.
- Original `PUBLICATION_DAG.json` SHA-256 is unchanged:
  `bcdc21a55863657c0da478e541132e0490267be6a56759d642b39698d0b14890`.
  No status, acceptance or dependency changed in the continuation.

The reviewer checked the [Charnes–Cooper original](https://iiif.library.cmu.edu/file/Cooper_box00010_fld00009_bdl0001_doc0001/Cooper_box00010_fld00009_bdl0001_doc0001.pdf),
[Carr redshift conventions](https://arxiv.org/html/2112.01471),
[Brout SALT2/PV discussion](https://arxiv.org/html/2202.04077), and
[SciPy marginal conventions](https://docs.scipy.org/doc/scipy/reference/optimize.linprog-highs.html).
The positive denominator, compactness, strict-event logic, restricted sharpness
and unsupported target-mass bounds were consistent. The NPIPE Table 5 detail
about start-of-year 5 was retained from parent intake; the reviewer's independent
page request returned 403, so that detail is not independently web-confirmed here.

Remaining limits: input weight/support/event bounds are hypothetical; the physical
Q domain remains unresolved; extreme or ill-conditioned numerical inputs may be
rejected. Product/spectrum-window availability supplies neither a complete map
operator nor a calibrated null law. A descriptive PR4 comparison is a separate
next calculation requiring its own scoped review.

Applied skill context: physmath-research-loop 1.3.0 R6/C9 and POLICY_INTEGRATION;
repo physics-math-audit, claim-firewall, scientific-code-validation, xqpi-fg;
current AGENTS.md and CURRENT_CODEX_RUNTIME.md.
