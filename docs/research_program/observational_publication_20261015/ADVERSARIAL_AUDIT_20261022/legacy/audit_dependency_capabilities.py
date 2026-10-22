"""Read-only DAG blocker audit + exact nonradial response counterexample.

Outputs an audit view, never changes acceptance or scientific node states.
The six-direction example is an algebraic capability, not an observed sky.
"""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path


def exact_rank(rows):
    a = [[Fraction(v) for v in row] for row in rows]
    r = 0
    for j in range(len(a[0])):
        pivot = next((i for i in range(r, len(a)) if a[i][j]), None)
        if pivot is None:
            continue
        a[r], a[pivot] = a[pivot], a[r]
        q = a[r][j]
        a[r] = [v/q for v in a[r]]
        for i in range(len(a)):
            if i != r:
                q = a[i][j]
                a[i] = [v-q*w for v,w in zip(a[i],a[r])]
        r += 1
        if r == len(a):
            break
    return r


def nonradial_counterexample():
    # mu(n)=(I-n n^T)g + Omega cross n, g=a_obs/c; observer acceleration, not cosmic-congruence A_a.
    directions = [[s if i == j else 0 for i in range(3)]
                  for j in range(3) for s in (1,-1)]
    rows, radial = [], []
    for n in directions:
        x,y,z = n
        p = [[int(i==j)-n[i]*n[j] for j in range(3)] for i in range(3)]
        # Omega cross n = -[n]_cross Omega.
        b = [[0,z,-y],[-z,0,x],[y,-x,0]]
        block = [p[i]+b[i] for i in range(3)]
        rows.extend(block)
        radial.append([sum(n[i]*block[i][j] for i in range(3)) for j in range(6)])
    gram = [[sum(row[i]*row[j] for row in rows) for j in range(6)] for i in range(6)]
    assert gram == [[4*int(i==j) for j in range(6)] for i in range(6)]
    assert exact_rank(rows) == 6 and exact_rank(radial) == 0
    return dict(kind="EXACT_SYNTHETIC_CAPABILITY_NOT_OBSERVATIONAL_ACCEPTANCE",
                direction_set=directions, parameters=["g_x","g_y","g_z","Omega_x","Omega_y","Omega_z"],
                response="mu(n)=(I-n*n^T)*(a_obs/c)+Omega cross n",
                response_rank=6, radial_response_rank=0, gram=gram,
                covariance_if_cartesian_noise_is_sigma2_identity="sigma2/4 I_6",
                real_source_obligations=["published proper-motion/vector-harmonic coefficient identity and covariance", "frame/NNR and source population qualification", "response sign, epoch, acceleration convention and systematic scope"],
                no_dependency_on=["H02 CF4 selection law", "B02 Bianchi atlas", "L03 Planck morphology null"],
                original_node_completion=False,
                original_K03_state="pending",
                acceleration_semantics="a_obs is observer acceleration; not cosmic-congruence A_a")


def audit(path):
    raw = Path(path).read_bytes()
    dag = json.loads(raw)
    nodes = {n['id']:n for n in dag['nodes']}
    if len(nodes) != len(dag['nodes']):
        raise ValueError('duplicate node IDs')
    memo = {}
    def ancestors(k,active=()):
        if k in active:
            raise ValueError('dependency cycle: '+','.join(active+(k,)))
        if k not in memo:
            memo[k] = set()
            for dep in nodes[k]['depends_on']:
                memo[k].add(dep)
                memo[k].update(ancestors(dep,active+(k,)))
        return memo[k]
    pending = [n for n in nodes.values() if n['state'] != 'completed_scoped']
    external = {k for k,n in nodes.items() if n.get('external_missing')}
    frontier, closures = [], []
    for n in pending:
        unmet = [k for k in n['depends_on'] if nodes[k]['state'] != 'completed_scoped']
        own = n['id'] in external
        upstream = sorted((ancestors(n['id']) | {n['id']}) & external)
        row = dict(id=n['id'],state=n['state'],unmet_dependencies=unmet,
                   own_external_missing=n.get('external_missing',[]),
                   transitive_external_blockers=upstream)
        closures.append(row)
        if not unmet:
            frontier.append(row)
    impact = {k:sorted(n['id'] for n in pending if k == n['id'] or k in ancestors(n['id'])) for k in sorted(external)}
    return dict(schema="htt.read_only_node_capability_audit/1", input_sha256=hashlib.sha256(raw).hexdigest(),
                states=dict(Counter(n['state'] for n in nodes.values())),
                completed_ids=[n['id'] for n in nodes.values() if n['state']=='completed_scoped'],
                scientifically_ready_ids=[n['id'] for n in frontier if not n['own_external_missing']],
                dependency_frontier=frontier, transitive_blocker_closure=closures,
                external_blocker_impact=impact,
                nonradial_counterexample=nonradial_counterexample(),
                changes_to_original_acceptances=False,
                requested_runtime="gpt-6.1-sol/high",observed_runtime="UNKNOWN")

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dag')
    parser.add_argument('--output')
    args=parser.parse_args()
    result=json.dumps(audit(args.dag),indent=2)+"\n"
    if args.output:
        Path(args.output).write_text(result)
    else:
        print(result,end='')
