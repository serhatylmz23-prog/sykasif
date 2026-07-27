from syk_simulasyon.runtime_anlik_gorunum import RuntimeAnlikGorunumSaglayicisi
from syk_simulasyon.runtime_izleme import RuntimeIzlemeSaglayicisi
from syk_simulasyon.runtime_markdown import RuntimeMarkdownSaglayicisi
from syk_simulasyon.runtime_servisi import RuntimeServisi


def test_markdown_olusturulur():
    servis = RuntimeServisi()

    markdown_saglayici = RuntimeMarkdownSaglayicisi(
        RuntimeAnlikGorunumSaglayicisi(
            RuntimeIzlemeSaglayicisi(servis)
        )
    )

    markdown = markdown_saglayici.markdown_uret()

    assert "# SyKaşif Runtime" in markdown
    assert "| Alan | Değer |" in markdown
    assert "durum" in markdown


def test_markdown_tablo_icerir():
    servis = RuntimeServisi()

    markdown_saglayici = RuntimeMarkdownSaglayicisi(
        RuntimeAnlikGorunumSaglayicisi(
            RuntimeIzlemeSaglayicisi(servis)
        )
    )

    markdown = markdown_saglayici.markdown_uret()

    assert "|------|-------|" in markdown
    assert "|" in markdown


def test_markdown_guncel_veriyi_icerir():
    servis = RuntimeServisi()

    servis.durum.durum_guncelle(
        durum=servis.durum.durum,
        aktif_modul="DSP",
        ilerleme_yuzdesi=75.0,
    )

    markdown_saglayici = RuntimeMarkdownSaglayicisi(
        RuntimeAnlikGorunumSaglayicisi(
            RuntimeIzlemeSaglayicisi(servis)
        )
    )

    markdown = markdown_saglayici.markdown_uret()

    assert "DSP" in markdown
    assert "75.0" in markdown