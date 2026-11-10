"""Steg 4: sammenligner uavhengig verifisering (svar.csv) med GT-verdiene og skriver gt/verifisering2.csv.

Likhetsregel (fastsatt før svarene ble lest):
  Normalisering: '¦'->'|', alle mellomromstyper -> ett mellomrom, små bokstaver, − og – -> -, anførselstegn «»“”" fjernes,
  avsluttende . , ; : fjernes.
  - Tallverdi (GT-verdien inneholder et siffer og har høyst fire ord som ikke er tall/enheter): tallrekka i GT-verdien må
    finnes som sammenhengende delrekke i tallrekka i svaret. Tall leses med mellomrom som tusenskille og komma/punktum som desimal.
  - Tekstverdi: GT-verdien er inneholdt i svaret, eller svaret er inneholdt i GT-verdien og er minst halvparten så langt.
  Ellers AVVIK. AVVIK løses ved ny lesing av kilden (dokumenteres i gt/avvik_losning.md), aldri ved å velge én verdi.
Bruk: python3 -I -B tools/sammenlign_v2.py <rot> <svar.csv> <hvem>
"""
import csv
import datetime as dt
import re
import sys
from pathlib import Path

root, svarfil, hvem = Path(sys.argv[1]).resolve(), Path(sys.argv[2]), sys.argv[3]


def norm(s):
    s = s.replace("¦", "|")
    s = re.sub(r"[   \s]+", " ", s)
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    s = re.sub(r"[«»“”\"]", "", s).strip().lower()
    return re.sub(r"[.,;:]+$", "", s).strip()


def tall(s):
    s = norm(s)
    s = re.sub(r"(?<=\d) (?=\d{3}\b)", "", s)  # tusenskille
    return [float(x.replace(",", ".")) for x in re.findall(r"-?\d+(?:[.,]\d+)?", s)]


def er_tallverdi(v):
    ord_ = [w for w in norm(v).split() if not re.fullmatch(r"[-\d.,/%]+|mw|gw|twh|ca|om|lag|utover|inntil|rader|ms", w)]
    return bool(re.search(r"\d", v)) and len(ord_) <= 4 and not re.search(r"https?://|zenodo|arxiv|[a-z]+_[a-z]", v.lower())


def delrekke(a, b):
    return any(b[i:i + len(a)] == a for i in range(len(b) - len(a) + 1)) if a else False


gt = {r["gt_id"]: r for r in csv.DictReader(open(root / "gt/gt_rader.csv", encoding="utf-8"))}
svar = {r["gt_id"]: r for r in csv.DictReader(open(svarfil, encoding="utf-8"))}
# Tidspunkt per rad = mtime for svarfila i den blindrunden raden ble besvart i (gt/v2_runder.csv), ikke kjøretidspunktet.
runder = {r["runde"]: r["mtime_utc"] for r in csv.DictReader(open(root / "gt/v2_runder.csv", encoding="utf-8"))}


def naar_for(kommentar):
    m = re.match(r"\[runde (\w+)", kommentar or "")
    return f"{runder[m.group(1)]} (mtime svarfil runde {m.group(1)}, gt/v2_runder.csv)" if m and m.group(1) in runder else "ukjent"
ut, teller = [], {"LIK": 0, "AVVIK": 0, "MANGLER": 0}
for gid, r in gt.items():
    s = svar.get(gid)
    if not s:
        teller["MANGLER"] += 1
        continue
    a, b = r["verdi"], s["verdi"]
    if er_tallverdi(a):
        lik = delrekke(tall(a), tall(b))
        regel = "tall"
    else:
        na, nb = norm(a), norm(b)
        lik = bool(nb) and (na in nb or (nb in na and len(nb) >= 0.5 * len(na)))
        regel = "tekst"
    utfall = "LIK" if lik else "AVVIK"
    teller[utfall] += 1
    ut.append(dict(gt_id=gid, hvem=hvem, naar=naar_for(s.get("kommentar", "")), verdi=b, sted=s.get("sted", ""), metode=s.get("metode", ""),
                   kommentar=s.get("kommentar", ""), regel=regel, utfall=utfall))
p = root / "gt/verifisering2.csv"
with open(p, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(ut[0].keys()))
    w.writeheader()
    w.writerows(ut)
print(teller)
for u in ut:
    if u["utfall"] == "AVVIK":
        print(f"AVVIK {u['gt_id']}: GT «{gt[u['gt_id']]['verdi']}» / v2 «{u['verdi']}» ({u['sted']}) {u['kommentar'][:120]}")
