"""Henter én nettside som tekst (samme metode som tools/hent_kilder.py: urllib + html.parser, generisk User-Agent uten e-post).

Skriver «URL / Hentet (UTC) / Metode» øverst og deretter teksten. Skriver hentetidspunktet til stdout (verktøyutskrift).
Bruk: python3 -I -B tools/hent_side.py <url> <utfil>
"""
import datetime as dt
import html.parser
import sys
import urllib.request
from pathlib import Path

url, ut = sys.argv[1], Path(sys.argv[2])


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


t = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
req = urllib.request.Request(url, headers={"User-Agent": "EcoDeco-research/1.0"})
with urllib.request.urlopen(req, timeout=120) as r:
    data = r.read()
p = Txt()
p.feed(data.decode("utf-8", errors="replace"))
body = "\n".join(l.strip() for l in "".join(p.out).splitlines() if l.strip())
ut.write_text(f"URL: {url}\nHentet (UTC): {t}\nMetode: urllib + html.parser (tekst gjengitt, HTML-markering fjernet)\n\n{body}\n", encoding="utf-8")
print(f"{t} hentet {url} -> {ut} ({len(body)} tegn)")
