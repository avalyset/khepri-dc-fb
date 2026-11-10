"""Steg 3a: metadata for JAO Nordic realisert DA-nettoposisjon (netPos) og min/maks (maxNetPos), ett døgn hver.

Døgn: 2024-10-30 (første leveringsdag med flow-based) for begge, og 2026-10-26 for netPos. Rådata lagres utenfor git i utkatalogen.
Bruker jao-py (recon-venv) sin rå klient med nordisk BASEURL; User-Agent er jao-py sin egen (uten e-post).
Bruk: <recon-venv>/bin/python -I tools/meta_jao.py <utkatalog>
"""
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
from jao import JaoPublicationToolClient, JaoPublicationToolPandasNordics
from jao.exceptions import NoMatchingDataError

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)


class RawNordic(JaoPublicationToolClient):
    BASEURL = JaoPublicationToolPandasNordics.BASEURL


c = RawNordic()
res = {}
# Første forsøk 2024-10-30 (første leveringsdag) ga NoMatchingDataError for netPos; derfor også ett nyere døgn.
for navn, fn, dag in [("netPos", c.query_net_position, "2024-10-30"), ("maxNetPos", c.query_minmax_np, "2024-10-30"),
                      ("netPos", c.query_net_position, "2026-10-26")]:
    day = pd.Timestamp(dag, tz="Europe/Oslo")
    t = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    try:
        rows = fn(day=day)
    except NoMatchingDataError:
        res[f"{navn}_{dag}"] = dict(hentet_utc=t, rader=0, feil="NoMatchingDataError", url=c.BASEURL + navn)
        print(navn, dag, "NoMatchingDataError")
        continue
    p = OUT / f"jao_nordic_{navn}_{dag}.json"
    p.write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    felt = sorted(rows[0].keys()) if rows else []
    stamps = sorted(r["dateTimeUtc"] for r in rows)
    res[f"{navn}_{dag}"] = dict(hentet_utc=t, rader=len(rows), felt=felt, foerste=stamps[0] if stamps else None,
                     siste=stamps[-1] if stamps else None, sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                     url=c.BASEURL + navn)
(OUT / "jao_meta.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
for k, v in res.items():
    print(k, v["rader"], v.get("foerste"), v.get("siste"), "felt:", " ".join(v.get("felt", []))[:500])
