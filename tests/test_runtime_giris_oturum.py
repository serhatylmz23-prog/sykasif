import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from syk_simulasyon.runtime_anlik_gorunum import (
    RuntimeAnlikGorunumSaglayicisi,
)
from syk_simulasyon.runtime_csv import RuntimeCsvSaglayicisi
from syk_simulasyon.runtime_disa_aktarim import RuntimeDisaAktarim
from syk_simulasyon.runtime_fastapi_sunucusu import (
    RuntimeFastApiSunucusu,
)
from syk_simulasyon.runtime_html import RuntimeHtmlSaglayicisi
from syk_simulasyon.runtime_izleme import RuntimeIzlemeSaglayicisi
from syk_simulasyon.runtime_json import RuntimeJsonSaglayicisi
from syk_simulasyon.runtime_markdown import (
    RuntimeMarkdownSaglayicisi,
)
from syk_simulasyon.runtime_oturum import (
    OTURUM_CEREZI_ADI,
    RuntimeOturumYoneticisi,
    parola_dogrula,
    parola_ozeti_uret,
)
from syk_simulasyon.runtime_servisi import RuntimeServisi
from syk_simulasyon.runtime_websocket import (
    RuntimeWebSocketYayincisi,
)
from syk_simulasyon.runtime_xml import RuntimeXmlSaglayicisi
from syk_simulasyon.runtime_yaml import RuntimeYamlSaglayicisi


KULLANICI = "kurucu"
PAROLA = "yalnizca-test-parolasi"
ANAHTAR = b"0123456789abcdef0123456789abcdef"


def _istemci() -> TestClient:
    servis = RuntimeServisi()

    gorunum = RuntimeAnlikGorunumSaglayicisi(
        RuntimeIzlemeSaglayicisi(servis)
    )

    disa_aktarim = RuntimeDisaAktarim(
        RuntimeJsonSaglayicisi(gorunum),
        RuntimeCsvSaglayicisi(gorunum),
        RuntimeHtmlSaglayicisi(gorunum),
        RuntimeMarkdownSaglayicisi(gorunum),
        RuntimeXmlSaglayicisi(gorunum),
        RuntimeYamlSaglayicisi(gorunum),
    )

    websocket_yayinci = RuntimeWebSocketYayincisi(
        gorunum,
        servis.durum.sistem_hazirlik_ozeti,
    )

    yonetici = RuntimeOturumYoneticisi(
        kullanici_adi=KULLANICI,
        parola_ozeti=parola_ozeti_uret(
            PAROLA,
            tur_sayisi=100_000,
            tuz=b"0123456789abcdef",
        ),
        oturum_anahtari=ANAHTAR,
        oturum_suresi_saniye=600,
    )

    uygulama = RuntimeFastApiSunucusu(
        disa_aktarim,
        websocket_yayinci,
        servis.durum,
        runtime_servisi=servis,
        oturum_yoneticisi=yonetici,
    ).olustur()

    return TestClient(
        uygulama,
        follow_redirects=False,
    )


def test_parola_ozeti_duz_metni_saklamaz():
    ozet = parola_ozeti_uret(
        PAROLA,
        tur_sayisi=100_000,
        tuz=b"0123456789abcdef",
    )

    assert PAROLA not in ozet
    assert parola_dogrula(PAROLA, ozet)
    assert not parola_dogrula("yanlis-parola", ozet)


def test_giris_ekrani_acilir():
    yanit = _istemci().get("/giris")

    assert yanit.status_code == 200
    assert "SyKa\u015fif" in yanit.text
    assert 'type="password"' in yanit.text


def test_oturumsuz_terminal_girise_yonlendirilir():
    yanit = _istemci().get("/terminal")

    assert yanit.status_code == 303
    assert yanit.headers["location"] == "/giris"


def test_yanlis_kimlik_bilgisi_reddedilir():
    yanit = _istemci().post(
        "/runtime/oturum",
        json={
            "kullanici_adi": KULLANICI,
            "parola": "yanlis",
        },
    )

    assert yanit.status_code == 401
    assert OTURUM_CEREZI_ADI not in yanit.cookies


def test_dogru_giris_terminali_acar():
    istemci = _istemci()

    giris = istemci.post(
        "/runtime/oturum",
        json={
            "kullanici_adi": KULLANICI,
            "parola": PAROLA,
        },
    )

    assert giris.status_code == 200
    assert OTURUM_CEREZI_ADI in giris.cookies

    terminal = istemci.get("/terminal")

    assert terminal.status_code == 200
    assert "<title>" in terminal.text
    assert "SyOta" in terminal.text
    assert "</title>" in terminal.text


def test_cikis_oturumu_kapatir():
    istemci = _istemci()

    istemci.post(
        "/runtime/oturum",
        json={
            "kullanici_adi": KULLANICI,
            "parola": PAROLA,
        },
    )

    cikis = istemci.post("/cikis")

    assert cikis.status_code == 200

    terminal = istemci.get("/terminal")

    assert terminal.status_code == 303
    assert terminal.headers["location"] == "/giris"


def test_oturumsuz_websocket_reddedilir():
    istemci = _istemci()

    with pytest.raises(WebSocketDisconnect) as hata:
        with istemci.websocket_connect("/ws/runtime"):
            pass

    assert hata.value.code == 4401


def test_oturumlu_websocket_baglanir():
    istemci = _istemci()

    istemci.post(
        "/runtime/oturum",
        json={
            "kullanici_adi": KULLANICI,
            "parola": PAROLA,
        },
    )

    with istemci.websocket_connect(
        "/ws/runtime"
    ) as websocket:
        mesaj = websocket.receive_json()

    assert isinstance(mesaj, dict)
    assert "sistem_hazirlik" in mesaj


def test_oturum_farkli_hesap_kimligi_ve_rol_tasir():
    yonetici = RuntimeOturumYoneticisi(
        kullanici_adi=KULLANICI,
        parola_ozeti=parola_ozeti_uret(
            PAROLA,
            tur_sayisi=100_000,
            tuz=b"0123456789abcdef",
        ),
        oturum_anahtari=ANAHTAR,
        oturum_suresi_saniye=600,
    )

    belirtec = yonetici.oturum_uret(
        kullanici_adi="ikinci-kullanici",
        hesap_kimligi=42,
        rol="normal_kullanici",
        simdi=1_000,
    )

    bilgi = yonetici.oturum_bilgisi(
        belirtec,
        simdi=1_001,
    )

    assert bilgi is not None
    assert bilgi["kullanici"] == "ikinci-kullanici"
    assert bilgi["hesap_kimligi"] == 42
    assert bilgi["rol"] == "normal_kullanici"


def test_suresi_dolan_oturum_reddedilir():
    yonetici = RuntimeOturumYoneticisi(
        kullanici_adi=KULLANICI,
        parola_ozeti=parola_ozeti_uret(
            PAROLA,
            tur_sayisi=100_000,
            tuz=b"0123456789abcdef",
        ),
        oturum_anahtari=ANAHTAR,
        oturum_suresi_saniye=600,
    )

    belirtec = yonetici.oturum_uret(
        simdi=1_000,
    )

    assert not yonetici.oturum_dogrula(
        belirtec,
        simdi=1_601,
    )


def test_degistirilen_oturum_belirteci_reddedilir():
    yonetici = RuntimeOturumYoneticisi(
        kullanici_adi=KULLANICI,
        parola_ozeti=parola_ozeti_uret(
            PAROLA,
            tur_sayisi=100_000,
            tuz=b"0123456789abcdef",
        ),
        oturum_anahtari=ANAHTAR,
        oturum_suresi_saniye=600,
    )

    belirtec = yonetici.oturum_uret(
        simdi=1_000,
    )

    son_karakter = (
        "A"
        if belirtec[-1] != "A"
        else "B"
    )

    bozuk = (
        belirtec[:-1]
        + son_karakter
    )

    assert not yonetici.oturum_dogrula(
        bozuk,
        simdi=1_001,
    )
