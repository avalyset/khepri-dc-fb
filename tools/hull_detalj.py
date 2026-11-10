"""Lister manglende kvarter (intervallstart, UTC) i hentede A65-filer for gitte (sone, måned). Ingen henting.
Bruk: python3 -I -B tools/hull_detalj.py <sone:YYYY-MM> ...   (leser ~/khepri-data/kdf-meta-2026-11-09/entsoe_raw/A65/<sone>/<YYYY-MM>.xml.gz)
A03: hold forrige verdi til neste posisjon/periodens slutt; A01: bare oppgitte posisjoner (som tools/dekning_lokal.py).
"""
import datetime as dt
import gzip
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

K = Path.home() / "khepri-data/kdf-meta-2026-11-09/entsoe_raw/A65"
RES = {"PT15M": 15, "PT60M": 60}
for arg in sys.argv[1:]:
    sone, mnd = arg.split(":")
    y, m = map(int, mnd.split("-"))
    s = dt.datetime(y, m, 1)
    e = dt.datetime(y + (m == 12), m % 12 + 1, 1)
    root = ET.fromstring(gzip.decompress((K / sone / f"{mnd}.xml.gz").read_bytes()))
    dekket = set()
    for ts in root.iterfind(".//{*}TimeSeries"):
        kurve = (ts.findtext("{*}curveType") or "A01").strip()
        for per in ts.iterfind("{*}Period"):
            ps = dt.datetime.strptime(per.findtext("{*}timeInterval/{*}start"), "%Y-%m-%dT%H:%MZ")
            pe = dt.datetime.strptime(per.findtext("{*}timeInterval/{*}end"), "%Y-%m-%dT%H:%MZ")
            r = RES[per.findtext("{*}resolution")]
            n = int((pe - ps).total_seconds() // 60 // r)
            pos = sorted(int(p.findtext("{*}position")) for p in per.iterfind("{*}Point") if (p.findtext("{*}quantity") or "") != "")
            for i, q in enumerate(pos):
                slutt = (pos[i + 1] if i + 1 < len(pos) else n + 1) if kurve == "A03" else q + 1
                for k in range(q, slutt):
                    t0 = ps + dt.timedelta(minutes=(k - 1) * r)
                    for j in range(r // 15):
                        dekket.add(t0 + dt.timedelta(minutes=15 * j))
    t, mangler = s, []
    while t < e:
        if t not in dekket:
            mangler.append(t.strftime("%Y-%m-%dT%H:%MZ"))
        t += dt.timedelta(minutes=15)
    print(f"A65 {sone} {mnd}: {len(mangler)} manglende kvarter: {' '.join(mangler)}")
