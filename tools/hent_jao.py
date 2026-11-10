"""Dataruna steg 1: JAO Nordic netPos og maxNetPos for alle forretningsdøgn som overlapper perioden.

Perioden er [2024-10-30T00:00Z, 2026-11-01T00:00Z) [GT-361, GT-379]. Forretningsdøgnet er norsk døgn (Europe/Oslo),
som starter 23:00Z ved normaltid og 22:00Z ved sommertid [GT-373, GT-393]. Døgnene regnes ut, ikke hardkodes:
døgn D tas med når [start(D), start(D+1)) overlapper perioden.

Klient: jao-py 0.8.7 (recon-venv), rå klient med nordisk BASEURL, som i recon-skriptet 09.11
(~/khepri-data/recon-fb-2026-11-09/kode/hent_jao_nordic_maxnp.py). User-Agent er jao-py sin egen (uten e-post).
Tempo: dataruna 10.11 brukte recon-skriptets tempo (ingen pause, K-85). For senere henting er det en fast pause på
khepri_dc_fb.hent.PAUSE_MELLOM_KALL_S mellom kallene og ventetid etter Retry-After / VENT_VED_429_S ved HTTP 429
(etter JAOs fire 429-svar i A2-hentingen, GT-664–GT-667).
Forbigående feil: høyst 3 forsøk per døgn og datasett, med backoff 10 s og 30 s. NoMatchingDataError og tom liste er
ikke forbigående: de føres straks som fravær med feilnavn (preregistrering avsnitt 12).
Rådata: én fil per døgn og datasett i utkatalogen (utenfor git); manifest.csv med sha256, hentetidspunkt (UTC),
kontrollstreng og utfall (khepri_dc_fb.hent.lagre_jao). Døgn med status OK eller INGEN_DATA i manifestet hoppes over
ved omstart.
Bruk: <recon-venv>/bin/python -I tools/hent_jao.py <utkatalog> [døgnliste]
  døgnliste: skriver bare døgnene (første, siste, antall) og avslutter, uten nettkall.
"""
import datetime as dt
import csv
import hashlib
import json
import sys
import time
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from khepri_dc_fb import hent  # noqa: E402

A = dt.datetime(2024, 10, 30, tzinfo=dt.timezone.utc)
B = dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc)
OSLO = ZoneInfo("Europe/Oslo")
PAUSE_S = hent.PAUSE_MELLOM_KALL_S
BACKOFF_S = [10, 30]
MAKS_FORSOK = 3
RECON_SKRIPT = Path.home() / "khepri-data/recon-fb-2026-11-09/kode/hent_jao_nordic_maxnp.py"


def start_utc(d: dt.date) -> dt.datetime:
    return dt.datetime(d.year, d.month, d.day, tzinfo=OSLO).astimezone(dt.timezone.utc)


def forretningsdoegn() -> list[dt.date]:
    d = (A - dt.timedelta(days=2)).date()
    ut = []
    while start_utc(d) < B:
        if start_utc(d + dt.timedelta(days=1)) > A:
            ut.append(d)
        d += dt.timedelta(days=1)
    return ut


def main() -> None:
    out = Path(sys.argv[1]).expanduser()
    dager = forretningsdoegn()
    if sys.argv[2:] == ["døgnliste"]:
        print(dager[0], dager[-1], len(dager), start_utc(dager[0]).isoformat(), start_utc(dager[-1]).isoformat())
        return
    import pandas as pd
    from importlib.metadata import version
    from jao import JaoPublicationToolClient, JaoPublicationToolPandasNordics
    from jao.exceptions import NoMatchingDataError

    class RawNordic(JaoPublicationToolClient):
        BASEURL = JaoPublicationToolPandasNordics.BASEURL

    out.mkdir(parents=True, exist_ok=True)
    manifest = out / "manifest.csv"
    ferdig = set()
    if manifest.exists():
        for r in csv.DictReader(open(manifest, encoding="utf-8")):
            if r["status"] in ("OK", "INGEN_DATA"):
                ferdig.add((r["noekkel"], r["vindu_start"]))
    c = RawNordic()
    param = out / "hente_parametre.json"
    if not param.exists():
        param.write_text(json.dumps(dict(
            jao_py=version("jao-py"), user_agent=c.s.headers.get("user-agent"), baseurl=c.BASEURL,
            pause_s=PAUSE_S, pause_kilde="khepri_dc_fb.hent.PAUSE_MELLOM_KALL_S (etter HTTP 429 i A2-hentingen, GT-664–GT-667)",
            maks_forsok=MAKS_FORSOK, backoff_s=BACKOFF_S, periode=[A.isoformat(), B.isoformat()],
            doegn_foerste=str(dager[0]), doegn_siste=str(dager[-1]), doegn_antall=len(dager),
            startet_utc=hent.naa_utc()), ensure_ascii=False, indent=1))
    logg = open(out / "hentelogg.txt", "a", encoding="utf-8")
    for d in dager:
        for navn, fn in (("netPos", c.query_net_position), ("maxNetPos", c.query_minmax_np)):
            if (navn, str(d)) in ferdig:
                continue
            day = pd.Timestamp(str(d), tz="Europe/Oslo")
            for forsok in range(1, MAKS_FORSOK + 1):
                try:
                    rows = fn(day=day)
                    if rows:
                        rad = hent.lagre_jao(out, manifest, navn, str(d), rows)
                    else:
                        rad = hent.lagre_jao(out, manifest, navn, str(d), None, "tom liste")
                    break
                except NoMatchingDataError:
                    rad = hent.lagre_jao(out, manifest, navn, str(d), None, "NoMatchingDataError")
                    break
                except Exception as e:  # forbigående: nettverk, tidsavbrudd, HTTP-feil
                    feil = hent.saner(f"{type(e).__name__}: {e}")[:200]
                    logg.write(f"{hent.naa_utc()} {navn} {d} forsøk {forsok} {feil}\n")
                    logg.flush()
                    if forsok == MAKS_FORSOK:
                        rad = dict(kilde=f"JAO/{navn}", noekkel=navn, vindu_start=str(d), vindu_slutt=str(d),
                                   status="FEILET", kontrollstreng_funnet="nei",
                                   aarsak=f"{MAKS_FORSOK} forsøk: {type(e).__name__}", hentet_utc=hent.naa_utc())
                        hent.skriv_manifestrad(manifest, rad)
                        break
                    kode = getattr(getattr(e, "response", None), "status_code", None)
                    time.sleep(hent.ventetid_429(dict(e.response.headers)) if kode == 429 else BACKOFF_S[forsok - 1])
            logg.write(f"{hent.naa_utc()} {navn} {d} {rad['status']} {rad.get('aarsak', '')}\n")
            logg.flush()
            if PAUSE_S:
                time.sleep(PAUSE_S)
    logg.write(f"{hent.naa_utc()} FERDIG\n")
    logg.close()


if __name__ == "__main__":
    main()
