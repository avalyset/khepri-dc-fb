"""Leser én produksjonstype for én sone fra A68-avlesningen i K-35 (JSON-strengene med «\\n» som skilletegn).

Bruk: python3 -I -B tools/a68_type.py <rot> <sone> "<produksjonstype>"
Skriver de tre verdiene (2024 2025 2026) slik de står i K-35, skilt med mellomrom.
"""
import json
import sys
from pathlib import Path

root, sone, typ = Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3]
tekst = (root / "kilder/K-35_ENTSOE_TP_avlesning_2026-11-09.txt").read_text(encoding="utf-8")
blokk = tekst.split("=== A68")[1].split("===", 2)[1]
linje = next(l for l in blokk.splitlines() if l.startswith(f"{sone} (sa "))
tab = json.loads(linje[linje.index("{"):])["tab"].split("\n")
i = tab.index(typ)
print(*tab[i + 1:i + 4])
