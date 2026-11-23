import healpy as hp
import numpy as np
import pytest

from scripts.r105.commander_transfer import chunk_terms, design, fit_vectors, ranks, read_column


@pytest.mark.parametrize("sign", [-1, 1])
def test_independent_spin_synthesis_and_masked_recovery(sign):
    ns = 16
    pix = np.arange(hp.nside2npix(ns))
    theta, phi = hp.pix2ang(ns, pix)
    beam = np.array([0.83, 0.61])
    t, p = design(theta, phi, beam)
    rng = np.random.default_rng(5105)
    coeff = sign * rng.normal(size=(3, 5))
    alm = np.zeros((3, hp.Alm.getsize(2)), complex)
    for j in range(3):
        alm[j, hp.Alm.getidx(2, 2, 0)] = coeff[j,0]
        for m in (1, 2):
            alm[j,hp.Alm.getidx(2,2,m)] = (coeff[j,2*m-1] - 1j*coeff[j,2*m]) / np.sqrt(2)
        alm[j] *= beam[0 if j == 0 else 1]
    sky = hp.alm2map(alm, ns, lmax=2)
    sky[0] += 2.5 + np.sin(theta)*np.cos(phi) - 4.3*np.cos(theta)
    mask_t = (np.cos(theta) > -0.73) & (np.sin(phi) < 0.92)
    mask_p = (np.cos(theta) < 0.65) & (np.cos(phi) < 0.83)
    g_t, r_t = chunk_terms(t, sky[0], mask_t)
    g_p, r_p = chunk_terms(p, sky[1]+1j*sky[2], mask_p)
    fit = fit_vectors([g_t,g_p],[r_t,r_p])
    np.testing.assert_allclose(fit, coeff, rtol=2e-13, atol=3e-13)


def test_mc_ties_order_and_bintable_gather():
    stats = ranks([3,1,0], [[2,1,0],[1,2,0]])
    assert stats["upper_ge_count"] == [0,2,2]
    assert stats["one_sided_plus_one_ranks"] == [1/3, 1, 1]
    with pytest.raises(ValueError):
        ranks([1], [])
    x=np.arange(60).reshape(10, 2, 3)[:,1,:]
    np.testing.assert_array_equal(read_column(x,np.array([15,1,5])),x.flatten()[[15,1,5]])
    with pytest.raises(ValueError,match="Invalid data"):
        chunk_terms(np.ones((3,2)),np.array([0-1.6375e30j,1,1]),np.ones(3,bool))


def test_merge_deduplicates_and_rejects_conflicts():
    from copy import deepcopy
    from scripts.r105.commander_ensemble import merge

    coeff = np.ones((3,5)).tolist()
    blank = {"fit_uK": np.zeros((3,5)).tolist()}
    one = {"fit_uK": coeff}
    row = {"schema":"r105.commander.galactic.real_l2_masked_fit.v1", "code_sha256":"abc",
           "healpy":"1.19.0","real_basis":[],"field_order":["T","E","B"],"ell":2,"nside":2048,
           "net_response_TP":[1,1],"kept_fraction_TP":[0.7,0.8],"observed":one,
           "input_sha256_and_bytes":{k:{"sha256":k} for k in ("observed","temperature_mask","polarization_mask")},
           "realizations":{"00000":{"signal":one,"noise":blank,"paired":one}}}
    for kind in ("cmb","noise"):
        row["input_sha256_and_bytes"][f"{kind}_00000"] = {
            "filename":f"dx12_v3_commander_{kind}_mc_00000_raw.fits","sha256":kind}
    assert merge([row,row])["rank"]["n_pairs"] == 1
    changed = deepcopy(row)
    changed["input_sha256_and_bytes"]["noise_00000"]["sha256"] = "new"
    with pytest.raises(ValueError, match="Conflicting duplicate"):
        merge([row,changed])
    changed = deepcopy(row)
    changed["net_response_TP"][0]=0.9
    with pytest.raises(ValueError, match="Incompatible observation"):
        merge([row,changed])


def test_budget_preflight_before_any_download(tmp_path, monkeypatch):
    from scripts.r105 import commander_ensemble as ce
    import sys
    monkeypatch.setattr(sys,"argv",["batch","batch","--start","0","--stop","2",
                        "--root",str(tmp_path),"--directory",str(tmp_path/"out"),
                        "--max-download-bytes",str(3 * ce.COMMANDER_SIZE)])
    with pytest.raises(SystemExit) as exc:
        ce.main()
    assert exc.value.code == 2 and not (tmp_path/"out").exists()
