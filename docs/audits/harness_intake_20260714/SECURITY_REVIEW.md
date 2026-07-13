# GPT-5.6 physmath harness security review

## Verdict

PASS FOR ISOLATED VENDORING. Root extraction is rejected. The two upstream
packages are documentation/prompt harnesses with four small local Python tools;
they are not scientific solvers or transfer providers.

## Evidence

- Both ZIP CRC checks passed and their SHA-256 values match `receipt.json`.
- Normalized members contain no absolute or parent-traversal paths, backslash
  aliases, symlinks, encryption, duplicate/case-fold/NFC collisions, nested
  archives, suspicious compression ratios, binary payloads, or archive comments.
- Static inspection found no subprocess, socket, HTTP client, shell, or external
  write behavior. Initializers write only state files relative to their own
  package roots; validators are read-only.
- Both upstream validators passed in separate mode-0700 temporary roots. Python
  compilation passed after static inspection.

## Root collision finding

The coding archive conflicts with five tracked root files and the research
archive with four. Eleven paths collide across the two archives. Direct root
installation would therefore replace repository authority and is forbidden.
The exact upstream bytes are stored under separate immutable vendor roots;
their nested `.agents/skills` directories are not repo-active skills.

## Kill switches

Reject activation on checksum/version/license mismatch, unsafe path, unexpected
executable, network/subprocess behavior, root-file drift, upstream initializer
execution in the vendor tree, generic-skill promotion, or production claim-gate
weakening.

## Artifact status

- owner: COMMON
- implementation scope: common
- bundle kind: common_contract
- claim tier: diagnostic_only
- artifact mode: governance_diagnostic
- allowed use: external_audit
- transfer source: none
- sky support: not directional
- null/covariance status: not statistical
- workflow use: audit prompts and evidence templates
- forbidden use: scientific validation, native-transfer evidence, or family claim
