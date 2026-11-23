"""Join the R78 scientific DAG, R102 capabilities and reviewed R103 result bytes."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from .cross_routes import cross_routes


ROOT = Path(__file__).resolve().parents[2]
PAPER = Path('docs/research_program/observational_publication_20261015')
DAG = PAPER / 'R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json'
PUB = PAPER / 'PUBLICATION_DAG.json'
PRIOR = PAPER / 'R102_CF4_HOLDOUT_NATIVE_SOLVER_20261123/NODE60_EXECUTION.json'
CURRENT = PAPER / 'R103_SOLVER_SOURCE_CONTINUATION_20261123'
AUTHORITY = '90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11'
ORIGINAL = 'e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d'
PRIOR_HASH = '374002e191c3a00b8c76608b7680d9760c591002977f652185d4e4dcd6a7d0c0'
PARENT_HEAD = '664845022a9600ad925d6c1332143395aac5ed90'

# The earlier DAG's next_action is generic for a subset of the original 42.
# These are physical/local operations, never automatic promotions.
NEXT = {
    'E0': 'Reuse the PR533 dossier identity when citing its scoped claims.',
    'E1': 'Reuse the 35,970 selected IDs and 17 conditional covariance scenarios.',
    'E2': 'Use original Planck release IDs, masks and shared simulation indices when joining new data.',
    'E3': 'Reuse the PR066/PR521 samplewise function and its domain flags on new admitted draws.',
    'S04': 'Profile the admitted physical functional against its independent calibration law and report uncovered mass.',
    'S05': 'Compare the qualified S04 interval with an ordinary pushforward on the same held-out cohort.',
    'S06': 'Assemble the source-to-estimand evidence for S01–S05 and record the P1 submission decision.',
    'L04': 'Apply the frozen joint statistic to beam/mask/foreground-matched held-out realizations and rank by simulation ID.',
    'L05': 'Vary the registered nuisance family on the L04 joint ranks with shared-sky covariance.',
    'L06': 'Compare the L04–L05 null and assumptions with the release-specific Planck analysis.',
    'H04': 'Propagate independent zero points, upstream selection and correlated peculiar velocities through the selected group windows.',
    'H05': 'Compare published anisotropic and null CF4 models on the identical held-out survey window and covariance.',
    'H06': 'Summarize the calibrated H04/H05 alternatives and independent validation before deciding on P3.',
    'V04': 'Whiten local and history response columns in one observation operator; profile nuisances and report identified singular modes.',
    'V05': 'Inject each admissible local/global history on independent mocks; measure power and false-positive rate under the same prior family.',
    'V06': 'Report identified and degenerate transfer modes and the calibration evidence for P4.',
    'B02': 'Extend polarized native transfer across ICs, multipoles and stiffness; compare observable amplitudes with an independent solver on common conventions.',
    'B03': 'Project qualified T/E/B templates through measured beam, masks, foreground response and release-matched null.',
    'B04': 'Inject physically identified families and hold out amplitudes and orientations to measure confusion among equivalence classes.',
    'B05': 'Restrict the family claim to modes with calibrated injection recovery and an available Planck likelihood.',
    'K03': 'Crossmatch source IDs, redshifts, scanning-law and proper-motion covariance; repeat held-out sky patches in one frame.',
    'K04': 'Profile the common-congruence CF4 and tangential forward response; carry unconstrained eigenmodes as unbounded.',
    'K05': 'Estimate measured cross-probe covariance on overlapping objects and frames before a joint kinematic fit.',
    'K06': 'Enumerate physically identified combinations with independent error budgets and decide the P6 scope.',
    'SQ-CF4': 'Use same-group held-out predictions; obtain original targeting failures, independent zero-point errors and common-window peculiar-velocity covariance for physical calibration.',
    'SQ-GAIA': 'Join registered quasar IDs to redshift, AGN and scanning-law columns; validate 16D E/B fits on disjoint patches and a source-specific null.',
    'SQ-RADIO': 'Rerun source-level peak/integrated flux selection under Doppler/aberration and infer k,kappa jointly on held-out objects.',
    'SQ-FRAME': 'Attach the observer/source names, epochs and signed tetrad maps to each catalogue; validate boost and inverse on the same release.',
    'SQ-P1-ANCHOR': 'Join the original 274 row identities to an independent physical scale and selected-source null.',
    'SQ-CMB-NULL': 'Use distinct Commander signal/noise IDs; match observed beam, pixel and split/foreground transfer, then measure held-out statistic coverage.',
    'SQ-PHOTON-FLUX': 'Supply common-frame photon flux, energy density and independent matter momentum; evaluate moment positivity and Codazzi residual.',
    'SQ-LIE-FLUX': 'Source an independent normal-frame matter flux and shear covariance; test the exceptional-family left-null direction.',
    'SQ-OPTICAL': 'Propagate the Sachs screen and redshift Jacobian for the named family and source population; check z→0 and finite-z error.',
    'SQ-CROSS-COV': 'Build repeat-sample cross-probe covariance from verified shared sources and run held-out common-frame predictions.',
    'SQ-NATIVE': 'Develop the coupled polarized Bianchi solver and independently compare its family ICs, sign, normalization and high-ell convergence, then fold in a calibrated Commander null.',
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def verified_json(root, path, expected):
    raw = (root / path).read_bytes()
    if digest(raw) != expected:
        raise ValueError(f'{path}: SHA-256 differs from the pinned result')
    return json.loads(raw)


def build(root=ROOT):
    dag = verified_json(root, DAG, AUTHORITY)
    prior = verified_json(root, PRIOR, PRIOR_HASH)
    pub = json.loads((root / PUB).read_bytes())
    if digest(json.dumps(pub['nodes'], sort_keys=True).encode()) != ORIGINAL:
        raise ValueError('PUBLICATION_DAG original-42 canonical node SHA-256 mismatch')
    previous = {row['id']: row for row in prior['nodes']}
    graph = {row['id']: row for row in dag['nodes']}
    if len(graph) != 60 or len(dag['edges']) != 129 or set(graph) != set(previous):
        raise ValueError('scientific node or edge population changed')
    order = dag['topological_order']
    dependencies = {node_id: [] for node_id in graph}
    for edge in dag['edges']:
        if edge['hard']:
            dependencies[edge['to']].append(edge['from'])
    derivations = cross_routes(dag)
    evidence = review_results(root)
    rows = []
    for node_id in order:
        n = graph[node_id]
        inherited = previous[node_id]
        if inherited['science_status'] != n['state']:
            raise ValueError(f'{node_id}: historical statuses disagree')
        action = NEXT.get(node_id) or n.get('next_bounded_empirical_test') or n.get('next_action')
        if not action:
            raise ValueError(f'{node_id}: missing local action')
        links = [file for file, rec in evidence.items()
                 if rec['state'] == 'reviewed' and node_id in rec['direct_nodes']]
        rows.append({
            'id': node_id, 'paper': n['paper'], 'objective': n['objective'],
            'canonical_state': n['state'], 'canonical_acceptance': n['acceptance'],
            'hard_dependencies': dependencies[node_id],
            'hard_dependencies_outside_inherited_completion': [
                dep for dep in dependencies[node_id] if graph[dep]['state'] != 'completed_scoped'],
            'r102_job_references': inherited['r102_conditional_jobs'],
            'r103_direct_evidence_files': links,
            'r103_direct_cross_route_result': node_id if node_id in derivations else None,
            'local_action': action, 'new_scientific_acceptance': False,
        })
    return {
        'schema': 'htt.r103.science_execution_overlay/1',
        'starting_commit': PARENT_HEAD,
        'science_authority': {'path': str(DAG), 'sha256': AUTHORITY},
        'original_42': {'path': str(PUB), 'canonical_nodes_sha256': ORIGINAL},
        'r102_overlay': {'path': str(PRIOR), 'sha256': PRIOR_HASH},
        'next_id': dag['next_action_id'], 'papers': dag['papers'],
        'seven_research_axes': dag['seven_R67_research_axes'],
        'seven_cross_routes': dag['seven_R77_PHY_combinations'],
        'edges': dag['edges'], 'node_count': len(rows),
        'canonical_state_counts': dict(sorted(Counter(n['canonical_state'] for n in rows).items())),
        'new_science_acceptances': 0, 'publication_status': dag['publication_status'],
        'source_qualification': prior['source_qualification_guarantees'],
        'node_reading': 'The canonical_state is the verbatim R78 state. Direct evidence includes recorded source diagnostics, theory, transfer tests or acquisition plans as labeled in reviewed_results. Each retained physical acceptance still requires its own inputs.',
        'cross_route_scope': 'Bounds computed from the R78 stored summaries and its two synthetic closure witnesses. All ranks, errors and bounds condition on the recorded frame, norm, windows and inputs.',
        'reviewed_counts_by_kind': dict(sorted(Counter(rec['evidence_kind'] for rec in evidence.values()
                                                       if rec['state'] == 'reviewed').items())),
        'cross_route_results': derivations, 'reviewed_results': evidence, 'nodes': rows,
    }


# Populate only from R103 artefacts whose actual contents were independently
# inspected. Unlisted, missing or subsequently regenerated bytes receive no
# completion credit, even if their filenames match a planned job.
REVIEWED = {
    'CF4_SHARED_FIELD_HOLDOUT.json': (
        '22b281e84c215411e6b7f1f22a51b57cc941a1ae84de18d8724867556d68bd7e',
        'source_conditioned_analysis', ('SQ-CF4',),
        'Shared-field and fresh-prior predictions on 8,885 6dFGSv release rows with two group linkages.'),
    'GAIA_FRAME_RESULT.json': (
        '2529920ca13330f9209d5dfa8acac74ce275eee9a237c8928f637f013fead7fd',
        'source_conditioned_analysis', ('SQ-GAIA',),
        'Four-shell VSH curvature and exact patch deletion influence on cached 634,233 Gaia/Quaia rows.'),
    'RADIO_COVARIANCE_RESULT.json': (
        'be68f74137c552fd127b2bb3d1124ef71c09796ec813baed19554096b6c398e2',
        'source_conditioned_analysis', ('SQ-RADIO',),
        'Sharp additional covariance budget on 241,892 shared NVSS components under paired Poisson influence.'),
    'SIGNED_REFERENCE.json': (
        '36b4c5b33d12baeb3f31318e296992ff88404193ff4ddd891efbd19e342c907f',
        'transfer_reference_comparison', ('SQ-NATIVE', 'B02'),
        'Signed collision and matched test-photon IX blocks; separate AniCLASS output convention. Full all-family matched transfer remains open.'),
    'CLOSED_TENSOR_HISTORY.json': (
        'c66ffa6786349114362c91d99387122bfad31739cacfdff6878a71c73ce3d49f',
        'transfer_reference_comparison', ('SQ-NATIVE', 'B02'),
        'Closed regular IX m=2 photon evolution on supplied AniCLASS metric and opacity; matched signed T/E/B at five times and four resolutions.'),
    'P1_PATTERN_RESULT.json': (
        'd534faeaf4decefd27a16ab314cb6c991c39363bf99acdfc7ad680b7fa545e28',
        'source_conditioned_analysis', ('S02', 'S03'),
        'Actual joint-window counts on the original 2,048 apparent-CF4 draws and sharp integer bounds from compressed marginals.'),
    'COMMANDER_PAIR_REPLAY.json': (
        'd982a2ba9eb2291d81efe00d0f56a2163ba30c82feb25d8dded465bfbc69ff03',
        'source_conditioned_analysis', ('SQ-CMB-NULL', 'L03'),
        'One PR3 Commander signal/noise pair, six raw pseudo-spectra. Beam, foreground adequacy and the ensemble null remain open.'),
    'COMMANDER_ENSEMBLE_PLAN.json': (
        '284b094346729fa425c5558a2822080908120d1d43dac36fe7bcf02c28f02f18',
        'acquisition_plan', ('SQ-CMB-NULL',),
        'Existing size candidates and additional required bytes for 300 pairs. This plan does not execute an ensemble.'),
    'PV_FIELD_PLAN.json': (
        '999e800ec16f4f638df3acea01c199acc3b40500b4fe0c6e43e6289dd618764f',
        'source_geometry_and_acquisition_plan', ('SQ-CF4',),
        'Geometry joined for all 35,970 CF4 groups at 198,924 grid vertices. Manticore field host timed out; zero posterior fields and no physical S_PV computed.'),
    'NATIVE_RESULT.json': (
        '4ef43fdabd5ac3b1ed028a6e930de609d412e364641a056c0b9935c5f97fce81',
        'solver_numerical_test', ('SQ-NATIVE', 'B02'),
        'Cold moving Thomson in the coupled cell step, stiffness-1000 residual and fixed-fiducial family sweeps.'),
    'MASSLESS_NEUTRINO_RESULT.json': (
        '4d876b895e0fcea28bcfceece2aa53e7044755e6abcf48095f0fe862d3286786',
        'solver_numerical_test', ('SQ-NATIVE', 'B02', 'SQ-PHOTON-FLUX'),
        'Separate massless neutrino hierarchy with photon-only drag and joint stress feedback at fixed total radiation density. Independent observational flux remains open.'),
    'HIGH_TILT_QUADRATURE.json': (
        '9ef330bce5e65ff6d6bad6253212e1d342e20b2bc2c5caf421af46dc6c819384',
        'solver_numerical_test', ('SQ-NATIVE', 'B02'),
        'At |beta|=0.90554, four-force on one fixed all-Stokes sky reaches relative error 5.26e-10 with 32 angular rings.'),
    'REC_REI_RESULT.json': (
        '5553891711a8d4e0d1e0d89c524ad39e2317e09de975ad2bd94e3218fb2769bf',
        'solver_numerical_test', ('SQ-NATIVE', 'B02'),
        'Class B density and baryon-clock controls, positive optical interpolation and visibility closure in REC/REI.'),
    'REI_SOURCE_RESULT.json': (
        '3292c67234e6406fc0c15bf0e08889dafa884382695d1fdd1263dff4a251c02a',
        'external_material_history_replay', ('SQ-NATIVE', 'B02'),
        'Published 1001-row H/He scenario passed to opacity; finite depth from z=20 to z=4 with named observer and material history.'),
    'REI_FIVE_CASE_OPTICAL.json': (
        'b7cd8858016291af45f49ba5d615d902fe156f950d1f574035027b89d05c4cdb',
        'external_material_history_replay', ('SQ-NATIVE', 'B02'),
        'Conditional even/odd depth comparison across five signed prescribed homogeneous shear histories with 1001 rows each.'),
}


def review_results(root, proofs=None):
    checked = {}
    for filename, (expected, grade, node_ids, scope) in (REVIEWED if proofs is None else proofs).items():
        path = root / CURRENT / filename
        observed = digest(path.read_bytes()) if path.is_file() else None
        checked[filename] = {'sha256': observed, 'reviewed_sha256': expected,
                             'state': 'missing' if observed is None else
                                      'reviewed' if observed == expected else 'different_bytes',
                             'evidence_kind': grade, 'direct_nodes': list(node_ids), 'scope': scope}
    return checked


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--node', help='Show a single node, including its acceptance and blockers')
    parser.add_argument('--output', type=Path, help='Write JSON; the default prints to stdout')
    args = parser.parse_args(argv)
    result = build(args.root)
    if args.node:
        matches = [n for n in result['nodes'] if n['id'] == args.node]
        if not matches:
            parser.error(f'unknown node: {args.node}')
        result = matches[0]
    txt = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(txt, encoding='utf-8')
    else:
        print(txt, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
