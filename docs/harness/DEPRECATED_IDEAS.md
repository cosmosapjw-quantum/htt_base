# Deprecated Ideas

Record why ideas were deprecated. Do not delete historical context silently.

## 2026-06-12 - PR-011 deprecated approaches

- Deprecated: defining a second `ArtifactManifest` schema in
  `common.artifact_manifest`; this would split ownership/scope/claim-tier
  semantics from `common.contracts`.
- Deprecated: treating filenames, captions, or old manuscript references as
  manifest provenance; this would reinterpret legacy figures instead of
  quarantining them.
- Deprecated: allowing a sidecar manifest to de-quarantine a different file
  than its `artifact_path`; sidecars must match the scanned artifact path.

## 2026-08-08 - PR-295 deprecated approaches

- Deprecated: exempting a production CAMB import from the external-code
  scanner; the oracle is physically outside the installable project.
- Deprecated: relying on package-data or manifest exclusions to remove a
  stale Python module from `build/lib`; the non-editable staging tree is
  refreshed under a path/symlink guard.
- Deprecated: treating any exception from an external oracle as tool
  unavailability; only exact top-level CAMB absence is a registered blocker.
- Deprecated: rewriting frozen audit manifests after source relocation;
  current consumers move forward and the PR delta binds old/new identities.
