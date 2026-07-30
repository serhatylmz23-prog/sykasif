from fastapi.testclient import TestClient

from syk_simulasyon.runtime_anlik_gorunum import (
    RuntimeAnlikGorunumSaglayicisi,
)
from syk_simulasyon.runtime_csv import RuntimeCsvSaglayicisi
from syk_simulasyon.runtime_disa_aktarim import RuntimeDisaAktarim
from syk_simulasyon.runtime_durumu import RuntimeDurumTuru
from syk_simulasyon.runtime_fastapi_sunucusu import (
    RuntimeFastApiSunucusu,
)
from syk_simulasyon.runtime_html import RuntimeHtmlSaglayicisi
from syk_simulasyon.runtime_izleme import RuntimeIzlemeSaglayicisi
from syk_simulasyon.runtime_json import RuntimeJsonSaglayicisi
from syk_simulasyon.runtime_markdown import (
    RuntimeMarkdownSaglayicisi,
)
from syk_simulasyon.runtime_servisi import RuntimeServisi
from syk_simulasyon.runtime_websocket import (
    RuntimeWebSocketYayincisi,
)
from syk_simulasyon.runtime_xml import RuntimeXmlSaglayicisi
from syk_simulasyon.runtime_yaml import RuntimeYamlSaglayicisi


def _istemci_ve_servis() -> tuple[TestClient, RuntimeServisi]:
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

    uygulama = RuntimeFastApiSunucusu(
        disa_aktarim,
        websocket_yayinci,
        servis.durum,
    ).olustur()

    return TestClient(uygulama), servis


def test_terminal_servisin_canli_durumunu_gosterir():
    istemci, servis = _istemci_ve_servis()

    servis.durum.adimlari_guncelle(
        tamamlanan_adim=2,
        toplam_adim=5,
        aktif_modul="Canlı Sinyal İşleme",
    )
    servis.durum.durum_guncelle(
        durum=RuntimeDurumTuru.CALISIYOR,
    )
    servis.durum.sistem_hazirlik_guncelle(
        "veri_akisi",
        80,
    )

    yanit = istemci.get("/terminal")

    assert yanit.status_code == 200
    assert "Canlı Sinyal İşleme" in yanit.text
    assert "<dt>Tamamlanan Adım</dt><dd>2</dd>" in yanit.text
    assert "<dt>Toplam Adım</dt><dd>5</dd>" in yanit.text
    assert "<dt>Genel İlerleme</dt><dd>%40</dd>" in yanit.text
    assert "<dt>Veri Akışı</dt><dd>%80</dd>" in yanit.text
    assert "çalışıyor" in yanit.text


def test_terminal_sonraki_istekte_guncel_durumu_okur():
    istemci, servis = _istemci_ve_servis()

    ilk_yanit = istemci.get("/terminal")
    assert "Sinyal Çözümleme" not in ilk_yanit.text

    servis.durum.adimlari_guncelle(
        tamamlanan_adim=4,
        toplam_adim=4,
        aktif_modul="Sinyal Çözümleme",
    )
    servis.durum.durum_guncelle(
        durum=RuntimeDurumTuru.TAMAMLANDI,
        ilerleme_yuzdesi=100,
    )

    ikinci_yanit = istemci.get("/terminal")

    assert ikinci_yanit.status_code == 200
    assert "Sinyal Çözümleme" in ikinci_yanit.text
    assert "<dt>Genel İlerleme</dt><dd>%100</dd>" in ikinci_yanit.text
    assert "tamamlandı" in ikinci_yanit.text


def test_websocket_ve_terminal_ayni_servis_durumunu_okur():
    istemci, servis = _istemci_ve_servis()

    servis.durum.adimlari_guncelle(
        tamamlanan_adim=3,
        toplam_adim=6,
        aktif_modul="Ortak Canlı Kaynak",
    )
    servis.durum.durum_guncelle(
        durum=RuntimeDurumTuru.CALISIYOR,
    )

    terminal_yaniti = istemci.get("/terminal")

    assert "Ortak Canlı Kaynak" in terminal_yaniti.text
    assert "<dt>Genel İlerleme</dt><dd>%50</dd>" in (
        terminal_yaniti.text
    )

    with istemci.websocket_connect("/ws/runtime") as websocket:
        baglanti = websocket.receive_json()

        assert baglanti["mesaj"] == (
            "SyOtağı bağlantısı kuruldu"
        )
        assert baglanti["gorunum"]["aktif_modul"] == (
            "Ortak Canlı Kaynak"
        )
        assert baglanti["gorunum"]["ilerleme_yuzdesi"] == 50.0

        servis.durum.adimlari_guncelle(
            tamamlanan_adim=5,
            toplam_adim=6,
            aktif_modul="Ortak Canlı Kaynak",
        )

        websocket.send_text("yenile")
        guncelleme = websocket.receive_json()

        assert guncelleme["mesaj"] == (
            "Canlı görünüm güncellendi"
        )
        assert guncelleme["gorunum"]["aktif_modul"] == (
            "Ortak Canlı Kaynak"
        )
        assert guncelleme["gorunum"]["ilerleme_yuzdesi"] == 83.33


def test_eski_sunucu_kurulumu_geriye_uyumludur():
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

    uygulama = RuntimeFastApiSunucusu(
        disa_aktarim
    ).olustur()

    istemci = TestClient(uygulama)
    yanit = istemci.get("/terminal")

    assert yanit.status_code == 200
    assert "SYKAŞİF" in yanit.text
    assert "İşleyiş Durumu" in yanit.text
