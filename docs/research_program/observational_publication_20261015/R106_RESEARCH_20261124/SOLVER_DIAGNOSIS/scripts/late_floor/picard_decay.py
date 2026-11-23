import sys, json, numpy as np
from concurrent.futures import ProcessPoolExecutor
def solve(t):
    fam, cells = t
    import bass.transport.coupled_einstein_boltzmann as m
    from scripts.r105.native_optical_refinement import angular_basis
    out = m.solve_coupled_einstein_boltzmann(fam, m.CoupledSolverConfig(n_cells=cells, ell_max=4, n_picard=12, max_substep_depth=1.0, epsilon=2e-4, substeps_per_cell=2, record_history=True), lie_op=angular_basis(4, 16))
    its = out.history['picard_iterations']; rows = []
    for p in range(len(its)):
        h = its[p]; qs, qf = h['q_over_E_sky'][0], h['q_over_E_fluid'][0]
        rel = np.linalg.norm(qs-qf, axis=1)/np.linalg.norm(qf, axis=1)
        row = dict(it=p, final_rel=float(rel[-1]), max_rel=float(rel.max()))
        if p:
            a, b = its[p]['pi_over_E_sky'][0], its[p-1]['pi_over_E_sky'][0]
            na = np.linalg.norm(a.reshape(len(a), -1), axis=1); d = np.linalg.norm((a-b).reshape(len(a), -1), axis=1)
            row.update(global_change=float(d.max()/na.max()), local_change_max=float((d/np.maximum(na, 1e-300)).max()), local_change_final=float(d[-1]/na[-1]))
        rows.append(row)
    return dict(fam=fam, cells=cells, rows=rows, final_metric=out.picard_pi_rel_change)
if __name__ == '__main__':
    with ProcessPoolExecutor(4, max_tasks_per_child=1) as ex: res = list(ex.map(solve, [('VI_-1/9', 96), ('VI_-1/9', 192), ('VII_h', 96), ('IX', 96)]))
    json.dump(res, open(sys.argv[1], 'w'), indent=1)
    for r in res:
        print('==', r['fam'], r['cells'])
        for x in r['rows']: print('  it %2d final_rel %.2e max_rel %.2e global %.1e local_max %.1e local_final %.1e' % (x['it'], x['final_rel'], x['max_rel'], x.get('global_change', np.nan), x.get('local_change_max', np.nan), x.get('local_change_final', np.nan)))
