# Manuscript Rearchitecture Report

owner: COMMON
implementation_scope: manuscript
claim_tier: diagnostic_only
transfer_source: mixed_external_proxy_and_none
sky_support_status: mixed
null_mock_status: mixed_blocked_and_not_applicable
artifact_path: docs/generated/manuscript_rearchitecture_report.md
config_hash: sha256:a3d063cb43fe1ee01a4a078aee3981ab32810b3818e8fbaf44562f52ace496f2
input_hashes:
- docs/manuscript/main.tex:sha256:4acbf5d4c0dbf1d6ae6c829cb3c907a3368e206f7199b510b76cbcc9d71bb38a
- docs/manuscript/ch01_introduction.tex:sha256:e3b8e5f0026b688d8cf899c9cdaf73656b3f3794cbcf15ac72e30828e343df54
- docs/manuscript/ch03_framework.tex:sha256:6535bcfa1dc28b44faeac3685d6d8dad1a0d2951b418f3692e25c985ba3e472f
- docs/manuscript/ch07_results.tex:sha256:e0055a19b016a932f04c2c7ebc2b6d9bd6b60183750cb8291bf958ce5c4cec8c
- docs/manuscript/ch08_robustness.tex:sha256:68ecf9a6e9749169bda3913a64d40fddd178ce8b6753ea9ec2b95a7f87956467
- docs/manuscript/ch09_discussion.tex:sha256:3525f471dc97c763bbe2e3338cb98a1597550519b6d2807ffa17344c41781520
- docs/manuscript/ch10_future.tex:sha256:9ae640f38376bb183a00f4a66cba0afdecdee3fd06e4d346ebab15d1834b864a
- docs/manuscript/appendices.tex:sha256:3aaa77c82432e553cc6cb86285477f1eef788eefe2349391dc3a4da86d2bfa38
- docs/manuscript/references.bib:sha256:483b7d393c6ccc79d108ec96dec1b7ac2428cb2086b3f6c1b21942c69a399e92
- docs/manuscript/generated/theorem_extension_appendix_figures.tex:sha256:308ac808adce7e89de15b075e89a22adf7ad0b1d1fc570db2d42901fd10501f2
generating_command: Codex REV-R086 manuscript rearchitecture edit with focused pytest, LaTeX, PDF claim lint, and manuscript figure dry-run gates
git_commit_or_worktree_state: 23fa8f6+dirty
caveats:
- no native solver output
- no Bianchi family identification
- no geometry-detection claim
- no HTT evidence from theorem snippets
- not MIO posterior or truth-validation semantics
- legacy likelihood values remain transfer-conditional and rest-frame conditioned

## Narrative Order

1. formal no-go and identifiability: scalar evidence, low-ell scalar summaries, and x/Q/Pi/F/G_F diagnostics do not identify a geometry or family.
2. transfer-conditional rest-frame tilt-like diagnostic: legacy Bayes-factor surfaces are sensitivity/provenance records, not headline discoveries.
3. rank/null/prior theorem-backed local/global rest-frame program: the safe positive result is a pre-inference gate stack with finite mocks, channel-matched occupancy, data binding, rank tests, and observer-motion marginalization.
4. current diagnostic figures: figures remain in lanes allowed by their manifests and source JSON; paper-main use remains bounded.
5. theorem appendix: synthetic/manufactured theorem-helper figures are appendix-only and not HTT evidence, MIO certificates, native validation, or family evidence.
6. future native solver bridge: the native morphology atlas, transfer adapter, sky support, covariance/null calibration, and family-equivalence gates are future prerequisites only.

## File Mapping

| File | Rearchitecture role | Claim ceiling |
|---|---|---|
| `docs/manuscript/main.tex` | Adds title-page narrative-order guard. | diagnostic_only |
| `docs/manuscript/ch01_introduction.tex` | Adds safe-strong-results architecture section and removes early numeric Bayes-factor headline. | diagnostic_only |
| `docs/manuscript/ch03_framework.tex` | Elevates scalar-identifiability no-go as the formal claim ceiling. | diagnostic_only |
| `docs/manuscript/ch07_results.tex` | Demotes legacy Bayes factors to sensitivity/provenance records. | transfer_conditional |
| `docs/manuscript/ch08_robustness.tex` | Reframes robustness around gates rather than result strength. | diagnostic_only |
| `docs/manuscript/ch09_discussion.tex` | Leads with what survives the firewall before legacy evidence discussion. | diagnostic_only |
| `docs/manuscript/ch10_future.tex` | Stages future work around rank/null/prior gates and native-atlas prerequisites. | specified_future_interface |
| `docs/manuscript/appendices.tex` | Routes theorem figures to appendix-only diagnostic lane. | paper_appendix_conditioned |
| `docs/manuscript/references.bib` | Adds CRAG-verified redshift tomography, DESI DR1, DESI DR1 quasar, and grouped CF4 reconstruction references. | citation_context |

## CRAG Sources

- von Hausegger and Dalang, Phys. Rev. D 111, 123547 (2025), DOI `10.1103/PhysRevD.111.123547`.
- Official DESI DR1 documentation, `https://data.desi.lbl.gov/doc/releases/dr1/`.
- DESI DR1 quasar cosmological-principle analysis, arXiv `2606.00551`, A&A 708, A307 (2026), DOI `10.1051/0004-6361/202556955`.
- Grouped Cosmicflows-4 velocity reconstruction, DOI `10.1093/mnras/stad3433`.

## Blocked Claims

- no native solver output is generated or implied;
- no Bianchi family identification is made;
- no scalar x/Q/Pi/F/G_F surface is promoted to geometry evidence;
- no MIO diagnostic certificate is merged into HTT evidence;
- no external or proxy transfer result is labeled native;
- no theorem appendix figure is promoted beyond diagnostic appendix use.
