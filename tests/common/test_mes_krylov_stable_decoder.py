from __future__ import annotations

import importlib.util
from itertools import permutations
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "mes_krylov_stable_decoder_under_test",
    ROOT / "htt/src/common/mes_krylov_completion.py",
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


def test_forward_packet_inverse_is_admitted_or_typed_unavailable() -> None:
    """The encoder must not emit a packet that the inverse calls malformed."""
    q = np.array(
        [
            [0.19902670434116299, -0.1473749251995256, -0.018246426486134337],
            [-0.1473749251995256, -0.8234425592407619, 0.08908642860670035],
            [-0.018246426486134337, 0.08908642860670035, 0.6244158548995988],
        ]
    )
    o = np.array(
        [
            [
                [-0.01046709341323293, 0.9967915791316708, -0.13714575248113997],
                [0.9967915791316708, -0.3543288863145395, -0.2402098505174114],
                [-0.13714575248113997, -0.2402098505174114, 0.36479597972777256],
            ],
            [
                [0.9967915791316708, -0.3543288863145395, -0.24020985051741137],
                [-0.3543288863145395, -1.352433189220621, -0.1705933754651729],
                [-0.24020985051741142, -0.17059337546517286, 0.35564161008895007],
            ],
            [
                [-0.13714575248113997, -0.24020985051741137, 0.36479597972777267],
                [-0.2402098505174114, -0.17059337546517292, 0.3556416100889501],
                [0.36479597972777245, 0.35564161008895007, 0.30773912794631286],
            ],
        ]
    )
    packet = MOD.krylov16(q, o)
    try:
        qr, orr = MOD.reconstruct_krylov16(packet)
    except MOD.OrbitChartUnavailable:
        return
    replay = MOD.krylov16(
        qr,
        orr,
        condition_limit=packet["condition_limit"],
    )
    np.testing.assert_allclose(
        replay["values"],
        packet["values"],
        rtol=1e-7,
        atol=1e-10,
    )


def test_near_boundary_forward_packet_replays_without_silent_projection() -> None:
    """A conditioned packet must replay or fail as chart-unavailable."""
    q = np.diag([-0.7, 0.1, 0.6])
    q /= np.linalg.norm(q)

    o = np.zeros((3, 3, 3))
    entries = {
        (0, 0, 0): -0.30618621784789724,
        (0, 0, 1): 0.3779644730092272,
        (0, 0, 2): 0.10127393670836667,
        (0, 1, 1): -0.10206207261596577,
        (0, 1, 2): 0.1259881576697424,
        (0, 2, 2): 0.4082482904638631,
        (1, 1, 1): -0.3779644730092272,
        (1, 1, 2): -0.30382181012510003,
        (1, 2, 2): 0.0,
        (2, 2, 2): 0.20254787341673336,
    }
    for triple, value in entries.items():
        for perm in set(permutations(triple)):
            o[perm] = value
    trace = np.einsum("iik->k", o)
    eye = np.eye(3)
    o -= (
        np.einsum("ij,k->ijk", eye, trace)
        + np.einsum("ik,j->ijk", eye, trace)
        + np.einsum("jk,i->ijk", eye, trace)
    ) / 5.0
    o /= np.linalg.norm(o)

    packet = MOD.krylov16(q, o)
    try:
        qr, orr = MOD.reconstruct_krylov16(packet)
    except MOD.OrbitChartUnavailable:
        return
    replay = MOD.krylov16(
        qr,
        orr,
        condition_limit=packet["condition_limit"],
    )
    np.testing.assert_allclose(
        replay["values"],
        packet["values"],
        rtol=1e-7,
        atol=1e-10,
    )
