"""KHEPRI-DC-FB: headroom og hendelser som rene funksjoner (ingen I/O, ingen data).

Definisjoner (preregistrering avsnitt 5):
  H(t) = NP(t) − minNP(t)                    importheadroom, MW (NP = nettoeksport; minNP ≤ 0 er største import)
  hendelse(t) = L_f > H(t)                   streng ulikhet; manglende H gir None (telles som manglende)
  L_f = (E_ref − E_y) + b · (f · R_new + f · Q),  R_new = max(0, R − E_ref / b)   (som v1, med w = q = f)
  H2(t) = H(t) + (installert − faktisk regulerbar vannkraft)   sekundærmål, øvre grense
           regulerbar vannkraft = Hydro Water Reservoir + Hydro Pumped Storage (produksjonssiden) [GT-320];
           faktisk pumpekraft per A75-intervall etter K-77: produksjon / pumpeintervall (0) / datahull (MTU manglende)
  time = hendelse hvis minst én MTU i timen er hendelse; mangler en MTU, er timen manglende [GT-318, GT-346]
"""
from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
import math
from typing import Optional, Sequence


def mangler(x: Optional[float]) -> bool:
    """Manglende verdi: None eller NaN (NaN fra CSV-kilder behandles som manglende, aldri som tall)."""
    return x is None or (isinstance(x, float) and math.isnan(x))


def r_new(R: float, E_ref: float, b: float) -> float:
    """Ny reservert kapasitet utover det som alt er i drift (speiler v1 khepri_dc/analysis.py)."""
    return max(0.0, R - E_ref / b)


def last_paalagt(E_ref: float, E_y: float, R: float, Q: float, w: float, q: float, b: float) -> float:
    """Flat påslagslast i MW (speiler v1): (E_ref − E_y) + b · (w · R_new + q · Q)."""
    return (E_ref - E_y) + b * (w * r_new(R, E_ref, b) + q * Q)


def last_f(E_ref: float, E_y: float, R: float, Q: float, f: float, b: float) -> float:
    """Påslag langs kurven w = q = f."""
    return last_paalagt(E_ref, E_y, R, Q, f, f, b)


def headroom(np_mw: Optional[float], min_np_mw: Optional[float]) -> Optional[float]:
    """Importheadroom H = NP − minNP. None hvis en av verdiene mangler."""
    if mangler(np_mw) or mangler(min_np_mw):
        return None
    return np_mw - min_np_mw


def headroom_sekundaer(H: Optional[float], installert_mw: Optional[float], faktisk_mw: Optional[float]) -> Optional[float]:
    """Sekundærmål H2 = H + (installert − faktisk) regulerbar vannkraft. None hvis noe mangler."""
    if mangler(H) or mangler(installert_mw) or mangler(faktisk_mw):
        return None
    return H + (installert_mw - faktisk_mw)


def installert_regulerbar(magasin_mw: Optional[float], pumpe_mw: Optional[float], pumpeledd: bool) -> Optional[float]:
    """Installert regulerbar vannkraft fra A68 = Hydro Water Reservoir + Hydro Pumped Storage [GT-320].

    pumpeledd=False for soner der A68 oppgir «n/e» for pumpekraft (NO1, NO4): leddet er 0 [GT-354].
    Ellers gir manglende verdi None (ingen imputering).
    """
    if mangler(magasin_mw):
        return None
    if not pumpeledd:
        return magasin_mw
    if mangler(pumpe_mw):
        return None
    return magasin_mw + pumpe_mw


PRODUKSJON, PUMPEINTERVALL, DATAHULL = "produksjon", "pumpeintervall", "datahull"


def pumpekategori(produksjon_mw: Optional[float], forbruk_mw: Optional[float]) -> str:
    """Kategori for ett A75-intervall (time eller kvarter) for Hydro Pumped Storage etter K-77 punkt 1.

    Produksjonsverdi finnes -> produksjon. Mangler den og «Actual Consumption» er > 0 i samme intervall og sone
    -> pumpeintervall (produksjon settes til 0 før varighetsvektingen). Ellers -> datahull (også når kilden ikke
    har forbruksfeltet, eller forbruket er 0).
    """
    if not mangler(produksjon_mw):
        return PRODUKSJON
    if not mangler(forbruk_mw) and forbruk_mw > 0:
        return PUMPEINTERVALL
    return DATAHULL


def faktisk_regulerbar_mtu(intervaller: Sequence[tuple], mtu_minutter: int, pumpeledd: bool) -> Optional[float]:
    """Faktisk regulerbar vannkraft for én JAO-MTU, varighetsvektet over A75-intervallene i MTU-en (K-77 punkt 1).

    intervaller: (minutter, magasin_mw, pumpe_produksjon_mw, pumpe_forbruk_mw) for hvert A75-intervall i MTU-en.
    None (MTU manglende for sekundærmålet) hvis intervallene ikke dekker MTU-en, et intervall mangler verdi for
    Hydro Water Reservoir, eller et pumpekraftintervall er datahull. Pumpeintervall gir 0 før vektingen.
    pumpeledd=False (NO1, NO4): pumpeleddet er 0 og forbruk/produksjon for pumpekraft leses ikke [GT-354].
    """
    if not intervaller or sum(m for m, *_ in intervaller) != mtu_minutter:
        return None
    sum_mw = 0.0
    for minutter, magasin, prod, forbruk in intervaller:
        if mangler(magasin):
            return None
        pumpe = 0.0
        if pumpeledd:
            k = pumpekategori(prod, forbruk)
            if k == DATAHULL:
                return None
            pumpe = prod if k == PRODUKSJON else 0.0
        sum_mw += (magasin + pumpe) * minutter
    return sum_mw / mtu_minutter


def hendelse(L: float, H: Optional[float]) -> Optional[bool]:
    """True når påslaget krever mer import enn min nettoposisjon tillater (L > H). None ved manglende H."""
    if mangler(H):
        return None
    return L > H


def hendelse_time(hendelser: Sequence[Optional[bool]], minutter: Sequence[int]) -> Optional[bool]:
    """Timen er hendelse hvis minst én MTU i timen er hendelse [GT-318]. Dekker MTU-ene ikke hele timen,
    eller mangler en MTU (None), er timen manglende [GT-346]."""
    if len(hendelser) != len(minutter):
        raise ValueError("hendelser og minutter må ha samme lengde")
    if not hendelser or sum(minutter) != 60 or any(e is None for e in hendelser):
        return None
    return any(hendelser)


@dataclass(frozen=True)
class Utfall:
    timer_med_hendelse: int
    timer_gyldige: int
    timer_manglende: int
    andel_timer_med_hendelse: Optional[float]
    andel_mtu_med_hendelse: Optional[float]
    mtu_gyldige: int
    mtu_manglende: int


def utfall(H: Sequence[Optional[float]], start: Sequence[dt.datetime], minutter: Sequence[int], L: float) -> Utfall:
    """Utfall for én serie: MTU-er med intervallstart (UTC) og lengde i minutter, på fullt forventet rutenett
    (manglende MTU som None). Timer grupperes på UTC-timen MTU-en starter i. Andel hendelses-MTU og andel
    hendelsestimer rapporteres begge [GT-347]."""
    if not (len(H) == len(start) == len(minutter)):
        raise ValueError("H, start og minutter må ha samme lengde")
    timer: dict = {}
    n_h, n_g, n_m = 0, 0, 0
    for h, t, m in zip(H, start, minutter):
        e = hendelse(L, h)
        if e is None:
            n_m += 1
        else:
            n_g += 1
            n_h += int(e)
        es, ms = timer.setdefault(t.replace(minute=0, second=0, microsecond=0), ([], []))
        es.append(e)
        ms.append(m)
    per_time = [hendelse_time(e, m) for e, m in timer.values()]
    t_g = sum(1 for x in per_time if x is not None)
    t_h = sum(1 for x in per_time if x)
    return Utfall(t_h, t_g, len(per_time) - t_g, (t_h / t_g) if t_g else None, (n_h / n_g) if n_g else None, n_g, n_m)
