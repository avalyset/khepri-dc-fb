"""Tester av kontrollstrenger og manifest på syntetiske svar (ingen nett)."""
from khepri_dc_fb import hent


def test_kontroll_jao():
    assert hent.kontroll_jao([{"dateTimeUtc": "x", "hub_NO1": 1}], "hub_") == (True, "")
    assert hent.kontroll_jao([], "hub_")[0] is False
    assert hent.kontroll_jao([{"hub_NO1": 1}], "hub_")[0] is False
    assert hent.kontroll_jao([{"dateTimeUtc": "x", "min_NO1": 1}], "hub_")[0] is False


def test_kontroll_entsoe():
    assert hent.kontroll_entsoe(b"<GL_MarketDocument><TimeSeries/></GL_MarketDocument>") == ("OK", "")
    ack = b"<Acknowledgement_MarketDocument><Reason><code>999</code><text>No matching data found</text></Reason></Acknowledgement_MarketDocument>"
    assert hent.kontroll_entsoe(ack) == ("INGEN_DATA", "999")
    assert hent.kontroll_entsoe(b"<html>feil</html>")[0] == "FEILET"


def test_saner():
    assert hent.saner("https://x/api?securityToken=abc-123&a=1") == "https://x/api?securityToken=***&a=1"


def test_lagre_jao_skriver_manifest(tmp_path):
    m = tmp_path / "manifest.csv"
    r = hent.lagre_jao(tmp_path, m, "netPos", "2026-10-26", [{"dateTimeUtc": "t", "hub_NO1": 5}])
    assert r["status"] == "OK" and r["kontrollstreng_funnet"] == "ja" and len(r["sha256"]) == 64
    r2 = hent.lagre_jao(tmp_path, m, "netPos", "2024-10-30", None, "NoMatchingDataError")
    assert r2["status"] == "INGEN_DATA" and r2["aarsak"] == "NoMatchingDataError"
    assert len(m.read_text().strip().splitlines()) == 3  # header + 2 rader


def test_ventetid_429():
    assert hent.ventetid_429({"Retry-After": "7"}) == 7.0
    assert hent.ventetid_429({"retry-after": "x"}) == hent.VENT_VED_429_S
    assert hent.ventetid_429({}) == hent.VENT_VED_429_S


def test_tempo_holder_pause():
    t = [100.0]
    sovet = []

    def sov(s):
        sovet.append(s)
        t[0] += s

    tp = hent.Tempo(2.0, klokke=lambda: t[0], sov=sov)
    assert tp.vent() == 0.0          # første kall: ingen pause
    t[0] += 0.5
    assert tp.vent() == 1.5          # 0,5 s gått -> vent 1,5 s
    t[0] += 3.0
    assert tp.vent() == 0.0          # mer enn pausen har gått
    assert sovet == [1.5]
