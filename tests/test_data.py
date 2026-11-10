"""Tester av khepri_dc_fb.data på håndregnede, syntetiske tall (ingen rådata, ingen nett)."""
import datetime as dt

from khepri_dc_fb import data as D

U = dt.timezone.utc


def t(s):
    return dt.datetime.fromisoformat(s).replace(tzinfo=U)


def test_doegnstart_normal_og_sommertid():
    assert D.doegnstart(dt.date(2024, 10, 30)) == t("2024-10-29T23:00")
    assert D.doegnstart(dt.date(2026, 4, 2)) == t("2026-04-01T22:00")  # håndbokas eksempel [GT-393]


def test_jao_doegn_lengder():
    # døgn 2024-10-30 slutter 2024-10-30T23:00Z; tre rader: 23:00Z, 00:00Z og 22:00Z
    rader = [{"dateTimeUtc": "2024-10-30T00:00:00Z"}, {"dateTimeUtc": "2024-10-29T23:00:00Z"},
             {"dateTimeUtc": "2024-10-30T22:00:00Z"}]
    m = D.jao_doegn(rader, dt.date(2024, 10, 30))
    assert [(x[0], x[1]) for x in m] == [(t("2024-10-29T23:00"), 60), (t("2024-10-30T00:00"), 22 * 60),
                                         (t("2024-10-30T22:00"), 60)]


def test_mtu_skifte_foerste_doegn_med_bare_15():
    d1, d2, d3 = dt.date(2025, 1, 1), dt.date(2025, 1, 2), dt.date(2025, 1, 3)
    doegn = {d1: [(None, 60, {})], d2: [(None, 15, {}), (None, 60, {})], d3: [(None, 15, {}), (None, 15, {})]}
    assert D.mtu_skifte(doegn) == d3


def test_rutenett_rundt_skillet():
    nett = D.rutenett(t("2025-01-01T00:00"), t("2024-12-31T22:00"), t("2025-01-01T00:30"))
    assert nett == [(t("2024-12-31T22:00"), 60), (t("2024-12-31T23:00"), 60), (t("2025-01-01T00:00"), 15),
                    (t("2025-01-01T00:15"), 15)]


def test_paa_rutenett_varighetsvekting_og_mangler():
    v = {t("2025-01-01T00:00"): (15, 1.0), t("2025-01-01T00:15"): (15, 2.0), t("2025-01-01T00:30"): (15, 3.0),
         t("2025-01-01T00:45"): (15, 4.0), t("2025-01-01T01:00"): (60, 7.0), t("2025-01-01T02:00"): (15, 1.0)}
    nett = [(t("2025-01-01T00:00"), 60), (t("2025-01-01T01:00"), 60), (t("2025-01-01T02:00"), 60)]
    assert D.paa_rutenett(v, nett) == [2.5, 7.0, None]  # (1+2+3+4)/4; samme MTU; bare ett av fire kvarter


XML = b"""<GL_MarketDocument><TimeSeries><curveType>A03</curveType><MktPSRType><psrType>B10</psrType></MktPSRType>
<inBiddingZone_Domain.mRID>10YNO-2--------T</inBiddingZone_Domain.mRID>
<Period><timeInterval><start>2025-05-01T00:00Z</start><end>2025-05-01T01:00Z</end></timeInterval><resolution>PT15M</resolution>
<Point><position>1</position><quantity>10</quantity></Point><Point><position>3</position><quantity>30</quantity></Point>
</Period></TimeSeries>
<TimeSeries><curveType>A01</curveType><MktPSRType><psrType>B12</psrType></MktPSRType>
<Period><timeInterval><start>2025-05-01T00:00Z</start><end>2025-05-01T01:00Z</end></timeInterval><resolution>PT15M</resolution>
<Point><position>1</position><quantity>10</quantity></Point><Point><position>3</position><quantity>30</quantity></Point>
</Period></TimeSeries></GL_MarketDocument>"""


def test_xml_a03_holder_forrige_verdi_a01_bare_posisjoner():
    s = D.xml_serier(XML)
    assert s[0]["psr"] == "B10" and s[0]["inn_bz"] == "10YNO-2--------T"
    assert [(x[0].strftime("%H:%M"), x[1], x[2]) for x in s[0]["intervaller"]] == [
        ("00:00", 15, 10.0), ("00:15", 15, 10.0), ("00:30", 15, 30.0), ("00:45", 15, 30.0)]
    assert [(x[0].strftime("%H:%M"), x[2]) for x in s[1]["intervaller"]] == [("00:00", 10.0), ("00:30", 30.0)]


def test_csv_flatet_header_og_lengder(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text(",Hydro Pumped Storage|Actual Aggregated,Hydro Pumped Storage|Actual Consumption\n"
                 "2025-10-01 02:00:00+02:00,,9.39\n2025-10-01 02:15:00+02:00,0.0,\n"
                 "2025-10-01 02:30:00+02:00,nan,1\n", encoding="utf-8")
    kol, rader = D.csv_tabell(p)
    assert kol == [("Hydro Pumped Storage", "Actual Aggregated"), ("Hydro Pumped Storage", "Actual Consumption")]
    assert [(r[0], r[1]) for r in rader] == [(t("2025-10-01T00:00"), 15), (t("2025-10-01T00:15"), 15),
                                             (t("2025-10-01T00:30"), 15)]
    assert [D.celleverdi(r[2][0]) for r in rader] == [None, 0.0, None]  # null er en verdi, nan og tom er ikke


def test_csv_to_headerlinjer_og_timer(tmp_path):
    p = tmp_path / "b.csv"
    p.write_text(",Hydro Water Reservoir,Hydro Pumped Storage\n,Actual Aggregated,Actual Consumption\n"
                 "2025-01-01 01:00:00+01:00,5,6\n2025-01-01 02:00:00+01:00,7,8\n", encoding="utf-8")
    kol, rader = D.csv_tabell(p)
    assert kol == [("Hydro Water Reservoir", "Actual Aggregated"), ("Hydro Pumped Storage", "Actual Consumption")]
    assert [r[1] for r in rader] == [60, 60]


def test_csv_en_headerlinje_uten_under_er_aggregated(tmp_path):
    p = tmp_path / "c.csv"
    p.write_text(",Hydro Water Reservoir\n2026-01-01 01:00:00+01:00,1.5\n2026-01-01 01:15:00+01:00,2\n", encoding="utf-8")
    kol, _ = D.csv_tabell(p)
    assert kol == [("Hydro Water Reservoir", "Actual Aggregated")]


def test_til_kvarter_og_prioritet():
    k = D.til_kvarter([(t("2025-01-01T00:00"), 60, 4.0)], t("2025-01-01T00:00"), t("2025-01-01T00:30"))
    assert k == {t("2025-01-01T00:00"): 4.0, t("2025-01-01T00:15"): 4.0}
    q1, q2, q3 = t("2025-01-01T00:00"), t("2025-01-01T00:15"), t("2025-01-01T00:30")
    s = D.slaa_sammen({"K": {q1: 1.0, q2: None}, "X": {q1: 2.0, q2: 3.0}, "R": {q2: 9.0, q3: 5.0}})
    assert s == {q1: (1.0, "K"), q2: (3.0, "X"), q3: (5.0, "R")}


def test_fbdsp_rader_til_hub_felt():
    rows = [{"dateTimeUtc": "2025-01-01T00:00:00Z", "cnecName": "NetPosition_NO1", "flowFb": 10.5},
            {"dateTimeUtc": "2025-01-01T00:00:00Z", "cnecName": "NetPosition_NO2", "flowFb": -3.0},
            {"dateTimeUtc": "2025-01-01T01:00:00Z", "cnecName": "NetPosition_NO1", "flowFb": None},
            {"dateTimeUtc": "2025-01-01T00:00:00Z", "cnecName": "Border_NO1-NO2", "flowFb": 99.0}]
    r = {x["dateTimeUtc"]: x for x in D.fbdsp_rader(rows)}
    assert r["2025-01-01T00:00:00Z"] == {"dateTimeUtc": "2025-01-01T00:00:00Z", "hub_NO1": 10.5, "hub_NO2": -3.0}
    assert r["2025-01-01T01:00:00Z"]["hub_NO1"] is None


def test_fbdsp_ulike_dubletter_gir_feil():
    import pytest
    rows = [{"dateTimeUtc": "t", "cnecName": "NetPosition_NO1", "flowFb": 1.0},
            {"dateTimeUtc": "t", "cnecName": "NetPosition_NO1", "flowFb": 2.0}]
    with pytest.raises(ValueError):
        D.fbdsp_rader(rows)


def test_les_fbdsp_og_lengder(tmp_path):
    import gzip as gz
    import json as js
    rows = [{"dateTimeUtc": "2024-10-29T23:00:00Z", "cnecName": "NetPosition_NO1", "flowFb": 1.0},
            {"dateTimeUtc": "2024-10-30T00:00:00Z", "cnecName": "NetPosition_NO1", "flowFb": 2.0}]
    (tmp_path / "jao_fbDomainShadowPrice_2024-10-30.json.gz").write_bytes(gz.compress(js.dumps(rows).encode()))
    d = D.les_fbdsp(tmp_path)[dt.date(2024, 10, 30)]
    assert [(x[0], x[1], x[2]["hub_NO1"]) for x in d] == [(t("2024-10-29T23:00"), 60, 1.0), (t("2024-10-30T00:00"), 23 * 60, 2.0)]


def test_aar_i_navn_aars_og_maanedsfiler():
    from pathlib import Path
    assert D.aar_i_navn(Path("A11_NO_1__NO_2_2024-10.xml")) == "2024"
    assert D.aar_i_navn(Path("A11_NO_4__SE_1_2025.xml")) == "2025"
    assert D.aar_i_navn(Path("A75_NO_2_2023.xml")) == "2023"
