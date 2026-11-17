"""Full-covariance finite STF-series class witnesses for one confidence ellipsoid.

The tensor-major vector uses the orthonormal R54/R61 STF5 convention. A local
profile fit supplies a feasible upper bound, never a certified global minimum.
Only a reconstructed witness inside the supplied ellipsoid proves intersection.
Optional signed-commutator enclosures may prove numerical exclusion; otherwise
an outside nonlinear fit remains UNRESOLVED. No LRT tail or model probability
is assigned. All tensor entries have the caller's common physical units.
"""
from __future__ import annotations

import itertools

import numpy as np
from scipy import linalg, optimize
from scipy.spatial.transform import Rotation


CLASS_NAMES = (
    "ZERO", "SHARED_FRAME", "SHARED_AXIS",
    "SHARED_ZERO_EIGENVALUE_SHAPE", "SHARED_GENERAL_SHAPE",
)


def stf_basis():
    """R54/R61 orthonormal order: diagonal 1, diagonal 2, xy, xz, yz."""
    e = np.zeros((5, 3, 3))
    e[0] = np.diag([1., -1., 0.]) / np.sqrt(2.)
    e[1] = np.diag([1., 1., -2.]) / np.sqrt(6.)
    for a, (i, j) in enumerate(((0, 1), (0, 2), (1, 2)), 2):
        e[a, i, j] = e[a, j, i] = 1. / np.sqrt(2.)
    return e


def _finite_vector(value, name):
    a = np.asarray(value, dtype=float)
    if a.ndim != 1 or not a.size or not np.isfinite(a).all():
        raise ValueError(name + " must be a nonempty finite vector")
    return a


def _count(value, name, minimum=1):
    if (isinstance(value, (bool, np.bool_))
            or not isinstance(value, (int, np.integer)) or value < minimum):
        raise ValueError(name + " must be an integer >= " + str(minimum))
    return int(value)


def _carrier(mean, covariance):
    h = _finite_vector(mean, "mean")
    if h.size % 5:
        raise ValueError("mean must contain tensor-major blocks of five STF coefficients")
    v = np.asarray(covariance, dtype=float)
    if v.shape != (h.size, h.size) or not np.isfinite(v).all():
        raise ValueError("covariance must be finite and match mean")
    scale = max(float(np.max(np.abs(v))), np.finfo(float).tiny)
    if np.max(np.abs(v-v.T)) > 1e-12 * scale:
        raise ValueError("covariance must be symmetric")
    v = (v+v.T) / 2.
    try:
        ch = linalg.cholesky(v, lower=True)
    except linalg.LinAlgError as exc:
        raise ValueError("covariance must be positive definite") from exc
    return h, v, ch


def coefficients_to_tensors(coefficients):
    """Map (...,5) coefficients to (...,3,3), preserving Frobenius norm."""
    q = np.asarray(coefficients, dtype=float)
    if q.ndim == 0 or q.shape[-1] != 5 or not np.isfinite(q).all():
        raise ValueError("coefficients must be finite with final dimension five")
    return np.einsum("...a,aij->...ij", q, stf_basis())


def tensors_to_coefficients(tensors):
    t = np.asarray(tensors, dtype=float)
    if t.ndim < 2 or t.shape[-2:] != (3, 3) or not np.isfinite(t).all():
        raise ValueError("tensors must be finite with final shape (3,3)")
    scale = max(float(np.max(np.abs(t))), np.finfo(float).tiny)
    if (np.max(np.abs(t-np.swapaxes(t, -1, -2))) > 1e-12*scale
            or np.max(np.abs(np.trace(t, axis1=-2, axis2=-1))) > 1e-12*scale):
        raise ValueError("tensors must be symmetric and trace free")
    return np.einsum("...ij,aij->...a", t, stf_basis())


def _rotation(rotation):
    r = np.asarray(rotation, dtype=float)
    if (r.shape != (3, 3) or not np.isfinite(r).all()
            or np.linalg.norm(r.T@r-np.eye(3)) > 1e-10
            or abs(np.linalg.det(r)-1.) > 1e-10):
        raise ValueError("rotation must be in SO(3)")
    return r


def stf_rotation_matrix(rotation):
    """D(R)_AB = E_A : R E_B R.T; active rotations q' = D(R) q."""
    r = _rotation(rotation)
    rotated = np.einsum("ij,bjk,lk->bil", r, stf_basis(), r)
    return np.einsum("aij,bij->ab", stf_basis(), rotated)


def rotate_tensor_series(mean, covariance, rotation):
    h, v, _ = _carrier(mean, covariance)
    operator = np.kron(np.eye(h.size//5), stf_rotation_matrix(rotation))
    return dict(mean=operator@h, covariance=operator@v@operator.T, operator=operator)


def common_offset_operator(n_tensors, *, reference=0):
    """L producing K_j-K_reference, in increasing j != reference order."""
    k = _count(n_tensors, "n_tensors", 2)
    ref = _count(reference, "reference", 0)
    if ref >= k:
        raise ValueError("reference must index a tensor")
    indices = [j for j in range(k) if j != ref]
    a = np.zeros((k-1, k))
    for row, j in enumerate(indices):
        a[row, j], a[row, ref] = 1., -1.
    return np.kron(a, np.eye(5))


def common_offset_contrast(mean, covariance, *, reference=0):
    """Quotient out an arbitrary additive common STF, retaining all covariance.

    The caller supplies the confidence cutoff for this new 5(k-1)-dimensional
    carrier. No measured bound on the eliminated common calibration is implied.
    """
    h, v, _ = _carrier(mean, covariance)
    op = common_offset_operator(h.size//5, reference=reference)
    return dict(mean=op@h, covariance=op@v@op.T, operator=op,
                reference=int(reference), tensor_indices=[j for j in range(h.size//5)
                                                         if j != reference],
                dimension=int(op.shape[0]))


def _axis_shape(axis):
    u = np.asarray(axis, dtype=float)
    u = u / np.linalg.norm(u)
    return np.sqrt(1.5)*np.einsum("i,aij,j->a", u, stf_basis(), u)


def _shape_basis(class_name, orientation):
    if class_name == "SHARED_AXIS":
        return _axis_shape(orientation)[:, None]
    if class_name == "SHARED_GENERAL_SHAPE":
        return (orientation/np.linalg.norm(orientation))[:, None]
    d = stf_rotation_matrix(orientation)
    if class_name == "SHARED_FRAME":
        return d[:, :2]
    if class_name == "SHARED_ZERO_EIGENVALUE_SHAPE":
        return d[:, :1]
    raise ValueError("unknown profile class")


class _Profiler:
    def __init__(self, mean, covariance):
        self.h, self.v, self.ch = _carrier(mean, covariance)
        self.k = self.h.size//5
        self.white_h = linalg.solve_triangular(self.ch, self.h, lower=True)

    def evaluate(self, shape_basis):
        design = np.kron(np.eye(self.k), shape_basis)
        wd = linalg.solve_triangular(self.ch, design, lower=True)
        amplitudes, _, rank, _ = linalg.lstsq(wd, self.white_h, lapack_driver="gelsy")
        if rank != design.shape[1]:
            raise ArithmeticError("whitened amplitude design is numerically rank deficient")
        witness = design@amplitudes
        # Recompute the actual unwhitened residual before the triangular solve.
        residual = linalg.solve_triangular(self.ch, witness-self.h, lower=True)
        objective = float(residual@residual)
        if not np.isfinite(objective) or not np.isfinite(witness).all():
            raise ArithmeticError("nonfinite profiled witness")
        return dict(witness=witness, amplitudes=amplitudes.reshape(self.k, -1),
                    residual=residual, objective=objective,
                    amplitude_rank=int(rank),
                    amplitude_normal_residual=float(np.linalg.norm(wd.T@residual)))

    def zero(self):
        return dict(witness=np.zeros_like(self.h), amplitudes=np.zeros((self.k, 1)),
                    residual=-self.white_h, objective=float(self.white_h@self.white_h),
                    amplitude_rank=0, amplitude_normal_residual=0.)


def profile_fixed_orientation(mean, covariance, class_name, orientation):
    """Globally solve only the linear amplitudes at a supplied orientation/shape.

    SHARED_FRAME amplitudes multiply the two orthonormal diagonal basis tensors;
    the other classes have one signed amplitude per tensor. The nonlinear
    orientation is deliberately not optimized by this function.
    """
    if class_name == "ZERO":
        ans = _Profiler(mean, covariance).zero()
    else:
        o = np.asarray(orientation, dtype=float)
        expected = (3,) if class_name == "SHARED_AXIS" else (5,)
        if class_name in ("SHARED_FRAME", "SHARED_ZERO_EIGENVALUE_SHAPE"):
            o = _rotation(o)
        elif (class_name not in CLASS_NAMES or o.shape != expected
              or not np.isfinite(o).all() or np.linalg.norm(o) == 0):
            raise ValueError("invalid orientation or class")
        ans = _Profiler(mean, covariance).evaluate(_shape_basis(class_name, o))
    ans["guarantee"] = "global linear-amplitude GLS at fixed orientation only"
    return ans


def _sphere_chart(seed):
    base = np.asarray(seed, dtype=float)
    base = base/np.linalg.norm(base)
    tangent = linalg.null_space(base[None, :])

    def mapped(parameters):
        radius = float(np.linalg.norm(parameters))
        direction = np.cos(radius)*base + np.sinc(radius/np.pi)*(tangent@parameters)
        return direction / np.linalg.norm(direction)

    return mapped, base.size-1


def _proper_frame(tensor):
    _, r = linalg.eigh(tensor)
    if np.linalg.det(r) < 0:
        r[:, 0] *= -1
    return r


def _seed_pools(h, grid_size, seed):
    """Finite deterministic proposals, with data eigenframes and rank-one shapes."""
    q = h.reshape(-1, 5)
    tensors = coefficients_to_tensors(q)
    rng = np.random.default_rng(seed)
    frames = [np.eye(3)]
    axes = list(np.eye(3))
    shapes = list(np.eye(5))
    combinations = list(tensors)
    combinations += [np.einsum("k,kij->ij", weights, tensors)
                     for weights in (np.ones(len(q)), np.arange(1., len(q)+1.))]
    for t in combinations:
        r = _proper_frame(t)
        frames.append(r)
        axes.extend(r.T)
    for row in q:
        if np.linalg.norm(row):
            shapes.append(row / np.linalg.norm(row))
    _, _, vh = linalg.svd(q, full_matrices=False)
    shapes.extend(vh)
    # Permutations matter for the distinguished zero eigenvalue, but not for
    # the common-frame subspace. These exact proposals preserve zero-eigenvalue
    # hand cases for any ordering of the eigensolver's columns.
    zero_frames = []
    for r in frames:
        for order in ((0, 1, 2), (0, 2, 1), (1, 2, 0)):
            p = r[:, order].copy()
            if np.linalg.det(p) < 0:
                p[:, 0] *= -1
            zero_frames.append(p)
    for _ in range(grid_size):
        quat = rng.normal(size=4)
        frames.append(Rotation.from_quat(quat/np.linalg.norm(quat)).as_matrix())
        axes.append(rng.normal(size=3))
        shapes.append(rng.normal(size=5))
    zero_frames.extend(frames[-grid_size:] if grid_size else [])
    return dict(SHARED_FRAME=frames, SHARED_AXIS=axes,
                SHARED_GENERAL_SHAPE=shapes,
                SHARED_ZERO_EIGENVALUE_SHAPE=zero_frames)


def tensor_series_diagnostics(witness):
    q = _finite_vector(witness, "witness")
    if q.size % 5:
        raise ValueError("witness must contain STF5 blocks")
    tensors = coefficients_to_tensors(q.reshape(-1, 5))
    pairs = list(itertools.combinations(range(len(tensors)), 2))
    commutators = [tensors[i]@tensors[j]-tensors[j]@tensors[i] for i, j in pairs]
    return dict(tensors=tensors.tolist(),
                frobenius_norms=np.linalg.norm(tensors, axis=(1, 2)).tolist(),
                traces=np.trace(tensors, axis1=1, axis2=2).tolist(),
                eigenvalues=np.linalg.eigvalsh(tensors).tolist(),
                commutator_pairs=[list(pair) for pair in pairs],
                commutators=[c.tolist() for c in commutators],
                commutator_norms=[float(np.linalg.norm(c)) for c in commutators])


def _package_fit(class_name, fit, orientation, cutoff, runs, starts_evaluated):
    q = fit["witness"]
    diagnostics = tensor_series_diagnostics(q)
    if class_name == "ZERO":
        reconstruction = np.zeros_like(q)
        basis = np.empty((5, 0))
        params = dict()
    else:
        basis = _shape_basis(class_name, orientation)
        reconstruction = (fit["amplitudes"]@basis.T).ravel()
        if class_name == "SHARED_AXIS":
            params = dict(axis=(orientation/np.linalg.norm(orientation)).tolist())
        elif class_name == "SHARED_GENERAL_SHAPE":
            params = dict(shape_stf5=(orientation/np.linalg.norm(orientation)).tolist())
        else:
            params = dict(frame=orientation.tolist())
            if class_name == "SHARED_FRAME":
                diagonals = np.einsum("ka,aij->kij", fit["amplitudes"], stf_basis()[:2])
                params["frame_diagonal_eigenvalues"] = np.diagonal(diagonals, axis1=1, axis2=2).tolist()
    error = float(np.linalg.norm(q-reconstruction))
    verified = (np.isfinite(q).all() and np.isfinite(fit["objective"])
                and error <= 1e-12*max(1., float(np.linalg.norm(q))))
    if not verified:
        raise ArithmeticError("class witness failed reconstruction verification")
    objective = fit["objective"]
    status = "INTERSECTS" if objective <= cutoff else "UNRESOLVED"
    guarantee = "feasible upper bound; nonlinear global optimum unproved"
    if class_name == "ZERO":
        guarantee = "unique fixed-state objective; exact linear model in floating arithmetic"
        margin = 512*np.finfo(float).eps*max(1., abs(objective), abs(cutoff))
        if objective > cutoff+margin:
            status = "EXCLUDED"
    return dict(status=status, objective=objective,
                profile_distance_squared_upper=objective, objective_guarantee=guarantee,
                witness=q.tolist(), amplitudes=fit["amplitudes"].tolist(),
                parameters=params, shape_basis=basis.tolist(),
                witness_verified=True, reconstruction_error=error,
                amplitude_rank=fit["amplitude_rank"],
                amplitude_normal_residual=fit["amplitude_normal_residual"],
                diagnostics=diagnostics,
                optimization=dict(proposals_evaluated=starts_evaluated,
                    starts_attempted=sum(r["phase"] == "local_search" for r in runs),
                    converged_starts=sum(r["success"] for r in runs),
                    runs=runs))


def _fit_class(profiler, class_name, seeds, *, n_starts, max_nfev, cutoff):
    # Zero is in every class, so even a failed optimization has a class witness.
    fallback = np.eye(3) if class_name in ("SHARED_FRAME", "SHARED_ZERO_EIGENVALUE_SHAPE") else np.eye(3 if class_name == "SHARED_AXIS" else 5)[0]
    best = profiler.zero()
    best["amplitudes"] = np.zeros((profiler.k, 2 if class_name == "SHARED_FRAME" else 1))
    orientation = fallback
    proposals, runs = [], []
    for i, initial in enumerate(seeds):
        try:
            candidate = profiler.evaluate(_shape_basis(class_name, initial))
        except (ValueError, ArithmeticError, linalg.LinAlgError) as exc:
            runs.append(dict(success=False, phase="proposal", index=i, error=str(exc), nfev=0))
            continue
        proposals.append((candidate["objective"], i, initial, candidate))
        if candidate["objective"] < best["objective"]:
            best, orientation = candidate, initial
    proposals.sort(key=lambda item: (item[0], item[1]))
    for _, i, initial, candidate in proposals[:n_starts]:
        if class_name in ("SHARED_FRAME", "SHARED_ZERO_EIGENVALUE_SHAPE"):
            mapped = lambda x, base=initial: Rotation.from_rotvec(x).as_matrix()@base
            dimension = 3
        else:
            mapped, dimension = _sphere_chart(initial)
        def residual(parameters):
            return profiler.evaluate(_shape_basis(class_name, mapped(parameters)))["residual"]
        try:
            sol = optimize.least_squares(residual, np.zeros(dimension), method="trf",
                ftol=1e-10, xtol=1e-10, gtol=1e-10, max_nfev=max_nfev)
            fitted_orientation = mapped(sol.x)
            fitted = profiler.evaluate(_shape_basis(class_name, fitted_orientation))
            runs.append(dict(success=bool(sol.success), phase="local_search", index=i,
                status=int(sol.status), message=str(sol.message), nfev=int(sol.nfev),
                objective=float(fitted["objective"])))
            if fitted["objective"] < best["objective"]:
                best, orientation = fitted, fitted_orientation
        except (ValueError, ArithmeticError, RuntimeError, linalg.LinAlgError) as exc:
            runs.append(dict(success=False, phase="local_search", index=i, error=str(exc), nfev=0))
    if class_name in ("SHARED_AXIS", "SHARED_GENERAL_SHAPE"):
        orientation = orientation / np.linalg.norm(orientation)
    return _package_fit(class_name, best, orientation, cutoff, runs, len(seeds))


def commutator_quadratic_matrices(n_tensors):
    """Symmetric M with q.T M q = [K_i,K_j]_(a,b), a<b.

    Off-diagonal 5x5 blocks are B/2 and B.T/2, with
    B_AB = (E_A E_B - E_B E_A)_(a,b). The signed components, unlike squared
    commutator norms, are quadratic and directly usable by R61's global solver.
    """
    k = _count(n_tensors, "n_tensors")
    e = stf_basis()
    products = np.einsum("aij,bjk->abik", e, e)
    comm = products-np.swapaxes(products, 0, 1)
    answer = []
    for i, j in itertools.combinations(range(k), 2):
        for a, b in ((0, 1), (0, 2), (1, 2)):
            m = np.zeros((5*k, 5*k))
            block = comm[:, :, a, b]/2.
            m[5*i:5*i+5, 5*j:5*j+5] = block
            m[5*j:5*j+5, 5*i:5*i+5] = block.T
            answer.append(dict(pair=(i, j), component=(a, b), matrix=m))
    return answer


def commutator_ellipsoid_enclosures(mean, covariance, *, cutoff, range_solver,
                                   include_center_projection=True):
    """Use a caller-supplied R61-compatible global quadratic enclosure function.

    A projected component parallel to the center commutator supplements the
    coordinate components. Every range uses this same complete ellipsoid.
    Returned exclusions are floating primal/dual enclosures, not interval proofs.
    """
    h, v, _ = _carrier(mean, covariance)
    if not np.isfinite(cutoff) or cutoff <= 0 or not callable(range_solver):
        raise ValueError("positive cutoff and callable global range_solver required")
    forms = commutator_quadratic_matrices(h.size//5)
    if include_center_projection:
        for i in range(0, len(forms), 3):
            group = forms[i:i+3]
            direction = np.array([h@item["matrix"]@h for item in group])
            norm = np.linalg.norm(direction)
            if norm:
                direction /= norm
                forms.append(dict(pair=group[0]["pair"], component="center_projection",
                    projection=direction.tolist(), matrix=sum(direction[a]*group[a]["matrix"] for a in range(3))))
    results = []
    for form in forms:
        try:
            result = range_solver(h, v, form["matrix"], cutoff=float(cutoff))
            lo, hi = float(result["lower"]), float(result["upper"])
            if not np.isfinite([lo, hi]).all() or lo > hi:
                raise ArithmeticError("invalid quadratic enclosure endpoints")
            entry = dict(pair=list(form["pair"]), component=form["component"],
                lower=lo, upper=hi, excludes_zero=bool(lo > 0 or hi < 0),
                enclosure=result, status="COMPUTED")
            if "projection" in form:
                entry["projection"] = form["projection"]
            results.append(entry)
        except (ValueError, ArithmeticError, RuntimeError, linalg.LinAlgError) as exc:
            results.append(dict(pair=list(form["pair"]), component=form["component"],
                excludes_zero=False, status="UNRESOLVED", error=str(exc)))
    return dict(excludes_commuting_class=any(x["excludes_zero"] for x in results),
                ranges=results, cutoff=float(cutoff),
                guarantee="numerical global quadratic enclosures supplied by range_solver")


def classify_tensor_series(mean, covariance, cutoff, *, n_starts=10, grid_size=64,
                           max_nfev=180, seed=620017, commutator_solver=None):
    """Classify a 1--4 tensor STF series against one caller-declared ellipsoid.

    ``cutoff`` is the squared Mahalanobis threshold of the *carrier*, not a
    class-specific Wilks threshold. Signed amplitudes and zero states are kept.
    Local solver failure does not establish exclusion. A witness whose directly
    reconstructed objective is <= cutoff is INTERSECTS. Outside nonlinear fits
    remain UNRESOLVED unless a valid necessary commutator enclosure excludes.
    """
    profiler = _Profiler(mean, covariance)
    if profiler.k > 4:
        raise ValueError("bounded R62 profile implementation supports at most four tensors")
    if not np.isscalar(cutoff) or not np.isfinite(cutoff) or cutoff < 0:
        raise ValueError("cutoff must be finite and nonnegative")
    if cutoff == 0 and commutator_solver is not None:
        raise ValueError("the optional R61 enclosure solver requires a positive cutoff")
    n_starts = _count(n_starts, "n_starts", 0)
    grid_size = _count(grid_size, "grid_size", 0)
    max_nfev = _count(max_nfev, "max_nfev")
    seed = _count(seed, "seed", 0)
    pools = _seed_pools(profiler.h, grid_size, seed)
    results = {"ZERO": _package_fit("ZERO", profiler.zero(), None, cutoff, [], 1)}
    # Nested-class candidates seed the larger classes; this does not certify
    # a nonlinear optimum. Extra eigenframes transport an arbitrary shared shape.
    for name in ("SHARED_AXIS", "SHARED_ZERO_EIGENVALUE_SHAPE",
                 "SHARED_GENERAL_SHAPE", "SHARED_FRAME"):
        if name == "SHARED_GENERAL_SHAPE":
            pools[name].extend(np.asarray(results[x]["shape_basis"])[:, 0]
                for x in ("SHARED_AXIS", "SHARED_ZERO_EIGENVALUE_SHAPE"))
        if name == "SHARED_FRAME":
            for x in ("SHARED_AXIS", "SHARED_ZERO_EIGENVALUE_SHAPE", "SHARED_GENERAL_SHAPE"):
                shape = np.asarray(results[x]["shape_basis"])[:, 0]
                pools[name].append(_proper_frame(coefficients_to_tensors(shape)))
        results[name] = _fit_class(profiler, name, pools[name],
            n_starts=n_starts, max_nfev=max_nfev, cutoff=float(cutoff))
    enclosures = None
    if commutator_solver is not None:
        enclosures = commutator_ellipsoid_enclosures(profiler.h, profiler.v,
            cutoff=cutoff, range_solver=commutator_solver)
        if enclosures["excludes_commuting_class"]:
            for result in results.values():
                if result["status"] == "INTERSECTS":
                    raise ArithmeticError("commutator enclosure contradicts a feasible class witness")
                result["status"] = "EXCLUDED"
                result["exclusion_reason"] = "signed commutator numerical enclosure excludes zero"
    return dict(classes={name: results[name] for name in CLASS_NAMES},
        dimension=int(profiler.h.size), n_tensors=profiler.k, cutoff=float(cutoff),
        basis_order="R54_R61_orthonormal_STF5: diag1, diag2, xy, xz, yz",
        mean_diagnostics=tensor_series_diagnostics(profiler.h),
        covariance_condition_number=float(np.linalg.cond(profiler.v)),
        optimizer_config=dict(n_starts=n_starts, grid_size=grid_size,
            max_nfev=max_nfev, seed=seed, method="variable_projection_least_squares"),
        commutator_enclosures=enclosures,
        interpretation="set intersection with one supplied joint ellipsoid; no model probabilities or Wilks tails")
