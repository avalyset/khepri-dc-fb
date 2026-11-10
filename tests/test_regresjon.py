"""Tester av regresjonskontrollen på håndregnede, syntetiske serier."""
import numpy as np
import pytest

from khepri_dc_fb import analyse as An
from khepri_dc_fb import regresjon as Rg

T0 = 1780000000 - 1780000000 % 3600  # en hel time i 2026


def serie(H_no1):
    n = len(H_no1)
    d = {"start": T0 + 900 * np.arange(n, dtype=np.int64), "minutter": np.full(n, 15.0)}
    for z in An.SONER:
        for m in ("primaer", "sekundaer"):
            d[f"{z}__{m}"] = np.array(H_no1, dtype=float) if z == "NO_1" else np.full(n, 1e6)
    return d


def test_status_haandregnet():
    s = Rg.mtu_status(np.array([100.0, 50.0, np.nan, 200.0]), np.full(4, 60.0))
    assert s.tolist() == [Rg.IKKE, Rg.HEND, Rg.MANGL, Rg.IKKE]
    t = Rg.time_status(s, T0 + 900 * np.arange(4), np.full(4, 15.0))
    assert t.tolist() == [Rg.MANGL]
    s2 = Rg.mtu_status(np.array([100.0, 50.0, 70.0, 200.0]), np.full(4, 60.0))
    assert Rg.time_status(s2, T0 + 900 * np.arange(4), np.full(4, 15.0)).tolist() == [Rg.HEND]


def test_like_serier_gir_null_avvik():
    a = serie([100.0, 50.0, 3000.0, 200.0, 10.0, 10.0, 10.0, 10.0])
    u = Rg.sammenlign(a, a, T0, T0 + 7200)
    assert u["mtu_avvik"] == 0 and u["time_avvik"] == 0 and u["H_ulike"] == 0
    assert u["kombinasjoner"] == 5 * 2 * 3 * 101 and u["mtu"] == 8


def test_endret_verdi_over_L_gir_avvik():
    a = serie([5000.0] * 8)
    b = serie([5000.0] * 7 + [-5000.0])  # siste MTU: H = −5000 < L for alle f (L_0 = 0 for NO1 2026 er ikke < −5000)
    u = Rg.sammenlign(a, b, T0, T0 + 7200)
    # NO1, begge mål, alle scenarier og f: én MTU og én time endrer status
    assert u["mtu_avvik"] == 2 * 3 * 101 and u["time_avvik"] == 2 * 3 * 101 and u["H_ulike"] == 2


def test_ulikt_rutenett_gir_feil():
    a = serie([1.0] * 8)
    b = serie([1.0] * 8)
    b["minutter"] = b["minutter"].copy()
    b["minutter"][0] = 60.0
    with pytest.raises(ValueError):
        Rg.sammenlign(a, b, T0, T0 + 7200)
