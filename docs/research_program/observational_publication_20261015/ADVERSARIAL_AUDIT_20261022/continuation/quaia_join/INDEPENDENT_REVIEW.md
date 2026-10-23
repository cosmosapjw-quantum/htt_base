# A22-03 independent decision

Verdict **SCOPED_PASS** for the source join and transition to A22-05. Reviewer
`a22_join_review`, fresh context, read-only, requested `gpt-6-astra/xhigh`,
observed UNKNOWN. Parent records the returned decision. No original K03/K04
admission or physical astrometric likelihood follows.

The reviewer independently checked all755850 rows/34columns, exact integer IDs,
all Quaia astrometry, the692154 retained intersection rows, the63696 subset
records, covariance positivity and units, seven templates, ICRS/RING pixels and
the reported-redshift loss table. Source/derived hashes and the actual author
release-day notebook/code blobs matched. It viewed the figure and ran the tests.

One concrete replay finding was repaired: the collector contacted an expiring
UWS job before consuming an already valid local payload. Injecting an outage
gave `ConnectionError` despite retained data; the job destruction timestamp is
2026-10-25 17:34:53UTC. The new cache-first path avoids UWS and retains every raw
hash, QUERY_STATUS, schema, NULL/finite, exact-ID and covariance check.
The same reviewer targeted that change and independently observed **6 passed**,
exit0. No query or full Gaia campaign was replayed.

Final reviewed SHA256:

| Artifact | Identity |
|---|---|
| join.py | 3c38fe9b571aeffa3f82ac22de8ecc19233b5bced2e95cb751f3408d8345fba8 |
| supplement.py | 4a5c3264224baeba628d4b494055ebffa09bee76d6625173a54a5c588b580765 |
| test_join.py | 8e16c7aa871a59fd136f8713fbaadba2549bca85d095c63751847dcb7b5bd6ca |
| RESULT.json | ee5e420423337ed6b38ea3feb5b0d1312fd422de6c23878f837ad703a03a2431 |
| SUPPLEMENT_RESULT.json | ba9977d25f193fd37dc4e3a7373d97bf20c99d674f5d9da17d4c1a60ab146239 |
| Full joined NPZ | 4cd83b1e8bb9f71f89aacfc2db5daba87f9a79f2af8ccd2e7e94b0be57252dae |

Applied context: physmath-research-loop1.3.0 R6/C9 and integration/subagent
policies; repo observable-statistics, claim-firewall, scientific-code-validation;
current runtime, AGENTS and taskA22-03. Source-dependent selection and absent
cross-source covariance remain explicit.
