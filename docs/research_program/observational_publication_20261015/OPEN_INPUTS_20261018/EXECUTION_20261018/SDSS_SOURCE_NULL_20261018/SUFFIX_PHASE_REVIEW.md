# Focused independent suffix-transport review

SCOPED_PARENT_LAUNCH_PASS at HEAD2840975012db67f7a5cb0ef3b7148e262fb634d7.
Author /root/sdss_suffix_execute requestedgpt-6.1-sol/high; fresh read-only
reviewer /root/sdss_suffix_review requestedgpt-6-astra/xhigh. Observed runtimes
UNKNOWN. No reviewer source writes, network, production append or science.

Exact reviewed SHA256 bindings:

|Artifact|SHA256|
|---|---|
|chunked_suffix.py|9ec53f73c148d4392d5ff95de444c4386d7a0c6476171623af625a84feea66a7|
|test_chunked_suffix.py|7e40a870c00feb6ba7f26b5a0f1c4a4221f39b856eca4c6f4e0eba54d183c8c1|
|SUFFIX_PHASE_PRESEAL.json|91ae0d2fdf59a4cfbdbd962ad6c4e97f3bfdd001177a24cb6c048e25df580747|
|SUFFIX_PHASE_CONTRACT.md|4e0f100ccbeefaac39d6201cab8041fe8f2380a03bc720ca2b7cfe860e2b4f71|

One concrete launch-blocking framing finding was reproduced: HTTPResponse can
prioritize Transfer-Encoding over Content-Length, allowing more decoded body
than the accepted declaration. This was an offline contract counterexample,
NOT evidence that the actual Zenodo short-body failure involved that header.
New guards reject ANY present Transfer-Encoding before metadata or bulk body
reads, including empty/identity values; old frozen helpers are unchanged.
Author preserved the two old-code failing fixtures and original19test evidence;
final22/22offlinefixtures PASS. Reviewer independently checked chunked, empty,
identity and gzip values with lowercase headers. Same-reviewer closeout accepted
the targeted repair; no outstanding launch-blocking finding.

Pre-repair code/tests/preseal remain at *.pre_transfer_encoding. Final consuming
preseal differs only in the two code/test SHA fields; locked source identities,
historical receipts/contracts/science ledger are unchanged. Parent rehashes all
three retained sources under locks before network. New16request allocation is
distinct from exhausted/failed3request allocation, not a reset or reinterpretation.
Newbodycap3893648816bytes, one<=1MiBmetadata,256MiBresponsesincluding64KiBoverlap,
two streams/sequentialwithinpart,1200srequest/7200sphase; noautomaticretry.
Completedpart2 is reused. All failures/partials retained; wholeMD5 then index/
actual-header inspection must stop before source science for Astra approval.

Parent actually launched the reviewed command in session72267, PID1257886.
This records a program-launch observation only: startup full-prefix guards
precede the new phase marker, metadata request and workers. Fresh metadata later
completed and workers1265557/1265585 were observed launched; their per-request
response receipts exist. Consult external
suffix.1792327821626160108.suffix_phase1.* evidence for subsequent actual
PIDs/requests/terminal status; never relaunch a consumed phase or infer liveness
from this note. Scientific execution remains NOT_STARTED, sharedledger
2.2925612370017916/600. This review does not validate the unseen whole archive
or admit H02/any original scientific node.
