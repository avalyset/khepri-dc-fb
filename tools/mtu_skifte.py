"""3c punkt 3b: første 15-minutters tidsstempel (UTC) for A65 og A75 per NO-sone, lest fra lokale rådata (ingen henting).

Kilder per (dok, sone):
  X  /Volumes/Vault/khepri-dc/raw/{dok}/{dok}_{sone}_2025*.xml   ENTSO-E XML: første Period med resolution PT15M
     (start + (første posisjon med verdi − 1) · 15 min), og siste PT60M-periode før den.
  F  /Volumes/Vault/khepri-data/flowtracing/raw/2025/{dok}/{dok}_{sone}_2025-*.csv   første rad der neste rad ligger 15 min etter
  R  ~/khepri-data/raw/entsoe-rest/NO{n}_generation_2025.csv (bare A75)            samme regel som F
Utskrift: CSV med dok, sone, kilde, første 15-min tidsstempel (UTC), siste 60-min tidsstempel før (UTC).
Bruk: python3 -I -B tools/mtu_skifte.py
"""
import csv
import datetime as dt
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

X = Path("/Volumes/Vault/khepri-dc/raw")
F = Path("/Volumes/Vault/khepri-data/flowtracing/raw/2025")
R = Path.home() / "khepri-data/raw/entsoe-rest"
ZONES = ["NO_1", "NO_2", "NO_3", "NO_4", "NO_5"]


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%MZ")


def fra_xml(paths):
    forste15, siste60 = None, None
    for p in paths:
        root = ET.parse(p).getroot()
        for ts in root.iterfind(".//{*}TimeSeries"):
            for per in ts.iterfind("{*}Period"):
                rs = per.findtext("{*}resolution")
                ps = dt.datetime.strptime(per.findtext("{*}timeInterval/{*}start"), "%Y-%m-%dT%H:%MZ")
                pe = dt.datetime.strptime(per.findtext("{*}timeInterval/{*}end"), "%Y-%m-%dT%H:%MZ")
                pos = sorted(int(x.findtext("{*}position")) for x in per.iterfind("{*}Point"))
                if not pos:
                    continue
                if rs == "PT15M":
                    t = ps + dt.timedelta(minutes=15 * (pos[0] - 1))
                    forste15 = t if forste15 is None or t < forste15 else forste15
                elif rs == "PT60M":
                    t = pe - dt.timedelta(minutes=60)
                    siste60 = t if siste60 is None or t > siste60 else siste60
    if forste15 and siste60 and siste60 >= forste15:  # bare 60-min-perioder FØR skiftet er relevante
        siste60 = None
    return forste15, siste60


def fra_csv(paths):
    tider = []
    for p in sorted(paths):
        for r in list(csv.reader(open(p, encoding="utf-8")))[1:]:
            if r and r[0] and r[0][:2] == "20":
                tider.append(dt.datetime.fromisoformat(r[0]).astimezone(dt.timezone.utc).replace(tzinfo=None))
    tider = sorted(set(tider))
    for a, b in zip(tider, tider[1:]):
        if b - a == dt.timedelta(minutes=15):
            forrige = [x for x in tider if x < a]
            return a, (forrige[-1] if forrige else None)
    return None, None


w = csv.writer(sys.stdout)
w.writerow(["dok", "sone", "kilde", "forste_15min_utc", "siste_60min_for_utc"])
for dok in ("A65", "A75"):
    for z in ZONES:
        a, b = fra_xml(sorted((X / dok).glob(f"{dok}_{z}_2025*.xml")))
        w.writerow([dok, z, "X", iso(a) if a else "", iso(b) if b else ""])
        a, b = fra_csv((F / dok).glob(f"{dok}_{z}_2025-*.csv"))
        w.writerow([dok, z, "F", iso(a) if a else "", iso(b) if b else ""])
        if dok == "A75":
            a, b = fra_csv([R / f"NO{z[-1]}_generation_2025.csv"])
            w.writerow([dok, z, "R", iso(a) if a else "", iso(b) if b else ""])
