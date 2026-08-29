"""Thin WU-008 bridge to unchanged accepted scalar and observable-STF code."""
from __future__ import annotations
import hashlib
import numpy as np

FAMILIES=('MES_10','OBSERVABLE_IRREP_ORBIT_V1')
TAILS={FAMILIES[0]:('two-sided',)*10,
       FAMILIES[1]:('two-sided','two-sided','two-sided','upper','two-sided','upper','two-sided','two-sided')}


def make_extractor(metadata: dict, reference_carriers: np.ndarray, source_identity: str):
    # Deliberately lazy: --help and registry verification do not need healpy,
    # private inputs, a workdir, or any GitHub endpoint.
    from scripts.observed_runs import run_planck_pr3 as worker
    from scripts.observed_runs.run_planck_mes_morphology import SOURCE_FEATURE_IDS,SOURCE_FEATURE_UNITS
    from obsstat.mes_row_anchor import build_mes_row_anchor_state, ResidualDipoleAttribution
    from common.observable_irrep_state import ObservableIrrepCarrier
    from obsstat.planck_lowell_irrep_projection import project_planck_carrier_to_observable_irreps
    from obsstat.observable_irrep_orbit import observable_irrep_orbit_report,orbit_family_vector,FRAME_FREE_TAILS,FRAME_FREE_FEATURE_IDS
    if tuple(FRAME_FREE_TAILS)!=TAILS[FAMILIES[1]] or len(FRAME_FREE_FEATURE_IDS)!=8:
        raise ValueError('accepted irrep registry drifted')
    if metadata['coordinate_frame']!='GALACTIC' or metadata['map_unit']!='microK_CMB':
        raise ValueError('accepted frame/unit drifted')
    scalar_reference=np.array([worker._component_features_from_real_carrier(row) for row in reference_carriers],dtype=float)
    if scalar_reference.shape!=(len(reference_carriers),12) or not np.all(np.isfinite(scalar_reference)):
        raise ValueError('reference scalar feature extraction failed')
    covariance=np.ascontiguousarray(np.cov(scalar_reference,rowvar=False,ddof=1),dtype='<f8')
    covariance_id='sha256:'+hashlib.sha256(b'WU008_DIAGNOSTIC_REFERENCE_COVARIANCE_NOT_USED_IN_SCORE\0'+covariance.tobytes()).hexdigest()

    def extract(components):
        row=np.asarray(components,dtype=float)
        if row.shape!=(32,) or not np.all(np.isfinite(row)):raise ValueError('finite harmonic carrier required')
        row_id='WU008-INJECTED-'+hashlib.sha256(row.astype('<f8').tobytes()).hexdigest()
        values={};absence={}
        carrier=ObservableIrrepCarrier(
            components=tuple(map(float,row)),frame='GALACTIC',
            basis='ORTHONORMAL_CONDON_SHORTLEY_REAL_L2_L5_V1',units='microK_CMB',
            source_identity=source_identity,operator_identity=metadata['operator_identity_sha256'],row_identity=row_id)
        state=project_planck_carrier_to_observable_irreps(carrier)
        report=observable_irrep_orbit_report(state)
        unavailable=[name for name in FRAME_FREE_FEATURE_IDS if report.coordinate(name).status!='AVAILABLE']
        if unavailable:absence[FAMILIES[1]]='TYPED_ABSENCE:'+','.join(unavailable)
        else:values[FAMILIES[1]]=np.asarray(orbit_family_vector(report,FAMILIES[1]),dtype=float)
        try:
            scalar=np.asarray(worker._component_features_from_real_carrier(row),dtype=float)
        except worker.PlanckWorkerError as error:
            absence[FAMILIES[0]]='REGISTERED_SCALAR_EXTRACTOR_ABSTENTION:'+str(error)
        else:
            anchor=build_mes_row_anchor_state(
                row_id=row_id,feature_values=tuple(map(float,scalar)),
                feature_ids=SOURCE_FEATURE_IDS,feature_units=SOURCE_FEATURE_UNITS,
                residual_dipole_attribution=ResidualDipoleAttribution.SAG_OBSERVER_MOTION_EPS1_ZERO,
                source_identity=source_identity,covariance_identity=covariance_id,
                operator_identity=metadata['operator_identity_sha256'])
            values[FAMILIES[0]]=np.r_[anchor.anchor('sigma').value,anchor.anchor('omega').value,scalar[4:]]
        return values,absence
    references={f:[] for f in FAMILIES}
    for row in reference_carriers:
        values,absence=extract(row)
        if absence:raise ValueError('registered calibration row unavailable; never drop it: '+str(absence))
        for f in FAMILIES:references[f].append(values[f])
    return extract,{f:np.asarray(v) for f,v in references.items()}
