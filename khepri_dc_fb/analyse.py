"""KHEPRI-DC-FB dataruna steg 3: analyse etter preregistreringen (tagg prereg-v1), med funksjonene i headroom.py.

Parametre (alle med GT-ID, VERIFISERT×2):
  E_MW 2024/2025 per sone fra v1-parameterfila (K-22) [GT-466–GT-470]; E_ref = E for referanseåret 2025 [GT-199];
  E_2026 fra Elhub-fila [GT-339, GT-369]. R og Q per sone: 02.11-køen [GT-018–GT-027] (primær), 09.11-køen
  [GT-047–GT-051, GT-177, GT-202–GT-205] (sensitivitet). Brukstid 0,70 [GT-185] og 1,0 [GT-186], begge steder [GT-316].
  f-rutenett 0,00–1,00 i steg 0,01 [GT-201]. A68 installert: Hydro Water Reservoir [GT-471–GT-475] og Hydro Pumped
  Storage [GT-330, GT-331, GT-333]; NO1 og NO4 uten pumpeledd [GT-354].
Vektorisert telling (utfall_vektor) gir samme tall som headroom.utfall; det testes i tests/test_analyse.py.
"""
from __future__ import annotations

import datetime as dt
from typing import Optional, Sequence

import numpy as np

from khepri_dc_fb import headroom as Hm

SONER = ["NO_1", "NO_2", "NO_3", "NO_4", "NO_5"]
E_MW = {  # K-22, v1-parameterfila: E_MW per sone og år [GT-466–GT-470]
    "NO_1": {2024: 40.604627, 2025: 96.966518},
    "NO_2": {2024: 17.977821, 2025: 26.68425},
    "NO_3": {2024: 93.707314, 2025: 153.82739},
    "NO_4": {2024: 70.993339, 2025: 81.096372},
    "NO_5": {2024: 0.891418, 2025: 0.05676},
}
E_2026 = {"NO_1": 106.676, "NO_2": 62.196, "NO_3": 109.066, "NO_4": 77.291, "NO_5": 0.039}  # [GT-339]
E_REF_AAR = 2025  # [GT-199]
KOE = {
    "0211": {"R": {"NO_1": 1398, "NO_2": 1950, "NO_3": 96, "NO_4": 477, "NO_5": 270},       # [GT-018, 020, 022, 024, 026]
             "Q": {"NO_1": 2220, "NO_2": 3092, "NO_3": 1646, "NO_4": 2258, "NO_5": 894}},   # [GT-019, 021, 023, 025, 027]
    "0911": {"R": {"NO_1": 1413, "NO_2": 1950, "NO_3": 96, "NO_4": 477, "NO_5": 270},       # [GT-047, 203, 204, 205, 051]
             "Q": {"NO_1": 2220, "NO_2": 3668, "NO_3": 1745, "NO_4": 2248, "NO_5": 894}},   # [GT-202, 048, 049, 050, 177]
}
SCENARIER = {  # én endring om gangen [GT-411]
    "primaer": dict(b=0.70, koe="0211"),
    "brukstid_1_0": dict(b=1.0, koe="0211"),
    "koe_0911": dict(b=0.70, koe="0911"),
}
F_GRID = [round(i / 100.0, 2) for i in range(101)]  # [GT-201]
A68_MAGASIN = {  # K-35: Hydro Water Reservoir 2024 / 2025 / 2026 [GT-471–GT-475]
    "NO_1": (1419.81, 1401.70, 1401.60), "NO_2": (9816.30, 9870.80, 9854.10), "NO_3": (3415.56, 3421.50, 3448.00),
    "NO_4": (4906.57, 4914.30, 4852.80), "NO_5": (7101.92, 7104.00, 7123.90)}
A68_PUMPE = {"NO_2": (522.00, 522.00, 532.40), "NO_3": (60.20, 60.20, 61.20), "NO_5": (482.50, 482.50, 482.50)}  # [GT-330, 331, 333]
PUMPESONER = ("NO_2", "NO_3", "NO_5")


def e_y(sone: str, aar: int) -> float:
    return E_2026[sone] if aar == 2026 else E_MW[sone][aar]


def L(scenario: str, sone: str, aar: int, f: float) -> float:
    s = SCENARIER[scenario]
    k = KOE[s["koe"]]
    return Hm.last_f(E_MW[sone][E_REF_AAR], e_y(sone, aar), k["R"][sone], k["Q"][sone], f, s["b"])


def installert(sone: str, aar: int) -> Optional[float]:
    i = aar - 2024
    return Hm.installert_regulerbar(A68_MAGASIN[sone][i], A68_PUMPE.get(sone, (None,) * 3)[i], sone in PUMPESONER)


def utfall_vektor(H: np.ndarray, time_id: np.ndarray, minutter: np.ndarray, Lv: np.ndarray) -> Hm.Utfall:
    """Samme som headroom.utfall, vektorisert: H (nan = manglende), time_id (heltall per UTC-time), minutter, L per MTU."""
    gyldig = ~np.isnan(H)
    e = gyldig & (Lv > np.where(gyldig, H, 0.0))
    _, inv = np.unique(time_id, return_inverse=True)
    n_t = inv.max() + 1 if len(inv) else 0
    min_t = np.bincount(inv, weights=minutter, minlength=n_t)
    ugyldig_t = np.bincount(inv, weights=(~gyldig).astype(float), minlength=n_t)
    e_t = np.bincount(inv, weights=e.astype(float), minlength=n_t)
    tg = (min_t == 60) & (ugyldig_t == 0)
    t_g = int(tg.sum())
    t_h = int((tg & (e_t > 0)).sum())
    n_g = int(gyldig.sum())
    n_h = int(e.sum())
    return Hm.Utfall(t_h, t_g, n_t - t_g, (t_h / t_g) if t_g else None, (n_h / n_g) if n_g else None, n_g,
                     int(len(H) - n_g))


def time_ider(start: Sequence[dt.datetime]) -> np.ndarray:
    return np.array([int(t.timestamp()) // 3600 for t in start], dtype=np.int64)
