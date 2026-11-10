"""Enhetstester på håndregnede tall (ingen data, ingen nett)."""
import datetime as dt

import pytest

from khepri_dc_fb import headroom as hr


def test_r_new_som_v1_tabell():
    # v1 tabell 1: NO1 R = 1398, E_ref = 97, b = 0,70 -> R_new ≈ 1259 (1398 − 97/0,7 = 1259,43)
    assert hr.r_new(1398, 97, 0.7) == pytest.approx(1259.428571, abs=1e-6)


def test_r_new_aldri_negativ():
    # NO3 i v1: R = 96 < E_ref/b = 154/0,7 = 220 -> 0
    assert hr.r_new(96, 154, 0.7) == 0.0


def test_last_paalagt_handregnet():
    # R_new = 1000 − 100/0,7 = 857,142857; L = (100 − 80) + 0,7·(0,5·857,142857 + 0,5·500) = 20 + 475 = 495
    assert hr.last_paalagt(100, 80, 1000, 500, 0.5, 0.5, 0.7) == pytest.approx(495.0, abs=1e-9)
    assert hr.last_f(100, 80, 1000, 500, 0.5, 0.7) == pytest.approx(495.0, abs=1e-9)


def test_last_f_null_gir_bare_loeft():
    assert hr.last_f(100, 80, 1000, 500, 0.0, 0.7) == pytest.approx(20.0)


def test_brukstid_en():
    # b = 1,0: R_new = 1000 − 100 = 900; L = 0 + 1·(1·900 + 1·500) = 1400
    assert hr.last_f(100, 100, 1000, 500, 1.0, 1.0) == pytest.approx(1400.0)


def test_headroom_og_hendelse():
    H = hr.headroom(-1200, -3000)  # eksport −1200 (import 1200), største import 3000 -> 1800 MW igjen
    assert H == 1800
    assert hr.hendelse(2000, H) is True
    assert hr.hendelse(1800, H) is False  # streng ulikhet
    assert hr.hendelse(1800, None) is None


def test_headroom_manglende():
    assert hr.headroom(None, -100) is None
    assert hr.headroom(5, None) is None


def test_sekundaer():
    assert hr.headroom_sekundaer(100, 5000, 4200) == 900
    assert hr.headroom_sekundaer(None, 5000, 4200) is None


def _t(h, m):
    return dt.datetime(2025, 6, 1, h, m, tzinfo=dt.timezone.utc)


def test_installert_regulerbar():
    assert hr.installert_regulerbar(1000, 500, pumpeledd=True) == 1500
    assert hr.installert_regulerbar(1000, None, pumpeledd=False) == 1000  # NO1/NO4: «n/e» -> 0
    assert hr.installert_regulerbar(1000, None, pumpeledd=True) is None
    assert hr.installert_regulerbar(None, 5, pumpeledd=True) is None


def test_pumpekategori():
    assert hr.pumpekategori(12.0, None) == hr.PRODUKSJON
    assert hr.pumpekategori(0.0, 50.0) == hr.PRODUKSJON  # produksjonsverdi finnes
    assert hr.pumpekategori(None, 50.0) == hr.PUMPEINTERVALL
    assert hr.pumpekategori(None, 0.0) == hr.DATAHULL  # ingen registrert pumping
    assert hr.pumpekategori(None, None) == hr.DATAHULL  # kilde uten forbruksfelt


def test_faktisk_regulerbar_mtu():
    # time-MTU med fire kvarter: magasin 400 hele timen; pumpe 100, pumpeintervall, 100, pumpeintervall
    # -> (500 + 400 + 500 + 400) / 4 = 450 (0 satt per kvarter før vektingen)
    iv = [(15, 400, 100, None), (15, 400, None, 80), (15, 400, 100, None), (15, 400, None, 30)]
    assert hr.faktisk_regulerbar_mtu(iv, 60, pumpeledd=True) == pytest.approx(450.0)
    # ett kvarter datahull for pumpekraft -> MTU manglende
    assert hr.faktisk_regulerbar_mtu(iv[:3] + [(15, 400, None, None)], 60, pumpeledd=True) is None
    # ett kvarter uten magasinverdi -> MTU manglende
    assert hr.faktisk_regulerbar_mtu(iv[:3] + [(15, None, 100, None)], 60, pumpeledd=True) is None
    # NO1/NO4: pumpeleddet 0, manglende pumpekraft er ikke datahull
    assert hr.faktisk_regulerbar_mtu([(60, 400, None, None)], 60, pumpeledd=False) == pytest.approx(400.0)
    # time-intervall (A75 før 2025-04-10) i time-MTU
    assert hr.faktisk_regulerbar_mtu([(60, 400, None, 10)], 60, pumpeledd=True) == pytest.approx(400.0)
    # dekker ikke MTU-en
    assert hr.faktisk_regulerbar_mtu(iv[:3], 60, pumpeledd=True) is None
    # sekundærmål: installert 1500 − faktisk 450 lagt til H = 100
    assert hr.headroom_sekundaer(100, 1500, hr.faktisk_regulerbar_mtu(iv, 60, True)) == pytest.approx(1150.0)


def test_hendelse_time():
    assert hr.hendelse_time([False, True, False, False], [15, 15, 15, 15]) is True
    assert hr.hendelse_time([False, False, False, False], [15, 15, 15, 15]) is False
    assert hr.hendelse_time([True, None, False, False], [15, 15, 15, 15]) is None  # manglende MTU -> manglende time
    assert hr.hendelse_time([True, False, False], [15, 15, 15]) is None  # dekker ikke hele timen
    assert hr.hendelse_time([True], [60]) is True


def test_utfall_kvarter_med_manglende():
    # time 1: H = 100, 50, 300, 200 (L = 80 -> én hendelse) -> time med hendelse
    # time 2: H = 100, None, 300, 200 -> manglende time; tre gyldige MTU uten hendelse
    H = [100, 50, 300, 200, 100, None, 300, 200]
    start = [_t(0, 0), _t(0, 15), _t(0, 30), _t(0, 45), _t(1, 0), _t(1, 15), _t(1, 30), _t(1, 45)]
    u = hr.utfall(H, start, [15] * 8, 80)
    assert (u.timer_med_hendelse, u.timer_gyldige, u.timer_manglende) == (1, 1, 1)
    assert u.andel_timer_med_hendelse == pytest.approx(1.0)
    assert u.andel_mtu_med_hendelse == pytest.approx(1 / 7)
    assert (u.mtu_gyldige, u.mtu_manglende) == (7, 1)


def test_utfall_time_mtu():
    # to time-MTU: én hendelse -> 1 av 2 timer; andel MTU 1/2
    u = hr.utfall([10, 500], [_t(0, 0), _t(1, 0)], [60, 60], 80)
    assert (u.timer_med_hendelse, u.timer_gyldige) == (1, 2)
    assert u.andel_mtu_med_hendelse == pytest.approx(0.5)


def test_utfall_lengdekrav():
    with pytest.raises(ValueError):
        hr.utfall([1, 2], [_t(0, 0)], [15], 0)


def test_nan_er_manglende():
    nan = float("nan")
    assert hr.headroom(nan, -100) is None
    assert hr.hendelse(80, nan) is None
    assert hr.pumpekategori(nan, 50.0) == hr.PUMPEINTERVALL
    assert hr.pumpekategori(nan, nan) == hr.DATAHULL
    assert hr.faktisk_regulerbar_mtu([(60, nan, 10.0, None)], 60, pumpeledd=True) is None
    assert hr.installert_regulerbar(1000, nan, pumpeledd=True) is None
    u = hr.utfall([nan, 500], [_t(0, 0), _t(1, 0)], [60, 60], 80)
    assert (u.mtu_gyldige, u.mtu_manglende, u.timer_manglende) == (1, 1, 1)
