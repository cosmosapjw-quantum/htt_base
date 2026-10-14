# Continuation state

This successor follows the active continuous-DAG rule: a completed scoped node
transitions to the next dependency-ready node after source identity, scoped
validation, and independent review. It is not a conversational stop signal.
A genuine missing input or authority is recorded as `HOLD`, then independent
ready work is selected; it is never converted to a pass.

Current state after the C01 review is `READY_TO_PUBLISH`, followed immediately
by dependency selection. This protocol does not alter frozen contracts,
historical adjudications, environment seals, or scientific claim status.
