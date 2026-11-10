"""Recon (K-95-bestillingen, punkt 1 og 4): JAO Nordic fbDomainShadowPrice, Netposition-CNEC-er (Flow_FB), som kandidat
for realisert DA-nettoposisjon før netPos starter. Ingen analyse, ingen bruk i resultater.

Håndboka (K-25): «Net Position SDAC» tas fra «Shadow Price and Flow FB», der «NetPostion_BZ» CNECs «Flow_FB» value
publiseres per BZ og MTU. Spørringen filtrerer på CnecName «Netposition» (JAO-filteret er en delstrengsøk).
Klient: jao-py 0.8.7 sin sesjon og User-Agent (uten e-post), rå forespørsler mot nordisk BASEURL, ingen pause
(som recon-skriptet 09.11), høyst 3 forsøk med backoff 10 s og 30 s.
Rådata: hele JSON-svaret per forretningsdøgn, gzip, i <ut>/ (utenfor git), og manifest.csv (døgn, rader, sha256 av
ukomprimert svar, hentet_utc, utfall).
Bruk: <recon-venv>/bin/python -I tools/recon_np_jao.py <ut> foerste            # første døgn med data (sonde per døgn)
      <recon-venv>/bin/python -I tools/recon_np_jao.py <ut> doegn <YYYY-MM-DD> [<YYYY-MM-DD>]   # henter døgn i intervallet
"""
import csv
import datetime as dt
import gzip
import hashlib
import json
import sys
import time
from pathlib import Path
from zoneinfo import ZoneInfo

from jao import JaoPublicationToolClient, JaoPublicationToolPandasNordics

OSLO = ZoneInfo("Europe/Oslo")
FILTER = json.dumps({"CnecName": "Netposition"})


class RawNordic(JaoPublicationToolClient):
    BASEURL = JaoPublicationToolPandasNordics.BASEURL


def start(d):
    return dt.datetime(d.year, d.month, d.day, tzinfo=OSLO).astimezone(dt.timezone.utc)


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def naa():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


c = RawNordic()
out = Path(sys.argv[1]).expanduser()
out.mkdir(parents=True, exist_ok=True)


def kall(fra, til, take):
    for f in range(3):
        try:
            r = c.s.get(c.BASEURL + "fbDomainShadowPrice",
                        params={"FromUtc": iso(fra), "ToUtc": iso(til), "Skip": 0, "Take": take, "Filter": FILTER},
                        timeout=300)
            r.raise_for_status()
            return r
        except Exception:
            if f == 2:
                raise
            time.sleep([10, 30][f])


if sys.argv[2] == "foerste":
    d = dt.date(2024, 10, 28)
    while d <= dt.date(2024, 11, 3):
        r = kall(start(d), start(d + dt.timedelta(days=1)), 1)
        print(d, "rader_med_filter", r.json().get("totalRowsWithFilter"), "hentet", naa())
        d += dt.timedelta(days=1)
    raise SystemExit
a = dt.date.fromisoformat(sys.argv[3])
b = dt.date.fromisoformat(sys.argv[4]) if len(sys.argv) > 4 else a
man = out / "manifest.csv"
ny = not man.exists()
with open(man, "a", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    if ny:
        w.writerow(["doegn", "rader", "rader_med_filter", "sha256", "bytes", "hentet_utc", "utfall"])
    d = a
    while d <= b:
        if (out / f"np_fbdsp_{d}.json.gz").exists():
            d += dt.timedelta(days=1)
            continue
        r = kall(start(d), start(d + dt.timedelta(days=1)), 5000)
        j = r.json()
        rows = j.get("data") or []
        body = r.content
        (out / f"np_fbdsp_{d}.json.gz").write_bytes(gzip.compress(body))
        w.writerow([d, len(rows), j.get("totalRowsWithFilter"), hashlib.sha256(body).hexdigest(), len(body), naa(),
                    "OK" if rows and len(rows) == j.get("totalRowsWithFilter") else "UFULLSTENDIG/TOM"])
        fh.flush()
        d += dt.timedelta(days=1)
print("ferdig", a, b)
