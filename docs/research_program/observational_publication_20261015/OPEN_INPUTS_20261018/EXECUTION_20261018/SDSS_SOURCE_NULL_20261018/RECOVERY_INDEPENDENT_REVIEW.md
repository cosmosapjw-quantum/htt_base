# Scoped transport review and execution checkpoint

Owner: obsstat; scope: append-only official SDSS archive acquisition, not source
science or original DAG admission. Claim tier C0, transfer source none.

Code author `/root/sdss_transport_recovery` requested `gpt-6.1-sol/high`;
independent read-only reviewer `/root/sdss_recovery_review` requested
`gpt-6-astra/xhigh`. Observed runtime identities remain UNKNOWN. The parent
launches Python data jobs; those jobs have no model identity.

The same fresh reviewer found and closed two concrete defects: automatic HTTP
redirects violated the bounded direct-request contract, and HTTPError lost raw
status/header evidence. The repaired direct opener rejects redirects without a
second request and records response metadata before rejection. Its corrected
offline suite passed 22 tests. The first faulty test fixture did not establish
absence of external GETs; count and bytes remain UNKNOWN, with its raw failure
preserved. Do not infer zero historical GETs from later offline tests.

The first parent-owned attempt `1792327821626160108`, session64752, failed before
bulk launch because the validator expected `v1.1.0` instead of the saved official
API literal `1.1.0`. Record6824749, size10643218721 and MD5
9ba3e8876f6f08a2af00d30cbf1c6cd9 matched. Raw metadata, failed execution, original
marker, code preimages and all retained source prefixes remain unchanged.

The reviewer approved one exact-literal repair and one linked `metadata_phase1`
of that same logical attempt. Independent closeout: **33/33 offline tests PASS**,
real sockets and subprocess launches prohibited. Actual saved-history read-only
guards passed. Wrong version/record/size/checksum, nonempty child history,
range/alternate execution artifacts, live old PID and a consumed phase are
rejected. Exclusive phase marking precedes network; no generic retry is allowed.

Exact reviewed SHA256 identities:

|Artifact|SHA256|
|---|---|
|RECOVERY_PRESEAL_FINAL.json|5ead33fef7cbc47c8d82aeee31571e8086d3800825a094920d65fe7491d51a95|
|METADATA_PHASE_APPROVAL_ADDENDUM.md|7f7e6f154d38e6fb6e0711bd9df0711233f1c1ef6c0bdc80c932475c20507b66|
|root_launcher.py|e786532fc69ccf737fb677975a8d2183bca91673e791f477a3a9887a1c7879d8|
|resume_acquisition.py|b50fc0af995c68d835033e831430c910aae9942aac438939582bf32c878dcd0a|

Parent launch at HEAD db8ce0b88af7c4e4cac35e87a4871694d9b7a9c0:
tool session58969, controllerPID999286; actual childPIDs1001635/1001651/1001653
were observed running after retained-prefix guards and fresh metadata validation.
These are a historical launch observation, not an assertion of present liveness.
Durable controller log:
`/mnt/extdrive/workdir/htt_open_data/sdss_source_null_20261018/recovery.controller.1792328704648347017.log`.
Phase artifacts use namespace `recovery.1792327821626160108.metadata_phase1` in
that external directory. Cumulative ROOT bulk ceiling is three; three worker
processes launched in this phase, with zero preceding ROOT bulk workers. Actual
HTTP results must be read from their response/completion receipts.

**SCOPED LAUNCH PASS only.** Archive completion/checksum and actual-header approval
remain pending at this checkpoint. Science is NOT_STARTED; its cumulative ledger
remains 0.3223955580033362 /600 seconds. No H02 coverage, CF4 joint law, scientific
node completion or submission readiness is established. Never invoke this
single-phase command again; monitor its existing session and durable receipts.
