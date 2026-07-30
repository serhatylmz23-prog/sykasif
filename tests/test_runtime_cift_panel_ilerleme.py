from syk_simulasyon.runtime_durumu import RuntimeDurumu
from syk_simulasyon.runtime_terminal import RuntimeTerminal


def test_cift_panel_alanlari_gorunur():
    html = RuntimeTerminal().html()

    assert "\u0130\u015fleyi\u015f Durumu" in html
    assert "Sistem Haz\u0131rl\u0131k Durumu" in html
    assert "Aktif Ad\u0131m" in html
    assert "Tamamlanan Ad\u0131m" in html
    assert "Toplam Ad\u0131m" in html
    assert "Genel \u0130lerleme" in html
    assert "Terminal Aray\u00fcz\u00fc" in html
    assert "Veri Ak\u0131\u015f\u0131" in html
    assert "Kay\u0131t Zinciri" in html
    assert "Test Durumu" in html
    assert "D\u0131\u015fa Aktar\u0131m Haz\u0131rl\u0131\u011f\u0131" in html
    assert "\u00dcretime Haz\u0131rl\u0131k" in html


def test_sistem_hazirlik_yuzdeleri_hesaplanir():
    durum = RuntimeDurumu()

    assert hasattr(durum, "sistem_hazirlik_guncelle")
    assert hasattr(durum, "sistem_hazirlik_ozeti")

    durum.sistem_hazirlik_guncelle("terminal_arayuzu", 100)
    durum.sistem_hazirlik_guncelle("veri_akisi", 100)
    durum.sistem_hazirlik_guncelle("kayit_zinciri", 100)
    durum.sistem_hazirlik_guncelle("test_durumu", 100)
    durum.sistem_hazirlik_guncelle("disa_aktarim_hazirligi", 80)

    ozet = durum.sistem_hazirlik_ozeti()

    assert ozet["terminal_arayuzu"] == 100
    assert ozet["veri_akisi"] == 100
    assert ozet["kayit_zinciri"] == 100
    assert ozet["test_durumu"] == 100
    assert ozet["disa_aktarim_hazirligi"] == 80
    assert ozet["genel_uretime_hazirlik"] == 96.0
