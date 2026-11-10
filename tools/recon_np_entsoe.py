"""Recon (K-95-bestillingen, punkt 2 og 4): ENTSO-E Transparency 12.1.E «Implicit Allocations – Net Positions»
(documentType A25, businessType B09, contract_MarketAgreement.Type A01 = day-ahead), per NO-sone.
Ingen analyse, ingen bruk i resultater.

Token fra miljøvariabelen ENTSOE_API_TOKEN (lastes av kalleren fra ~/.config/khepri/entsoe.env i samme kommando);
tokenet skrives aldri ut, URL-er saneres. Generisk User-Agent uten e-post. 5 s mellom kall, høyst 3 forsøk.
Rå XML (gzip) per sone og vindu i <ut>/ (utenfor git) og manifest.csv (sone, vindu, status, årsak, sha256, bytes,
hentet_utc, TimeSeries-antall, in/out-domener og fortegnsretning fra XML).
Bruk: set -a; . ~/.config/khepri/entsoe.env; set +a; python3 -I -B tools/recon_np_entsoe.py <ut> <YYYY-MM-DD> <YYYY-MM-DD>
      (vindu [start 00:00Z, slutt 00:00Z) i UTC; én fil per sone og vindu)
"""
import csv
import datetime as dt
import gzip
import hashlib
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://web-api.tp.entsoe.eu/api"
UA = "KHEPRI-DC-FB-recon/1.0 (python-urllib)"
EIC = {"NO_1": "10YNO-1--------2", "NO_2": "10YNO-2--------T", "NO_3": "10YNO-3--------J",
       "NO_4": "10YNO-4--------9", "NO_5": "10Y1001A1001A48H"}
tok = os.environ.get("ENTSOE_API_TOKEN", "")
assert len(tok) > 10, "mangler token"
out = Path(sys.argv[1]).expanduser()
out.mkdir(parents=True, exist_ok=True)
a, b = sys.argv[2], sys.argv[3]
fmt = lambda s: dt.datetime.fromisoformat(s).strftime("%Y%m%d0000")


def naa():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


man = out / "manifest.csv"
ny = not man.exists()
with open(man, "a", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    if ny:
        w.writerow(["sone", "vindu", "status", "aarsak", "sha256", "bytes", "hentet_utc", "timeseries", "domener"])
    for z, eic in EIC.items():
        q = {"documentType": "A25", "businessType": "B09", "contract_MarketAgreement.Type": "A01",
             "in_Domain": eic, "out_Domain": eic, "periodStart": fmt(a), "periodEnd": fmt(b), "securityToken": tok}
        url = API + "?" + urllib.parse.urlencode(q)
        body, feil = b"", ""
        for f in range(3):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=180) as r:
                    body = r.read()
                break
            except urllib.error.HTTPError as e:
                body = e.read()
                feil = f"HTTP {e.code}"
                if e.code < 500:
                    break
            except Exception as e:
                feil = type(e).__name__
            time.sleep(10 * (f + 1))
        tekst = body.decode("utf-8", "replace")
        n_ts = tekst.count("<TimeSeries>")
        if n_ts:
            status, aarsak = "OK", ""
        else:
            status = "INGEN_DATA"
            aarsak = " ".join(re.findall(r"<(?:\w+:)?text>([^<]*)<", tekst))[:200] or feil
        dom = sorted(set(re.findall(r"<(in_Domain|out_Domain)\.mRID[^>]*>([^<]+)<", tekst)))
        p = out / f"A25_B09_{z}_{a}_{b}.xml.gz"
        p.write_bytes(gzip.compress(body))
        w.writerow([z, f"{a}/{b}", status, aarsak.replace(tok, "***"), hashlib.sha256(body).hexdigest(), len(body), naa(),
                    n_ts, " ".join(f"{k}={v}" for k, v in dom)])
        fh.flush()
        print(z, a, b, status, n_ts, aarsak[:100].replace(tok, "***"))
        time.sleep(5)
