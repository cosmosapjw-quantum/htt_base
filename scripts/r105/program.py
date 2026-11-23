"""R105 evidence-indexed science DAG. Rebuild or query an individual node."""
import argparse
from collections import Counter
import json
from pathlib import Path

from scripts.r103.program import AUTHORITY, DAG, ORIGINAL, PAPER, PUB, digest, verified_json


ROOT = Path(__file__).resolve().parents[2]
OLDER = PAPER/'R103_SOLVER_SOURCE_CONTINUATION_20261123/NODE60_EXECUTION.json'
PREVIOUS = PAPER/'R104_DATA_SOLVER_CONTINUATION_20261124/R104_RESULTS.json'
OUTPUT_DIR = PAPER/'R105_RESEARCH_20261124'
BASE = '5a5f3b44d4fa5be65b71c2f80e715ebf9d1abf0a'
R103_HASH = '393bf7d3c233762a30ce52e90bed55e32dbde731db5b87a187befdbb8a5fbb34'
R104_HASH = '50381913d08a82f428b1ce268c0dbd919eb2fd1bc032495a0cd4c9f61e3d8202'

NEXT_ACTIONS={
    'S02':'Bind a common-congruence physical source/scale and selection law to the 2,048 paired IDs before computing physical functional mass.',
    'S03':'Use the same draw IDs for an independently justified selection sensitivity budget; compare that budget with the P1_ORDERING pairwise tie costs.',
    'H02':'Compare held-out indicators and independent zero points on the original groups. Model unmeasured velocity support jointly across the 36 coefficients and qualify cross-group covariance.',
    'SQ-CF4':'Run the calibrated method/selection and correlated-flow holdout on exact CF4 groups; retain the 2MRS finite-support remainder and inter-group dependence.',
    'SQ-RADIO':'Repeat matched nonlinear peak/integrated fits under a source-matched clustering/multiplicity null; compare observed shifts with the same estimator.',
    'SQ-GAIA':'Measure source-specific AGN/scanning residuals shared across shells and validate the magnetic cross-row covariance on held-out sky patches.',
    'PHY-01':'Combine the selected-group hemisphere response with independent normal-frame shear and selection calibration; retain differences between 2MRS-covered and missing groups.',
    'PHY-02':'Recover common-normal photon flux, density and other-species momentum at matched times; compare moment positivity with the solved forward model.',
    'PHY-03':'Infer peak/integrated selection response from the same objects, propagate its covariance and test the signed transverse residual against a qualified LSS null.',
    'PHY-04':'Use independent redshifts, scanning and AGN centroid controls for the weak first B2 shell contrast and compare the optical transfer on that sample.',
    'PHY-05':'Attach independent total normal flux and a bound on tetrad orientation, then compare the projected left-null component with its orientation and measurement budget.',
    'PHY-06':'Fit independently supplied higher photon multipoles and compare the eigenvalue and orientation contributions to same-frame stress evolution.',
    'PHY-07':'Apply the calibrated CF4/radio joint covariance to the projected radial inverse-distance design and test the weakest axis in the retained windows.',
}


def verified_evidence(root, directory, manifest, graph):
    """A reviewed byte identity and optional per-node JSON section bind every new link."""
    found={}
    for name, receipt in manifest.items():
        if Path(name).name!=name:
            raise ValueError(f'invalid source basename: {name}')
        if receipt.get('format')=='markdown':
            data=(root/directory/name).read_bytes()
            if digest(data)!=receipt['sha256'] or not data.decode('utf-8').strip():
                raise ValueError(f'{name}: reviewed text is absent or differs')
            payload={}
        else:
            payload=verified_json(root,directory/name,receipt['sha256'])
        if not isinstance(payload, dict) or not receipt['nodes']:
            raise ValueError(f'{name}: missing scientific source or node mapping')
        for nid,anchor in receipt['nodes'].items():
            if nid not in graph or (anchor is not None and anchor not in payload):
                raise ValueError(f'{name}: unresolved node/section {nid}/{anchor}')
        found[name]=receipt
    return found


def build(root=ROOT):
    dag=verified_json(root,DAG,AUTHORITY)
    old=verified_json(root,OLDER,R103_HASH)
    parent=verified_json(root,PREVIOUS,R104_HASH)
    pub=json.loads((root/PUB).read_bytes())
    if digest(json.dumps(pub['nodes'],sort_keys=True).encode())!=ORIGINAL:
        raise ValueError('original 42-node payload changed')
    graph={n['id']:n for n in dag['nodes']}
    predecessor={n['id']:n for n in old['nodes']}
    if (set(graph)!=set(predecessor) or len(graph)!=60 or len(dag['edges'])!=129
            or dag['edges']!=old['edges'] or dag['next_action_id']!=old['next_id']):
        raise ValueError('R78/R103 graph identity mismatch')
    for name, rec in old['reviewed_results'].items():
        if rec['state']!='reviewed':
            raise ValueError(f'{name}: unexpected R103 review state')
        verified_json(root,OLDER.parent/name,rec['reviewed_sha256'])
    for name, sha in parent['artifacts_sha256'].items():
        verified_json(root,PREVIOUS.parent/name,sha)
    manifest_path=root/OUTPUT_DIR/'NODE_EVIDENCE.json'
    manifest_bytes=manifest_path.read_bytes()
    evidence=verified_evidence(root,OUTPUT_DIR,json.loads(manifest_bytes),graph)
    rows=[]
    for nid in dag['topological_order']:
        n=graph[nid]; prev=predecessor[nid]
        if n['state']!=prev['canonical_state'] or n['acceptance']!=prev['canonical_acceptance']:
            raise ValueError(f'{nid}: R78/R103 state mismatch')
        r104=parent['node_links'].get(nid,{})
        older_refs=r104.get('evidence',[])
        if not all(f in parent['artifacts_sha256'] for f in older_refs):
            raise ValueError(f'{nid}: unbound R104 evidence file')
        direct=[{'file':f,'section':rec['nodes'][nid],'kind':rec.get('kind_per_node',{}).get(nid,rec['kind'])} for f,rec in evidence.items()
                if nid in rec['nodes']]
        rows.append({'id':nid,'paper':n['paper'],'objective':n['objective'],'canonical_state':n['state'],
                     'canonical_acceptance':n['acceptance'],'hard_dependencies':prev['hard_dependencies'],
                     'hard_dependencies_outside_inherited_completion':prev['hard_dependencies_outside_inherited_completion'],
                     'R103_evidence_files':prev['r103_direct_evidence_files'],
                     'R103_cross_route':prev['r103_direct_cross_route_result'],
                     'R104_report_state':r104.get('status'),'R104_evidence_files':older_refs,
                     'R104_input_or_dependency_note':r104.get('remaining_input',r104.get('reason',r104.get('note'))),
                     'R105_direct_evidence':direct,'R105_science_acceptance':False,
                     'local_action':NEXT_ACTIONS.get(nid,prev['local_action'])})
    direct=sum(bool(n['R105_direct_evidence']) for n in rows)
    open_direct=sum(bool(n['R105_direct_evidence']) and n['canonical_state']!='completed_scoped' for n in rows)
    open_count=sum(n['canonical_state']!='completed_scoped' for n in rows)
    r104_direct=sum(bool(n['R104_evidence_files']) for n in rows)
    return {'schema':'htt.r105.science_evidence/1','starting_commit':BASE,
            'r78_source':str(DAG),'r78_sha256':AUTHORITY,'original_42_sha256':ORIGINAL,
            'predecessors':{str(OLDER):R103_HASH,str(PREVIOUS):R104_HASH},
            'reviewed_manifest':str(OUTPUT_DIR/'NODE_EVIDENCE.json'),'reviewed_manifest_sha256':digest(manifest_bytes),
            'new_receipts':evidence,'state_meaning':'canonical_state is the R78 state; evidence links record bounded work done without replacing that acceptance.',
            'counts':{'nodes':len(rows),'edges':len(dag['edges']),'r104_nodes_with_evidence':r104_direct,
                      'r105_nodes_with_direct_work':direct,'r105_nodes_without_direct_work':len(rows)-direct,
                      'canonical_open':open_count,'canonical_open_with_r105_direct_work':open_direct,
                      'canonical_open_without_r105_direct_work':open_count-open_direct,
                      'r105_new_scientific_acceptances':0,'new_receipt_files':len(evidence)},
            'canonical_states':dict(sorted(Counter(n['canonical_state'] for n in rows).items())),
            'publication_status':dag['publication_status'],'next_id':dag['next_action_id'],
            'physical_Pi':None,'physical_GF':None,'calibrated_p':None,'Bianchi_family_attribution':None,
            'papers':dag['papers'],'seven_research_axes':dag['seven_R67_research_axes'],
            'seven_cross_routes':dag['seven_R77_PHY_combinations'],'edges':dag['edges'],'nodes':rows}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--node',help='show a single canonical ID and its evidence at three successive cycles')
    p.add_argument('--output',type=Path)
    a=p.parse_args(argv);r=build(a.root)
    if a.node:
        matches=[n for n in r['nodes'] if n['id']==a.node]
        if not matches:
            p.error(f'unknown canonical node: {a.node}')
        r=matches[0]
    encoded=json.dumps(r,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if a.output:
        a.output.write_text(encoded,encoding='utf-8')
    else:
        print(encoded,end='')


if __name__=='__main__':
    main()
