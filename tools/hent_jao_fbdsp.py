"""Avvik A2 (K-104): JAO Nordic fbDomainShadowPrice, Netposition-CNEC-er, for alle forretningsdøgn i perioden.

Samme regler som tools/hent_jao.py: døgnene regnes ut (tools/hent_jao.forretningsdoegn) [GT-355, GT-361]; jao-py 0.8.7 sin
sesjon og User-Agent; høyst 3 forsøk med backoff 10 s og 30 s. A2-hentingen 10.11 gikk uten pause og fikk fire HTTP 429
(GT-664–GT-667); for senere henting holdes khepri_dc_fb.hent.PAUSE_MELLOM_KALL_S mellom kallene, og ved HTTP 429 ventes
Retry-After eller VENT_VED_429_S.
Spørring: FromUtc/ToUtc = forretningsdøgnets grenser, Filter {"CnecName": "Netposition"} (JAO-filteret er delstreng),
Take 5000. Rådata: svarets «data»-liste, gzip, én fil per døgn: <ut>/jao_fbDomainShadowPrice_<døgn>.json.gz.
Manifest (khepri_dc_fb.hent.MANIFEST_FELT): sha256 og bytes av den ukomprimerte JSON-lista, hentetidspunkt (UTC),
kontrollstreng og utfall. Kontrollstreng: ikke-tom liste der hver rad har «dateTimeUtc», «cnecName» og «flowFb», og der
NetPosition_NO1 … NetPosition_NO5 alle finnes. Tomt svar føres som fravær med feilnavn (INGEN_DATA, «tom liste»).
Døgn som alt er hentet i reconen (K-100, ~/khepri-data/kdf-recon-np/jao/np_fbdsp_<døgn>.json.gz) tas inn med reconens
hentetidspunkt og samme kontroll, uten nytt kall («importert fra recon» i årsak).
Bruk: <recon-venv>/bin/python -I tools/hent_jao_fbdsp.py <ut>
"""
import csv
import datetime as dt
import gzip
import hashlib
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
from khepri_dc_fb import hent  # noqa: E402
from hent_jao import forretningsdoegn, start_utc  # noqa: E402

RECON = Path.home() / "khepri-data/kdf-recon-np/jao"
SONER = [f"NetPosition_NO{i}" for i in range(1, 6)]
FILTER = json.dumps({"CnecName": "Netposition"})


def kontroll(rows):
    if not isinstance(rows, list) or not rows:
        return False, "tom eller ikke liste"
    if not all(isinstance(r, dict) and {"dateTimeUtc", "cnecName", "flowFb"} <= set(r) for r in rows):
        return False, "rad mangler dateTimeUtc/cnecName/flowFb"
    mangler = [s for s in SONER if s not in {r["cnecName"] for r in rows}]
    return (False, "mangler " + " ".join(mangler)) if mangler else (True, "")


def lagre(out, manifest, dag, rows, hentet, aarsak=""):
    rad = dict(kilde="JAO/fbDomainShadowPrice", noekkel="fbDomainShadowPrice", vindu_start=dag, vindu_slutt=dag,
               hentet_utc=hentet)
    if not rows:
        rad.update(status="INGEN_DATA", kontrollstreng_funnet="nei", aarsak=aarsak or "tom liste")
    else:
        ok, a = kontroll(rows)
        body = json.dumps(rows, ensure_ascii=False).encode()
        (out / f"jao_fbDomainShadowPrice_{dag}.json.gz").write_bytes(gzip.compress(body))
        rad.update(status="OK" if ok else "FEILET", kontrollstreng_funnet="ja" if ok else "nei",
                   aarsak="; ".join(x for x in (a, aarsak) if x), sha256=hashlib.sha256(body).hexdigest(), bytes=len(body))
    hent.skriv_manifestrad(manifest, rad)
    return rad


def main():
    out = Path(sys.argv[1]).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    manifest = out / "manifest.csv"
    ferdig = set()
    if manifest.exists():
        ferdig = {r["vindu_start"] for r in csv.DictReader(open(manifest, encoding="utf-8")) if r["status"] in ("OK", "INGEN_DATA")}
    recon_tid = {r["doegn"]: r["hentet_utc"] for r in csv.DictReader(open(RECON / "manifest.csv", encoding="utf-8"))}
    from jao import JaoPublicationToolClient, JaoPublicationToolPandasNordics

    class RawNordic(JaoPublicationToolClient):
        BASEURL = JaoPublicationToolPandasNordics.BASEURL

    c = RawNordic()
    tempo = hent.Tempo()
    logg = open(out / "hentelogg.txt", "a", encoding="utf-8")
    for d in forretningsdoegn():
        dag = str(d)
        if dag in ferdig:
            continue
        p = RECON / f"np_fbdsp_{dag}.json.gz"
        if p.exists() and dag in recon_tid:
            rows = json.loads(gzip.decompress(p.read_bytes()))["data"]
            rad = lagre(out, manifest, dag, rows, recon_tid[dag], "importert fra recon (K-100)")
            logg.write(f"{hent.naa_utc()} {dag} {rad['status']} importert fra recon\n")
            continue
        fra = start_utc(d)
        til = start_utc(d + dt.timedelta(days=1))
        params = {"FromUtc": fra.strftime("%Y-%m-%dT%H:%M:%S.000Z"), "ToUtc": til.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                  "Skip": 0, "Take": 5000, "Filter": FILTER}
        for forsok in range(1, 4):
            try:
                tempo.vent()
                r = c.s.get(c.BASEURL + "fbDomainShadowPrice", params=params, timeout=300)
                r.raise_for_status()
                j = r.json()
                rows = j.get("data") or []
                if rows and j.get("totalRowsWithFilter") != len(rows):
                    raise RuntimeError(f"ufullstendig: {len(rows)} av {j.get('totalRowsWithFilter')}")
                rad = lagre(out, manifest, dag, rows, hent.naa_utc())
                break
            except Exception as e:
                logg.write(f"{hent.naa_utc()} {dag} forsøk {forsok} {hent.saner(type(e).__name__ + ': ' + str(e))[:200]}\n")
                logg.flush()
                if forsok == 3:
                    rad = dict(kilde="JAO/fbDomainShadowPrice", noekkel="fbDomainShadowPrice", vindu_start=dag,
                               vindu_slutt=dag, status="FEILET", kontrollstreng_funnet="nei",
                               aarsak=f"3 forsøk: {type(e).__name__}", hentet_utc=hent.naa_utc())
                    hent.skriv_manifestrad(manifest, rad)
                    break
                kode = getattr(getattr(e, "response", None), "status_code", None)
                time.sleep(hent.ventetid_429(dict(e.response.headers)) if kode == 429 else [10, 30][forsok - 1])
        logg.write(f"{hent.naa_utc()} {dag} {rad['status']} {rad.get('aarsak', '')}\n")
        logg.flush()
    logg.write(f"{hent.naa_utc()} FERDIG\n")


if __name__ == "__main__":
    main()
