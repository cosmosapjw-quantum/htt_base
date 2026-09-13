# Lean execution receipt

Pinned toolchain observed: Lean 4.31.0, commit
`68218e876d2a38b1985b8590fff244a83c321783`; Lake `5.0.0-src+68218e8`.

The first raw-log redirection used `formal/.agent-harness/...` by mistake and
therefore failed before the runner started with `No such file or directory`.
That empty accidental directory was removed exactly, and the assignment-owned
raw-log directory was then used.

In the first actual engine executions for D1 and D3, Lean reported that
`AddGroup` is not available in the core-only project. The one permitted
targeted repair replaced it with a named `AddSubCancel` class. The repaired D1
and D3 executions still failed: the source needs the additional cancellation
law `residual + transport initial - transport initial = residual`. The cap
forbids another repair.

D2 and D4 were then executed, in the required order after D1/D3. They reached
the same unresolved source goal and did not emit contract payloads. All four
actual runner invocations exited 1 within the 180-second limit. Their stdout
is retained under `raw_logs/`; each stderr file is present and empty.

The strict registered-result validator accepted `results/depth_lean.json`, and
`cas_gate.py check-axis` accepted each stored D1--D4 axis envelope as an
inconclusive stored receipt. Neither validation recompiles the Lean source or
promotes any claim.
