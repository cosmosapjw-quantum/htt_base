# Actual source intake and authorized notation transition

Actual task: R32-06-P4-DESIGN; attempt 1. Agent: `/root/rc_2a504af3ea3221e2`. Packet: `2a504af3ea3221e2f1ecf03938a5b042296403afb7c07384eafef5847ec8c459`. Input identity: `sha256:263f8707d940df778ea5a6eeef1023cd7784fe5dac5ebe1be2795f0c6e4de450`. Runtime observation: UNKNOWN. Controller ACK was read at `/mnt/extdrive/workdir/htt_open_data/r35_publication_acceleration_controller/P4_ACTUAL_ACK_GO.json` before production writes.

Initial intake read `/mnt/extdrive/workdir/htt_open_data/r35_p4_p5_source_contract_intake/P4_BUILD_CONTRACT.md` and verified SHA-256 `92cf81863ce53eb9a0747e87ce8acf386c732ed8fa0876cec6c91c790b633056`. The source identity file verified as `f5640c1ec3c2af4c9c40a9e295de23c2897f89bae84180ebfaa88b0e91d22a12`, and all nine source files matched their recorded hashes and sizes. No source mismatch was present at intake.

After the initial read, the controller reported and authorized a notation-only source correction by the retained framer. The final contract hash is `cdc26625caf799110f58d101bcde3182134d77aa2e1f8b512112e5ade8aee309`. The changed text is exactly:

- Initial: `The scalar rate is h*m. STF rate tensor is h*S, S=sum s_a F_a.`
- Final: `The scalar rate is h_* m. STF rate tensor is h_* S, with h_*=v*/R* and S=sum s_a F_a.`

Verification read the actual final bytes, replaced that final string once by the initial string in memory, and recovered SHA-256 `92cf81863ce53eb9a0747e87ce8acf386c732ed8fa0876cec6c91c790b633056`. This establishes that there is no other byte difference. The source-identity JSON hash remains unchanged. The production literal contract copy was made after the external correction and matches the final hash byte for byte; no intermediate production file with the old bytes was overwritten.

Classification: explicitly authorized source-contract notation correction, not a change to response, normalization, proof, acceptance or model. The manuscript already binds h_* in (1) and uses h_*m and h_*S consistently. This transition preserves packet, task, attempt, input identity and accounting. It does not promote any scientific acceptance.

Author actions to this handoff: read current repository/runtime rules and selected packet; read the retained source locators; verify frozen identities and this exact transition; write science text/proofs, literal contract, builder handoff, claim map and research note. No historical producer, ODE/native solver, raw catalogue execution, new download or Git mutation was performed. An initial read-only Git branch/status/HEAD capture occurred before the no-Git reminder; it changed no files and no subsequent Git command was used.
