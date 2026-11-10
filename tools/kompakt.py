"""Kompakte sammendragslinjer (én per datasett/sone/kilde) fra de detaljerte CSV-ene i tools/foer_analyse.py, for GT.

Bruk: python3 -I -B tools/kompakt.py <2a|2c|2d> <detaljert.csv>
  2a  dekning_mnd,<datasett>,<sone>: «mm:verdi/rutenett» for alle måneder; hentet_mnd,<datasett>: «mm:første–siste»
  2c  avvik,<serie>,<kildepar>: måneder, parrede kvarter, avvikende kvarter, største avvik (MW), måneder med avvik
  2d  kategori,<sone>,<kilde>: sum produksjon/pumpeintervall/datahull og «mm:p/pi/h» per måned;
      samlet_mtu,<sone>: sum MTU/manglende/med pumpeintervall og «mm:manglende/pump» for måneder med noe annet enn 0/0;
      dekning_kvarter,<sone>: kvarter med magasinverdi / kvarter, og med pumpeproduksjon (sammenslått), sum og per måned
      med mangler
Alle linjer er «;»-skilte felt: post;nøkkel;verdi.
"""
import collections
import csv
import sys

modus, fil = sys.argv[1], sys.argv[2]
rader = list(csv.reader(open(fil, encoding="utf-8")))
hode, rader = rader[0], rader[1:]


def ut(*f):
    print(";".join(str(x) for x in f))


if modus == "2a":
    d = collections.defaultdict(list)
    h = collections.defaultdict(list)
    for r in rader:
        if r[0] == "dekning":
            d[(r[1], r[2])].append(f"{r[3]}:{r[4]}/{r[5]}")
        elif r[0] == "hentet":
            a, b = r[4].split()
            h[r[1]].append(f"{r[3]}:{a[11:19]}–{b[11:19]}")
    for (ds, z), v in sorted(d.items()):
        ut("dekning_mnd", f"{ds} {z}", " ".join(v))
    for ds, v in sorted(h.items()):
        ut("hentet_mnd", f"{ds} (2026-11-10, UTC)", " ".join(v))
elif modus == "2c":
    a = collections.defaultdict(lambda: [0, 0, 0, 0.0, []])
    for omr, serie, par, mm, n, av, st in rader:
        k = ("A11" if serie == "A11" else serie, par)
        x = a[k]
        x[0] += 1
        x[1] += int(n)
        x[2] += int(av)
        x[3] = max(x[3], float(st))
        if int(av):
            x[4].append(f"{omr} {mm}")
    for (serie, par), x in sorted(a.items()):
        ut("avvik", f"{serie} {par}", f"måneder {x[0]}; parrede kvarter {x[1]}; avvikende kvarter {x[2]}; "
           f"største avvik {x[3]:.3f} MW; måneder med avvik: {' '.join(x[4]) or 'ingen'}")
elif modus == "2d":
    kat = collections.defaultdict(lambda: [0, 0, 0, []])
    sm = collections.defaultdict(lambda: [0, 0, 0, []])
    dk = collections.defaultdict(lambda: [0, 0, 0, []])
    for r in rader:
        p, z, k, mm = r[:4]
        if p == "kategori":
            x = kat[(z, k)]
            v = [int(r[4]), int(r[5]), int(r[6])]
            x[0] += v[0]
            x[1] += v[1]
            x[2] += v[2]
            x[3].append(f"{mm}:{v[0]}/{v[1]}/{v[2]}")
        elif p == "samlet_mtu":
            x = sm[z]
            v = [int(r[4]), int(r[5]), int(r[6] or 0)]
            x[0] += v[0]
            x[1] += v[1]
            x[2] += v[2]
            if v[1] or v[2]:
                x[3].append(f"{mm}:{v[1]}/{v[2]}")
        elif p == "samlet_kvarter":
            x = dk[z]
            q, qm = int(r[4]), int(r[5])
            qp = int(r[6]) if r[6] else None
            x[0] += q
            x[1] += qm
            x[2] += qp or 0
            if qm < q or (qp is not None and qp < q):
                x[3].append(f"{mm}:{qm}/{qp if qp is not None else '-'}/{q}")
    for (z, k), x in sorted(kat.items()):
        ut("kategori", f"{z} {k}", f"sum {x[0]}/{x[1]}/{x[2]}; " + " ".join(x[3]))
    for z, x in sorted(sm.items()):
        ut("samlet_mtu", z, f"MTU {x[0]}; manglende for sekundærmålet {x[1]}; med pumpeintervall {x[2]}; "
           + (" ".join(x[3]) or "ingen måneder med manglende eller pumpeintervall"))
    for z, x in sorted(dk.items()):
        ut("dekning_kvarter", z, f"kvarter {x[0]}; med magasinverdi {x[1]}; med pumpeproduksjon {x[2] if z in ('NO_2', 'NO_3', 'NO_5') else '-'}; "
           "måneder med mangler (magasin/pumpe/kvarter): " + (" ".join(x[3]) or "ingen"))
