# Targeted exact-factor metadata closeout: HOLD

The single authorized check stopped at reviewer check.py:148 before deriving the new exact mask. I introduced an uncontracted int64 requirement for all index arrays; nonreference_channel is signed int8 in both the immutable original and repaired factors. Header-only inspection confirms the same dtype and shape (35019,) in both files. This is a reviewer implementation error, not evidence of a candidate scientific defect.

Before stopping, the checker verified all bound initial hashes, controller identities and output-path binding, every unaffected array dtype/shape/raw byte, every unchanged RESULT value (including float bits), current factor hash/size, and legacy mask byte preservation. The first failed review's pre-line161 value/response evidence is retained, but neither failed whole check is relabelled PASS.

The new masks, full mismatch set/counts, remaining permutation and subnormal controls, and final source rehash remain unverified by this closeout. No producer, full contraction, B/N calculation or old reviewer was replayed. No retry occurred. No products are qualified and acceptance_met is false.

Observed overlapping times: API 4.042 s, exec host 3.500494503 s, kernel 1.69 s, outer monotonic after receipt fsync 1.534654419 s. Child peak RSS was 40464 KiB; polled combined RSS was 60194816 bytes. The root must settle the started failed check once under the existing account; numerical admission and original physical gates remain pending.

The minimal checker correction is to accept the preserved integer channel dtype with existing shape/range checks. It requires a newly explicit bounded continuation decision within remaining original limits; no candidate mutation is needed. Raw stderr, checker, receipt, input and dtype headers are preserved here.
