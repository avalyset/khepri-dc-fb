"""Klargjør det offentlige repoet lokalt (K-117 punkt 4) fra committet innhold (git archive HEAD), med en fast hviteliste.

Med: kode med henteskript (khepri_dc_fb/, tools/), tests/, resultater/, manuskript/, GROUND_TRUTH.md, gt/,
kilder/KILDER_MANIFEST.csv, prereg-fila, adr/, ots/ (stemplene med de stemplede filene ved siden av, K-119 punkt 1),
AVVIK_FRA_PREREG.md, POSISJONERING.md, PUBLISERINGSPORT.md, README.md, CITATION.cff, .zenodo.json, LICENSE,
LICENSE-DATA, .gitignore.
Ikke med: kilder/ utover manifestet (tredjepartskopier), ankersjekk/, JAO-rådata, JAO-tidsserier og prereg-tarballen.
Bruk: python3 -I -B tools/lag_offentlig.py <tom eller ny mappe>
Skriver fillista (sti, bytes, sha256) til <mappe>/../<mappenavn>_FILLISTE.txt.
"""
import hashlib
import subprocess
import sys
import tarfile
import io
from pathlib import Path

ROT = Path(__file__).resolve().parents[1]
HVIT = ["khepri_dc_fb", "tools", "tests", "resultater", "manuskript", "GROUND_TRUTH.md", "gt",
        "kilder/KILDER_MANIFEST.csv", "KHEPRI-DC-FB_PREREG_v1_2026-11-09.md", "adr", "ots",
        "AVVIK_FRA_PREREG.md", "POSISJONERING.md", "PUBLISERINGSPORT.md", "README.md",
        "CITATION.cff", ".zenodo.json", "LICENSE", "LICENSE-DATA", ".gitignore"]

ut = Path(sys.argv[1]).expanduser()
if ut.exists() and any(ut.iterdir()):
    raise SystemExit(f"{ut} finnes og er ikke tom")
ut.mkdir(parents=True, exist_ok=True)
tar = subprocess.run(["git", "-C", str(ROT), "archive", "--format=tar", "HEAD", "--"] + HVIT, capture_output=True, check=True).stdout
with tarfile.open(fileobj=io.BytesIO(tar)) as t:
    t.extractall(ut, filter="data")
liste = []
for p in sorted(x for x in ut.rglob("*") if x.is_file()):
    b = p.read_bytes()
    liste.append(f"{p.relative_to(ut)}\t{len(b)}\t{hashlib.sha256(b).hexdigest()}")
(ut.parent / f"{ut.name}_FILLISTE.txt").write_text("sti\tbytes\tsha256\n" + "\n".join(liste) + "\n", encoding="utf-8")
print(len(liste), "filer i", ut)
