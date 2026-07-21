# PR-175 Sage+Singular axis: QQ Koszul chain vs external anchor.
# Independent EXECUTION engine transliterating the same registered formula
# lineage as the SymPy axis (disclosed); the algorithmically independent
# cross-check is Engine B (coordinate/complex-step) plus the external
# anchor. No family ranking or identification.
import json

TYPES = {
    "I": ((0, 0, 0), 0), "II": ((1, 0, 0), 0), "VI_0": ((1, -1, 0), 0),
    "VII_0": ((1, 1, 0), 0), "VIII": ((1, 1, -1), 0), "IX": ((1, 1, 1), 0),
    "V": ((0, 0, 0), 1), "IV": ((0, 0, 1), 1), "III": ((0, 1, -1), 1),
    "VI_h": ((0, 1, -1), QQ(1) / 2), "VII_h": ((0, 1, 1), QQ(1) / 2),
}
H_PARAMS = {"VI_h": QQ(-1) / 4, "VII_h": QQ(1) / 4}


def eps(i, j, k):
    return QQ((i - j) * (j - k) * (k - i)) / 2


def structure(nvec, a):
    n = [QQ(v) for v in nvec]
    avec = [QQ(a), QQ(0), QQ(0)]
    C = [[[QQ(0)] * 3 for _ in range(3)] for _ in range(3)]
    for A in range(3):
        for b in range(3):
            for c in range(3):
                val = eps(b, c, A) * n[A]  # diagonal n: eps_{bcd} n^{dA}
                val += avec[b] * (1 if A == c else 0)
                val -= avec[c] * (1 if A == b else 0)
                C[A][b][c] = val
    return C


def ricci_scalar(nvec, a):
    C = structure(nvec, a)
    G = [[[QQ(1) / 2 * (C[c][x][b] - C[x][b][c] + C[b][c][x])
           for b in range(3)] for x in range(3)] for c in range(3)]
    total = QQ(0)
    for b in range(3):
        for c in range(3):
            if b != c:
                continue
            for A in range(3):
                for e in range(3):
                    total += G[e][b][c] * G[A][A][e]
                    total -= G[e][A][c] * G[A][b][e]
                    total -= C[e][A][b] * G[A][e][c]
    return total


def anchor(nvec, a):
    n1, n2, n3 = (QQ(v) for v in nvec)
    return (-QQ(1) / 2 * (n1**2 + n2**2 + n3**2)
            + (n1 * n2 + n2 * n3 + n3 * n1) - 6 * QQ(a) ** 2)


computed = {}
anchor_ok = True
for name, (nvec, a) in TYPES.items():
    exact = ricci_scalar(nvec, a)
    anchor_ok = anchor_ok and (exact == anchor(nvec, a))
    computed["R_" + name] = str(exact)

# Class-B constraint DERIVED from constructed C: reconstruct n (symmetric
# part) and a-vector, require a.n = 0 and the Jacobi identity per type.
class_b_ok = True
for name, (nvec, a) in TYPES.items():
    C = structure(nvec, a)
    n_rec = matrix(QQ, 3, 3, lambda A, b: QQ(1) / 2 * sum(
        eps(b, c, d) * C[A][c][d] for c in range(3) for d in range(3)))
    n_sym = (n_rec + n_rec.transpose()) / 2
    a_rec = [QQ(1) / 2 * sum(C[d][d][b] for d in range(3)) for b in range(3)]
    a_dot_n = [sum(a_rec[b] * n_sym[b, A] for b in range(3)) for A in range(3)]
    class_b_ok = class_b_ok and all(v == 0 for v in a_dot_n)
    for A in range(3):
        for b in range(3):
            for c in range(3):
                for d in range(3):
                    cyc = sum(C[e][b][c] * C[A][d][e] + C[e][c][d] * C[A][b][e]
                              + C[e][d][b] * C[A][c][e] for e in range(3))
                    class_b_ok = class_b_ok and (cyc == 0)
h_ok = True
for name, h in H_PARAMS.items():
    nvec, a = TYPES[name]
    n2, n3 = QQ(nvec[1]), QQ(nvec[2])
    h_ok = h_ok and (QQ(a) ** 2 == abs(h) * abs(n2 * n3)) and (
        (h > 0) == (n2 * n3 > 0)
    )

checks = {
    "eleven_type_ricci_scalar_matches_anchor": bool(anchor_ok),
    "class_b_vector_constraint_a_dot_n_zero": bool(class_b_ok),
    "vi_vii_h_relation_consistent": bool(h_ok),
}
singular_version = singular.eval('system("version");')
payload = {
    "all_pass": all(checks.values()),
    "checks": checks,
    "computed": computed,
    "sage_version": str(version()),
    "singular_version": str(singular_version).strip(),
}
print(json.dumps(payload, sort_keys=True))
