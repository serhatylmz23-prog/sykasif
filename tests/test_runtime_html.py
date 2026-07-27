from syk_simulasyon.runtime_anlik_gorunum import RuntimeAnlikGorunumSaglayicisi
from syk_simulasyon.runtime_html import RuntimeHtmlSaglayicisi
from syk_simulasyon.runtime_izleme import RuntimeIzlemeSaglayicisi
from syk_simulasyon.runtime_servisi import RuntimeServisi


def test_html_olusturulur():
    servis = RuntimeServisi()

    html_saglayici = RuntimeHtmlSaglayicisi(
        RuntimeAnlikGorunumSaglayicisi(
            RuntimeIzlemeSaglayicisi(servis)
        )
    )

    html = html_saglayici.html_uret()

    assert "<table>" in html
    assert "</table>" in html
    assert "durum" in html


def test_html_satirlar_icerir():
    servis = RuntimeServisi()

    html_saglayici = RuntimeHtmlSaglayicisi(
        RuntimeAnlikGorunumSaglayicisi(
            RuntimeIzlemeSaglayicisi(servis)
        )
    )

    html = html_saglayici.html_uret()

    assert "<tr>" in html
    assert "<th>" in html
    assert "<td>" in html


def test_html_guncel_veriyi_icerir():
    servis = RuntimeServisi()

    servis.durum.durum_guncelle(
        durum=servis.durum.durum,
        aktif_modul="DSP",
        ilerleme_yuzdesi=60.0,
    )

    html_saglayici = RuntimeHtmlSaglayicisi(
        RuntimeAnlikGorunumSaglayicisi(
            RuntimeIzlemeSaglayicisi(servis)
        )
    )

    html = html_saglayici.html_uret()

    assert "DSP" in html
    assert "60.0" in html