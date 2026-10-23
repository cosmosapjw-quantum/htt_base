# Gaia properties: blind-review targeted correction

**HOST-TRANSCRIBED REVIEW SUMMARY**, not a reviewer-authored file. Fresh blind reviewer `/root/r25_blind_gaia_properties` returned **HOLD** with two corrections. Requested/transport-selected `gpt-6-astra/xhigh`; observed runtime UNKNOWN. This transcription does not assert new independent execution, production, qualification, or scientific acceptance. Same-reviewer targeted closeout remains pending.

P2: Host flag3 means “No host galaxy detected.” Flag5 nonconvergence can occur with host_galaxy_detected True OR False; flag5/False is not intrinsically inconsistent. Flag6 is the doubtful nearby-source category, not necessarily nonconvergence. [Pipeline §7.1](https://arxiv.org/html/2206.14491v1#S7.SS1) supports this clarification. Retain raw categories, host-flag/boolean crosstabs, missingness and versioned table/pipeline ambiguity. Do not impose a flag-to-boolean implication. Future host1–2versus3 is unchanged.

P3: The actual capability describes **outputLimit50000rows** and **uploadLimit100000000bytes**. The previous upload_rows50000 label was wrong. Rename the fields without inventing an upload-row or download cap.

All nine field types and source-ID-only design were approved in the bounded contract review. Only the two specified corrections were requested. The host corrected the input, regenerated the frontier input SHA and updated the advisor-source note; the exact previous candidate is under runtime/r25/gaia_properties_first_candidate with hashes. No query, scientific run, controller state, acceptance, commit or push occurred in this correction.
