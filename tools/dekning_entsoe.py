"""Steg 3c-supplement: dekning (bare metadata) for ENTSO-E A65, A75 og A11, NO1–NO5, månedsvinduer i UTC 2024-10-30 → 2026-11-01.

- Token leses fra miljøvariabelen ENTSOE_API_TOKEN (lastes av kalleren fra ~/.config/khepri/entsoe.env i samme kommando).
  Tokenet skrives aldri ut; URL-er i logg saneres (securityToken fjernes).
- 5 s mellom kall; HTTP 429 -> 90 s pause; 5xx og 400 med «Timeout deadline»/«I/O error» er forbigående; maks 3 forsøk.
- Rå XML (gzip) til <ut>/entsoe_raw/<dok>/<område>/<YYYY-MM>.xml.gz (utenfor git). Oppsummering: <ut>/dekning_entsoe.csv.
- Dekning telles i kvarter (15 min): en MTU på 60 min dekker fire kvarter. Kurvetype A03 (variable blokker) ekspanderes:
  en manglende posisjon betyr at forrige verdi gjelder til neste posisjon eller periodens slutt. A01: bare oppgitte posisjoner.
- Kontrollstreng for vellykket datasvar: «TimeSeries». Svar uten data: Acknowledgement_MarketDocument (årsakskode føres).
- Gjenopptakbart: rader som alt står i oppsummeringen med status OK/INGEN_DATA hoppes over.
Bruk: set -a; . ~/.config/khepri/entsoe.env; set +a; <venv>/bin/python -I tools/dekning_entsoe.py <ut> [--hull <lokal-dekning.csv>]
      Med --hull hentes bare (dok, område, måned) der lokal unionsdekning er under 1 (Eiriks instruks: hent bare hullene).
"""
import csv
import datetime as dt
import gzip
import hashlib
import io
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from entsoe.mappings import Area

OUT = Path(sys.argv[1])
RAW = OUT / "entsoe_raw"
SUM = OUT / "dekning_entsoe.csv"
LOG = OUT / "dekning_entsoe.log"
API = "https://web-api.tp.entsoe.eu/api"
UA = "EcoDeco-research/1.0"
TOKEN = os.environ.get("ENTSOE_API_TOKEN", "")
if not (len(TOKEN) == 36 and TOKEN.count("-") == 4):
    sys.exit("ENTSOE_API_TOKEN mangler eller har uventet form (verdien vises ikke)")

ZONES = ["NO_1", "NO_2", "NO_3", "NO_4", "NO_5"]
# Samme 15 grenser som KHEPRI-DC v1 (build/build_series.py), begge retninger
BORDERS = ("NO_1-NO_2 NO_1-NO_3 NO_1-NO_5 NO_1-SE_3 NO_2-NO_5 NO_2-DK_1 NO_2-DE_LU NO_2-NL NO_2-GB NO_3-NO_4 "
           "NO_3-NO_5 NO_3-SE_2 NO_4-SE_1 NO_4-SE_2 NO_4-FI").split()
FIELDS = ["dok", "omraade", "maaned", "vindu_start", "vindu_slutt", "status", "http", "forsok", "kontrollstreng_funnet",
          "ack_aarsak", "opploesninger", "kurvetyper", "mtu_med_verdi", "kvarter_dekket", "kvarter_forventet", "andel",
          "serier", "min_andel_per_serie", "sha256_raa", "hentet_utc"]


def utc(y, m, d=1):
    return dt.datetime(y, m, d, tzinfo=dt.timezone.utc)


def vinduer():
    v = [(utc(2024, 10, 30), utc(2024, 11, 1))]
    s = utc(2024, 11, 1)
    while s < utc(2026, 11, 1):
        e = utc(s.year + (s.month == 12), s.month % 12 + 1)
        v.append((s, e))
        s = e
    return v


def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def log(msg):
    msg = re.sub(r"securityToken=[^&\s]+", "securityToken=***", msg)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(f"{now()} {msg}\n")


def params_for(dok, omr):
    if dok == "A65":
        return {"documentType": "A65", "processType": "A16", "outBiddingZone_Domain": Area[omr].code}
    if dok == "A75":
        return {"documentType": "A75", "processType": "A16", "in_Domain": Area[omr].code}
    fra, til = omr.split(">")
    return {"documentType": "A11", "out_Domain": Area[fra].code, "in_Domain": Area[til].code}


def hent(q):
    url = API + "?" + urllib.parse.urlencode({**q, "securityToken": TOKEN})
    for forsok in range(1, 4):
        time.sleep(5)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.status, r.read(), forsok
        except urllib.error.HTTPError as e:
            body = e.read() or b""
            txt = body[:2000].decode("utf-8", "replace")
            log(f"HTTP {e.code} forsøk {forsok} {urllib.parse.urlencode(q)} :: {re.sub(r'\s+', ' ', txt)[:300]}")
            if e.code == 429:
                time.sleep(90)
                continue
            if e.code >= 500 or (e.code == 400 and re.search(r"Timeout deadline|I/O error", txt)):
                continue
            return e.code, body, forsok
        except (urllib.error.URLError, TimeoutError) as e:
            log(f"NETTFEIL forsøk {forsok} {urllib.parse.urlencode(q)} :: {type(e).__name__}")
            continue
    return -1, b"", 3


RES = {"PT15M": 15, "PT30M": 30, "PT60M": 60}


def tid(s):
    return dt.datetime.strptime(s, "%Y-%m-%dT%H:%MZ").replace(tzinfo=dt.timezone.utc)


def dekning(xmls, start, slutt):
    alle, per_serie, res_set, kurver, mtu = set(), [], set(), set(), {}
    for x in xmls:
        root = ET.fromstring(x)
        for ts in root.iterfind(".//{*}TimeSeries"):
            kurve = (ts.findtext("{*}curveType") or "A01").strip()
            kurver.add(kurve)
            s_kv = set()
            for per in ts.iterfind("{*}Period"):
                ps = tid(per.findtext("{*}timeInterval/{*}start"))
                pe = tid(per.findtext("{*}timeInterval/{*}end"))
                rs = per.findtext("{*}resolution")
                res_set.add(rs)
                r = RES.get(rs)
                if r is None:
                    continue
                n = int((pe - ps).total_seconds() // 60 // r)
                pos = sorted(int(p.findtext("{*}position")) for p in per.iterfind("{*}Point")
                             if p.findtext("{*}quantity") not in (None, ""))
                dekket = set()
                if kurve == "A03" and pos:
                    for i, p in enumerate(pos):
                        dekket.update(range(p, (pos[i + 1] if i + 1 < len(pos) else n + 1)))
                else:
                    dekket.update(pos)
                mtu[rs] = mtu.get(rs, 0) + len(dekket)
                for p in dekket:
                    t0 = ps + dt.timedelta(minutes=(p - 1) * r)
                    for k in range(r // 15):
                        t = t0 + dt.timedelta(minutes=15 * k)
                        if start <= t < slutt:
                            s_kv.add(t)
            per_serie.append(s_kv)
            alle |= s_kv
    forventet = int((slutt - start).total_seconds() // 900)
    min_andel = min((len(s) / forventet for s in per_serie), default=0.0)
    return dict(opploesninger=" ".join(sorted(res_set)), kurvetyper=" ".join(sorted(kurver)),
                mtu_med_verdi=" ".join(f"{k}:{v}" for k, v in sorted(mtu.items())), kvarter_dekket=len(alle),
                kvarter_forventet=forventet, andel=f"{len(alle) / forventet:.4f}", serier=len(per_serie),
                min_andel_per_serie=f"{min_andel:.4f}")


def xml_deler(body):
    if body[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(body)) as z:
            return [z.read(n) for n in z.namelist()]
    return [body]


if "--omregn" in sys.argv:
    rows = list(csv.DictReader(open(SUM, encoding="utf-8")))
    for r in rows:
        if r["status"] == "OK":
            p = RAW / r["dok"] / r["omraade"].replace(">", "_til_") / f"{r['maaned']}.xml.gz"
            body = gzip.decompress(p.read_bytes())
            assert hashlib.sha256(body).hexdigest() == r["sha256_raa"], p
            r.update(dekning(xml_deler(body), tid(r["vindu_start"][:16] + "Z"), tid(r["vindu_slutt"][:16] + "Z")))
    with open(SUM, "w", newline="", encoding="utf-8") as fh2:
        w2 = csv.DictWriter(fh2, fieldnames=FIELDS)
        w2.writeheader()
        w2.writerows(rows)
    log(f"OMREGNET {sum(r['status'] == 'OK' for r in rows)} rader fra rådata")
    sys.exit(0)

ferdig = set()
if SUM.exists():
    for r in csv.DictReader(open(SUM, encoding="utf-8")):
        if r["status"] in ("OK", "INGEN_DATA"):
            ferdig.add((r["dok"], r["omraade"], r["maaned"]))
ny = not SUM.exists()
fh = open(SUM, "a", newline="", encoding="utf-8")
w = csv.DictWriter(fh, fieldnames=FIELDS)
if ny:
    w.writeheader()

jobber = [("A65", z) for z in ZONES] + [("A75", z) for z in ZONES] + \
         [("A11", f"{a}>{b}") for bb in BORDERS for a, b in [bb.split("-"), bb.split("-")[::-1]]]
hull = None
if "--hull" in sys.argv:  # bare (dok, område, måned) med lokal unionsdekning < 1 (fra tools/dekning_lokal.py)
    hp = Path(sys.argv[sys.argv.index("--hull") + 1])
    hull = {(r["dok"], r["omraade"].replace("__", ">"), r["maaned"]) for r in csv.DictReader(open(hp, encoding="utf-8"))
            if r["dok"] in ("A65", "A75", "A11") and r["union_andel"] != "1.0000"}
log(f"START {len(jobber)} serier × {len(vinduer())} vinduer" + (f", bare {len(hull)} hull" if hull is not None else ""))
for dok, omr in jobber:
    for start, slutt in vinduer():
        if hull is not None and (dok, omr, f"{start:%Y-%m}" if start.day == 1 else f"{start:%Y-%m-%d}") not in hull:
            continue
        mnd = f"{start:%Y-%m}" if start.day == 1 else f"{start:%Y-%m-%d}"
        if (dok, omr, mnd) in ferdig:
            continue
        q = {**params_for(dok, omr), "periodStart": f"{start:%Y%m%d%H%M}", "periodEnd": f"{slutt:%Y%m%d%H%M}"}
        status, body, forsok = hent(q)
        rad = dict(dok=dok, omraade=omr, maaned=mnd, vindu_start=start.isoformat().replace("+00:00", "Z"),
                   vindu_slutt=slutt.isoformat().replace("+00:00", "Z"), http=status, forsok=forsok, hentet_utc=now())
        p = RAW / dok / omr.replace(">", "_til_") / f"{mnd}.xml.gz"
        p.parent.mkdir(parents=True, exist_ok=True)
        if body:
            p.write_bytes(gzip.compress(body))
            rad["sha256_raa"] = hashlib.sha256(body).hexdigest()
        txt = body.decode("utf-8", "replace") if body[:2] != b"PK" else ""
        if status == 200 and (b"TimeSeries" in body or body[:2] == b"PK"):
            try:
                rad.update(dekning(xml_deler(body), start, slutt), status="OK", kontrollstreng_funnet="ja")
            except ET.ParseError as e:
                rad.update(status=f"PARSEFEIL {e}", kontrollstreng_funnet="ja")
        elif "Acknowledgement_MarketDocument" in txt:
            aarsak = re.sub(r"\s+", " ", " ".join(re.findall(r"<(?:\w+:)?text>([^<]*)<", txt)))[:200]
            kode = ",".join(re.findall(r"<(?:\w+:)?code>([^<]*)<", txt))
            rad.update(status="INGEN_DATA" if "999" in kode else f"ACK {kode}", kontrollstreng_funnet="nei",
                       ack_aarsak=f"{kode}: {aarsak}", kvarter_dekket=0,
                       kvarter_forventet=int((slutt - start).total_seconds() // 900), andel="0.0000")
        else:
            rad.update(status=f"FEILET http={status}", kontrollstreng_funnet="nei")
        w.writerow(rad)
        fh.flush()
        log(f"{dok} {omr} {mnd} {rad['status']} {rad.get('andel', '')}")
log("SLUTT")
fh.close()
