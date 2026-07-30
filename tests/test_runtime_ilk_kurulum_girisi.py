from pathlib import Path

from fastapi.testclient import TestClient

from syk_simulasyon.runtime_anlik_gorunum import (
    RuntimeAnlikGorunumSaglayicisi,
)
from syk_simulasyon.runtime_csv import RuntimeCsvSaglayicisi
from syk_simulasyon.runtime_disa_aktarim import RuntimeDisaAktarim
from syk_simulasyon.runtime_fastapi_sunucusu import (
    RuntimeFastApiSunucusu,
)
from syk_simulasyon.runtime_hesap_deposu import (
    RuntimeHesapDeposu,
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
    parola_ozeti_uret,
)
from syk_simulasyon.runtime_servisi import RuntimeServisi
from syk_simulasyon.runtime_websocket import (
    RuntimeWebSocketYayincisi,
)
from syk_simulasyon.runtime_xml import RuntimeXmlSaglayicisi
from syk_simulasyon.runtime_yaml import RuntimeYamlSaglayicisi


PAROLA = "1234"


class TestKoruyucusu:
    ON_EK = b"TEST:"

    def koru(self, veri: bytes) -> bytes:
        return self.ON_EK + veri[::-1]

    def ac(self, veri: bytes) -> bytes:
        return veri[len(self.ON_EK):][::-1]


def _istemci(tmp_path: Path):
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

    websocket = RuntimeWebSocketYayincisi(
        gorunum,
        servis.durum.sistem_hazirlik_ozeti,
    )

    depo = RuntimeHesapDeposu(
        tmp_path / "guvenlik" / "hesaplar.db",
        koruyucu=TestKoruyucusu(),
    )

    yonetici = RuntimeOturumYoneticisi(
        kullanici_adi="__hesap_deposu__",
        parola_ozeti=parola_ozeti_uret(
            "yalnizca-test",
            tur_sayisi=100_000,
            tuz=b"0123456789abcdef",
        ),
        oturum_anahtari=(
            b"0123456789abcdef0123456789abcdef"
        ),
        oturum_suresi_saniye=600,
    )

    uygulama = RuntimeFastApiSunucusu(
        disa_aktarim,
        websocket,
        servis.durum,
        runtime_servisi=servis,
        oturum_yoneticisi=yonetici,
        hesap_deposu=depo,
    ).olustur()

    return (
        TestClient(
            uygulama,
            follow_redirects=False,
        ),
        depo,
        yonetici,
    )


def test_depo_bosken_ilk_kurulum_ekrani_gosterilir(
    tmp_path,
):
    istemci, _depo, _yonetici = _istemci(tmp_path)

    yanit = istemci.get("/giris")

    assert yanit.status_code == 200
    assert "ilk-kurulum" in yanit.text
    assert "parola_tekrar" in yanit.text


def test_ilk_kurulum_kurucu_hesabi_ve_oturum_olusturur(
    tmp_path,
):
    istemci, depo, yonetici = _istemci(tmp_path)

    yanit = istemci.post(
        "/runtime/ilk-kurulum",
        json={
            "kullanici_adi": "kurucu",
            "eposta": "kurucu@example.test",
            "telefon": "+905551112233",
            "parola": PAROLA,
            "parola_tekrar": PAROLA,
        },
    )

    assert yanit.status_code == 201
    assert depo.hesap_var_mi()
    assert OTURUM_CEREZI_ADI in yanit.cookies

    bilgi = yonetici.oturum_bilgisi(
        yanit.cookies[OTURUM_CEREZI_ADI]
    )

    assert bilgi is not None
    assert bilgi["kullanici"] == "kurucu"
    assert bilgi["hesap_kimligi"] == 1
    assert bilgi["rol"] == "kurucu"


def test_ikinci_ilk_kurulum_reddedilir(tmp_path):
    istemci, depo, _yonetici = _istemci(tmp_path)

    depo.hesap_olustur(
        kullanici_adi="kurucu",
        parola=PAROLA,
        tur_sayisi=100_000,
    )

    yanit = istemci.post(
        "/runtime/ilk-kurulum",
        json={
            "kullanici_adi": "ikinci",
            "parola": PAROLA,
            "parola_tekrar": PAROLA,
        },
    )

    assert yanit.status_code == 409


def test_hesap_varken_normal_giris_ekrani_gosterilir(
    tmp_path,
):
    istemci, depo, _yonetici = _istemci(tmp_path)

    depo.hesap_olustur(
        kullanici_adi="kurucu",
        parola=PAROLA,
        tur_sayisi=100_000,
    )

    yanit = istemci.get("/giris")

    assert yanit.status_code == 200
    assert "/runtime/oturum" in yanit.text
    assert "parola_tekrar" not in yanit.text


def test_eposta_ile_giris_yapilir(tmp_path):
    istemci, depo, yonetici = _istemci(tmp_path)

    hesap = depo.hesap_olustur(
        kullanici_adi="kurucu",
        eposta="kurucu@example.test",
        parola=PAROLA,
        tur_sayisi=100_000,
    )

    yanit = istemci.post(
        "/runtime/oturum",
        json={
            "kullanici_adi": "kurucu@example.test",
            "parola": PAROLA,
        },
    )

    assert yanit.status_code == 200

    bilgi = yonetici.oturum_bilgisi(
        yanit.cookies[OTURUM_CEREZI_ADI]
    )

    assert bilgi is not None
    assert bilgi["hesap_kimligi"] == hesap.hesap_kimligi


def test_yanlis_parola_reddedilir(tmp_path):
    istemci, depo, _yonetici = _istemci(tmp_path)

    depo.hesap_olustur(
        kullanici_adi="kurucu",
        parola=PAROLA,
        tur_sayisi=100_000,
    )

    yanit = istemci.post(
        "/runtime/oturum",
        json={
            "kullanici_adi": "kurucu",
            "parola": "yanlis",
        },
    )

    assert yanit.status_code == 401


def test_depo_bosken_normal_giris_reddedilir(tmp_path):
    istemci, _depo, _yonetici = _istemci(tmp_path)

    yanit = istemci.post(
        "/runtime/oturum",
        json={
            "kullanici_adi": "kurucu",
            "parola": PAROLA,
        },
    )

    assert yanit.status_code == 409
