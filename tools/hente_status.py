"""Tall for 3c-supplementet (A11) fra K-73 (dekning), K-74 (hentelogg) og K-75 (henteoppsummering).

Hullhentingen = rader i K-75 med hentet_utc >= 2026-11-09T17:38:14Z (START «bare 374 hull» i K-74).
Bruk: python3 -I -B tools/hente_status.py <rot> <modus>
  vinduer        OK-vinduer i hullhentingen, A11 / A65 / A75
  totalt         alle vinduer i hullhentingen
  ikke_ok        vinduer i hullhentingen med status ulik OK
  flere_forsok   vinduer som trengte mer enn ett forsøk / sum ekstra forsøk
  http599        linjer med «HTTP 599» i K-74 etter START for hullhentingen
  a11_tid        første og siste hentet_utc for A11 i hullhentingen
  kurve          kurvetype og oppløsning i hullhentingen (unike)
  full <dok>     kombinasjoner med union_andel 1.0000 / alle, i K-73 (dok = A11, A11-sone(min), A65, A75)
  retninger      antall A11-grenseretninger i K-73
"""
import csv
import sys
from pathlib import Path

root, modus = Path(sys.argv[1]).resolve(), sys.argv[2]
K = root / "kilder"
START = "2026-11-09T17:38:14Z"
h = [x for x in csv.DictReader(open(K / "K-75_henteoppsummering_ENTSOE_alle.csv", encoding="utf-8")) if x["hentet_utc"] >= START]
d = list(csv.DictReader(open(K / "K-73_dekning_A65_A75_A11_2024-10-30_2026-10-31.csv", encoding="utf-8")))
if modus == "vinduer":
    print(" / ".join(str(sum(1 for x in h if x["dok"] == t and x["status"] == "OK")) for t in ("A11", "A65", "A75")))
elif modus == "totalt":
    print(len(h))
elif modus == "ikke_ok":
    print(sum(1 for x in h if x["status"] != "OK"))
elif modus == "flere_forsok":
    print(sum(1 for x in h if int(x["forsok"]) > 1), "/", sum(int(x["forsok"]) - 1 for x in h))
elif modus == "http599":
    L = (K / "K-74_hentelogg_ENTSOE_slutt.txt").read_text(encoding="utf-8").splitlines()
    s = max(i for i, l in enumerate(L) if "bare 374 hull" in l)
    print(sum(1 for l in L[s + 1:] if "HTTP 599" in l))
elif modus == "a11_tid":
    a = [x["hentet_utc"] for x in h if x["dok"] == "A11"]
    print(min(a), max(a))
elif modus == "kurve":
    print(*sorted({f"{x['kurvetyper']} {x['opploesninger']}" for x in h}))
elif modus == "full":
    r = [x for x in d if x["dok"] == sys.argv[3]]
    print(sum(1 for x in r if x["union_andel"] == "1.0000"), "/", len(r))
elif modus == "retninger":
    print(len({x["omraade"] for x in d if x["dok"] == "A11"}))
