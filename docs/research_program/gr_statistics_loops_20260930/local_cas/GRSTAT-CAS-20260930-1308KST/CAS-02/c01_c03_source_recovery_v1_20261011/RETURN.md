# G02-A local source recovery receipt

Status: `PARTIAL_LOCAL_RECOVERY`.

The exact local candidate `Cas02.lean` matches required SHA-256
`283f64377e49585c697c3cb51f04cacece79015b36fa3c8d4a8e2d640678b520`.
Its pinned-oracle compile and the byte-identical-prefix type/axiom inspection
both exited 0.  The eight inspected declarations depend only on `propext`,
`Classical.choice`, and `Quot.sound`; raw receipts are in this directory.
The executed packet is preserved byte-for-byte (SHA-256
`ab15ec7bd36850820858f9f7411adb521bcddec033622a25aaa9f84e95254e00`).
Because the first compile did not create an importable `Cas02.olean`, the
controller approved the recorded byte-identical-prefix inspection as a narrow
execution-mechanics deviation; it adds only `#check` and `#print axioms`.

This does not close full G02-A: the package additionally requires a remote
published source binding and C04 import/provenance linkage.  PR #498 is correctly
identified as C04 head `c0365da5789ee5de1cb11c47be827e577f86ca3d`, but no remote
publication mutation or C04 import integration was performed here.  The C04
import/provenance linkage remains open; this task does not re-review or alter
the separately reused prior C04 acceptance.  Historical four-axis adjudication
and scientific admission are not promoted.

Requested author: `gpt-6.1-sol/medium`; requested reviewer:
`gpt-6-astra/ultra`; observed runtimes: `UNKNOWN`.
