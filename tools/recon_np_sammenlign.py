"""Recon (K-95-bestillingen, punkt 4): kandidater for realisert DA-nettoposisjon sammenlignet MTU for MTU med JAO netPos
(hub_<sone>) i overlappet [2026-05-27T22:00Z, 2026-11-01T00:00Z), per NO-sone. Ingen analyse, ingen bruk i resultater.

Kandidater:
  JAO-FBDSP  JAO Nordic fbDomainShadowPrice, rader med cnecName «NetPosition_<sone>», feltet flowFb (K-25: netPos tas
             herfra). Kilde: ~/khepri-data/kdf-recon-np/jao/np_fbdsp_<døgn>.json.gz
  ENTSOE     ENTSO-E 12.1.E A25/B09 day-ahead (contract A01). Fortegn fra XML: out_Domain = sonen -> +verdi (eksport),
             in_Domain = sonen -> −verdi (import). A03: hold forrige verdi (khepri_dc_fb.data.xml_serier).
             Kilde: ~/khepri-data/kdf-recon-np/entsoe/A25_B09_<sone>_2026-05-27_2026-11-01.xml.gz
Sammenligning per 15-minutters MTU: par = MTU der begge har verdi; avvik = |Δ| > 1e-9 MW (T6); i tillegg antall med
|Δ| > 0,5 MW og > 1 MW, største |Δ| og fortegnstreff (sign lik). Ingen verdier skrives ut.
Utdata (stdout): én linje per kandidat og sone, og per kandidat samlet; pluss MTU-oppløsning per kandidat.
Bruk: python3 -I -B tools/recon_np_sammenlign.py
"""
import collections
import datetime as dt
import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from khepri_dc_fb import data as D  # noqa: E402

UTC = dt.timezone.utc
A = dt.datetime(2026, 5, 27, 22, tzinfo=UTC)
B = dt.datetime(2026, 11, 1, tzinfo=UTC)
R = Path.home() / "khepri-data/kdf-recon-np"
SONER = D.SONER


def ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(UTC)


# JAO netPos (referanse), på MTU-start
np_d = D.les_jao(Path.home() / "khepri-data/kdf-jao-raw", "netPos")
ref = {z: {} for z in SONER}
for d, mtuer in np_d.items():
    for t, m, r in mtuer:
        if A <= t < B:
            for z in SONER:
                v = r.get("hub_" + z.replace("_", ""))
                if v is not None:
                    ref[z][t] = (m, float(v))

# JAO fbDomainShadowPrice, NetPosition_<sone>
fb = {z: {} for z in SONER}
fb_res = collections.Counter()
for p in sorted((R / "jao").glob("np_fbdsp_*.json.gz")):
    rows = json.loads(gzip.decompress(p.read_bytes()))["data"]
    per = collections.defaultdict(list)
    for r in rows:
        per[r["cnecName"]].append((ts(r["dateTimeUtc"]), r["flowFb"]))
    for z in SONER:
        serie = sorted(per.get("NetPosition_" + z.replace("_", ""), []))
        for i, (t, v) in enumerate(serie):
            if A <= t < B and v is not None:
                nxt = serie[i + 1][0] if i + 1 < len(serie) else None
                fb[z][t] = float(v)
                if nxt:
                    fb_res[int((nxt - t).total_seconds() // 60)] += 1

# ENTSO-E A25/B09
en = {z: {} for z in SONER}
en_res = collections.Counter()
for z in SONER:
    p = R / "entsoe" / f"A25_B09_{z}_2026-05-27_2026-11-01.xml.gz"
    eic = D.EIC and next(k for k, v in D.EIC.items() if v == z)
    for s in D.xml_serier(p.read_bytes()):
        sign = 1.0 if s["ut"] == eic else (-1.0 if s["inn"] == eic else None)
        if sign is None:
            raise SystemExit(f"ukjent retning i {p}")
        for t, m, v in s["intervaller"]:
            en_res[m] += 1
            for q in D.kvarter(t, m):
                if A <= q < B:
                    en[z][q] = sign * v

print("referanse JAO netPos: MTU med verdi per sone", " ".join(f"{z}={len(ref[z])}" for z in SONER))
print("oppløsning JAO-FBDSP (minutter: antall)", dict(sorted(fb_res.items())))
print("oppløsning ENTSOE (minutter: antall intervaller)", dict(sorted(en_res.items())))
for navn, kand in (("JAO-FBDSP", fb), ("ENTSOE", en)):
    tot = collections.Counter()
    st_tot = 0.0
    for z in SONER:
        par = [(ref[z][t][1], kand[z][t]) for t in ref[z] if t in kand[z]]
        bare_kand = sum(1 for t in kand[z] if t not in ref[z])
        d = [abs(a - b) for a, b in par]
        c = dict(par=len(par), avvik=sum(x > 1e-9 for x in d), over_0_5=sum(x > 0.5 for x in d),
                 over_1=sum(x > 1 for x in d), fortegn_ulikt=sum((a > 0) != (b > 0) for a, b in par if a and b),
                 bare_kandidat=bare_kand, uten_kandidat=sum(1 for t in ref[z] if t not in kand[z]))
        st = max(d) if d else 0.0
        st_tot = max(st_tot, st)
        tot.update(c)
        print(f"{navn};{z};par {c['par']}; avvik (>1e-9 MW) {c['avvik']}; >0,5 MW {c['over_0_5']}; >1 MW {c['over_1']}; "
              f"største avvik {st:.6f} MW; ulikt fortegn {c['fortegn_ulikt']}; netPos-MTU uten kandidat {c['uten_kandidat']}; "
              f"kandidat-MTU uten netPos {c['bare_kandidat']}")
    print(f"{navn};samlet;par {tot['par']}; avvik (>1e-9 MW) {tot['avvik']}; >0,5 MW {tot['over_0_5']}; >1 MW {tot['over_1']}; "
          f"største avvik {st_tot:.6f} MW; ulikt fortegn {tot['fortegn_ulikt']}; netPos-MTU uten kandidat {tot['uten_kandidat']}; "
          f"kandidat-MTU uten netPos {tot['bare_kandidat']}")

# NO2: ENTSO-E «sum of all commercial exchanges across all bidding zone borders» (K-96) mot JAO, der HVDC-forbindelsene
# går via virtuelle soner NO2_SK, NO2_ND, NO2_NK (fortegn: positivt fra virtuell sone til reell sone, K-25 / GT-328).
# Test: ENTSO-E NO2 mot hub_NO2 ± summen av hver delmengde av de virtuelle sonene (16 varianter).
import itertools  # noqa: E402
NAVN = ["hub_NO2_SK", "hub_NO2_ND", "hub_NO2_NK"]
rader = {}
for d, mtuer in np_d.items():
    for t, m, r in mtuer:
        if A <= t < B and r.get("hub_NO2") is not None and all(r.get(k) is not None for k in NAVN):
            rader[t] = r
for sgn in (1, -1):
    for k in range(4):
        for sub in itertools.combinations(NAVN, k):
            d = [abs(float(r["hub_NO2"]) + sgn * sum(float(r[x]) for x in sub) - en["NO_2"][t])
                 for t, r in rader.items() if t in en["NO_2"]]
            print(f"ENTSOE mot hub_NO2 {'+' if sgn > 0 else '−'} ({' + '.join(sub) or 'ingen'});NO_2;par {len(d)}; "
                  f">0,01 MW {sum(x > 0.01 for x in d)}; største avvik {max(d):.3f} MW")
