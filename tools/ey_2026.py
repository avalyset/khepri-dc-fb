"""E_y for 2026 fra K-69 (Elhub consumption_datacenter_per_mba_hour), med v1s regel fra build/elhub_ey.py:
E_MW = sum(VOLUM_KWH) / 1000 / forventede timer, her over vinduet [2026-01-01T00:00Z, 2026-11-01T00:00Z) (7296 timer).

Bruk: python3 -I -B tools/ey_2026.py <rot> e <sone>      -> E_MW (3 desimaler)
      python3 -I -B tools/ey_2026.py <rot> timer <sone>  -> antall distinkte timer i vinduet
      python3 -I -B tools/ey_2026.py <rot> siste         -> siste STARTTID i fila (UTC)
      python3 -I -B tools/ey_2026.py <rot> forventet     -> forventede timer i vinduet
      python3 -I -B tools/ey_2026.py <rot> kontroll <sone> <år>  -> samme regel over helt UTC-år (gjenskaper K-22 for 2023–2025)
"""
import csv
import datetime as dt
import sys
from pathlib import Path

root, mode = Path(sys.argv[1]).resolve(), sys.argv[2]
A = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
B = dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc)
if mode == "kontroll":
    aar = int(sys.argv[4])
    A, B = dt.datetime(aar, 1, 1, tzinfo=dt.timezone.utc), dt.datetime(aar + 1, 1, 1, tzinfo=dt.timezone.utc)
forventet = int((B - A).total_seconds() // 3600)
kwh, timer, siste = {}, {}, None
with open(root / "kilder/K-69_Elhub_consumption_datacenter_per_mba_hour-all.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter=";"):
        t = dt.datetime.fromisoformat(r["STARTTID"]).astimezone(dt.timezone.utc)
        siste = t if siste is None or t > siste else siste
        if A <= t < B:
            z = r["PRISOMRÅDE"]
            kwh[z] = kwh.get(z, 0.0) + float(r["VOLUM_KWH"].replace(",", "."))
            timer.setdefault(z, set()).add(t)
if mode in ("e", "kontroll"):
    print(f"{kwh[sys.argv[3]] / 1000.0 / forventet:.3f}")
elif mode == "timer":
    print(len(timer[sys.argv[3]]))
elif mode == "siste":
    print(siste.isoformat().replace("+00:00", "Z"))
elif mode == "forventet":
    print(forventet)
