"""Frozen R7 q-proxy consumer: deterministic scenario, no physical inference."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np

from common.conditional_source_image import BoxSourceImage, SourceImageError
from common.r9_product import ProductIntake, SharedStateEmbedding

PINS = {
    'inputs/FROZEN_CALIBRATION_INPUT.npz': '3817128984e39696ac8c7957666c58e55bb7fce08386dbb3e8e7dc82c096d8a7',
    'inputs/FROZEN_CALIBRATION_PARAMETER_CONTRACT.json': 'e3083b7335dd9ca33ce5b0233d1f5323332c3d03d44c6fe42e3ec79ec257453e',
    'verification/COHERENT_CALIBRATION_FIXTURE.npz': '0f6a4d37b4d06ea9ac1c310ee5fbc5ce4112d1da7953205f3358347d6c3df1c2',
}
HOLDS = {
    'physical_source_closure': 'HOLD',
    'target_source_full_response': 'HOLD',
    'reference_U_R_optical_bridge': 'HOLD',
    'empirical_MES_D': 'HOLD_NOT_COMPUTED',
    'source_mean': 'UNRESOLVED',
    'source_correlation': 'UNRESOLVED',
    'target_transfer': 'UNRESOLVED',
}
PARAMETERS = ('beta_flow','Vx_Gal','Vy_Gal','Vz_Gal')
UNITS = ('dimensionless','km/s','km/s','km/s')
LABELS = tuple(name+sign for name in [*[f'basis_E{i+1}' for i in range(5)],'nominal','left_null'] for sign in ('+','-'))


def load_frozen(source):
    source=Path(source)
    # Freeze bytes once before loading; do not re-open mutable paths after hashes.
    import io
    payload={}
    for name,expected in PINS.items():
        raw=(source/name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected:
            raise SourceImageError('SOURCE_IDENTITY_MISMATCH',name)
        payload[name]=raw
    with np.load(io.BytesIO(payload['inputs/FROZEN_CALIBRATION_INPUT.npz']),allow_pickle=False) as f:
        data={k:f[k] for k in f.files}
    with np.load(io.BytesIO(payload['verification/COHERENT_CALIBRATION_FIXTURE.npz']),allow_pickle=False) as f:
        fixture={k:f[k] for k in f.files}
    contract=json.loads(payload['inputs/FROZEN_CALIBRATION_PARAMETER_CONTRACT.json'])
    rows=tuple(f'PantheonPlus:{i}' for i in data['indices'])
    image=BoxSourceImage(data['L'],data['z'],data['v'],fixture['G'],fixture['halfwidth'],rows,rows)
    if not np.array_equal(image.A,fixture['A']) or not np.array_equal(image.L,fixture['L']):
        raise SourceImageError('FROZEN_ARRAY_MISMATCH','stored A/L differ from frozen row construction')
    if contract['units']!=list(UNITS) or not np.array_equal(contract['halfwidth'],image.halfwidth):
        raise SourceImageError('UNIT_MISMATCH','parameter contract')
    intake=ProductIntake(
        product_id='MES_R7_FROZEN_CALIBRATION',release='PantheonPlus:c447f0fea703fcd0fff57de5000947b5ca81286b',
        source_ids=tuple(str(x) for x in data['CID']),row_ids=rows,
        feature_units=('km/s',)*525,frame='ICRS final SN positions; Galactic calibration velocity',
        epoch='RELEASE_DEFINED_NOT_A_CONGRUENCE_EPOCH',extraction='frozen signed L; q-proxy finite increment',
        selection='FROZEN_525_ROWS',group='RELEASE_FIXED_NO_GROUP_RESPONSE',
        calibration='DETERMINISTIC_MARGINAL_INTERVAL_SCALES',mask='FROZEN_ROW_WINDOW',
        covariance_source=None,covariance_row_ids=None,law_kind='SCENARIO_ONLY')
    embedding=SharedStateEmbedding(
        state_id='MES_R7_CALIBRATION_INCREMENT',state_names=PARAMETERS,state_units=UNITS,
        state_roles=('SHARED_NUISANCE',)*4,frame='GALACTIC_CARTESIAN',epoch='FROZEN_RELEASE',
        local_parameter_names=PARAMETERS,local_parameter_units=UNITS,
        nuisance_names=(),nuisance_units=(),theta_map=np.eye(4),eta_map=np.empty((0,4)))
    return image,intake,embedding,fixture,contract


def conditional_report(source, *, request='q_proxy', cover_depth=6):
    if request!='q_proxy':
        return {'status':'INSUFFICIENT_PHYSICAL_INPUTS','requested_quantity':request,
                'reason':'Only deterministic q_proxy sensitivity is supported; no same-channel physical bridge, source law, joint coverage or native result is supplied.',
                'unresolved_inputs':dict(HOLDS),'production_enabled':False}
    image,intake,embedding,fixture,contract=load_frozen(source)
    records,certificate=image.support(fixture['directions'],LABELS,cover_depth=cover_depth)
    for row in records:
        mapped,_=embedding.split(row['feasible_delta_theta'])
        if not np.array_equal(mapped,row['feasible_delta_theta']):
            raise SourceImageError('STATE_INCIDENCE_MISMATCH','shared calibration state')
    return {'status':'CONDITIONAL_SCENARIO','owner':'obsstat','quantity':'q_proxy_calibration_increment',
            'source_pins':dict(PINS),'row_ids':list(intake.row_ids),'literal_CIDs':list(intake.source_ids),
            'rows':525,'literal_CID_count':len(set(intake.source_ids)),
            'product_intake_identity':intake.identity,'sampling_law_kind':intake.law_kind,
            'state_embedding_identity':embedding.identity,'parameter_names':list(PARAMETERS),
            'parameter_units':list(UNITS),'theta0':contract['theta0'],'halfwidth':contract['halfwidth'],
            'latent_coordinates':'dimensionless xi in [-1,1]^4; delta_theta=halfwidth*xi',
            'feature_units':['dimensionless']*5,'feature_frame':image.feature_frame,
            'velocity_frame':image.velocity_frame,'nominal_anchor_velocity':image.velocity(np.zeros(4)).tolist(),
            'origin_feature_vector':list(image.realization(np.zeros(4)).feature_vector),
            'support_results':records,'certificate':certificate,'unresolved_inputs':dict(HOLDS),
            'implemented_domain':'4D box; m=525 q=4 p=5','ellipsoid':'UNSUPPORTED_DOMAIN',
            'general_dimension_support':False,'production_enabled':False,
            'joint_confidence':'NOT_ASSIGNED','mes_anchor_registered':False,
            'canonical_F_modified':False,'independent_direction_queries_are_joint_realization':False,
            'physical_scope':'beta_flow is reconstruction calibration, not congruence tilt; q-proxy STF is not physical shear',
            'image_scope':'nonlinear image, not generally convex or zonotopal; support bounds do not establish image membership'}


def _json(value):
    if isinstance(value,np.ndarray):return value.tolist()
    if isinstance(value,np.generic):return value.item()
    raise TypeError(type(value).__name__)


def write_report(source, output, *, request='q_proxy', cover_depth=6):
    """Reserve a new directory atomically before computing or writing results."""
    output=Path(output)  # Do not resolve an existing/dangling output symlink.
    if output.exists() or output.is_symlink():
        raise SourceImageError('OUTPUT_EXISTS',str(output))
    try:
        output.mkdir(parents=True,exist_ok=False)
    except FileExistsError as exc:
        raise SourceImageError('OUTPUT_EXISTS',str(output)) from exc
    result=conditional_report(source,request=request,cover_depth=cover_depth)
    with (output/'result.json').open('x') as f:
        json.dump(result,f,indent=2,default=_json,allow_nan=False)
        f.write('\n')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--request',default='q_proxy')
    p.add_argument('--cover-depth',type=int,default=6)
    args=p.parse_args()
    try:
        result=write_report(args.source,args.out,request=args.request,cover_depth=args.cover_depth)
    except (SourceImageError,OSError) as exc:
        p.exit(2,f'{exc}\n')
    print(json.dumps({'status':result['status'],'out':str(args.out)}))
    return 0 if result['status']=='CONDITIONAL_SCENARIO' else 2


if __name__=='__main__':
    raise SystemExit(main())
