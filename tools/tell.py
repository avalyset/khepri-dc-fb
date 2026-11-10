"""Fraværs-/forekomstbelegg for GT-rader av type beregnet.

  tell.py <rot> linjer <K-ID> <regex>            antall linjer med treff (re.I) i kildens tekst
  tell.py <rot> side <K-ID> <side> <regex>       antall treff på én PDF-side (1-basert)
  tell.py <rot> samtreff <regexA> <regexB>       antall sider/tekstfiler i HELE arkivet der begge forekommer
  tell.py <rot> samtreff-liste <regexA> <regexB> som over, men lister K-ID:side
Tekst: PDF -> kilder/txt/<K-ID>.txt; ellers fila selv. Skriver bare tallet (eller lista). Exit 0.
"""
import csv
import re
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
mode = sys.argv[2]
man = [r for r in csv.DictReader(open(root / "kilder/KILDER_MANIFEST.csv", encoding="utf-8"))
       if r["fil"] and r["status"] == "OK" and (root / "kilder" / r["fil"]).exists()]


def tekst(r):
    f = root / "kilder" / r["fil"]
    if f.suffix == ".pdf":
        return (root / "kilder/txt" / f"{r['kilde_id']}.txt").read_text(errors="replace").split("\f")
    return [f.read_text(errors="replace")]


def rad(kid):
    return next(r for r in man if r["kilde_id"] == kid)


if mode == "linjer":
    rx = re.compile(sys.argv[4], re.I)
    print(sum(1 for s in tekst(rad(sys.argv[3])) for l in s.splitlines() if rx.search(l)))
elif mode == "side":
    rx = re.compile(sys.argv[5], re.I)
    print(len(rx.findall(tekst(rad(sys.argv[3]))[int(sys.argv[4]) - 1])))
elif mode in ("samtreff", "samtreff-liste"):
    a, b = re.compile(sys.argv[3], re.I), re.compile(sys.argv[4], re.I)
    # valgfritt: --til K-nn begrenser til K-01 … K-nn (kildearkivet slik det var på et gitt steg)
    tak = int(sys.argv[sys.argv.index("--til") + 1].split("-")[1]) if "--til" in sys.argv else 999
    hits = []
    for r in man:
        if r["kilde_id"] == "K-34" or int(r["kilde_id"].split("-")[1]) > tak:  # K-34 er bestilling, ikke faktakilde
            continue
        for i, s in enumerate(tekst(r), 1):
            if a.search(s) and b.search(s):
                hits.append(f"{r['kilde_id']}:{i}")
    print(len(hits) if mode == "samtreff" else " ".join(hits) or "ingen")
