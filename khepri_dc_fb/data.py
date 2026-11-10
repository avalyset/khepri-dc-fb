"""KHEPRI-DC-FB dataruna: innlesing av lagrede rådata til intervaller og kvarter (ingen nettkall).

Regler fra preregistreringen (tagg prereg-v1):
- JAO: én fil per forretningsdøgn og datasett; MTU-lengden er tiden til neste tidsstempel i døgnet, for siste MTU
  tiden til døgnets slutt. Forretningsdøgnet er norsk døgn [GT-373]. Tidsstempel = intervallstart, anker A [GT-315].
- MTU-skiftet per datasett: første døgn der alle MTU er 15 minutter («96 MTU» [GT-209, GT-373]); skillet er den seneste
  av datasettenes datoer [GT-355]. Døgn mellom datoene hører til 60-minuttersdelperioden [GT-373, GT-378].
- ENTSO-E-XML: kurvetype A03 = hold forrige verdi til neste posisjon eller periodens slutt; A01 = bare oppgitte
  posisjoner [GT-352]. Tom quantity = ingen verdi.
- CSV (flowtracing, entsoe-rest): intervallet har verdi når cellen for intervallstarten er ikke-tom og ikke NaN; null er
  en verdi (prereg avsnitt 5). Radens lengde = minste avstand til nabo-tidsstemplene, høyst 60 min (AVVIK_FRA_PREREG.md, T5).
- Kildeprioritet K > X > F > R per kvarter og serie [GT-358, GT-376].
Alt holdes i kvarter (15 min): et timeintervall gir fire kvarter med samme verdi, noe som gir samme varighetsvekting.
"""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import io
import json
import math
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable, Optional
from zoneinfo import ZoneInfo

UTC = dt.timezone.utc
OSLO = ZoneInfo("Europe/Oslo")
Q = dt.timedelta(minutes=15)
A = dt.datetime(2024, 10, 30, tzinfo=UTC)
B = dt.datetime(2026, 11, 1, tzinfo=UTC)
PRIORITET = ["K", "X", "F", "R"]
RES = {"PT15M": 15, "PT30M": 30, "PT60M": 60}
EIC = {"10YNO-1--------2": "NO_1", "10YNO-2--------T": "NO_2", "10YNO-3--------J": "NO_3",
       "10YNO-4--------9": "NO_4", "10Y1001A1001A48H": "NO_5"}


def doegnstart(d: dt.date) -> dt.datetime:
    return dt.datetime(d.year, d.month, d.day, tzinfo=OSLO).astimezone(UTC)


def kvarter(t0: dt.datetime, minutter: int) -> list[dt.datetime]:
    return [t0 + i * Q for i in range(minutter // 15)]


# ---------------------------------------------------------------- JAO
def jao_doegn(rader: list[dict], dag: dt.date) -> list[tuple[dt.datetime, int, dict]]:
    """(start, minutter, rad) for ett forretningsdøgn, sortert. Lengde = tid til neste tidsstempel / døgnslutt."""
    slutt = doegnstart(dag + dt.timedelta(days=1))
    ts = sorted(((dt.datetime.fromisoformat(r["dateTimeUtc"].replace("Z", "+00:00")).astimezone(UTC), r) for r in rader),
                key=lambda x: x[0])
    ut = []
    for i, (t, r) in enumerate(ts):
        nxt = ts[i + 1][0] if i + 1 < len(ts) else slutt
        ut.append((t, int((nxt - t).total_seconds() // 60), r))
    return ut


def les_jao(rot: Path, datasett: str) -> dict[dt.date, list[tuple[dt.datetime, int, dict]]]:
    ut = {}
    for p in sorted(rot.glob(f"jao_{datasett}_*.json")):
        dag = dt.date.fromisoformat(p.stem.rsplit("_", 1)[1])
        ut[dag] = jao_doegn(json.loads(p.read_text(encoding="utf-8")), dag)
    return ut


def alle_kvarter_15(mtuer: list) -> bool:
    return bool(mtuer) and all(m == 15 for _, m, _ in mtuer)


def mtu_skifte(doegn: dict[dt.date, list]) -> Optional[dt.date]:
    """Første forretningsdøgn der alle MTU er 15 minutter [GT-209, GT-373]."""
    for d in sorted(doegn):
        if alle_kvarter_15(doegn[d]):
            return d
    return None


def jao_kvarterverdier(doegn: dict[dt.date, list], felt: str) -> dict[dt.datetime, tuple[int, Optional[float]]]:
    """MTU-start -> (minutter, verdi) for ett felt; None når feltet mangler eller er tomt."""
    ut = {}
    for d, mtuer in doegn.items():
        for t, m, r in mtuer:
            v = r.get(felt)
            ut[t] = (m, None if v is None or (isinstance(v, float) and math.isnan(v)) else float(v))
    return ut


def rutenett(skille: dt.datetime, a: dt.datetime = A, b: dt.datetime = B) -> list[tuple[dt.datetime, int]]:
    """Forventet JAO-rutenett: 60 min før skillet, 15 min fra skillet, innenfor [a, b) [GT-361]."""
    ut, t = [], a
    while t < b:
        m = 60 if t < skille else 15
        ut.append((t, m))
        t += dt.timedelta(minutes=m)
    return ut


def paa_rutenett(verdier: dict[dt.datetime, tuple[int, Optional[float]]], nett: list[tuple[dt.datetime, int]]) -> list[Optional[float]]:
    """Verdi per rutenett-MTU med varighetsvekting [GT-206]: samme MTU -> verdien; kortere MTU-er som dekker hele
    rutenett-MTU-en -> varighetsvektet middel; ellers None (ingen interpolering)."""
    ut = []
    for t, m in nett:
        if t in verdier and verdier[t][0] == m:
            ut.append(verdier[t][1])
            continue
        tot, s, ok, u = 0, 0.0, True, t
        while u < t + dt.timedelta(minutes=m):
            if u not in verdier or verdier[u][1] is None or verdier[u][0] <= 0:
                ok = False
                break
            mm = verdier[u][0]
            s += verdier[u][1] * mm
            tot += mm
            u += dt.timedelta(minutes=mm)
        ut.append(s / m if ok and tot == m else None)
    return ut


# ---------------------------------------------------------------- ENTSO-E XML
def tid(s: str) -> dt.datetime:
    return dt.datetime.strptime(s.strip(), "%Y-%m-%dT%H:%MZ").replace(tzinfo=UTC)


def xml_deler(body: bytes) -> list[bytes]:
    if body[:2] == b"\x1f\x8b":
        body = gzip.decompress(body)
    if body[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(body)) as z:
            return [z.read(n) for n in z.namelist()]
    return [body]


def xml_serier(body: bytes) -> list[dict]:
    """Hver TimeSeries: dict(psr, inn, ut, inn_bz, ut_bz, kurve, intervaller=[(start, minutter, verdi)])."""
    ut = []
    for d in xml_deler(body):
        if b"TimeSeries" not in d:
            continue
        root = ET.fromstring(d)
        for ts in root.iterfind(".//{*}TimeSeries"):
            kurve = (ts.findtext("{*}curveType") or "A01").strip()
            iv = []
            for p in ts.iterfind("{*}Period"):
                ps, pe = tid(p.findtext("{*}timeInterval/{*}start")), tid(p.findtext("{*}timeInterval/{*}end"))
                r = RES.get((p.findtext("{*}resolution") or "").strip())
                if not r:
                    continue
                n = int((pe - ps).total_seconds() // 60 // r)
                pkt = {}
                for x in p.iterfind("{*}Point"):
                    q = (x.findtext("{*}quantity") or "").strip()
                    if q != "":
                        pkt[int(x.findtext("{*}position"))] = float(q)
                pos = sorted(pkt)
                for i, q in enumerate(pos):
                    siste = (pos[i + 1] - 1 if i + 1 < len(pos) else n) if kurve == "A03" else q
                    for k in range(q, siste + 1):
                        iv.append((ps + dt.timedelta(minutes=(k - 1) * r), r, pkt[q]))
            ut.append(dict(psr=ts.findtext("{*}MktPSRType/{*}psrType"), inn=ts.findtext("{*}in_Domain.mRID"),
                           ut=ts.findtext("{*}out_Domain.mRID"), inn_bz=ts.findtext("{*}inBiddingZone_Domain.mRID"),
                           ut_bz=ts.findtext("{*}outBiddingZone_Domain.mRID"), kurve=kurve, intervaller=iv))
    return ut


# ---------------------------------------------------------------- CSV (entsoe-py-format)
def csv_tabell(path: Path) -> tuple[list[tuple[str, str]], list[tuple[dt.datetime, int, list[str]]]]:
    """Kolonner som (type, underkolonne) og rader som (start UTC, minutter, celler).

    Headerformer: én linje («Type» eller flatet «Type|Under»), eller to linjer («Type» + «Actual …»). Uten underkolonne
    er den «Actual Aggregated» (A75) eller kolonnenavnet selv (A11 «MW»). Lengde: minste avstand til naboradene, høyst 60.
    """
    rader = list(csv.reader(open(path, encoding="utf-8")))
    h1 = rader[0]
    to = len(rader) > 1 and rader[1] and rader[1][0] == "" and any("Actual" in c for c in rader[1][1:])
    data = [r for r in (rader[2:] if to else rader[1:]) if r and r[0]]
    kol = []
    for i in range(1, len(h1)):
        if to:
            kol.append((h1[i].strip(), rader[1][i].strip()))
        elif "|" in h1[i]:
            a, b = h1[i].split("|", 1)
            kol.append((a.strip(), b.strip()))
        else:
            kol.append((h1[i].strip(), "Actual Aggregated" if h1[i].strip() != "MW" else "MW"))
    tider = [dt.datetime.fromisoformat(r[0]).astimezone(UTC) for r in data]
    ut = []
    for i, r in enumerate(data):
        avst = []
        if i + 1 < len(tider):
            avst.append(tider[i + 1] - tider[i])
        if i > 0:
            avst.append(tider[i] - tider[i - 1])
        m = min([int(a.total_seconds() // 60) for a in avst] + [60])
        ut.append((tider[i], m, r[1:]))
    return kol, ut


def celleverdi(c: str) -> Optional[float]:
    c = c.strip()
    if c == "" or c.lower() == "nan":
        return None
    return float(c)


# ---------------------------------------------------------------- kvarterkart
def til_kvarter(intervaller: Iterable[tuple[dt.datetime, int, Optional[float]]], a=A, b=B) -> dict[dt.datetime, Optional[float]]:
    """Kvarter -> verdi (None = intervall finnes, men uten verdi). Bare kvarter i [a, b)."""
    ut = {}
    for t, m, v in intervaller:
        for k in kvarter(t, m):
            if a <= k < b:
                if v is not None or k not in ut:
                    ut[k] = v
    return ut


def slaa_sammen(per_kilde: dict[str, dict[dt.datetime, Optional[float]]]) -> dict[dt.datetime, tuple[float, str]]:
    """Kvarter -> (verdi, kilde) fra kilden med høyest prioritet som har verdi [GT-376]."""
    ut = {}
    for k in reversed(PRIORITET):
        for t, v in per_kilde.get(k, {}).items():
            if v is not None:
                ut[t] = (v, k)
    return ut


# ---------------------------------------------------------------- lagrede ENTSO-E-kilder (samme stier som tools/dekning_lokal.py)
HOME = Path.home()
KILDE_X = Path("/Volumes/Vault/khepri-dc/raw")
KILDE_F = Path("/Volumes/Vault/khepri-data/flowtracing/raw/2025")
KILDE_R = HOME / "khepri-data/raw/entsoe-rest"
KILDE_K = HOME / "khepri-data/kdf-meta-2026-11-09/entsoe_raw"
SONER = ["NO_1", "NO_2", "NO_3", "NO_4", "NO_5"]
PUMPESONER = ["NO_2", "NO_3", "NO_5"]  # NO1 og NO4: A68 «n/e», pumpeleddet er 0 [GT-329, GT-332, GT-354]
GRENSER = ("NO_1-NO_2 NO_1-NO_3 NO_1-NO_5 NO_1-SE_3 NO_2-NO_5 NO_2-DK_1 NO_2-DE_LU NO_2-NL NO_2-GB NO_3-NO_4 "
           "NO_3-NO_5 NO_3-SE_2 NO_4-SE_1 NO_4-SE_2 NO_4-FI").split()
RETNINGER = [f"{a}__{b}" for g in GRENSER for a, b in [g.split("-"), g.split("-")[::-1]]]
AAR = ("2024", "2025", "2026")
MAGASIN, PUMPE = "Hydro Water Reservoir", "Hydro Pumped Storage"
PSR = {"B12": MAGASIN, "B10": PUMPE}


def aar_i_navn(p: Path) -> str:
    """Året i et v1-filnavn, enten «…_<år>.xml» eller «…_<år>-<mm>.xml»."""
    return p.stem.rsplit("_", 1)[1][:4]


def a75_filer(sone: str) -> list[tuple[str, Path]]:
    n = sone[-1]
    ut = [("X", p) for p in sorted((KILDE_X / "A75").glob(f"A75_{sone}_*.xml")) if aar_i_navn(p) in AAR]
    ut += [("F", p) for p in sorted((KILDE_F / "A75").glob(f"A75_{sone}_2025-*.csv"))]
    ut += [("R", p) for p in sorted(KILDE_R.glob(f"NO{n}_generation_202[456].csv"))]
    ut += [("K", p) for p in sorted((KILDE_K / "A75" / sone).glob("*.xml.gz"))]
    return ut


def a75_fil(kilde: str, p: Path, sone: str) -> dict:
    """Én A75-fil: dict(magasin, pumpe_prod, pumpe_forbruk) som intervallister [(start, min, verdi|None)], og
    univers = intervaller der minst én produksjonstype har verdi (som dekningen i GT-298), og antall CSV-rader
    med lengde ulik 15 og 60 (T5)."""
    ut = dict(magasin=[], pumpe_prod=[], pumpe_forbruk=[], univers=set(), rare_lengder=0)
    if kilde in ("X", "K"):
        eic = next(k for k, v in EIC.items() if v == sone)
        for s in xml_serier(p.read_bytes()):
            if s["inn_bz"] == eic:
                ut["univers"].update((t, m) for t, m, v in s["intervaller"])
                if s["psr"] == "B12":
                    ut["magasin"] += s["intervaller"]
                elif s["psr"] == "B10":
                    ut["pumpe_prod"] += s["intervaller"]
            elif s["ut_bz"] == eic and s["psr"] == "B10":
                ut["pumpe_forbruk"] += s["intervaller"]
        return ut
    kol, rader = csv_tabell(p)
    agg = [i for i, (_, u) in enumerate(kol) if u == "Actual Aggregated"]
    idx = {(a, u): i for i, (a, u) in enumerate(kol)}
    for t, m, celler in rader:
        if m not in (15, 60):
            ut["rare_lengder"] += 1
        if any(i < len(celler) and celleverdi(celler[i]) is not None for i in agg):
            ut["univers"].add((t, m))
        for navn, key in (("magasin", (MAGASIN, "Actual Aggregated")), ("pumpe_prod", (PUMPE, "Actual Aggregated")),
                          ("pumpe_forbruk", (PUMPE, "Actual Consumption"))):
            i = idx.get(key)
            if i is not None and i < len(celler):
                ut[navn].append((t, m, celleverdi(celler[i])))
    return ut


def a75_sone(sone: str) -> dict:
    """Per kilde: kvarterkart for magasin, pumpe_prod og pumpe_forbruk, universet (native intervaller i perioden),
    pluss sammenslåtte kvarterkart etter prioritet."""
    per = {}
    for kilde, p in a75_filer(sone):
        f = a75_fil(kilde, p, sone)
        k = per.setdefault(kilde, dict(magasin={}, pumpe_prod={}, pumpe_forbruk={}, univers=set(), rare_lengder=0,
                                        filer=0))
        k["filer"] += 1
        k["rare_lengder"] += f["rare_lengder"]
        k["univers"].update(iv for iv in f["univers"] if A <= iv[0] < B)
        for navn in ("magasin", "pumpe_prod", "pumpe_forbruk"):
            for t, v in til_kvarter(f[navn]).items():
                if v is not None or t not in k[navn]:
                    k[navn][t] = v
    samlet = {navn: slaa_sammen({k: v[navn] for k, v in per.items()}) for navn in ("magasin", "pumpe_prod", "pumpe_forbruk")}
    return dict(per_kilde=per, samlet=samlet)


def a11_filer(retning: str) -> list[tuple[str, Path]]:
    ut = [("X", p) for p in sorted((KILDE_X / "A11").glob(f"A11_{retning}_*.xml")) if aar_i_navn(p) in AAR]
    ut += [("F", p) for p in sorted((KILDE_F / "A11").glob(f"A11_{retning}_2025-*.csv"))]
    ut += [("K", p) for p in sorted((KILDE_K / "A11" / retning.replace("__", "_til_")).glob("*.xml.gz"))]
    return ut


def a11_retning(retning: str) -> dict:
    """Per kilde kvarterkart for flyt fra a til b (retning «a__b»), og sammenslått etter prioritet.
    XML kontrolleres mot domenene: NO-siden må stå som in_Domain (b) eller out_Domain (a)."""
    a, b = retning.split("__")
    per = {}
    for kilde, p in a11_filer(retning):
        k = per.setdefault(kilde, {})
        if kilde in ("X", "K"):
            for s in xml_serier(p.read_bytes()):
                if (b in EIC.values() and EIC.get(s["inn"]) != b) or (a in EIC.values() and EIC.get(s["ut"]) != a):
                    raise ValueError(f"A11-domene stemmer ikke med retningen {retning} i {p}")
                for t, v in til_kvarter(s["intervaller"]).items():
                    if v is not None or t not in k:
                        k[t] = v
        else:
            kol, rader = csv_tabell(p)
            i = 0
            for t, v in til_kvarter([(t0, m, celleverdi(c[i]) if i < len(c) else None) for t0, m, c in rader]).items():
                if v is not None or t not in k:
                    k[t] = v
    return dict(per_kilde=per, samlet=slaa_sammen(per))


# ---------------------------------------------------------------- JAO fbDomainShadowPrice (avvik A2, K-104)
def fbdsp_rader(rows: list[dict]) -> list[dict]:
    """Netposition-CNEC-rader («NetPosition_<BZ>», flowFb) -> én rad per tidsstempel med feltene hub_<BZ>, slik at
    resten av kjeden er lik som for netPos [GT-601]. To ulike verdier for samme CNEC og tidsstempel gir feil."""
    per = {}
    for r in rows:
        navn = r.get("cnecName") or ""
        if not navn.startswith("NetPosition_"):
            continue
        felt = "hub_" + navn[len("NetPosition_"):]
        rad = per.setdefault(r["dateTimeUtc"], {"dateTimeUtc": r["dateTimeUtc"]})
        v = r.get("flowFb")
        if felt in rad and rad[felt] != v:
            raise ValueError(f"ulike flowFb for {navn} {r['dateTimeUtc']}")
        rad[felt] = v
    return list(per.values())


def les_fbdsp(rot: Path) -> dict[dt.date, list[tuple[dt.datetime, int, dict]]]:
    ut = {}
    for p in sorted(rot.glob("jao_fbDomainShadowPrice_*.json.gz")):
        dag = dt.date.fromisoformat(p.name.split("_")[-1][:10])
        ut[dag] = jao_doegn(fbdsp_rader(json.loads(gzip.decompress(p.read_bytes()))), dag)
    return ut


def les_np(kilde: str, rot: Optional[Path] = None) -> dict:
    """NP-kilden: «fbdsp» (avvik A2, standard) eller «netpos» (forrige kjøring, for regresjonskontrollen)."""
    if kilde == "fbdsp":
        return les_fbdsp(rot or HOME / "khepri-data/kdf-jao-raw-fbdsp")
    if kilde == "netpos":
        return les_jao(rot or HOME / "khepri-data/kdf-jao-raw", "netPos")
    raise ValueError(kilde)
