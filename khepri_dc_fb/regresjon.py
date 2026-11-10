"""Regresjonskontroll for avvik A2 (K-104, GT-607): hendelse/ikke-hendelse per MTU og per time i vinduet skal være lik
mellom forrige kjøring (NP fra netPos) og ny kjøring (NP fra fbDomainShadowPrice), for hver sone, f, mål og sensitivitet.

Status per MTU: «hendelse» (L_f > H), «ikke» (L_f ≤ H) eller «manglende» (H mangler). Status per time etter timeregelen
[GT-318, GT-346]: manglende hvis en MTU mangler eller timen ikke dekkes, ellers hendelse hvis minst én MTU er hendelse.
Ulik status, også mellom manglende og ikke-manglende, er et avvik. Rutenettet i vinduet må være likt i begge kjøringene.
"""
from __future__ import annotations

import numpy as np

from khepri_dc_fb import analyse as An

MANGL, IKKE, HEND = 0, 1, 2


def mtu_status(H: np.ndarray, L: np.ndarray) -> np.ndarray:
    g = ~np.isnan(H)
    s = np.full(len(H), MANGL, dtype=np.int8)
    s[g] = np.where(L[g] > H[g], HEND, IKKE)
    return s


def time_status(s: np.ndarray, start: np.ndarray, minutter: np.ndarray) -> np.ndarray:
    tid = start // 3600
    _, inv = np.unique(tid, return_inverse=True)
    n = inv.max() + 1
    mins = np.bincount(inv, weights=minutter, minlength=n)
    mangl = np.bincount(inv, weights=(s == MANGL).astype(float), minlength=n) > 0
    hend = np.bincount(inv, weights=(s == HEND).astype(float), minlength=n) > 0
    ut = np.where(hend, HEND, IKKE).astype(np.int8)
    ut[mangl | (mins != 60)] = MANGL
    return ut


def sammenlign(a: dict, b: dict, fra: int, til: int) -> dict:
    """a, b: dict med «start» (epoch s), «minutter» og «<sone>__<mål>» (H). Vindu [fra, til) i epoch-sekunder."""
    ma = (a["start"] >= fra) & (a["start"] < til)
    mb = (b["start"] >= fra) & (b["start"] < til)
    if not (np.array_equal(a["start"][ma], b["start"][mb]) and np.array_equal(a["minutter"][ma], b["minutter"][mb])):
        raise ValueError("rutenettet i vinduet er ulikt mellom kjøringene")
    start, mins = a["start"][ma], a["minutter"][ma]
    aar = np.array([int(np.datetime64(int(t), "s").astype("datetime64[Y]").astype(int)) + 1970 for t in start])
    ut = dict(mtu=int(ma.sum()), kombinasjoner=0, mtu_sammenligninger=0, mtu_avvik=0, time_sammenligninger=0,
              time_avvik=0, H_ulike=0, eksempler=[])
    for z in An.SONER:
        for maal in ("primaer", "sekundaer"):
            Ha, Hb = a[f"{z}__{maal}"][ma], b[f"{z}__{maal}"][mb]
            ut["H_ulike"] += int(np.sum((np.isnan(Ha) != np.isnan(Hb)) | (np.abs(np.nan_to_num(Ha) - np.nan_to_num(Hb)) > 1e-9)))
            for sc in An.SCENARIER:
                for f in An.F_GRID:
                    Ly = {y: An.L(sc, z, y, f) for y in set(aar.tolist())}
                    L = np.array([Ly[y] for y in aar], dtype=float)
                    sa, sb = mtu_status(Ha, L), mtu_status(Hb, L)
                    ta, tb = time_status(sa, start, mins), time_status(sb, start, mins)
                    ut["kombinasjoner"] += 1
                    ut["mtu_sammenligninger"] += len(sa)
                    ut["time_sammenligninger"] += len(ta)
                    da, dt_ = int(np.sum(sa != sb)), int(np.sum(ta != tb))
                    ut["mtu_avvik"] += da
                    ut["time_avvik"] += dt_
                    if (da or dt_) and len(ut["eksempler"]) < 10:
                        ut["eksempler"].append((sc, maal, z, f, da, dt_))
    return ut
