"""Render cached derived envelope only; no source catalogue or fit execution."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent


def main():
    result = json.loads((HERE / 'RESULTS.json').read_text())
    rows = result['results']
    for name in ('ENVELOPE.png', 'ENVELOPE.pdf', 'REPORT.md', 'PLOT_PROVENANCE.json'):
        if (HERE / name).exists():
            raise FileExistsError(name)
    labels = [r['coordinate'].replace('_', ' ') for r in rows]
    y = np.arange(13)
    fig, axes = plt.subplots(1, 2, figsize=(12, 7), sharey=True)
    for ax, key, title, color in zip(axes, ['sigma_ref', 'sigma_envelope'],
            ['Block-diagonal working reference', 'Relaxed coordinatewise maximum'], ['#356393', '#aa5328']):
        ax.barh(y, [r[key] for r in rows], color=color)
        ax.set_title(title, fontsize=11)
        ax.set_xlabel('Square root of variance [microas/yr]')
        ax.grid(axis='x', alpha=.2)
        ax.set_axisbelow(True)
    axes[0].set_yticks(y, labels)
    axes[0].invert_yaxis()
    fig.suptitle('Gaia-CRF3: fixed working-marginal covariance envelope', fontsize=13)
    fig.text(.5, .025, 'obsstat | C0 / DIAGNOSTIC_ONLY | transfer: none | null: unavailable\n'
             'Arbitrary PSD cross-source completion; maxima may differ by coordinate.\n'
             'No joint covariance, coverage, physical-error or frame-compatibility claim.',
             ha='center', fontsize=9)
    fig.tight_layout(rect=(0, .12, 1, .94))
    fig.savefig(HERE / 'ENVELOPE.png', dpi=180)
    fig.savefig(HERE / 'ENVELOPE.pdf')
    plt.close(fig)
    provenance = {key: result[key] for key in ('owner', 'scope', 'claim_tier', 'claim_status',
        'artifact_mode', 'allowed_use', 'transfer_source', 'null_mock_status', 'covariance_status',
        'sky_support_status', 'forbidden_uses', 'caveats', 'source_commit', 'contract_sha256')}
    provenance.update(source_json='RESULTS.json', source_json_sha256=hashlib.sha256((HERE/'RESULTS.json').read_bytes()).hexdigest(),
                      generating_command='.venv/bin/python -B '+
                      str(HERE.relative_to(Path.cwd())/'bounded_run.py')+' plots',
                      renderer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with (HERE / 'PLOT_PROVENANCE.json').open('x') as out:
        json.dump(provenance, out, indent=2)
    lines = [
        '# Gaia working-marginal covariance envelope', '',
        'Owner obsstat; C0 / DIAGNOSTIC_ONLY. This is a floating-point evaluation of the analytic, '
        'coordinatewise sharp bound in the relaxed PSD completion class with fixed published 2×2 working marginals.', '',
        'The single raw pass retained all 1,614,173 sources and verified the complete XML, OK QUERY_STATUS, '
        'raw SHA256, source FD/path identity and exact row count. The existing D05 full 16-column normal matrix '
        'defines the fixed 13-coordinate Schur/frame quotient. No RHS, fit, holdout or radio calculation was rerun.', '',
        'For each coordinate k, s_ki²=ell_ki C_i ell_kiᵀ, v_ref=Σ_i s_ki² and v_max=(Σ_i s_ki)². '
        'v_ref is a block-diagonal working reference; it does not establish source independence. '
        'The displayed square roots are scales of these variances, not calibrated confidence intervals.', '',
        '| Coordinate | v_ref [microas²/yr²] | v_max [microas²/yr²] | sqrt(v_ref) [microas/yr] | sqrt(v_max) [microas/yr] | v_max/v_ref |',
        '|---|---:|---:|---:|---:|---:|',
    ]
    for row in rows:
        lines.append('| '+row['coordinate']+' | '+' | '.join(f'{row[k]:.12g}' for k in
            ('v_ref', 'v_max', 'sigma_ref', 'sigma_envelope', 'variance_ratio'))+' |')
    maximum = max(result['controls']['stream_reference_relative_error'])
    lines += ['', f'Maximum actual-stream relative working-reference difference: {maximum:.12g} '
              '(frozen limit 1e-10, atol=0). Frame annihilation maximum absolute residual: '
              f"{result['controls']['frame_annihilation_maxabs']:.12g} (limit 1e-10). "
              'Finite/parser control details are in CONTROLS.json and the create-only raw controls log. '
              'The locked NUMERICAL_USAGE.jsonl records cumulative wall time, exact commands and sampled resources.', '',
        'The 13 maxima need not be jointly attainable. Their diagonal is neither a joint covariance nor a Loewner '
        'upper bound. Compatibility with actual Gaia source/frame constraints is UNKNOWN. Published working '
        'marginal correctness after selection, missing systematic errors and bias are not resolved. Physical B1 '
        'remains UNKNOWN. There is no coverage, physical-error, cosmic-curl, vorticity, family or K03 admission.', '',
        'Plot/table metadata: artifact_mode=CONDITIONAL_RELAXED_COORDINATEWISE_ENVELOPE; allowed_use=working-marginal '
        'coordinate envelope; transfer_source=none; null_mock_status=NOT_AVAILABLE; '
        'covariance_status=fixed working marginals with arbitrary relaxed PSD completion; '
        'sky_support=selected CRF3 membership/directions fixed. Forbidden uses are joint covariance, calibrated '
        'coverage, physical error or native family identification. PLOT_PROVENANCE.json binds the figure source.', '',
        'Implementation/requested runtime: gpt-6.1-sol/high; observed model/effort UNKNOWN. '
        'Fresh independent read-only Astra review is pending. Original 17/42 and all six NOT_READY_TO_SUBMIT '
        'statuses remain unchanged.', '',
        f"Contract SHA256: `{result['contract_sha256']}`. Source SHA256: `{result['source']['sha256']}`. "
        f"Code SHA256: `{result['code_sha256']}`.", '',
        '![Derived covariance envelope](ENVELOPE.png)', '',
        'Protocol/source references (qualified in the frozen contract): '
        '[VOTable 1.4](https://www.ivoa.net/documents/VOTable/20191021/REC-VOTable-1.4-20191021.html), '
        '[TAP 1.1](https://www.ivoa.net/documents/TAP/20190927/REC-TAP-1.1.html), '
        '[DALI 1.1](https://www.ivoa.net/documents/DALI/20170517/REC-DALI-1.1.html), '
        '[Gaia-CRF3](https://arxiv.org/html/2204.12574v2).', '',
    ]
    with (HERE / 'REPORT.md').open('x') as out:
        out.write('\n'.join(lines))
    print(json.dumps({'rendered': ['ENVELOPE.png', 'ENVELOPE.pdf', 'REPORT.md', 'PLOT_PROVENANCE.json']}))


if __name__ == '__main__':
    main()
