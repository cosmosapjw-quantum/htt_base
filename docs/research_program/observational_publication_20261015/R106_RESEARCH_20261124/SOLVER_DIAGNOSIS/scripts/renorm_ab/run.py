import sys, json, time, importlib.util, numpy as np
from concurrent.futures import ProcessPoolExecutor
def load(path):
    import bass.transport.coupled_einstein_boltzmann as live
    if path == 'live': return live
    spec = importlib.util.spec_from_file_location('cb_raw_variant', path); m = importlib.util.module_from_spec(spec)
    sys.modules['cb_raw_variant'] = m; spec.loader.exec_module(m); m.HYREC_REF_CSV = live.HYREC_REF_CSV; return m
def solve(t):
    path, lr, cells = t
    from scripts.r105.common_time_moments import nested_samples
    from scripts.r105.native_optical_refinement import angular_basis
    m = load(path)
    cfg = m.CoupledSolverConfig(n_cells=cells, ell_max=4, n_picard=4, max_substep_depth=1.0, epsilon=2e-4, substeps_per_cell=2,
                                record_history=True, stage_rate_collision=True, max_substep_log_rate=lr)
    out = m.solve_coupled_einstein_boltzmann('VI_-1/9', cfg, lie_op=angular_basis(4, 16))
    h = out.history['picard_iterations'][-1]; common = h['N_end'][cells//48-1::cells//48]
    s = nested_samples(common, h['N_end'], h['q_over_E_sky'][0], h['q_over_E_fluid'][0]); rel = np.array([x['relative_norm'] for x in s])
    i = 2 + int(rel[2:].argmax())
    return dict(variant='raw' if path!='live' else 'renorm', lr=lr, cells=cells, first2=rel[:2].tolist(), max2=float(rel[2:].max()), argmax_ln_a=float(common[i]),
                med2=float(np.median(rel[2:])), C2={c: float(out.cl_final[c][2]) for c in 'TEB'}, sub=int(np.sum(h['photon_substeps'])))
if __name__ == '__main__':
    raw = sys.argv[1]
    tasks = [(p, lr, c) for p in (raw, 'live') for lr in (None, 0.25) for c in (48, 96, 192, 384)]
    with ProcessPoolExecutor(12, max_tasks_per_child=1) as ex: res = list(ex.map(solve, tasks))
    json.dump(res, open(sys.argv[2], 'w'), indent=1)
    for r in res: print(r['variant'], r['lr'], r['cells'], 'sub', r['sub'], 'first2 %.2e %.2e' % tuple(r['first2']), 'max2 %.2e @ %.3f med %.2e' % (r['max2'], r['argmax_ln_a'], r['med2']), 'C2E %.6e' % r['C2']['E'])
