# Separate bounded fixture-representation repair

Read-only /root/gaia_covariance_bound_frame, requestedAstra/xhigh,
observedUNKNOWN, explicitly approves ONE new fixture-only repair. The earlier
configuration approval was exhausted; worker stopped and did not infer another
attempt from it. This is not controls PASS or final independent review.

controls_0337c2943c62 completedexit1 with11 byte-comparison failures after plain
np.concatenate in test_envelope.py:49. Integer byte order was reversed by
native-endian normalization while mask bytes remained unchanged. Production
FrozenReader uses np.frombuffer(...,dtype=DTYPE), not this concatenation.
The complete12-test unit is FAILED, irrespective of earlier successful checks.
Elapsed1.9815527310129255s remains charged; cumulative4.75330478393252/120.

Only test-helper change: assert every collected batch dtype==e.DTYPE and
itemsize==88 BEFORE concatenation; concatenate with
np.concatenate(collected,dtype=e.DTYPE,casting='no'). Preserve ALL existing
byte-equality, Astropy, NULL, malformed-input and numerical assertions. No
production parser/kernel/source/tolerance/runner/resource-limit changes.
Preserve both raw failed logs and exact code preimages.

NumPy primary semantics verified read-only by approver:
[byte-order normalization](https://numpy.org/doc/stable/user/byteswapping.html),
[explicit concatenate dtype/casting](https://numpy.org/doc/stable/reference/generated/numpy.concatenate.html),
and installed NumPy source. No new numerical diagnostic was executed for this
decision and no raw source catalogue was opened.

Authorize EXACTLYONE guarded controls closure via canonical .venv/bin/python -B
bounded_run.py controls. IFF the ENTIRE unit passes, proceed to the already
authorized FIRST/ONLY actual source pass. Any further failure stops for
interpretation. SAME cumulative120seconds, source one-pass and all original
acceptance/HOLD boundaries remain. No budget reset, excluded retry or physical
admission. Fresh separate independent scientific review remains required.
