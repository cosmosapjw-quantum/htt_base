# OBS-01 source-weight guard follow-up

Decision returned by independent read-only Astra reviewer: `SCOPED_PASS_OBS01_SOURCE_WEIGHT_GUARD`. This is a controller transcription of the reviewer session message, not a raw tool log. Requested reviewer: `gpt-6-astra/xhigh`; observed runtime identity: `UNKNOWN`. The author used a requested `gpt-5.6-terra/medium` profile; observed identity: `UNKNOWN`.

The reviewer first reproduced a defect in the prior candidate: nonfinite or negative source weights could silently change the likelihood's active sample and return a finite number. The first repair revealed a precision division underflow when factors 1e123 and 1e-123 should cancel, shifting log likelihood by 0.03581911123365. These are retained here as reviewer-reported counterexamples; no separate raw reproducer file was captured or manufactured.

Final reviewed SHA-256: `htt/src/common/bulkflow_likelihood.py` `69b3b33976639211f1390bc7329e33636632819cd7829a36e4ffa6188de07b57`; `htt/src/common/test_bulkflow_likelihood.py` `1d19b4128ae5e63241049ded6a7f0a79e2931d0f726bde5d2b1afdd645c95a59`.

The author ran 47 likelihood and 37 estimator tests, both passing. The independent reviewer ran the focused selection (21 passed, 26 deselected, exit 0) and direct checks: 16 invalid-weight cases reject; four exact-zero cases retain the correct five-row normalized likelihood; survey scale controls retain six rows; reciprocal precision factors now give the same 1e-200 variance and exactly zero log-likelihood shift. The reviewed repair validates each source array before masking, uses separate positive predicates for activity, and divides precision by the combined factor. This closes the reproduced shared weight-contract defect; it is not a scientific admission.
