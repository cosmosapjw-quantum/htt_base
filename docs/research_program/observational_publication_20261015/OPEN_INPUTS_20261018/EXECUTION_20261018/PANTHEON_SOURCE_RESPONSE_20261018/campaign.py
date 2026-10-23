"""One finite, source-conditioned descriptive campaign; not a calibration law.

Only named released columns are read. No upstream code is executed.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
from decimal import Decimal
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import shlex
import tarfile

import numpy as np
from astropy.io import fits

OUT = Path(__file__).resolve().parent
RAW = Path('/mnt/extdrive/workdir/htt_open_data/pantheonplus/source_null_20261018')
TRUTH = {
    'SIM_ZCMB': 'SIM_REDSHIFT_CMB', 'SIM_DLMAG': 'SIM_DLMU',
    'SIM_PKMJD': 'SIM_PEAKMJD', 'SIM_x0': 'SIM_SALT2x0',
    'SIM_x1': 'SIM_SALT2x1', 'SIM_c': 'SIM_SALT2c',
    'SIM_mB': 'SIM_SALT2mB', 'SIM_alpha': 'SIM_SALT2alpha',
    'SIM_beta': 'SIM_SALT2beta', 'SIM_gammaDM': 'SIM_SALT2gammaDM',
    'SIM_AV': 'SIM_AV', 'SIM_RV': 'SIM_RV', 'SIM_VPEC': 'SIM_VPEC',
    'SIM_ZFLAG': 'SIM_REDSHIFT_FLAG', 'SIM_TYPE_INDEX': 'SIM_TYPE_INDEX',
    'SIM_TEMPLATE_INDEX': 'SIM_TEMPLATE_INDEX',
}
REQUIRED = ('x1', 'c', 'x1ERR', 'cERR', 'SIM_x1', 'SIM_c', 'SIM_AV', 'SIM_RV', 'SIM_ZCMB')
METRICS = ('E', 'rx', 'rc0', 'rc', 'sx', 'sc0', 'sc', 'q_working')


def dump(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parse_fitres(path):
    """Retain literal tokens, including CID and serialization precision."""
    columns = None
    rows = []
    with gzip.open(path, 'rt') as stream:
        for line_no, line in enumerate(stream, 1):
            tokens = line.split()
            if not tokens:
                continue
            if tokens[0] == 'VARNAMES:':
                if columns is not None or len(set(tokens[1:])) != len(tokens[1:]):
                    raise ValueError('Duplicate VARNAMES')
                columns = tokens[1:]
            elif tokens[0] == 'SN:':
                if columns is None or len(tokens) != len(columns) + 1:
                    raise ValueError(f'Column count at {path}:{line_no}')
                rows.append((line_no, dict(zip(columns, tokens[1:]))))
    if columns is None:
        raise ValueError('Missing VARNAMES')
    return columns, rows


def storage_ulp(value, dtype):
    dtype = np.dtype(dtype).newbyteorder('=')
    v = dtype.type(value)
    if dtype.kind not in 'fc':
        return 0.0
    return max(abs(float(np.nextafter(v, dtype.type(np.inf))) - float(v)),
               abs(float(v) - float(np.nextafter(v, dtype.type(-np.inf)))))


def truth_agrees(token, value, dtype):
    dtype = np.dtype(dtype)
    if dtype.kind in 'iu':
        return Decimal(token) == Decimal(int(value))
    if not math.isfinite(float(value)) or not Decimal(token).is_finite():
        return False
    digit = Decimal(1).scaleb(Decimal(token).as_tuple().exponent)
    tolerance = abs(digit) / 2 + Decimal.from_float(storage_ulp(value, dtype))
    return abs(Decimal(token) - Decimal.from_float(float(value))) <= tolerance


def choose_candidate(tokens, candidates):
    """Input candidates already share realization, literal CID, and both LIBIDs."""
    if not candidates:
        return 'ZERO_CANDIDATE', None, []
    agreeing = []
    diagnostics = []
    missing = False
    for c in candidates:
        bad = []
        absent = []
        for fit_name, head_name in TRUTH.items():
            # These are all shared truth fields in the actual release schema.
            if fit_name not in tokens or head_name not in c['values']:
                absent.append([fit_name, head_name])
            elif not truth_agrees(tokens[fit_name], c['values'][head_name], c['dtypes'][head_name]):
                bad.append(fit_name)
        diagnostics.append({'head_path': c['path'], 'head_row_index': c['row_index'],
                            'disagreeing_fields': bad, 'missing_pairs': absent})
        missing |= bool(absent)
        if not bad and not absent:
            agreeing.append(c)
    if len(agreeing) == 1:
        return 'UNIQUE_TRUTH_MATCH', agreeing[0], diagnostics
    if len(agreeing) > 1:
        return 'MULTIPLE_AGREEING', None, diagnostics
    return ('MISSING_TRUTH_BINDING' if missing else 'TRUTH_DISAGREEMENT'), None, diagnostics


def response(tokens):
    flags = []
    if int(tokens['ERRFLAG_FIT']) != 0:
        flags.append('ERRFLAG_FIT_NONZERO')
    if not int(tokens['CUTFLAG_SNANA']) & 2:
        flags.append('CUTFLAG_BIT2_ABSENT')
    values = {k: float(tokens[k]) for k in REQUIRED}
    if not all(math.isfinite(v) for v in values.values()):
        flags.append('NONFINITE_REQUIRED')
    if values['x1ERR'] <= 0 or values['cERR'] <= 0:
        flags.append('NONPOSITIVE_ERROR')
    if values['SIM_RV'] <= 0:
        flags.append('NONPOSITIVE_RV')
    if values['SIM_AV'] < 0:
        flags.append('NEGATIVE_AV')
    if flags:
        return {'eligible': False, 'exclusion_reasons': '|'.join(flags),
                'quadratic_status': 'INELIGIBLE'}, flags
    E = values['SIM_AV'] / values['SIM_RV']
    rx = values['x1'] - values['SIM_x1']
    rc0 = values['c'] - values['SIM_c']
    rc = rc0 - E
    sx, sc0, sc = rx / values['x1ERR'], rc0 / values['cERR'], rc / values['cERR']
    result = {'eligible': True, 'exclusion_reasons': '', 'E': E, 'rx': rx, 'rc0': rc0,
              'rc': rc, 'sx': sx, 'sc0': sc0, 'sc': sc}
    if not all(math.isfinite(v) for v in (E, rx, rc0, rc, sx, sc0, sc)):
        result.update(eligible=False, exclusion_reasons='NONFINITE_COMPUTED', quadratic_status='INELIGIBLE')
        return result, ['NONFINITE_COMPUTED']
    covariance = float(tokens['COV_x1_c'])
    rho = covariance / values['x1ERR'] / values['cERR']
    result['rho'] = rho if math.isfinite(rho) else None
    # eigenvalues of [[1,rho],[rho,1]] are 1 +/- abs(rho).
    if not math.isfinite(rho) or 1 - abs(rho) <= 1e-10:
        result['quadratic_status'] = 'UNEVALUABLE_CORRELATION'
    else:
        q = (sx*sx - 2*rho*sx*sc + sc*sc) / (1-rho*rho)
        if math.isfinite(q) and q >= 0:
            result.update(q_working=q, quadratic_status='DESCRIPTIVE_ONLY')
        else:
            result['quadratic_status'] = 'UNEVALUABLE_COMPUTED'
    return result, []


def direction(candidate, rule):
    vals = candidate['values']
    ra, dec, simra, simdec = (float(vals[x]) for x in ('RA', 'DEC', 'SIM_RA', 'SIM_DEC'))
    if not all(math.isfinite(x) for x in (ra, dec, simra, simdec)):
        return 'NONFINITE', None, None
    if not (0 <= ra < 360 and -90 <= dec <= 90 and 0 <= simra < 360 and -90 <= simdec <= 90):
        return 'SENTINEL_OR_RANGE', None, None
    if rule == 'STRICT_STORAGE_ULP':
        good = (abs(ra-simra) <= storage_ulp(vals['SIM_RA'], candidate['dtypes']['SIM_RA']) and
                abs(dec-simdec) <= storage_ulp(vals['SIM_DEC'], candidate['dtypes']['SIM_DEC']))
    elif rule == 'SNANA_FLOAT32_PROMOTED_TO_FITS_FLOAT64':
        good = simra == float(np.float32(ra)) and simdec == float(np.float32(dec))
    else:
        raise ValueError('Unknown direction contract')
    return ('QUALIFIED_NATIVE_RELEASED' if good else 'SOURCE_COORDINATE_DISAGREEMENT',
            ra if good else None, dec if good else None)


def describe(values):
    data = np.asarray([x for x in values if x is not None and math.isfinite(x)], dtype=float)
    if not len(data):
        return {'count': 0, 'mean': None, 'median': None, 'sd_ddof1': None, 'p16': None, 'p84': None}
    return {'count': len(data), 'mean': float(np.mean(data)), 'median': float(np.median(data)),
            'sd_ddof1': float(np.std(data, ddof=1)) if len(data)>1 else None,
            'p16': float(np.percentile(data,16)), 'p84': float(np.percentile(data,84))}


def summarize(rows):
    return {'rows': len(rows), 'eligible': sum(r['eligible'] for r in rows),
            'join_status': dict(Counter(r['join_status'] for r in rows)),
            'direction_status': dict(Counter(r['direction_status'] for r in rows)),
            'quadratic_status': dict(Counter(r['quadratic_status'] for r in rows)),
            'response': {m: describe(r.get(m) for r in rows if r['eligible']) for m in METRICS}}


def configuration_evidence(acquisition):
    output = []
    wanted = ('RANSEED', 'GENMAG_OFF_GLOBAL', 'GENMAG_SMEAR', 'GENMAG_SMEAR_MODELNAME',
              'GENMAG_SMEAR_SCALE', 'GENMAG_SMEAR_SCALE(c)', 'GENMODEL', 'GENSIGMA_VPEC',
              'VPEC_ERR', 'GENPDF_FILE', 'HOSTLIB_FILE', 'GENPEAK_SALT2ALPHA',
              'GENPEAK_SALT2BETA', 'GENPEAK_SALT2c')
    for e in acquisition['entries']:
        if not e['path'].endswith('/SIMLOGS.tar.gz'):
            continue
        with tarfile.open(e['local']) as tar:
            for member in tar.getmembers():
                if not member.isfile() or not member.name.endswith('.LOG'):
                    continue
                content = tar.extractfile(member).read().decode('utf-8', errors='replace')
                lines = content.splitlines()
                commands = [line.strip() for line in lines if 'Full command:' in line]
                tokens = shlex.split(commands[0].split('Full command:',1)[1]) if commands else []
                config = {}
                for key in wanted:
                    # Preserve occurrence ordering; do not infer omitted defaults.
                    config[key] = [tokens[i+1] for i,t in enumerate(tokens[:-1]) if t==key] or 'UNKNOWN_NOT_IN_COMMAND'
                output.append({'source_path': e['path'], 'archive_sha256': e['sha256'],
                               'member': member.name, 'member_sha256': hashlib.sha256(content.encode()).hexdigest(),
                               'actual_commands': commands, 'config_tokens': config,
                               'relevant_log_lines': [line for line in lines if re.search(
                                   r'Random number seed|Pec. Velocity|GENMAG_SMEAR_SCALE:|Generation model|MAG.*offset|mag.*offset',line)]})
    return {'runs': output, 'DES_actual_logs': 'ABSENT_FROM_PINNED_TREE_UNKNOWN',
            'interpretation': 'Actual commands only; omitted settings UNKNOWN; no generic INPUT defaults or cross-survey offset propagation.'}


def repeated_summary(rows):
    outputs = {}
    for field in ('CID', 'SIM_LIBID'):
        groups = defaultdict(list)
        for r in rows:
            groups[r[field]].append(r)
        repeated = {k:v for k,v in groups.items() if len(v)>1}
        outputs[field] = {'distinct': len(groups), 'repeated_values': len(repeated),
                          'excess_occurrences': sum(len(v)-1 for v in repeated.values()),
                          'values_crossing_surveys': sum(len({r['IDSURVEY'] for r in v})>1 for v in repeated.values()),
                          'values_crossing_realizations': sum(len({r['realization'] for r in v})>1 for v in repeated.values())}
    per_real = {}
    for real in sorted({r['realization'] for r in rows}):
        counts = Counter(r['CID'] for r in rows if r['realization']==real)
        per_real[real] = {'repeated_cid_values': sum(n>1 for n in counts.values()),
                          'excess_cid_occurrences': sum(n-1 for n in counts.values())}
    outputs['within_realization'] = per_real
    return outputs


def plot_results(rows, summary):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    eligible = [r for r in rows if r['eligible']]
    surveys = sorted({r['IDSURVEY'] for r in rows},key=int)
    plt.rcParams.update({'font.size':9})
    fig, axes = plt.subplots(1,2,figsize=(10,4),constrained_layout=True)
    labels = [str(s) for s in surveys]
    for metric, delta, color in [('rc0',-.14,'#3176b0'),('rc',.14,'#c86424')]:
        stat = [describe(r[metric] for r in eligible if r['IDSURVEY']==s) for s in surveys]
        med=np.array([x['median'] for x in stat]); lo=np.array([x['p16'] for x in stat]); hi=np.array([x['p84'] for x in stat])
        axes[0].errorbar(np.arange(len(surveys))+delta,med,yerr=[med-lo,hi-med],fmt='o',color=color,label=metric+' median, 16–84%')
    axes[0].set_xticks(np.arange(len(surveys)),labels); axes[0].set_xlabel('Released numeric IDSURVEY');axes[0].set_ylabel('Color response');axes[0].legend(fontsize=7)
    zbins=['[0,.03)','[.03,.1)','[.1,infinity)']
    for metric in ('rc0','rc'):
        stat=[describe(r[metric] for r in eligible if r['redshift_bin']==z) for z in zbins]
        axes[1].plot(zbins,[s['median'] for s in stat],'o-',label=metric+' median')
    axes[1].set_xlabel('SIM_ZCMB bin');axes[1].set_ylabel('Color response');axes[1].legend()
    fig.suptitle('Released selected simulations: raw and dust-predictor color response (C0)')
    for ext in ('png','pdf'):fig.savefig(OUT/f'color_response.{ext}',dpi=170)
    plt.close(fig)
    fig, axes=plt.subplots(1,2,figsize=(10,4),constrained_layout=True)
    for metric in ('sx','sc'):
        st=[describe(r[metric] for r in eligible if r['IDSURVEY']==s) for s in surveys]
        axes[0].plot(labels,[s['median'] for s in st],'o-',label=metric+' median')
    axes[0].set_ylabel('Response / reported error');axes[0].set_xlabel('Numeric IDSURVEY');axes[0].legend()
    for s in surveys:
        v=sorted(r['q_working'] for r in eligible if r['IDSURVEY']==s and 'q_working' in r)
        if v:axes[1].plot(v,(np.arange(len(v))+1)/len(v),label=s)
    axes[1].set_xscale('symlog',linthresh=1);axes[1].set_xlabel('Descriptive working quadratic discrepancy');axes[1].set_ylabel('Empirical fraction');axes[1].legend(fontsize=7,ncol=3)
    fig.suptitle('Working 2×2 covariance benchmark; no chi-square calibration or p-values')
    for ext in ('png','pdf'):fig.savefig(OUT/f'working_covariance.{ext}',dpi=170)
    plt.close(fig)
    qualified=[r for r in eligible if r['direction_status']=='QUALIFIED_NATIVE_RELEASED']
    fig,axes=plt.subplots(1,2,figsize=(10,4),constrained_layout=True)
    if qualified:
        scatter=axes[0].scatter([r['native_ra'] for r in qualified],[r['native_dec'] for r in qualified],c=[r['rc'] for r in qualified],s=3,cmap='coolwarm',rasterized=True)
        fig.colorbar(scatter,ax=axes[0],label='Dust-predictor color response rc')
    else:
        axes[0].text(.5,.5,'No source-qualified released coordinates',ha='center',transform=axes[0].transAxes)
    axes[0].set(xlim=(0,360),ylim=(-90,90),xlabel='Native released RA (deg)',ylabel='Native released DEC (deg)')
    sectors=[f'{hemi}:RA{q}' for hemi in ('S','N') for q in range(4)]
    med=[describe(r['rc'] for r in qualified if r['sector']==s) for s in sectors]
    axes[1].bar(np.arange(8),[s['count'] for s in med],color='#87b5ca');axes[1].set_xticks(np.arange(8),sectors,rotation=45);axes[1].set_ylabel('Eligible, qualified released rows')
    ax2=axes[1].twinx();ax2.plot(np.arange(8),[s['median'] if s['median'] is not None else np.nan for s in med],'o-',color='#b64c30');ax2.set_ylabel('Sector median rc')
    fig.suptitle('Released cadence positions only; SDSS/SNLS HEAD absent; no angular selection law')
    for ext in ('png','pdf'):fig.savefig(OUT/f'released_directions.{ext}',dpi=170)
    plt.close(fig)


def main():
    acquisition=json.loads((OUT/'acquisition.json').read_text())
    launch=json.loads((OUT/'launch.json').read_text())
    rule=launch['direction_rule']
    head_index=defaultdict(list);head_inventory=[];head_rows_all=[];column_map=[]
    for e in acquisition['entries']:
        if not e['path'].endswith('_HEAD.FITS.gz'):continue
        real=re.search(r'-(\d{4})_HEAD',e['path']).group(1)
        source_group=e['path'].split('/')[3]
        with fits.open(e['local'],memmap=False) as hdul:
            data=hdul[1].data
            needed={'SNID','SUBSURVEY','RA','DEC','SIM_RA','SIM_DEC','SIM_LIBID','SIM_NGEN_LIBID',*TRUTH.values()}
            available=sorted(needed & set(data.dtype.names))
            dtypes={n:data.dtype.fields[n][0] for n in available}
            column_map.append({'path':e['path'],'SURVEY':hdul[0].header.get('SURVEY'),
                               'columns':[{'name':c.name,'format':str(c.format),'unit':c.unit} for c in hdul[1].columns],
                               'missing_required_binding':sorted(needed-set(available))})
            for i,h in enumerate(data):
                vals={n:h[n] for n in available}
                c={'realization':real,'path':e['path'],'row_index':i,'source_group':source_group,
                   'survey':hdul[0].header.get('SURVEY'),'values':vals,'dtypes':dtypes}
                key=(real,str(h['SNID']).strip(),int(h['SIM_LIBID']),int(h['SIM_NGEN_LIBID']))
                head_index[key].append(c);head_rows_all.append(c)
            head_inventory.append({'path':e['path'],'rows':len(data),'realization':real,'source_group':source_group})
    dump('column_map.json',{'paired_truth':TRUTH,'integer_key':['realization','literal_CID_SNID','SIM_LIBID','SIM_NGEN_LIBID'],
                            'head_files':column_map,'direction_rule':rule,
                            'precision':'half FITRES token final decimal digit plus one ULP of actual HEAD dtype; exact shared integers'})
    dump('configuration_evidence.json',configuration_evidence(acquisition))
    rows=[];schemas=[];matched_head=set();crosswalk=Counter();exclusion=Counter()
    for e in acquisition['entries']:
        if not e['path'].endswith('.FITRES.gz'):continue
        real=re.search(r'SIM_(\d{4})',e['path']).group(1)
        columns,fitrows=parse_fitres(e['local'])
        missing=sorted(set(REQUIRED+('COV_x1_c','CID','IDSURVEY','ERRFLAG_FIT','CUTFLAG_SNANA','SIM_LIBID','SIM_NGEN_LIBID'))-set(columns))
        schemas.append({'path':e['path'],'columns':columns,'rows':len(fitrows),'missing_required':missing})
        if missing:raise ValueError(f'FITRES missing structural fields: {missing}')
        for idx,(line,tokens) in enumerate(fitrows):
            key=(real,tokens['CID'],int(tokens['SIM_LIBID']),int(tokens['SIM_NGEN_LIBID']))
            candidates=head_index.get(key,[])
            status,chosen,diags=choose_candidate(tokens,candidates)
            result,bad=response(tokens);exclusion.update(bad)
            r={**tokens,'realization':real,'fitres_path':e['path'],'original_row_index':idx,'original_line_number':line,
               'join_status':status,'candidate_count':len(candidates),'candidate_diagnostics':json.dumps(diags,separators=(',',':')),
               'direction_status':'NO_UNIQUE_TRUTH_MATCH','native_ra':None,'native_dec':None,'sector':'UNAVAILABLE',**result}
            z=float(tokens['SIM_ZCMB']);r['redshift_bin']='[0,.03)' if 0<=z<.03 else '[.03,.1)' if .03<=z<.1 else '[.1,infinity)' if z>=.1 else 'OUTSIDE_PRESPECIFIED_BINS'
            if chosen:
                matched_head.add((chosen['path'],chosen['row_index']))
                r.update(head_path=chosen['path'],head_row_index=chosen['row_index'],source_group=chosen['source_group'],
                         head_survey=chosen['survey'],head_subsurvey=str(chosen['values']['SUBSURVEY']).strip(),
                         matched_sim_ra=float(chosen['values']['SIM_RA']),matched_sim_dec=float(chosen['values']['SIM_DEC']),
                         matched_native_ra=float(chosen['values']['RA']),matched_native_dec=float(chosen['values']['DEC']))
                ds,ra,dec=direction(chosen,rule);r.update(direction_status=ds,native_ra=ra,native_dec=dec)
                if ra is not None:r['sector']=f'{"N" if dec>=0 else "S"}:RA{int(ra//90)}'
                crosswalk[(chosen['source_group'],str(chosen['survey']),r['head_subsurvey'],tokens['IDSURVEY'])]+=1
            rows.append(r)
    dump('fitres_schema.json',schemas)
    all_fields=list(dict.fromkeys(k for r in rows for k in r))
    with (OUT/'rows.csv.gz').open('wb') as rawfile:
        with gzip.GzipFile(filename='',fileobj=rawfile,mode='wb',mtime=0) as zipped:
            import io
            with io.TextIOWrapper(zipped,encoding='utf-8',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=all_fields);writer.writeheader();writer.writerows(rows)
    groups={'all':summarize(rows)}
    for dimension in ('realization','IDSURVEY','redshift_bin'):
        groups[dimension]={key:summarize([r for r in rows if r[dimension]==key]) for key in sorted({r[dimension] for r in rows})}
    groups['survey_redshift']={f'{survey}|{z}':summarize([r for r in rows if r['IDSURVEY']==survey and r['redshift_bin']==z])
                                for survey in sorted({r['IDSURVEY'] for r in rows},key=int)
                                for z in ('[0,.03)','[.03,.1)','[.1,infinity)')}
    groups['realization_survey']={f'{real}|{survey}':summarize([r for r in rows if r['realization']==real and r['IDSURVEY']==survey])
                                 for real in sorted({r['realization'] for r in rows}) for survey in sorted({r['IDSURVEY'] for r in rows},key=int)}
    groups['realization_redshift']={f'{real}|{z}':summarize([r for r in rows if r['realization']==real and r['redshift_bin']==z])
                                   for real in sorted({r['realization'] for r in rows}) for z in ('[0,.03)','[.03,.1)','[.1,infinity)')}
    qualified=[r for r in rows if r['direction_status']=='QUALIFIED_NATIVE_RELEASED']
    sectors=[f'{hemi}:RA{q}' for hemi in ('S','N') for q in range(4)]
    groups['sectors']={s:summarize([r for r in qualified if r['sector']==s]) for s in sectors}
    groups['realization_sectors']={f'{real}|{s}':summarize([r for r in qualified if r['realization']==real and r['sector']==s])
                                  for real in sorted({r['realization'] for r in rows}) for s in sectors}
    ranges={m:{'min':min(v),'max':max(v)} if (v:=[g['response'][m]['median'] for g in groups['realization'].values() if g['response'][m]['median'] is not None]) else None for m in METRICS}
    sub_to_ids=defaultdict(set);ids_to_sub=defaultdict(set)
    cw=[]
    for (sg,survey,sub,ids),n in sorted(crosswalk.items()):
        cw.append({'source_group':sg,'head_SURVEY':survey,'SUBSURVEY':sub,'IDSURVEY':ids,'count':n})
        sub_to_ids[(sg,survey,sub)].add(ids);ids_to_sub[ids].add((sg,survey,sub))
    missing_surveys=[s for s,g in groups['IDSURVEY'].items() if not g['join_status'].get('UNIQUE_TRUTH_MATCH',0)]
    summary={'metadata':{'owner':'obsstat','scope':'released selected LambdaCDM/BS21 source-response diagnostic',
                         'claim_tier':'C0','status':'DIAGNOSTIC_ONLY','transfer_source':'none',
                         'null_mock_status':'SOURCE_SELECTED_RELEASE_NOT_COMPLETE_NULL_LAW','covariance_status':'WORKING_DESCRIPTIVE_ONLY',
                         'sky_support_status':'NATIVE_RELEASED_CADENCE_POSITIONS_ONLY','mB_calibration':'HOLD','H02':'HOLD','S02':'HOLD',
                         'original_nodes':'17/42 completed unchanged; all six NOT_READY_TO_SUBMIT unchanged',
                         'direction_rule':rule,'population':'released selected rows, with no extra color/stretch/probability cuts',
                         'caveats':['c_pred=SIM_c+SIM_AV/SIM_RV is source predictor, not noiseless SALT2 refit truth',
                                    'SIM_beta is not fitted beta_SALT2; mB measurement calibration HOLD',
                                    'Source/model/selection response is not exclusively measurement noise',
                                    'Realizations may share seeds/cadence/library identities; no independence or sqrt(10) error reduction',
                                    'SDSS/SNLS HEAD absent; no coordinates inferred; no complete angular selection law',
                                    'No chi-square distribution, coverage, p-values, likelihood, cosmological fit or Bianchi inference']},
             'groups':groups,'exclusion_reasons_overlapping':dict(exclusion),'head_inventory':head_inventory,
             'head_total_rows':len(head_rows_all),'head_rows_used_unique':len(matched_head),
             'head_rows_unmatched':len(head_rows_all)-len(matched_head),
             'head_unmatched_by_file':{e['path']:e['rows']-sum(p==e['path'] for p,i in matched_head) for e in head_inventory},
             'surveys_without_any_unique_match':missing_surveys,'source_groups_without_HEADERS':['SIMSDSSREAL_4D_BS20','SIMSNLSREAL_4D_BS20'],
             'crosswalk':cw,'nonunique_subsurvey_mapping':[{'source_group':key[0],'head_SURVEY':key[1],'SUBSURVEY':key[2],'IDSURVEYs':sorted(ids)} for key,ids in sub_to_ids.items() if len(ids)>1],
             'nonunique_numeric_survey_mapping':{k:[list(x) for x in sorted(v)] for k,v in ids_to_sub.items() if len(v)>1},
             'repeated_identifiers':repeated_summary(rows),'per_realization_median_range':ranges,
             'statistic_conventions':'SD ddof=1; NumPy linear percentiles; empty cells null; no clipping or error bars on medians',
             'launch_sha256':sha(OUT/'launch.json'),'contract_sha256':launch['contract_sha256'],
             'acquisition_sha256':sha(OUT/'acquisition.json')}
    dump('summary.json',summary)
    plot_results(rows,summary)
    allgroup=groups['all']
    report=f'''# Released Pantheon+ source response — finite C0 diagnostic

Owner: obsstat. Release: {acquisition['release']}. Execution source/command/environment: launch.json and execution.json. Frozen scientific interpretation: CONTRACT.md plus coordinate addendum recorded at launch. Requested executor gpt-6.1-sol/high; observed runtime UNKNOWN. Independent review pending; no publication or scientific admission follows from execution.

Parsed {len(rows)} released FITRES rows across ten realizations; {allgroup['eligible']} meet the exact flag, finite-value, error and dust requirements. Exclusions (overlapping reasons): {dict(exclusion)}. No fitted-color, stretch, FITPROB cuts, fitting, offset subtraction or clipping were used.

Joins: {allgroup['join_status']}. Candidate identity is realization, literal CID/SNID and exact SIM_LIBID/SIM_NGEN_LIBID; all sixteen shared truth fields are tested using printed token precision plus HEAD storage ULP, with exact shared integers. Reordered columns are parsed by name. Candidate disagreement details remain in rows.csv.gz. All {len(head_rows_all)} HEAD rows are counted; {len(head_rows_all)-len(matched_head)} are unused. Missing HEAD groups are SDSS/SNLS, not fabricated coordinates. Numeric surveys with no unique match: {missing_surveys}.

Directions: {allgroup['direction_status']}. Retained native coordinates use {rule}. They are released simulated cadence positions; frame/equinox/ICRS and a complete angular selection law are not asserted. Eight fixed RA-quadrant × north/south sectors are reported, including empty cells; north includes DEC=0. Sector statistics use eligible, qualified rows. Crosswalks preserve blank SUBSURVEY values alongside primary SURVEY and report nonunique mappings.

Frozen response definitions: E=SIM_AV/SIM_RV, rx=x1−SIM_x1, rc0=c−SIM_c, rc=rc0−E. The color predictor SIM_c+E comes from the generator's pre-host-dust SALT2 convention. It is not a noiseless SALT2 refit. Response includes source/model/selection effects and cannot be read as pure measurement noise. No mB residual calibration is attempted; SIM_beta is not fitted beta_SALT2. Actual commands and seeds are preserved in configuration_evidence.json; DES actual logs are absent. Generic INPUT defaults are not substituted, and LOWZ offsets are not copied to other surveys.

All-row eligible medians: E={allgroup['response']['E']['median']}, rx={allgroup['response']['rx']['median']}, rc0={allgroup['response']['rc0']['median']}, rc={allgroup['response']['rc']['median']}. See summary.json for counts, means, medians, sample SD, 16th/84th percentiles by numeric survey, truth-redshift bin, realization and fixed sector; per-realization median ranges are retained without an independence assertion or sqrt(10) uncertainty reduction.

Working covariance order is (x1,c), with reported x1ERR², cERR² and COV_x1_c. Standardized components divide responses by the corresponding reported error. The quadratic discrepancy requires 1−|rho|>1e−10, without jitter or inflation. Status counts: {allgroup['quadratic_status']}. It is descriptive only: no chi-square distribution, calibrated residual law, p-value, coverage, H02 certification or likelihood is computed. Plots show population 16–84% ranges, not uncertainty on medians; no Gaussian overlay is used.

## Claim audit and retained limits

The generated summaries and three PNG/PDF figure pairs are C0, DIAGNOSTIC_ONLY source-conditioned observational statistics. Fixture controls verify implementation behavior only. mB calibration, H02 and S02 remain HOLD; original 17/42 completed and all six NOT_READY_TO_SUBMIT remain unchanged. No cosmology fit, complete null/selection law, Bianchi geometry/family claim, posterior or evidence was produced. Separate fresh read-only Astra review is required before scoped draft publication.
'''
    (OUT/'REPORT.md').write_text(report)
    print(json.dumps({'rows':len(rows),'eligible':allgroup['eligible'],'joins':allgroup['join_status'],
                      'directions':allgroup['direction_status'],'response_medians':{m:allgroup['response'][m]['median'] for m in METRICS}},indent=2),flush=True)


if __name__=='__main__':
    main()
