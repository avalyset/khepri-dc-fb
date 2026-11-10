"""Tester av khepri_dc_fb.analyse på håndregnede tall og mot headroom.utfall."""
import csv
import datetime as dt
import math
import random
from pathlib import Path

import numpy as np

from khepri_dc_fb import analyse as An
from khepri_dc_fb import headroom as Hm

U = dt.timezone.utc
ROT = Path(__file__).resolve().parents[1]


def test_L_haandregnet_NO1_primaer_f05_2025():
    # E_ref = E_y = 96.966518; R_new = 1398 − 96.966518/0,70 = 1259.4764028571; L = 0,70 · 0,5 · (1259.4764028571 + 2220)
    assert math.isclose(An.L("primaer", "NO_1", 2025, 0.5), 1217.8167410000, abs_tol=1e-6)


def test_L_haandregnet_NO5_brukstid_1_f0_2026():
    # f = 0: L = E_ref − E_y = 0.05676 − 0.039 = 0.01776
    assert math.isclose(An.L("brukstid_1_0", "NO_5", 2026, 0.0), 0.01776, abs_tol=1e-12)


def test_L_haandregnet_NO2_koe0911_f1_2024():
    # R_new = 1950 − 26.68425/0,7 = 1911.8796428571; L = (26.68425 − 17.977821) + 0,7 · (1911.8796428571 + 3668) = 8.706429 + 3905.91575
    assert math.isclose(An.L("koe_0911", "NO_2", 2024, 1.0), 3914.6221790000, abs_tol=1e-6)


def test_installert():
    assert An.installert("NO_1", 2025) == 1401.70
    assert math.isclose(An.installert("NO_2", 2026), 9854.10 + 532.40)


def test_utfall_vektor_haandregnet():
    # time 1: fire kvarter H = 100, 50, nan, 200; time 2: én 60-min MTU H = 10; L = 60
    t0 = dt.datetime(2025, 6, 1, tzinfo=U)
    start = [t0 + dt.timedelta(minutes=15 * i) for i in range(4)] + [t0 + dt.timedelta(hours=1)]
    H = np.array([100, 50, np.nan, 200, 10], dtype=float)
    m = np.array([15, 15, 15, 15, 60], dtype=float)
    u = An.utfall_vektor(H, An.time_ider(start), m, np.full(5, 60.0))
    assert (u.timer_med_hendelse, u.timer_gyldige, u.timer_manglende, u.mtu_gyldige, u.mtu_manglende) == (1, 1, 1, 4, 1)
    assert u.andel_mtu_med_hendelse == 2 / 4 and u.andel_timer_med_hendelse == 1.0


def test_utfall_vektor_lik_headroom_utfall():
    rnd = random.Random(7)
    t0 = dt.datetime(2025, 3, 1, tzinfo=U)
    start, mm, H = [], [], []
    t = t0
    for _ in range(400):
        m = rnd.choice([15, 60])
        if m == 60 and t.minute:
            m = 15
        start.append(t)
        mm.append(m)
        H.append(None if rnd.random() < 0.1 else rnd.uniform(-500, 1500))
        t += dt.timedelta(minutes=m)
    for Lval in (-10.0, 0.0, 300.0, 900.0):
        ref = Hm.utfall(H, start, mm, Lval)
        v = An.utfall_vektor(np.array([np.nan if h is None else h for h in H]), An.time_ider(start),
                             np.array(mm, dtype=float), np.full(len(H), Lval))
        assert ref == v


def test_parametre_lik_GT():
    gt = {r["gt_id"]: r["verdi"] for r in csv.DictReader(open(ROT / "gt/gt_rader.csv", encoding="utf-8"))}
    assert gt["GT-339"] == " ".join(f"{An.E_2026[z]:.3f}" for z in An.SONER)
    for gid, z, typ in [("GT-018", "NO_1", "R"), ("GT-019", "NO_1", "Q"), ("GT-020", "NO_2", "R"), ("GT-021", "NO_2", "Q"),
                        ("GT-022", "NO_3", "R"), ("GT-023", "NO_3", "Q"), ("GT-024", "NO_4", "R"), ("GT-025", "NO_4", "Q"),
                        ("GT-026", "NO_5", "R"), ("GT-027", "NO_5", "Q")]:
        assert int(gt[gid].replace(" ", "")) == An.KOE["0211"][typ][z]
    for gid, z, typ in [("GT-047", "NO_1", "R"), ("GT-202", "NO_1", "Q"), ("GT-203", "NO_2", "R"), ("GT-048", "NO_2", "Q"),
                        ("GT-204", "NO_3", "R"), ("GT-049", "NO_3", "Q"), ("GT-205", "NO_4", "R"), ("GT-050", "NO_4", "Q"),
                        ("GT-051", "NO_5", "R"), ("GT-177", "NO_5", "Q")]:
        assert int(gt[gid].replace(" ", "")) == An.KOE["0911"][typ][z]
    for gid, z in [("GT-330", "NO_2"), ("GT-331", "NO_3"), ("GT-333", "NO_5")]:
        assert gt[gid] == " ".join(f"{x:.2f}" for x in An.A68_PUMPE[z])
    assert gt["GT-201"] == "F_GRID = np.round(np.arange(0, 101) / 100.0, 2)" and len(An.F_GRID) == 101
    for i, z in enumerate(An.SONER):
        assert gt[f"GT-{466 + i}"] == f"{An.E_MW[z][2024]} {An.E_MW[z][2025]}"
        assert gt[f"GT-{471 + i}"] == " ".join(f"{x:.2f}" for x in An.A68_MAGASIN[z])
