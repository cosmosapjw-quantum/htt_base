# PR-304 external trusted-launcher contract

This candidate does not contain an authorization trust root or an execution
launcher. Candidate-local code, tests, registry rows, and public keys are
non-authoritative diagnostic inputs.

The only future authority-use boundary is an independently installed,
root-owned launcher at `/usr/local/libexec/htt-auth-launcher`. Its trust anchor
must be provisioned outside the repository at
`/etc/htt/trust/root_authority_ed25519.pub`, with its reviewed fingerprint at
`/etc/htt/trust/root_authority_ed25519.pub.sha256`. Neither path is
caller-selectable.

Before any later transaction may start, that launcher must independently:

1. inspect the exact candidate commit and tree with a trusted Git-object
   reader and a scrubbed environment;
2. verify an externally stored detached Ed25519 signature over the registry
   blob hash, candidate commit, candidate tree, and authorization domain;
3. verify the human receipt and its exact lane admission, model contract,
   runtime environment, computed response-rank, normalization, and execution
   plan bindings;
4. acquire the output lock, atomically consume the nonce, write and fsync the
   start receipt, and only then start the process that may open observed data.

The tracked `human_authority_registry.signature.json` is a pending schema
template, not a signature or trust anchor. Embedding a real signature that
binds the containing candidate inside that same candidate would be recursive
and is forbidden. The detached root signature and private key remain outside
repository and agent access.

PR-304 does not implement these privileged launcher actions. Therefore it
cannot emit `READY_TO_START_SAMPLER`, consume a nonce, or open observed data.
Those operations remain blocked pending the separate PR-305 transaction and
external deployment review.
