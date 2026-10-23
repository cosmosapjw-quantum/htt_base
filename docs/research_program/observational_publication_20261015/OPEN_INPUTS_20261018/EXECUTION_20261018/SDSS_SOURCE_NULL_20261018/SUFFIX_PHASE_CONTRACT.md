# Separately frozen SDSS remaining-suffix allocation

Explicit Astra decision /root/pantheon_source_response_review, requested
gpt-6-astra/xhigh, observedUNKNOWN; same public-source research authority/task,
not an automatic retry loop. Executor requestedgpt-6.1-sol/high, observedUNKNOWN.
Original source CONTRACT.md/source semantics/600s science cap unchanged.

## Observed terminal failure, preserved allocation

metadata_phase1 of original task1792327821626160108 is CLOSED/FAILED_PRESERVED,
3/3ROOTbulkrequests consumed. Failed execution outsideGit:
recovery.1792327821626160108.metadata_phase1.execution.json
SHA937817522ef9c2b2cdcd76ac0a55511448863bb76f48abd06ff589295ebe3f1a.
Range0SHORT_RESPONSE_BODY aftercorrect206; range1controllerSIGTERM15 aftersibling
failure,CANCELLED_PRESERVED notsecondserverfailure; range2VALIDATED. Controller
999286/children1001635/1001651/1001653 allabsent. Old markers/preseals/receipts/
codepreimages remain immutable. Do not invoke the consumed controller again.

Currentexternalroot /mnt/extdrive/workdir/htt_open_data/sdss_source_null_20261018/:
part0originalstart0,length4294967296,retained2591793744,missing1703173552;
part1start4294967296,length4294967296,retained2105540608,missing2189426688;
part2start8589934592,length2053284129,complete2053284129,
SHA43f62633765b085d50359bbd2a91589c99bec8e15f73048471b21629dc5cc1a5.
Totalretained6750618481;remaining3892600240. Reuse part2 without new requests.

## New bounded suffix phase

Same official direct HTTPS endpoint from CONTRACT.md, record6824749, literalAPI
version1.1.0, total10643218721, MD5 9ba3e8876f6f08a2af00d30cbf1c6cd9.
One NEWexclusive phase marker linked to terminalfailure and preservedreceipts;
old3requestallocation not reopened/relabelled/increased. Newallocation maximum
16bulkrequests (7forpart0,9forpart1), totalcumulativeobservedROOTceiling19;
unknownhistorical/earlierfaultyfixtureGETs/bytes remainUNKNOWN separately.

BEFOREnetwork, exclusively lock/sealcurrentcompleteSHA256,size,fileidentity of
two retained prefixes; verify completedpart2+receiptidentity. Any unexpected
drift stops. Parentlaunchrecheckssealedstate; preventconcurrentwriters.
Within each unfinishedpart originalstartB,currentverifiedprefixP,lengthL=4294967296:
overlap65536; new=min(268369920,L-P);
requeststart=B+P-65536; requestend=B+P+new-1.
Maximum256MiBRESPONSEINCLUDINGoverlap. Verify ALLoverlapbytes beforefirstappend.
Strictsequentialwithinpart; maximum2concurrentparts/streams. Distinctcreateonly
perrequest/phase evidence and durable cumulative accounting, no overwrite/retry.

Hardlimits:16newbulkrequests/3893648816bulkresponse-bodybytes (3892600240novel+
1048576overlap); ONEfreshofficialmetadataresponse<=1MiB; phase7200s;
eachrequest1200s/socketinactivity120s. Count attempts/actualusage alongside
historicalusage, never reset. DirectHTTPS/206/identityencoding/exactContentRange/
ContentLength/total mandatory; no redirects/alternativeURLs/retries; reject200
beforebody. Perrequestdeadlinemustcoverbody read, notonlysocketinactivity.
Shortbody/overlapmismatch/identitydrift/timeout/cap/unexpectedresponse immediately
failsphase, stopssibling and preservesallbytes. Anothercontinuation needs another
explicitdecision, not auto-loop. Sourceinvalidity is not inferred from transport.

Remainingnovelbytes+2GiBfree beforetransfer; TOTAL+2GiBfree beforeassembly.
Completednewparts getwholepartSHA/completionreceipts withpreservedprefixchecks;
reusepart2; unchangedassembly/wholeMD5/index/header workflow only afterallparts
validated. No extractionbeforewholearchiveidentity. StopSTAGE1_RETURN_TO_ASTRA
for actual-field approval, NOautomaticmockscience.

LowerSol implements newscopedfiles andofflinefailure-boundarytests only,
preservingoldsourcefiles. Focused freshindependenttransportreview beforeparent
ONLYlaunch, observedcommand/codeidentities/PIDs/durablelogs. No worker-owned
longsourcejob; no nestedagents/clone/worktree/ODE/native/mainmerge/submission.
ScientificexecutionNOT_STARTED; sharedledger2.2925612370017916/600 unchanged.
