from pathlib import Path

from fastapi.testclient import TestClient

from syk_simulasyon.runtime_anlik_gorunum import (
    RuntimeAnlikGorunumSaglayicisi,
)
from syk_simulasyon.runtime_csv import RuntimeCsvSaglayicisi
from syk_simulasyon.runtime_disa_aktarim import RuntimeDisaAktarim
from syk_simulasyon.runtime_fastapi_sunucusu import (
    CIHAZ_ANAHTARI_CEREZI_ADI,
    CIHAZ_KIMLIGI_CEREZI_ADI,
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
        if not veri.startswith(self.ON_EK):
            raise ValueError("Gecersiz veri.")

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

    hesap = depo.hesap_olustur(
        kullanici_adi="kurucu",
        parola=PAROLA,
        tur_sayisi=100_000,
    )

    istemci = TestClient(
        uygulama,
        follow_redirects=False,
    )

    return istemci, depo, hesap


def _beni_taniyarak_giris_yap(
    istemci: TestClient,
):
    return istemci.post(
        "/runtime/oturum",
        json={
            "kullanici_adi": "kurucu",
            "parola": PAROLA,
            "beni_tani": True,
        },
    )


def test_giris_ekrani_beni_tani_secenegi_gosterir(
    tmp_path,
):
    istemci, _depo, _hesap = _istemci(tmp_path)

    yanit = istemci.get("/giris")

    assert yanit.status_code == 200
    assert 'id="beni_tani"' in yanit.text


def test_beni_tani_cihaz_cerezlerini_ve_tercihi_olusturur(
    tmp_path,
):
    istemci, depo, hesap = _istemci(tmp_path)

    yanit = _beni_taniyarak_giris_yap(
        istemci
    )

    assert yanit.status_code == 200
    assert CIHAZ_KIMLIGI_CEREZI_ADI in yanit.cookies
    assert CIHAZ_ANAHTARI_CEREZI_ADI in yanit.cookies

    guncel = depo.hesap_getir(
        hesap.hesap_kimligi
    )

    assert guncel is not None
    assert guncel.hizli_giris_etkin


def test_taninmis_cihaz_otomatik_oturum_acar(
    tmp_path,
):
    istemci, _depo, _hesap = _istemci(tmp_path)

    _beni_taniyarak_giris_yap(
        istemci
    )

    istemci.cookies.delete(
        OTURUM_CEREZI_ADI
    )

    yanit = istemci.get("/giris")

    assert yanit.status_code == 303
    assert yanit.headers["location"] == "/terminal"
    assert OTURUM_CEREZI_ADI in yanit.cookies


def test_bozuk_cihaz_anahtari_otomatik_girisi_reddeder(
    tmp_path,
):
    istemci, _depo, _hesap = _istemci(tmp_path)

    _beni_taniyarak_giris_yap(
        istemci
    )

    istemci.cookies.delete(
        OTURUM_CEREZI_ADI
    )

    istemci.cookies.set(
        CIHAZ_ANAHTARI_CEREZI_ADI,
        "gecersiz-cihaz-anahtari",
    )

    yanit = istemci.get("/giris")

    assert yanit.status_code == 200
    assert "/runtime/oturum" in yanit.text


def test_hizli_giris_kapatilinca_otomatik_giris_durur(
    tmp_path,
):
    istemci, depo, hesap = _istemci(tmp_path)

    _beni_taniyarak_giris_yap(
        istemci
    )

    istemci.cookies.delete(
        OTURUM_CEREZI_ADI
    )

    depo.hizli_giris_ayarla(
        hesap.hesap_kimligi,
        False,
    )

    yanit = istemci.get("/giris")

    assert yanit.status_code == 200


def test_cihaz_iptali_cerezleri_siler_ve_hizli_girisi_keser(
    tmp_path,
):
    istemci, _depo, _hesap = _istemci(tmp_path)

    _beni_taniyarak_giris_yap(
        istemci
    )

    cihaz_kimligi = istemci.cookies.get(
        CIHAZ_KIMLIGI_CEREZI_ADI
    )
    cihaz_anahtari = istemci.cookies.get(
        CIHAZ_ANAHTARI_CEREZI_ADI
    )

    yanit = istemci.post(
        "/runtime/cihaz-iptal"
    )

    assert yanit.status_code == 200

    istemci.cookies.set(
        CIHAZ_KIMLIGI_CEREZI_ADI,
        cihaz_kimligi,
    )
    istemci.cookies.set(
        CIHAZ_ANAHTARI_CEREZI_ADI,
        cihaz_anahtari,
    )
    istemci.cookies.delete(
        OTURUM_CEREZI_ADI
    )

    giris = istemci.get("/giris")

    assert giris.status_code == 200


def test_sunucu_yeniden_baslayinca_taninmis_cihaz_yeni_oturum_alir(
    tmp_path,
):
    veritabani_yolu = (
        tmp_path
        / "guvenlik"
        / "hesaplar.db"
    )

    servis_bir = RuntimeServisi()

    gorunum_bir = RuntimeAnlikGorunumSaglayicisi(
        RuntimeIzlemeSaglayicisi(
            servis_bir
        )
    )

    disa_aktarim_bir = RuntimeDisaAktarim(
        RuntimeJsonSaglayicisi(
            gorunum_bir
        ),
        RuntimeCsvSaglayicisi(
            gorunum_bir
        ),
        RuntimeHtmlSaglayicisi(
            gorunum_bir
        ),
        RuntimeMarkdownSaglayicisi(
            gorunum_bir
        ),
        RuntimeXmlSaglayicisi(
            gorunum_bir
        ),
        RuntimeYamlSaglayicisi(
            gorunum_bir
        ),
    )

    websocket_bir = RuntimeWebSocketYayincisi(
        gorunum_bir,
        servis_bir.durum.sistem_hazirlik_ozeti,
    )

    depo_bir = RuntimeHesapDeposu(
        veritabani_yolu,
        koruyucu=TestKoruyucusu(),
    )

    yonetici_bir = RuntimeOturumYoneticisi(
        kullanici_adi="__hesap_deposu__",
        parola_ozeti=parola_ozeti_uret(
            "yalnizca-test-bir",
            tur_sayisi=100_000,
            tuz=b"0123456789abcdef",
        ),
        oturum_anahtari=(
            b"11111111111111111111111111111111"
        ),
        oturum_suresi_saniye=600,
    )

    uygulama_bir = RuntimeFastApiSunucusu(
        disa_aktarim_bir,
        websocket_bir,
        servis_bir.durum,
        runtime_servisi=servis_bir,
        oturum_yoneticisi=yonetici_bir,
        hesap_deposu=depo_bir,
    ).olustur()

    depo_bir.hesap_olustur(
        kullanici_adi="kurucu",
        parola=PAROLA,
        tur_sayisi=100_000,
    )

    istemci_bir = TestClient(
        uygulama_bir,
        follow_redirects=False,
    )

    giris = istemci_bir.post(
        "/runtime/oturum",
        json={
            "kullanici_adi": "kurucu",
            "parola": PAROLA,
            "beni_tani": True,
        },
    )

    assert giris.status_code == 200

    eski_oturum = istemci_bir.cookies.get(
        OTURUM_CEREZI_ADI
    )
    cihaz_kimligi = istemci_bir.cookies.get(
        CIHAZ_KIMLIGI_CEREZI_ADI
    )
    cihaz_anahtari = istemci_bir.cookies.get(
        CIHAZ_ANAHTARI_CEREZI_ADI
    )

    assert eski_oturum
    assert cihaz_kimligi
    assert cihaz_anahtari

    servis_iki = RuntimeServisi()

    gorunum_iki = RuntimeAnlikGorunumSaglayicisi(
        RuntimeIzlemeSaglayicisi(
            servis_iki
        )
    )

    disa_aktarim_iki = RuntimeDisaAktarim(
        RuntimeJsonSaglayicisi(
            gorunum_iki
        ),
        RuntimeCsvSaglayicisi(
            gorunum_iki
        ),
        RuntimeHtmlSaglayicisi(
            gorunum_iki
        ),
        RuntimeMarkdownSaglayicisi(
            gorunum_iki
        ),
        RuntimeXmlSaglayicisi(
            gorunum_iki
        ),
        RuntimeYamlSaglayicisi(
            gorunum_iki
        ),
    )

    websocket_iki = RuntimeWebSocketYayincisi(
        gorunum_iki,
        servis_iki.durum.sistem_hazirlik_ozeti,
    )

    depo_iki = RuntimeHesapDeposu(
        veritabani_yolu,
        koruyucu=TestKoruyucusu(),
    )

    yonetici_iki = RuntimeOturumYoneticisi(
        kullanici_adi="__hesap_deposu__",
        parola_ozeti=parola_ozeti_uret(
            "yalnizca-test-iki",
            tur_sayisi=100_000,
            tuz=b"fedcba9876543210",
        ),
        oturum_anahtari=(
            b"22222222222222222222222222222222"
        ),
        oturum_suresi_saniye=600,
    )

    uygulama_iki = RuntimeFastApiSunucusu(
        disa_aktarim_iki,
        websocket_iki,
        servis_iki.durum,
        runtime_servisi=servis_iki,
        oturum_yoneticisi=yonetici_iki,
        hesap_deposu=depo_iki,
    ).olustur()

    assert not yonetici_iki.oturum_dogrula(
        eski_oturum
    )

    istemci_iki = TestClient(
        uygulama_iki,
        follow_redirects=False,
    )

    istemci_iki.cookies.set(
        CIHAZ_KIMLIGI_CEREZI_ADI,
        cihaz_kimligi,
    )
    istemci_iki.cookies.set(
        CIHAZ_ANAHTARI_CEREZI_ADI,
        cihaz_anahtari,
    )

    yanit = istemci_iki.get(
        "/giris"
    )

    assert yanit.status_code == 303
    assert yanit.headers["location"] == "/terminal"

    yeni_oturum = yanit.cookies.get(
        OTURUM_CEREZI_ADI
    )

    assert yeni_oturum
    assert yeni_oturum != eski_oturum
    assert yonetici_iki.oturum_dogrula(
        yeni_oturum
    )
