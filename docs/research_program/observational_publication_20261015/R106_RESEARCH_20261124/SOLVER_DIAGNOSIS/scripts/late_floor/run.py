import sys, json, numpy as np
from concurrent.futures import ProcessPoolExecutor
def solve(t):
    fam, ell, pic, cells, eps = t
    import bass.transport.coupled_einstein_boltzmann as m
    from scripts.r105.native_optical_refinement import angular_basis
    cfg = m.CoupledSolverConfig(n_cells=cells, ell_max=ell, n_picard=pic, max_substep_depth=1.0, epsilon=eps, substeps_per_cell=2, record_history=True)
    out = m.solve_coupled_einstein_boltzmann(fam, cfg, lie_op=angular_basis(ell, max(16, ell+8)))
    h = out.history['picard_iterations'][-1]; qs, qf = h['q_over_E_sky'][0], h['q_over_E_fluid'][0]
    rel = np.linalg.norm(qs-qf, axis=1)/np.linalg.norm(qf, axis=1)
    k = cells//48; idx = np.arange(1, 49)*k - 1
    d = qs[-1]-qf[-1]; par = float(d@qf[-1]/(qf[-1]@qf[-1]))
    return dict(fam=fam, ell=ell, pic=pic, cells=cells, eps=eps, final_rel=float(rel[-1]), final_signed_par=par,
                common_rel_at=[float(rel[i]) for i in idx[[10, 20, 30, 40, 47]]], common_ln_a=[float(h['N_end'][i]) for i in idx[[10, 20, 30, 40, 47]]],
                pic_change=out.picard_pi_rel_change)
if __name__ == '__main__':
    tasks = [('VI_-1/9', l, p, c, 2e-4) for (l, p) in ((4, 4), (6, 4), (8, 4), (4, 8)) for c in (192, 384)]
    tasks += [(f, 4, 4, c, 2e-4) for f in ('IX', 'VII_h') for c in (192, 384)]
    tasks += [('VI_-1/9', 4, 4, c, 1e-4) for c in (192, 384)]
    with ProcessPoolExecutor(14, max_tasks_per_child=1) as ex: res = list(ex.map(solve, tasks))
    json.dump(res, open(sys.argv[1], 'w'), indent=1)
    for r in res: print(r['fam'], 'ell', r['ell'], 'pic', r['pic'], 'eps', r['eps'], r['cells'], 'final %.3e par %+.3e' % (r['final_rel'], r['final_signed_par']), 'at lna', ['%.2f:%.1e' % (a, b) for a, b in zip(r['common_ln_a'], r['common_rel_at'])])
