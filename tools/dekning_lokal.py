"""Steg 3c-supplement, punkt 1: dekning regnet LOKALT (ingen henting) for A65, A75 og A11, NO1–NO5,
2024-10-30T00:00Z–2026-01-01T00:00Z, per månedsvindu i UTC.

Kilder (fra KHEPRI-DC v1 truth/SHA256_RAADATA og Eiriks instruks):
  X  /Volumes/Vault/khepri-dc/raw/{A65,A75,A11}/*.xml           ENTSO-E XML (v1-henting)
  R  ~/khepri-data/raw/entsoe-rest/NO{n}_generation_{år}.csv     A75 CSV (entsoe-py-format)
  F  /Volumes/Vault/khepri-data/flowtracing/raw/2025/{A65,A75,A11}/*.csv   CSV per måned (entsoe-py-format)
  K  ~/khepri-data/kdf-meta-2026-11-09/entsoe_raw/{A65,A75,A11}/<område>/*.xml.gz   (hentet 09.11 via API: 16 A65 NO1-vinduer
     før stopp + hullene i 2026)
Regler:
  - CSV leses etter kolonnenavn. Headerform detekteres per fil: én headerlinje («,Kol1,Kol2»), én flatet linje
    («,Type|Actual Aggregated,Type|Actual Consumption») eller to linjer («,Type…» + «,Actual Aggregated…»).
    A65: kolonnen «Actual Load» (andre kolonner ignoreres). A11: kolonnen «MW» eller eneste verdikolonne.
    A75: produksjonstypekolonner; ved flatet eller todelt header bare «Actual Aggregated» (ikke «Actual Consumption»).
  - Varighetsvekt: hver rad dekker fra sitt tidsstempel til neste (maks 60 min); siste rad får samme lengde som forrige.
    Dekning telles i kvarter (15 min) innenfor vinduet; en rad «har verdi» når minst én valgt kolonne ikke er tom.
  - XML: A01 = bare oppgitte posisjoner; A03 = hold forrige verdi til neste posisjon eller periodens slutt.
  - Per (dok, område, måned) rapporteres dekning per kilde og unionen av kildene. A11 rapporteres per grenseretning,
    og per sone som minste dekning over sonens grenseretninger (NP fra A11 krever alle grenser).
Bruk: python3 -I -B tools/dekning_lokal.py <ut-csv> [slutt, ISO-dato, standard 2026-01-01]
"""
import csv
import datetime as dt
import gzip
import io
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

HOME = Path.home()
X = Path("/Volumes/Vault/khepri-dc/raw")
R = HOME / "khepri-data/raw/entsoe-rest"
F = Path("/Volumes/Vault/khepri-data/flowtracing/raw/2025")
K = HOME / "khepri-data/kdf-meta-2026-11-09/entsoe_raw"
ZONES = ["NO_1", "NO_2", "NO_3", "NO_4", "NO_5"]
BORDERS = ("NO_1-NO_2 NO_1-NO_3 NO_1-NO_5 NO_1-SE_3 NO_2-NO_5 NO_2-DK_1 NO_2-DE_LU NO_2-NL NO_2-GB NO_3-NO_4 "
           "NO_3-NO_5 NO_3-SE_2 NO_4-SE_1 NO_4-SE_2 NO_4-FI").split()
DIRS = [f"{a}__{b}" for bb in BORDERS for a, b in [bb.split("-"), bb.split("-")[::-1]]]
Q = dt.timedelta(minutes=15)
START = dt.datetime(2024, 10, 30, tzinfo=dt.timezone.utc)
SLUTT = dt.datetime.fromisoformat(sys.argv[2]).replace(tzinfo=dt.timezone.utc) if len(sys.argv) > 2 else \
    dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)


def vinduer():
    v, s = [(START, dt.datetime(2024, 11, 1, tzinfo=dt.timezone.utc))], dt.datetime(2024, 11, 1, tzinfo=dt.timezone.utc)
    while s < SLUTT:
        e = dt.datetime(s.year + (s.month == 12), s.month % 12 + 1, 1, tzinfo=dt.timezone.utc)
        v.append((s, e))
        s = e
    return v


def kvarter(t0, t1):
    t = t0 - dt.timedelta(minutes=t0.minute % 15, seconds=t0.second)
    while t < t1:
        if START <= t < SLUTT:
            yield t
        t += Q


# ---------- XML
def tid(s):
    return dt.datetime.strptime(s, "%Y-%m-%dT%H:%MZ").replace(tzinfo=dt.timezone.utc)


RES = {"PT15M": 15, "PT30M": 30, "PT60M": 60}


def xml_kvarter(body):
    """Returnerer (mengde kvarter med verdi, liste av per-serie-mengder, oppløsninger)."""
    deler = [body]
    if body[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(body)) as z:
            deler = [z.read(n) for n in z.namelist()]
    alle, per, res = set(), [], set()
    for d in deler:
        if b"TimeSeries" not in d:
            continue
        root = ET.fromstring(d)
        for ts in root.iterfind(".//{*}TimeSeries"):
            kurve = (ts.findtext("{*}curveType") or "A01").strip()
            s = set()
            for p in ts.iterfind("{*}Period"):
                ps, pe = tid(p.findtext("{*}timeInterval/{*}start")), tid(p.findtext("{*}timeInterval/{*}end"))
                rs = p.findtext("{*}resolution")
                res.add(rs)
                r = RES.get(rs)
                if not r:
                    continue
                n = int((pe - ps).total_seconds() // 60 // r)
                pos = sorted(int(x.findtext("{*}position")) for x in p.iterfind("{*}Point")
                             if (x.findtext("{*}quantity") or "") != "")
                dek = set()
                if kurve == "A03" and pos:
                    for i, q in enumerate(pos):
                        dek.update(range(q, pos[i + 1] if i + 1 < len(pos) else n + 1))
                else:
                    dek.update(pos)
                for q in dek:
                    t0 = ps + dt.timedelta(minutes=(q - 1) * r)
                    s.update(kvarter(t0, t0 + dt.timedelta(minutes=r)))
            per.append(s)
            alle |= s
    return alle, per, res


# ---------- CSV
def csv_kvarter(path, dok):
    rader = list(csv.reader(open(path, encoding="utf-8")))
    h1 = rader[0]
    to_header = len(rader) > 1 and rader[1] and rader[1][0] == "" and any("Actual" in c for c in rader[1][1:])
    data = rader[2:] if to_header else rader[1:]
    if dok == "A65":
        kol = [i for i, c in enumerate(h1) if c.strip() == "Actual Load"]
    elif dok == "A11":
        kol = [i for i, c in enumerate(h1) if c.strip() == "MW"] or [i for i in range(1, len(h1))][:1]
    else:
        if to_header:
            kol = [i for i in range(1, len(h1)) if rader[1][i].strip() == "Actual Aggregated"]
        else:  # én headerlinje, enten «Type» eller flatet «Type|Underkolonne»
            kol = [i for i in range(1, len(h1)) if "|" not in h1[i] or h1[i].strip().endswith("|Actual Aggregated")]
    flatet = any("|" in c for c in h1)
    form = ("2 headerlinjer" if to_header else ("1 headerlinje, flatet Type|Under" if flatet else "1 headerlinje")) + \
        f"; {len(kol)} valgte kolonner"
    if not kol:
        return set(), [], set(), form + " (INGEN GJENKJENT KOLONNE)"
    tider = [dt.datetime.fromisoformat(r[0]).astimezone(dt.timezone.utc) for r in data if r and r[0]]
    alle, per, res = set(), [set() for _ in kol], set()
    for i, r in enumerate(data):
        if not r or not r[0]:
            continue
        t0 = tider[i]
        lengde = (tider[i + 1] - t0) if i + 1 < len(tider) else ((t0 - tider[i - 1]) if i else dt.timedelta(minutes=60))
        lengde = min(lengde, dt.timedelta(minutes=60))
        res.add(int(lengde.total_seconds() // 60))
        ks = list(kvarter(t0, t0 + lengde))
        for j, k in enumerate(kol):
            if k < len(r) and r[k].strip() not in ("", "nan", "NaN"):
                per[j].update(ks)
                alle.update(ks)
    return alle, per, {f"PT{m}M" for m in res}, form


# ---------- kildefiler per (dok, område)
def kildefiler(dok, omr):
    ut = []
    if dok in ("A65", "A75"):
        ut += [("X", p) for p in sorted((X / dok).glob(f"{dok}_{omr}_*.xml"))]
        ut += [("F", p) for p in sorted((F / dok).glob(f"{dok}_{omr}_2025-*.csv"))]
        if dok == "A75":
            n = omr[-1]
            ut += [("R", p) for p in sorted(R.glob(f"NO{n}_generation_202[456].csv"))]
        ut += [("K", p) for p in sorted((K / dok / omr).glob("*.xml.gz"))]
    else:
        ut += [("X", p) for p in sorted((X / "A11").glob(f"A11_{omr}_*.xml"))]
        ut += [("F", p) for p in sorted((F / "A11").glob(f"A11_{omr}_2025-*.csv"))]
        ut += [("K", p) for p in sorted((K / "A11" / omr.replace("__", "_til_")).glob("*.xml.gz"))]
    return ut


def les(kilde, p, dok):
    if p.suffix == ".gz":
        return (*xml_kvarter(gzip.decompress(p.read_bytes())), "XML (gz)")
    if p.suffix == ".xml":
        return (*xml_kvarter(p.read_bytes()), "XML")
    return csv_kvarter(p, dok)


out = Path(sys.argv[1])
felt = ["dok", "omraade", "maaned", "kvarter_forventet", "union_dekket", "union_andel", "X_andel", "R_andel", "F_andel",
        "K_andel", "min_andel_per_kolonne_beste_kilde", "opploesninger", "headerformer", "filer"]
rows = []
for dok, omrader in [("A65", ZONES), ("A75", ZONES), ("A11", DIRS)]:
    for omr in omrader:
        per_kilde, formar, opp, filer, kolmin = {}, set(), set(), [], {}
        for kilde, p in kildefiler(dok, omr):
            alle, per, res, form = les(kilde, p, dok)
            if not alle:
                continue
            per_kilde.setdefault(kilde, set()).update(alle)
            kolmin.setdefault(kilde, []).append(per)
            formar.add(f"{kilde}: {form}")
            opp |= res
            filer.append(str(p).replace(str(HOME), "~"))
        for s, e in vinduer():
            forv = int((e - s) / Q)
            ivindu = {k: {t for t in v if s <= t < e} for k, v in per_kilde.items()}
            union = set().union(*ivindu.values()) if ivindu else set()
            beste = max(ivindu, key=lambda k: len(ivindu[k]), default=None)
            mn = ""
            if beste and dok == "A75":
                kol = [c for per in kolmin[beste] for c in per]
                kol = [{t for t in c if s <= t < e} for c in kol]
                kol = [c for c in kol if c]
                mn = f"{min(len(c) for c in kol) / forv:.4f}" if kol else ""
            rows.append(dict(dok=dok, omraade=omr, maaned=f"{s:%Y-%m}" if s.day == 1 else f"{s:%Y-%m-%d}",
                             kvarter_forventet=forv, union_dekket=len(union), union_andel=f"{len(union) / forv:.4f}",
                             **{f"{k}_andel": (f"{len(ivindu[k]) / forv:.4f}" if k in ivindu else "") for k in "XRFK"},
                             min_andel_per_kolonne_beste_kilde=mn, opploesninger=" ".join(sorted(opp)),
                             headerformer=" ; ".join(sorted(formar)), filer=len(filer)))
        print(dok, omr, "kilder:", {k: len(v) for k, v in per_kilde.items()}, flush=True)
# A11 per sone = minste dekning over sonens grenseretninger
for z in ZONES:
    mine = [d for d in DIRS if z in d.split("__")]
    for s, e in vinduer():
        m = f"{s:%Y-%m}" if s.day == 1 else f"{s:%Y-%m-%d}"
        a = [float(r["union_andel"]) for r in rows if r["dok"] == "A11" and r["omraade"] in mine and r["maaned"] == m]
        rows.append(dict(dok="A11-sone(min)", omraade=z, maaned=m, kvarter_forventet=int((e - s) / Q), union_dekket="",
                         union_andel=f"{min(a):.4f}", filer=len(mine)))
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=felt, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
print("skrev", out, len(rows))
