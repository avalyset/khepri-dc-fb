"""Hvorfor sekundærmålet mangler timer: per sone og måned, manglende timer og MTU for begge mål (resultater/
manglende_per_maaned.csv), og datahull for pumpekraft per lagret A75-kilde i samme måned (K-110, detaljerte
«kategori»-rader: produksjon/pumpeintervall/datahull i kildens egne intervaller). Bare måneder der sekundærmålet
mangler mer enn primærmålet skrives ut. Bruk: python3 -I -B tools/sekundaer_mangler.py
"""
import csv
from pathlib import Path

ROT = Path(__file__).resolve().parents[1]
M = {(r["maal"], r["sone"], r["maaned"]): r for r in csv.DictReader(open(ROT / "resultater/manglende_per_maaned.csv", encoding="utf-8"))}
K = {}
tekst = (ROT / "kilder/K-110_dataruna_A2_2d_pumpekraft_2026-11-10.txt").read_text(encoding="utf-8").split("--- detaljert ---")[1]
for r in csv.reader(tekst.strip().splitlines()):
    if r and r[0] == "kategori":
        K.setdefault((r[1], r[3]), []).append(f"{r[2]}: produksjon {r[4]}, pumpeintervall {r[5]}, datahull {r[6]}")
print("sone;maaned;timer manglende primær/sekundær;MTU manglende primær/sekundær;A75-kilder med pumpekraftkategorier")
for (maal, sone, mnd), s in sorted(M.items(), key=lambda x: (x[0][1], x[0][2])):
    if maal != "sekundaer":
        continue
    p = M[("primaer", sone, mnd)]
    if int(s["timer_manglende"]) > int(p["timer_manglende"]):
        print(f"{sone};{mnd};{p['timer_manglende']}/{s['timer_manglende']};{p['mtu_manglende']}/{s['mtu_manglende']};"
              + " | ".join(K.get((sone, mnd), ["ingen kategorirader"])))
