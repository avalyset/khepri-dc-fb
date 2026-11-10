"""Leser per-fil-avsnittet i K-78 og skriver, for NO2 NO3 NO5, hvilke filer i én kilde som har B10-forbruksfeltet.

Bruk: python3 -I -B tools/k78_filer.py <rot> <kilde K|X|F|R>
Utdata: «NO_2: <filer med feltet, uten prefiks/endelse> | NO_3: … | NO_5: …» («ingen» hvis ingen fil har feltet).
"""
import re
import sys
from pathlib import Path

root, kilde = Path(sys.argv[1]).resolve(), sys.argv[2]
tekst = (root / "kilder/K-78_A75_pumpeforbruk_per_kilde_2026-11-09.txt").read_text(encoding="utf-8")
blokk = tekst.split("Per fil (")[1]
ut = []
for sone in ("NO_2", "NO_3", "NO_5"):
    linje = next(l for l in blokk.splitlines() if l.startswith(f"{kilde} {sone}: "))
    filer = [f.rsplit(" ", 1) for f in linje.split(": ", 1)[1].split(";")]
    med = [re.sub(r"^(A75_NO_\d_|NO\d_generation_)|\.(xml\.gz|xml|csv)$", "", n) for n, k in filer if int(k) > 0]
    ut.append(f"{sone}: {' '.join(med) if med else 'ingen'}")
print(" | ".join(ut))
