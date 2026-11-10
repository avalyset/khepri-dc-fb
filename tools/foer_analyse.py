"""Dataruna steg 2 (før analysen): tall som føres i GT og blindverifiseres før analysen kjøres (K-84 punkt 2).

Bruk: python3 -I -B tools/foer_analyse.py <modus> [--np fbdsp|netpos]   (standard fbdsp, avvik A2)
  jao        2a: JAO-dekning per datasett, sone og måned (MTU med verdi / MTU i rutenettet), hentetidspunkt per måned
             (første og siste hentet_utc i manifestet), fravær, og MTU-skiftet per datasett og samlet [GT-209, GT-355]
  fortegn    2b: Pearson-korrelasjon JAO netPos (hub_<sone>) mot A11-nettoeksport per MTU på JAO-oppløsning,
             alle NO-soner samlet og per sone [GT-356, GT-366, GT-374]; T3 i AVVIK_FRA_PREREG.md
  overlapp   2c: avvik mellom lagrede ENTSO-E-kilder i overlappet per sone/retning, serie og måned [GT-358, GT-376]; T6
  pumpe      2d: dekning for Hydro Water Reservoir og Hydro Pumped Storage per sone, kilde og måned, og kategoriene
             produksjon / pumpeintervall / datahull per sone, kilde og måned (K-77, GT-407, GT-412), pluss for den
             sammenslåtte serien MTU manglende for sekundærmålet og MTU med minst ett pumpeintervall per sone og måned
Utdata er bare tellinger, datoer og korrelasjonskoeffisienter (ingen JAO-verdier eller avledede serier), som CSV på stdout.
"""
import collections
import csv
import datetime as dt
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from khepri_dc_fb import data as D  # noqa: E402
from khepri_dc_fb import headroom as Hm  # noqa: E402

JAO = Path.home() / "khepri-data/kdf-jao-raw"  # maxNetPos (og netPos i forrige kjøring)
# NP-kilde: --np fbdsp (standard etter avvik A2, K-104) eller --np netpos (forrige kjøring)
NP_KILDE = sys.argv[sys.argv.index("--np") + 1] if "--np" in sys.argv else "fbdsp"
NP_NAVN = {"fbdsp": "fbDomainShadowPrice", "netpos": "netPos"}[NP_KILDE]
NP_MANIFEST = (Path.home() / "khepri-data/kdf-jao-raw-fbdsp/manifest.csv") if NP_KILDE == "fbdsp" else JAO / "manifest.csv"
W = csv.writer(sys.stdout, lineterminator="\n")


def mnd(t):
    return f"{t:%Y-%m}"


def skille():
    np_d, mn_d = D.les_np(NP_KILDE), D.les_jao(JAO, "maxNetPos")
    s_np, s_mn = D.mtu_skifte(np_d), D.mtu_skifte(mn_d)
    s = max(x for x in (s_np, s_mn) if x is not None)
    return np_d, mn_d, s_np, s_mn, s, D.doegnstart(s)


def jao():
    np_d, mn_d, s_np, s_mn, s, T = skille()
    W.writerow(["post", "datasett", "sone", "maaned", "verdi1", "verdi2"])
    W.writerow(["mtu_skifte", NP_NAVN, "", "", s_np, D.doegnstart(s_np).isoformat() if s_np else ""])
    W.writerow(["mtu_skifte", "maxNetPos", "", "", s_mn, D.doegnstart(s_mn).isoformat() if s_mn else ""])
    W.writerow(["mtu_skifte", "samlet (seneste)", "", "", s, T.isoformat()])
    nett = D.rutenett(T)
    for ds, doegn, pre in ((NP_NAVN, np_d, "hub_"), ("maxNetPos", mn_d, "min_")):
        for z in D.SONER:
            v = D.paa_rutenett(D.jao_kvarterverdier(doegn, pre + z.replace("_", "")), nett)
            c = collections.Counter()
            for (t, m), x in zip(nett, v):
                c[(mnd(t), "alle")] += 1
                c[(mnd(t), "verdi")] += x is not None
            for mm in sorted({k[0] for k in c}):
                W.writerow(["dekning", ds, z, mm, c[(mm, "verdi")], c[(mm, "alle")]])
    man = list(csv.DictReader(open(JAO / "manifest.csv", encoding="utf-8")))
    if NP_KILDE == "fbdsp":
        man += list(csv.DictReader(open(NP_MANIFEST, encoding="utf-8")))
    for ds in (NP_NAVN, "maxNetPos"):
        rader = [r for r in man if r["noekkel"] == ds]
        per = collections.defaultdict(list)
        for r in rader:
            per[r["vindu_start"][:7]].append(r)
        for mm in sorted(per):
            tider = sorted(r["hentet_utc"] for r in per[mm])
            st = collections.Counter(r["status"] + (":" + r["aarsak"] if r["aarsak"] else "") for r in per[mm])
            W.writerow(["hentet", ds, "", mm, f"{tider[0]} {tider[-1]}", " ".join(f"{k}={v}" for k, v in sorted(st.items()))])
        st = collections.Counter(r["status"] for r in rader)
        ok = sorted(r["vindu_start"] for r in rader if r["status"] == "OK")
        W.writerow(["status", ds, "", "", " ".join(f"{k}={v}" for k, v in sorted(st.items())),
                    f"første OK {ok[0] if ok else ''}, siste OK {ok[-1] if ok else ''}"])
        W.writerow(["bytes", ds, "", "", sum(int(r["bytes"] or 0) for r in rader), len(rader)])


def a11_netto(z, nett):
    mine = [r for r in D.RETNINGER if z in r.split("__")]
    flyt = {r: D.a11_retning(r)["samlet"] for r in mine}
    alle = set.intersection(*(set(f) for f in flyt.values()))
    q = {}
    for t in alle:
        s = 0.0
        for r, f in flyt.items():
            s += f[t][0] if r.split("__")[0] == z else -f[t][0]
        q[t] = (15, s)
    return D.paa_rutenett(q, nett), len(mine)


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    return sxy / math.sqrt(sxx * syy)


def fortegn():
    np_d, mn_d, s_np, s_mn, s, T = skille()
    nett = D.rutenett(T)
    W.writerow(["omfang", "retninger", "par", "pearson_r"])
    X, Y = [], []
    for z in D.SONER:
        npv = D.paa_rutenett(D.jao_kvarterverdier(np_d, "hub_" + z.replace("_", "")), nett)
        a11, nr = a11_netto(z, nett)
        par = [(a, b) for a, b in zip(npv, a11) if a is not None and b is not None]
        xs, ys = [p[0] for p in par], [p[1] for p in par]
        X += xs
        Y += ys
        W.writerow([z, nr, len(par), f"{pearson(xs, ys):.6f}" if len(par) > 2 else ""])
    W.writerow(["NO1-NO5 samlet", 30, len(X), f"{pearson(X, Y):.6f}"])


def avvik_rader(navn, omr, per):
    kilder = [k for k in D.PRIORITET if k in per]
    for i, a in enumerate(kilder):
        for b in kilder[i + 1:]:
            c = collections.defaultdict(lambda: [0, 0, 0.0])
            for t, va in per[a].items():
                vb = per[b].get(t)
                if va is None or vb is None:
                    continue
                d = abs(va - vb)
                e = c[mnd(t)]
                e[0] += 1
                if d > 1e-9:
                    e[1] += 1
                    e[2] = max(e[2], d)
            for mm in sorted(c):
                W.writerow([omr, navn, f"{a}-{b}", mm, c[mm][0], c[mm][1], f"{c[mm][2]:.3f}"])


def overlapp():
    W.writerow(["omraade", "serie", "kildepar", "maaned", "parrede_kvarter", "avvikende_kvarter", "stoerste_avvik_MW"])
    for z in D.SONER:
        a = D.a75_sone(z)["per_kilde"]
        for navn in ("magasin", "pumpe_prod", "pumpe_forbruk"):
            avvik_rader(navn, z, {k: v[navn] for k, v in a.items()})
    for r in D.RETNINGER:
        avvik_rader("A11", r, D.a11_retning(r)["per_kilde"])


def pumpe():
    np_d, mn_d, s_np, s_mn, s, T = skille()
    nett = D.rutenett(T)
    W.writerow(["post", "sone", "kilde", "maaned", "a", "b", "c", "d"])
    for z in D.SONER:
        a = D.a75_sone(z)
        for k in D.PRIORITET:
            if k not in a["per_kilde"]:
                continue
            v = a["per_kilde"][k]
            c = collections.Counter()
            for t, m in sorted(v["univers"]):
                mm = mnd(t)
                c[(mm, "int")] += 1
                c[(mm, "mag")] += v["magasin"].get(t) is not None
                if z in D.PUMPESONER:
                    kat = Hm.pumpekategori(v["pumpe_prod"].get(t), v["pumpe_forbruk"].get(t))
                    c[(mm, kat)] += 1
            for mm in sorted({x[0] for x in c}):
                # dekning: intervaller i universet, med magasinverdi; kategorier (bare NO2, NO3, NO5)
                W.writerow(["kilde_intervaller", z, k, mm, c[(mm, "int")], c[(mm, "mag")], "", ""])
                if z in D.PUMPESONER:
                    W.writerow(["kategori", z, k, mm, c[(mm, Hm.PRODUKSJON)], c[(mm, Hm.PUMPEINTERVALL)],
                                c[(mm, Hm.DATAHULL)], ""])
            W.writerow(["rare_lengder", z, k, "", v["rare_lengder"], v["filer"], "", ""])
        sm = a["samlet"]
        c = collections.Counter()
        for t, m in nett:
            iv = []
            pump = False
            for q in D.kvarter(t, m):
                mag = sm["magasin"].get(q, (None,))[0]
                pp = sm["pumpe_prod"].get(q, (None,))[0]
                pf = sm["pumpe_forbruk"].get(q, (None,))[0]
                iv.append((15, mag, pp, pf))
                if z in D.PUMPESONER and Hm.pumpekategori(pp, pf) == Hm.PUMPEINTERVALL:
                    pump = True
            f = Hm.faktisk_regulerbar_mtu(iv, m, z in D.PUMPESONER)
            mm = mnd(t)
            c[(mm, "mtu")] += 1
            c[(mm, "mangler")] += f is None
            c[(mm, "pump")] += pump
            for q in D.kvarter(t, m):
                c[(mm, "q")] += 1
                c[(mm, "q_mag")] += q in sm["magasin"]
                c[(mm, "q_pumpe")] += q in sm["pumpe_prod"]
        for mm in sorted({x[0] for x in c}):
            W.writerow(["samlet_mtu", z, "samlet", mm, c[(mm, "mtu")], c[(mm, "mangler")],
                        c[(mm, "pump")] if z in D.PUMPESONER else "", ""])
            W.writerow(["samlet_kvarter", z, "samlet", mm, c[(mm, "q")], c[(mm, "q_mag")],
                        c[(mm, "q_pumpe")] if z in D.PUMPESONER else "", ""])


{"jao": jao, "fortegn": fortegn, "overlapp": overlapp, "pumpe": pumpe}[sys.argv[1]]()
