"""K-77 punkt 1: hvilke lagrede A75-kilder har «Actual Consumption» for Hydro Pumped Storage?

Leser lagrede A75-rådata lokalt (ingen henting), samme fire kilder og periode som tools/a75_pumpe.py:
  K  ~/khepri-data/kdf-meta-2026-11-09/entsoe_raw/A75/<sone>/*.xml.gz   (ny API-henting)
  X  /Volumes/Vault/khepri-dc/raw/A75/A75_<sone>_<år>.xml               (v1-XML)
  F  /Volumes/Vault/khepri-data/flowtracing/raw/2025/A75/A75_<sone>_2025-*.csv (flowtracing-CSV)
  R  ~/khepri-data/raw/entsoe-rest/NO<n>_generation_<år>.csv            (entsoe-rest-CSV)
Periode [2024-10-30T00:00Z, 2026-11-01T00:00Z); filer utenfor perioden leses ikke.
XML: TimeSeries med psrType B10; forbruk = TimeSeries med outBiddingZone_Domain.mRID (som i ENTSO-E-formatet).
CSV: kolonner der navn eller underoverskrift inneholder «Consumption», og spesielt for «Hydro Pumped Storage».
Telles bare antall serier/kolonner, antall ikke-tomme verdier i perioden og filer; ingen verdier skrives ut.
Bruk: python3 -I -B tools/a75_forbruk.py <kilde K|X|F|R> <sone, f.eks. NO_2> [filer]
Utdata: «forbruksserier/-kolonner B10=<n> verdier=<n>; forbrukskolonner/-serier alle typer=<n>; filer lest=<n>»
Med «filer»: én linje per fil, «<filnavn> <B10-forbruksserier/-kolonner i fila>», så filene med feltet kan tidfestes.
"""
import csv
import datetime as dt
import gzip
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

kilde, sone = sys.argv[1], sys.argv[2]
n = sone.split("_")[1]
A = dt.datetime(2024, 10, 30, tzinfo=dt.timezone.utc)
B = dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc)
HOME = Path.home()
filer = {
    "K": sorted((HOME / "khepri-data/kdf-meta-2026-11-09/entsoe_raw/A75" / sone).glob("*.xml.gz")),
    "X": sorted(p for p in Path("/Volumes/Vault/khepri-dc/raw/A75").glob(f"A75_{sone}_*.xml") if p.stem[-4:] in ("2024", "2025", "2026")),
    "F": sorted(Path("/Volumes/Vault/khepri-data/flowtracing/raw/2025/A75").glob(f"A75_{sone}_2025-*.csv")),
    "R": sorted((HOME / "khepri-data/raw/entsoe-rest").glob(f"NO{n}_generation_202[4-6].csv")),
}[kilde]
b10 = [0, 0]
alle = 0


def iso(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def xml(root):
    global alle
    for ts in root.iterfind("{*}TimeSeries"):
        if ts.find("{*}outBiddingZone_Domain.mRID") is None:
            continue
        alle += 1
        if ts.findtext("{*}MktPSRType/{*}psrType") != "B10":
            continue
        b10[0] += 1
        for per in ts.iterfind("{*}Period"):
            start = iso(per.findtext("{*}timeInterval/{*}start"))
            res = int(per.findtext("{*}resolution")[2:-1])
            for p in per.iterfind("{*}Point"):
                t = start + dt.timedelta(minutes=(int(p.findtext("{*}position")) - 1) * res)
                if A <= t < B and p.findtext("{*}quantity") not in (None, ""):
                    b10[1] += 1


def csvfil(path):
    global alle
    rader = list(csv.reader(open(path, encoding="utf-8")))
    h1 = rader[0]
    to = len(rader) > 1 and rader[1] and rader[1][0] == "" and any("Actual" in c for c in rader[1][1:])
    data = rader[2:] if to else rader[1:]
    for i, c in enumerate(h1):
        under = rader[1][i] if to else c
        if "Consumption" not in under and "Consumption" not in c:
            continue
        alle += 1
        if "Hydro Pumped Storage" not in c:
            continue
        b10[0] += 1
        for r in data:
            if not r or not r[0] or i >= len(r):
                continue
            t = dt.datetime.fromisoformat(r[0]).astimezone(dt.timezone.utc)
            if A <= t < B and r[i].strip() not in ("", "nan", "NaN"):
                b10[1] += 1


per_fil = []
for p in filer:
    for0 = b10[0]
    if kilde == "K":
        xml(ET.fromstring(gzip.open(p).read()))
    elif kilde == "X":
        xml(ET.parse(p).getroot())
    else:
        csvfil(p)
    per_fil.append((p.name, b10[0] - for0))
if sys.argv[3:] == ["filer"]:
    for navn, k in per_fil:
        print(navn, k)
    raise SystemExit
print(f"forbruksserier/-kolonner B10={b10[0]} verdier={b10[1]}; forbrukskolonner/-serier alle typer={alle}; filer lest={len(filer)}")
