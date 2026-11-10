"""3b-anker: ordrette utdrag fra rådataene rundt MTU-skiftet for A65 og A75 (NO1), og to ankre beregnet fra utdragene.

Anker A (intervallstart): starttidspunktet for den første MTU-en med lengde 15 min.
  XML: Period med resolution PT15M; MTU nr. p dekker [timeInterval.start + (p−1)·15 min, … + 15 min).
  CSV (entsoe-py): radens tidsstempel er intervallstart; første rad der NESTE rad ligger 15 min senere.
Anker B (første 15-minutters tidsstempel i rekka): første tidsstempel der avstanden til FORRIGE tidsstempel er 15 min.
Utdragene skrives ordrett (linjer fra fila), med fil og sha256.
Bruk: python3 -I -B tools/utdrag_skifte.py > kilder/K-42_RAAUTDRAG_MTU-skifte.txt
"""
import csv
import datetime as dt
import hashlib
import re
from pathlib import Path

X = Path("/Volumes/Vault/khepri-dc/raw")
F = Path("/Volumes/Vault/khepri-data/flowtracing/raw/2025")
R = Path.home() / "khepri-data/raw/entsoe-rest"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def xml_utdrag(p, skifte_dato):
    """Skriver Period-hodene (ordrett) for perioden som slutter og perioden som starter ved skiftet, i første TimeSeries."""
    t = p.read_text()
    print(f"### XML {p}  sha256 {sha(p)}")
    ts = re.search(r"<TimeSeries>.*?</TimeSeries>", t, re.S).group(0)
    perioder = re.findall(r"<Period>.*?</Period>", ts, re.S)
    for per in perioder:
        s = re.search(r"<start>([^<]+)</start>", per).group(1)
        e = re.search(r"<end>([^<]+)</end>", per).group(1)
        if e.startswith(skifte_dato) or s.startswith(skifte_dato):
            linjer = per.splitlines()
            hode = [l for l in linjer[:8]]
            punkter = re.findall(r"<Point>\s*<position>(\d+)</position>\s*<quantity>([^<]*)</quantity>", per)
            print("\n".join(hode))
            print(f"    … første punkt: position {punkter[0][0]}, quantity {punkter[0][1]}; "
                  f"siste punkt: position {punkter[-1][0]}, quantity {punkter[-1][1]}; antall punkter {len(punkter)}")
    return perioder


def csv_utdrag(p, rundt_utc):
    rader = list(csv.reader(open(p, encoding="utf-8")))
    linjer = open(p, encoding="utf-8").read().splitlines()
    print(f"### CSV {p}  sha256 {sha(p)}")
    print(f"linje 1 (header): {linjer[0][:160]}")
    tider = []
    for i, r in enumerate(rader[1:], 2):
        if r and r[0][:2] == "20":
            tider.append((i, dt.datetime.fromisoformat(r[0]).astimezone(dt.timezone.utc)))
    idx = next(k for k, (i, t) in enumerate(tider) if t >= rundt_utc)
    for k in range(max(0, idx - 2), idx + 3):
        i, t = tider[k]
        print(f"linje {i}: {linjer[i - 1][:120]}    (UTC {t:%Y-%m-%dT%H:%MZ})")
    a = next(t for (i, t), (_, t2) in zip(tider, tider[1:]) if t2 - t == dt.timedelta(minutes=15))
    b = next(t2 for (_, t), (_, t2) in zip(tider, tider[1:]) if t2 - t == dt.timedelta(minutes=15))
    print(f"anker A (intervallstart for første 15-min MTU): {a:%Y-%m-%dT%H:%MZ}")
    print(f"anker B (første tidsstempel med 15 min til forrige): {b:%Y-%m-%dT%H:%MZ}")


print("Rådatautdrag rundt MTU-skiftet, NO1. Generert av tools/utdrag_skifte.py",
      dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"))
print()
print("== A65 (last), skifte rundt 2025-03-18")
xml_utdrag(X / "A65/A65_NO_1_2025.xml", "2025-03-18")
csv_utdrag(F / "A65/A65_NO_1_2025-03.csv", dt.datetime(2025, 3, 17, 23, tzinfo=dt.timezone.utc))
print()
print("== A75 (produksjon), skifte rundt 2025-04-10")
xml_utdrag(X / "A75/A75_NO_1_2025.xml", "2025-04-10")
csv_utdrag(F / "A75/A75_NO_1_2025-04.csv", dt.datetime(2025, 4, 9, 23, tzinfo=dt.timezone.utc))
csv_utdrag(R / "NO1_generation_2025.csv", dt.datetime(2025, 4, 9, 23, tzinfo=dt.timezone.utc))
