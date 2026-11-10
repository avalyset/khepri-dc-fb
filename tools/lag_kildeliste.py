"""Bygger manuskript/sources.csv (supplement: kildelista) fra kilder/KILDER_MANIFEST.csv. Ingen filer følger med.

Kolonner: source_id, title, publisher, url, retrieved_utc, sha256 (= kilde_id, tittel, avledet utgiver, url_doi,
hentet_utc, sha256 i manifestet). Utgiveren avledes mekanisk av URL-domenet (UTGIVER nedenfor); kilder uten nettadresse
(lokale kjøringer, øktlogger, egne avlesninger, git-utdrag) får «author's own archive (KHEPRI-DC-FB)». Hjemmekatalogen
i lokale stier (også i øktloggkatalogens navn) erstattes med «~». tools/check_anchors.py (vii) bygger fila på nytt og krever like byte.
Bruk: python3 -I -B tools/lag_kildeliste.py [<utfil>]
"""
import csv
import io
import re
import sys
from pathlib import Path

ROT = Path(__file__).resolve().parents[1]
UTGIVER = [
    (r"(^|\.)statnett\.no$", "Statnett SF"),
    (r"(^|\.)jao\.eu$", "JAO S.A."),
    (r"(^|\.)arxiv\.org$", "arXiv"),
    (r"(^|\.)nve\.no$", "NVE (Norwegian Water Resources and Energy Directorate)"),
    (r"(^|\.)entsoe\.eu$|^eepublicdownloads\.blob\.core\.windows\.net$", "ENTSO-E"),
    (r"(^|\.)nordic-rcc\.net$", "Nordic RCC"),
    (r"(^|\.)acer\.europa\.eu$", "ACER"),
    (r"(^|\.)regjeringen\.no$", "Regjeringen.no (Menon Economics report)"),
    (r"^doi\.org$", "DOI registration agency metadata (doi.org)"),
    (r"(^|\.)osf\.io$", "Center for Open Science (OSF)"),
    (r"(^|\.)nordpoolgroup\.com$", "Nord Pool AS"),
    (r"(^|\.)faktaportalen\.no$", "Faktaportalen"),
]
EGET = "author's own archive (KHEPRI-DC-FB)"


def utgiver(url):
    m = re.match(r"https?://([^/ ]+)", url)
    if not m:
        return EGET
    vert = m.group(1).lower()
    for mønster, navn in UTGIVER:
        if re.search(mønster, vert):
            return navn
    return vert


def bygg():
    rader = list(csv.DictReader(open(ROT / "kilder/KILDER_MANIFEST.csv", encoding="utf-8")))
    ut = io.StringIO()
    w = csv.writer(ut, lineterminator="\n")
    w.writerow(["source_id", "title", "publisher", "url", "retrieved_utc", "sha256"])
    for r in rader:
        url = re.sub(r"/Users/[^/ ]+", "~", r["url_doi"])
        url = re.sub(r"-Users-[^-/ ]+-", "-~-", url)  # øktloggkatalogen under ~/.claude/projects/
        w.writerow([r["kilde_id"], r["tittel"], utgiver(r["url_doi"]), url, r["hentet_utc"], r["sha256"]])
    return ut.getvalue()


if __name__ == "__main__":
    mål = Path(sys.argv[1]) if len(sys.argv) > 1 else ROT / "manuskript/sources.csv"
    mål.write_text(bygg(), encoding="utf-8")
    print("skrev", mål)
