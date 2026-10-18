"""All 104 cached scalar envelopes; plots are not confidence error bars."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from envelope import HERE, digest, require


def main():
    data=json.loads((HERE/'RESULTS.json').read_text())
    rows=data['results'];require(len(rows)==104,'Incomplete cached plot input')
    labels=data['retained_order']
    fig,axes=plt.subplots(2,2,figsize=(17,13),layout='constrained')
    values=[]
    for col in range(2):
        for j,(key,title,units) in enumerate([
            ('sqrt_vmax_uasyr','Sharp coordinatewise SD envelope','microarcsec/year'),
            ('sqrt_vmax_over_vwork','Envelope / working SD','dimensionless')]):
            a=np.array([[rows[(col*4+c)*13+k][key] for c in range(4)] for k in range(13)])
            require(np.all(np.isfinite(a)),'Nonfinite plot input')
            ax=axes[j,col]
            im=ax.imshow(a,aspect='auto',cmap='viridis')
            fig.colorbar(im,ax=ax,label=units,shrink=.88)
            ax.set_xticks(range(4),['−0.9','−0.5','+0.5','+0.9'])
            ax.set_yticks(range(13),labels)
            ax.set_xlabel('Working rho defining the estimator')
            ax.set_title(('Tangent pmRA' if col==0 else 'Coordinate-rate pmRA')+'\n'+title)
            midpoint=(a.min()+a.max())/2
            for (r,c),v in np.ndenumerate(a):
                ax.text(c,r,f'{v:.2f}',ha='center',va='center',fontsize=9,
                        color='white' if v<midpoint else 'black')
            values.append(dict(column=col,key=key,values=a.tolist()))
    fig.suptitle('Radio: conditional scalar-marginal PSD covariance envelopes\n713 sources · 8 fixed maps · 13 retained coordinates · C0 diagnostic only',fontsize=16)
    fig.supxlabel('Working marginal errors assumed; unknown bias/frame constraints. Coordinate maxima need not be jointly attained. Not confidence limits.',fontsize=11)
    for ext in ('png','pdf'):
        fig.savefig(HERE/('ENVELOPE.'+ext),dpi=170)
    plt.close(fig)
    prov={key:data[key] for key in ('owner','claim_tier','artifact_mode','allowed_use',
        'transfer_source','null_status','covariance_status','forbidden_uses','scope','sky_support_status')}
    prov.update(source_results_sha256=digest(HERE/'RESULTS.json'),
        source_identities=data['source_identity'],code_sha256=digest(HERE/'plot_report.py'),
        generating_command='.venv/bin/python -B '+str(HERE/'bounded_run.py')+' plots',
        matrices=values,outputs={ext:dict(sha256=digest(HERE/('ENVELOPE.'+ext)),
            bytes=(HERE/('ENVELOPE.'+ext)).stat().st_size) for ext in ('png','pdf')})
    (HERE/'PLOT_PROVENANCE.json').write_text(json.dumps(prov,indent=2,allow_nan=False)+'\n')
    vmax=[r['sqrt_vmax_uasyr'] for r in rows];rat=[r['sqrt_vmax_over_vwork'] for r in rows]
    checks=data['scenarios']
    report=f'''# Radio conditional scalar covariance envelope

Executed the one authorized 713-row pass for all eight frozen D05 maps:
104 scalar coordinate maxima, with all focused controls passing beforehand.
Independent fresh read-only Astra review remains PENDING.

The conditional SD envelopes span {min(vmax):.6g} to {max(vmax):.6g} microarcsec/year;
their ratios to the old working SD span {min(rat):.6g} to {max(rat):.6g}.
All 104 values and all eight newly accumulated normal matrices are in RESULTS.json.
PNG and PDF show every coordinate in the fixed scenario order, with separate
units for envelope magnitude and the dimensionless working-reference ratio.

For flattened scalar marginals, PSD implies |Sigma_ab| <= sigma_a sigma_b.
Therefore ell Sigma ell^T <= (sum |ell_a| sigma_a)^2. The rank-one covariance
u u^T, u_a = sigma_a sign(ell_a), attains this maximum for each coordinate
separately; either sign is allowed at zero weight. Positive-definite restriction
has the same supremum, by approaching this witness with a diagonal mixture.
This scalar-marginal result differs from the earlier Gaia fixed-block question.

The estimator map uses the full 16-column cached covariance before selecting the
13 retained coordinates. The frame quotient leaves physical B1 UNKNOWN.
Maximum |V N - I|: {max(s['checks']['VN_max_abs'] for s in checks):.6g}.
Maximum |sum L_i X_i - R|: {max(s['checks']['LX_minus_R_max_abs'] for s in checks):.6g}.
Maximum relative working-variance residual: {max(s['checks']['working_relative_residual_max'] for s in checks):.6g}.
Motion errors are already microarcsec/year, without factors 15 or 1000.
The position RA hour conversion alone uses 15 degrees/hour. Released J2000
directions refer to the most recent VLBA observing epoch; no propagation occurred.

Owner obsstat; claim tier C0; DIAGNOSTIC_ONLY; transfer source none.
True joint covariance and empirical null are UNKNOWN/NOT_AVAILABLE.
Working rho defines each fixed map, not a restriction on the true correlations.
Published marginal errors are a working hypothesis for this selected catalogue.
Bias is unmeasured: these are centered-variance envelopes, not MSE bounds.
Frame/NNR constraints may exclude the maximizing covariance. Coordinate maxima
need not be jointly attained and their diagonal is neither a joint covariance
nor a Loewner upper bound. Neither RA interpretation is preferred or resolved.
These are not confidence error bars or coverage statements. No p-value,
Gaia-radio independence, cosmic curl, matter vorticity, native solver, family
identification or K03 admission follows. Original 17/42 and all six
NOT_READY_TO_SUBMIT states remain unchanged.

Sources, hashes, method, environment and rows are bound in RESULTS.json;
plot hashes and plotted matrices are in PLOT_PROVENANCE.json. No source rows,
motions, RHS, fitted coefficients, holdouts or row-level weights are stored here.
Requested author gpt-6.1-sol/high; observed model/effort UNKNOWN.
NUMERICAL_USAGE.jsonl records every numerical command, resource samples, exit
and cumulative wall time, including this cached plot step; the fixed cap is 60s.

Claim audit: only conditional scalar variance maxima are asserted, supported by
focused controls and the generated artifact. No scientific status promotion or
permanent claim-ledger update is made. Source failure, invalid rows, map failure,
nonfinite values or resource exhaustion require STOP/HOLD under CONTRACT.md.
'''
    (HERE/'REPORT.md').write_text(report)
    print(json.dumps(dict(status='PLOTS_AND_REPORT_WRITTEN',rows=104,source_replay=False,
        outputs=prov['outputs'],SD_range=[min(vmax),max(vmax)],ratio_range=[min(rat),max(rat)])),flush=True)


if __name__=='__main__':
    main()
