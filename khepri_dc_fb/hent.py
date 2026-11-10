"""KHEPRI-DC-FB: hentemoduler med kontrollstreng og manifest (skjelett; ikke kjørt mot nye data i denne runden).

Hver henting skriver én manifestrad: kilde, nøkkel, vindu, status, kontrollstreng_funnet, årsak, sha256, bytes, hentet_utc.
Kontrollstrenger (preregistrering avsnitt 12):
  JAO:     ikke-tom JSON-liste, første rad har «dateTimeUtc» og minst ett felt med forventet prefiks (hub_ / min_).
  ENTSO-E: svaret inneholder «TimeSeries»; ellers føres Acknowledgement-årsakskoden som fravær.
Tokens leses fra miljøet og skrives aldri ut; URL-er saneres før logging.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Optional

MANIFEST_FELT = ["kilde", "noekkel", "vindu_start", "vindu_slutt", "status", "kontrollstreng_funnet", "aarsak",
                 "sha256", "bytes", "hentet_utc"]


def naa_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def saner(tekst: str) -> str:
    """Fjerner token-verdier fra URL-er og tekst før logging."""
    return re.sub(r"(securityToken=)[^&\s]+", r"\1***", tekst)


def kontroll_jao(rader: Any, prefiks: str) -> tuple[bool, str]:
    """(ok, årsak) for et JAO-svar."""
    if not isinstance(rader, list) or not rader:
        return False, "tom eller ikke liste"
    første = rader[0]
    if not isinstance(første, dict) or "dateTimeUtc" not in første:
        return False, "mangler dateTimeUtc"
    if not any(k.startswith(prefiks) for k in første):
        return False, f"mangler felt med prefiks {prefiks}"
    return True, ""


def kontroll_entsoe(body: bytes) -> tuple[str, str]:
    """(status, årsak): OK, INGEN_DATA (årsakskode 999) eller FEILET."""
    if b"TimeSeries" in body:
        return "OK", ""
    tekst = body.decode("utf-8", "replace")
    if "Acknowledgement_MarketDocument" in tekst:
        koder = ",".join(re.findall(r"<(?:\w+:)?code>([^<]*)<", tekst))
        return ("INGEN_DATA" if "999" in koder else f"ACK {koder}"), koder
    return "FEILET", "verken TimeSeries eller Acknowledgement"


def skriv_manifestrad(manifest: Path, rad: dict) -> None:
    ny = not manifest.exists()
    with open(manifest, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=MANIFEST_FELT)
        if ny:
            w.writeheader()
        w.writerow({k: rad.get(k, "") for k in MANIFEST_FELT})


def lagre_jao(ut: Path, manifest: Path, endepunkt: str, dag: str, rader: Optional[list], feil: str = "") -> dict:
    """Lagrer ett JAO-døgn (rå JSON) og skriver manifestrad med kontrollstreng. Gjør ingen nettkall selv."""
    prefiks = {"netPos": "hub_", "maxNetPos": "min_"}[endepunkt]
    rad = dict(kilde=f"JAO/{endepunkt}", noekkel=endepunkt, vindu_start=dag, vindu_slutt=dag, hentet_utc=naa_utc())
    if rader is None:
        rad.update(status="INGEN_DATA", kontrollstreng_funnet="nei", aarsak=feil)
    else:
        ok, aarsak = kontroll_jao(rader, prefiks)
        body = json.dumps(rader, ensure_ascii=False).encode()
        p = ut / f"jao_{endepunkt}_{dag}.json"
        p.write_bytes(body)
        rad.update(status="OK" if ok else "FEILET", kontrollstreng_funnet="ja" if ok else "nei", aarsak=aarsak,
                   sha256=hashlib.sha256(body).hexdigest(), bytes=len(body))
    skriv_manifestrad(manifest, rad)
    return rad


# Tempo for senere henting (etter JAOs fire HTTP 429-svar i A2-hentingen uten pause, GT-664–GT-667):
PAUSE_MELLOM_KALL_S = 2.0      # fast pause etter hvert kall mot JAO
VENT_VED_429_S = 60.0          # ventetid ved HTTP 429 uten Retry-After (samme som jao-py sin RATE_LIMIT_HANDLER)


def ventetid_429(headers: dict, standard: float = VENT_VED_429_S) -> float:
    """Sekunder å vente etter HTTP 429: Retry-After (sekunder) hvis oppgitt og gyldig, ellers standard."""
    v = {k.lower(): val for k, val in (headers or {}).items()}.get("retry-after")
    try:
        s = float(v)
        return s if s >= 0 else standard
    except (TypeError, ValueError):
        return standard


class Tempo:
    """Holder minst pause_s sekunder mellom kall. klokke og sov kan byttes ut i tester."""

    def __init__(self, pause_s: float = PAUSE_MELLOM_KALL_S, klokke=None, sov=None):
        import time as _t
        self.pause_s, self.klokke, self.sov, self.sist = pause_s, klokke or _t.monotonic, sov or _t.sleep, None

    def vent(self) -> float:
        """Venter til pause_s har gått siden forrige kall; returnerer ventetiden."""
        naa = self.klokke()
        v = 0.0 if self.sist is None else max(0.0, self.pause_s - (naa - self.sist))
        if v:
            self.sov(v)
        self.sist = self.klokke()
        return v
