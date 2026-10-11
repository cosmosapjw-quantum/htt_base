# CAS15 spectral-wrapper continuation protocol

## Observed control failure

The prior execution treated a completed bounded proof node as a conversational
terminal state.  That is not a mathematical blocker, and it conflicts with the
owner direction to continue through dependency-ready work.  No historical CAS
contract, adjudication, budget, or scientific status is changed by this note.

## State transition rule

For this successor, a node that has produced its scoped evidence transitions as
follows:

1. Freeze its source identity and run its scoped validation.
2. Dispatch the next dependency-ready proof or review node immediately; a
   completed node is not a stop condition.
3. If a node is genuinely blocked, preserve the first failure and exact missing
   lemma/input, then scan the remaining in-scope dependency graph for an
   independent ready node.  A blocked node is neither silently skipped nor
   converted into a pass.
4. End only when no in-scope executable node remains, or when an external
   authority/input is required.  Record that condition explicitly.

## Current transition

`ordered_witness` has supplied the ordered orthogonal diagonalization and
pairwise gap witness.  The active successor state is therefore
`INTEGRATION_RUNNING`: instantiate it against the existing CAS15 definitions,
compile the wrapper, then route the final candidate to a fresh independent
reviewer.  Publication remains conditional on that review and on final axiom
inspection.  Historical CAS15-C03 `CAS_CONFLICT` and scientific admission
`HOLD` remain unchanged.
