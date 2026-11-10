"""Steg 5: ankersjekk. Feiler høyt (exit 1) ved første klasse avvik; skriver alle avvik før den avslutter.

(i)   sha256 og bytes i kilder/KILDER_MANIFEST.csv stemmer mot filene (rader med status OK).
(ii)  hver GT-rad med status VERIFISERT×2 har en kilde-ID som finnes i manifestet med status OK.
(iii) hver DOI og arXiv-ID i GROUND_TRUTH.md og i alle .md-filer i repoet løses over nett, og tittelen er lik GT-tittelen
      for den ID-en (DOI: doi.org CSL-JSON; arXiv: export.arxiv.org API). Generisk User-Agent uten e-post. Ingen curl.
(v)   sha256-verdier i prereg på formen `<fil>` … `<64 heks>` er lik digesten i OTS-fila (steg 6) for samme fil.
(iv)  i ADR-filer (adr/KDF-*.md), prereg-filer (*PREREG*.md), PUBLISERINGSPORT.md og manuskript/*.tex (GT-ID i
      LaTeX-kommentaren på linja; se blokka for .tex nedenfor): hver linje med et tall eller et «sitat» har minst én GT-ID,
      alle GT-ID-ene på linja har status VERIFISERT×2, hvert tall på linja finnes i verdien til en GT-ID på linja, og hvert
      «sitat» er lik (eller ordrett del av) verdien til en GT-ID på linja.
      Unntatt fra tallkravet: ID-er (GT-nnn, K-nn, KDF-nnnn), versjonsmerker (v1, v2, prereg-v1), budområdekoder (NO1, SE3,
      DK1, NOS1, NO1A), ENTSO-E-dokumenttyper (A65), oppløsningskoder (PT15M), stegnavn (steg 3d), markdown-overskriftsnummer
      og listenummer i linjestart, og tekst i `kode`.
(vi)  genererte manuskriptfiler (manuskript/generert/): kilde-sha256 lik resultater/ og GT, og byte-lik ny kjøring.
(vii) manuskript/sources.csv (supplement) byte-lik det tools/lag_kildeliste.py bygger fra kilder/KILDER_MANIFEST.csv.
(viii) hver ots/<fil>.ots har den stemplede fila ots/<fil> ved siden av med sha256 lik «File sha256 hash» (unntak:
      prereg-tarballen), og ingen .ots-fil ligger utenfor ots/. En DOI som er reservert i et upublisert Zenodo-utkast
      (manifestets url_doi sier «reservert») gir INFO i (iii) til den løses; løses den, må tittelen være lik GT.
Bruk: python3 -I -B tools/check_anchors.py <rot> [--uten-nett]
"""
import csv
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

root = Path(sys.argv[1]).resolve()
uten_nett = "--uten-nett" in sys.argv
UA = "EcoDeco-research/1.0"
feil, info = [], []


def norm(s):
    s = s.replace("¦", "|")
    s = re.sub(r"[   \s]+", " ", s)
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    return re.sub(r"[«»“”\"]", "", s).strip().lower().rstrip(".,;:")


def tall(s):
    # tusenskille (mellomrom, også hardt og smalt hardt) bare etter et frittstående heltall på 1–3 sifre, ikke inne i lister
    # av desimaltall som «62.196 109.066»
    s = re.sub(r"(?<![\d.,])(\d{1,3})[ \u00a0\u202f](?=\d{3}(?![\d.,]\d))", r"\1", s)
    ut = []
    # desimalpunktum, eller desimalkomma med høyst tre sifre etter (ikke CSV-felt som «30,230410»)
    for x in re.findall(r"\d+(?:\.\d+|,\d{1,3}(?![\d.]))?", s):
        x = x.replace(",", ".")
        if "." in x:
            x = x.rstrip("0").rstrip(".")
        ut.append(x.lstrip("0") or "0")
    return ut


# --- GT
gt = {}
for line in open(root / "GROUND_TRUTH.md", encoding="utf-8"):
    if re.match(r"\| GT-\d{3} ", line):
        c = [x.strip() for x in line.strip().strip("|").split(" | ")]
        gt[c[0]] = dict(verdi=c[2], kilde=c[4].split(",")[0].strip(), utdrag=c[5], status=c[9])
man = {r["kilde_id"]: r for r in csv.DictReader(open(root / "kilder/KILDER_MANIFEST.csv", encoding="utf-8"))}

# (i)
n_i = 0
for kid, r in man.items():
    if r["status"] != "OK":
        info.append(f"(i) {kid} har status {r['status']} — ingen fil å kontrollere")
        continue
    f = root / "kilder" / r["fil"]
    if not f.exists():
        feil.append(f"(i) {kid}: fila {r['fil']} mangler")
        continue
    b = f.read_bytes()
    if hashlib.sha256(b).hexdigest() != r["sha256"] or str(len(b)) != r["bytes"]:
        feil.append(f"(i) {kid}: sha256/bytes stemmer ikke for {r['fil']}")
    n_i += 1
info.append(f"(i) {n_i} filer kontrollert mot manifestet")

# (ii)
n_ii = 0
for gid, g in gt.items():
    if g["status"].startswith("VERIFISERT×2"):
        n_ii += 1
        if g["kilde"] not in man or man[g["kilde"]]["status"] != "OK":
            feil.append(f"(ii) {gid}: kilde {g['kilde']} finnes ikke (med status OK) i manifestet")
ikke2 = [gid for gid, g in gt.items() if not g["status"].startswith("VERIFISERT×2")]
info.append(f"(ii) {n_ii} rader VERIFISERT×2; ikke ×2: {', '.join(ikke2) or 'ingen'}")

# (iii)
md = [p for p in root.rglob("*.md") if ".git" not in p.parts] + [p for p in (root / "manuskript").glob("*.tex")]
dois, arx = set(), set()
for p in md:
    t = p.read_text(errors="replace")
    dois |= {d.rstrip(".,;)\"").lower() for d in re.findall(r"10\.\d{4,9}/[^\s|)»\]]+", t)}  # avsluttende " fra JSON-utdrag
    arx |= set(re.findall(r"(?i)arxiv[: ]\s*(\d{4}\.\d{4,5})", t)) | set(re.findall(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", t))


def gt_tittel(kind, ident):
    for gid, g in gt.items():
        if not g["status"].startswith("VERIFISERT×2"):
            continue
        u = g["utdrag"].lower()
        if kind == "doi" and '"title":' in u and g["kilde"] in man and ident in man[g["kilde"]]["url_doi"].lower():
            return gid, g["verdi"]
        if kind == "arxiv" and g["kilde"] in man and ident in man[g["kilde"]]["url_doi"] and "tittel" in gid_paastand.get(gid, ""):
            return gid, g["verdi"]
    return None, None


gid_paastand = {r["gt_id"]: r["påstand"] for r in csv.DictReader(open(root / "gt/gt_rader.csv", encoding="utf-8"))}


def hent_json(url, accept):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


for d in sorted(dois):
    gid, forventet = gt_tittel("doi", d)
    if not gid:
        feil.append(f"(iii) DOI {d}: ingen VERIFISERT×2 GT-rad med tittel for denne DOI-en")
        continue
    if uten_nett:
        info.append(f"(iii) DOI {d}: nettsjekk hoppet over (--uten-nett); GT-tittel i {gid}")
        continue
    try:
        tittel = json.loads(hent_json("https://doi.org/" + d, "application/vnd.citationstyles.csl+json")).get("title", "")
        if norm(tittel) != norm(forventet):
            feil.append(f"(iii) DOI {d}: tittel «{tittel}» ≠ GT {gid} «{forventet}»")
        else:
            info.append(f"(iii) DOI {d}: løst, tittel = {gid}")
    except Exception as e:
        # en DOI reservert i et upublisert Zenodo-utkast (manifestets url_doi sier «reservert») løses først etter publisering
        if "reservert" in man[gt[gid]["kilde"]]["url_doi"]:
            info.append(f"(iii) DOI {d}: reservert i Zenodo-utkastet ({gt[gid]['kilde']}), løses ikke før publisering ({type(e).__name__}); GT-tittel i {gid}")
        else:
            feil.append(f"(iii) DOI {d}: kunne ikke løses ({type(e).__name__})")
for a in sorted(arx):
    gid, forventet = gt_tittel("arxiv", a)
    if not gid:
        feil.append(f"(iii) arXiv {a}: ingen VERIFISERT×2 GT-rad med tittel for denne ID-en")
        continue
    if uten_nett:
        info.append(f"(iii) arXiv {a}: nettsjekk hoppet over (--uten-nett); GT-tittel i {gid}")
        continue
    try:
        try:
            x = hent_json("https://export.arxiv.org/api/query?id_list=" + urllib.parse.quote(a), "application/atom+xml").decode()
            titler = re.findall(r"<entry>.*?<title>(.*?)</title>", x, re.S)
            kilde = "API"
        except Exception:  # API-et rate-begrenser (429); abs-sidens citation_title er reserve
            x = hent_json("https://arxiv.org/abs/" + urllib.parse.quote(a), "text/html").decode()
            titler = re.findall(r'<meta name="citation_title" content="([^"]*)"', x)
            kilde = "abs-side"
        tittel = re.sub(r"\s+", " ", titler[0]).strip() if titler else ""
        if norm(tittel) != norm(forventet):
            feil.append(f"(iii) arXiv {a}: tittel «{tittel}» ≠ GT {gid} «{forventet}»")
        else:
            info.append(f"(iii) arXiv {a}: løst ({kilde}), tittel = {gid}")
    except Exception as e:
        feil.append(f"(iii) arXiv {a}: kunne ikke løses ({type(e).__name__})")

def sjekk_linje(sted, line, rest, sitater, ids):
    """Felles regel (iv) for .md og .tex: tall og sitater på linja må finnes i verdiene til GT-ID-ene på linja."""
    rest = re.sub(r"\b(K-\d{2,3}|KDF-\d{4}|prereg-v\d|v\d+(?:\.\d+)*s?)\b", " ", rest)
    # identifikatorer med sifre: budområder (NO1, SE3, DK1, NOS1, NO1A), ENTSO-E-dokumenttyper (A65),
    # oppløsningskoder (PT15M), stegnavn (steg 3d, 3c-supplement)
    rest = re.sub(r"\b(NOS?\d[A-Z]?|SE\d|DK\d|A\d{2}|PT\d+M|steg \d+[a-d]?|\d[a-d](?:-supplement)?)\b", " ", rest)
    rest = re.sub(r"\bsha256\b", " ", rest)  # algoritmenavn, ikke tall
    rest = re.sub(r"^\s*#+\s*\d+(?:\.\d+)*\.?", " ", rest)
    rest = re.sub(r"^\s*\d+\.\s", " ", rest)
    talliste = tall(rest)
    for gid in ids:
        if gid not in gt:
            feil.append(f"(iv) {sted}: {gid} finnes ikke i GT")
        elif not gt[gid]["status"].startswith("VERIFISERT×2"):
            feil.append(f"(iv) {sted}: {gid} har status {gt[gid]['status']}")
    if not talliste and not sitater:
        return 0
    if not ids:
        feil.append(f"(iv) {sted}: tall/sitat uten GT-ID: {line.strip()[:120]}")
        return 1
    verdier = [gt[g]["verdi"] for g in ids if g in gt]
    alle_tall = [x for v in verdier for x in tall(v)]
    for x in talliste:
        if x not in alle_tall:
            feil.append(f"(iv) {sted}: tallet {x} finnes ikke i verdien til {', '.join(ids)}")
    for q in sitater:
        if not any(norm(q) and norm(q) in norm(v) for v in verdier):
            feil.append(f"(iv) {sted}: «{q[:80]}» er ikke lik verdien til {', '.join(ids)}")
    return 1


# (iv)
TAG = re.compile(r"GT-(\d{3})(?:\s*[–-]\s*GT-(\d{3}))?")
filer = sorted((root / "adr").glob("KDF-*.md")) + sorted(p for p in root.glob("*PREREG*.md")) + \
    sorted(p for p in root.glob("PUBLISERINGSPORT.md"))
n_linjer = 0
for p in filer:
    i_kode = False
    for nr, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip().startswith("```"):
            i_kode = not i_kode
            continue
        ids = []
        for a, b in TAG.findall(line):
            ids += [f"GT-{k:03d}" for k in range(int(a), int(b or a) + 1)]
        rest = re.sub(r"`[^`]*`", " ", line)
        rest = TAG.sub(" ", rest)
        sitater = re.findall(r"«([^»]+)»", rest)  # sitater sammenlignes ordrett, før ID-unntakene under
        rest = re.sub(r"«[^»]+»", " ", rest)
        n_linjer += sjekk_linje(f"{p.relative_to(root)}:{nr}", line, rest, sitater, ids)


info.append(f"(iv) {len(filer)} ADR/prereg/port-filer, {n_linjer} linjer med tall eller sitat kontrollert")

import subprocess

# (iv) for manuskriptet: manuskript/*.tex (ikke generert/ og ikke preambel.tex). GT-ID-ene står i LaTeX-kommentaren på
# samme linje («% GT-123»). Teksten før kommentaren kontrolleres som i .md: tall og ``sitater'' må finnes i verdiene.
# Unntatt fra tallkravet: argumenter til \ref, \label, \cite, \url, \input, \includegraphics, \texttt, URL-delen av
# \href, og tallmakroer \res… (de kommer fra manuskript/generert/tall.tex, kontrollert i (vi)).
n_tex, n_tex_ankre = 0, 0
texfiler = sorted(p for p in (root / "manuskript").glob("*.tex") if p.name != "preambel.tex")
for p in texfiler:
    for nr, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        m = re.search(r"(?<!\\)%", line)
        tekst, kommentar = (line[:m.start()], line[m.start():]) if m else (line, "")
        ids = []
        for a, b in TAG.findall(kommentar):
            ids += [f"GT-{k:03d}" for k in range(int(a), int(b or a) + 1)]
        n_tex_ankre += len(TAG.findall(kommentar))
        rest = re.sub(r"\\(?:ref|label|cite|url|nolinkurl|input|texttt|eqref)\{[^}]*\}", " ", tekst)
        rest = re.sub(r"\\includegraphics(?:\[[^\]]*\])?\{[^}]*\}", " ", rest)
        rest = re.sub(r"\\href\{[^}]*\}", " ", rest)
        rest = re.sub(r"\\multicolumn\{\d+\}\{[^}]*\}|\\cmidrule\(lr\)\{[\d-]+\}|\\begin\{thebibliography\}\{\d+\}", " ", rest)
        rest = re.sub(r"\\res[A-Za-z]+", " ", rest)
        rest = re.sub(r"\\[A-Za-z]+", " ", rest)  # kommandonavn har ikke sifre
        sitater = re.findall(r"``(.+?)''", rest)
        rest = re.sub(r"``.+?''", " ", rest)
        rest = rest.replace("\\%", " ")
        rest = re.sub(r"(?<=\d)(?:~|\\,)(?=\d{3}\b)", "", rest)  # tusenskille i LaTeX (75~380)
        rest = re.sub(r"\b(A[1-9]|T[1-9]|M[1-9])\b", " ", rest)  # merkene for avvik, tolkninger og merknader
        n_tex += sjekk_linje(f"{p.relative_to(root)}:{nr}", line, rest, sitater, ids)
info.append(f"(iv) {len(texfiler)} .tex-filer i manuskript/, {n_tex} linjer med tall eller sitat kontrollert, {n_tex_ankre} GT-ankre")

# (vi) genererte manuskriptfiler: første linje nevner kildefil, sha256 og GT-ID; hashen må være lik fila i resultater/ og
# verdien til GT-ID-en (VERIFISERT×2), og en ny kjøring av tools/lag_manus.py må gi like byte for alle filer.
import tempfile
gen = root / "manuskript/generert"
n_vi = 0
if gen.exists():
    for p in sorted(gen.glob("*.tex")):
        forste = p.read_text(encoding="utf-8").splitlines()[0]
        trip = re.findall(r"resultater/(\S+) sha256 ([0-9a-f]{64}) \[(GT-\d{3})\]", forste)
        if not forste.startswith("% generert av tools/lag_manus.py") or not trip:
            feil.append(f"(vi) {p.name}: mangler generert-linje med kilde, sha256 og GT-ID")
        for fil, h, gid in trip:
            n_vi += 1
            ekte = hashlib.sha256((root / "resultater" / fil).read_bytes()).hexdigest()
            if h != ekte:
                feil.append(f"(vi) {p.name}: sha256 for resultater/{fil} i fila ≠ fila på disk")
            if gid not in gt or gt[gid]["verdi"] != h or not gt[gid]["status"].startswith("VERIFISERT×2"):
                feil.append(f"(vi) {p.name}: {gid} har ikke verdien {h[:12]}… med VERIFISERT×2")
    with tempfile.TemporaryDirectory() as d:
        # samme tolk som laget filene (matplotlib-versjonen står i fig_kilder.tex); kan overstyres med KDF_GEN_PY
        import os
        gen_py = os.environ.get("KDF_GEN_PY", "/opt/homebrew/bin/python3")
        r = subprocess.run([gen_py, "-I", "-B", str(root / "tools/lag_manus.py"), d], capture_output=True, text=True)
        if r.returncode:
            feil.append(f"(vi) tools/lag_manus.py feilet: {r.stderr.strip()[-200:]}")
        else:
            for q in sorted(gen.iterdir()):
                ny = Path(d) / q.name
                if not ny.exists() or ny.read_bytes() != q.read_bytes():
                    feil.append(f"(vi) {q.name}: ny kjøring av tools/lag_manus.py gir ikke like byte")
            for q in Path(d).iterdir():
                if not (gen / q.name).exists():
                    feil.append(f"(vi) {q.name}: lages av tools/lag_manus.py, men mangler i manuskript/generert/")
    info.append(f"(vi) {len(list(gen.iterdir()))} genererte filer, {n_vi} kilde-sha256 kontrollert mot resultater/ og GT, ny kjøring byte-lik")

# (vii) supplementet manuskript/sources.csv: bygges på nytt fra kilder/KILDER_MANIFEST.csv med tools/lag_kildeliste.py og
# må være byte-likt, med én rad per kilde i manifestet.
ks = root / "manuskript/sources.csv"
if ks.exists():
    sys.path.insert(0, str(root / "tools"))
    import lag_kildeliste
    ny = lag_kildeliste.bygg()
    if ks.read_text(encoding="utf-8") != ny:
        feil.append("(vii) manuskript/sources.csv er ikke lik det tools/lag_kildeliste.py bygger fra KILDER_MANIFEST.csv")
    n_ks = len(list(csv.DictReader(open(ks, encoding="utf-8"))))
    if n_ks != len(man):
        feil.append(f"(vii) manuskript/sources.csv har {n_ks} rader, manifestet {len(man)}")
    info.append(f"(vii) manuskript/sources.csv: {n_ks} kilder, lik manifestet (K-ID, tittel, URL, hentet_utc, sha256)")

# (v) sha256-verdier i prereg (i `kode`, på formen `<filnavn>` … `sha256`) skal være lik digesten i OTS-fila for samme fil
import subprocess
# Stemplene ligger i ots/ ved siden av den stemplede fila (K-119 punkt 1). Filer stemplet i en tidligere commit har
# commit-ID-en i navnet (GROUND_TRUTH_10b8886.md); prereg viser til dem under det opprinnelige navnet.
ots_dig = {}
for o in sorted((root / "ots").glob("*.ots")):
    ut = subprocess.run(["ots", "info", str(o)], capture_output=True, text=True).stdout
    m = re.search(r"File sha256 hash: ([0-9a-f]{64})", ut)
    if not m:
        feil.append(f"(v) {o.relative_to(root)}: ingen «File sha256 hash» i ots info")
        continue
    ots_dig[re.sub(r"_[0-9a-f]{7}(?=\.[a-z]+$)", "", o.name[:-4])] = m.group(1)
    # (viii) den stemplede fila ligger ved siden av stemplet og har samme sha256 (unntak: prereg-tarballen, som ikke
    # publiseres fordi den inneholder kilder/)
    f = o.with_suffix("")
    if o.name == "khepri-dc-fb-prereg-v1.tar.gz.ots":
        info.append(f"(viii) {o.relative_to(root)}: unntak (tarballen publiseres ikke), digest {m.group(1)[:12]}…")
    elif not f.exists():
        feil.append(f"(viii) {o.relative_to(root)}: den stemplede fila {f.name} mangler i ots/")
    elif hashlib.sha256(f.read_bytes()).hexdigest() != m.group(1):
        feil.append(f"(viii) {f.relative_to(root)}: sha256 ≠ digesten i {o.name}")
    else:
        info.append(f"(viii) {f.relative_to(root)}: sha256 = digesten i {o.name} ({m.group(1)[:12]}…)")
for o in root.rglob("*.ots"):
    if ".git" not in o.parts and o.parent != root / "ots":
        feil.append(f"(viii) {o.relative_to(root)}: .ots-fil utenfor ots/")
n_v = 0
for p in sorted(root.glob("*PREREG*.md")):
    for nr, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        for navn, dig in re.findall(r"`([A-Za-z_./-]+\.(?:md|csv))`[^`]*?`([0-9a-f]{64})`", line):
            n_v += 1
            base = navn.split("/")[-1]
            if base not in ots_dig:
                feil.append(f"(v) {p.name}:{nr}: ingen OTS-digest for {navn}")
            elif ots_dig[base] != dig:
                feil.append(f"(v) {p.name}:{nr}: sha256 for {navn} ({dig[:12]}…) ≠ OTS-digest ({ots_dig[base][:12]}…)")
info.append(f"(v) {n_v} sha256-referanser i prereg kontrollert mot OTS-digest ({', '.join(f'{k}: {v[:12]}…' for k, v in ots_dig.items() if k in ('GROUND_TRUTH.md', 'KILDER_MANIFEST.csv', 'POSISJONERING.md'))})")

for l in info:
    print("OK  " if not l.startswith("(i) K") else "INFO", l)
for l in feil:
    print("FEIL", l)
print(f"\n{'GRØNN' if not feil else 'RØD'}: {len(feil)} avvik")
sys.exit(1 if feil else 0)
