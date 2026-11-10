"""Hendelseslogg: skriver «<UTC-tid> | <hendelse> | <utskrift>» til gt/HENDELSESLOGG.txt og til stdout.

Brukes for hendelser som skal ha sporbart tidspunkt i GT (ny lesing ved AVVIK, OTS, tagging, OSF).
Bruk: python3 -I -B tools/logg.py <rot> "<hendelse>" [-- kommando ...]   (med kommando: utskriften logges også)
"""
import datetime as dt
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
hendelse = sys.argv[2]
ut = ""
if "--" in sys.argv:
    cmd = sys.argv[sys.argv.index("--") + 1:]
    res = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    ut = (res.stdout.strip() or res.stderr.strip()).replace("\n", " ⏎ ")
t = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
linje = f"{t} | {hendelse} | {ut}"
with open(root / "gt/HENDELSESLOGG.txt", "a", encoding="utf-8") as fh:
    fh.write(linje + "\n")
print(linje)
