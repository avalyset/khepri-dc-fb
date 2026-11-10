"""Steg 0: henter kildene i tools/kildeliste.csv og lokale kilder, skriver kilder/KILDER_MANIFEST.csv.

- PDF lagres som den er; HTML gjengis som tekst (.txt) med URL og hentetidspunkt øverst.
- PDF-tekst trekkes ut med `pdftotext -layout` til kilder/txt/<K-ID>.txt (avledet, for lesing og verifisering).
- Kontrollstrengen må finnes i teksten (store/små bokstaver ignoreres); ellers FEILET.
- User-Agent er generisk, uten e-post.
Bruk: python3 -I tools/hent_kilder.py <repo-rot>
"""
import csv
import datetime as dt
import hashlib
import html.parser
import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
KILDER = ROOT / "kilder"
TXT = KILDER / "txt"
TXT.mkdir(parents=True, exist_ok=True)
UA = "EcoDeco-research/1.0"
V1 = Path("/Volumes/Vault/khepri-dc/repo-public")
RECON = Path.home() / "khepri-data/recon-fb-2026-11-09"
JAOPY = RECON / "venv/lib/python3.14/site-packages"


def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class Txt(html.parser.HTMLParser):
    SKIP = {"script", "style", "noscript", "svg", "head"}

    def __init__(self):
        super().__init__()
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        if tag in {"p", "br", "li", "h1", "h2", "h3", "h4", "tr", "div", "section"}:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read(), r.headers.get("Content-Type", "")


def pdf_pages_text(path, kid):
    info = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True).stdout
    pages = next((l.split()[-1] for l in info.splitlines() if l.startswith("Pages:")), "")
    subprocess.run(["pdftotext", "-layout", str(path), str(TXT / f"{kid}.txt")], check=True)
    return pages, (TXT / f"{kid}.txt").read_text(errors="replace")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


rows = []
for r in csv.DictReader(open(ROOT / "tools/kildeliste.csv", encoding="utf-8")):
    kid, out, t = r["kilde_id"], KILDER / r["fil"], now()
    rec = dict(kilde_id=kid, tittel=r["tittel"], url_doi=r["url"], fil=r["fil"], hentet_utc=t,
               sha256="", bytes="", sider="", kontrollstreng=r["kontrollstreng"], kontroll_funnet="", status="")
    try:
        data, ctype = fetch(r["url"])
        if r["type"] == "pdf":
            if not data.startswith(b"%PDF"):
                raise ValueError(f"ikke PDF (Content-Type {ctype}, {len(data)} bytes)")
            out.write_bytes(data)
            pages, text = pdf_pages_text(out, kid)
        else:
            p = Txt()
            p.feed(data.decode("utf-8", errors="replace"))
            body = "\n".join(l.strip() for l in "".join(p.out).splitlines() if l.strip())
            text = f"URL: {r['url']}\nHentet (UTC): {t}\nMetode: urllib + html.parser (tekst gjengitt, HTML-markering fjernet)\n\n{body}\n"
            out.write_text(text, encoding="utf-8")
            pages = ""
        ok = r["kontrollstreng"].lower() in text.lower()
        rec.update(sha256=sha(out), bytes=out.stat().st_size, sider=pages,
                   kontroll_funnet="ja" if ok else "nei", status="OK" if ok else "FEILET (kontrollstreng ikke funnet)")
    except Exception as e:  # feilet henting føres, hoppes ikke over
        rec.update(status=f"FEILET ({type(e).__name__}: {str(e)[:120]})", kontroll_funnet="nei")
    rows.append(rec)
    print(kid, rec["status"], rec["bytes"], rec["sider"])


def local(kid, tittel, src_desc, out_name, content_bytes, kontroll):
    out = KILDER / out_name
    out.write_bytes(content_bytes)
    text = content_bytes.decode("utf-8", errors="replace")
    ok = kontroll.lower() in text.lower()
    rows.append(dict(kilde_id=kid, tittel=tittel, url_doi=src_desc, fil=out_name, hentet_utc=now(),
                     sha256=sha(out), bytes=out.stat().st_size, sider="", kontrollstreng=kontroll,
                     kontroll_funnet="ja" if ok else "nei", status="OK" if ok else "FEILET (kontrollstreng ikke funnet)"))
    print(kid, rows[-1]["status"])


def git(*args):
    return subprocess.run(["git", "-C", str(V1), *args], capture_output=True, check=True).stdout


local("K-14", "KHEPRI-DC v1 manus (tagg v1.0.1)", "git show v1.0.1:manus/MANUS_KHEPRI-DC_v1_2026-11-02.md i " + str(V1),
      "K-14_KHEPRI-DC_v1_manus_v1.0.1.md", git("show", "v1.0.1:manus/MANUS_KHEPRI-DC_v1_2026-11-02.md"), "KHEPRI-DC")
local("K-15", "KHEPRI-DC v1 README (tagg v1.0.1)", "git show v1.0.1:README.md i " + str(V1),
      "K-15_KHEPRI-DC_v1_README_v1.0.1.md", git("show", "v1.0.1:README.md"), "KHEPRI-DC")
local("K-21", "KHEPRI-DC v1 Power BI-avlesning 02.11 (tagg v1.0.1)", "git show v1.0.1:analyse/POWERBI_AVLESNING_KHEPRI-DC_v0_2026-11-02.md i " + str(V1),
      "K-21_KHEPRI-DC_v1_POWERBI_AVLESNING_2026-11-02.md", git("show", "v1.0.1:analyse/POWERBI_AVLESNING_KHEPRI-DC_v0_2026-11-02.md"), "Datasenter")
local("K-22", "KHEPRI-DC v1 params/parametre.json (tagg v1.0.1)", "git show v1.0.1:params/parametre.json i " + str(V1),
      "K-22_KHEPRI-DC_v1_parametre.json", git("show", "v1.0.1:params/parametre.json"), "0.7")
gitinfo = ("$ git -C " + str(V1) + " rev-list -n1 v1.0.1\n").encode() + git("rev-list", "-n1", "v1.0.1") + \
          ("$ git -C " + str(V1) + " rev-parse HEAD\n").encode() + git("rev-parse", "HEAD") + \
          ("$ git -C " + str(V1) + " remote get-url origin\n").encode() + git("remote", "get-url", "origin") + \
          ("$ git -C " + str(V1) + " cat-file -p v1.0.1\n").encode() + git("cat-file", "-p", "v1.0.1")
local("K-24", "KHEPRI-DC v1 git-tagg og HEAD (kommandoutskrift)", "git i " + str(V1), "K-24_KHEPRI-DC_v1_git.txt", gitinfo, "v1.0.1")
local("K-20", "Recon Power BI-avlesning 09.11.2026", str(RECON / "POWERBI_AVLESNING_2026-11-09.md"),
      "K-20_POWERBI_AVLESNING_2026-11-09.md", (RECON / "POWERBI_AVLESNING_2026-11-09.md").read_bytes(), "Datasenter")
local("K-23", "Recon JAO Nordic maxNetPos 2026-10-26..2026-11-01 (samlet CSV)", str(RECON / "maxNetPos_nordic_2026-10-26_2026-11-01.csv"),
      "K-23_recon_maxNetPos_nordic_2026-10-26_2026-11-01.csv", (RECON / "maxNetPos_nordic_2026-10-26_2026-11-01.csv").read_bytes(), "max_NO1")
meta = next(JAOPY.glob("jao_py-*.dist-info/METADATA"))
local("K-28", "jao-py jao_nordic.py + METADATA (installert i recon-venv)", str(JAOPY / "jao/jao_nordic.py") + " + " + str(meta),
      "K-28_jao-py_jao_nordic_og_METADATA.txt",
      b"### " + str(JAOPY / "jao/jao_nordic.py").encode() + b"\n" + (JAOPY / "jao/jao_nordic.py").read_bytes() +
      b"\n### " + str(meta).encode() + b" (de 12 forste linjene)\n" + b"\n".join(meta.read_bytes().splitlines()[:12]) + b"\n",
      "JaoPublicationToolPandasNordics")

for kid, doi in [("K-29", "10.5281/zenodo.23887356"), ("K-30", "10.5281/zenodo.23101127"), ("K-31", "10.5281/zenodo.22893246")]:
    t = now()
    try:
        req = urllib.request.Request("https://doi.org/" + doi, headers={"User-Agent": UA, "Accept": "application/vnd.citationstyles.csl+json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        title = json.loads(data).get("title", "")
        local(kid, f"DOI-metadata (CSL-JSON via doi.org) {doi}", "https://doi.org/" + doi, f"{kid}_doi_{doi.replace('/', '_')}.json", data, "title")
        print("   tittel:", title)
    except Exception as e:
        rows.append(dict(kilde_id=kid, tittel=f"DOI-metadata {doi}", url_doi="https://doi.org/" + doi, fil="", hentet_utc=t, sha256="",
                         bytes="", sider="", kontrollstreng="title", kontroll_funnet="nei", status=f"FEILET ({type(e).__name__}: {e})"))
        print(kid, "FEILET", e)

rows.sort(key=lambda d: int(d["kilde_id"].split("-")[1]))
with open(KILDER / "KILDER_MANIFEST.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print("skrev", KILDER / "KILDER_MANIFEST.csv", len(rows), "rader")
