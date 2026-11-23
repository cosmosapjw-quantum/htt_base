"""Build variant/coupled_stage_rate.py from the repo solver with asserted single-occurrence patches.
RATE_MODE (module global): 'frozen' = R105 (rate=depth/h at both stages), 'stage' = instantaneous
opacity rate at the same SDIRK stage times as the baryon velocity, 'stage_norm' = stage shape rescaled
so that the SDIRK(2,2) b-weighted rate reproduces the exact substep depth."""
import hashlib, pathlib, sys
repo = pathlib.Path("/home/cosmosapjw/Dropbox/bianchi/htt_base/htt/bass/transport/coupled_einstein_boltzmann.py")
src = repo.read_text()
def sub(old, new):
    global src
    assert src.count(old) == 1, (src.count(old), old[:80])
    src = src.replace(old, new)
sub('''def _advance_moving_photon_cell(op, state, delta_N, geometry, shear_source, sub_depths,
                                baryon_velocity_at, *, sub_edges=None):''',
'''RATE_MODE = "frozen"


def _advance_moving_photon_cell(op, state, delta_N, geometry, shear_source, sub_depths,
                                baryon_velocity_at, *, sub_edges=None, rate_at=None):''')
sub('''        h = edges[j+1]-edges[j]
        rate = float(depth) / h
        stages = []
        for c in (gamma, 1.0):
            v = np.asarray(baryon_velocity_at(edges[j] + c * h), dtype=np.float64)
            inc = gamma * h * shear_source
            if rate > 0.0 and np.any(v):
                moving = MovingCollisionStage(op, v)
                solve = moving.factor_sdirk_stage(m_total, gamma * h, rate)
                inc = inc + gamma * float(depth) * moving.emission''',
'''        h = edges[j+1]-edges[j]
        if RATE_MODE == "frozen" or rate_at is None:
            stage_rates = (float(depth) / h, float(depth) / h)
        else:
            stage_rates = tuple(float(rate_at(edges[j] + c * h)) for c in (gamma, 1.0))
            if RATE_MODE == "stage_norm":
                quad = h * ((1.0 - gamma) * stage_rates[0] + gamma * stage_rates[1])
                if quad > 0.0:
                    stage_rates = tuple(r * float(depth) / quad for r in stage_rates)
            elif RATE_MODE != "stage":
                raise ValueError(RATE_MODE)
        stages = []
        for c, rate in zip((gamma, 1.0), stage_rates):
            v = np.asarray(baryon_velocity_at(edges[j] + c * h), dtype=np.float64)
            inc = gamma * h * shear_source
            if rate > 0.0 and np.any(v):
                moving = MovingCollisionStage(op, v)
                solve = moving.factor_sdirk_stage(m_total, gamma * h, rate)
                stage_depth = float(depth) if RATE_MODE == "frozen" or rate_at is None else h * rate
                inc = inc + gamma * stage_depth * moving.emission''')
sub('''                S_vec = _advance_moving_photon_cell(op_lie, S_vec, dN_cell, geom, src_vec,
                                                    sub_depths, _baryon_velocity_at, sub_edges=u_edges)''',
'''                def _rate_at(u, n0=n0, dn=dN_cell):
                    return dn * float(opacity.rate(min(n0 + u * dn, float(N_eval[i1]))))

                S_vec = _advance_moving_photon_cell(op_lie, S_vec, dN_cell, geom, src_vec,
                                                    sub_depths, _baryon_velocity_at, sub_edges=u_edges,
                                                    rate_at=_rate_at)''')
out = pathlib.Path(sys.argv[1]); out.write_text(src)
print("repo", hashlib.sha256(repo.read_bytes()).hexdigest(), "variant", hashlib.sha256(src.encode()).hexdigest())
