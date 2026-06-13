# Future Solver Interface Review

Review the package for native-solver handoff readiness without treating the
future solver as present.

Required checks:

- Native adapter and atlas references are schema/provenance surfaces only.
- External-transfer paths remain side-by-side with future native paths.
- No current artifact is labeled as native output.
- AtlasEntryLite and transfer registry materials preserve input domains,
  transfer source, calibration status, and caveats.
- The native morphology atlas is absent, so morphology compatibility and
  geometry/family claims remain blocked.

Return exact missing schema fields or provenance gaps.
