"""Steg 4: celle-for-celle-sammenligning av to sett utfallstabeller (hovedøkta mot uavhengig omregning).

Regel (fastsatt før den uavhengige tabellen ble lest): rader pares på nøkkelkolonnene; heltall må være like; desimaltall må
være like innen 1e-9 (absolutt); tomme celler må være tomme på begge sider; rader som bare finnes på én side er ulikheter.
Bruk: python3 -I -B tools/sammenlign_utfall.py <katalog A> <katalog B>
Skriver per tabell: rader A, rader B, parrede rader, celler sammenlignet, ulike celler, rader bare i A / bare i B, og de
første ulikhetene (nøkkel, kolonne, A, B).
"""
import csv
import sys
from pathlib import Path

A, B = Path(sys.argv[1]), Path(sys.argv[2])
NOEKLER = {
    "utfall.csv": ["scenario", "maal", "sone", "f", "aar", "delperiode"],
    "h_under_null.csv": ["sone", "delperiode"],
    "manglende_per_maaned.csv": ["maal", "sone", "maaned"],
    "L_f.csv": ["scenario", "sone", "aar", "f"],
}


def norm_noekkel(k, v):
    v = v.strip()
    if k == "f":
        return f"{float(v):.2f}"
    return v


def lik(a, b):
    a, b = a.strip(), b.strip()
    if a == "" or b == "":
        return a == b
    try:
        fa, fb = float(a), float(b)
    except ValueError:
        return a == b
    return abs(fa - fb) <= 1e-9


feil_i_alt = 0
for navn, nk in NOEKLER.items():
    ra = list(csv.DictReader(open(A / navn, encoding="utf-8")))
    rb = list(csv.DictReader(open(B / navn, encoding="utf-8")))
    da = {tuple(norm_noekkel(k, r[k]) for k in nk): r for r in ra}
    db = {tuple(norm_noekkel(k, r[k]) for k in nk): r for r in rb}
    kol = [c for c in ra[0] if c not in nk]
    mangler_kol = [c for c in kol if c not in rb[0]]
    felles = sorted(set(da) & set(db))
    celler, ulike, eks = 0, 0, []
    for key in felles:
        for c in kol:
            if c in mangler_kol:
                continue
            celler += 1
            if not lik(da[key][c], db[key][c]):
                ulike += 1
                if len(eks) < 15:
                    eks.append((key, c, da[key][c], db[key][c]))
    bare_a, bare_b = len(set(da) - set(db)), len(set(db) - set(da))
    feil_i_alt += ulike + bare_a + bare_b + len(mangler_kol)
    print(f"{navn}: rader A {len(ra)}, rader B {len(rb)}, parret {len(felles)}, celler {celler}, ulike {ulike}, "
          f"bare A {bare_a}, bare B {bare_b}, kolonner som mangler i B {mangler_kol or 'ingen'}")
    for e in eks:
        print("   ulik", e)
    for key in sorted(set(da) - set(db))[:5]:
        print("   bare A", key)
    for key in sorted(set(db) - set(da))[:5]:
        print("   bare B", key)
print("ULIKHETER I ALT", feil_i_alt)
