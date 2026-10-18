# Independent review — SH0ES ladder finite reproduction

Decision: **SCOPED_REVIEW_PASS**, no actionable blocking finding or required
repair. This new event supersedes the frozen report/receipt's historical
`REVIEW_PENDING`; their numerical contents are unchanged.

Fresh read-only reviewer `/root/shoes_ladder_review` did not frame or implement
this unit. Requested `gpt-6-astra/xhigh`; observed runtime `UNKNOWN`. Author
requested `gpt-6.1-sol/high`; observed runtime `UNKNOWN`. Existing primary
checkout HEAD at execution/review was
`ad27f4cb5f84dfaccc322e53f2810ad29dc72276`.

Candidate bundle SHA256:
`64acca3225eec8f18b49f55bbcdce203f54d7fc99310f64096a58720c78f4f28`.
All 12 candidate file seals, six external source/input seals, README identity
and campaign code seals were verified. This later record is outside the frozen
candidate's file set.

The reviewer independently checked primary reanalysis section 2.1/Table 3 and
pinned official source text: composite 47-coordinate mapping, all 37 named
intervals, matrix orientation, eight selectors and retained dummy semantics
agree. The mapping is not an official Riess parameter dictionary.

QR covariance construction/SVD comparison are consistent. Cached full covariance
is positive definite; dummy variance is `9.999999717180685e-10` with zero
cross-covariance. Independent elementwise double-centering reproduced host
covariance within `6.94e-18`, rank 36 and preserved host-difference variances.
Cached parameters independently reproduced H0 `73.042819102` and delta-method
uncertainty `1.007147851`; formal source-model uncertainty is distinguished
from the published broader `1.04`.

Read-only validation using the existing `.venv`:

```
.venv/bin/python -m pytest -q -o addopts= docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/SH0ES_LADDER_20261018/test_ladder.py
```

Result: **7 passed / 5.03 s**, exit 0. Numerical campaign and D07 were not rerun.
PNG names, units, title and C0/joint-law caveats were inspected and legible;
forbidden-claim scan found no matches. Parent also inspected PNG/report.

Supported scope: conditional Gaussian ladder reproduction and host-difference
covariance only. Physical eta anchoring remains unestablished; Pantheon+/CF4
joint law remains UNKNOWN; original 42 acceptance states and D07's consumed
97/97 allocation are unchanged. No broader scientific admission, submission
readiness, main merge or journal submission. No targeted repair was needed.
