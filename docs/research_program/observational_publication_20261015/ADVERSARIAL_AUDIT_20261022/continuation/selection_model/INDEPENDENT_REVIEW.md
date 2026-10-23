# A22-06 independent review and targeted repair closeout

Separate read-only native reviewer `/root/a22_selection_review`, requested
Astra/xhigh, observed UNKNOWN; base d256ed4669b1ded62fa0db606929af108160ccf6.
PASS_SCOPED_COMPONENT_REVIEW after one review and one targeted closeout.

Initial findings retained:
1. Absolute quadrature tolerance accepted inaccurate tiny Gaussian tails: cuts
[10,-30], independent standard normals, returned2.618362323602611e-23 rather than
7.61985302416047e-24 (factor3.436237307), with permutation failure. CLOSED by exact
independent/one-cut evaluation, mode-scaled relative quadrature and swapped-cut
agreement/rejection. No floor or tolerance relaxation. Independent erfc references
now agree within1.7e-14relative; four correlated tails agree with65-digit reference
within3.4e-14. Five focused tests pass.
2. Report called the full pi_or*F_or law executable although code evaluated only
mark likelihood and pooled completion. CLOSED by narrowing the execution claim;
conditional distance factors remain explicitly defined but unimplemented.

Independent actual-data reconstruction confirms all8counts,274present/354missing,
728strict breakpoints, all input hashes,983630new source bytes,8885/11102rows and
12/23membership differences. RESULT and PNG stayed byte-identical across repair.
Figure and source semantics checked. Physical selection/calibration/velocity and
true-distance inference remain open. No original-node promotion/four-axis CAS.

Final reviewed hashes:

```json
{
  "cohort.py": "e3c9e8bf9f111dd30f1ad3d7fcfede1ee21704c36d4abde79961609c54bd7f28",
  "test_cohort.py": "14075004224b40efe2cffafbc50ca75d7c9e29342826fceff34a2820b87badff",
  "REPORT.md": "f99d1def61d65daca1acd5b8fa10bc3e5019e5caabecb8aa263ad1023554d566",
  "RESULT.json": "4fb2f100764ae5539a6b24ca89dc389ace9eb6a56e83be1b4401d6a20b6880b8",
  "SELECTION.png": "b2756965f53e6d79ec6ec64a301b23e0b08d3f6b93df89f7c364514425444d93"
}
```
