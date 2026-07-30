from syk_simulasyon.runtime_durumu import (
    RuntimeDurumu,
    RuntimeDurumTuru,
)
from syk_simulasyon.runtime_terminal import RuntimeTerminal


def test_terminal_gercek_isleyis_verilerini_gosterir():
    durum = RuntimeDurumu()

    durum.adimlari_guncelle(
        tamamlanan_adim=3,
        toplam_adim=8,
        aktif_modul="Ham Sinyal Birleşimi",
    )
    durum.durum_guncelle(
        durum=RuntimeDurumTuru.CALISIYOR,
        ilerleme_yuzdesi=37.5,
    )
    durum.risk_guncelle("Düşük gecikme riski")

    html = RuntimeTerminal(durum).html()

    assert "Ham Sinyal Birleşimi" in html
    assert "<dd>3</dd>" in html
    assert "<dd>8</dd>" in html
    assert "<dd>5</dd>" in html
    assert "<dd>%37.5</dd>" in html
    assert "çalışıyor" in html
    assert "Düşük gecikme riski" in html


def test_terminal_gercek_hazirlik_yuzdelerini_gosterir():
    durum = RuntimeDurumu()

    durum.sistem_hazirlik_guncelle("terminal_arayuzu", 100)
    durum.sistem_hazirlik_guncelle("veri_akisi", 80)
    durum.sistem_hazirlik_guncelle("kayit_zinciri", 60)
    durum.sistem_hazirlik_guncelle("test_durumu", 40)
    durum.sistem_hazirlik_guncelle(
        "disa_aktarim_hazirligi",
        20,
    )

    html = RuntimeTerminal(
        runtime_durumu=durum,
    ).html()

    assert "<dt>Terminal Arayüzü</dt><dd>%100</dd>" in html
    assert "<dt>Veri Akışı</dt><dd>%80</dd>" in html
    assert "<dt>Kayıt Zinciri</dt><dd>%60</dd>" in html
    assert "<dt>Test Durumu</dt><dd>%40</dd>" in html
    assert (
        "<dt>Dışa Aktarım Hazırlığı</dt><dd>%20</dd>"
        in html
    )
    assert "<dt>Üretime Hazırlık</dt><dd>%60</dd>" in html


def test_terminal_metinsel_verileri_html_kacisiyla_korur():
    durum = RuntimeDurumu()

    durum.adimlari_guncelle(
        tamamlanan_adim=1,
        toplam_adim=2,
        aktif_modul='<script>alert("x")</script>',
    )
    durum.risk_guncelle("<b>kritik</b>")

    html = RuntimeTerminal(durum).html()

    assert '<script>alert("x")</script>' not in html
    assert "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;" in html
    assert "<b>kritik</b>" not in html
    assert "&lt;b&gt;kritik&lt;/b&gt;" in html


def test_terminal_varsayilan_kullanimda_geriye_uyumludur():
    terminal = RuntimeTerminal()
    html = terminal.html()

    assert terminal.durum().runtime_durumu == "AKTİF"
    assert "SYKAŞİF" in html
    assert "SyOtağı" in html
    assert "İşleyiş Durumu" in html
    assert "Sistem Hazırlık Durumu" in html
    assert "<dt>Genel İlerleme</dt><dd>%0</dd>" in html


def test_terminal_ayni_durum_nesnesindeki_guncellemeyi_yansitir():
    durum = RuntimeDurumu()
    terminal = RuntimeTerminal(durum)

    ilk_html = terminal.html()
    assert "Sinyal Çözümleme" not in ilk_html

    durum.adimlari_guncelle(
        tamamlanan_adim=4,
        toplam_adim=5,
        aktif_modul="Sinyal Çözümleme",
    )

    ikinci_html = terminal.html()

    assert "Sinyal Çözümleme" in ikinci_html
    assert "<dt>Genel İlerleme</dt><dd>%80</dd>" in ikinci_html
