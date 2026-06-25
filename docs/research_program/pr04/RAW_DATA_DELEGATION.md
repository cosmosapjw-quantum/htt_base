# Raw-data and long-run delegation

This handoff intentionally does not download or analyse every raw data product.
The following are local-repository responsibilities:

- CF4 release download, fixed release binding, method/group/selection hierarchy;
- Planck PR4/NPIPE map and end-to-end simulation processing;
- constrained/posterior 3D velocity-field ensembles;
- expensive matched-mock replay and adaptive global calibration;
- light-cone/ray-tracing or validated transfer artifacts;
- new Rust solver development.

Every delegated ticket already contains inputs, entry point, outputs, PASS gate,
claim boundary and blocker code in `registries/local_tickets.json`.

A missing input is a valid terminal state. Use the blocker code and emit no
substitute estimate from compact, proxy or legacy products.
