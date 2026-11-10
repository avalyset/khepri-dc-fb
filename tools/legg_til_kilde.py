"""Legger én lokal kilde til kilder/KILDER_MANIFEST.csv (eller oppdaterer raden hvis K-ID finnes).

Bruk: python3 -I -B tools/legg_til_kilde.py <rot> <K-ID> <tittel> <url/opphav> <fil i kilder/> <kontrollstreng>
Beregner sha256, bytes, sider (pdfinfo for PDF, og pdftotext til kilder/txt/), kontrollstreng-treff. hentet_utc = nå.
"""
import csv
import datetime as dt
import hashlib
import subprocess
import sys
from pathlib import Path

root, kid, tittel, url, fil, kontroll = Path(sys.argv[1]).resolve(), *sys.argv[2:7]
f = root / "kilder" / fil
pages = ""
if f.suffix == ".pdf":
    info = subprocess.run(["pdfinfo", str(f)], capture_output=True, text=True).stdout
    pages = next((l.split()[-1] for l in info.splitlines() if l.startswith("Pages:")), "")
    subprocess.run(["pdftotext", "-layout", str(f), str(root / "kilder/txt" / f"{kid}.txt")], check=True)
    text = (root / "kilder/txt" / f"{kid}.txt").read_text(errors="replace")
else:
    text = f.read_text(errors="replace")
ok = kontroll.lower() in text.lower()
rad = dict(kilde_id=kid, tittel=tittel, url_doi=url, fil=fil,
           hentet_utc=dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
           sha256=hashlib.sha256(f.read_bytes()).hexdigest(), bytes=f.stat().st_size, sider=pages,
           kontrollstreng=kontroll, kontroll_funnet="ja" if ok else "nei",
           status="OK" if ok else "FEILET (kontrollstreng ikke funnet)")
p = root / "kilder/KILDER_MANIFEST.csv"
rows = [r for r in csv.DictReader(open(p, encoding="utf-8")) if r["kilde_id"] != kid] + [rad]
rows.sort(key=lambda d: int(d["kilde_id"].split("-")[1]))
with open(p, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rad.keys()))
    w.writeheader()
    w.writerows(rows)
print(kid, rad["status"], rad["sha256"][:12], rad["bytes"])
