"""Regresjonskontroll (avvik A2, K-104, GT-607): forrige kjøring (NP fra netPos) mot ny (NP fra fbDomainShadowPrice).

Leser to serieuttak fra tools/kjor_analyse.py --dump (lokale .npz utenfor repoet) og sammenligner status per MTU og per time
i vinduet [2026-05-27T22:00Z, 2026-11-01T00:00Z), som er forretningsdøgnene 2026-05-28–2026-11-01 begrenset av perioden
[GT-379], for hver sone, f, mål og sensitivitet (khepri_dc_fb.regresjon). Skriver bare tellinger.
Bruk: python3 -I -B tools/kjor_regresjon.py <forrige.npz> <ny.npz>
"""
import datetime as dt
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from khepri_dc_fb import regresjon as Rg  # noqa: E402

FRA = int(dt.datetime(2026, 5, 27, 22, tzinfo=dt.timezone.utc).timestamp())
TIL = int(dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc).timestamp())
a, b = (dict(np.load(Path(p).expanduser())) for p in sys.argv[1:3])
u = Rg.sammenlign(a, b, FRA, TIL)
print(f"vindu 2026-05-27T22:00Z–2026-11-01T00:00Z; MTU i vinduet {u['mtu']}; kombinasjoner (sone × mål × sensitivitet × f) {u['kombinasjoner']}")
print(f"MTU-sammenligninger {u['mtu_sammenligninger']}; MTU med ulik status {u['mtu_avvik']}")
print(f"time-sammenligninger {u['time_sammenligninger']}; timer med ulik status {u['time_avvik']}")
print(f"MTU med ulik H eller H2 (|Δ| > 1e-9 MW eller ulik mangel), over soner og mål {u['H_ulike']}")
for e in u["eksempler"]:
    print("eksempel på avvik (scenario, mål, sone, f, MTU-avvik, time-avvik):", e)
print("REGRESJON " + ("GRØNN" if u["mtu_avvik"] == 0 and u["time_avvik"] == 0 else "RØD: STOPP"))
