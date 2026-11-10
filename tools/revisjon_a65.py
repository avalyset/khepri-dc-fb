"""3c punkt 3c + 4: periode for de 16 A65 NO1-vinduene fra den stoppede hentingen (K), overlapp med v1-rådata (X),
og revisjonskontroll MTU for MTU i overlappen. Ingen henting.

K: ~/khepri-data/kdf-meta-2026-11-09/entsoe_raw/A65/NO_1/*.xml.gz, bare de 16 vinduene som sto i oppsummeringen før omstart
   (vinduene 2024-10-30 og 2024-11 … 2026-01), hentet 2026-11-09.
X: /Volumes/Vault/khepri-dc/raw/A65/A65_NO_1_*.xml (v1-henting, 2026-11-02).
MTU-er ekspanderes per serie: A01 = oppgitte posisjoner, A03 = hold forrige verdi til neste posisjon / periodens slutt.
Nøkkel = (MTU-start UTC, oppløsning). Avvik = |K − X| > 1e-9 MW.
Belegg (presisering nr. 2, K-41): antall parrede MTU der begge sider har verdi, MTU uten par på hver side (i K-perioden),
filnavn og sha256 for begge filsett (kontrollstreng), og positiv kontroll: med --positiv-kontroll legges +1 MW inn i én
kjent MTU i en kopi av ett K-vindu (2025-06, PT15M-punkt der neste posisjon er neste MTU), og skriptet skal melde nøyaktig
én avvikende MTU med avvik 1.000 MW på det tidspunktet.
Bruk: python3 -I -B tools/revisjon_a65.py [--positiv-kontroll]
"""
import hashlib
import re
import sys
import datetime as dt
import gzip
import xml.etree.ElementTree as ET
from pathlib import Path

K = Path.home() / "khepri-data/kdf-meta-2026-11-09/entsoe_raw/A65/NO_1"
X = Path("/Volumes/Vault/khepri-dc/raw/A65")
VINDUER = ["2024-10-30"] + [f"{y}-{m:02d}" for y, m in [(2024, 11), (2024, 12)] + [(2025, i) for i in range(1, 13)] + [(2026, 1)]]
RES = {"PT15M": 15, "PT60M": 60}


def verdi(q):
    try:
        v = float(q)
    except (TypeError, ValueError):
        return None
    return None if v != v else v  # NaN -> None


def mtu(body):
    ut = {}
    root = ET.fromstring(body)
    for ts in root.iterfind(".//{*}TimeSeries"):
        kurve = (ts.findtext("{*}curveType") or "A01").strip()
        for per in ts.iterfind("{*}Period"):
            ps = dt.datetime.strptime(per.findtext("{*}timeInterval/{*}start"), "%Y-%m-%dT%H:%MZ")
            pe = dt.datetime.strptime(per.findtext("{*}timeInterval/{*}end"), "%Y-%m-%dT%H:%MZ")
            rs = per.findtext("{*}resolution")
            r = RES[rs]
            n = int((pe - ps).total_seconds() // 60 // r)
            pts = sorted((int(p.findtext("{*}position")), verdi(p.findtext("{*}quantity"))) for p in per.iterfind("{*}Point"))
            for i, (pos, q) in enumerate(pts):
                slutt = (pts[i + 1][0] if i + 1 < len(pts) else n + 1) if kurve == "A03" else pos + 1
                for k in range(pos, slutt):
                    ut[(ps + dt.timedelta(minutes=(k - 1) * r), rs)] = q
    return ut


POSITIV = "--positiv-kontroll" in sys.argv
kfiler = [K / f"{v}.xml.gz" for v in VINDUER]
xfiler = sorted(X.glob("A65_NO_1_*.xml"))
k, kontroll_t = {}, None
for f in kfiler:
    body = gzip.decompress(f.read_bytes())
    if POSITIV and f.name == "2025-06.xml.gz":
        # +1 MW i ett PT15M-punkt der neste posisjon er neste MTU (påvirker nøyaktig én MTU også ved A03)
        t = body.decode()
        per = re.search(r"<resolution>PT15M</resolution>(.*?)</Period>", t, re.S)
        pts = list(re.finditer(r"<position>(\d+)</position>\s*<quantity>([^<]+)</quantity>", per.group(1)))
        for a, b in zip(pts, pts[1:]):
            if int(b.group(1)) == int(a.group(1)) + 1 and int(a.group(1)) >= 100:
                pos, q = int(a.group(1)), float(a.group(2))
                break
        start = dt.datetime.strptime(re.search(r"<start>([^<]+)</start>", t[:per.start()][::-1][::-1].split("<Period>")[-1]).group(1), "%Y-%m-%dT%H:%MZ")
        kontroll_t = start + dt.timedelta(minutes=15 * (pos - 1))
        gammel = f"<position>{pos}</position>"
        i = per.start(1) + per.group(1).index(gammel)
        j = t.index("</quantity>", i)
        qstart = t.index("<quantity>", i) + len("<quantity>")
        t = t[:qstart] + repr(q + 1.0) + t[j:]
        body = t.encode()
        print(f"positiv_kontroll_innlagt {kontroll_t:%Y-%m-%dT%H:%MZ} PT15M posisjon {pos}: {q} -> {q + 1.0} (+1 MW)")
    k.update(mtu(body))
x = {}
for f in xfiler:
    x.update(mtu(f.read_bytes()))
print("kontrollstreng_K_filer " + " ".join(f"{f.name}:{hashlib.sha256(f.read_bytes()).hexdigest()}" for f in kfiler))
print("kontrollstreng_X_filer " + " ".join(f"{f.name}:{hashlib.sha256(f.read_bytes()).hexdigest()}" for f in xfiler))
kt = sorted(t for t, _ in k)
i_k_per = {t for t in x if kt[0] <= t[0] <= kt[-1]}
felles = sorted(set(k) & i_k_per)
parret = [t for t in felles if k[t] is not None and x[t] is not None]
avvik = [(t, k[t], x[t]) for t in parret if abs(k[t] - x[t]) > 1e-9]
storste = max(avvik, key=lambda a: abs(a[1] - a[2]), default=None)
print(f"K_vinduer {len(VINDUER)}")
print(f"K_periode {kt[0]:%Y-%m-%dT%H:%MZ} til {kt[-1]:%Y-%m-%dT%H:%MZ} (siste MTU-start)")
print(f"K_mtu {len(k)}")
print(f"X_mtu_i_K_perioden {len(i_k_per)}")
print(f"overlapp_mtu {len(felles)}")
fs = sorted(t for t, _ in felles)
print(f"overlapp_periode {fs[0]:%Y-%m-%dT%H:%MZ} til {fs[-1]:%Y-%m-%dT%H:%MZ}")
print(f"parrede_mtu_begge_med_verdi {len(parret)}")
print(f"mtu_uten_par_bare_K {len(set(k) - i_k_per)}")
print(f"mtu_uten_par_bare_X {len(i_k_per - set(k))}")
print(f"mtu_i_overlapp_med_manglende_verdi_K_eller_X {len(felles) - len(parret)}")
print(f"avvikende_mtu {len(avvik)}")
print(f"storste_avvik_MW {abs(storste[1] - storste[2]) if storste else 0.0:.3f}")
if storste:
    print(f"storste_avvik_ved {storste[0][0]:%Y-%m-%dT%H:%MZ} {storste[0][1]} K={storste[1]} X={storste[2]}")
if POSITIV:
    ok = len(avvik) == 1 and avvik[0][0][0] == kontroll_t and abs(abs(avvik[0][1] - avvik[0][2]) - 1.0) < 1e-9
    print(f"positiv_kontroll_resultat {'BESTÅTT' if ok else 'FEILET'}")
