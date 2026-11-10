"""Finn et ordrett utdrag i en kilde og oppgi sted.

Bruk: python3 -I tools/finn.py <repo-rot> <K-ID> "<utdrag>"
- PDF-kilder søkes i kilder/txt/<K-ID>.txt (pdftotext -layout); sted = PDF-side (1-basert indeks, ikke trykt sidetall).
- Tekst-/md-/csv-/json-kilder søkes i fila selv; sted = linje.
Mellomrom og linjeskift normaliseres til ett mellomrom; ellers eksakt treff (store/små bokstaver teller).
Exit 0 ved minst ett treff, 1 ellers.
"""
import csv
import re
import sys
from pathlib import Path


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def kildefil(root, kid):
    for r in csv.DictReader(open(root / "kilder/KILDER_MANIFEST.csv", encoding="utf-8")):
        if r["kilde_id"] == kid and r["fil"]:
            return root / "kilder" / r["fil"]
    raise SystemExit(f"{kid}: ikke i manifestet")


def finn(root, kid, utdrag):
    f = kildefil(root, kid)
    q = norm(utdrag)
    treff = []
    if f.suffix == ".pdf":
        sider = (root / "kilder/txt" / f"{kid}.txt").read_text(errors="replace").split("\f")
        for i, s in enumerate(sider, 1):
            if q in norm(s):
                treff.append(f"PDF-side {i}")
    else:
        linjer = f.read_text(errors="replace").splitlines()
        flat = norm(" ".join(linjer))
        if q in flat:
            # finn første linje der utdraget starter (linjeomspennende treff tillates)
            for i in range(len(linjer)):
                if q in norm(" ".join(linjer[i:i + 8])) and q not in norm(" ".join(linjer[i + 1:i + 8])):
                    treff.append(f"linje {i + 1}")
    return treff


if __name__ == "__main__":
    root, kid, utdrag = Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3]
    t = finn(root, kid, utdrag)
    print(f"{kid}: {', '.join(t) if t else 'IKKE FUNNET'}")
    sys.exit(0 if t else 1)
