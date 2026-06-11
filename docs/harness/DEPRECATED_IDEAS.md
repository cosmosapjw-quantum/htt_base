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
