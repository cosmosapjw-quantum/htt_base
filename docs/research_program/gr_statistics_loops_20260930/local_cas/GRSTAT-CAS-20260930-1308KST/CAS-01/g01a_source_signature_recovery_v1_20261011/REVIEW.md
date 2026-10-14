# Independent review — G01-A source-signature recovery

Verdict: **PASS_SCOPED** for source-definition recovery only.

The fresh read-only reviewer requested `gpt-6-astra/ultra`; observed runtime is
`UNKNOWN`.  It first identified two P2 issues: the target was misnamed as an
M04 premise rather than `CAS07M05.JacobiPremises K L`, and the candidate did
not enumerate all of that structure's requirements.  The author corrected the
target, all structure fields, and the separate determinant-distance hypotheses.
The reviewer rechecked exactly those changes and reported no remaining blocking
finding.

Final reviewed identities:

| File | SHA-256 |
|---|---|
| `SOURCE_SIGNATURE_RECOVERY.md` | `b97b94b122661f05856ec2dc2a6e17a04037854fb7a84c1ab6c736eb04d094a7` |
| `RETURN.json` | `c7757f0f22f60a8c406cde88b4671e8406c909f6649e35eefeea42b7f7fb809b` |

The review explicitly retains `G01-A` as `NOT_PROVED` and scientific admission
as `HOLD`.  It did not rerun Lean and is not a review of the historical CAS07
candidate or a four-axis decision.
