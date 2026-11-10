"""Bygger GROUND_TRUTH.md fra gt/gt_rader.csv og kjører verifisering 1.

Verifisering 1 (hovedøkta, mekanisk):
  type=sitat:    utdraget finnes ordrett i kilden (tools/finn.py) OG verdien står ordrett i utdraget.
  type=beregnet: kommandoen kjøres i repo-roten, og utskriften (strip) er lik verdien.
Verifisering 2 kommer fra gt/verifisering2.csv (steg 4: uavhengig underagent som ikke så verdiene).
  Lik verdi (normalisert) -> VERIFISERT×2; ulik -> AVVIK (begge verdier vises); mangler -> beholdes ×1.
'¦' i utdrag/verdi står for '|' i kilden (for å holde markdown-tabellen gyldig).
Bruk: python3 -I tools/gt_render.py <repo-rot>
"""
import csv
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT / "tools"))
from finn import finn  # noqa: E402


def norm(s):
    s = s.replace("¦", "|").replace(" ", " ").replace(" ", " ").replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip()


def norm_v(s):
    return norm(s).replace("−", "-").replace("–", "-").lower()


def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


manifest = {r["kilde_id"]: r for r in csv.DictReader(open(ROOT / "kilder/KILDER_MANIFEST.csv", encoding="utf-8"))}
rader = list(csv.DictReader(open(ROOT / "gt/gt_rader.csv", encoding="utf-8")))
v2 = {}
p2 = ROOT / "gt/verifisering2.csv"
if p2.exists():
    v2 = {r["gt_id"]: r for r in csv.DictReader(open(p2, encoding="utf-8"))}

losning = {}
pl = ROOT / "gt/avvik_losning.csv"
if pl.exists():
    losning = {r["gt_id"]: r for r in csv.DictReader(open(pl, encoding="utf-8"))}
ut, teller = [], {}
t1 = now()
for r in rader:
    kid = r["kilde"]
    hentet = manifest.get(kid, {}).get("hentet_utc", "MANGLER I MANIFEST")
    if r["type"] == "forslag":  # metodevalg foreslått av CC (Claude Code); ikke verifiserbart, venter på Eiriks beslutning
        status = "FORSLAG (venter på Eiriks beslutning)"
        teller["FORSLAG"] = teller.get("FORSLAG", 0) + 1
        ut.append([r["gt_id"], r["påstand"], r["verdi"], r["enhet"], f"{kid} (forslag)", r["utdrag"], "—",
                   "ikke aktuelt (forslag)", "ikke aktuelt (forslag)", status])
        continue
    if r["type"] == "sitat":
        sted = finn(ROOT, kid, r["utdrag"].replace("¦", "|"))
        i_utdrag = norm_v(r["verdi"]) in norm_v(r["utdrag"])
        ok = bool(sted) and i_utdrag
        v1 = f"hovedøkt (Opus 5.5) {t1}: tools/finn.py → {', '.join(sted) or 'IKKE FUNNET'}; verdi i utdrag: {'ja' if i_utdrag else 'NEI'}"
        sted_txt = ", ".join(sted) if sted else "IKKE FUNNET"
    else:
        res = subprocess.run(r["kommando"], shell=True, cwd=ROOT, capture_output=True, text=True)
        out = res.stdout.strip()
        ok = res.returncode == 0 and norm_v(out) == norm_v(r["verdi"])
        v1 = f"hovedøkt (Opus 5.5) {t1}: `{r['kommando'].replace('|', '¦')}` → {(out or res.stderr.strip()[:80]).replace('|', '¦')}"  # '|' i kommandoen vises som '¦' (markdown-tabell)
        sted_txt = "beregnet (se verifisering 1)"
    status = "VERIFISERT×1" if ok else "UVERIFISERT"
    ver2 = ""
    if ok and r["gt_id"] in v2:
        a = v2[r["gt_id"]]
        ver2 = f"{a['hvem']} {a['naar']}: oppga «{a['verdi'].replace('|', '¦')}» ({a['sted'].replace('|', '¦')})"
        if a.get("utfall") == "LIK":
            status = "VERIFISERT×2"
        elif a.get("utfall") == "AVVIK" and losning.get(r["gt_id"], {}).get("utfall") == "LIK":
            lo = losning[r["gt_id"]]
            status = "VERIFISERT×2"
            ver2 += f"; AVVIK løst ved ny lesing {lo['ny_lesing_utc']}: {lo['begrunnelse']}"
        elif a.get("utfall") == "AVVIK":
            status = f"AVVIK (GT: {r['verdi']} / v2: {a['verdi'].replace('|', '¦')})"
    teller[status.split(" ")[0]] = teller.get(status.split(" ")[0], 0) + 1
    ut.append([r["gt_id"], r["påstand"], r["verdi"], r["enhet"], f"{kid}, {sted_txt}", r["utdrag"], hentet, v1, ver2, status])

hode = """# GROUND_TRUTH — KHEPRI-DC-FB (KHEPRI-DC v2, flow-based)

**Regel:** Ingen verdi, sitat, dato, ID eller påstand om en kilde brukes i noen fil (ADR, prereg, README, rapport) uten at raden her har status **VERIFISERT×2**. Finnes en verdi ikke i en kilde, står den som «ikke funnet» med kontrollstreng, aldri som anslag.

**Slik verifiseres fila:**
1. *Verifisering 1* (hovedøkta, mekanisk, `tools/gt_render.py`): for type sitat finner `tools/finn.py` utdraget ordrett i kilden og oppgir stedet (PDF-side = 1-basert indeks i PDF-en, ikke trykt sidetall; linje for tekstfiler), og verdien må stå ordrett i utdraget. For type beregnet kjøres kommandoen og utskriften må være lik verdien.
2. *Verifisering 2* (steg 4): en egen Opus 5.5-underagent får bare GT-ID, påstand, kilde-ID og sted, ikke verdien, leser kilden og oppgir verdien selv. Lik verdi gir VERIFISERT×2. Ulik verdi gir AVVIK med begge verdier, som løses ved ny lesing av kilden, aldri ved å velge én.
3. `tools/check_anchors.py` (steg 5) kontrollerer sha256 mot `kilder/KILDER_MANIFEST.csv`, at kilde-ID-ene finnes, at DOI-er og arXiv-ID-er løses med riktig tittel, og at hvert tall og sitat i ADR- og prereg-filene har en GT-ID med lik verdi.

Rader med status **FORSLAG** er metodevalg foreslått av CC (Claude Code) som venter på Eiriks beslutning. De er ikke verifiserbare fakta og kan ikke brukes i låste dokumenter før Eiriks svar er arkivert som K-kilde og raden er erstattet av en beslutningsrad.

Kilderadene redigeres i `gt/gt_rader.csv`; denne fila genereres. `¦` står for `|` i kilden. Alle tidspunkter er UTC.

**Tidsspor (hvor hvert tidspunkt kommer fra):**
- *Hentet (UTC)*: `hentet_utc` i `kilder/KILDER_MANIFEST.csv`, skrevet av `tools/hent_kilder.py` (K-01–K-32) eller `tools/legg_til_kilde.py` (senere kilder) ved registrering; manifestet er committet. For lokale kilder er det registreringstidspunktet, ikke opprinnelig hentetidspunkt (det står i radene for K-47–K-49 og GT-239–GT-241).
- *Verifisering 1*: kjøretidspunktet for `tools/gt_render.py`, som kjører kontrollen på nytt ved hver bygging.
- *Verifisering 2*: mtime for svarfila fra den blindrunden raden ble besvart i (`gt/v2_runder.csv`, filene `gt/v2_svar_runde*.csv` er bevart med `cp -p`).
- *AVVIK løst ved ny lesing*: `ny_lesing_utc` i `gt/avvik_losning.csv`, enten fra `gt/HENDELSESLOGG.txt` (`tools/logg.py`) eller som tidsintervall avgrenset av verktøyutskrifter, med kilde oppgitt.
- *«Arkivert (UTC)» i K-34, K-37, K-40 og K-41*: skrevet av hovedøkta ved arkivering (K-34: filens mtime fra `stat`, rettet fra et feilaktig tidspunkt; de andre: `date -u` i samme kommando); se også manifestets `hentet_utc`.
- Tidspunkter i verdikolonnen kommer fra kildene selv (dokumenter, rådata, manifester) og har kildens presisjon.

"""
tab = ["| GT-ID | Påstand | Verdi | Enhet | Kilde + sted | Ordrett utdrag | Hentet (UTC) | Verifisering 1 | Verifisering 2 | Status |",
       "|---|---|---|---|---|---|---|---|---|---|"]
for row in ut:
    tab.append("| " + " | ".join(c.replace("\n", " ") for c in row) + " |")
sammendrag = "\n\n**Status per rad:** " + ", ".join(f"{k}: {v}" for k, v in sorted(teller.items())) + f" (generert {now()})\n"
(ROOT / "GROUND_TRUTH.md").write_text(hode + "\n".join(tab) + sammendrag, encoding="utf-8")
print(sammendrag.strip())
for row in ut:
    if not row[9].startswith("VERIFISERT"):
        print("  ", row[0], row[9], "|", row[7][:160])
