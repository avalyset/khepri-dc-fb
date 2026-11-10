"""Dataruna steg 3: kjører analysen og skriver utfallstabellene til <ut> (resultater/ i repoet, privat, ikke pushet).

Mål [prereg avsnitt 5]: primær H = NP − minNP; sekundær H2 = H + installert − faktisk regulerbar vannkraft, med regelen
for pumpekraft og delvis dekning (K-77). Hendelse L_f > H. Timeregel [GT-318, GT-346].
Utfall [prereg avsnitt 7, T1]: per scenario, mål, sone, f, år (2024, 2025, 2026, alle) og delperiode (før, etter, samlet).
Tabeller:
  utfall.csv               scenario, maal, sone, f, aar, delperiode, mtu_minutter, timer_med_hendelse, timer_gyldige,
                           timer_manglende, andel_timer_med_hendelse, mtu_med_hendelse, mtu_gyldige, mtu_manglende,
                           andel_mtu_med_hendelse (tom for delperiode «samlet» [GT-360, GT-378])
  h_under_null.csv         sone, delperiode, mtu_H_under_null, mtu_med_H   (primærmålets H [GT-357, GT-375])
  manglende_per_maaned.csv maal, sone, maaned, mtu_i_rutenett, mtu_manglende, timer_i_rutenett, timer_manglende
  L_f.csv                  scenario, sone, aar, f, L_MW
Bruk: python3 -I -B tools/kjor_analyse.py <ut> [--np fbdsp|netpos] [--dump <fil.npz utenfor repoet>]   (standard fbdsp, avvik A2)
"""
import collections
import csv
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from khepri_dc_fb import analyse as An  # noqa: E402
from khepri_dc_fb import data as D  # noqa: E402
from khepri_dc_fb import headroom as Hm  # noqa: E402

UT = Path(sys.argv[1])
JAO = Path.home() / "khepri-data/kdf-jao-raw"  # maxNetPos
NP_KILDE = sys.argv[sys.argv.index("--np") + 1] if "--np" in sys.argv else "fbdsp"  # avvik A2 (K-104)
DUMP = Path(sys.argv[sys.argv.index("--dump") + 1]).expanduser() if "--dump" in sys.argv else None
UT.mkdir(parents=True, exist_ok=True)


def fmt(x):
    return "" if x is None else repr(float(x))


np_d, mn_d = D.les_np(NP_KILDE), D.les_jao(JAO, "maxNetPos")
skille_dag = max(d for d in (D.mtu_skifte(np_d), D.mtu_skifte(mn_d)) if d is not None)
T = D.doegnstart(skille_dag)
nett = D.rutenett(T)
start = [t for t, _ in nett]
minutter = np.array([m for _, m in nett], dtype=float)
aar = np.array([t.year for t in start])
foer = np.array([t < T for t in start])
tid = An.time_ider(start)
maaned = [f"{t:%Y-%m}" for t in start]
print("skilledøgn", skille_dag, T.isoformat(), "MTU i rutenettet", len(nett), flush=True)

serier = {}
for z in An.SONER:
    zz = z.replace("_", "")
    NP = D.paa_rutenett(D.jao_kvarterverdier(np_d, "hub_" + zz), nett)
    MN = D.paa_rutenett(D.jao_kvarterverdier(mn_d, "min_" + zz), nett)
    H = [Hm.headroom(a, b) for a, b in zip(NP, MN)]
    sm = D.a75_sone(z)["samlet"]
    H2 = []
    for (t, m), h in zip(nett, H):
        iv = [(15, sm["magasin"].get(q, (None,))[0], sm["pumpe_prod"].get(q, (None,))[0],
               sm["pumpe_forbruk"].get(q, (None,))[0]) for q in D.kvarter(t, m)]
        fak = Hm.faktisk_regulerbar_mtu(iv, m, z in An.PUMPESONER)
        H2.append(Hm.headroom_sekundaer(h, An.installert(z, t.year), fak))
    serier[(z, "primaer")] = np.array([np.nan if x is None else x for x in H], dtype=float)
    serier[(z, "sekundaer")] = np.array([np.nan if x is None else x for x in H2], dtype=float)
    print(z, "MTU med H", int((~np.isnan(serier[(z, 'primaer')])).sum()), "med H2",
          int((~np.isnan(serier[(z, 'sekundaer')])).sum()), flush=True)

if DUMP:  # serien per MTU, bare lokalt (utenfor repoet), til regresjonskontrollen [GT-607]
    np.savez_compressed(DUMP, start=np.array([int(t.timestamp()) for t in start], dtype=np.int64), minutter=minutter,
                        **{f"{z}__{m}": v for (z, m), v in serier.items()})

masker = []
for a in (2024, 2025, 2026, "alle"):
    ma = np.ones(len(nett), bool) if a == "alle" else (aar == a)
    for dp, md in (("foer", foer), ("etter", ~foer), ("samlet", np.ones(len(nett), bool))):
        m = ma & md
        if m.any():
            mins = sorted({int(x) for x in minutter[m]})
            masker.append((str(a), dp, m, "/".join(str(x) for x in mins)))

felt = ["scenario", "maal", "sone", "f", "aar", "delperiode", "mtu_minutter", "timer_med_hendelse", "timer_gyldige",
        "timer_manglende", "andel_timer_med_hendelse", "mtu_med_hendelse", "mtu_gyldige", "mtu_manglende",
        "andel_mtu_med_hendelse"]
with open(UT / "utfall.csv", "w", newline="", encoding="utf-8") as fh, \
        open(UT / "L_f.csv", "w", newline="", encoding="utf-8") as fl:
    w = csv.writer(fh, lineterminator="\n")
    wl = csv.writer(fl, lineterminator="\n")
    w.writerow(felt)
    wl.writerow(["scenario", "sone", "aar", "f", "L_MW"])
    for sc in An.SCENARIER:
        for z in An.SONER:
            for f in An.F_GRID:
                Ly = {y: An.L(sc, z, y, f) for y in (2024, 2025, 2026)}
                for y in (2024, 2025, 2026):
                    wl.writerow([sc, z, y, f"{f:.2f}", fmt(Ly[y])])
                Lv = np.array([Ly[y] for y in aar], dtype=float)
                for maal in ("primaer", "sekundaer"):
                    H = serier[(z, maal)]
                    for a, dp, m, mins in masker:
                        u = An.utfall_vektor(H[m], tid[m], minutter[m], Lv[m])
                        n_h = int(((~np.isnan(H[m])) & (Lv[m] > np.nan_to_num(H[m]))).sum())
                        w.writerow([sc, maal, z, f"{f:.2f}", a, dp, mins, u.timer_med_hendelse, u.timer_gyldige,
                                    u.timer_manglende, fmt(u.andel_timer_med_hendelse), n_h, u.mtu_gyldige,
                                    u.mtu_manglende, "" if dp == "samlet" else fmt(u.andel_mtu_med_hendelse)])
        print("scenario", sc, "ferdig", flush=True)

with open(UT / "h_under_null.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["sone", "delperiode", "mtu_H_under_null", "mtu_med_H"])
    for z in An.SONER:
        H = serier[(z, "primaer")]
        for dp, md in (("foer", foer), ("etter", ~foer), ("samlet", np.ones(len(nett), bool))):
            g = md & ~np.isnan(H)
            w.writerow([z, dp, int((H[g] < 0).sum()), int(g.sum())])

with open(UT / "manglende_per_maaned.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["maal", "sone", "maaned", "mtu_i_rutenett", "mtu_manglende", "timer_i_rutenett", "timer_manglende"])
    for maal in ("primaer", "sekundaer"):
        for z in An.SONER:
            H = serier[(z, maal)]
            c = collections.Counter()
            timer = collections.defaultdict(lambda: [0, False])
            for i, mm in enumerate(maaned):
                c[(mm, "n")] += 1
                c[(mm, "m")] += bool(np.isnan(H[i]))
                tt = timer[(mm, tid[i])]
                tt[0] += minutter[i]
                tt[1] = tt[1] or bool(np.isnan(H[i]))
            for (mm, _), (mins, mangler) in timer.items():
                c[(mm, "t")] += 1
                c[(mm, "tm")] += mangler or mins != 60
            for mm in sorted({k[0] for k in c}):
                w.writerow([maal, z, mm, c[(mm, "n")], c[(mm, "m")], c[(mm, "t")], c[(mm, "tm")]])
print("ferdig", UT)
