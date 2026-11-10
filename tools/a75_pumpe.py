"""K-70-vilkåret for GT-354: har A75 Hydro Pumped Storage-produksjon i NO1 eller NO4 i perioden?

Leser lagrede A75-rådata lokalt (ingen henting), samme kilder som tools/dekning_lokal.py:
  X  /Volumes/Vault/khepri-dc/raw/A75/A75_<sone>_<år>.xml
  F  /Volumes/Vault/khepri-data/flowtracing/raw/2025/A75/A75_<sone>_2025-*.csv
  R  ~/khepri-data/raw/entsoe-rest/NO<n>_generation_<år>.csv
  K  ~/khepri-data/kdf-meta-2026-11-09/entsoe_raw/A75/<sone>/*.xml.gz
Periode [2024-10-30T00:00Z, 2026-11-01T00:00Z).
XML: TimeSeries med psrType B10 (Hydro Pumped Storage); produksjon = inBiddingZone_Domain, forbruk = outBiddingZone_Domain.
CSV: kolonner der navnet inneholder «Hydro Pumped Storage»; forbrukskolonner («Actual Consumption») telles for seg.
Bruk: python3 -I -B tools/a75_pumpe.py <sone, f.eks. NO_1> [kort]
Med «kort»: tre tall, produksjonsserier/-kolonner, produksjonsverdier i perioden og filer lest. Ellers én linje: «produksjon: serier/kolonner=<n> verdier=<n> ulik_null=<n>; forbruk: …; filer lest=<n>».
"""
import csv
import datetime as dt
import gzip
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sone = sys.argv[1]
n = sone.split("_")[1]
A = dt.datetime(2024, 10, 30, tzinfo=dt.timezone.utc)
B = dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc)
HOME = Path.home()
X = sorted(Path("/Volumes/Vault/khepri-dc/raw/A75").glob(f"A75_{sone}_*.xml"))
F = sorted(Path("/Volumes/Vault/khepri-data/flowtracing/raw/2025/A75").glob(f"A75_{sone}_2025-*.csv"))
R = sorted((HOME / "khepri-data/raw/entsoe-rest").glob(f"NO{n}_generation_202[4-6].csv"))
K = sorted((HOME / "khepri-data/kdf-meta-2026-11-09/entsoe_raw/A75" / sone).glob("*.xml.gz"))
tell = {"produksjon": [0, 0, 0], "forbruk": [0, 0, 0]}


def iso(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def xml(root):
    for ts in root.iterfind("{*}TimeSeries"):
        if ts.findtext("{*}MktPSRType/{*}psrType") != "B10":
            continue
        side = "produksjon" if ts.find("{*}inBiddingZone_Domain.mRID") is not None else "forbruk"
        tell[side][0] += 1
        for per in ts.iterfind("{*}Period"):
            start = iso(per.findtext("{*}timeInterval/{*}start"))
            res = int(per.findtext("{*}resolution")[2:-1])
            for p in per.iterfind("{*}Point"):
                t = start + dt.timedelta(minutes=(int(p.findtext("{*}position")) - 1) * res)
                q = p.findtext("{*}quantity")
                if A <= t < B and q not in (None, ""):
                    tell[side][1] += 1
                    tell[side][2] += int(float(q) != 0.0)


def csvfil(path):
    rader = list(csv.reader(open(path, encoding="utf-8")))
    h1 = rader[0]
    to = len(rader) > 1 and rader[1] and rader[1][0] == "" and any("Actual" in c for c in rader[1][1:])
    data = rader[2:] if to else rader[1:]
    for i, c in enumerate(h1):
        if "Hydro Pumped Storage" not in c:
            continue
        under = rader[1][i] if to else (c.split("|")[1] if "|" in c else "Actual Aggregated")
        side = "forbruk" if "Consumption" in under else "produksjon"
        tell[side][0] += 1
        for r in data:
            if not r or not r[0] or i >= len(r):
                continue
            t = dt.datetime.fromisoformat(r[0]).astimezone(dt.timezone.utc)
            if A <= t < B and r[i].strip() not in ("", "nan", "NaN"):
                tell[side][1] += 1
                tell[side][2] += int(float(r[i]) != 0.0)


for p in X:
    xml(ET.parse(p).getroot())
for p in K:
    xml(ET.fromstring(gzip.open(p).read()))
for p in F + R:
    csvfil(p)
if sys.argv[2:] == ["kort"]:
    print(tell["produksjon"][0], tell["produksjon"][1], len(X) + len(K) + len(F) + len(R))
    raise SystemExit
print("; ".join(f"{k}: serier/kolonner={v[0]} verdier={v[1]} ulik_null={v[2]}" for k, v in tell.items())
      + f"; filer lest={len(X) + len(K) + len(F) + len(R)}")
